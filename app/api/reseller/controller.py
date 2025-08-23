from app.models import Reseller, Transaksi
from app.database import db
from sqlalchemy import func, desc
import datetime

def get_all_resellers():
    """Mendapatkan semua reseller"""
    resellers = Reseller.query.filter_by(deleted=False).all()
    return resellers

def get_reseller_by_kode(kode):
    """Mendapatkan reseller berdasarkan kode"""
    reseller = Reseller.query.filter_by(kode=kode, deleted=False).first()
    return reseller

def get_reseller_dengan_statistik(kode):
    """Mendapatkan reseller dengan statistik transaksi"""
    reseller = get_reseller_by_kode(kode)
    if not reseller:
        return None
    
    # Hitung statistik transaksi bulan ini
    now = datetime.datetime.now()
    start_bulan = datetime.datetime(now.year, now.month, 1)
    
    stats_bulan_ini = db.session.query(
        func.count(Transaksi.kode).label('total_transaksi'),
        func.sum(Transaksi.harga).label('total_omset'),
        func.sum(Transaksi.komisi).label('total_komisi')
    ).filter(
        Transaksi.kode_reseller == kode,
        Transaksi.tgl_entri >= start_bulan,
        Transaksi.status == 'SUCCESS'
    ).first()
    
    # Hitung jumlah downline (anak reseller)
    jumlah_downline = Reseller.query.filter_by(
        kode_upline=kode, deleted=False
    ).count()
    
    return {
        'reseller': reseller,
        'statistik': {
            'transaksi_bulan_ini': stats_bulan_ini.total_transaksi or 0,
            'omset_bulan_ini': stats_bulan_ini.total_omset or 0,
            'komisi_bulan_ini': stats_bulan_ini.total_komisi or 0,
            'jumlah_downline': jumlah_downline
        }
    }

def get_resellers_by_level(level):
    """Mendapatkan reseller berdasarkan level"""
    resellers = Reseller.query.filter_by(
        kode_level=level, deleted=False
    ).all()
    return resellers

def get_downline_resellers(kode_upline):
    """Mendapatkan reseller downline dari seorang upline"""
    downlines = Reseller.query.filter_by(
        kode_upline=kode_upline, deleted=False
    ).all()
    return downlines

def get_top_resellers_by_omset(limit=10, bulan=None, tahun=None):
    """Mendapatkan top reseller berdasarkan omset"""
    if bulan and tahun:
        start_date = datetime.datetime(tahun, bulan, 1)
        if bulan == 12:
            end_date = datetime.datetime(tahun + 1, 1, 1)
        else:
            end_date = datetime.datetime(tahun, bulan + 1, 1)
    else:
        # Bulan ini
        now = datetime.datetime.now()
        start_date = datetime.datetime(now.year, now.month, 1)
        if now.month == 12:
            end_date = datetime.datetime(now.year + 1, 1, 1)
        else:
            end_date = datetime.datetime(now.year, now.month + 1, 1)
    
    top_resellers = db.session.query(
        Reseller.kode,
        Reseller.nama,
        Reseller.kode_level,
        func.sum(Transaksi.harga).label('total_omset'),
        func.count(Transaksi.kode).label('total_transaksi'),
        func.sum(Transaksi.komisi).label('total_komisi')
    ).join(
        Transaksi, Reseller.kode == Transaksi.kode_reseller
    ).filter(
        Transaksi.tgl_entri >= start_date,
        Transaksi.tgl_entri < end_date,
        Transaksi.status == 'SUCCESS',
        Reseller.deleted == False
    ).group_by(
        Reseller.kode, Reseller.nama, Reseller.kode_level
    ).order_by(
        desc('total_omset')
    ).limit(limit).all()
    
    return [
        {
            'kode': row.kode,
            'nama': row.nama,
            'kode_level': row.kode_level,
            'total_omset': row.total_omset or 0,
            'total_transaksi': row.total_transaksi or 0,
            'total_komisi': row.total_komisi or 0,
            'periode': f"{start_date.strftime('%B %Y')}"
        }
        for row in top_resellers
    ]