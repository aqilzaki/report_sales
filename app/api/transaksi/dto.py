from flask_restx import Namespace, fields

class TransaksiDto:
    api = Namespace('transaksi', description='API untuk transaksi')

    transaksi_basic = api.model('TransaksiBasic', {
        'kode': fields.String(description='Kode unik transaksi'),
        'tgl_entri': fields.DateTime(description='Tanggal transaksi'),
        'kode_produk': fields.String(description='Kode produk'),
        'tujuan': fields.String(description='Nomor tujuan'),
        'kode_reseller': fields.String(description='Kode reseller'),
        'harga': fields.Integer(description='Harga transaksi'),
        'status': fields.String(description='Status transaksi'),
        'komisi': fields.Integer(description='Komisi yang didapat'),
        'sn': fields.String(description='Serial number (jika success)'),
    })

    transaksi_detail = api.model('TransaksiDetail', {
        'kode': fields.String,
        'tgl_entri': fields.DateTime,
        'kode_produk': fields.String,
        'tujuan': fields.String,
        'kode_reseller': fields.String,
        'harga': fields.Integer,
        'harga_beli': fields.Integer,
        'status': fields.String,
        'tgl_status': fields.DateTime,
        'komisi': fields.Integer,
        'poin': fields.Integer,
        'sn': fields.String,
        'penerima': fields.String,
        'qty': fields.Integer,
        'is_voucher': fields.Boolean,
        'keterangan': fields.String,
    })

    ringkasan_status = api.model('RingkasanStatus', {
        'status': fields.String,
        'jumlah': fields.Integer,
        'total_harga': fields.Integer,
        'total_komisi': fields.Integer,
    })

    produk_populer = api.model('ProdukPopuler', {
        'kode_produk': fields.String,
        'jumlah_transaksi': fields.Integer,
        'total_omset': fields.Integer,
    })

    summary_transaksi = api.model('SummaryTransaksi', {
        'periode': fields.String,
        'ringkasan_status': fields.List(fields.Nested(ringkasan_status)),
        'produk_populer': fields.List(fields.Nested(produk_populer)),
    })

    top_reseller_harian = api.model('TopResellerHarian', {
        'kode': fields.String,
        'nama': fields.String,
        'jumlah_transaksi': fields.Integer,
        'total_omset': fields.Integer,
    })

    laporan_harian = api.model('LaporanHarian', {
        'tanggal': fields.String,
        'ringkasan_status': fields.List(fields.Nested(ringkasan_status)),
        'top_reseller': fields.List(fields.Nested(top_reseller_harian)),
    })