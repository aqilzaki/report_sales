from app.models import Reseller, Transaksi
import jwt
from app.database import db
from sqlalchemy import text
from datetime import datetime, timedelta, date
from flask import current_app
from decimal import Decimal
import calendar
from collections import defaultdict

# ======================== UTIL DIALECT & HELPERS ========================

def _dialect():
    return db.engine.dialect.name.lower()

def _is_mssql():
    d = _dialect()
    return d in ("mssql", "microsoft sql server")

def _date_expr(col="tgl_entri"):
    # Ekspresi SQL untuk cast ke DATE per-dialect
    if _is_mssql():
        return f"CAST({col} AS DATE)"
    return f"DATE({col})"

def _paginate_root(limit, offset):
    if _is_mssql():
        return f"ORDER BY kode OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY"
    return f"ORDER BY kode LIMIT :limit OFFSET :offset"

def _placeholders(prefix, values):
    # Buat placeholder named params untuk IN (...) aman
    names = []
    params = {}
    for i, v in enumerate(values):
        key = f"{prefix}_{i}"
        names.append(f":{key}")
        params[key] = v
    return ", ".join(names), params

# ======================== PERIOD FILTER ========================

def _get_period_range(period: str, year=None, month=None, day=None, week=None):
    """Hitung range waktu berdasarkan period (day|month|week) - inclusive"""
    try:
        if period == "day":
            if not day:
                raise ValueError("day harus diisi format YYYY-MM-DD")
            start = datetime.strptime(day, "%Y-%m-%d")
            end = start.replace(hour=23, minute=59, second=59)

        elif period == "month":
            if not year or not month:
                raise ValueError("year dan month harus diisi untuk period=month")
            start = datetime(year, month, 1)
            days_in_month = calendar.monthrange(year, month)[1]
            end = datetime(year, month, days_in_month, 23, 59, 59)

        elif period == "week":
            if not year or not month or not week:
                raise ValueError("year, month, dan week harus diisi untuk period=week")
            month_cal = calendar.Calendar(firstweekday=0).monthdatescalendar(year, month)
            if week < 1 or week > len(month_cal):
                raise ValueError(f"Bulan {month}/{year} hanya punya {len(month_cal)} minggu")
            week_days = month_cal[week - 1]
            start = datetime.combine(week_days[0], datetime.min.time())
            end = datetime.combine(week_days[-1], datetime.max.time())

        else:
            raise ValueError("period harus day|month|week")

        return start, end
    except Exception as e:
        print(f"Error in _get_period_range: {str(e)}")
        raise e

# ======================== INSENTIF CALCULATION =======================

def calculate_insentif(profit):
    profit = Decimal(profit)
    basic_salary = Decimal(3_000_000)
    q1 = q2 = q3 = q4 = q5 = Decimal(0)
    bonus_ekstra = Decimal(0)

    if profit <= Decimal(3_000_000):
        return {
            "basic_salary": int(basic_salary),
            "q1": 0, "q2": 0, "q3": 0, "q4": 0, "q5": 0,
            "bonus_ekstra": 0,
            "total_insentif": 0,
            "total_salary": int(basic_salary)
        }

    if profit > Decimal(3_000_000):
        q1_max = min(profit, Decimal(10_000_000))
        q1 = (q1_max - Decimal(3_000_000)) * Decimal("0.10")
    if profit > Decimal(10_000_000):
        q2_max = min(profit, Decimal(15_000_000))
        q2 = (q2_max - Decimal(10_000_000)) * Decimal("0.20")
    if profit > Decimal(15_000_000):
        q3_max = min(profit, Decimal(20_000_000))
        q3 = (q3_max - Decimal(15_000_000)) * Decimal("0.30")
    if profit > Decimal(20_000_000):
        q4_max = min(profit, Decimal(25_000_000))
        q4 = (q4_max - Decimal(20_000_000)) * Decimal("0.40")
    if profit > Decimal(25_000_000):
        q5 = (profit - Decimal(25_000_000)) * Decimal("0.50")

    if profit > Decimal(10_000_000):
        bonus_ekstra = Decimal(700_000)

    total_insentif = q1 + q2 + q3 + q4 + q5 + bonus_ekstra
    total_salary = basic_salary + total_insentif

    return {
        "basic_salary": int(basic_salary),
        "q1": int(q1),
        "q2": int(q2),
        "q3": int(q3),
        "q4": int(q4),
        "q5": int(q5),
        "bonus_ekstra": int(bonus_ekstra),
        "total_insentif": int(total_insentif),
        "total_salary": int(total_salary)
    }

