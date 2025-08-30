# 📊 Marketing Salary Report API

API Backend untuk sistem laporan reseller dengan perhitungan insentif otomatis menggunakan **Flask + Flask-RESTX + SQLAlchemy**.

## 🎯 Overview

Sistem ini menyediakan API untuk mengelola laporan performa reseller dalam struktur hierarki (upline-downline) dengan fitur:
- Perhitungan insentif bertingkat berdasarkan profit
- Analisis aktivitas reseller (minimum 3 transaksi/hari, gap maksimal 15 hari)
- Laporan per periode (hari, minggu, bulan)
- Perbandingan performa antar bulan
- Pagination untuk performa optimal

---

## 🚀 Fitur Report API

### 1. **Hierarchy Report**
Menampilkan struktur upline-downline dengan total profit dan statistik transaksi.

### 2. **Custom Period Summary** 
Ringkasan transaksi reseller dengan filter periode fleksibel:
- **Day**: Laporan transaksi untuk tanggal tertentu
- **Week**: Laporan per minggu dalam bulan tertentu  
- **Month**: Laporan bulanan lengkap

### 3. **Self Summary (Authenticated)**
Laporan khusus untuk reseller yang login - hanya menampilkan data mereka sendiri.

### 4. **Admin Weekly Summary**
Laporan per minggu untuk semua upline (khusus admin) dengan pagination.

### 5. **Monthly Comparison**
Analisis perbandingan performa 2 bulan berbeda untuk evaluasi growth.

---

## 💰 Sistem Insentif

Perhitungan insentif menggunakan sistem bertingkat:

| Profit Range | Rate | Bonus |
|--------------|------|-------|
| ≤ 3 juta | Basic Salary: 3 juta | - |
| 3 - 10 juta | 10% | - |
| 10 - 15 juta | 20% | +700rb bonus |
| 15 - 20 juta | 30% | +700rb bonus |
| 20 - 25 juta | 40% | +700rb bonus |
| > 25 juta | 50% | +700rb bonus |

**Contoh**: Profit 18 juta = 3jt + (7jt × 10%) + (5jt × 20%) + (3jt × 30%) + 700rb = **6.4 juta**

---

## 🔍 Kriteria Reseller Aktif

Reseller dianggap **aktif** jika memenuhi kedua syarat:
1. **Minimal 3 transaksi dalam 1 hari** (di periode yang dianalisis)
2. **Tidak ada gap ≥ 15 hari** tanpa transaksi dalam periode

**Akuisisi aktif**: Reseller yang aktif + total transaksi ≥ 3 dalam periode.

---

## 📋 API Endpoints

### 🔹 **Hierarchy**
```http
GET /report/hierarchy?page=1&limit=10
```

