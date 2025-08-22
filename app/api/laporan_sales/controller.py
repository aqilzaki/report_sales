from app.models import Sales, ReportTransaksi, Outlet
from app.database import db
from sqlalchemy import func
import datetime
from decimal import Decimal # <-- 1. TAMBAHKAN IMPORT INI

# --- KONSTANTA RUMUS BISNIS ---
# Gunakan Decimal untuk presisi keuangan
PROFIT_MARGIN = Decimal('0.20') # <-- 2. UBAH KE DECIMAL
GAJI_POKOK_SALES = 3000000
ID_KONDISI_OUTLET_AKTIF = 'K01' 
PERSENTASE_INSENTIF = Decimal('0.10') # <-- 3. UBAH KE DECIMAL JUGA

def get_laporan_sales(id_mr, bulan, tahun):
    sales = Sales.query.get(id_mr)
    if not sales:
        return None 

    start_dt = datetime.datetime(tahun, bulan, 1)
    next_month_start_dt = (start_dt.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
    start_timestamp = int(start_dt.timestamp())
    end_timestamp = int(next_month_start_dt.timestamp())

    q_transaksi = db.session.query(
        func.sum(ReportTransaksi.transaksi).label('total_omset'),
        func.count(ReportTransaksi.id_trx).label('total_transaksi')
    ).filter(
        ReportTransaksi.id_mr == id_mr,
        ReportTransaksi.create_at.between(start_timestamp, end_timestamp - 1)
    ).first()

    omset = q_transaksi.total_omset or 0
    jml_transaksi = q_transaksi.total_transaksi or 0

    jml_outlet_aktif = Outlet.query.filter_by(
        id_mr=id_mr, id_kondisi_outlet=ID_KONDISI_OUTLET_AKTIF
    ).count()

    profit = int(omset * PROFIT_MARGIN)
    insentif = int(profit * PERSENTASE_INSENTIF)
    gaji = GAJI_POKOK_SALES + insentif

    return {
        "sales_info": sales,
        "periode": start_dt.strftime('%B %Y'),
        "omset_total": omset,
        "jumlah_transaksi": jml_transaksi,
        "jumlah_outlet_aktif": jml_outlet_aktif,
        "profit": profit,
        "gaji": gaji
    }

def all_report_sales(bulan, tahun):
    start_dt = datetime.datetime(tahun, bulan, 1)
    next_month_start_dt = (start_dt.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
    start_timestamp = int(start_dt.timestamp())
    end_timestamp = int(next_month_start_dt.timestamp())

    q_transaksi = db.session.query(
        ReportTransaksi.id_mr,
        func.sum(ReportTransaksi.transaksi).label('total_omset'),
        func.count(ReportTransaksi.id_trx).label('total_transaksi')
    ).filter(
        ReportTransaksi.create_at.between(start_timestamp, end_timestamp - 1)
    ).group_by(ReportTransaksi.id_mr).all()

    laporan = []
    for row in q_transaksi:
        sales = Sales.query.get(row.id_mr)
        if not sales:
            continue

        jml_outlet_aktif = Outlet.query.filter_by(
            id_mr=row.id_mr, id_kondisi_outlet=ID_KONDISI_OUTLET_AKTIF
        ).count()

        profit = int(row.total_omset * PROFIT_MARGIN)
        insentif = int(profit * PERSENTASE_INSENTIF)
        gaji = GAJI_POKOK_SALES + insentif

        laporan.append({
            "sales_info": sales,
            "periode": start_dt.strftime('%B %Y'),
            "omset_total": row.total_omset or 0,
            "jumlah_transaksi": row.total_transaksi or 0,
            "jumlah_outlet_aktif": jml_outlet_aktif,
            "profit": profit,
            "gaji": gaji
        })
    return laporan