from app.models import Reseller, Transaksi
from app.database import db
from sqlalchemy import func, desc, and_
import datetime

def get_transaksi_by_reseller(kode_reseller, limit=50, status=None, start_date=None, end_date=None):
    """Mendapatkan transaksi berdasarkan kode reseller"""
    query = Transaksi.query.filter_by(kode_reseller=kode_reseller)
    
    if status:
        query = query.filter_by(status=status)
    
    if start_date:
        query = query.filter(Transaksi.tgl_entri >= start_date)
    
    if end_date:
        query = query.filter(Transaksi.tgl_entri <= end_date)
    
    transaksi = query.order_by(desc(Transaksi.tgl_entri)).limit(limit).all()
    return transaksi

def get_transaksi_summary_by_reseller(kode_reseller, bulan=None, tahun=None):
    """Mendapatkan ringkasan transaksi reseller"""
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
    
    # Query ringkasan berdasarkan status
    summary = db.session.query(
        Transaksi.status,
        func.count(Transaksi.kode).label('jumlah'),
        func.sum(Transaksi.harga).label('total_harga'),
        func.sum(Transaksi.komisi).label('total_komisi')
    ).filter(
        and_(
            Transaksi.kode_reseller == kode_reseller,
            Transaksi.tgl_entri >= start_date,
            Transaksi.tgl_entri < end_date
        )
    ).group_by(Transaksi.status).all()
    
    # Query produk terpopuler
    produk_populer = db.session.query(
        Transaksi.kode_produk,
        func.count(Transaksi.kode).label('jumlah_transaksi'),
        func.sum(Transaksi.harga).label('total_omset')
    ).filter(
        and_(
            Transaksi.kode_reseller == kode_reseller,
            Transaksi.tgl_entri >= start_date,
            Transaksi.tgl_entri < end_date,
            Transaksi.status == 'SUCCESS'
        )
    ).group_by(
        Transaksi.kode_produk
    ).order_by(
        desc('jumlah_transaksi')
    ).limit(5).all()
    
    return {
        'periode': f"{start_date.strftime('%B %Y')}",
        'ringkasan_status': [
            {
                'status': row.status,
                'jumlah': row.jumlah,
                'total_harga': row.total_harga or 0,
                'total_komisi': row.total_komisi or 0
            }
            for row in summary
        ],
        'produk_populer': [
            {
                'kode_produk': row.kode_produk,
                'jumlah_transaksi': row.jumlah_transaksi,
                'total_omset': row.total_omset or 0
            }
            for row in produk_populer
        ]
    }

def get_transaksi_recent(limit=20):
    """Mendapatkan transaksi terbaru"""
    transaksi = db.session.query(Transaksi).join(
        Reseller, Transaksi.kode_reseller == Reseller.kode
    ).order_by(desc(Transaksi.tgl_entri)).limit(limit).all()
    
    return transaksi

def get_transaksi_by_status(status, limit=50):
    """Mendapatkan transaksi berdasarkan status"""
    transaksi = Transaksi.query.filter_by(status=status).order_by(
        desc(Transaksi.tgl_entri)
    ).limit(limit).all()
    return transaksi

def get_laporan_harian(tanggal=None):
    """Mendapatkan laporan transaksi harian"""
    if not tanggal:
        tanggal = datetime.date.today()
    
    start_datetime = datetime.datetime.combine(tanggal, datetime.time.min)
    end_datetime = datetime.datetime.combine(tanggal, datetime.time.max)
    
    # Summary berdasarkan status
    summary = db.session.query(
        Transaksi.status,
        func.count(Transaksi.kode).label('jumlah'),
        func.sum(Transaksi.harga).label('total_harga'),
        func.sum(Transaksi.komisi).label('total_komisi')
    ).filter(
        and_(
            Transaksi.tgl_entri >= start_datetime,
            Transaksi.tgl_entri <= end_datetime
        )
    ).group_by(Transaksi.status).all()
    
    # Top reseller hari ini
    top_reseller = db.session.query(
        Reseller.kode,
        Reseller.nama,
        func.count(Transaksi.kode).label('jumlah_transaksi'),
        func.sum(Transaksi.harga).label('total_omset')
    ).join(
        Transaksi, Reseller.kode == Transaksi.kode_reseller
    ).filter(
        and_(
            Transaksi.tgl_entri >= start_datetime,
            Transaksi.tgl_entri <= end_datetime,
            Transaksi.status == 'SUCCESS'
        )
    ).group_by(
        Reseller.kode, Reseller.nama
    ).order_by(
        desc('total_omset')
    ).limit(10).all()
    
    return {
        'tanggal': tanggal.strftime('%Y-%m-%d'),
        'ringkasan_status': [
            {
                'status': row.status,
                'jumlah': row.jumlah,
                'total_harga': row.total_harga or 0,
                'total_komisi': row.total_komisi or 0
            }
            for row in summary
        ],
        'top_reseller': [
            {
                'kode': row.kode,
                'nama': row.nama,
                'jumlah_transaksi': row.jumlah_transaksi,
                'total_omset': row.total_omset or 0
            }
            for row in top_reseller
        ]
    }