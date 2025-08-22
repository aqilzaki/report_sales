from flask_marshmallow import Marshmallow
from marshmallow import fields

ma = Marshmallow()

class SalesSchema(ma.Schema):
    id_mr = fields.Str()
    nama_mr = fields.Str()

# Ini adalah skema utama untuk output laporan kita
class LaporanSalesSchema(ma.Schema):
    class Meta:
        # Urutan field dalam output JSON
        ordered = True

    sales_info = fields.Nested(SalesSchema)
    periode = fields.Str(metadata={"description": "Contoh: Agustus 2025"})
    
    # Metrik hasil perhitungan
    omset_total = fields.Int(metadata={"description": "Total nilai transaksi"})
    jumlah_transaksi = fields.Int()
    jumlah_outlet_aktif = fields.Int()
    profit = fields.Int()
    gaji = fields.Int()