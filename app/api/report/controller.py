from app.models import Reseller, Transaksi
import jwt
from app.database import db
from sqlalchemy import func, case, and_, distinct, text
from datetime import datetime, timedelta, date
from flask import current_app
import calendar
from app.api.auth.controller import get_user_from_token
from decimal import Decimal


def get_reseller_hierarchy_with_profit(page=1, limit=10):
    """Ambil hierarchy dengan pagination - support MySQL & MSSQL"""
    try:
        print("=== DEBUG HIERARCHY WITH PAGINATION ===")
        offset = (page - 1) * limit
        dialect = db.engine.dialect.name.lower()
        
        # Query dengan pagination berdasarkan dialect
        if dialect == "mssql":
            root_query = text("""
                SELECT kode, nama, kode_upline
                FROM reseller
                WHERE kode_upline IS NULL OR kode_upline = '' OR kode_upline = '0'
                ORDER BY kode
                OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
            """)
        else:  # MySQL
            root_query = text("""
                SELECT kode, nama, kode_upline
                FROM reseller
                WHERE kode_upline IS NULL OR kode_upline = '' OR kode_upline = '0'
                ORDER BY kode
                LIMIT :limit OFFSET :offset
            """)
        
        root_results = db.session.execute(root_query, {'offset': offset, 'limit': limit}).fetchall()
        print(f"Found {len(root_results)} roots for page {page}")
        
        if not root_results:
            return {"page": page, "limit": limit, "total": 0, "data": []}

        hasil = []
        for root_row in root_results:
            root_kode, root_nama = root_row[0], root_row[1]
            
            # Ambil downlines dan hitung profit dalam 1 query
            downline_query = text("""
                SELECT 
                    r.kode, r.nama,
                    COALESCE(COUNT(t.kode), 0) as jumlah_transaksi,
                    COALESCE(SUM(t.harga - t.harga_beli), 0) as total_profit
                FROM reseller r
                LEFT JOIN transaksi t ON t.kode_reseller = r.kode
                WHERE r.kode_upline = :upline_kode
                GROUP BY r.kode, r.nama
            """)
            
            downline_results = db.session.execute(downline_query, {'upline_kode': root_kode}).fetchall()
            
            downline_data = []
            total_profit_upline = 0.0
            
            for dl in downline_results:
                profit = float(dl[3] or 0)
                total_profit_upline += profit
                downline_data.append({
                    "kode": dl[0], "nama": dl[1],
                    "jumlah_transaksi": int(dl[2] or 0),
                    "total_profit": profit
                })

            hasil.append({
                "upline": {"kode": root_kode, "nama": root_nama, "total_profit": total_profit_upline},
                "downlines": downline_data
            })

        # Get total count untuk pagination info
        count_query = text("SELECT COUNT(*) FROM reseller WHERE kode_upline IS NULL OR kode_upline = '' OR kode_upline = '0'")
        total = db.session.execute(count_query).scalar()

        return {
            "page": page, "limit": limit, "total": total,
            "total_pages": (total + limit - 1) // limit,
            "data": hasil
        }
        
    except Exception as e:
        print(f"Error in get_reseller_hierarchy_with_profit: {str(e)}")
        return {"page": page, "limit": limit, "total": 0, "data": []}

# ======================== PERIOD FILTER (unchanged) ========================
def _get_period_range(period: str, year=None, month=None, day=None, week=None):
    """Hitung range waktu berdasarkan period (day|month|week) - inclusive"""
    try:
        if period == "day":
            if not day:
                raise ValueError("day harus diisi format YYYY-MM-DD")
            start = datetime.strptime(day, "%Y-%m-%d")
            end = start.replace(hour=23, minute=59, second=59)

        elif period == "month":
            if not year or not month:
                raise ValueError("year dan month harus diisi untuk period=month")
            start = datetime(year, month, 1)
            days_in_month = calendar.monthrange(year, month)[1]
            end = datetime(year, month, days_in_month, 23, 59, 59)

        elif period == "week":
            if not year or not month or not week:
                raise ValueError("year, month, dan week harus diisi untuk period=week")

            month_cal = calendar.Calendar(firstweekday=0).monthdatescalendar(year, month)  
            if week < 1 or week > len(month_cal):
                raise ValueError(f"Bulan {month}/{year} hanya punya {len(month_cal)} minggu")

            week_days = month_cal[week - 1]
            start = datetime.combine(week_days[0], datetime.min.time())
            end = datetime.combine(week_days[-1], datetime.max.time())

        else:
            raise ValueError("period harus day|month|week")

        return start, end
    except Exception as e:
        print(f"Error in _get_period_range: {str(e)}")
        raise e

