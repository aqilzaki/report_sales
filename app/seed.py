import click
from flask.cli import with_appcontext
from .database import db
from .models import Sales, KondisiOutlet, Outlet, ReportTransaksi, KodeInsentif
import time
import random
import datetime

# Fungsi untuk menghapus semua data yang ada (membersihkan tabel)
def clear_data():
    meta = db.metadata
    for table in reversed(meta.sorted_tables):
        print(f'Menghapus tabel {table.name}...')
        db.session.execute(table.delete())
    db.session.commit()
    print('Semua data berhasil dihapus.')

# Fungsi utama untuk seeding
def seed_data():
    print('Memulai proses seeding...')
    
    # -- 1. Buat Data Kondisi Outlet --
    kondisi_outlet_data = [
        KondisiOutlet(id='K01', kondisi='Aktif'),
        KondisiOutlet(id='K02', kondisi='Tidak Aktif'),
    ]
    db.session.bulk_save_objects(kondisi_outlet_data)
    print(f'{len(kondisi_outlet_data)} data KondisiOutlet ditambahkan.')

    # -- 2. Buat Data Sales --
    sales_data = [
        Sales(id_mr='MR001', nama_mr='Budi Santoso'),
        Sales(id_mr='MR002', nama_mr='Citra Lestari'),
        Sales(id_mr='MR003', nama_mr='Agus Setiawan'),
    ]
    db.session.bulk_save_objects(sales_data)
    print(f'{len(sales_data)} data Sales ditambahkan.')

    # -- 3. Buat Data Kode Insentif --
    kode_insentif_data = [
        KodeInsentif(id_insentif='INS01', kode='Q1', persentase=0.10),
        KodeInsentif(id_insentif='INS02', kode='Q2', persentase=0.20),
        KodeInsentif(id_insentif='INS03', kode='Q3', persentase=0.30),
        KodeInsentif(id_insentif='INS04', kode='Q4', persentase=0.40),
        KodeInsentif(id_insentif='INS05', kode='Q5', persentase=0.50),
    ]
    db.session.bulk_save_objects(kode_insentif_data)
    print(f'{len(kode_insentif_data)} data KodeInsentif ditambahkan.')

    # -- 4. Buat Data Outlet (Toko) --
    # Kita akan mengasosiasikan outlet dengan sales yang sudah dibuat
    outlet_data = [
        # Outlet milik Budi (MR001)
        Outlet(id_tm='TM01', nama_tm='Toko Maju Jaya', id_kondisi_outlet='K01', lokasi='Jl. Merdeka No. 1', id_mr='MR001'),
        Outlet(id_tm='TM02', nama_tm='Warung Berkah', id_kondisi_outlet='K01', lokasi='Jl. Pahlawan No. 2', id_mr='MR001'),
        Outlet(id_tm='TM03', nama_tm='Minimarket Sentosa', id_kondisi_outlet='K02', lokasi='Jl. Kemerdekaan No. 3', id_mr='MR001'),
        
        # Outlet milik Citra (MR002)
        Outlet(id_tm='TM04', nama_tm='Toko Sejahtera', id_kondisi_outlet='K01', lokasi='Jl. Sudirman No. 4', id_mr='MR002'),
        Outlet(id_tm='TM05', nama_tm='Kios Bahagia', id_kondisi_outlet='K01', lokasi='Jl. Diponegoro No. 5', id_mr='MR002'),
    ]
    db.session.bulk_save_objects(outlet_data)
    print(f'{len(outlet_data)} data Outlet ditambahkan.')

    # -- 5. Buat Data Report Transaksi (Data Acak) --
    # Kita akan buat 50 transaksi acak untuk bulan Agustus 2025
    transaksi_data = []
    outlets_mr001 = ['TM01', 'TM02']
    outlets_mr002 = ['TM04', 'TM05']
    
    # Tanggal di bulan Agustus 2025 (dalam format timestamp)
    start_date = datetime.datetime(2025, 8, 1)
    end_date = datetime.datetime(2025, 8, 31)

    for i in range(50):
        # Pilih sales secara acak
        sales_id = random.choice(['MR001', 'MR002'])
        outlet_id = random.choice(outlets_mr001) if sales_id == 'MR001' else random.choice(outlets_mr002)

        # Buat tanggal & waktu acak di bulan Agustus
        random_date = start_date + datetime.timedelta(
            seconds=random.randint(0, int((end_date - start_date).total_seconds()))
        )

        transaksi = ReportTransaksi(
            id_trx=f'TRX{202508000 + i}',
            id_mr=sales_id,
            id_tm=outlet_id,
            transaksi=random.randint(100000, 2000000), # Nilai transaksi acak
            create_at=int(random_date.timestamp())
        )
        transaksi_data.append(transaksi)

    db.session.bulk_save_objects(transaksi_data)
    print(f'{len(transaksi_data)} data ReportTransaksi ditambahkan.')

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