from flask_restx import Resource, reqparse
from .dto import TransaksiDto
from . import controller as ctrl
import datetime

api = TransaksiDto.api
_transaksi_basic = TransaksiDto.transaksi_basic
_transaksi_detail = TransaksiDto.transaksi_detail
_summary_transaksi = TransaksiDto.summary_transaksi
_laporan_harian = TransaksiDto.laporan_harian

# Parser untuk query parameters
parser_transaksi = reqparse.RequestParser()
parser_transaksi.add_argument('limit', type=int, default=50, help='Jumlah data maksimal')
parser_transaksi.add_argument('status', type=str, help='Filter berdasarkan status')
parser_transaksi.add_argument('start_date', type=str, help='Tanggal mulai (YYYY-MM-DD)')
parser_transaksi.add_argument('end_date', type=str, help='Tanggal akhir (YYYY-MM-DD)')

parser_summary = reqparse.RequestParser()
parser_summary.add_argument('bulan', type=int, help='Bulan (1-12)')
parser_summary.add_argument('tahun', type=int, help='Tahun')

parser_harian = reqparse.RequestParser()
parser_harian.add_argument('tanggal', type=str, help='Tanggal laporan (YYYY-MM-DD)')

@api.route('/reseller/<string:kode_reseller>')
class TransaksiByReseller(Resource):
    @api.expect(parser_transaksi)
    @api.marshal_list_with(_transaksi_basic)
    def get(self, kode_reseller):
        """Mendapatkan transaksi berdasarkan kode reseller"""
        args = parser_transaksi.parse_args()
        
        start_date = None
        end_date = None
        
        if args['start_date']:
            try:
                start_date = datetime.datetime.strptime(args['start_date'], '%Y-%m-%d')
            except ValueError:
                api.abort(400, "Format start_date salah. Gunakan YYYY-MM-DD")
        
        if args['end_date']:
            try:
                end_date = datetime.datetime.strptime(args['end_date'], '%Y-%m-%d')
            except ValueError:
                api.abort(400, "Format end_date salah. Gunakan YYYY-MM-DD")
        
        transaksi = ctrl.get_transaksi_by_reseller(
            kode_reseller=kode_reseller,
            limit=args['limit'],
            status=args['status'],
            start_date=start_date,
            end_date=end_date
        )
        return transaksi

@api.route('/reseller/<string:kode_reseller>/summary')
class TransaksiSummaryByReseller(Resource):
    @api.expect(parser_summary)
    @api.marshal_with(_summary_transaksi)
    def get(self, kode_reseller):
        """Mendapatkan ringkasan transaksi reseller"""
        args = parser_summary.parse_args()
        summary = ctrl.get_transaksi_summary_by_reseller(
            kode_reseller=kode_reseller,
            bulan=args.get('bulan'),
            tahun=args.get('tahun')
        )
        return summary

@api.route('/recent')
class TransaksiRecent(Resource):
    @api.expect(parser_transaksi)
    @api.marshal_list_with(_transaksi_basic)
    def get(self):
        """Mendapatkan transaksi terbaru"""
        args = parser_transaksi.parse_args()
        transaksi = ctrl.get_transaksi_recent(limit=args.get('limit', 20))
        return transaksi

@api.route('/status/<string:status>')
class TransaksiByStatus(Resource):
    @api.expect(parser_transaksi)
    @api.marshal_list_with(_transaksi_basic)
    def get(self, status):
        """Mendapatkan transaksi berdasarkan status"""
        args = parser_transaksi.parse_args()
        transaksi = ctrl.get_transaksi_by_status(
            status=status.upper(),
            limit=args.get('limit', 50)
        )
        return transaksi

@api.route('/laporan/harian')
class LaporanHarian(Resource):
    @api.expect(parser_harian)
    @api.marshal_with(_laporan_harian)
    def get(self):
        """Mendapatkan laporan transaksi harian"""
        args = parser_harian.parse_args()
        
        tanggal = None
        if args['tanggal']:
            try:
                tanggal = datetime.datetime.strptime(args['tanggal'], '%Y-%m-%d').date()
            except ValueError:
                api.abort(400, "Format tanggal salah. Gunakan YYYY-MM-DD")
        
        laporan = ctrl.get_laporan_harian(tanggal=tanggal)
        return laporan