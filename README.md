# 📊 Marketing Salary Report - Backend

Backend service untuk sistem laporan reseller (hierarchy, summary transaksi, weekly growth, dan monthly comparison) menggunakan **Flask + Flask-RESTX + SQLAlchemy**.

---

## 🚀 Fitur

- **Reseller Hierarchy**
  - Ambil struktur upline–downline dengan total profit.
  - `GET /report/hierarchy`

- **Reseller Summary (Custom Period)**
  - Ambil ringkasan transaksi reseller berdasarkan filter:
    - `day` (tanggal tertentu)
    - `week` (minggu tertentu dalam bulan)
    - `month` (bulan penuh)
  - `GET /report/reseller/summary/custom`

- **Self Summary (Upline)**
  - Lihat ringkasan transaksi hanya untuk reseller/upline tertentu (berdasarkan kode login).
  - `GET /report/self/summary?kode=RM001&period=month&year=2025&month=8`

- **Admin Summary Weekly**
  - Ringkasan per minggu untuk semua upline dalam satu bulan.
  - `GET /report/admin/summary/week?year=2025&month=8`

- **Admin Monthly Compare**
  - Bandingkan performa reseller di **2 bulan berbeda** (growth analysis).
  - `GET /report/admin/summary/compare?year1=2025&month1=7&year2=2025&month2=8`

---

## 🗂 Struktur Project

```bash
app/
├── api/
│   ├── report/
│   │   ├── resource.py      # Resource (endpoint)
│   │   ├── controller.py    # Logic controller
│   │   ├── dto.py           # Data Transfer Objects (schema response)
│   │   └── __init__.py
├── models.py                # Model SQLAlchemy (Reseller, Transaksi)
├── database.py              # Konfigurasi database
└── __init__.py
```

---

## ⚡️ Instalasi & Setup

1. Clone repository:
   ```bash
   git clone https://github.com/username/marketing-salary-report.git
   cd marketing-salary-report/bakcend
   ```

2. Buat virtual environment:
   ```bash
   python -m venv env
   source env/bin/activate  # Linux/Mac
   env\Scripts\activate     # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Setup database (misalnya SQLite / PostgreSQL), lalu jalankan migrasi:
   ```bash
   flask db upgrade
   ```

5. Seed data dummy:
   ```bash
   flask seed
   ```

6. Jalankan server:
   ```bash
   flask run
   ```

---

## 📌 API Endpoint

### 🔹 Hierarchy
```
GET /report/hierarchy
```

**Response:**
```json
{
  "status": "success",
  "message": "Laporan hierarchy berhasil diambil",
  "data": [
    {
      "upline": {
        "kode": "RM001",
        "nama": "Master Reseller 1",
        "total_profit": 1200000
      },
      "downlines": [
        {
          "kode": "RSLA001",
          "nama": "Agen 1",
          "jumlah_transaksi": 150,
          "total_profit": 250000
        }
      ]
    }
  ]
}
```

---

### 🔹 Custom Summary
```
GET /report/reseller/summary/custom?period=month&year=2025&month=8
```

**Response:**
```json
[
  {
    "id_upline": "RM001",
    "nama_upline": "Master Reseller 1",
    "periode": "month",
    "jmlh_trx": 500,
    "jmlh_trx_aktif": 450,
    "akuisisi": 10,
    "akuisisi_aktif": 8,
    "omset": 5000000,
    "profit_upline": 500000,
    "insentif": 50000,
    "start": "2025-08-01T00:00:00",
    "end": "2025-08-31T23:59:59"
  }
]
```

---

### 🔹 Self Summary
```
GET /report/self/summary?kode=RM001&period=month&year=2025&month=8
```

**Response:**
```json
{
  "id_upline": "RM001",
  "nama_upline": "Master Reseller 1",
  "periode": "month",
  "jmlh_trx": 500,
  "jmlh_trx_aktif": 450,
  "akuisisi": 10,
  "akuisisi_aktif": 8,
  "omset": 5000000,
  "profit_upline": 500000,
  "insentif": 50000,
  "start": "2025-08-01T00:00:00",
  "end": "2025-08-31T23:59:59"
}
```

---

### 🔹 Admin Weekly Summary
```
GET /report/admin/summary/week?year=2025&month=8
```

**Response:**
```json
[
  {
    "id_upline": "RM001",
    "nama_upline": "Master Reseller 1",
    "week": 1,
    "jmlh_trx": 120,
    "jmlh_trx_aktif": 100,
    "omset": 1500000,
    "profit_upline": 150000
  }
]
```

---

### 🔹 Admin Monthly Compare
```
GET /report/admin/summary/compare?year1=2025&month1=7&year2=2025&month2=8
```

**Response:**
```json
[
  {
    "upline": "RM001",
    "month1": {
      "jmlh_trx": 400,
      "omset": 4000000,
      "profit": 400000
    },
    "month2": {
      "jmlh_trx": 500,
      "omset": 5000000,
      "profit": 500000
    }
  }
]
```

---

## 🧪 Testing

Gunakan **Postman** atau **cURL** untuk mencoba API.

Contoh:
```bash
curl "http://127.0.0.1:5000/report/self/summary?kode=RM001&period=month&year=2025&month=8"
```

---

## 👨‍💻 Author
Dikembangkan oleh **Muhammad Aqil Zaki**  
Institut Teknologi Padang – Teknik Informatika
