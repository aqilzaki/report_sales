from flask import Flask
from .config import Config
from flask_cors import CORS
from .database import db, migrate

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

# Enable CORS
    CORS(app)  # Bisa juga diatur lebih spesifik dengan resources={r"/api/*": {"origins": "*"}}


    db.init_app(app)
    migrate.init_app(app, db)

    # Import models untuk memastikan mereka terdaftar dengan SQLAlchemy
    from . import models

    from .api import blueprint as api_bp
    app.register_blueprint(api_bp)

    return app