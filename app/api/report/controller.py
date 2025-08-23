from app.models import Reseller, Transaksi
from app.database import db
from sqlalchemy import func, case
from decimal import Decimal




def get_reseller_hierarchy_with_profit():
    """Ambil semua reseller root, cek downline, dan hitung profit per downline lalu akumulasi ke upline"""
    roots = Reseller.query.filter(
        (Reseller.kode_upline == None) | (Reseller.kode_upline == '')
    ).all()

    hasil = []
    for root in roots:
        downlines = Reseller.query.filter_by(kode_upline=root.kode).all()

        downline_data = []
        total_profit_upline = 0

        for d in downlines:
            transaksi_summary = db.session.query(
                func.sum(Transaksi.harga - Transaksi.harga_beli).label('profit'),
                func.count(Transaksi.kode).label('jumlah_transaksi')
            ).filter(Transaksi.kode_reseller == d.kode).first()

            profit_downline = transaksi_summary.profit or 0
            total_profit_upline += profit_downline

            downline_data.append({
                "kode": d.kode,
                "nama": d.nama,
                "jumlah_transaksi": transaksi_summary.jumlah_transaksi or 0,
                "total_profit": profit_downline
            })

        hasil.append({
            "upline": {
                "kode": root.kode,
                "nama": root.nama,
                "total_profit": total_profit_upline
            },
            "downlines": downline_data
        })

    return hasil


def get_reseller_summary():
    """
    Menghasilkan ringkasan per upline:
    id_upline | nama_upline | jmlh_trx | jmlh_trx_aktif | akuisisi | akuisisi_aktif | omset | profit_upline | insentif
    """
    roots = Reseller.query.filter(
        (Reseller.kode_upline == None) | (Reseller.kode_upline == '')
    ).all()

    hasil = []
    for root in roots:
        downlines = Reseller.query.filter_by(kode_upline=root.kode).all()
        downline_codes = [d.kode for d in downlines]

        jmlh_trx = 0
        jmlh_trx_aktif = 0
        total_omset = 0
        total_profit = 0

        if downline_codes:
            trx_summary = db.session.query(
                func.count(Transaksi.kode).label("jumlah"),
                func.sum(case((Transaksi.status == "SUCCESS", 1), else_=0)).label("jumlah_aktif"),
                func.sum(Transaksi.harga).label("omset"),
                func.sum(Transaksi.harga - Transaksi.harga_beli).label("profit")
            ).filter(Transaksi.kode_reseller.in_(downline_codes)).first()

            jmlh_trx = int(trx_summary.jumlah or 0)
            jmlh_trx_aktif = int(trx_summary.jumlah_aktif or 0)
            total_omset = float(trx_summary.omset or 0)
            total_profit = float(trx_summary.profit or 0)

        akuisisi = len(downlines)
        akuisisi_aktif = len([d for d in downlines if d.aktif])

        insentif = total_profit * 0.10  # sudah float

        hasil.append({
            "id_upline": root.kode,
            "nama_upline": root.nama,
            "jmlh_trx": jmlh_trx,
            "jmlh_trx_aktif": jmlh_trx_aktif,
            "akuisisi": akuisisi,
            "akuisisi_aktif": akuisisi_aktif,
            "omset": total_omset,
            "profit_upline": total_profit,
            "insentif": insentif
        })

    return hasil

