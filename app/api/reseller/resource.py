from flask_restx import Resource, reqparse
from .dto import ResellerDto
from . import controller as ctrl
import datetime

api = ResellerDto.api
_reseller_basic = ResellerDto.reseller_basic
_reseller_detail = ResellerDto.reseller_detail
_reseller_dengan_statistik = ResellerDto.reseller_dengan_statistik
_top_reseller = ResellerDto.top_reseller

# Parser untuk query parameters
parser_periode = reqparse.RequestParser()
parser_periode.add_argument('bulan', type=int, help='Bulan (1-12)')
parser_periode.add_argument('tahun', type=int, help='Tahun')
parser_periode.add_argument('limit', type=int, default=10, help='Jumlah data maksimal')

@api.route('')
class ResellerList(Resource):
    @api.marshal_list_with(_reseller_basic)
    def get(self):
        """Mendapatkan daftar semua reseller"""
        resellers = ctrl.get_all_resellers()
        return resellers

@api.route('/<string:kode>')
class ResellerDetail(Resource):
    @api.marshal_with(_reseller_dengan_statistik)
    def get(self, kode):
        """Mendapatkan detail reseller beserta statistik"""
        result = ctrl.get_reseller_dengan_statistik(kode)
        if not result:
            api.abort(404, f"Reseller dengan kode '{kode}' tidak ditemukan")
        return result

@api.route('/level/<string:level>')
class ResellerByLevel(Resource):
    @api.marshal_list_with(_reseller_basic)
    def get(self, level):
        """Mendapatkan reseller berdasarkan level (MASTER/AGEN/DEALER)"""
        resellers = ctrl.get_resellers_by_level(level.upper())
        return resellers

@api.route('/<string:kode>/downline')
class ResellerDownline(Resource):
    @api.marshal_list_with(_reseller_basic)
    def get(self, kode):
        """Mendapatkan daftar downline dari seorang reseller"""
        downlines = ctrl.get_downline_resellers(kode)
        return downlines

@api.route('/top-omset')
class TopResellerOmset(Resource):
    @api.expect(parser_periode)
    @api.marshal_list_with(_top_reseller)
    def get(self):
        """Mendapatkan top reseller berdasarkan omset"""
        args = parser_periode.parse_args()
        top_resellers = ctrl.get_top_resellers_by_omset(
            limit=args.get('limit', 10),
            bulan=args.get('bulan'),
            tahun=args.get('tahun')
        )
        return top_resellers