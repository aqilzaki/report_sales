import os
from dotenv import load_dotenv

# Muat variabel dari file .env
load_dotenv()

class Config:
    """Konfigurasi dasar aplikasi."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'kunci-rahasia-yang-sangat-sulit-ditebak')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False