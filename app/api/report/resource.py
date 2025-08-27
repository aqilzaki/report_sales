from flask_restx import Resource, Namespace
from flask import request
from .dto import ReportDto
from . import controller as ctrl
from app.api.report.dto import ReportDto

api = ReportDto.api

# ================= HIERARCHY =================

@api.route("/hierarchy")
class ReportHierarchy(Resource):
    @api.marshal_with(ReportDto.response_hierarchy)
    @api.doc('get_hierarchy', 
             description='Ambil struktur upline-downline beserta profit transaksi',
             params={
                 "page": "Halaman saat ini (default: 1)",
                 "limit": "Jumlah data per halaman (default: 10)"
             })
    def get(self):
        """Ambil struktur upline–downline beserta profit transaksi"""
        try:
            page = request.args.get("page", type=int, default=1)
            limit = request.args.get("limit", type=int, default=10)

            result = ctrl.get_reseller_hierarchy_with_profit(page=page, limit=limit)

            if not result or not result.get("data"):
                return {
                    "status": "error",
                    "message": "Tidak ada data ditemukan",
                    "page": page,
                    "limit": limit,
                    "total": 0,
                    "data": []
                }, 404

            return {
                "status": "success",
                "message": "Laporan hierarchy berhasil diambil",
                "page": result.get("page", page),
                "limit": result.get("limit", limit),
                "total": result.get("total", 0),
                "data": result.get("data", [])
            }, 200

        except Exception as e:
            return {
                "status": "error",
                "message": "Gagal mengambil data hierarchy",
                "page": 1,
                "limit": 0,
                "total": 0,
                "data": [],
                "error": str(e)
            }, 500

# ================= RESELLER SUMMARY =================

