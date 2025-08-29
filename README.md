Tentu, ini draf README.md yang diperbarui dengan fokus pada endpoint laporan saja.

***

# Laporan Penjualan API

API ini menyediakan endpoint untuk laporan penjualan dan hierarki reseller.

## Fitur Laporan

* **Laporan Hierarki:** Menampilkan struktur upline-downline beserta total profit dari transaksi.
* **Ringkasan Reseller:** Memberikan ringkasan penjualan per reseller dengan filter kustom (harian, mingguan, bulanan).
* **Ringkasan Pribadi:** Menyediakan ringkasan penjualan khusus untuk pengguna yang sedang login.
* **Ringkasan Admin:**
    * Laporan mingguan untuk semua upline.
    * Perbandingan data penjualan antara dua bulan yang berbeda.
* **Debugging:** Endpoint khusus untuk men-debug aktivitas reseller tertentu.

## Endpoint Laporan

Berikut adalah daftar endpoint yang tersedia terkait laporan:

### Hierarki

* **GET `/report/hierarchy`**
    * **Deskripsi:** Mengambil struktur hierarki upline-downline beserta profit transaksi.
    * **Parameter:** `page`, `limit`

### Ringkasan Penjualan

* **GET `/report/reseller/summary/custom`**
    * **Deskripsi:** Mengambil ringkasan data penjualan semua reseller dengan filter berdasarkan periode (hari, minggu, atau bulan).
    * **Parameter:** `period`, `year`, `month`, `day`, `week`, `page`, `limit`

* **GET `/report/self/summary`**
    * **Deskripsi:** Mengambil ringkasan data penjualan untuk pengguna (upline) yang sedang login. Memerlukan token autentikasi.
    * **Parameter:** `period`, `year`, `month`, `day`, `week`
    * **Keamanan:** `Bearer Token`

### Laporan Admin

* **GET `/report/admin/summary/week`**
    * **Deskripsi:** Mengambil ringkasan mingguan untuk semua upline. Hanya dapat diakses oleh admin.
    * **Parameter:** `year`, `month`, `page`, `limit`

* **GET `/report/admin/summary/compare`**
    * **Deskripsi:** Membandingkan data penjualan dari dua bulan yang berbeda (per minggu). Hanya dapat diakses oleh admin.
    * **Parameter:** `year1`, `month1`, `year2`, `month2`, `page`, `limit`

### Debug

* **GET `/report/debug/activity/<reseller_code>`**
    * **Deskripsi:** Endpoint untuk melakukan debug dan melihat detail aktivitas dari reseller tertentu dalam periode waktu yang spesifik.
    * **Parameter:** `year`, `month`