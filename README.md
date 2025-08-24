Tentu, ini adalah file `README.md` yang Anda minta.

````markdown
# Laporan Penjualan API

API Laporan Penjualan adalah layanan backend yang dibuat dengan Python dan Flask untuk mengelola data penjualan dari reseller. API ini menyediakan fungsionalitas untuk mengelola reseller, transaksi, dan membuat laporan penjualan.

## Fitur

* **Manajemen Reseller**: Operasi CRUD untuk mengelola data reseller.
* **Manajemen Transaksi**: Melacak transaksi penjualan yang dilakukan oleh reseller.
* **Laporan Penjualan**: Membuat laporan penjualan berdasarkan periode (harian, mingguan, bulanan).
* **Hirarki Reseller**: Mengelola hubungan upline-downline antar reseller.
* **Autentikasi**: Mengamankan endpoint menggunakan token JWT.

## Teknologi yang Digunakan

* **Python**: Bahasa pemrograman utama yang digunakan untuk membangun aplikasi.
* **Flask**: Kerangka kerja web yang digunakan untuk membangun API.
* **Flask-SQLAlchemy**: Ekstensi Flask untuk bekerja dengan database SQL.
* **Flask-Migrate**: Ekstensi Flask untuk menangani migrasi database.
* **Flask-RESTX**: Ekstensi Flask untuk membangun RESTful API.
* **MySQL**: Database relasional yang digunakan untuk menyimpan data.
* **JWT**: JSON Web Tokens digunakan untuk autentikasi.

## Instalasi

1.  **Kloning repositori:**
    ```bash
    git clone [https://github.com/aqilzaki/report_sales.git](https://github.com/aqilzaki/report_sales.git)
    cd report_sales
    ```

2.  **Buat dan aktifkan lingkungan virtual:**
    ```bash
    python -m venv env
    source env/bin/activate  # Di Windows, gunakan `env\Scripts\activate`
    ```

3.  **Instal dependensi:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Konfigurasi variabel lingkungan:**
    Buat file `.env` di direktori root dan tambahkan variabel berikut:
    ```
    SECRET_KEY=kunci_rahasia_anda
    SQLALCHEMY_DATABASE_URI=mysql+mysqlconnector://user:password@host/db_name
    ```

5.  **Jalankan migrasi database:**
    ```bash
    flask db upgrade
    ```

6.  **Jalankan aplikasi:**
    ```bash
    python run.py
    ```

## Struktur Proyek

````

.
├── app/
│   ├── **init**.py
│   ├── api/
│   │   ├── **init**.py
│   │   ├── auth/
│   │   ├── report/
│   │   ├── reseller/
│   │   └── transaksi/
│   ├── database.py
│   ├── models.py
│   └── seed.py
├── migrations/
├── requirements.txt
└── run.py

```

## Model Database

### Reseller

| Nama Kolom     | Tipe Data      | Deskripsi                               |
| :--------------- | :------------- | :-------------------------------------- |
| `kode`           | `String(50)`   | **Kunci Utama**, Kode unik reseller.    |
| `nama`           | `String(100)`  | Nama reseller.                          |
| `saldo`          | `BigInteger`   | Saldo reseller.                         |
| `alamat`         | `Text`         | Alamat reseller.                        |
| `pin`            | `String(10)`   | PIN reseller.                           |
| `aktif`          | `Boolean`      | Status aktif reseller.                  |
| `kode_upline`    | `String(50)`   | Kode upline reseller.                   |
| `kode_level`     | `String(10)`   | Kode level reseller.                    |
| `tgl_daftar`     | `DateTime`     | Tanggal pendaftaran reseller.           |
| `saldo_minimal`  | `BigInteger`   | Saldo minimal yang harus dimiliki.      |
| ...              | ...            | ...                                     |

### Transaksi

| Nama Kolom      | Tipe Data      | Deskripsi                              |
| :---------------- | :------------- | :------------------------------------- |
| `kode`            | `String(50)`   | **Kunci Utama**, Kode unik transaksi.  |
| `tgl_entri`       | `DateTime`     | Tanggal entri transaksi.               |
| `kode_produk`     | `String(50)`   | Kode produk.                           |
| `tujuan`          | `String(50)`   | Tujuan transaksi.                      |
| `kode_reseller`   | `String(50)`   | Kode reseller yang melakukan transaksi.|
| `harga`           | `BigInteger`   | Harga transaksi.                       |
| `harga_beli`      | `BigInteger`   | Harga beli produk.                     |
| `status`          | `String(20)`   | Status transaksi.                      |
| ...               | ...            | ...                                    |

## Endpoint API

### Otentikasi

* `POST /auth/login`: Login untuk mendapatkan token JWT.
* `POST /auth/register`: Mendaftarkan reseller baru.

### Reseller

* `GET /reseller`: Mendapatkan semua data reseller.
* `GET /reseller/<kode>`: Mendapatkan data reseller berdasarkan kode.
* `GET /reseller/<kode>/statistik`: Mendapatkan data reseller beserta statistik transaksi.
* `GET /reseller/level/<level>`: Mendapatkan data reseller berdasarkan level.
* `GET /reseller/downline/<kode_upline>`: Mendapatkan data downline dari seorang upline.
* `GET /reseller/top`: Mendapatkan top reseller berdasarkan omset.

### Transaksi

* `GET /transaksi/reseller/<kode_reseller>`: Mendapatkan transaksi berdasarkan kode reseller.
* `GET /transaksi/summary/<kode_reseller>`: Mendapatkan ringkasan transaksi reseller.
* `GET /transaksi/recent`: Mendapatkan transaksi terbaru.
* `GET /transaksi/status/<status>`: Mendapatkan transaksi berdasarkan status.
* `GET /transaksi/laporan/harian`: Mendapatkan laporan transaksi harian.

### Laporan

* `GET /report/profit-hirarki`: Mendapatkan hierarki reseller dengan profit.
* `GET /report/summary`: Mendapatkan ringkasan transaksi reseller dengan filter periode.
* `GET /report/summary/self`: Mendapatkan ringkasan transaksi untuk 1 upline (diri sendiri).
* `GET /report/summary/weekly`: Mendapatkan ringkasan per minggu untuk semua upline.
* `GET /report/compare`: Membandingkan ringkasan bulan1 vs bulan2 (per minggu).
```