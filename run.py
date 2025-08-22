from app import create_app
from app.database import db
from app.models import Sales

app = create_app()

# Perintah shell tambahan (opsional, untuk kemudahan debug)
@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'Sales': Sales}

# TAMBAHKAN BLOK INI
if __name__ == '__main__':
    # Menjalankan server dalam mode debug
    # Mode debug akan otomatis restart server setiap ada perubahan kode
    app.run(debug=True)