# ======================== INSENTIF CALCULATION (unchanged) =======================
def calculate_insentif(profit):
    """Perhitungan insentif berdasarkan profit"""
    profit = Decimal(profit)
    basic_salary = Decimal(3_000_000)
    q1 = q2 = q3 = q4 = q5 = bonus_ekstra = Decimal(0)
    
    if profit <= Decimal(3_000_000):
        return {
            "basic_salary": int(basic_salary), "q1": 0, "q2": 0, "q3": 0, "q4": 0, "q5": 0,
            "bonus_ekstra": 0, "total_insentif": 0, "total_salary": int(basic_salary)
        }

    # Q1: 3jt - 10jt (10%)
    if profit > Decimal(3_000_000):
        q1 = (min(profit, Decimal(10_000_000)) - Decimal(3_000_000)) * Decimal("0.10")
    
    # Q2: 10jt - 15jt (20%)
    if profit > Decimal(10_000_000):
        q2 = (min(profit, Decimal(15_000_000)) - Decimal(10_000_000)) * Decimal("0.20")
    
    # Q3: 15jt - 20jt (30%)
    if profit > Decimal(15_000_000):
        q3 = (min(profit, Decimal(20_000_000)) - Decimal(15_000_000)) * Decimal("0.30")
    
    # Q4: 20jt - 25jt (40%)
    if profit > Decimal(20_000_000):
        q4 = (min(profit, Decimal(25_000_000)) - Decimal(20_000_000)) * Decimal("0.40")
    
    # Q5: 25jt+ (50%)
    if profit > Decimal(25_000_000):
        q5 = (profit - Decimal(25_000_000)) * Decimal("0.50")
    
    # Bonus ekstra jika profit > 10jt
    if profit > Decimal(10_000_000):
        bonus_ekstra = Decimal(700_000)
    
    total_insentif = q1 + q2 + q3 + q4 + q5 + bonus_ekstra
    
    return {
        "basic_salary": int(basic_salary), "q1": int(q1), "q2": int(q2), "q3": int(q3), 
        "q4": int(q4), "q5": int(q5), "bonus_ekstra": int(bonus_ekstra),
        "total_insentif": int(total_insentif), "total_salary": int(basic_salary + total_insentif)
    }

# ======================== COMPACT HELPER FUNCTIONS ========================
def _count_active_resellers(reseller_codes, start_dt, end_dt):
    """Hitung reseller aktif - optimized query"""
    if not reseller_codes:
        return 0
    
    try:
        # Single query untuk semua reseller sekaligus
        placeholders = ','.join([f':code_{i}' for i in range(len(reseller_codes))])
        params = {f'code_{i}': code for i, code in enumerate(reseller_codes)}
        params.update({'start_dt': start_dt, 'end_dt': end_dt})
        
        # Ambil semua data transaksi harian dalam 1 query
        daily_query = text(f"""
            SELECT 
                kode_reseller,
                CAST(tgl_entri AS DATE) as trx_date,
                COUNT(kode) as daily_count
            FROM transaksi 
            WHERE kode_reseller IN ({placeholders})
                AND tgl_entri >= :start_dt AND tgl_entri <= :end_dt
            GROUP BY kode_reseller, CAST(tgl_entri AS DATE)
            HAVING COUNT(kode) >= 3
        """)
        
        results = db.session.execute(daily_query, params).fetchall()
        
        # Group by reseller untuk cek gap
        reseller_dates = {}
        for row in results:
            reseller_code = row[0]
            if reseller_code not in reseller_dates:
                reseller_dates[reseller_code] = []
            reseller_dates[reseller_code].append(row[1])
        
        # Cek mana yang tidak ada gap 15 hari
        active_count = 0
        for reseller_code, dates in reseller_dates.items():
            if _has_no_15_day_gap_simple(dates, start_dt, end_dt):
                active_count += 1
        
        return active_count
    except Exception as e:
        print(f"Error in _count_active_resellers: {str(e)}")
        return 0

def _has_no_15_day_gap_simple(transaction_dates, start_dt, end_dt):
    """Simplified gap check"""
    if not transaction_dates:
        return False
    
    try:
        sorted_dates = sorted(transaction_dates)
        
        # Cek gap dari start ke first transaction
        if (sorted_dates[0] - start_dt.date()).days >= 15:
            return False
        
        # Cek gap antar transaksi
        for i in range(len(sorted_dates) - 1):
            if (sorted_dates[i + 1] - sorted_dates[i]).days > 15:
                return False
        
        # Cek gap dari last transaction ke end
        if (end_dt.date() - sorted_dates[-1]).days >= 15:
            return False
        
        return True
    except:
        return False

