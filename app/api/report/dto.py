from flask_restx import Namespace, fields

class ReportDto:
    api = Namespace("report", description="Laporan Reseller")

    # ======================== BASIC MODELS ========================
    
    # Model untuk upline info
    upline_info = api.model("UplineInfo", {
        "id": fields.String(description="Kode upline"),
        "nama": fields.String(description="Nama upline"),
        "week": fields.Integer(description="Minggu ke-")
    })

    # Model untuk monthly data
    monthly_data = api.model("MonthlyData", {
        "jmlh_trx": fields.Integer(description="Jumlah transaksi"),
        "jmlh_trx_aktif": fields.Integer(description="Jumlah reseller aktif"),
        "akuisisi": fields.Integer(description="Total akuisisi"),
        "akuisisi_aktif": fields.Integer(description="Akuisisi aktif"),
        "omset": fields.Float(description="Total omset"),
        "profit": fields.Float(description="Total profit"),
        "insentif": fields.Float(description="Insentif upline")
    })

    # ======================== DATA MODELS ========================

    # Untuk summary custom (sudah ada)
    reseller_summary_dto = api.model("ResellerSummary", {
        "id_upline": fields.String,
        "nama_upline": fields.String,
        "periode": fields.String,
        "jmlh_trx": fields.Integer,
        "jmlh_trx_aktif": fields.Integer,
        "akuisisi": fields.Integer,
        "akuisisi_aktif": fields.Integer,
        "omset": fields.Float,
        "profit_upline": fields.Float,
        "insentif": fields.Float,
        "start": fields.String,
        "end": fields.String,
    })

    # Untuk self summary (1 upline)
    self_summary_dto = api.model("SelfSummary", {
        "id_upline": fields.String,
        "nama_upline": fields.String,
        "periode": fields.String,
        "jmlh_trx": fields.Integer,
        "jmlh_trx_aktif": fields.Integer,
        "akuisisi": fields.Integer,
        "akuisisi_aktif": fields.Integer,
        "omset": fields.Float,
        "profit_upline": fields.Float,
        "insentif": fields.Float,
        "start": fields.String,
        "end": fields.String,
    })

    # Untuk summary mingguan (per week)
    weekly_summary_dto = api.model("WeeklySummary", {
        "id_upline": fields.String,
        "nama_upline": fields.String,
        "week": fields.Integer,
        "jmlh_trx": fields.Integer,
        "jmlh_trx_aktif": fields.Integer,
        "akuisisi": fields.Integer,
        "akuisisi_aktif": fields.Integer,
        "omset": fields.Float,
        "profit_upline": fields.Float,
        "insentif": fields.Float,
    })

    # Untuk compare bulan
    monthly_compare_dto = api.model("MonthlyCompare", {
        "upline": fields.Nested(upline_info, description="Info upline dan week"),
        "month1": fields.Nested(monthly_data, description="Data bulan pertama"),
        "month2": fields.Nested(monthly_data, description="Data bulan kedua")
    })

    # ======================== RESPONSE WRAPPERS ========================

    # Response untuk hierarchy
    response_hierarchy = api.model("ResponseHierarchy", {
        "status": fields.String(description="Status response", example="success"),
        "message": fields.String(description="Pesan response", example="Data berhasil diambil"),
        "data": fields.Raw(description="Data hierarchy reseller")
    })

    # Response untuk summary custom (list)
    response_reseller_summary = api.model("ResponseResellerSummary", {
        "status": fields.String(description="Status response", example="success"),
        "message": fields.String(description="Pesan response", example="Data summary berhasil diambil"),
        "data": fields.List(fields.Nested(reseller_summary_dto), description="List summary reseller")
    })

    # Response untuk self summary (single object)
    response_self_summary = api.model("ResponseSelfSummary", {
        "status": fields.String(description="Status response", example="success"),
        "message": fields.String(description="Pesan response", example="Data summary pribadi berhasil diambil"),
        "data": fields.Nested(self_summary_dto, description="Summary reseller pribadi")
    })

    # Response untuk weekly summary (list)
    response_weekly_summary = api.model("ResponseWeeklySummary", {
        "status": fields.String(description="Status response", example="success"),
        "message": fields.String(description="Pesan response", example="Data summary mingguan berhasil diambil"),
        "data": fields.List(fields.Nested(weekly_summary_dto), description="List summary per minggu")
    })

    # Response untuk monthly compare (list)
    response_monthly_compare = api.model("ResponseMonthlyCompare", {
        "status": fields.String(description="Status response", example="success"),
        "message": fields.String(description="Pesan response", example="Data perbandingan bulanan berhasil diambil"),
        "data": fields.List(fields.Nested(monthly_compare_dto), description="List perbandingan per bulan")
    })

    # Response untuk error
    response_error = api.model("ResponseError", {
        "status": fields.String(description="Status response", example="error"),
        "message": fields.String(description="Pesan error", example="Terjadi kesalahan"),
        "error": fields.String(description="Detail error", example="Invalid parameters")
    })