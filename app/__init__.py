from flask import Flask
from .config import Config
from .models import db
from .schemas import ma

def create_app():
    """Application factory function."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inisialisasi ekstensi
    db.init_app(app)
    ma.init_app(app)

    with app.app_context():
        # Import routes
        from . import routes
        
        # Buat semua tabel database jika belum ada
        # Hapus atau beri komentar baris ini di lingkungan produksi
        db.create_all() 

        return app