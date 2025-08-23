from flask_restx import Resource
from .dto import ReportDto
from . import controller as ctrl

api = ReportDto.api
_response_hierarchy = ReportDto.response_hierarchy
_response_summary = ReportDto.response_summary

@api.route('/hierarchy')
class ReportHierarchy(Resource):
    @api.marshal_with(_response_hierarchy)
    def get(self):
        """Ambil struktur upline–downline beserta profit transaksi"""
        data = ctrl.get_reseller_hierarchy_with_profit()
        if not data:
            return {"status": "error", "message": "Tidak ada data ditemukan", "data": []}, 404
        return {"status": "success", "message": "Laporan hierarchy berhasil diambil", "data": data}, 200


@api.route('/summary')
class ReportSummary(Resource):
    @api.marshal_with(_response_summary)
    def get(self):
        """Ambil ringkasan per upline"""
        data = ctrl.get_reseller_summary()
        if not data:
            return {"status": "error", "message": "Tidak ada data ditemukan", "data": []}, 404
        return {"status": "success", "message": "Laporan summary berhasil diambil", "data": data}, 200