# ======================== MAIN SUMMARY (unchanged - sudah benar) ========================
def get_reseller_summary_custom(period="month", year=None, month=None, day=None, week=None, page=None, limit=None):
    try:
        start_dt, end_dt = _get_period_range(period, year, month, day, week)
        offset = (page - 1) * limit
        dialect = db.engine.dialect.name.lower()

        if dialect == "mssql":
            query = text(f"""
                WITH root_reseller AS (
                    SELECT 
                        kode, nama,
                        ROW_NUMBER() OVER (ORDER BY kode) AS rn
                    FROM reseller
                    WHERE kode_upline IS NULL OR kode_upline = '' OR kode_upline = '0'
                )
                SELECT 
                    r.kode AS id_upline, r.nama AS nama_upline,
                    COUNT(DISTINCT d.kode) AS akuisisi,
                    COALESCE(COUNT(t.kode), 0) AS jmlh_trx,
                    COALESCE(SUM(t.harga), 0) AS omset,
                    COALESCE(SUM(t.harga - t.harga_beli), 0) AS profit_upline
                FROM root_reseller r
                LEFT JOIN reseller d ON d.kode_upline = r.kode
                LEFT JOIN transaksi t ON t.kode_reseller = d.kode AND t.tgl_entri >= :start_dt AND t.tgl_entri <= :end_dt
                WHERE r.rn BETWEEN :offset+1 AND :offset+:limit
                GROUP BY r.kode, r.nama, r.rn
                ORDER BY r.rn
            """)
        else:
            query = text(f"""
                SELECT 
                    r.kode AS id_upline, r.nama AS nama_upline,
                    COUNT(DISTINCT d.kode) AS akuisisi,
                    COALESCE(COUNT(t.kode), 0) AS jmlh_trx,
                    COALESCE(SUM(t.harga), 0) AS omset,
                    COALESCE(SUM(t.harga - t.harga_beli), 0) AS profit_upline
                FROM reseller r
                LEFT JOIN reseller d ON d.kode_upline = r.kode
                LEFT JOIN transaksi t ON t.kode_reseller = d.kode AND t.tgl_entri >= :start_dt AND t.tgl_entri <= :end_dt
                WHERE r.kode_upline IS NULL OR r.kode_upline = '' OR r.kode_upline = '0'
                GROUP BY r.kode, r.nama
                ORDER BY r.kode
                LIMIT :limit OFFSET :offset
            """)

        results = db.session.execute(query, {
            "start_dt": start_dt, "end_dt": end_dt, "offset": offset, "limit": limit
        }).fetchall()

        hasil = []
        for row in results:
            insentif_detail = calculate_insentif(row.profit_upline)
            hasil.append({
                "id_upline": row.id_upline, "nama_upline": row.nama_upline, "periode": period,
                "jmlh_trx": int(row.jmlh_trx or 0),
                "jmlh_trx_aktif": _count_active_resellers([row.id_upline], start_dt, end_dt),
                "akuisisi": int(row.akuisisi or 0),
                "akuisisi_aktif": _count_active_resellers([row.id_upline], start_dt, end_dt),
                "omset": float(row.omset or 0), "profit_upline": float(row.profit_upline or 0),
                "insentif": insentif_detail["total_insentif"], "insentif_detail": insentif_detail,
                "start": start_dt.isoformat(timespec="seconds"), "end": end_dt.isoformat(timespec="seconds")
            })

        return hasil
    except Exception as e:
        print(f"Error in get_reseller_summary_custom: {str(e)}")
        return []

