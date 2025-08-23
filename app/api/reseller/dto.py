from flask_restx import Namespace, fields

class ResellerDto:
    api = Namespace('reseller', description='API untuk manajemen reseller')

    reseller_basic = api.model('ResellerBasic', {
        'kode': fields.String(description='Kode unik reseller'),
        'nama': fields.String(description='Nama reseller'),
        'kode_level': fields.String(description='Level reseller (MASTER/AGEN/DEALER)'),
        'aktif': fields.Boolean(description='Status aktif reseller'),
        'nama_pemilik': fields.String(description='Nama pemilik reseller'),
        'nomor_hp': fields.String(description='Nomor HP reseller'),
        'alamat': fields.String(description='Alamat reseller'),
    })

    reseller_detail = api.model('ResellerDetail', {
        'kode': fields.String,
        'nama': fields.String,
        'saldo': fields.Integer(description='Saldo reseller'),
        'alamat': fields.String,
        'aktif': fields.Boolean,
        'kode_upline': fields.String(description='Kode upline reseller'),
        'kode_level': fields.String,
        'nama_pemilik': fields.String,
        'nomor_hp': fields.String,
        'email': fields.String,
        'tgl_daftar': fields.DateTime,
        'saldo_minimal': fields.Integer,
        'markup': fields.Integer(description='Markup harga untuk reseller ini'),
        'poin': fields.Integer,
        'komisi': fields.Integer,
    })

    statistik = api.model('Statistik', {
        'transaksi_bulan_ini': fields.Integer,
        'omset_bulan_ini': fields.Integer,
        'komisi_bulan_ini': fields.Integer,
        'jumlah_downline': fields.Integer,
    })

    reseller_dengan_statistik = api.model('ResellerDenganStatistik', {
        'reseller': fields.Nested(reseller_detail),
        'statistik': fields.Nested(statistik),
    })

    top_reseller = api.model('TopReseller', {
        'kode': fields.String,
        'nama': fields.String,
        'kode_level': fields.String,
        'total_omset': fields.Integer,
        'total_transaksi': fields.Integer,
        'total_komisi': fields.Integer,
        'periode': fields.String,
    })