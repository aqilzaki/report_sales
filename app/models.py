from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Tabel-tabel berdasarkan ERD Anda dengan penambahan panjang string
class Sales(db.Model):
    __tablename__ = 'sales'
    # BERI PANJANG, contoh: 50 karakter
    id_mr = db.Column(db.String(50), primary_key=True)
    nama_mr = db.Column(db.String(100), nullable=False)

class KondisiOutlet(db.Model):
    __tablename__ = 'kondisi_outlet'
    id = db.Column(db.String(50), primary_key=True)
    kondisi = db.Column(db.String(100), nullable=False)

class Outlet(db.Model):
    __tablename__ = 'outlet'
    id_tm = db.Column(db.String(50), primary_key=True)
    nama_tm = db.Column(db.String(100))
    id_kondisi_outlet = db.Column(db.String(50), db.ForeignKey('kondisi_outlet.id'))
    lokasi = db.Column(db.String(255)) # Lokasi bisa lebih panjang
    id_mr = db.Column(db.String(50), db.ForeignKey('sales.id_mr'))
    transaksi = db.Column(db.BigInteger)

class ReportTransaksi(db.Model):
    __tablename__ = 'report_transaksi'
    id_trx = db.Column(db.String(50), primary_key=True)
    id_mr = db.Column(db.String(50), db.ForeignKey('sales.id_mr'))
    id_tm = db.Column(db.String(50), db.ForeignKey('outlet.id_tm'))
    transaksi = db.Column(db.BigInteger, nullable=False, default=0)
    create_at = db.Column(db.BigInteger)

class KodeInsentif(db.Model):
    __tablename__ = 'kode_insentif'
    id_insentif = db.Column(db.String(50), primary_key=True)
    kode = db.Column(db.String(50))
    persentase = db.Column(db.Float, nullable=False, default=0.0)