# ======================== SELF SUMMARY (unchanged - sudah benar) ========================
def get_self_summary(token, period="month", year=None, month=None, day=None, week=None):
    try:
        payload = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
        kode = payload["sub"]
        
        user_query = text("SELECT kode, nama FROM reseller WHERE kode = :kode")
        user_result = db.session.execute(user_query, {'kode': kode}).fetchone()
        
        if not user_result:
            return {"error": f"Reseller {kode} tidak ditemukan"}

        start_dt, end_dt = _get_period_range(period, year, month, day, week)
        root_kode, root_nama = user_result[0], user_result[1]
        
        # Ambil downlines
        downline_query = text("SELECT kode FROM reseller WHERE kode_upline = :upline_kode")
        downline_codes = [r[0] for r in db.session.execute(downline_query, {'upline_kode': root_kode}).fetchall()]

        jmlh_trx = jmlh_trx_aktif = akuisisi_aktif = 0
        total_omset = total_profit = 0.0

        if downline_codes:
            placeholders = ','.join([f':code_{i}' for i in range(len(downline_codes))])
            params = {f'code_{i}': code for i, code in enumerate(downline_codes)}
            params.update({'start_dt': start_dt, 'end_dt': end_dt})

            trx_query = text(f"""
                SELECT COALESCE(COUNT(kode), 0), COALESCE(SUM(harga), 0), COALESCE(SUM(harga - harga_beli), 0)
                FROM transaksi WHERE kode_reseller IN ({placeholders}) AND tgl_entri >= :start_dt AND tgl_entri <= :end_dt
            """)

            trx_result = db.session.execute(trx_query, params).fetchone()
            jmlh_trx, total_omset, total_profit = int(trx_result[0] or 0), float(trx_result[1] or 0), float(trx_result[2] or 0)
            jmlh_trx_aktif = akuisisi_aktif = _count_active_resellers(downline_codes, start_dt, end_dt)

        insentif_detail = calculate_insentif(total_profit)
        return {
            "id_upline": root_kode, "nama_upline": root_nama, "periode": period,
            "jmlh_trx": jmlh_trx, "jmlh_trx_aktif": jmlh_trx_aktif,
            "akuisisi": len(downline_codes), "akuisisi_aktif": akuisisi_aktif,
            "omset": total_omset, "profit_upline": total_profit,
            "insentif": insentif_detail["total_insentif"], "insentif_detail": insentif_detail,
            "start": start_dt.isoformat(timespec="seconds"), "end": end_dt.isoformat(timespec="seconds")
        }
    except Exception as e:
        print(f"Error in get_self_summary: {str(e)}")
        return {"error": str(e)}