# ======================== BATCH ACTIVITY CHECKS ========================

def _batch_daily_counts(reseller_codes, start_dt, end_dt):
    """
    Tarik agregasi harian untuk banyak reseller sekaligus:
    return dict: {kode_reseller: {date: count, ...}, ...}
    """
    if not reseller_codes:
        return {}

    date_col = _date_expr("t.tgl_entri")
    placeholders, params = _placeholders("code", reseller_codes)
    params.update({"start_dt": start_dt, "end_dt": end_dt})

    sql = text(f"""
        SELECT 
            t.kode_reseller,
            {date_col} AS trx_date,
            COUNT(t.kode) AS daily_count
        FROM transaksi t
        WHERE t.kode_reseller IN ({placeholders})
          AND t.tgl_entri >= :start_dt AND t.tgl_entri <= :end_dt
        GROUP BY t.kode_reseller, {date_col}
        ORDER BY t.kode_reseller, {date_col}
    """)

    rows = db.session.execute(sql, params).fetchall()
    result = defaultdict(dict)
    for kode, trx_date, cnt in rows:
        result[kode][trx_date] = cnt
    return result

def _has_no_15_day_gap(daily_transactions, start_dt, end_dt):
    """Cek apakah tidak ada gap 15 hari berturut-turut tanpa transaksi"""
    if not daily_transactions:
        return False
    try:
        transaction_dates = sorted(daily_transactions.keys())
        first_trx_date = transaction_dates[0]
        if (first_trx_date - start_dt.date()).days >= 15:
            return False
        for i in range(len(transaction_dates) - 1):
            current_date = transaction_dates[i]
            next_date = transaction_dates[i + 1]
            gap_days = (next_date - current_date).days - 1
            if gap_days >= 15:
                return False
        last_trx_date = transaction_dates[-1]
        if (end_dt.date() - last_trx_date).days >= 15:
            return False
        return True
    except Exception as e:
        print(f"Error in _has_no_15_day_gap: {str(e)}")
        return False

def _count_active_resellers(reseller_codes, start_dt, end_dt):
    """
    Reseller aktif:
    1) Ada minimal 3 transaksi pada salah satu hari dalam periode
    2) Tidak ada gap >= 15 hari tanpa transaksi
    Dibatch supaya 1 query, sisanya proses di Python.
    """
    if not reseller_codes:
        return 0
    try:
        daily = _batch_daily_counts(reseller_codes, start_dt, end_dt)
        active = 0
        for kode in reseller_codes:
            d = daily.get(kode, {})
            if not d:
                continue
            has_min_daily = any(cnt >= 3 for cnt in d.values())
            if not has_min_daily:
                continue
            if _has_no_15_day_gap(d, start_dt, end_dt):
                active += 1
        return active
    except Exception as e:
        print(f"Error in _count_active_resellers: {str(e)}")
        return 0

