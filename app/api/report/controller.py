from app.models import Reseller, Transaksi
from app.database import db
from sqlalchemy import func, case
from datetime import datetime, timedelta, date
import calendar


def get_reseller_hierarchy_with_profit():
    """Ambil semua reseller root, cek downline, dan hitung profit per downline lalu akumulasi ke upline"""
    roots = Reseller.query.filter(
        (Reseller.kode_upline == None) | (Reseller.kode_upline == "")
    ).all()

    hasil = []
    for root in roots:
        downlines = Reseller.query.filter_by(kode_upline=root.kode).all()

        downline_data = []
        total_profit_upline = 0

        for d in downlines:
            transaksi_summary = db.session.query(
                func.sum(Transaksi.harga - Transaksi.harga_beli).label("profit"),
                func.count(Transaksi.kode).label("jumlah_transaksi"),
            ).filter(Transaksi.kode_reseller == d.kode).first()

            profit_downline = transaksi_summary.profit or 0
            total_profit_upline += profit_downline

            downline_data.append({
                "kode": d.kode,
                "nama": d.nama,
                "jumlah_transaksi": transaksi_summary.jumlah_transaksi or 0,
                "total_profit": profit_downline,
            })

        hasil.append({
            "upline": {
                "kode": root.kode,
                "nama": root.nama,
                "total_profit": total_profit_upline,
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


# ======================== MAIN SUMMARY ========================

def get_reseller_summary_custom(period="month", year=None, month=None, day=None, week=None):
    """Ringkasan transaksi reseller dengan filter period (day|month|week)"""
    start_dt, end_dt = _get_period_range(period, year, month, day, week)

    roots = Reseller.query.filter(
        (Reseller.kode_upline == None) | (Reseller.kode_upline == "")
    ).all()

    hasil = []
    for root in roots:
        downlines = Reseller.query.filter_by(kode_upline=root.kode).all()
        downline_codes = [d.kode for d in downlines]

        jmlh_trx = jmlh_trx_aktif = 0
        total_omset = total_profit = 0.0

        if downline_codes:
            base_filters = [
                Transaksi.kode_reseller.in_(downline_codes),
                Transaksi.tgl_entri >= start_dt,
                Transaksi.tgl_entri <= end_dt,
            ]

            trx_summary = db.session.query(
                func.count(Transaksi.kode).label("jumlah"),
                func.sum(case((Transaksi.status == "SUCCESS", 1), else_=0)).label("jumlah_aktif"),
                func.sum(Transaksi.harga).label("omset"),
                func.sum(Transaksi.harga - Transaksi.harga_beli).label("profit"),
            ).filter(*base_filters).first()

            jmlh_trx = int(trx_summary.jumlah or 0)
            jmlh_trx_aktif = int(trx_summary.jumlah_aktif or 0)
            total_omset = float(trx_summary.omset or 0)
            total_profit = float(trx_summary.profit or 0)

            akuisisi_aktif = db.session.query(
                func.count(func.distinct(Transaksi.kode_reseller))
            ).filter(*base_filters).scalar() or 0
        else:
            akuisisi_aktif = 0

        akuisisi = len(downlines)
        insentif = total_profit * 0.10

        hasil.append({
            "id_upline": root.kode,
            "nama_upline": root.nama,
            "periode": period,
            "jmlh_trx": jmlh_trx,
            "jmlh_trx_aktif": jmlh_trx_aktif,
            "akuisisi": akuisisi,
            "akuisisi_aktif": int(akuisisi_aktif),
            "omset": total_omset,
            "profit_upline": total_profit,
            "insentif": insentif,
            "start": start_dt.isoformat(timespec="seconds"),
            "end": end_dt.isoformat(timespec="seconds"),
        })

    return hasil

def get_self_summary(reseller_kode, period="month", year=None, month=None, day=None, week=None):
    """Ringkasan transaksi untuk 1 upline saja (self)"""
    start_dt, end_dt = _get_period_range(period, year, month, day, week)

    root = Reseller.query.filter_by(kode=reseller_kode).first()
    if not root:
        return {"error": f"Reseller {reseller_kode} tidak ditemukan"}

    downlines = Reseller.query.filter_by(kode_upline=root.kode).all()
    downline_codes = [d.kode for d in downlines]

    jmlh_trx = jmlh_trx_aktif = 0
    total_omset = total_profit = 0.0

    if downline_codes:
        base_filters = [
            Transaksi.kode_reseller.in_(downline_codes),
            Transaksi.tgl_entri >= start_dt,
            Transaksi.tgl_entri <= end_dt,
        ]

        trx_summary = db.session.query(
            func.count(Transaksi.kode).label("jumlah"),
            func.sum(case((Transaksi.status == "SUCCESS", 1), else_=0)).label("jumlah_aktif"),
            func.sum(Transaksi.harga).label("omset"),
            func.sum(Transaksi.harga - Transaksi.harga_beli).label("profit"),
        ).filter(*base_filters).first()

        jmlh_trx = int(trx_summary.jumlah or 0)
        jmlh_trx_aktif = int(trx_summary.jumlah_aktif or 0)
        total_omset = float(trx_summary.omset or 0)
        total_profit = float(trx_summary.profit or 0)

        akuisisi_aktif = db.session.query(
            func.count(func.distinct(Transaksi.kode_reseller))
        ).filter(*base_filters).scalar() or 0
    else:
        akuisisi_aktif = 0

    akuisisi = len(downlines)
    insentif = total_profit * 0.10

    return {
        "id_upline": root.kode,
        "nama_upline": root.nama,
        "periode": period,
        "jmlh_trx": jmlh_trx,
        "jmlh_trx_aktif": jmlh_trx_aktif,
        "akuisisi": akuisisi,
        "akuisisi_aktif": int(akuisisi_aktif),
        "omset": total_omset,
        "profit_upline": total_profit,
        "insentif": insentif,
        "start": start_dt.isoformat(timespec="seconds"),
        "end": end_dt.isoformat(timespec="seconds"),
    }


def get_summary_by_week(year, month):
    """Ambil summary per minggu untuk semua upline"""
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

            if not downline_codes:
                continue

            base_filters = [
                Transaksi.kode_reseller.in_(downline_codes),
                Transaksi.tgl_entri >= start_dt,
                Transaksi.tgl_entri <= end_dt,
            ]

            trx_summary = db.session.query(
                func.count(Transaksi.kode).label("jumlah"),
                func.sum(case((Transaksi.status == "SUCCESS", 1), else_=0)).label("jumlah_aktif"),
                func.sum(Transaksi.harga).label("omset"),
                func.sum(Transaksi.harga - Transaksi.harga_beli).label("profit"),
            ).filter(*base_filters).first()

            results.append({
                "id_upline": root.kode,
                "nama_upline": root.nama,
                "week": week_num,
                "jmlh_trx": int(trx_summary.jumlah or 0),
                "jmlh_trx_aktif": int(trx_summary.jumlah_aktif or 0),
                "omset": float(trx_summary.omset or 0),
                "profit_upline": float(trx_summary.profit or 0),
            })

    return results



def compare_months(year1, month1, year2, month2):
    """Bandingkan summary bulan1 vs bulan2 (per minggu)"""
    data1 = get_summary_by_week(year1, month1)
    data2 = get_summary_by_week(year2, month2)

    comparison = {}
    for d in data1:
        key = (d["id_upline"], d["week"])
        comparison[key] = {
            "upline": d["nama_upline"],
            "month1": {"trx": d["jmlh_trx"], "omset": d["omset"], "profit": d["profit_upline"]},
            "month2": {"trx": 0, "omset": 0, "profit": 0},
        }

    for d in data2:
        key = (d["id_upline"], d["week"])
        if key not in comparison:
            comparison[key] = {
                "upline": d["nama_upline"],
                "month1": {"trx": 0, "omset": 0, "profit": 0},
                "month2": {"trx": d["jmlh_trx"], "omset": d["omset"], "profit": d["profit_upline"]},
            }
        else:
            comparison[key]["month2"] = {"trx": d["jmlh_trx"], "omset": d["omset"], "profit": d["profit_upline"]}

    return list(comparison.values())