@api.route("/reseller/summary/custom")
class ResellerSummaryCustomResource(Resource):
    @api.marshal_with(ReportDto.response_reseller_summary)
    @api.doc('get_custom_summary',
             params={
                 'period': 'Periode laporan (day/week/month)',
                 'year': 'Tahun (wajib untuk month/week)',
                 'month': 'Bulan 1-12 (wajib untuk month/week)',
                 'day': 'Tanggal format YYYY-MM-DD (untuk period=day)',
                 'week': 'Minggu ke-N dalam bulan (untuk period=week)',
                 'page': 'Halaman yang diminta',
                 'limit': 'Jumlah data per halaman'
             })
    def get(self):
        """Ambil ringkasan reseller dengan filter hari/bulan/minggu"""
        try:
            period = request.args.get("period", "month")
            year = request.args.get("year", type=int)
            month = request.args.get("month", type=int)
            day = request.args.get("day")
            week = request.args.get("week", type=int)
            page = request.args.get("page", type=int, default=1)
            limit = request.args.get("limit", type=int, default=25)

            data = ctrl.get_reseller_summary_custom(
                period=period, year=year, month=month, day=day, week=week, page=page, limit=limit
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

# ================= SELF SUMMARY =================

@api.route("/self/summary")
class SelfSummaryResource(Resource):
    @api.marshal_with(ReportDto.response_self_summary)
    @api.doc('get_self_summary',
             params={
                 'period': 'Periode laporan (day/week/month)',
                 'year': 'Tahun (wajib untuk month/week)',
                 'month': 'Bulan 1-12 (wajib untuk month/week)',
                 'day': 'Tanggal format YYYY-MM-DD (untuk period=day)',
                 'week': 'Minggu ke-N dalam bulan (untuk period=week)',
             },
             security='Bearer')
    @api.doc(security='Bearer')
    def get(self):
        """Ambil ringkasan khusus untuk upline login (self only)"""
        try:
            # Validasi token
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return {
                    "status": "error",
                    "message": "Token tidak ada atau tidak valid. Gunakan header: Authorization: Bearer <token>"
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

# ================= ADMIN WEEKLY SUMMARY =================
@api.route("/admin/summary/week")
class WeeklySummaryResource(Resource):
    @api.marshal_with(ReportDto.response_weekly_summary_paginated)
    @api.doc('get_weekly_summary',
             params={
                 'year': 'Tahun (wajib)',
                 'month': 'Bulan 1-12 (wajib)',
                 'page': 'Nomor halaman (opsional, default=1)',
                 'limit': 'Jumlah data per halaman (opsional, default=10)',
             })
    def get(self):
        """Ambil ringkasan per minggu untuk semua upline (Admin only)"""
        try:
            year = request.args.get("year", type=int)
            month = request.args.get("month", type=int)
            
            if not year or not month:
                return {
                    "status": "error",
                    "message": "Parameter year dan month wajib diisi",
                    "error": "Contoh: /admin/summary/week?year=2024&month=1"
                }, 400

            if month < 1 or month > 12:
                return {
                    "status": "error",
                    "message": "Parameter month harus antara 1-12",
                    "error": f"Month yang diberikan: {month}"
                }, 400
            
            page = request.args.get("page", type=int, default=1)
            limit = request.args.get("limit", type=int, default=10)

            result = ctrl.get_summary_by_week(year, month, page=page, limit=limit)

            return {
                "status": "success",
                "message": f"Data summary mingguan bulan {month}/{year} berhasil diambil",
                "page": result.get("page", page),
                "per_page": result.get("limit", limit),
                "total_roots": result.get("total", 0),
                "total_pages": result.get("total_pages", 1),
                "data": result.get("data", [])
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

# ================= ADMIN MONTHLY COMPARE =================

@api.route("/admin/summary/compare")
class CompareSummaryResource(Resource):
    @api.marshal_with(ReportDto.response_monthly_compare)
    @api.doc('compare_months',
             params={
                 'year1': 'Tahun pertama (wajib)',
                 'month1': 'Bulan pertama 1-12 (wajib)',
                 'year2': 'Tahun kedua (wajib)',
                 'month2': 'Bulan kedua 1-12 (wajib)'
             })
    def get(self):
        """Bandingkan 2 bulan (per minggu) - Admin only"""
        try:
            year1 = request.args.get("year1", type=int)
            month1 = request.args.get("month1", type=int)
            year2 = request.args.get("year2", type=int)
            month2 = request.args.get("month2", type=int)
            
            # Validasi parameter
            if not all([year1, month1, year2, month2]):
                return {
                    "status": "error",
                    "message": "Parameter year1, month1, year2, month2 wajib diisi",
                    "error": "Contoh: /admin/summary/compare?year1=2024&month1=1&year2=2024&month2=2"
                }, 400

            # Validasi range bulan
            if month1 < 1 or month1 > 12 or month2 < 1 or month2 > 12:
                return {
                    "status": "error",
                    "message": "Parameter month1 dan month2 harus antara 1-12",
                    "error": f"Month1: {month1}, Month2: {month2}"
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

# ================= DEBUG ENDPOINT (Optional) =================

@api.route("/debug/activity/<string:reseller_code>")
class DebugActivityResource(Resource):
    @api.doc('debug_activity',
             params={
                 'year': 'Tahun (wajib)',
                 'month': 'Bulan 1-12 (wajib)'
             })
    def get(self, reseller_code):
        """Debug aktivitas reseller tertentu (untuk troubleshooting)"""
        try:
            year = request.args.get("year", type=int)
            month = request.args.get("month", type=int)
            
            if not year or not month:
                return {
                    "status": "error",
                    "message": "Parameter year dan month wajib diisi"
                }, 400
            
            from datetime import datetime
            import calendar
            
            start_dt = datetime(year, month, 1)
            days_in_month = calendar.monthrange(year, month)[1]
            end_dt = start_dt.replace(day=days_in_month, hour=23, minute=59, second=59)
            
            data = ctrl.get_reseller_activity_detail(reseller_code, start_dt, end_dt)
            
            return {
                "status": "success",
                "message": f"Debug aktivitas reseller {reseller_code} pada {month}/{year}",
                "data": data
            }, 200
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Gagal debug aktivitas reseller {reseller_code}",
                "error": str(e)
            }, 500