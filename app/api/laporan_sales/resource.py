from flask import request
from flask_restx import Resource, reqparse
from .dto import LaporanSalesDto
from . import controller as ctrl
import datetime

api = LaporanSalesDto.api
_laporan_output = LaporanSalesDto.laporan_output

parser = reqparse.RequestParser()
parser.add_argument('bulan', type=int, default=datetime.datetime.now().month)
parser.add_argument('tahun', type=int, default=datetime.datetime.now().year)

@api.route('/sales/<string:id_mr>')
class LaporanSales(Resource):
    @api.expect(parser)
    @api.marshal_with(_laporan_output)
    def get(self, id_mr):
        """Mendapatkan laporan keuangan lengkap seorang sales."""
        args = parser.parse_args()
        laporan = ctrl.get_laporan_sales(id_mr, args['bulan'], args['tahun'])
        if not laporan:
            api.abort(404, f"Sales dengan ID '{id_mr}' tidak ditemukan.")
        return laporan
    
@api.route('/ping')
class Ping(Resource):
    def get(self):
        """Endpoint untuk memeriksa status API."""
        return {"message": "API is running"}, 200   