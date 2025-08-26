from app.models import Reseller, Transaksi
import jwt
from app.database import db
from sqlalchemy import func, case, and_, distinct, text
from datetime import datetime, timedelta, date
from flask import current_app
import calendar
from app.api.auth.controller import get_user_from_token

def get_reseller_hierarchy_with_profit():
    """Ambil semua reseller root, cek downline, dan hitung profit per downline lalu akumulasi ke upline"""
    try:
        print("=== DEBUG HIERARCHY ===")
        
        # Debug: Cek struktur tabel reseller dulu
        print("Checking table structure...")
        
        # Gunakan raw query untuk lebih aman
        # 1. Cari reseller yang tidak punya upline (root)
        root_query = text("""
            SELECT kode, nama, kode_upline 
            FROM reseller 
            WHERE kode_upline IS NULL OR kode_upline = '' OR kode_upline = '0'
            LIMIT 10
        """)
        
        root_results = db.session.execute(root_query).fetchall()
        print(f"Found {len(root_results)} potential roots")
        
        if not root_results:
            # Jika tidak ada root, coba ambil semua reseller dan lihat strukturnya
            sample_query = text("SELECT kode, nama, kode_upline FROM reseller LIMIT 5")
            sample_results = db.session.execute(sample_query).fetchall()
            print("Sample resellers:")
            for r in sample_results:
                print(f"  Kode: {r[0]}, Nama: {r[1]}, Upline: {r[2]}")
            return []

        hasil = []
        for root_row in root_results:
            root_kode = root_row[0]
            root_nama = root_row[1]
            print(f"\nProcessing root: {root_kode} - {root_nama}")
            
            # 2. Cari downlines untuk root ini
            downline_query = text("""
                SELECT kode, nama 
                FROM reseller 
                WHERE kode_upline = :upline_kode
            """)
            
            downline_results = db.session.execute(
                downline_query, 
                {'upline_kode': root_kode}
            ).fetchall()
            
            print(f"  Found {len(downline_results)} downlines")

            downline_data = []
            total_profit_upline = 0.0

            for downline_row in downline_results:
                downline_kode = downline_row[0]
                downline_nama = downline_row[1]
                print(f"    Processing downline: {downline_kode}")
                
                # 3. Hitung profit untuk downline ini
                profit_query = text("""
                    SELECT 
                        COALESCE(SUM(harga - harga_beli), 0) as profit,
                        COALESCE(COUNT(kode), 0) as jumlah_transaksi
                    FROM transaksi 
                    WHERE kode_reseller = :reseller_kode
                """)
                
                profit_result = db.session.execute(
                    profit_query, 
                    {'reseller_kode': downline_kode}
                ).fetchone()

                profit_downline = float(profit_result[0] or 0)
                jumlah_transaksi = int(profit_result[1] or 0)
                total_profit_upline += profit_downline
                
                print(f"      Transactions: {jumlah_transaksi}, Profit: {profit_downline}")

                downline_data.append({
                    "kode": downline_kode,
                    "nama": downline_nama,
                    "jumlah_transaksi": jumlah_transaksi,
                    "total_profit": profit_downline,
                })

            hasil.append({
                "upline": {
                    "kode": root_kode,
                    "nama": root_nama,
                    "total_profit": float(total_profit_upline),
                },
                "downlines": downline_data,
            })

        print(f"\nReturning {len(hasil)} results")
        return hasil
        
    except Exception as e:
        print(f"Error in get_reseller_hierarchy_with_profit: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

# ======================== PERIOD FILTER ========================

def _get_period_range(period: str, year=None, month=None, day=None, week=None):
    """Hitung range waktu berdasarkan period (day|month|week)"""
    try:
        if period == "day":
            if not day:
                raise ValueError("day harus diisi format YYYY-MM-DD")
            start = datetime.strptime(day, "%Y-%m-%d")
            end = start + timedelta(days=1)

        elif period == "month":
            if not year or not month:
                raise ValueError("year dan month harus diisi untuk period=month")
            start = datetime(year, month, 1)
            days_in_month = calendar.monthrange(year, month)[1]
            end = start + timedelta(days=days_in_month)

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

# ======================== INSENTIF CALCULATION ========================

def calculate_insentif(profit):
    """
    Hitung insentif berdasarkan skema:
    - 0-3jt: 0 (basic salary 3jt)
    - 3jt-10jt: Q1 10%
    - 10jt-15jt: Q2 20% 
    - 15jt-20jt: Q3 30%
    - 20jt-25jt: Q4 40%
    - 25jt+: Q5 50%
    - Bonus ekstra 700rb jika profit > 10jt
    """
    if profit <= 3_000_000:
        return {
            "basic_salary": 3_000_000,
            "q1": 0,
            "q2": 0,
            "q3": 0,
            "q4": 0,
            "q5": 0,
            "bonus_ekstra": 0,
            "total_insentif": 0,
            "total_salary": 3_000_000
        }
    
    basic_salary = 3_000_000
    q1 = q2 = q3 = q4 = q5 = 0
    bonus_ekstra = 0
    
    # Q1: 3jt - 10jt (10%)
    if profit > 3_000_000:
        q1_max = min(profit, 10_000_000)
        q1 = (q1_max - 3_000_000) * 0.10
    
    # Q2: 10jt - 15jt (20%)
    if profit > 10_000_000:
        q2_max = min(profit, 15_000_000)
        q2 = (q2_max - 10_000_000) * 0.20
    
    # Q3: 15jt - 20jt (30%)
    if profit > 15_000_000:
        q3_max = min(profit, 20_000_000)
        q3 = (q3_max - 15_000_000) * 0.30
    
    # Q4: 20jt - 25jt (40%)
    if profit > 20_000_000:
        q4_max = min(profit, 25_000_000)
        q4 = (q4_max - 20_000_000) * 0.40
    
    # Q5: 25jt+ (50%)
    if profit > 25_000_000:
        q5 = (profit - 25_000_000) * 0.50
    
    # Bonus ekstra jika profit > 10jt
    if profit > 10_000_000:
        bonus_ekstra = 700_000
    
    total_insentif = q1 + q2 + q3 + q4 + q5 + bonus_ekstra
    total_salary = basic_salary + total_insentif
    
    return {
        "basic_salary": basic_salary,
        "q1": q1,
        "q2": q2,
        "q3": q3,
        "q4": q4,
        "q5": q5,
        "bonus_ekstra": bonus_ekstra,
        "total_insentif": total_insentif,
        "total_salary": total_salary
    }

# ======================== HELPER FUNCTIONS FOR ACTIVITY CHECK ========================

def _count_active_resellers(reseller_codes, start_dt, end_dt):
    """
    Hitung reseller aktif berdasarkan kriteria:
    1. Pernah melakukan minimal 3 transaksi dalam sehari
    2. Tidak ada gap 15 hari berturut-turut tanpa transaksi
    """
    if not reseller_codes:
        return 0
    
    active_count = 0
    
    try:
        for reseller_code in reseller_codes:
            # Query dengan raw SQL untuk lebih aman
            daily_trx_query = text("""
                SELECT 
                    DATE(tgl_entri) as trx_date,
                    COUNT(kode) as daily_count
                FROM transaksi 
                WHERE kode_reseller = :reseller_code
                    AND tgl_entri >= :start_dt
                    AND tgl_entri <= :end_dt
                GROUP BY DATE(tgl_entri)
            """)
            
            trx_results = db.session.execute(daily_trx_query, {
                'reseller_code': reseller_code,
                'start_dt': start_dt,
                'end_dt': end_dt
            }).fetchall()
            
            if not trx_results:
                continue
                
            daily_transactions = {row[0]: row[1] for row in trx_results}
            
            # Cek kriteria 1: apakah ada hari dengan >= 3 transaksi
            has_min_daily_trx = any(count >= 3 for count in daily_transactions.values())
            
            if not has_min_daily_trx:
                continue
                
            # Cek kriteria 2: apakah tidak ada gap 15 hari tanpa transaksi
            if _has_no_15_day_gap(daily_transactions, start_dt, end_dt):
                active_count += 1
        
        return active_count
    except Exception as e:
        print(f"Error in _count_active_resellers: {str(e)}")
        return 0

def _count_acquisition_active_resellers(reseller_codes, start_dt, end_dt):
    """
    Hitung reseller akuisisi aktif:
    1. Memiliki >= 3 total transaksi dalam periode
    2. Memenuhi kriteria aktif
    """
    if not reseller_codes:
        return 0
    
    try:
        # Buat placeholder untuk IN clause
        placeholders = ','.join([f':code_{i}' for i in range(len(reseller_codes))])
        params = {f'code_{i}': code for i, code in enumerate(reseller_codes)}
        params.update({
            'start_dt': start_dt,
            'end_dt': end_dt
        })
        
        min_trx_query = text(f"""
            SELECT kode_reseller
            FROM transaksi 
            WHERE kode_reseller IN ({placeholders})
                AND tgl_entri >= :start_dt
                AND tgl_entri <= :end_dt
            GROUP BY kode_reseller
            HAVING COUNT(kode) >= 3
        """)
        
        qualified_results = db.session.execute(min_trx_query, params).fetchall()
        qualified_resellers = [r[0] for r in qualified_results]
        
        if not qualified_resellers:
            return 0
        
        return _count_active_resellers(qualified_resellers, start_dt, end_dt)
    except Exception as e:
        print(f"Error in _count_acquisition_active_resellers: {str(e)}")
        return 0

def _has_no_15_day_gap(daily_transactions, start_dt, end_dt):
    """Cek apakah tidak ada gap 15 hari berturut-turut tanpa transaksi"""
    if not daily_transactions:
        return False
    
    try:
        transaction_dates = sorted(daily_transactions.keys())
        
        # Cek gap dari start_dt ke transaksi pertama
        first_trx_date = transaction_dates[0]
        if (first_trx_date - start_dt.date()).days >= 15:
            return False
        
        # Cek gap antar transaksi
        for i in range(len(transaction_dates) - 1):
            current_date = transaction_dates[i]
            next_date = transaction_dates[i + 1]
            gap_days = (next_date - current_date).days - 1
            
            if gap_days >= 15:
                return False
        
        # Cek gap dari transaksi terakhir ke end_dt
        last_trx_date = transaction_dates[-1]
        if (end_dt.date() - last_trx_date).days >= 15:
            return False
        
        return True
    except Exception as e:
        print(f"Error in _has_no_15_day_gap: {str(e)}")
        return False

# ======================== MAIN SUMMARY ========================

def get_reseller_summary_custom(period="month", year=None, month=None, day=None, week=None, page=1, limit=100):
    try:
        start_dt, end_dt = _get_period_range(period, year, month, day, week)
        offset = (page - 1) * limit
        dialect = db.engine.dialect.name.lower()
        print(f"Database dialect: {dialect}")

        if dialect == "mssql":  # SQL Server pakai OFFSET-FETCH
            root_query = text("""
                SELECT kode, nama 
                FROM reseller 
                WHERE kode_upline IS NULL OR kode_upline = '' OR kode_upline = '0'
                ORDER BY kode
                OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
            """)
        else:  # MySQL, PostgreSQL, SQLite pakai LIMIT OFFSET
            root_query = text("""
                SELECT kode, nama 
                FROM reseller 
                WHERE kode_upline IS NULL OR kode_upline = '' OR kode_upline = '0'
                ORDER BY kode
                LIMIT :limit OFFSET :offset
            """)

        root_results = db.session.execute(root_query, {"offset": offset, "limit": limit}).fetchall()
        
        hasil = []
        for root_row in root_results:
            root_kode, root_nama = root_row
            downline_query = text("SELECT kode FROM reseller WHERE kode_upline = :upline_kode")
            downline_results = db.session.execute(downline_query, {"upline_kode": root_kode}).fetchall()
            downline_codes = [r[0] for r in downline_results]

            jmlh_trx = total_omset = total_profit = 0.0
            jmlh_trx_aktif = akuisisi_aktif = 0

            if downline_codes:
                placeholders = ",".join([f":code_{i}" for i in range(len(downline_codes))])
                params = {f"code_{i}": code for i, code in enumerate(downline_codes)}
                params.update({"start_dt": start_dt, "end_dt": end_dt})

                trx_summary_query = text(f"""
                    SELECT 
                        COALESCE(COUNT(kode), 0) as jumlah,
                        COALESCE(SUM(harga), 0) as omset,
                        COALESCE(SUM(harga - harga_beli), 0) as profit
                    FROM transaksi 
                    WHERE kode_reseller IN ({placeholders})
                        AND tgl_entri >= :start_dt
                        AND tgl_entri <= :end_dt
                """)
                trx_result = db.session.execute(trx_summary_query, params).fetchone()
                jmlh_trx = int(trx_result[0] or 0)
                total_omset = float(trx_result[1] or 0)
                total_profit = float(trx_result[2] or 0)

                jmlh_trx_aktif = _count_active_resellers(downline_codes, start_dt, end_dt)
                akuisisi_aktif = _count_acquisition_active_resellers(downline_codes, start_dt, end_dt)

            akuisisi = len(downline_codes)
            insentif_detail = calculate_insentif(total_profit)

            dto = {
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
            print(f"[DEBUG] Reseller Summary DTO: {dto}")  # log ke terminal
            hasil.append(dto)

        return hasil
        

    except Exception as e:
        print(f"Error in get_reseller_summary_custom: {str(e)}")
        return {
            "status": "error",
            "message": "Terjadi kesalahan saat mengambil data summary",
            "error": str(e),
            "data": []
        }

def get_self_summary(token, period="month", year=None, month=None, day=None, week=None):
    try:
        payload = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
        kode = payload["sub"]
        
        # Cek user dengan raw query
        user_query = text("SELECT kode, nama FROM reseller WHERE kode = :kode")
        user_result = db.session.execute(user_query, {'kode': kode}).fetchone()
        
        if not user_result:
            return {"error": f"Reseller {kode} tidak ditemukan"}

        start_dt, end_dt = _get_period_range(period, year, month, day, week)

        root_kode = user_result[0]
        root_nama = user_result[1]
        
        # Ambil downlines
        downline_query = text("SELECT kode FROM reseller WHERE kode_upline = :upline_kode")
        downline_results = db.session.execute(downline_query, {'upline_kode': root_kode}).fetchall()
        downline_codes = [r[0] for r in downline_results]

        jmlh_trx = jmlh_trx_aktif = 0
        total_omset = total_profit = 0.0
        akuisisi_aktif = 0

        if downline_codes:
            placeholders = ','.join([f':code_{i}' for i in range(len(downline_codes))])
            params = {f'code_{i}': code for i, code in enumerate(downline_codes)}
            params.update({'start_dt': start_dt, 'end_dt': end_dt})

            trx_summary_query = text(f"""
                SELECT 
                    COALESCE(COUNT(kode), 0) as jumlah,
                    COALESCE(SUM(harga), 0) as omset,
                    COALESCE(SUM(harga - harga_beli), 0) as profit
                FROM transaksi 
                WHERE kode_reseller IN ({placeholders})
                    AND tgl_entri >= :start_dt
                    AND tgl_entri <= :end_dt
            """)

            trx_result = db.session.execute(trx_summary_query, params).fetchone()
            jmlh_trx = int(trx_result[0] or 0)
            total_omset = float(trx_result[1] or 0)
            total_profit = float(trx_result[2] or 0)

            jmlh_trx_aktif = _count_active_resellers(downline_codes, start_dt, end_dt)
            akuisisi_aktif = _count_acquisition_active_resellers(downline_codes, start_dt, end_dt)

        akuisisi = len(downline_codes)
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

def get_summary_by_week(year, month):
    """Ambil summary per minggu untuk semua upline (admin view)"""
    try:
        month_cal = calendar.Calendar(firstweekday=0).monthdatescalendar(year, month)
        results = []

        # Query root
        root_query = text("SELECT kode, nama FROM reseller WHERE kode_upline IS NULL OR kode_upline = '' OR kode_upline = '0'")
        root_results = db.session.execute(root_query).fetchall()

        for week_num, week_days in enumerate(month_cal, start=1):
            start_dt = datetime.combine(week_days[0], datetime.min.time())
            end_dt = datetime.combine(week_days[-1], datetime.max.time())

            for root_row in root_results:
                root_kode = root_row[0]
                root_nama = root_row[1]
                
                # Ambil downlines
                downline_query = text("SELECT kode FROM reseller WHERE kode_upline = :upline_kode")
                downline_results = db.session.execute(downline_query, {'upline_kode': root_kode}).fetchall()
                downline_codes = [r[0] for r in downline_results]

                jmlh_trx = jmlh_trx_aktif = 0
                total_omset = total_profit = 0.0
                akuisisi_aktif = 0

                if downline_codes:
                    placeholders = ','.join([f':code_{i}' for i in range(len(downline_codes))])
                    params = {f'code_{i}': code for i, code in enumerate(downline_codes)}
                    params.update({'start_dt': start_dt, 'end_dt': end_dt})

                    trx_summary_query = text(f"""
                        SELECT 
                            COALESCE(COUNT(kode), 0) as jumlah,
                            COALESCE(SUM(harga), 0) as omset,
                            COALESCE(SUM(harga - harga_beli), 0) as profit
                        FROM transaksi 
                        WHERE kode_reseller IN ({placeholders})
                            AND tgl_entri >= :start_dt
                            AND tgl_entri <= :end_dt
                    """)

                    trx_result = db.session.execute(trx_summary_query, params).fetchone()
                    jmlh_trx = int(trx_result[0] or 0)
                    total_omset = float(trx_result[1] or 0)
                    total_profit = float(trx_result[2] or 0)

                    jmlh_trx_aktif = _count_active_resellers(downline_codes, start_dt, end_dt)
                    akuisisi_aktif = _count_acquisition_active_resellers(downline_codes, start_dt, end_dt)

                akuisisi = len(downline_codes)
                insentif_detail = calculate_insentif(total_profit)

                results.append({
                    "id_upline": root_kode,
                    "nama_upline": root_nama,
                    "week": week_num,
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
                })

        return results
    except Exception as e:
        print(f"Error in get_summary_by_week: {str(e)}")
        return []

def compare_months(year1, month1, year2, month2):
    """Bandingkan summary bulan1 vs bulan2 (per minggu, per upline)"""
    try:
        data1 = get_summary_by_week(year1, month1)
        data2 = get_summary_by_week(year2, month2)

        comparison = {}
        
        # Process data1 first
        for d in data1:
            key = (d["id_upline"], d["week"])
            comparison[key] = {
                "upline": {
                    "id": d["id_upline"],
                    "nama": d["nama_upline"],
                    "week": d["week"]
                },
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

        # Process data2
        for d in data2:
            key = (d["id_upline"], d["week"])
            month2_data = {
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
                    "upline": {
                        "id": d["id_upline"],
                        "nama": d["nama_upline"],
                        "week": d["week"]
                    },
                    "month1": {
                        "jmlh_trx": 0,
                        "jmlh_trx_aktif": 0,
                        "akuisisi": 0,
                        "akuisisi_aktif": 0,
                        "omset": 0,
                        "profit": 0,
                        "insentif": 0,
                        "insentif_detail": {},
                    },
                    "month2": month2_data,
                }
            else:
                comparison[key]["month2"] = month2_data

        return list(comparison.values())
    except Exception as e:
        print(f"Error in compare_months: {str(e)}")
        return []

# ======================== UTILITY FUNCTIONS ========================

def get_reseller_activity_detail(reseller_code, start_dt, end_dt):
    """Fungsi untuk debugging - melihat detail aktivitas reseller"""
    try:
        daily_trx_query = text("""
            SELECT 
                DATE(tgl_entri) as trx_date,
                COUNT(kode) as daily_count
            FROM transaksi 
            WHERE kode_reseller = :reseller_code
                AND tgl_entri >= :start_dt
                AND tgl_entri <= :end_dt
            GROUP BY DATE(tgl_entri)
            ORDER BY trx_date
        """)
        
        trx_results = db.session.execute(daily_trx_query, {
            'reseller_code': reseller_code,
            'start_dt': start_dt,
            'end_dt': end_dt
        }).fetchall()
        
        daily_transactions = {row[0]: row[1] for row in trx_results}
        has_min_daily = any(count >= 3 for count in daily_transactions.values())
        has_no_gap = _has_no_15_day_gap(daily_transactions, start_dt, end_dt)
        
        return {
            "reseller_code": reseller_code,
            "transaction_dates": [(str(row[0]), row[1]) for row in trx_results],
            "has_min_daily_trx": has_min_daily,
            "has_no_15_day_gap": has_no_gap,
            "is_active": has_min_daily and has_no_gap
        }
    except Exception as e:
        print(f"Error in get_reseller_activity_detail: {str(e)}")
        return {
            "reseller_code": reseller_code,
            "error": str(e)
        }