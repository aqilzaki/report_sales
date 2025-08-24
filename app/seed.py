import click
from flask.cli import with_appcontext
from .database import db
from .models import Reseller, Transaksi
import datetime
import random
import string
import calendar


def clear_data():
    meta = db.metadata
    for table in reversed(meta.sorted_tables):
        print(f'Menghapus tabel {table.name}...')
        db.session.execute(table.delete())
    db.session.commit()
    print('Semua data berhasil dihapus.')


def generate_code(prefix, length=6):
    random_part = ''.join(random.choices(string.digits, k=length))
    return f"{prefix}{random_part}"


def seed_data():
    print('Memulai proses seeding...')
    
    # ---- 1. Data Reseller (sama seperti sebelumnya) ----
    reseller_data = []

    for i in range(1, 10):
        reseller_data.append(
            Reseller(
                kode=f"RM{i:03d}",
                nama=f"Master Reseller {i}",
                saldo=random.randint(5_000_000, 20_000_000),
                alamat=f"Jl. Master {i} No.{i}",
                pin=str(random.randint(1000, 9999)),
                aktif=True,
                kode_upline=None,
                kode_level="MASTER",
                nama_pemilik=f"Pemilik Master {i}",
                nomor_hp=f"08{random.randint(1000000000,9999999999)}",
                email=f"master{i}@reseller.com",
                tgl_daftar=datetime.datetime.now() - datetime.timedelta(days=random.randint(200, 400)),
                saldo_minimal=100_000,
                markup=random.randint(500, 2000),
                poin=random.randint(1000, 3000),
                komisi=0
            )
        )

    # AGEN
    agen_counter = 1
    for master in reseller_data[:3]:
        for j in range(10):
            kode = f"RSLA{agen_counter:03d}"
            reseller_data.append(
                Reseller(
                    kode=kode,
                    nama=f"Agen {agen_counter}",
                    saldo=random.randint(1_000_000, 5_000_000),
                    alamat=f"Jl. Agen {agen_counter}",
                    pin=str(random.randint(1000, 9999)),
                    aktif=True,
                    kode_upline=master.kode,
                    kode_level="AGEN",
                    nama_pemilik=f"Pemilik Agen {agen_counter}",
                    nomor_hp=f"08{random.randint(1000000000,9999999999)}",
                    email=f"agen{agen_counter}@reseller.com",
                    tgl_daftar=datetime.datetime.now() - datetime.timedelta(days=random.randint(50, 200)),
                    saldo_minimal=50_000,
                    markup=random.randint(500, 1500),
                    poin=random.randint(200, 1000),
                    komisi=random.randint(10_000, 200_000)
                )
            )
            agen_counter += 1

    # DEALER
    dealer_counter = 1
    agen_resellers = [r for r in reseller_data if r.kode_level == "AGEN"]
    for agen in agen_resellers:
        for k in range(5):
            kode = f"RSLD{dealer_counter:03d}"
            reseller_data.append(
                Reseller(
                    kode=kode,
                    nama=f"Dealer {dealer_counter}",
                    saldo=random.randint(200_000, 2_000_000),
                    alamat=f"Jl. Dealer {dealer_counter}",
                    pin=str(random.randint(1000, 9999)),
                    aktif=True,
                    kode_upline=agen.kode,
                    kode_level="DEALER",
                    nama_pemilik=f"Pemilik Dealer {dealer_counter}",
                    nomor_hp=f"08{random.randint(1000000000,9999999999)}",
                    email=f"dealer{dealer_counter}@reseller.com",
                    tgl_daftar=datetime.datetime.now() - datetime.timedelta(days=random.randint(10, 100)),
                    saldo_minimal=20_000,
                    markup=random.randint(500, 2000),
                    poin=random.randint(50, 500),
                    komisi=random.randint(5_000, 50_000)
                )
            )
            dealer_counter += 1

    db.session.bulk_save_objects(reseller_data)
    print(f'{len(reseller_data)} data Reseller ditambahkan.')

    # ---- 2. Data Transaksi (khusus 1 bulan penuh) ----
    produk_list = [
        {'kode': 'TEL5', 'harga': 5500, 'harga_beli': 5000},
        {'kode': 'TEL10', 'harga': 10750, 'harga_beli': 10000},
        {'kode': 'TEL20', 'harga': 20500, 'harga_beli': 19500},
        {'kode': 'TEL50', 'harga': 49500, 'harga_beli': 48500},
        {'kode': 'IND5', 'harga': 5400, 'harga_beli': 4900},
        {'kode': 'IND10', 'harga': 10600, 'harga_beli': 9950},
        {'kode': 'IND25', 'harga': 24500, 'harga_beli': 24000},
        {'kode': 'XL10', 'harga': 10800, 'harga_beli': 10100},
        {'kode': 'XL25', 'harga': 24800, 'harga_beli': 24200},
        {'kode': 'AXIS5', 'harga': 5200, 'harga_beli': 4800}
    ]
    nomor_hp_list = [f"08{random.randint(1000000000,9999999999)}" for _ in range(200)]
    status_list = ['20', '40']
    reseller_codes = [r.kode for r in reseller_data]

    transaksi_data = []

    # Tentukan bulan sekarang
    today = datetime.date.today()
    first_day = today.replace(day=1)
    last_day = today.replace(day=calendar.monthrange(today.year, today.month)[1])

    num_trx = 3000  # total transaksi sebulan
    for i in range(num_trx):
        produk = random.choice(produk_list)
        reseller_code = random.choice(reseller_codes)
        nomor_tujuan = random.choice(nomor_hp_list)
        status = random.choice(status_list)

        # pilih tanggal random dalam bulan ini
        random_day = first_day + datetime.timedelta(days=random.randint(0, (last_day - first_day).days))
        random_time = datetime.timedelta(seconds=random.randint(0, 86400))  # acak jam
        random_date = datetime.datetime.combine(random_day, datetime.time()) + random_time

        saldo_awal = random.randint(1_000_000, 10_000_000)
        profit = produk['harga'] - produk['harga_beli']
        komisi = int(profit * 0.05)

        transaksi_data.append(
            Transaksi(
                kode=generate_code('TRX', 10),
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
                sn=generate_code('SN', 12) if status == '20' else None,
                penerima=nomor_tujuan,
                qty=1,
                is_voucher=False,
                komisi=komisi if status == '20' else 0,
                poin=random.randint(1, 10) if status == '20' else 0,
                hide_kiosk=False
            )
        )

    db.session.bulk_save_objects(transaksi_data)
    print(f'{len(transaksi_data)} data Transaksi ditambahkan untuk bulan {today.strftime("%B %Y")}.')

    db.session.commit()
    print('Seeding selesai!')


@click.command('seed')
@with_appcontext
def seed_command():
    """Menghapus data lama dan mengisi database dengan data dummy (1 bulan terakhir)."""
    clear_data()
    seed_data()
