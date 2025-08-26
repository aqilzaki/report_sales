from flask_restx import Namespace, fields

class ReportDto:
    api = Namespace("report", description="Laporan Reseller")

    # ======================== BASIC MODELS ========================
    
    # Model untuk detail insentif
    insentif_detail = api.model("InsentifDetail", {
        "basic_salary": fields.Float(description="Gaji pokok 3 juta"),
        "q1": fields.Float(description="Insentif Q1 (3-10jt, 10%)"),
        "q2": fields.Float(description="Insentif Q2 (10-15jt, 20%)"),
        "q3": fields.Float(description="Insentif Q3 (15-20jt, 30%)"),
        "q4": fields.Float(description="Insentif Q4 (20-25jt, 40%)"),
        "q5": fields.Float(description="Insentif Q5 (25jt+, 50%)"),
        "bonus_ekstra": fields.Float(description="Bonus ekstra 700rb (profit > 10jt)"),
        "total_insentif": fields.Float(description="Total insentif (tanpa basic salary)"),
        "total_salary": fields.Float(description="Total gaji + insentif")
    })
    
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
        "insentif": fields.Float(description="Insentif upline"),
        "insentif_detail": fields.Nested(insentif_detail, description="Detail perhitungan insentif")
    })

    # ======================== DATA MODELS ========================

    # Untuk summary custom (sudah ada)
    reseller_summary_dto = api.model("ResellerSummary", {
        "id_upline": fields.String(description="Kode upline"),
        "nama_upline": fields.String(description="Nama upline"),
        "periode": fields.String(description="Periode (day/week/month)"),
        "jmlh_trx": fields.Integer(description="Jumlah transaksi"),
        "jmlh_trx_aktif": fields.Integer(description="Jumlah reseller aktif"),
        "akuisisi": fields.Integer(description="Total akuisisi"),
        "akuisisi_aktif": fields.Integer(description="Akuisisi aktif"),
        "omset": fields.Float(description="Total omset"),
        "profit_upline": fields.Float(description="Total profit"),
        "insentif": fields.Float(description="Total insentif"),
        "insentif_detail": fields.Nested(insentif_detail, description="Detail perhitungan insentif"),
        "start": fields.String(description="Tanggal mulai periode"),
        "end": fields.String(description="Tanggal akhir periode"),
    })

    # Untuk self summary (1 upline)
    self_summary_dto = api.model("SelfSummary", {
        "id_upline": fields.String(description="Kode upline"),
        "nama_upline": fields.String(description="Nama upline"),
        "periode": fields.String(description="Periode (day/week/month)"),
        "jmlh_trx": fields.Integer(description="Jumlah transaksi"),
        "jmlh_trx_aktif": fields.Integer(description="Jumlah reseller aktif"),
        "akuisisi": fields.Integer(description="Total akuisisi"),
        "akuisisi_aktif": fields.Integer(description="Akuisisi aktif"),
        "omset": fields.Float(description="Total omset"),
        "profit_upline": fields.Float(description="Total profit"),
        "insentif": fields.Float(description="Total insentif"),
        "insentif_detail": fields.Nested(insentif_detail, description="Detail perhitungan insentif"),
        "start": fields.String(description="Tanggal mulai periode"),
        "end": fields.String(description="Tanggal akhir periode"),
    })

    # Untuk summary mingguan (per week)
    weekly_summary_dto = api.model("WeeklySummary", {
        "id_upline": fields.String(description="Kode upline"),
        "nama_upline": fields.String(description="Nama upline"),
        "week": fields.Integer(description="Minggu ke-"),
        "jmlh_trx": fields.Integer(description="Jumlah transaksi"),
        "jmlh_trx_aktif": fields.Integer(description="Jumlah reseller aktif"),
        "akuisisi": fields.Integer(description="Total akuisisi"),
        "akuisisi_aktif": fields.Integer(description="Akuisisi aktif"),
        "omset": fields.Float(description="Total omset"),
        "profit_upline": fields.Float(description="Total profit"),
        "insentif": fields.Float(description="Total insentif"),
        "insentif_detail": fields.Nested(insentif_detail, description="Detail perhitungan insentif"),
        "start": fields.String(description="Tanggal mulai periode"),
        "end": fields.String(description="Tanggal akhir periode"),
    })

    # Untuk compare bulan
    monthly_compare_dto = api.model("MonthlyCompare", {
        "upline": fields.Nested(upline_info, description="Info upline dan week"),
        "month1": fields.Nested(monthly_data, description="Data bulan pertama"),
        "month2": fields.Nested(monthly_data, description="Data bulan kedua")
    })

    # ======================== HIERARCHY MODELS ========================
    
    # Model untuk downline dalam hierarchy
    downline_info = api.model("DownlineInfo", {
        "kode": fields.String(description="Kode downline"),
        "nama": fields.String(description="Nama downline"), 
        "jumlah_transaksi": fields.Integer(description="Jumlah transaksi downline"),
        "total_profit": fields.Float(description="Total profit downline")
    })
    
    # Model untuk upline dalam hierarchy
    upline_hierarchy = api.model("UplineHierarchy", {
        "kode": fields.String(description="Kode upline"),
        "nama": fields.String(description="Nama upline"),
        "total_profit": fields.Float(description="Total profit akumulasi dari downlines")
    })
    
    # Model untuk hierarchy data
    hierarchy_data = api.model("HierarchyData", {
        "upline": fields.Nested(upline_hierarchy, description="Info upline"),
        "downlines": fields.List(fields.Nested(downline_info), description="List downlines")
    })

    # ======================== RESPONSE WRAPPERS ========================

    # Response untuk hierarchy
    response_hierarchy = api.model("ResponseHierarchy", {
        "status": fields.String(description="Status response", example="success"),
        "message": fields.String(description="Pesan response", example="Data berhasil diambil"),
        "data": fields.List(fields.Nested(hierarchy_data), description="Data hierarchy reseller")
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