def _count_acquisition_active_resellers(reseller_codes, start_dt, end_dt):
    """
    Akuisisi aktif:
    1) Total transaksi >= 3 dalam periode
    2) Memenuhi kriteria aktif
    """
    if not reseller_codes:
        return 0
    try:
        placeholders, params = _placeholders("code", reseller_codes)
        params.update({"start_dt": start_dt, "end_dt": end_dt})

        min_trx_sql = text(f"""
            SELECT t.kode_reseller, COUNT(t.kode) AS total_trx
            FROM transaksi t
            WHERE t.kode_reseller IN ({placeholders})
              AND t.tgl_entri >= :start_dt AND t.tgl_entri <= :end_dt
            GROUP BY t.kode_reseller
            HAVING COUNT(t.kode) >= 3
        """)
        qualified = [r[0] for r in db.session.execute(min_trx_sql, params).fetchall()]
        if not qualified:
            return 0
        return _count_active_resellers(qualified, start_dt, end_dt)
    except Exception as e:
        print(f"Error in _count_acquisition_active_resellers: {str(e)}")
        return 0

# ======================== HIERARCHY WITH PROFIT ========================

def get_reseller_hierarchy_with_profit(page=1, limit=10):
    """Ambil reseller root (upline), list downline, dan profit per downline; pagination SQL-native."""
    try:
        offset = (page - 1) * limit

        # Roots dengan pagination native
        root_sql = text(f"""
            SELECT kode, nama, kode_upline
            FROM reseller
            WHERE kode_upline IS NULL OR kode_upline = '' OR kode_upline = '0'
            {_paginate_root(limit, offset)}
        """)
        roots = db.session.execute(root_sql, {"limit": limit, "offset": offset}).fetchall()
        if not roots:
            return {"page": page, "limit": limit, "total": 0, "data": []}

        root_codes = [r[0] for r in roots]

        # Ambil semua downline untuk roots sekaligus
        ph, params = _placeholders("root", root_codes)
        down_sql = text(f"""
            SELECT d.kode_upline AS root_kode, d.kode AS down_kode, d.nama AS down_nama
            FROM reseller d
            WHERE d.kode_upline IN ({ph})
        """)
        down_rows = db.session.execute(down_sql, params).fetchall()

        # Map root -> list downlines
        root_to_down = defaultdict(list)
        all_down_codes = []
        for root_kode, down_kode, down_nama in down_rows:
            root_to_down[root_kode].append((down_kode, down_nama))
            all_down_codes.append(down_kode)

        # Profit & count transaksi per downline (1 query untuk semua downline)
        profit_map = {}
        if all_down_codes:
            ph2, params2 = _placeholders("dcode", all_down_codes)
            profit_sql = text(f"""
                SELECT t.kode_reseller, 
                       COALESCE(COUNT(t.kode), 0) AS jumlah_trx,
                       COALESCE(SUM(t.harga - t.harga_beli), 0) AS profit
                FROM transaksi t
                WHERE t.kode_reseller IN ({ph2})
                GROUP BY t.kode_reseller
            """)
            for kode_reseller, jml, profit in db.session.execute(profit_sql, params2).fetchall():
                profit_map[kode_reseller] = (int(jml or 0), float(profit or 0.0))

        # Susun hasil per root
        data = []
        for kode, nama, _ in roots:
            downlines = []
            total_profit_upline = 0.0
            for dkode, dnama in root_to_down.get(kode, []):
                jml, prof = profit_map.get(dkode, (0, 0.0))
                total_profit_upline += prof
                downlines.append({
                    "kode": dkode,
                    "nama": dnama,
                    "jumlah_transaksi": jml,
                    "total_profit": prof,
                })
            data.append({
                "upline": {"kode": kode, "nama": nama, "total_profit": float(total_profit_upline)},
                "downlines": downlines
            })

        # Total roots
        total_sql = text("""
            SELECT COUNT(*)
            FROM reseller
            WHERE kode_upline IS NULL OR kode_upline = '' OR kode_upline = '0'
        """)
        total_roots = db.session.execute(total_sql).scalar()

        return {"page": page, "limit": limit, "total": int(total_roots or 0), "data": data}

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"page": page, "limit": limit, "total": 0, "data": []}

# ======================== MAIN SUMMARY (BULAN/HARI/MINGGU) ========================

