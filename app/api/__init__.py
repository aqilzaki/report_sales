from flask import Blueprint
from flask_restx import Api, Resource

# Import namespace baru
from .reseller.resource import api as reseller_ns
from .transaksi.resource import api as transaksi_ns

# SEMENTARA COMMENT DULU API LAMA SAMPAI KITA BUAT YANG BARU
# from .laporan_sales.resource import api as laporan_ns

blueprint = Blueprint('api', __name__, url_prefix='/v1')
api = Api(blueprint, title='API Reseller Pulsa', version='1.0')

# Daftarkan namespace baru
api.add_namespace(reseller_ns, path='/reseller')
api.add_namespace(transaksi_ns, path='/transaksi')

# SEMENTARA COMMENT DULU SAMPAI KITA BUAT API BARU
# api.add_namespace(laporan_ns, path='/laporan')

# Endpoint ping sederhana untuk testing
@api.route('/ping')
class Ping(Resource):
    def get(self):
        """Endpoint untuk memeriksa status API."""
        return {"message": "API Resellerfrom flask import Blueprint
from flask_restx import Api, Resource
    Pulsa is running"}

# SEMENTARA COMMENT DULU API LAMA SAMPAI KITA BUAT YANG BARU
# from .laporan_sales.resource import api as laporan_ns

blueprint = Blueprint('api', __name__, url_prefix='/v1')
api = Api(blueprint, title='API Reseller Pulsa', version='1.0')

# SEMENTARA COMMENT DULU SAMPAI KITA BUAT API BARU
# api.add_namespace(laporan_ns, path='/laporan')

# Endpoint ping sederhana untuk testing
@api.route('/ping')
class Ping(Resource):
    def get(self):
        """Endpoint untuk memeriksa status API."""
        return {"message": "API Reseller Pulsa is running"}