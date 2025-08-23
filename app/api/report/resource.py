from flask_restx import Resource, Namespace
from flask import request
from .dto import ReportDto
from . import controller as ctrl

api = ReportDto.api

# ================= EXISTING =================

@api.route("/hierarchy")
class ReportHierarchy(Resource):
    @api.marshal_with(ReportDto.response_hierarchy)
    def get(self):
        """Ambil struktur upline–downline beserta profit transaksi"""
        data = ctrl.get_reseller_hierarchy_with_profit()
        if not data:
            return {"status": "error", "message": "Tidak ada data ditemukan", "data": []}, 404
        return {"status": "success", "message": "Laporan hierarchy berhasil diambil", "data": data}, 200


@api.route("/reseller/summary/custom")
class ResellerSummaryCustomResource(Resource):
    @api.marshal_list_with(ReportDto.reseller_summary_dto)
    def get(self):
        """Ambil ringkasan reseller dengan filter hari/bulan/minggu"""
        period = request.args.get("period", "month")
        year = request.args.get("year", type=int)
        month = request.args.get("month", type=int)
        day = request.args.get("day")
        week = request.args.get("week", type=int)

        data = ctrl.get_reseller_summary_custom(period=period, year=year, month=month, day=day, week=week)
        return data, 200

# ================= NEW =================

@api.route("/self/summary")
class SelfSummaryResource(Resource):
    @api.marshal_with(ReportDto.self_summary_dto)
    def get(self):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return {"message": "Token tidak ada"}, 401

        token = auth_header.split(" ")[1]

        """Ambil ringkasan khusus untuk upline login (self only)"""
        period = request.args.get("period", "month")
        year = request.args.get("year", type=int)
        month = request.args.get("month", type=int)
        day = request.args.get("day")
        week = request.args.get("week", type=int)

        data = ctrl.get_self_summary(token, period=period, year=year, month=month, day=day, week=week)
        return data, 200


@api.route("/admin/summary/week")
class WeeklySummaryResource(Resource):
    @api.marshal_list_with(ReportDto.weekly_summary_dto)
    def get(self):
        """Ambil ringkasan per minggu untuk semua upline"""
        year = request.args.get("year", type=int)
        month = request.args.get("month", type=int)

        data = ctrl.get_summary_by_week(year, month)
        return data, 200


@api.route("/admin/summary/compare")
class CompareSummaryResource(Resource):
    @api.marshal_list_with(ReportDto.monthly_compare_dto)
    def get(self):
        """Bandingkan 2 bulan (per minggu)"""
        year1 = request.args.get("year1", type=int)
        month1 = request.args.get("month1", type=int)
        year2 = request.args.get("year2", type=int)
        month2 = request.args.get("month2", type=int)

        data = ctrl.compare_months(year1, month1, year2, month2)
        return data, 200
