from flask_restx import Namespace, fields

class LaporanSalesDto:
    api = Namespace('laporan', description='API untuk laporan sales')

    sales_info = api.model('SalesInfo', {
        'id_mr': fields.String,
        'nama_mr': fields.String,
    })

    laporan_output = api.model('LaporanOutput', {
        'sales_info': fields.Nested(sales_info),
        'periode': fields.String,
        'omset_total': fields.Integer,
        'jumlah_transaksi': fields.Integer,
        'jumlah_outlet_aktif': fields.Integer,
        'profit': fields.Integer,
        'gaji': fields.Integer,
    })