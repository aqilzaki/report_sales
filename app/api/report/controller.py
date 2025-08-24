from app.models import Reseller, Transaksi
import jwt
from app.database import db
from sqlalchemy import func, case, and_, distinct
from datetime import datetime, timedelta, date
from flask import current_app
import calendar
from app.api.auth.controller import get_user_from_token

def get_reseller_hierarchy_with_profit():
    """Ambil semua reseller root, cek downline, dan hitung profit per downline lalu akumulasi ke upline"""
    roots = Reseller.query.filter(
        (Reseller.kode_upline == None) | (Reseller.kode_upline == "")
    ).all()

    hasil = []
    for root in roots:
        downlines = Reseller.query.filter_by(kode_upline=root.kode).all()

        downline_data = []
        total_profit_upline = 0.0

        for d in downlines:
            transaksi_summary = db.session.query(
                func.sum(Transaksi.harga - Transaksi.harga_beli).label("profit"),
                func.count(Transaksi.kode).label("jumlah_transaksi"),
            ).filter(Transaksi.kode_reseller == d.kode).first()

            profit_downline = float(transaksi_summary.profit or 0)
            total_profit_upline += profit_downline

            downline_data.append({
                "kode": d.kode,
                "nama": d.nama,
                "jumlah_transaksi": int(transaksi_summary.jumlah_transaksi or 0),
                "total_profit": profit_downline,
            })

        hasil.append({
            "upline": {
                "kode": root.kode,
                "nama": root.nama,
                "total_profit": float(total_profit_upline),
            },
            "downlines": downline_data,
        })

    return hasil

# ======================== PERIOD FILTER ========================

def _get_period_range(period: str, year=None, month=None, day=None, week=None):
    """Hitung range waktu berdasarkan period (day|month|week)"""
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

        # ambil minggu ke-n dari bulan tsb
        month_cal = calendar.Calendar(firstweekday=0).monthdatescalendar(year, month)  
        # firstweekday=0 berarti Senin
        if week < 1 or week > len(month_cal):
            raise ValueError(f"Bulan {month}/{year} hanya punya {len(month_cal)} minggu")

        week_days = month_cal[week - 1]
        start = datetime.combine(week_days[0], datetime.min.time())
        end = datetime.combine(week_days[-1], datetime.max.time())

    else:
        raise ValueError("period harus day|month|week")

    return start, end


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
    
    for reseller_code in reseller_codes:
        # Ambil semua tanggal transaksi reseller dalam periode dengan jumlah per hari
        trx_dates = db.session.query(
            func.date(Transaksi.tgl_entri).label('trx_date'),
            func.count(Transaksi.kode).label('daily_count')
        ).filter(
            Transaksi.kode_reseller == reseller_code,
            Transaksi.tgl_entri >= start_dt,
            Transaksi.tgl_entri <= end_dt
        ).group_by(
            func.date(Transaksi.tgl_entri)
        ).all()
        
        if not trx_dates:
            continue
            
        # Konversi ke dictionary untuk kemudahan akses
        daily_transactions = {row.trx_date: row.daily_count for row in trx_dates}
        
        # Cek kriteria 1: apakah ada hari dengan >= 3 transaksi
        has_min_daily_trx = any(count >= 3 for count in daily_transactions.values())
        
        if not has_min_daily_trx:
            continue
            
        # Cek kriteria 2: apakah tidak ada gap 15 hari tanpa transaksi
        if _has_no_15_day_gap(daily_transactions, start_dt, end_dt):
            active_count += 1
    
    return active_count


def _count_acquisition_active_resellers(reseller_codes, start_dt, end_dt):
    """
    Hitung reseller akuisisi aktif:
    1. Memiliki >= 3 total transaksi dalam periode
    2. Memenuhi kriteria aktif
    """
    if not reseller_codes:
        return 0
    
    # Ambil reseller dengan >= 3 transaksi total
    resellers_with_min_trx = db.session.query(
        Transaksi.kode_reseller
    ).filter(
        Transaksi.kode_reseller.in_(reseller_codes),
        Transaksi.tgl_entri >= start_dt,
        Transaksi.tgl_entri <= end_dt
    ).group_by(
        Transaksi.kode_reseller
    ).having(
        func.count(Transaksi.kode) >= 3
    ).all()
    
    qualified_resellers = [r.kode_reseller for r in resellers_with_min_trx]
    
    if not qualified_resellers:
        return 0
    
    # Dari yang qualified, hitung yang juga aktif
    return _count_active_resellers(qualified_resellers, start_dt, end_dt)