def get_reseller_summary_custom(period="month", year=None, month=None, day=None, week=None, page=1, limit=50):
    """
    Summary per upline dalam periode berdasarkan transaksi seluruh downline.
    Optimized: 1 query besar + batch activity checks.
    """
    try:
        start_dt, end_dt = _get_period_range(period, year, month, day, week)
        offset = (page - 1) * limit

        # Ambil roots paginated (SQL native)
        root_sql = text(f"""
            SELECT r.kode, r.nama
            FROM reseller r
            WHERE r.kode_upline IS NULL OR r.kode_upline = '' OR r.kode_upline = '0'
            {_paginate_root(limit, offset)}
        """)
        roots = db.session.execute(root_sql, {"limit": limit, "offset": offset}).fetchall()
        if not roots:
            return []

        root_codes = [r[0] for r in roots]

        # Ambil seluruh downline untuk roots ini
        ph, params = _placeholders("root", root_codes)
        down_sql = text(f"""
            SELECT d.kode_upline AS id_upline, d.kode AS kode_down
            FROM reseller d
            WHERE d.kode_upline IN ({ph})
        """)
        down_rows = db.session.execute(down_sql, params).fetchall()

        root_to_down = defaultdict(list)
        for uid, dcode in down_rows:
            root_to_down[uid].append(dcode)

        # Agregasi transaksi untuk semua downline sekaligus
        all_down_codes = [d for lst in root_to_down.values() for d in lst]
        trx_agg = defaultdict(lambda: {"jmlh_trx": 0, "omset": 0.0, "profit": 0.0})
        if all_down_codes:
            ph2, params2 = _placeholders("dcode", all_down_codes)
            params2.update({"start_dt": start_dt, "end_dt": end_dt})
            trx_sql = text(f"""
                SELECT d.kode_upline AS id_upline,
                       COALESCE(COUNT(t.kode), 0) AS jmlh_trx,
                       COALESCE(SUM(t.harga), 0) AS omset,
                       COALESCE(SUM(t.harga - t.harga_beli), 0) AS profit
                FROM reseller d
                LEFT JOIN transaksi t
                  ON t.kode_reseller = d.kode
                 AND t.tgl_entri >= :start_dt AND t.tgl_entri <= :end_dt
                WHERE d.kode IN ({ph2})
                GROUP BY d.kode_upline
            """)
            for uid, jml, oms, prof in db.session.execute(trx_sql, params2).fetchall():
                trx_agg[uid] = {
                    "jmlh_trx": int(jml or 0),
                    "omset": float(oms or 0.0),
                    "profit": float(prof or 0.0),
                }

        # Batch activity metrics per upline (berdasar daftar downline per upline)
        active_map = {}
        acq_active_map = {}
        # Siapkan sekali daily counts untuk semua downline (hemat query)
        daily_counts_all = _batch_daily_counts(all_down_codes, start_dt, end_dt)

        # Hitung total transaksi per reseller untuk acq>=3
        # (gunakan agregasi dari daily_counts_all atau query kecil)
        # Lebih ringan: query count per reseller periode
        acq_params = {}
        acq_map = defaultdict(int)
        if all_down_codes:
            ph3, params3 = _placeholders("dcode", all_down_codes)
            params3.update({"start_dt": start_dt, "end_dt": end_dt})
            acq_sql = text(f"""
                SELECT t.kode_reseller, COUNT(t.kode) AS total_trx
                FROM transaksi t
                WHERE t.kode_reseller IN ({ph3})
                  AND t.tgl_entri >= :start_dt AND t.tgl_entri <= :end_dt
                GROUP BY t.kode_reseller
            """)
            for kode_reseller, total_trx in db.session.execute(acq_sql, params3).fetchall():
                acq_map[kode_reseller] = int(total_trx or 0)

        # Hitung per upline
        for uid, downs in root_to_down.items():
            # Active
            act = 0
            acq_act = 0
            for dcode in downs:
                d_daily = daily_counts_all.get(dcode, {})
                if not d_daily:
                    continue
                has_min_daily = any(cnt >= 3 for cnt in d_daily.values())
                if not has_min_daily:
                    continue
                no_gap = _has_no_15_day_gap(d_daily, start_dt, end_dt)
                if no_gap:
                    act += 1
                    if acq_map.get(dcode, 0) >= 3:
                        acq_act += 1
            active_map[uid] = act
            acq_active_map[uid] = acq_act

        # Susun DTO
        hasil = []
        for kode, nama in roots:
            akuisisi = len(root_to_down.get(kode, []))
            agg = trx_agg.get(kode, {"jmlh_trx": 0, "omset": 0.0, "profit": 0.0})
            insentif_detail = calculate_insentif(agg["profit"])
            hasil.append({
                "id_upline": kode,
                "nama_upline": nama,
                "periode": period,
                "jmlh_trx": agg["jmlh_trx"],
                "jmlh_trx_aktif": int(active_map.get(kode, 0)),
                "akuisisi": akuisisi,
                "akuisisi_aktif": int(acq_active_map.get(kode, 0)),
                "omset": agg["omset"],
                "profit_upline": agg["profit"],
                "insentif": insentif_detail["total_insentif"],
                "insentif_detail": insentif_detail,
                "start": start_dt.isoformat(timespec="seconds"),
                "end": end_dt.isoformat(timespec="seconds"),
            })

        return hasil

    except Exception as e:
        print(f"Error in get_reseller_summary_custom: {str(e)}")
        return {
            "status": "error",
            "message": "Terjadi kesalahan saat mengambil data summary",
            "error": str(e),
            "data": []
        }

