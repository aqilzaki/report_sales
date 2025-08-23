from flask_restx import Namespace, fields

class ReportDto:
    api = Namespace('report', description='API untuk laporan upline & downline')

    # --- Model untuk hierarchy ---
    downline_model = api.model('Downline', {
        'kode': fields.String,
        'nama': fields.String,
        'jumlah_transaksi': fields.Integer,
        'total_profit': fields.Float,
    })

    upline_model = api.model('Upline', {
        'kode': fields.String,
        'nama': fields.String,
        'total_profit': fields.Float,
    })

    report_model = api.model('Report', {
        'upline': fields.Nested(upline_model),
        'downlines': fields.List(fields.Nested(downline_model))
    })

    # --- Model untuk summary ---
    summary_model = api.model('SummaryReport', {
        'id_upline': fields.String,
        'nama_upline': fields.String,
        'jmlh_trx': fields.Integer,
        'jmlh_trx_aktif': fields.Integer,
        'akuisisi': fields.Integer,
        'akuisisi_aktif': fields.Integer,
        'omset': fields.Float,
        'profit_upline': fields.Float,
        'insentif': fields.Float,
    })

    # --- Response wrapper ---
    response_hierarchy = api.model('ReportHierarchyResponse', {
        'status': fields.String,
        'message': fields.String,
        'data': fields.List(fields.Nested(report_model))
    })

    response_summary = api.model('ReportSummaryResponse', {
        'status': fields.String,
        'message': fields.String,
        'data': fields.List(fields.Nested(summary_model))
    })
