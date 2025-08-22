from flask import Blueprint, jsonify, request
from models import db, Sales, ReportTransaksi, Outlet, KondisiOutlet, KodeInsentif
from schemas import LaporanSalesSchema
from sqlalchemy import func
import datetime

# --- ASUMSI DAN KONSTANTA UNTUK RUMUS ---
# Anda bisa memindahkan ini ke file konfigurasi atau tabel database
PROFIT_MARGIN = 0.20  # Asumsi profit adalah 20% dari omset
GAJI_POKOK_SALES = 3000000  # Asumsi gaji pokok per bulan
ID_KONDISI_OUTLET_AKTIF = 'K01' # Asumsi ID untuk kondisi 'Aktif' di tabel kondisi_outlet

# Inisialisasi skema
laporan_schema = LaporanSalesSchema()


def get_laporan_sales(id_mr):

    """
    Endpoint untuk mendapatkan laporan keuangan lengkap untuk seorang sales.
    Menerima query parameter `bulan` dan `tahun` (contoh: ?bulan=8&tahun=2025).
    """
    try:
        # Ambil query parameter bulan dan tahun
        bulan = int(request.args.get('bulan', datetime.datetime.now().month))
        tahun = int(request.args.get('tahun', datetime.datetime.now().year))
    except ValueError:
        return jsonify({"error": "Parameter bulan dan tahun harus berupa angka"}), 400

    # 1. Validasi Sales
    sales = Sales.query.get(id_mr)
    if not sales:
        return jsonify({"error": f"Sales dengan ID '{id_mr}' tidak ditemukan"}), 404

    # --- KUMPULAN QUERY & RUMUS PERHITUNGAN ---

    # 2. Hitung Omset Total & Jumlah Transaksi
    # Query ke tabel report_transaksi, filter berdasarkan id_mr dan periode waktu.
    # Kolom create_at diasumsikan Unix Timestamp.
    start_timestamp = int(datetime.datetime(tahun, bulan, 1).timestamp())
    # Cari akhir bulan
    next_month = datetime.datetime(tahun, bulan, 1).replace(day=28) + datetime.timedelta(days=4)
    end_timestamp = int(next_month.replace(day=1).timestamp())

    query_transaksi = db.session.query(
        func.sum(ReportTransaksi.transaksi).label('total_omset'),
        func.count(ReportTransaksi.id_trx).label('total_transaksi')
    ).filter(
        ReportTransaksi.id_mr == id_mr,
        ReportTransaksi.create_at >= start_timestamp,
        ReportTransaksi.create_at < end_timestamp
    ).first()

    omset_total = query_transaksi.total_omset if query_transaksi.total_omset else 0
    jumlah_transaksi = query_transaksi.total_transaksi if query_transaksi.total_transaksi else 0
    
    # 3. Hitung Jumlah Outlet Aktif
    # Query ke tabel outlet, filter berdasarkan id_mr dan id_kondisi_outlet
    jumlah_outlet_aktif = Outlet.query.filter_by(
        id_mr=id_mr,
        id_kondisi_outlet=ID_KONDISI_OUTLET_AKTIF
    ).count()

    # 4. Hitung Profit
    # Rumus: Profit = Omset Total * Margin Profit
    profit = int(omset_total * PROFIT_MARGIN)

    # 5. Hitung Gaji
    # Rumus: Gaji = Gaji Pokok + (Profit * Persentase Insentif)
    # Di sini kita asumsikan setiap sales punya 1 kode insentif default.
    # Dalam kasus nyata, ini bisa lebih kompleks.
    # Untuk contoh ini, kita hardcode persentase insentif 10%
    persentase_insentif = 0.10 
    insentif = int(profit * persentase_insentif)
    gaji = GAJI_POKOK_SALES + insentif

    # --- Persiapan Respon JSON ---
    
    # Gabungkan semua hasil perhitungan ke dalam satu dictionary
    hasil_laporan = {
        "sales_info": {"id_mr": sales.id_mr, "nama_mr": sales.nama_mr},
        "periode": f"{datetime.date(1900, bulan, 1).strftime('%B')} {tahun}",
        "omset_total": omset_total,
        "jumlah_transaksi": jumlah_transaksi,
        "jumlah_outlet_aktif": jumlah_outlet_aktif,
        "profit": profit,
        "gaji": gaji
    }
    
    # Serialisasi hasil menggunakan Marshmallow schema untuk output yang bersih
    return laporan_schema.dump(hasil_laporan), 200
