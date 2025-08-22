from app import create_app
from app.database import db
from app.models import Sales
from app.seed import seed_command # <-- 1. IMPORT PERINTAH SEED

app = create_app()

app.cli.add_command(seed_command)
# Perintah shell tambahan (opsional, untuk kemudahan debug)
@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'Sales': Sales}

# ===============================================
# <<< TAMBAHKAN KODE INI UNTUK MELIHAT SEMUA ROUTE >>>
with app.app_context():
    print("--- DAFTAR ROUTE TERDAFTAR ---")
    for rule in app.url_map.iter_rules():
        print(f"URL: {rule.rule}, Endpoint: {rule.endpoint}")
    print("----------------------------")
# ===============================================

# BLOK BAWAAN ANDA
if __name__ == '__main__':
    app.run(debug=True, port=9999)