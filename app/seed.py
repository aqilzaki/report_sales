import click
from flask.cli import with_appcontext
from .database import db
from .models import Reseller, Transaksi
import datetime
import random
import string

# Fungsi untuk menghapus semua data yang ada (membersihkan tabel)
def clear_data():
    meta = db.metadata
    for table in reversed(meta.sorted_tables):
        print(f'Menghapus tabel {table.name}...')
        db.session.execute(table.delete())
    db.session.commit()
    print('Semua data berhasil dihapus.')

# Fungsi untuk generate kode random
def generate_code(prefix, length=6):
    random_part = ''.join(random.choices(string.digits, k=length))
    return f"{prefix}{random_part}"

# Fungsi utama untuk seeding
def seed_data():
    print('Memulai proses seeding...')
    
    # -- 1. Buat Data Reseller --
    reseller_data = [
        Reseller(
            kode='RSL001',
            nama='Toko Maju Jaya',
            saldo=5000000,
            alamat='Jl. Merdeka No. 123, Jakarta',
            pin='1234',
            aktif=True,
            kode_upline=None,  # Master reseller
            kode_level='MASTER',
            nama_pemilik='Budi Santoso',
            nomor_hp='081234567890',
            email='budi@tokomaju.com',
            tgl_daftar=datetime.datetime.now() - datetime.timedelta(days=365),
            saldo_minimal=100000,
            markup=500,
            poin=1250,
            komisi=0
        ),
        Reseller(
            kode='RSL002',
            nama='Warung Berkah Cell',
            saldo=2500000,
            alamat='Jl. Sudirman No. 45, Bandung',
            pin='5678',
            aktif=True,
            kode_upline='RSL001',
            kode_level='AGEN',
            nama_pemilik='Siti Nurhaliza',
            nomor_hp='082345678901',
            email='siti@berkahcell.com',
            tgl_daftar=datetime.datetime.now() - datetime.timedelta(days=180),
            saldo_minimal=50000,
            markup=750,
            poin=625,
            komisi=125000
        ),
        Reseller(
            kode='RSL003',
            nama='Counter Sejahtera',
            saldo=1000000,
            alamat='Jl. Ahmad Yani No. 78, Surabaya',
            pin='9012',
            aktif=True,
            kode_upline='RSL001',
            kode_level='DEALER',
            nama_pemilik='Ahmad Fadli',
            nomor_hp='083456789012',
            email='ahmad@sejahtera.com',
            tgl_daftar=datetime.datetime.now() - datetime.timedelta(days=90),
            saldo_minimal=25000,
            markup=1000,
            poin=250,
            komisi=75000
        ),
        Reseller(
            kode='RSL004',
            nama='Pulsa Murah Store',
            saldo=3200000,
            alamat='Jl. Diponegoro No. 12, Medan',
            pin='3456',
            aktif=True,
            kode_upline='RSL002',
            kode_level='AGEN',
            nama_pemilik='Rina Marlina',
            nomor_hp='084567890123',
            email='rina@pulsamurah.com',
            tgl_daftar=datetime.datetime.now() - datetime.timedelta(days=60),
            saldo_minimal=30000,
            markup=600,
            poin=480,
            komisi=95000
        ),
        Reseller(
            kode='RSL005',
            nama='Handphone Center',
            saldo=750000,
            alamat='Jl. Pahlawan No. 56, Yogyakarta',
            pin='7890',
            aktif=False,  # Tidak aktif
            kode_upline='RSL003',
            kode_level='DEALER',
            nama_pemilik='Joko Widodo',
            nomor_hp='085678901234',
            email='joko@hpcenter.com',
            tgl_daftar=datetime.datetime.now() - datetime.timedelta(days=30),
            saldo_minimal=20000,
            markup=1200,
            poin=50,
            komisi=25000
        )
    ]
    
    db.session.bulk_save_objects(reseller_data)
    print(f'{len(reseller_data)} data Reseller ditambahkan.')

    # -- 2. Buat Data Transaksi --
    # Produk-produk yang tersedia
    produk_list = [
        {'kode': 'TEL5', 'nama': 'Telkomsel 5K', 'harga': 5500, 'harga_beli': 5000},
        {'kode': 'TEL10', 'nama': 'Telkomsel 10K', 'harga': 10750, 'harga_beli': 10000},
        {'kode': 'TEL20', 'nama': 'Telkomsel 20K', 'harga': 20500, 'harga_beli': 19500},
        {'kode': 'TEL50', 'nama': 'Telkomsel 50K', 'harga': 49500, 'harga_beli': 48500},
        {'kode': 'IND5', 'nama': 'Indosat 5K', 'harga': 5400, 'harga_beli': 4900},
        {'kode': 'IND10', 'nama': 'Indosat 10K', 'harga': 10600, 'harga_beli': 9950},
        {'kode': 'IND25', 'nama': 'Indosat 25K', 'harga': 24500, 'harga_beli': 24000},
        {'kode': 'XL10', 'nama': 'XL 10K', 'harga': 10800, 'harga_beli': 10100},
        {'kode': 'XL25', 'nama': 'XL 25K', 'harga': 24800, 'harga_beli': 24200},
        {'kode': 'AXIS5', 'nama': 'Axis 5K', 'harga': 5200, 'harga_beli': 4800}
    ]
    
    nomor_hp_list = [
        '081234567890', '082345678901', '083456789012', '084567890123', 
        '085678901234', '087890123456', '088901234567', '089012345678',
        '081987654321', '082876543210', '083765432109', '084654321098'
    ]
    
    status_list = ['SUCCESS', 'PENDING', 'FAILED', 'PROCESS']
    
    reseller_codes = ['RSL001', 'RSL002', 'RSL003', 'RSL004', 'RSL005']
    
    transaksi_data = []
    
    # Generate 100 transaksi untuk 3 bulan terakhir
    start_date = datetime.datetime.now() - datetime.timedelta(days=90)
    end_date = datetime.datetime.now()
    
    for i in range(100):
        # Pilih data secara acak
        produk = random.choice(produk_list)
        reseller_code = random.choice(reseller_codes)
        nomor_tujuan = random.choice(nomor_hp_list)
        status = random.choice(status_list)
        
        # Buat tanggal random dalam 3 bulan terakhir
        random_date = start_date + datetime.timedelta(
            seconds=random.randint(0, int((end_date - start_date).total_seconds()))
        )
        
        # Hitung saldo awal random (simulasi)
        saldo_awal = random.randint(1000000, 10000000)
        
        # Komisi (5% dari selisih harga jual - harga beli)
        profit = produk['harga'] - produk['harga_beli']
        komisi = int(profit * 0.05)
        
        transaksi = Transaksi(
            kode=generate_code('TRX', 8),
            tgl_entri=random_date,
            kode_produk=produk['kode'],
            tujuan=nomor_tujuan,
            kode_reseller=reseller_code,
            pengirim='SYSTEM',
            tipe_pengirim='AUTO',
            harga=produk['harga'],
            status=status,
            tgl_status=random_date + datetime.timedelta(seconds=random.randint(1, 300)),
            harga_beli=produk['harga_beli'],
            saldo_awal=saldo_awal,
            perintah=f"{produk['kode']}.{nomor_tujuan}",
            counter=random.randint(1, 5),
            sn=generate_code('SN', 12) if status == 'SUCCESS' else None,
            penerima=nomor_tujuan,
            qty=1,
            is_voucher=False,
            komisi=komisi if status == 'SUCCESS' else 0,
            poin=random.randint(1, 10) if status == 'SUCCESS' else 0,
            hide_kiosk=False
        )
        transaksi_data.append(transaksi)
    
    db.session.bulk_save_objects(transaksi_data)
    print(f'{len(transaksi_data)} data Transaksi ditambahkan.')

    # Commit semua perubahan ke database
    db.session.commit()
    print('Seeding selesai!')


# Perintah kustom untuk CLI Flask
@click.command('seed')
@with_appcontext
def seed_command():
    """Menghapus data lama dan mengisi database dengan data dummy."""
    clear_data()
    seed_data()