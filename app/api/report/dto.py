from flask_restx import Namespace, fields

class ReportDto:
    api = Namespace("report", description="Laporan Reseller")

    # Untuk hierarchy (sudah ada)
    response_hierarchy = api.model("ResponseHierarchy", {
        "status": fields.String,
        "message": fields.String,
        "data": fields.Raw,  # bisa nested
    })

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
        "omset": fields.Float,
        "profit_upline": fields.Float,
    })

    # Untuk compare bulan
    monthly_compare_dto = api.model("MonthlyCompare", {
        "upline": fields.String,
        "month1": fields.Raw,   # {trx, omset, profit}
        "month2": fields.Raw,   # {trx, omset, profit}
    })