# ======================== SELF SUMMARY ========================

def get_self_summary(token, period="month", year=None, month=None, day=None, week=None):
    try:
        payload = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
        kode = payload["sub"]

        user_sql = text("SELECT kode, nama FROM reseller WHERE kode = :kode")
        user = db.session.execute(user_sql, {"kode": kode}).fetchone()
        if not user:
            return {"error": f"Reseller {kode} tidak ditemukan"}

        start_dt, end_dt = _get_period_range(period, year, month, day, week)
        root_kode, root_nama = user[0], user[1]

        # Downlines
        dsql = text("SELECT kode FROM reseller WHERE kode_upline = :upline_kode")
        down_rows = db.session.execute(dsql, {"upline_kode": root_kode}).fetchall()
        down_codes = [r[0] for r in down_rows]

        jmlh_trx = jmlh_trx_aktif = 0
        total_omset = total_profit = 0.0
        akuisisi_aktif = 0

        if down_codes:
            ph, params = _placeholders("dcode", down_codes)
            params.update({"start_dt": start_dt, "end_dt": end_dt})
            trx_sql = text(f"""
                SELECT 
                    COALESCE(COUNT(t.kode), 0) AS jumlah,
                    COALESCE(SUM(t.harga), 0) AS omset,
                    COALESCE(SUM(t.harga - t.harga_beli), 0) AS profit
                FROM transaksi t
                WHERE t.kode_reseller IN ({ph})
                  AND t.tgl_entri >= :start_dt AND t.tgl_entri <= :end_dt
            """)
            jumlah, omset, profit = db.session.execute(trx_sql, params).fetchone()
            jmlh_trx = int(jumlah or 0)
            total_omset = float(omset or 0.0)
            total_profit = float(profit or 0.0)

            # Batch activity
            daily_counts = _batch_daily_counts(down_codes, start_dt, end_dt)
            # total transaksi per reseller (untuk acq >= 3)
            acq_map = defaultdict(int)
            acq_sql = text(f"""
                SELECT t.kode_reseller, COUNT(t.kode) AS total_trx
                FROM transaksi t
                WHERE t.kode_reseller IN ({ph})
                  AND t.tgl_entri >= :start_dt AND t.tgl_entri <= :end_dt
                GROUP BY t.kode_reseller
            """)
            for kode_reseller, total_trx in db.session.execute(acq_sql, params).fetchall():
                acq_map[kode_reseller] = int(total_trx or 0)

            for dcode in down_codes:
                d = daily_counts.get(dcode, {})
                if not d:
                    continue
                if any(c >= 3 for c in d.values()) and _has_no_15_day_gap(d, start_dt, end_dt):
                    jmlh_trx_aktif += 1
                    if acq_map.get(dcode, 0) >= 3:
                        akuisisi_aktif += 1

        akuisisi = len(down_codes)
        insentif_detail = calculate_insentif(total_profit)

        return {
            "id_upline": root_kode,
            "nama_upline": root_nama,
            "periode": period,
            "jmlh_trx": jmlh_trx,
            "jmlh_trx_aktif": int(jmlh_trx_aktif),
            "akuisisi": akuisisi,
            "akuisisi_aktif": int(akuisisi_aktif),
            "omset": total_omset,
            "profit_upline": total_profit,
            "insentif": insentif_detail["total_insentif"],
            "insentif_detail": insentif_detail,
            "start": start_dt.isoformat(timespec="seconds"),
            "end": end_dt.isoformat(timespec="seconds"),
        }

    except Exception as e:
        print(f"Error in get_self_summary: {str(e)}")
        return {"error": str(e)}