**Response:**
```json
{
  "status": "success",
  "message": "Laporan hierarchy berhasil diambil",
  "page": 1,
  "limit": 10,
  "total": 25,
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

### 🔹 **Custom Period Summary**
```http
GET /report/reseller/summary/custom?period=month&year=2025&month=8&page=1&limit=25
```

**Parameters:**
- `period`: `day` | `week` | `month`
- `year`: Tahun (wajib untuk week/month)
- `month`: Bulan 1-12 (wajib untuk week/month)
- `day`: Format YYYY-MM-DD (untuk period=day)
- `week`: Minggu ke-N dalam bulan (untuk period=week)
- `page`: Halaman pagination
- `limit`: Data per halaman

**Response:**
```json
{
  "status": "success",
  "message": "Data summary month berhasil diambil",
  "data": [
    {
      "id_upline": "RM001",
      "nama_upline": "Master Reseller 1",
      "periode": "month",
      "jmlh_trx": 500,
      "jmlh_trx_aktif": 8,
      "akuisisi": 10,
      "akuisisi_aktif": 8,
      "omset": 5000000,
      "profit_upline": 500000,
      "insentif": 720000,
      "insentif_detail": {
        "basic_salary": 3000000,
        "q1": 700000,
        "q2": 0,
        "q3": 0,
        "q4": 0,
        "q5": 0,
        "bonus_ekstra": 700000,
        "total_insentif": 1400000,
        "total_salary": 4400000
      },
      "start": "2025-08-01T00:00:00",
      "end": "2025-08-31T23:59:59"
    }
  ]
}
```

---

### 🔹 **Self Summary (Authenticated)**
```http
GET /report/self/summary?period=month&year=2025&month=8
Authorization: Bearer <jwt_token>
```

**Response:** Same structure as custom summary but returns single object in `data`.

---

### 🔹 **Admin Weekly Summary**
```http
GET /report/admin/summary/week?year=2025&month=8&page=1&limit=10
```

**Response:**
```json
{
  "status": "success",
  "message": "Data summary mingguan bulan 8/2025 berhasil diambil",
  "page": 1,
  "per_page": 10,
  "total_roots": 25,
  "total_pages": 3,
  "data": [
    {
      "id_upline": "RM001",
      "nama_upline": "Master Reseller 1",
      "week": 1,
      "jmlh_trx": 120,
      "jmlh_trx_aktif": 2,
      "akuisisi": 10,
      "akuisisi_aktif": 2,
      "omset": 1500000,
      "profit_upline": 150000,
      "insentif": 15000,
      "start": "2025-08-01T00:00:00",
      "end": "2025-08-03T23:59:59"
    }
  ]
}
```

---

### 🔹 **Monthly Comparison**
```http
GET /report/admin/summary/compare?year1=2025&month1=7&year2=2025&month2=8&page=1&limit=10
```

**Response:**
```json
{
  "status": "success",
  "message": "Data perbandingan bulanan berhasil diambil",
  "page": 1,
  "per_page": 10,
  "total_roots": 25,
  "total_pages": 3,
  "data": [
    {
      "upline": {
        "id": "RM001",
        "nama": "Master Reseller 1",
        "week": 1
      },
      "month1": {
        "jmlh_trx": 400,
        "jmlh_trx_aktif": 6,
        "akuisisi": 10,
        "akuisisi_aktif": 6,
        "omset": 4000000,
        "profit": 400000,
        "insentif": 740000
      },
      "month2": {
        "jmlh_trx": 500,
        "jmlh_trx_aktif": 8,
        "akuisisi": 10,
        "akuisisi_aktif": 8,
        "omset": 5000000,
        "profit": 500000,
        "insentif": 920000
      }
    }
  ]
}
```

---

### 🔹 **Debug Activity (Development)**
```http
GET /report/debug/activity/RSLA001?year=2025&month=8
```

Debug aktivitas reseller tertentu untuk troubleshooting kriteria aktif.

---

## ⚡️ Quick Start

1. **Clone & Setup**
   ```bash
   git clone <repository-url>
   cd marketing-salary-report/backend
   python -m venv env
   source env/bin/activate  # Linux/Mac
   pip install -r requirements.txt
   ```

2. **Database Setup**
   ```bash
   flask db upgrade
   flask seed  # Insert dummy data
   ```

3. **Run Development Server**
   ```bash
   flask run
   # Server akan berjalan di http://127.0.0.1:5000
   ```

4. **Test API**
   ```bash
   # Test hierarchy
   curl "http://127.0.0.1:5000/report/hierarchy?page=1&limit=5"
   
   # Test custom summary
   curl "http://127.0.0.1:5000/report/reseller/summary/custom?period=month&year=2025&month=8"
   ```

---

## 🗂 Project Structure

```
app/
├── api/
│   ├── report/
│   │   ├── resource.py      # API endpoints
│   │   ├── controller.py    # Business logic & calculations
│   │   ├── dto.py          # Response schemas
│   │   └── __init__.py
│   ├── reseller/           # Reseller management APIs  
│   └── transaksi/          # Transaction APIs
├── models.py               # SQLAlchemy models
├── database.py            # Database configuration
└── __init__.py
```

---

## 🛠 Key Features

### **Multi-Database Support**
- SQLite (development)
- PostgreSQL (production)
- SQL Server (enterprise)
- Automatic SQL dialect detection

### **Performance Optimizations**
- Batch processing untuk perhitungan aktivitas
- SQL-native pagination dengan ROW_NUMBER()
- Minimal database queries dengan aggregation
- Optimized daily transaction counting

### **Security**
- JWT authentication untuk self summary
- Parameter validation dan sanitization
- SQL injection protection dengan named parameters

---

## 🧪 Testing Examples

### **Postman Collection**
```bash
# Import environment variables
BASE_URL = http://127.0.0.1:5000
JWT_TOKEN = <your_jwt_token>
```

### **cURL Examples**
```bash
# 1. Get hierarchy with pagination
curl -X GET "http://127.0.0.1:5000/report/hierarchy?page=1&limit=5"

# 2. Monthly summary for all uplines
curl -X GET "http://127.0.0.1:5000/report/reseller/summary/custom?period=month&year=2025&month=8"

# 3. Weekly summary (admin only)
curl -X GET "http://127.0.0.1:5000/report/admin/summary/week?year=2025&month=8&page=1&limit=10"

# 4. Self summary (authenticated)
curl -X GET "http://127.0.0.1:5000/report/self/summary?period=month&year=2025&month=8" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 5. Compare two months
curl -X GET "http://127.0.0.1:5000/report/admin/summary/compare?year1=2025&month1=7&year2=2025&month2=8"
```

---

## 📈 Response Pagination

Semua endpoint yang mengembalikan banyak data menggunakan pagination:

```json
{
  "page": 1,
  "per_page": 10,
  "total_roots": 25,
  "total_pages": 3,
  "data": [...]
}
```

---

## 🐛 Error Handling

API mengembalikan error response yang konsisten:

```json
{
  "status": "error",
  "message": "Deskripsi error yang user-friendly",
  "error": "Technical error details"
}
```

**Common Error Codes:**
- `400`: Bad Request (parameter invalid)
- `401`: Unauthorized (token invalid/missing)
- `404`: Not Found (data tidak ditemukan)
- `500`: Internal Server Error

---

## 👨‍💻 Author

**Muhammad Aqil Zaki**  
Institut Teknologi Padang – Teknik Informatika

## 📝 License

Project ini dikembangkan untuk keperluan sistem manajemen reseller.

---

## 📚 Next Steps

1. **Frontend Integration**: Integrate dengan dashboard React/Vue
2. **Real-time Updates**: WebSocket untuk live transaction updates  
3. **Export Features**: PDF/Excel export untuk laporan
4. **Advanced Analytics**: Machine learning untuk prediksi performa
5. **Mobile App**: REST API sudah siap untuk mobile integration