def _has_no_15_day_gap(daily_transactions, start_dt, end_dt):
    """
    Cek apakah tidak ada gap 15 hari berturut-turut tanpa transaksi
    """
    if not daily_transactions:
        return False
    
    # Konversi ke list tanggal yang terurut
    transaction_dates = sorted(daily_transactions.keys())
    
    # Cek gap dari start_dt ke transaksi pertama
    first_trx_date = transaction_dates[0]
    if (first_trx_date - start_dt.date()).days >= 15:
        return False
    
    # Cek gap antar transaksi
    for i in range(len(transaction_dates) - 1):
        current_date = transaction_dates[i]
        next_date = transaction_dates[i + 1]
        gap_days = (next_date - current_date).days - 1  # -1 karena tidak menghitung hari transaksi
        
        if gap_days >= 15:
            return False
    
    # Cek gap dari transaksi terakhir ke end_dt
    last_trx_date = transaction_dates[-1]
    if (end_dt.date() - last_trx_date).days >= 15:
        return False
    
    return True


# ======================== MAIN SUMMARY ========================

def get_reseller_summary_custom(period="month", year=None, month=None, day=None, week=None):
    """
    Ringkasan transaksi reseller dengan filter period (day|month|week).
    - Jumlah aktif = reseller yang melakukan minimal 3 transaksi/hari DAN tidak ada gap 15 hari tanpa transaksi
    - Akuisisi aktif = reseller yang melakukan >= 3 transaksi pada periode DAN memenuhi kriteria aktif
    """
    start_dt, end_dt = _get_period_range(period, year, month, day, week)

    roots = Reseller.query.filter(
        (Reseller.kode_upline == None) | (Reseller.kode_upline == "")
    ).all()

    hasil = []
    for root in roots:
        downlines = Reseller.query.filter_by(kode_upline=root.kode).all()
        downline_codes = [d.kode for d in downlines]

        jmlh_trx = total_omset = total_profit = 0.0
        jmlh_trx_aktif = akuisisi_aktif = 0

        if downline_codes:
            base_filters = [
                Transaksi.kode_reseller.in_(downline_codes),
                Transaksi.tgl_entri >= start_dt,
                Transaksi.tgl_entri <= end_dt,
            ]

            # summary transaksi keseluruhan
            trx_summary = db.session.query(
                func.count(Transaksi.kode).label("jumlah"),
                func.sum(Transaksi.harga).label("omset"),
                func.sum(Transaksi.harga - Transaksi.harga_beli).label("profit"),
            ).filter(*base_filters).first()

            jmlh_trx = int(trx_summary.jumlah or 0)
            total_omset = float(trx_summary.omset or 0)
            total_profit = float(trx_summary.profit or 0)

            # Hitung reseller aktif dengan kriteria baru
            jmlh_trx_aktif = _count_active_resellers(downline_codes, start_dt, end_dt)
            
            # Akuisisi aktif = reseller yang >= 3 transaksi DAN memenuhi kriteria aktif
            akuisisi_aktif = _count_acquisition_active_resellers(downline_codes, start_dt, end_dt)

        akuisisi = len(downlines)
        insentif = total_profit * 0.10

        hasil.append({
            "id_upline": root.kode,
            "nama_upline": root.nama,
            "periode": period,
            "jmlh_trx": jmlh_trx,
            "jmlh_trx_aktif": int(jmlh_trx_aktif),
            "akuisisi": akuisisi,
            "akuisisi_aktif": int(akuisisi_aktif),
            "omset": total_omset,
            "profit_upline": total_profit,
            "insentif": insentif,
            "start": start_dt.isoformat(timespec="seconds"),
            "end": end_dt.isoformat(timespec="seconds"),
        })

    return hasil


def get_self_summary(token, period="month", year=None, month=None, day=None, week=None):
    try:
        payload = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
        kode = payload["sub"]
        user = Reseller.query.filter_by(kode=kode).first()
        if not user:
            return {"error": f"Reseller {kode} tidak ditemukan"}

        # ======================== periode ========================
        start_dt, end_dt = _get_period_range(period, year, month, day, week)

        root = Reseller.query.filter_by(kode=kode).first()
        downlines = Reseller.query.filter_by(kode_upline=root.kode).all()
        downline_codes = [d.kode for d in downlines]

        jmlh_trx = jmlh_trx_aktif = 0
        total_omset = total_profit = 0.0
        akuisisi_aktif = 0

        if downline_codes:
            base_filters = [
                Transaksi.kode_reseller.in_(downline_codes),
                Transaksi.tgl_entri >= start_dt,
                Transaksi.tgl_entri <= end_dt,
            ]

            # summary transaksi
            trx_summary = db.session.query(
                func.count(Transaksi.kode).label("jumlah"),
                func.sum(Transaksi.harga).label("omset"),
                func.sum(Transaksi.harga - Transaksi.harga_beli).label("profit"),
            ).filter(*base_filters).first()

            jmlh_trx = int(trx_summary.jumlah or 0)
            total_omset = float(trx_summary.omset or 0)
            total_profit = float(trx_summary.profit or 0)

            # Hitung dengan kriteria aktivitas baru
            jmlh_trx_aktif = _count_active_resellers(downline_codes, start_dt, end_dt)
            akuisisi_aktif = _count_acquisition_active_resellers(downline_codes, start_dt, end_dt)

        akuisisi = len(downlines)
        insentif = total_profit * 0.10

        return {
            "id_upline": root.kode,
            "nama_upline": root.nama,
            "periode": period,
            "jmlh_trx": jmlh_trx,
            "jmlh_trx_aktif": int(jmlh_trx_aktif),
            "akuisisi": akuisisi,
            "akuisisi_aktif": int(akuisisi_aktif),
            "omset": total_omset,
            "profit_upline": total_profit,
            "insentif": insentif,
            "start": start_dt.isoformat(timespec="seconds"),
            "end": end_dt.isoformat(timespec="seconds"),
        }

    except Exception as e:
        return {"error": str(e)}