# ======================== SUMMARY PER MINGGU ========================

def get_summary_by_week(year, month, page: int = 1, limit: int = 50):
    """Summary per minggu untuk semua upline dengan pagination SQL-native; batch untuk aktivitas."""
    try:
        month_cal = calendar.Calendar(firstweekday=0).monthdatescalendar(year, month)
        offset = (page - 1) * limit

        # Roots paginated
        root_sql = text(f"""
            SELECT kode, nama
            FROM reseller
            WHERE kode_upline IS NULL OR kode_upline = '' OR kode_upline = '0'
            {_paginate_root(limit, offset)}
        """)
        roots = db.session.execute(root_sql, {"limit": limit, "offset": offset}).fetchall()

        count_sql = text("""
            SELECT COUNT(*)
            FROM reseller
            WHERE kode_upline IS NULL OR kode_upline = '' OR kode_upline = '0'
        """)
        total_roots = int(db.session.execute(count_sql).scalar() or 0)

        if not roots:
            return {"page": page, "limit": limit, "total_roots": total_roots, "total_pages": (total_roots + limit - 1) // limit, "data": []}

        root_codes = [r[0] for r in roots]
        # Downlines untuk roots ini
        ph, params = _placeholders("root", root_codes)
        down_sql = text(f"""
            SELECT d.kode_upline AS id_upline, d.kode AS kode_down, d.nama AS nama_down
            FROM reseller d
            WHERE d.kode_upline IN ({ph})
        """)
        down_rows = db.session.execute(down_sql, params).fetchall()

        root_to_down = defaultdict(list)
        for uid, dcode, _ in down_rows:
            root_to_down[uid].append(dcode)

        data = []
        for week_num, week_days in enumerate(month_cal, start=1):
            start_dt = datetime.combine(week_days[0], datetime.min.time())
            end_dt = datetime.combine(week_days[-1], datetime.max.time())

            # Agregasi per upline untuk minggu ini
            all_down_codes = [d for lst in root_to_down.values() for d in lst]
            trx_agg = defaultdict(lambda: {"jmlh_trx": 0, "omset": 0.0, "profit": 0.0})
            if all_down_codes:
                ph2, params2 = _placeholders("dcode", all_down_codes)
                params2.update({"start_dt": start_dt, "end_dt": end_dt})
                trx_sql = text(f"""
                    SELECT d.kode_upline AS id_upline,
                           COALESCE(COUNT(t.kode), 0) AS jmlh_trx,
                           COALESCE(SUM(t.harga), 0) AS omset,
                           COALESCE(SUM(t.harga - t.harga_beli), 0) AS profit
                    FROM reseller d
                    LEFT JOIN transaksi t
                      ON t.kode_reseller = d.kode
                     AND t.tgl_entri >= :start_dt AND t.tgl_entri <= :end_dt
                    WHERE d.kode IN ({ph2})
                    GROUP BY d.kode_upline
                """)
                for uid, jml, oms, prof in db.session.execute(trx_sql, params2).fetchall():
                    trx_agg[uid] = {"jmlh_trx": int(jml or 0), "omset": float(oms or 0.0), "profit": float(prof or 0.0)}

            # Batch activity untuk minggu ini
            daily_counts = _batch_daily_counts(all_down_codes, start_dt, end_dt)
            # total trx per reseller minggu ini
            acq_map = defaultdict(int)
            if all_down_codes:
                acq_sql = text(f"""
                    SELECT t.kode_reseller, COUNT(t.kode) AS total_trx
                    FROM transaksi t
                    WHERE t.kode_reseller IN ({ph2})
                      AND t.tgl_entri >= :start_dt AND t.tgl_entri <= :end_dt
                    GROUP BY t.kode_reseller
                """)
                for kode_reseller, total_trx in db.session.execute(acq_sql, params2).fetchall():
                    acq_map[kode_reseller] = int(total_trx or 0)

            for root_kode, root_nama in roots:
                downs = root_to_down.get(root_kode, [])
                jmlh_trx_aktif = 0
                akuisisi_aktif = 0
                for dcode in downs:
                    d = daily_counts.get(dcode, {})
                    if not d:
                        continue
                    if any(c >= 3 for c in d.values()) and _has_no_15_day_gap(d, start_dt, end_dt):
                        jmlh_trx_aktif += 1
                        if acq_map.get(dcode, 0) >= 3:
                            akuisisi_aktif += 1

                agg = trx_agg.get(root_kode, {"jmlh_trx": 0, "omset": 0.0, "profit": 0.0})
                insentif_detail = calculate_insentif(agg["profit"])

                data.append({
                    "id_upline": root_kode,
                    "nama_upline": root_nama,
                    "week": week_num,
                    "jmlh_trx": agg["jmlh_trx"],
                    "jmlh_trx_aktif": int(jmlh_trx_aktif),
                    "akuisisi": len(downs),
                    "akuisisi_aktif": int(akuisisi_aktif),
                    "omset": agg["omset"],
                    "profit_upline": agg["profit"],
                    "insentif": float(insentif_detail["total_insentif"]),
                    "insentif_detail": insentif_detail,
                    "start": start_dt.isoformat(timespec="seconds"),
                    "end": end_dt.isoformat(timespec="seconds"),
                })

        return {
            "page": page,
            "limit": limit,
            "total_roots": total_roots,
            "total_pages": (total_roots + limit - 1) // limit,
            "data": data
        }

    except Exception as e:
        print(f"Error in get_summary_by_week: {str(e)}")
        return {"page": page, "limit": limit, "total_roots": 0, "total_pages": 0, "data": []}

# ======================== COMPARE MONTHS ========================

def compare_months(year1, month1, year2, month2, page: int = 1, limit: int = 50):
    """Bandingkan summary bulan1 vs bulan2 (per minggu, per upline) dengan pagination"""
    try:
        result1 = get_summary_by_week(year1, month1, page=page, limit=limit)
        result2 = get_summary_by_week(year2, month2, page=page, limit=limit)

        data1 = result1.get("data", []) if isinstance(result1, dict) else result1
        data2 = result2.get("data", []) if isinstance(result2, dict) else result2

        comparison = {}

        for d in data1:
            key = (d["id_upline"], d["week"])
            comparison[key] = {
                "upline": {"id": d["id_upline"], "nama": d["nama_upline"], "week": d["week"]},
                "month1": {
                    "jmlh_trx": d["jmlh_trx"],
                    "jmlh_trx_aktif": d["jmlh_trx_aktif"],
                    "akuisisi": d.get("akuisisi", 0),
                    "akuisisi_aktif": d.get("akuisisi_aktif", 0),
                    "omset": d["omset"],
                    "profit": d["profit_upline"],
                    "insentif": d.get("insentif", 0),
                    "insentif_detail": d.get("insentif_detail", {}),
                },
                "month2": {
                    "jmlh_trx": 0,
                    "jmlh_trx_aktif": 0,
                    "akuisisi": 0,
                    "akuisisi_aktif": 0,
                    "omset": 0,
                    "profit": 0,
                    "insentif": 0,
                    "insentif_detail": {},
                },
            }

        for d in data2:
            key = (d["id_upline"], d["week"])
            m2 = {
                "jmlh_trx": d["jmlh_trx"],
                "jmlh_trx_aktif": d["jmlh_trx_aktif"],
                "akuisisi": d.get("akuisisi", 0),
                "akuisisi_aktif": d.get("akuisisi_aktif", 0),
                "omset": d["omset"],
                "profit": d["profit_upline"],
                "insentif": d.get("insentif", 0),
                "insentif_detail": d.get("insentif_detail", {}),
            }
            if key not in comparison:
                comparison[key] = {
                    "upline": {"id": d["id_upline"], "nama": d["nama_upline"], "week": d["week"]},
                    "month1": {
                        "jmlh_trx": 0, "jmlh_trx_aktif": 0, "akuisisi": 0, "akuisisi_aktif": 0,
                        "omset": 0, "profit": 0, "insentif": 0, "insentif_detail": {}
                    },
                    "month2": m2,
                }
            else:
                comparison[key]["month2"] = m2

        return {
            "status": "success",
            "message": "Data perbandingan bulanan berhasil diambil",
            "page": page,
            "per_page": limit,
            "total_roots": max(result1.get("total_roots", 0), result2.get("total_roots", 0)),
            "total_pages": max(result1.get("total_pages", 0), result2.get("total_pages", 0)),
            "data": list(comparison.values())
        }

    except Exception as e:
        print(f"Error in compare_months: {str(e)}")
        return {
            "status": "error",
            "message": "Gagal membandingkan summary",
            "error": str(e),
            "page": page,
            "limit": limit,
            "total_roots": 0,
            "total_pages": 0,
            "data": []
        }

# ======================== DEBUG UTILS ========================

def get_reseller_activity_detail(reseller_code, start_dt, end_dt):
    """Debug detail aktivitas reseller berdasarkan daily aggregation (dialect-aware)."""
    try:
        date_col = _date_expr("t.tgl_entri")
        sql = text(f"""
            SELECT 
                {date_col} AS trx_date,
                COUNT(t.kode) AS daily_count
            FROM transaksi t
            WHERE t.kode_reseller = :reseller_code
              AND t.tgl_entri >= :start_dt AND t.tgl_entri <= :end_dt
            GROUP BY {date_col}
            ORDER BY {date_col}
        """)
        rows = db.session.execute(sql, {
            "reseller_code": reseller_code,
            "start_dt": start_dt,
            "end_dt": end_dt
        }).fetchall()

        daily_transactions = {row[0]: row[1] for row in rows}
        has_min_daily = any(count >= 3 for count in daily_transactions.values())
        has_no_gap = _has_no_15_day_gap(daily_transactions, start_dt, end_dt)
        return {
            "reseller_code": reseller_code,
            "transaction_dates": [(str(r[0]), r[1]) for r in rows],
            "has_min_daily_trx": has_min_daily,
            "has_no_15_day_gap": has_no_gap,
            "is_active": has_min_daily and has_no_gap
        }
    except Exception as e:
        print(f"Error in get_reseller_activity_detail: {str(e)}")
        return {"reseller_code": reseller_code, "error": str(e)}
