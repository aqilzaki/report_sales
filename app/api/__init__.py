from flask import Blueprint
from flask_restx import Api

from .laporan_sales.resource import api as laporan_ns

blueprint = Blueprint('api', __name__, url_prefix='/v1')
api = Api(blueprint, title='API Laporan Sales', version='1.0')

api.add_namespace(laporan_ns, path='/laporan')