def get_summary_by_week(year, month):
    """Ambil summary per minggu untuk semua upline (admin view)"""
    month_cal = calendar.Calendar(firstweekday=0).monthdatescalendar(year, month)
    results = []

    for week_num, week_days in enumerate(month_cal, start=1):
        start_dt = datetime.combine(week_days[0], datetime.min.time())
        end_dt = datetime.combine(week_days[-1], datetime.max.time())

        roots = Reseller.query.filter(
            (Reseller.kode_upline == None) | (Reseller.kode_upline == "")
        ).all()

        for root in roots:
            downlines = Reseller.query.filter_by(kode_upline=root.kode).all()
            downline_codes = [d.kode for d in downlines]

            jmlh_trx = jmlh_trx_aktif = 0
            total_omset = total_profit = 0.0
            akuisisi_aktif = 0

            if downline_codes:
                base_filters = [
                    Transaksi.kode_reseller.in_(downline_codes),
                    Transaksi.tgl_entri >= start_dt,
                    Transaksi.tgl_entri <= end_dt,
                ]

                trx_summary = db.session.query(
                    func.count(Transaksi.kode).label("jumlah"),
                    func.sum(Transaksi.harga).label("omset"),
                    func.sum(Transaksi.harga - Transaksi.harga_beli).label("profit"),
                ).filter(*base_filters).first()

                jmlh_trx = int(trx_summary.jumlah or 0)
                total_omset = float(trx_summary.omset or 0)
                total_profit = float(trx_summary.profit or 0)

                # Hitung dengan kriteria aktivitas baru
                jmlh_trx_aktif = _count_active_resellers(downline_codes, start_dt, end_dt)
                akuisisi_aktif = _count_acquisition_active_resellers(downline_codes, start_dt, end_dt)

            akuisisi = len(downlines)
            insentif = total_profit * 0.10

            results.append({
                "id_upline": root.kode,
                "nama_upline": root.nama,
                "week": week_num,
                "jmlh_trx": jmlh_trx,
                "jmlh_trx_aktif": int(jmlh_trx_aktif),
                "akuisisi": akuisisi,
                "akuisisi_aktif": int(akuisisi_aktif),
                "omset": total_omset,
                "profit_upline": total_profit,
                "insentif": insentif,
                "start": start_dt.isoformat(timespec="seconds"),
                "end": end_dt.isoformat(timespec="seconds"),
            })

    return results


def compare_months(year1, month1, year2, month2):
    """Bandingkan summary bulan1 vs bulan2 (per minggu, per upline)"""
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
            },
            "month2": {
                "jmlh_trx": 0,
                "jmlh_trx_aktif": 0,
                "akuisisi": 0,
                "akuisisi_aktif": 0,
                "omset": 0,
                "profit": 0,
                "insentif": 0,
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
        }
        
        if key not in comparison:
            # Create new entry for uplines that only exist in month2
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
                },
                "month2": month2_data,
            }
        else:
            # Update existing entry
            comparison[key]["month2"] = month2_data

    return list(comparison.values())


# ======================== UTILITY FUNCTIONS ========================

def get_reseller_activity_detail(reseller_code, start_dt, end_dt):
    """
    Fungsi untuk debugging - melihat detail aktivitas reseller
    """
    trx_dates = db.session.query(
        func.date(Transaksi.tgl_entri).label('trx_date'),
        func.count(Transaksi.kode).label('daily_count')
    ).filter(
        Transaksi.kode_reseller == reseller_code,
        Transaksi.tgl_entri >= start_dt,
        Transaksi.tgl_entri <= end_dt
    ).group_by(
        func.date(Transaksi.tgl_entri)
    ).order_by('trx_date').all()
    
    daily_transactions = {row.trx_date: row.daily_count for row in trx_dates}
    has_min_daily = any(count >= 3 for count in daily_transactions.values())
    has_no_gap = _has_no_15_day_gap(daily_transactions, start_dt, end_dt)
    
    return {
        "reseller_code": reseller_code,
        "transaction_dates": [(str(row.trx_date), row.daily_count) for row in trx_dates],
        "has_min_daily_trx": has_min_daily,
        "has_no_15_day_gap": has_no_gap,
        "is_active": has_min_daily and has_no_gap
    }