# ======================== OPTIMIZED WEEKLY SUMMARY ========================
def get_summary_by_week(year, month, page=1, limit=25):
    """Weekly summary dengan pagination yang optimal"""
    try:
        month_cal = calendar.Calendar(firstweekday=0).monthdatescalendar(year, month)
        
        # Get paginated roots
        offset = (page - 1) * limit
        dialect = db.engine.dialect.name.lower()
        
        if dialect == "mssql":
            root_query = text("""
                SELECT kode, nama FROM reseller 
                WHERE kode_upline IS NULL OR kode_upline = '' OR kode_upline = '0'
                ORDER BY kode OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
            """)
        else:
            root_query = text("""
                SELECT kode, nama FROM reseller 
                WHERE kode_upline IS NULL OR kode_upline = '' OR kode_upline = '0'
                ORDER BY kode LIMIT :limit OFFSET :offset
            """)
        
        root_results = db.session.execute(root_query, {'offset': offset, 'limit': limit}).fetchall()
        
        # Get total count
        count_query = text("SELECT COUNT(*) FROM reseller WHERE kode_upline IS NULL OR kode_upline = '' OR kode_upline = '0'")
        total_roots = db.session.execute(count_query).scalar()

        results = []
        for week_num, week_days in enumerate(month_cal, start=1):
            start_dt = datetime.combine(week_days[0], datetime.min.time())
            end_dt = datetime.combine(week_days[-1], datetime.max.time())

            for root_kode, root_nama in root_results:
                # Get downlines dan summary dalam 1 query
                summary_query = text("""
                    SELECT 
                        COUNT(DISTINCT d.kode) as akuisisi,
                        COALESCE(COUNT(t.kode), 0) as jmlh_trx,
                        COALESCE(SUM(t.harga), 0) as omset,
                        COALESCE(SUM(t.harga - t.harga_beli), 0) as profit
                    FROM reseller d
                    LEFT JOIN transaksi t ON t.kode_reseller = d.kode AND t.tgl_entri BETWEEN :start_dt AND :end_dt
                    WHERE d.kode_upline = :upline_kode
                """)
                
                summary_result = db.session.execute(summary_query, {
                    'upline_kode': root_kode, 'start_dt': start_dt, 'end_dt': end_dt
                }).fetchone()

                akuisisi = int(summary_result[0] or 0)
                jmlh_trx = int(summary_result[1] or 0)
                total_omset = float(summary_result[2] or 0)
                total_profit = float(summary_result[3] or 0)
                
                # Simplified active calculation untuk performance
                jmlh_trx_aktif = akuisisi_aktif = min(akuisisi, jmlh_trx // 3) if jmlh_trx > 0 else 0
                
                insentif_detail = calculate_insentif(total_profit)
                results.append({
                    "id_upline": root_kode, "nama_upline": root_nama, "week": week_num,
                    "jmlh_trx": jmlh_trx, "jmlh_trx_aktif": jmlh_trx_aktif,
                    "akuisisi": akuisisi, "akuisisi_aktif": akuisisi_aktif,
                    "omset": total_omset, "profit_upline": total_profit,
                    "insentif": float(insentif_detail["total_insentif"]), "insentif_detail": insentif_detail,
                    "start": start_dt.isoformat(timespec="seconds"), "end": end_dt.isoformat(timespec="seconds")
                })

        return {
            "page": page, "limit": limit, "total_roots": total_roots,
            "total_pages": (total_roots + limit - 1) // limit, "data": results
        }
    except Exception as e:
        print(f"Error in get_summary_by_week: {str(e)}")
        return {"page": page, "limit": limit, "total_roots": 0, "total_pages": 0, "data": []}

# ======================== OPTIMIZED MONTHLY COMPARE ========================
def compare_months(year1, month1, year2, month2, page=1, limit=25):
    """Compare months dengan pagination"""
    try:
        data1_result = get_summary_by_week(year1, month1, page, limit)
        data2_result = get_summary_by_week(year2, month2, page, limit)
        
        data1, data2 = data1_result["data"], data2_result["data"]
        comparison = {}
        
        # Process data1
        for d in data1:
            key = (d["id_upline"], d["week"])
            comparison[key] = {
                "upline": {"id": d["id_upline"], "nama": d["nama_upline"], "week": d["week"]},
                "month1": {k: d[k] for k in ["jmlh_trx", "jmlh_trx_aktif", "akuisisi", "akuisisi_aktif", "omset", "insentif", "insentif_detail"] if k in d},
                "month2": {"jmlh_trx": 0, "jmlh_trx_aktif": 0, "akuisisi": 0, "akuisisi_aktif": 0, "omset": 0, "profit": 0, "insentif": 0, "insentif_detail": {}}
            }

        # Process data2
        for d in data2:
            key = (d["id_upline"], d["week"])
            month2_data = {k: d[k] for k in ["jmlh_trx", "jmlh_trx_aktif", "akuisisi", "akuisisi_aktif", "omset", "insentif", "insentif_detail"] if k in d}
            month2_data["profit"] = d.get("profit_upline", 0)
            
            if key not in comparison:
                comparison[key] = {
                    "upline": {"id": d["id_upline"], "nama": d["nama_upline"], "week": d["week"]},
                    "month1": {"jmlh_trx": 0, "jmlh_trx_aktif": 0, "akuisisi": 0, "akuisisi_aktif": 0, "omset": 0, "profit": 0, "insentif": 0, "insentif_detail": {}},
                    "month2": month2_data
                }
            else:
                comparison[key]["month2"] = month2_data

        return {
            "page": page, "limit": limit, 
            "total_roots": data1_result.get("total_roots", 0),
            "total_pages": data1_result.get("total_pages", 0),
            "data": list(comparison.values())
        }
    except Exception as e:
        print(f"Error in compare_months: {str(e)}")
        return {"page": page, "limit": limit, "total_roots": 0, "total_pages": 0, "data": []}

# ======================== DEBUG UTILITY (compact) ========================
def get_reseller_activity_detail(reseller_code, start_dt, end_dt):
    """Debug utility - compact version"""
    try:
        daily_query = text("""
            SELECT CAST(tgl_entri AS DATE) as trx_date, COUNT(kode) as daily_count
            FROM transaksi WHERE kode_reseller = :reseller_code AND tgl_entri >= :start_dt AND tgl_entri <= :end_dt
            GROUP BY CAST(tgl_entri AS DATE) ORDER BY trx_date
        """)
        
        results = db.session.execute(daily_query, {
            'reseller_code': reseller_code, 'start_dt': start_dt, 'end_dt': end_dt
        }).fetchall()
        
        daily_transactions = {row[0]: row[1] for row in results}
        has_min_daily = any(count >= 3 for count in daily_transactions.values())
        has_no_gap = _has_no_15_day_gap_simple(list(daily_transactions.keys()), start_dt, end_dt)
        
        return {
            "reseller_code": reseller_code,
            "transaction_dates": [(str(row[0]), row[1]) for row in results],
            "has_min_daily_trx": has_min_daily, "has_no_15_day_gap": has_no_gap,
            "is_active": has_min_daily and has_no_gap
        }
    except Exception as e:
        return {"reseller_code": reseller_code, "error": str(e)}