from flask import Flask
from flask_migrate import Migrate   # <--- tambahkan ini
from .config import Config
from .database import db
import os

migrate = Migrate()   # <--- inisialisasi migrate

def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    # Import models supaya terdaftar dengan SQLAlchemy
    from . import models

    from .api import blueprint as api_bp
    app.register_blueprint(api_bp)

    return app
