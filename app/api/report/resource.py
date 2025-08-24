from flask_restx import Resource, Namespace
from flask import request
from .dto import ReportDto
from . import controller as ctrl

api = ReportDto.api

# ================= EXISTING (UPDATED) =================

@api.route("/hierarchy")
class ReportHierarchy(Resource):
    @api.marshal_with(ReportDto.response_hierarchy)
    def get(self):
        """Ambil struktur upline–downline beserta profit transaksi"""
        try:
            data = ctrl.get_reseller_hierarchy_with_profit()
            if not data:
                return {
                    "status": "error", 
                    "message": "Tidak ada data ditemukan", 
                    "data": []
                }, 404
            return {
                "status": "success", 
                "message": "Laporan hierarchy berhasil diambil", 
                "data": data
            }, 200
        except Exception as e:
            return {
                "status": "error",
                "message": "Gagal mengambil data hierarchy",
                "error": str(e)
            }, 500


@api.route("/reseller/summary/custom")
class ResellerSummaryCustomResource(Resource):
    @api.marshal_with(ReportDto.response_reseller_summary)
    def get(self):
        """Ambil ringkasan reseller dengan filter hari/bulan/minggu"""
        try:
            period = request.args.get("period", "month")
            year = request.args.get("year", type=int)
            month = request.args.get("month", type=int)
            day = request.args.get("day")
            week = request.args.get("week", type=int)

            data = ctrl.get_reseller_summary_custom(
                period=period, year=year, month=month, day=day, week=week
            )
            
            return {
                "status": "success",
                "message": f"Data summary {period} berhasil diambil",
                "data": data
            }, 200
            
        except ValueError as e:
            return {
                "status": "error",
                "message": "Parameter tidak valid",
                "error": str(e)
            }, 400
        except Exception as e:
            return {
                "status": "error",
                "message": "Gagal mengambil data summary",
                "error": str(e)
            }, 500

# ================= NEW (UPDATED) =================

@api.route("/self/summary")
class SelfSummaryResource(Resource):
    @api.marshal_with(ReportDto.response_self_summary)
    def get(self):
        """Ambil ringkasan khusus untuk upline login (self only)"""
        try:
            # Validasi token
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return {
                    "status": "error",
                    "message": "Token tidak ada atau tidak valid"
                }, 401

            token = auth_header.split(" ")[1]

            # Ambil parameters
            period = request.args.get("period", "month")
            year = request.args.get("year", type=int)
            month = request.args.get("month", type=int)
            day = request.args.get("day")
            week = request.args.get("week", type=int)

            # Panggil controller
            data = ctrl.get_self_summary(
                token, period=period, year=year, month=month, day=day, week=week
            )
            
            # Cek jika ada error dari controller
            if isinstance(data, dict) and data.get("error"):
                return {
                    "status": "error",
                    "message": "Gagal mengambil data summary pribadi",
                    "error": data["error"]
                }, 400
            
            return {
                "status": "success",
                "message": f"Data summary {period} pribadi berhasil diambil",
                "data": data
            }, 200
            
        except ValueError as e:
            return {
                "status": "error",
                "message": "Parameter tidak valid",
                "error": str(e)
            }, 400
        except Exception as e:
            return {
                "status": "error",
                "message": "Gagal mengambil data summary pribadi",
                "error": str(e)
            }, 500


@api.route("/admin/summary/week")
class WeeklySummaryResource(Resource):
    @api.marshal_with(ReportDto.response_weekly_summary)
    def get(self):
        """Ambil ringkasan per minggu untuk semua upline"""
        try:
            year = request.args.get("year", type=int)
            month = request.args.get("month", type=int)
            
            if not year or not month:
                return {
                    "status": "error",
                    "message": "Parameter year dan month wajib diisi"
                }, 400

            data = ctrl.get_summary_by_week(year, month)
            
            return {
                "status": "success",
                "message": f"Data summary minggu {month}/{year} berhasil diambil",
                "data": data
            }, 200
            
        except ValueError as e:
            return {
                "status": "error",
                "message": "Parameter tidak valid",
                "error": str(e)
            }, 400
        except Exception as e:
            return {
                "status": "error",
                "message": "Gagal mengambil data summary mingguan",
                "error": str(e)
            }, 500


@api.route("/admin/summary/compare")
class CompareSummaryResource(Resource):
    @api.marshal_with(ReportDto.response_monthly_compare)
    def get(self):
        """Bandingkan 2 bulan (per minggu)"""
        try:
            year1 = request.args.get("year1", type=int)
            month1 = request.args.get("month1", type=int)
            year2 = request.args.get("year2", type=int)
            month2 = request.args.get("month2", type=int)
            
            # Validasi parameter
            if not all([year1, month1, year2, month2]):
                return {
                    "status": "error",
                    "message": "Parameter year1, month1, year2, month2 wajib diisi"
                }, 400

            data = ctrl.compare_months(year1, month1, year2, month2)
            
            return {
                "status": "success",
                "message": f"Perbandingan {month1}/{year1} vs {month2}/{year2} berhasil diambil",
                "data": data
            }, 200
            
        except ValueError as e:
            return {
                "status": "error",
                "message": "Parameter tidak valid",
                "error": str(e)
            }, 400
        except Exception as e:
            return {
                "status": "error",
                "message": "Gagal mengambil data perbandingan",
                "error": str(e)
            }, 500