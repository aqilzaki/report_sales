from flask import current_app as app, jsonify, request

"""
Endpoint untuk mendapatkan laporan keuangan lengkap untuk seorang sales.
Menerima query parameter `bulan` dan `tahun` (contoh: ?bulan=8&tahun=2025).
"""
@app.route('/api/laporan/sales/<string:id_mr>', methods=['GET'])
def laporan_sales(id_mr):
    from app.controllers.get_laporan_sales_controllers import get_laporan_sales
    return get_laporan_sales(id_mr)

# Endpoint sederhana untuk memeriksa apakah API berjalan
@app.route('/api/ping', methods=['GET'])
def ping():
    return jsonify({"message": "pong!"})