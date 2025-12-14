import csv
import json
import sqlite3
import os
import sys
import glob
import re
from collections import OrderedDict
from datetime import datetime
import time

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    banner = """
    ╔═══════════════════════════════════════════════════╗
    ║      🗃️  مبدل حرفه‌ای پایگاه‌داده و فرمت‌ها      ║
    ║        Database & Format Converter v3.1          ║
    ║  پشتیبانی از: CSV, JSON, SQLite, SQL, TXT        ║
    ╚═══════════════════════════════════════════════════╝
    """
    print("\033[96m" + banner + "\033[0m")

def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    colors = {
        "INFO": "\033[94m",
        "WARNING": "\033[93m",
        "ERROR": "\033[91m",
        "SUCCESS": "\033[92m",
        "STATS": "\033[95m",
        "DEBUG": "\033[90m"
    }
    color = colors.get(level, "\033[0m")
    print(f"{color}[{timestamp}] {level}: {message}\033[0m")

def get_files_in_directory(extensions, description="فایل"):
    files = []
    
    for ext in extensions:
        pattern = f"*.{ext}"
        matched_files = glob.glob(pattern)
        for file in matched_files:
            size = os.path.getsize(file)
            size_str = f"{size:,} بایت"
            if size > 1024*1024:
                size_str = f"{size/(1024*1024):.1f} مگابایت"
            elif size > 1024:
                size_str = f"{size/1024:.1f} کیلوبایت"
            
            files.append({
                'path': file,
                'name': os.path.basename(file),
                'size': size_str,
                'ext': ext
            })
    
    if not files:
        print(f"\n⚠️  هیچ {description}‌ای با فرمت‌های {', '.join(extensions)} پیدا نشد!")
        return None
    
    files.sort(key=lambda x: x['name'].lower())
    
    print(f"\n📂 {description}‌های موجود در این پوشه:")
    print("="*70)
    print(f"{'شماره':<5} {'نام فایل':<35} {'حجم':<15} {'فرمت':<8}")
    print("-"*70)
    
    for i, file in enumerate(files, 1):
        print(f"{i:<5} {file['name']:<35} {file['size']:<15} {file['ext'].upper():<8}")
    
    print("="*70)
    
    while True:
        try:
            choice = input(f"\n📌 شماره فایل مورد نظر را انتخاب کنید (1-{len(files)}) یا 0 برای وارد کردن مسیر دستی: ").strip()
            
            if choice == '0':
                manual_path = input("📍 مسیر کامل فایل را وارد کنید: ").strip()
                if os.path.exists(manual_path):
                    return manual_path
                else:
                    print("⚠️  فایل یافت نشد!")
                    continue
            
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(files):
                    return files[idx]['path']
            
            print(f"⚠️  لطفاً عدد بین 1 تا {len(files)} وارد کنید")
            
        except KeyboardInterrupt:
            return None
        except Exception as e:
            print("⚠️  ورودی نامعتبر!")

def select_from_list(items, item_type="آیتم"):
    if not items:
        return None
    
    print(f"\n📋 {item_type}‌های موجود:")
    for i, item in enumerate(items, 1):
        print(f"  {i}. {item}")
    
    while True:
        try:
            choice = input(f"\n📌 شماره {item_type} مورد نظر (1-{len(items)}): ").strip()
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(items):
                    return items[idx]
            print(f"⚠️  لطفاً عدد بین 1 تا {len(items)} وارد کنید")
        except KeyboardInterrupt:
            return None

def csv_to_json(csv_path, json_path):
    try:
        log(f"شروع تبدیل CSV به JSON", "INFO")
        
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"فایل CSV یافت نشد: {csv_path}")
        
        data = []
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                data.append(row)
        
        log(f"{len(data)} ردیف خوانده شد", "STATS")
        
        with open(json_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, indent=2, ensure_ascii=False)
        
        log(f"فایل JSON با موفقیت ایجاد شد: {json_path}", "SUCCESS")
        return True
        
    except Exception as e:
        log(f"خطا در تبدیل CSV به JSON: {str(e)}", "ERROR")
        return False

def csv_to_sqlite(csv_path, db_path, table_name="data"):
    try:
        log(f"شروع تبدیل CSV به SQLite", "INFO")
        
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"فایل CSV یافت نشد: {csv_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            lines = csvfile.readlines()
            
            if not lines:
                raise ValueError("فایل CSV خالی است")

            first_line = lines[0].strip()
            delimiters = [',', ';', '\t', '|', ':', '#', '~']
            delimiter = ','
            
            for delim in delimiters:
                if delim in first_line:
                    delimiter = delim
                    break
            
            log(f"جداکننده تشخیص داده شده: '{delimiter}'", "STATS")
            
            headers = first_line.strip().split(delimiter)
            log(f"تعداد ستون‌ها: {len(headers)}", "STATS")

            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                {', '.join([f'"{col}" TEXT' for col in headers])}
            )
            """
            cursor.execute(create_table_sql)

            insert_sql = f"""
            INSERT INTO {table_name} ({', '.join([f'"{col}"' for col in headers])})
            VALUES ({', '.join(['?' for _ in headers])})
            """
            
            row_count = 0
            batch_size = 1000
            batch_data = []
            
            for i, line in enumerate(lines[1:], 1):
                line = line.strip()
                if not line:
                    continue
                    
                values = line.split(delimiter)
                if len(values) != len(headers):

                    values = values + [''] * (len(headers) - len(values))
                elif len(values) > len(headers):
                    values = values[:len(headers)]
                
                batch_data.append(values)
                
                if len(batch_data) >= batch_size:
                    cursor.executemany(insert_sql, batch_data)
                    row_count += len(batch_data)
                    batch_data = []
                    
                    if row_count % 10000 == 0:
                        log(f"تاکنون {row_count} ردیف ذخیره شد", "STATS")

            if batch_data:
                cursor.executemany(insert_sql, batch_data)
                row_count += len(batch_data)
            
            conn.commit()
        
        log(f"{row_count} ردیف در دیتابیس ذخیره شد", "STATS")
        
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        
        log(f"جدول '{table_name}' ایجاد شد:", "STATS")
        log(f"  • تعداد سطرها: {count}", "STATS")
        log(f"  • تعداد ستون‌ها: {len(headers)}", "STATS")
        
        conn.close()
        log(f"دیتابیس SQLite با موفقیت ایجاد شد: {db_path}", "SUCCESS")
        return True
        
    except Exception as e:
        log(f"خطا در تبدیل CSV به SQLite: {str(e)}", "ERROR")
        return False

def csv_to_sql(csv_path, sql_path, table_name="data"):
    try:
        log(f"شروع تبدیل CSV به SQL", "INFO")
        
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"فایل CSV یافت نشد: {csv_path}")
        
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            lines = csvfile.readlines()
            
            if not lines:
                raise ValueError("فایل CSV خالی است")

            first_line = lines[0].strip()
            delimiters = [',', ';', '\t', '|', ':', '#', '~']
            delimiter = ','
            
            for delim in delimiters:
                if delim in first_line:
                    delimiter = delim
                    break
            
            log(f"جداکننده تشخیص داده شده: '{delimiter}'", "STATS")

            headers = first_line.strip().split(delimiter)
            
            data = []
            for line in lines[1:]:
                line = line.strip()
                if not line:
                    continue
                    
                values = line.split(delimiter)
                if len(values) != len(headers):
                    values = values + [''] * (len(headers) - len(values))
                elif len(values) > len(headers):
                    values = values[:len(headers)]
                
                data.append(values)
        
        log(f"{len(data)} ردیف خوانده شد", "STATS")
        
        with open(sql_path, 'w', encoding='utf-8') as sqlfile:
            sqlfile.write(f"-- ایجاد جدول {table_name}\n")
            sqlfile.write(f"CREATE TABLE {table_name} (\n")
            
            columns = []
            for header in headers:
                columns.append(f"    {header} VARCHAR(255)")
            
            sqlfile.write(",\n".join(columns))
            sqlfile.write("\n);\n\n")

            sqlfile.write(f"-- درج داده‌ها در جدول {table_name}\n")
            
            batch_size = 500
            for i in range(0, len(data), batch_size):
                batch = data[i:i+batch_size]
                
                sqlfile.write(f"INSERT INTO {table_name} ({', '.join(headers)}) VALUES\n")
                
                values_list = []
                for row in batch:
                    escaped_values = []
                    for value in row:
                        if not value or value == 'NULL':
                            escaped_values.append("NULL")
                        else:
                            escaped = str(value).replace("'", "''")
                            escaped_values.append(f"'{escaped}'")
                    
                    values_list.append(f"    ({', '.join(escaped_values)})")
                
                sqlfile.write(",\n".join(values_list))
                sqlfile.write(";\n\n")
        
        log(f"فایل SQL با موفقیت ایجاد شد: {sql_path}", "SUCCESS")
        log(f"  • تعداد INSERT statement: {(len(data) + batch_size - 1) // batch_size}", "STATS")
        return True
        
    except Exception as e:
        log(f"خطا در تبدیل CSV به SQL: {str(e)}", "ERROR")
        return False

def csv_to_txt(csv_path, txt_path, delimiter="|"):
    try:
        log(f"شروع تبدیل CSV به TXT", "INFO")
        
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"فایل CSV یافت نشد: {csv_path}")
        
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            lines = csvfile.readlines()
        
        with open(txt_path, 'w', encoding='utf-8') as txtfile:
            for line in lines:
                if delimiter != ',':
                    line = line.replace(',', delimiter)
                txtfile.write(line)
        
        log(f"{len(lines)} ردیف به فایل TXT نوشته شد", "STATS")
        log(f"فایل TXT با موفقیت ایجاد شد: {txt_path}", "SUCCESS")
        return True
        
    except Exception as e:
        log(f"خطا در تبدیل CSV به TXT: {str(e)}", "ERROR")
        return False

def json_to_csv(json_path, csv_path):
    try:
        log(f"شروع تبدیل JSON به CSV", "INFO")
        
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"فایل JSON یافت نشد: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as jsonfile:
            data = json.load(jsonfile)
        
        if not data:
            raise ValueError("فایل JSON خالی است")
        
        headers = list(data[0].keys())
        
        with open(csv_path, 'w', encoding='utf-8', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            for row in data:
                writer.writerow(row)
        
        log(f"{len(data)} ردیف به CSV تبدیل شد", "STATS")
        log(f"فایل CSV با موفقیت ایجاد شد: {csv_path}", "SUCCESS")
        return True
        
    except Exception as e:
        log(f"خطا در تبدیل JSON به CSV: {str(e)}", "ERROR")
        return False

def json_to_sqlite(json_path, db_path, table_name="data"):
    try:
        log(f"شروع تبدیل JSON به SQLite", "INFO")
        
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"فایل JSON یافت نشد: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as jsonfile:
            data = json.load(jsonfile)
        
        if not data:
            raise ValueError("فایل JSON خالی است")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        headers = list(data[0].keys())
        
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            {', '.join([f'"{col}" TEXT' for col in headers])}
        )
        """
        cursor.execute(create_table_sql)
        
        insert_sql = f"""
        INSERT INTO {table_name} ({', '.join([f'"{col}"' for col in headers])})
        VALUES ({', '.join(['?' for _ in headers])})
        """
        
        row_count = 0
        batch_size = 1000
        batch_data = []
        
        for row in data:
            values = [row.get(col, "") for col in headers]
            batch_data.append(values)
            
            if len(batch_data) >= batch_size:
                cursor.executemany(insert_sql, batch_data)
                row_count += len(batch_data)
                batch_data = []
                
                if row_count % 10000 == 0:
                    log(f"تاکنون {row_count} ردیف ذخیره شد", "STATS")
        
        if batch_data:
            cursor.executemany(insert_sql, batch_data)
            row_count += len(batch_data)
        
        conn.commit()
        conn.close()
        
        log(f"{row_count} ردیف در دیتابیس ذخیره شد", "STATS")
        log(f"دیتابیس SQLite با موفقیت ایجاد شد: {db_path}", "SUCCESS")
        return True
        
    except Exception as e:
        log(f"خطا در تبدیل JSON به SQLite: {str(e)}", "ERROR")
        return False

def json_to_sql(json_path, sql_path, table_name="data"):
    try:
        log(f"شروع تبدیل JSON به SQL", "INFO")
        
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"فایل JSON یافت نشد: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as jsonfile:
            data = json.load(jsonfile)
        
        if not data:
            raise ValueError("فایل JSON خالی است")
        
        headers = list(data[0].keys())
        
        with open(sql_path, 'w', encoding='utf-8') as sqlfile:
            sqlfile.write(f"-- ایجاد جدول {table_name}\n")
            sqlfile.write(f"CREATE TABLE {table_name} (\n")
            
            columns = []
            for header in headers:
                columns.append(f"    {header} VARCHAR(255)")
            
            sqlfile.write(",\n".join(columns))
            sqlfile.write("\n);\n\n")
            
            sqlfile.write(f"-- درج داده‌ها در جدول {table_name}\n")
            
            batch_size = 500
            for i in range(0, len(data), batch_size):
                batch = data[i:i+batch_size]
                
                sqlfile.write(f"INSERT INTO {table_name} ({', '.join(headers)}) VALUES\n")
                
                values_list = []
                for row in batch:
                    escaped_values = []
                    for header in headers:
                        value = row.get(header, "")
                        if not value or value == 'NULL':
                            escaped_values.append("NULL")
                        else:
                            escaped = str(value).replace("'", "''")
                            escaped_values.append(f"'{escaped}'")
                    
                    values_list.append(f"    ({', '.join(escaped_values)})")
                
                sqlfile.write(",\n".join(values_list))
                sqlfile.write(";\n\n")
        
        log(f"فایل SQL با موفقیت ایجاد شد: {sql_path}", "SUCCESS")
        log(f"  • تعداد INSERT statement: {(len(data) + batch_size - 1) // batch_size}", "STATS")
        return True
        
    except Exception as e:
        log(f"خطا در تبدیل JSON به SQL: {str(e)}", "ERROR")
        return False

def json_to_txt(json_path, txt_path, delimiter="|"):
    try:
        log(f"شروع تبدیل JSON به TXT", "INFO")
        
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"فایل JSON یافت نشد: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as jsonfile:
            data = json.load(jsonfile)
        
        if not data:
            raise ValueError("فایل JSON خالی است")
        
        headers = list(data[0].keys())
        
        with open(txt_path, 'w', encoding='utf-8') as txtfile:
            txtfile.write(delimiter.join(headers) + "\n")
            
            for row in data:
                values = [str(row.get(col, "")) for col in headers]
                txtfile.write(delimiter.join(values) + "\n")
        
        log(f"{len(data)} ردیف به فایل TXT نوشته شد", "STATS")
        log(f"فایل TXT با موفقیت ایجاد شد: {txt_path}", "SUCCESS")
        return True
        
    except Exception as e:
        log(f"خطا در تبدیل JSON به TXT: {str(e)}", "ERROR")
        return False

def sqlite_to_csv(db_path, csv_path, table_name=None):
    try:
        log(f"شروع تبدیل SQLite به CSV", "INFO")
        
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"فایل دیتابیس یافت نشد: {db_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        if not table_name:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [t[0] for t in cursor.fetchall()]
            
            if not tables:
                raise ValueError("هیچ جدولی در دیتابیس یافت نشد")
            
            table_name = select_from_list(tables, "جدول")
            if not table_name:
                return False
        
        cursor.execute(f"SELECT * FROM {table_name}")
        data = cursor.fetchall()
        
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns_info = cursor.fetchall()
        headers = [col[1] for col in columns_info]
        
        with open(csv_path, 'w', encoding='utf-8', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            writer.writerows(data)
        
        conn.close()
        
        log(f"{len(data)} ردیف از جدول '{table_name}' به CSV تبدیل شد", "STATS")
        log(f"فایل CSV با موفقیت ایجاد شد: {csv_path}", "SUCCESS")
        return True
        
    except Exception as e:
        log(f"خطا در تبدیل SQLite به CSV: {str(e)}", "ERROR")
        return False

def sqlite_to_json(db_path, json_path, table_name=None):
    try:
        log(f"شروع تبدیل SQLite به JSON", "INFO")
        
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"فایل دیتابیس یافت نشد: {db_path}")
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if not table_name:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [t[0] for t in cursor.fetchall()]
            
            if not tables:
                raise ValueError("هیچ جدولی در دیتابیس یافت نشد")
            
            table_name = select_from_list(tables, "جدول")
            if not table_name:
                return False
        
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        data = [dict(row) for row in rows]
        
        with open(json_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, indent=2, ensure_ascii=False)
        
        conn.close()
        
        log(f"{len(data)} ردیف از جدول '{table_name}' به JSON تبدیل شد", "STATS")
        log(f"فایل JSON با موفقیت ایجاد شد: {json_path}", "SUCCESS")
        return True
        
    except Exception as e:
        log(f"خطا در تبدیل SQLite به JSON: {str(e)}", "ERROR")
        return False

def sqlite_to_sql(db_path, sql_path, table_name=None):
    try:
        log(f"شروع تبدیل SQLite به SQL", "INFO")
        
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"فایل دیتابیس یافت نشد: {db_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        if not table_name:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [t[0] for t in cursor.fetchall()]
            
            if not tables:
                raise ValueError("هیچ جدولی در دیتابیس یافت نشد")
            
            table_name = select_from_list(tables, "جدول")
            if not table_name:
                return False
        
        cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        create_table_result = cursor.fetchone()
        create_table_sql = create_table_result[0] if create_table_result else ""
        
        if not create_table_sql:
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns_info = cursor.fetchall()
            columns = []
            for col in columns_info:
                col_name = col[1]
                col_type = col[2]
                columns.append(f"{col_name} {col_type}")
            
            create_table_sql = f"CREATE TABLE {table_name} (\n    " + ",\n    ".join(columns) + "\n)"
        
        cursor.execute(f"SELECT * FROM {table_name}")
        data = cursor.fetchall()
        
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns_info = cursor.fetchall()
        headers = [col[1] for col in columns_info]
        
        with open(sql_path, 'w', encoding='utf-8') as sqlfile:
            sqlfile.write(f"-- SQL dump of table '{table_name}'\n")
            sqlfile.write(f"-- Generated by Database Converter\n\n")
            
            sqlfile.write(f"{create_table_sql};\n\n")
            
            if data:
                sqlfile.write(f"-- داده‌های جدول '{table_name}'\n")
                
                batch_size = 500
                for i in range(0, len(data), batch_size):
                    batch = data[i:i+batch_size]
                    
                    sqlfile.write(f"INSERT INTO {table_name} ({', '.join(headers)}) VALUES\n")
                    
                    values_list = []
                    for row in batch:
                        escaped_values = []
                        for value in row:
                            if value is None:
                                escaped_values.append("NULL")
                            else:
                                escaped = str(value).replace("'", "''")
                                escaped_values.append(f"'{escaped}'")
                        
                        values_list.append(f"    ({', '.join(escaped_values)})")
                    
                    sqlfile.write(",\n".join(values_list))
                    sqlfile.write(";\n\n")
        
        conn.close()
        
        log(f"{len(data)} ردیف از جدول '{table_name}' به SQL تبدیل شد", "STATS")
        log(f"فایل SQL با موفقیت ایجاد شد: {sql_path}", "SUCCESS")
        return True
        
    except Exception as e:
        log(f"خطا در تبدیل SQLite به SQL: {str(e)}", "ERROR")
        return False

def sqlite_to_txt(db_path, txt_path, table_name=None, delimiter="|"):
    try:
        log(f"شروع تبدیل SQLite به TXT", "INFO")
        
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"فایل دیتابیس یافت نشد: {db_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        if not table_name:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [t[0] for t in cursor.fetchall()]
            
            if not tables:
                raise ValueError("هیچ جدولی در دیتابیس یافت نشد")
            
            if len(tables) == 1:
                table_name = tables[0]
            else:
                table_name = select_from_list(tables, "جدول")
                if not table_name:
                    return False
        
        cursor.execute(f"SELECT * FROM {table_name}")
        data = cursor.fetchall()
        
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns_info = cursor.fetchall()
        headers = [col[1] for col in columns_info]
        
        with open(txt_path, 'w', encoding='utf-8') as txtfile:
            txtfile.write(delimiter.join(headers) + "\n")
            
            for row in data:
                values = [str(item) if item is not None else "" for item in row]
                txtfile.write(delimiter.join(values) + "\n")
        
        conn.close()
        
        log(f"{len(data)} ردیف از جدول '{table_name}' به TXT تبدیل شد", "STATS")
        log(f"فایل TXT با موفقیت ایجاد شد: {txt_path}", "SUCCESS")
        return True
        
    except Exception as e:
        log(f"خطا در تبدیل SQLite به TXT: {str(e)}", "ERROR")
        return False

def parse_sql_file(sql_path):
    try:
        with open(sql_path, 'r', encoding='utf-8') as sqlfile:
            content = sqlfile.read()

        content = re.sub(r'--.*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)

        create_table_match = re.search(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?"?(\w+)"?\s*\((.*?)\)\s*;', content, re.IGNORECASE | re.DOTALL)
        
        if not create_table_match:
            raise ValueError("دستور CREATE TABLE در فایل SQL یافت نشد")
        
        table_name = create_table_match.group(1)
        columns_section = create_table_match.group(2)

        columns = []
        lines = columns_section.split('\n')
        for line in lines:
            line = line.strip().strip(',')
            if line:
                col_parts = line.split()
                if col_parts:
                    col_name = col_parts[0].strip('"\'')
                    columns.append(col_name)

        insert_pattern = r'INSERT\s+INTO\s+\w+\s+VALUES\s*\((.*?)\);'
        insert_matches = re.findall(insert_pattern, content, re.IGNORECASE | re.DOTALL)
        
        data = []
        for insert_match in insert_matches:
            values = []
            in_string = False
            current_value = ""
            
            for char in insert_match:
                if char == "'" and not (len(current_value) > 0 and current_value[-1] == '\\'):
                    in_string = not in_string
                    current_value += char
                elif char == ',' and not in_string:
                    values.append(current_value.strip())
                    current_value = ""
                else:
                    current_value += char
            
            if current_value:
                values.append(current_value.strip())
            
            cleaned_values = []
            for value in values:
                if value.upper() == 'NULL':
                    cleaned_values.append(None)
                elif value.startswith("'") and value.endswith("'"):
                    cleaned_values.append(value[1:-1].replace("''", "'"))
                else:
                    cleaned_values.append(value)
            
            data.append(cleaned_values)
        
        return table_name, columns, data
        
    except Exception as e:
        raise ValueError(f"خطا در پارس کردن فایل SQL: {str(e)}")

def sql_to_csv(sql_path, csv_path):
    try:
        log(f"شروع تبدیل SQL به CSV", "INFO")
        
        if not os.path.exists(sql_path):
            raise FileNotFoundError(f"فایل SQL یافت نشد: {sql_path}")
        
        table_name, headers, data = parse_sql_file(sql_path)
        
        log(f"جدول '{table_name}' با {len(headers)} ستون و {len(data)} ردیف شناسایی شد", "STATS")
        
        with open(csv_path, 'w', encoding='utf-8', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            writer.writerows(data)
        
        log(f"{len(data)} ردیف به CSV تبدیل شد", "STATS")
        log(f"فایل CSV با موفقیت ایجاد شد: {csv_path}", "SUCCESS")
        return True
        
    except Exception as e:
        log(f"خطا در تبدیل SQL به CSV: {str(e)}", "ERROR")
        return False

def sql_to_json(sql_path, json_path):
    try:
        log(f"شروع تبدیل SQL به JSON", "INFO")
        
        if not os.path.exists(sql_path):
            raise FileNotFoundError(f"فایل SQL یافت نشد: {sql_path}")
        
        table_name, headers, data = parse_sql_file(sql_path)
        
        log(f"جدول '{table_name}' با {len(headers)} ستون و {len(data)} ردیف شناسایی شد", "STATS")
        
        json_data = []
        for row in data:
            item = {}
            for i, header in enumerate(headers):
                if i < len(row):
                    item[header] = row[i]
                else:
                    item[header] = None
            json_data.append(item)
        
        with open(json_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(json_data, jsonfile, indent=2, ensure_ascii=False)
        
        log(f"{len(json_data)} ردیف به JSON تبدیل شد", "STATS")
        log(f"فایل JSON با موفقیت ایجاد شد: {json_path}", "SUCCESS")
        return True
        
    except Exception as e:
        log(f"خطا در تبدیل SQL به JSON: {str(e)}", "ERROR")
        return False

def sql_to_sqlite(sql_path, db_path):
    try:
        log(f"شروع تبدیل SQL به SQLite", "INFO")
        
        if not os.path.exists(sql_path):
            raise FileNotFoundError(f"فایل SQL یافت نشد: {sql_path}")
        
        table_name, headers, data = parse_sql_file(sql_path)
        
        log(f"جدول '{table_name}' با {len(headers)} ستون و {len(data)} ردیف شناسایی شد", "STATS")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            {', '.join([f'"{col}" TEXT' for col in headers])}
        )
        """
        cursor.execute(create_table_sql)
        
        insert_sql = f"""
        INSERT INTO {table_name} ({', '.join([f'"{col}"' for col in headers])})
        VALUES ({', '.join(['?' for _ in headers])})
        """
        
        row_count = 0
        batch_size = 1000
        batch_data = []
        
        for row in data:
            batch_data.append(row)
            
            if len(batch_data) >= batch_size:
                cursor.executemany(insert_sql, batch_data)
                row_count += len(batch_data)
                batch_data = []
        
        if batch_data:
            cursor.executemany(insert_sql, batch_data)
            row_count += len(batch_data)
        
        conn.commit()
        conn.close()
        
        log(f"{row_count} ردیف در دیتابیس ذخیره شد", "STATS")
        log(f"دیتابیس SQLite با موفقیت ایجاد شد: {db_path}", "SUCCESS")
        return True
        
    except Exception as e:
        log(f"خطا در تبدیل SQL به SQLite: {str(e)}", "ERROR")
        return False

def sql_to_txt(sql_path, txt_path, delimiter="|"):
    try:
        log(f"شروع تبدیل SQL به TXT", "INFO")
        
        if not os.path.exists(sql_path):
            raise FileNotFoundError(f"فایل SQL یافت نشد: {sql_path}")
        
        table_name, headers, data = parse_sql_file(sql_path)
        
        log(f"جدول '{table_name}' با {len(headers)} ستون و {len(data)} ردیف شناسایی شد", "STATS")
        
        with open(txt_path, 'w', encoding='utf-8') as txtfile:
            txtfile.write(delimiter.join(headers) + "\n")
            
            for row in data:
                values = [str(item) if item is not None else "" for item in row]
                txtfile.write(delimiter.join(values) + "\n")
        
        log(f"{len(data)} ردیف به فایل TXT نوشته شد", "STATS")
        log(f"فایل TXT با موفقیت ایجاد شد: {txt_path}", "SUCCESS")
        return True
        
    except Exception as e:
        log(f"خطا در تبدیل SQL به TXT: {str(e)}", "ERROR")
        return False

def txt_to_csv(txt_path, csv_path, delimiter=None):
    try:
        log(f"شروع تبدیل TXT به CSV", "INFO")
        
        if not os.path.exists(txt_path):
            raise FileNotFoundError(f"فایل TXT یافت نشد: {txt_path}")
        
        with open(txt_path, 'r', encoding='utf-8') as txtfile:
            lines = [line.strip() for line in txtfile if line.strip()]
        
        if not lines:
            raise ValueError("فایل TXT خالی است")
        
        if not delimiter:
            delimiters = ['|', ',', ';', '\t', ':', '#', '~']
            max_count = 0
            
            for delim in delimiters:
                count = lines[0].count(delim)
                if count > max_count:
                    max_count = count
                    delimiter = delim
        
        log(f"جداکننده تشخیص داده شده: '{delimiter}'", "STATS")
        
        data = [line.split(delimiter) for line in lines]
        
        with open(csv_path, 'w', encoding='utf-8', newline='') as csvfile:
            writer = csv.writer(csvfile)
            for row in data:
                writer.writerow(row)
        
        log(f"{len(data)} ردیف به CSV تبدیل شد", "STATS")
        log(f"فایل CSV با موفقیت ایجاد شد: {csv_path}", "SUCCESS")
        return True
        
    except Exception as e:
        log(f"خطا در تبدیل TXT به CSV: {str(e)}", "ERROR")
        return False

def txt_to_json(txt_path, json_path, delimiter=None):
    try:
        log(f"شروع تبدیل TXT به JSON", "INFO")
        
        if not os.path.exists(txt_path):
            raise FileNotFoundError(f"فایل TXT یافت نشد: {txt_path}")
        
        with open(txt_path, 'r', encoding='utf-8') as txtfile:
            lines = [line.strip() for line in txtfile if line.strip()]
        
        if not lines:
            raise ValueError("فایل TXT خالی است")
        
        if not delimiter:
            delimiters = ['|', ',', ';', '\t', ':', '#', '~']
            max_count = 0
            
            for delim in delimiters:
                count = lines[0].count(delim)
                if count > max_count:
                    max_count = count
                    delimiter = delim
        
        log(f"جداکننده تشخیص داده شده: '{delimiter}'", "STATS")
        
        headers = lines[0].split(delimiter)
        start_idx = 1 if len(lines) > 1 and len(lines[0].split(delimiter)) == len(lines[1].split(delimiter)) else 0
        
        data = []
        for line in lines[start_idx:]:
            values = line.split(delimiter)
            if len(values) == len(headers):
                row = {headers[i]: values[i] for i in range(len(headers))}
                data.append(row)
        
        with open(json_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, indent=2, ensure_ascii=False)
        
        log(f"{len(data)} ردیف به JSON تبدیل شد", "STATS")
        log(f"فایل JSON با موفقیت ایجاد شد: {json_path}", "SUCCESS")
        return True
        
    except Exception as e:
        log(f"خطا در تبدیل TXT به JSON: {str(e)}", "ERROR")
        return False

def txt_to_sqlite(txt_path, db_path, table_name="data", delimiter=None):
    try:
        log(f"شروع تبدیل TXT به SQLite", "INFO")
        
        if not os.path.exists(txt_path):
            raise FileNotFoundError(f"فایل TXT یافت نشد: {txt_path}")
        
        with open(txt_path, 'r', encoding='utf-8') as txtfile:
            lines = [line.strip() for line in txtfile if line.strip()]
        
        if not lines:
            raise ValueError("فایل TXT خالی است")
        
        if not delimiter:
            delimiters = ['|', ',', ';', '\t', ':', '#', '~']
            max_count = 0
            
            for delim in delimiters:
                count = lines[0].count(delim)
                if count > max_count:
                    max_count = count
                    delimiter = delim
        
        log(f"جداکننده تشخیص داده شده: '{delimiter}'", "STATS")
        
        headers = lines[0].split(delimiter)
        start_idx = 1
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            {', '.join([f'"{col}" TEXT' for col in headers])}
        )
        """
        cursor.execute(create_table_sql)
        
        insert_sql = f"""
        INSERT INTO {table_name} ({', '.join([f'"{col}"' for col in headers])})
        VALUES ({', '.join(['?' for _ in headers])})
        """
        
        row_count = 0
        batch_size = 1000
        batch_data = []
        
        for line in lines[start_idx:]:
            values = line.split(delimiter)
            if len(values) == len(headers):
                batch_data.append(values)
                
                if len(batch_data) >= batch_size:
                    cursor.executemany(insert_sql, batch_data)
                    row_count += len(batch_data)
                    batch_data = []
        
        if batch_data:
            cursor.executemany(insert_sql, batch_data)
            row_count += len(batch_data)
        
        conn.commit()
        conn.close()
        
        log(f"{row_count} ردیف در دیتابیس ذخیره شد", "STATS")
        log(f"دیتابیس SQLite با موفقیت ایجاد شد: {db_path}", "SUCCESS")
        return True
        
    except Exception as e:
        log(f"خطا در تبدیل TXT به SQLite: {str(e)}", "ERROR")
        return False

def txt_to_sql(txt_path, sql_path, table_name="data", delimiter=None):
    try:
        log(f"شروع تبدیل TXT به SQL", "INFO")
        
        if not os.path.exists(txt_path):
            raise FileNotFoundError(f"فایل TXT یافت نشد: {txt_path}")
        
        with open(txt_path, 'r', encoding='utf-8') as txtfile:
            lines = [line.strip() for line in txtfile if line.strip()]
        
        if not lines:
            raise ValueError("فایل TXT خالی است")
        
        if not delimiter:
            delimiters = ['|', ',', ';', '\t', ':', '#', '~']
            max_count = 0
            
            for delim in delimiters:
                count = lines[0].count(delim)
                if count > max_count:
                    max_count = count
                    delimiter = delim
        
        log(f"جداکننده تشخیص داده شده: '{delimiter}'", "STATS")
        
        headers = lines[0].split(delimiter)
        start_idx = 1
        
        data = []
        for line in lines[start_idx:]:
            values = line.split(delimiter)
            if len(values) == len(headers):
                data.append(values)
        
        with open(sql_path, 'w', encoding='utf-8') as sqlfile:
            sqlfile.write(f"-- ایجاد جدول {table_name}\n")
            sqlfile.write(f"CREATE TABLE {table_name} (\n")
            
            columns = []
            for header in headers:
                columns.append(f"    {header} VARCHAR(255)")
            
            sqlfile.write(",\n".join(columns))
            sqlfile.write("\n);\n\n")
            
            sqlfile.write(f"-- درج داده‌ها در جدول {table_name}\n")
            
            batch_size = 500
            for i in range(0, len(data), batch_size):
                batch = data[i:i+batch_size]
                
                sqlfile.write(f"INSERT INTO {table_name} ({', '.join(headers)}) VALUES\n")
                
                values_list = []
                for row in batch:
                    escaped_values = []
                    for value in row:
                        if not value:
                            escaped_values.append("NULL")
                        else:
                            escaped = str(value).replace("'", "''")
                            escaped_values.append(f"'{escaped}'")
                    
                    values_list.append(f"    ({', '.join(escaped_values)})")
                
                sqlfile.write(",\n".join(values_list))
                sqlfile.write(";\n\n")
        
        log(f"فایل SQL با موفقیت ایجاد شد: {sql_path}", "SUCCESS")
        log(f"  • تعداد INSERT statement: {(len(data) + batch_size - 1) // batch_size}", "STATS")
        return True
        
    except Exception as e:
        log(f"خطا در تبدیل TXT به SQL: {str(e)}", "ERROR")
        return False

def get_output_filename(input_path, output_ext, default_name="output"):
    input_name = os.path.basename(input_path)
    name_without_ext = os.path.splitext(input_name)[0]
    
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', name_without_ext)
    
    if safe_name:
        return f"{safe_name}.{output_ext}"
    else:
        return f"{default_name}.{output_ext}"

def show_menu():
    clear_screen()
    print_banner()
    
    menu_options = [
        "1. CSV به JSON",
        "2. CSV به SQLite",
        "3. CSV به SQL",
        "4. CSV به TXT",
        "5. JSON به CSV",
        "6. JSON به SQLite",
        "7. JSON به SQL",
        "8. JSON به TXT",
        "9. SQLite به CSV",
        "10. SQLite به JSON",
        "11. SQLite به SQL",
        "12. SQLite به TXT",
        "13. SQL به CSV",
        "14. SQL به JSON",
        "15. SQL به SQLite",
        "16. SQL به TXT",
        "17. TXT به CSV",
        "18. TXT به JSON",
        "19. TXT به SQLite",
        "20. TXT به SQL",
        "0. خروج"
    ]
    
    print("\033[93m" + "="*70 + "\033[0m")
    print("\033[97m" + "📋 منوی اصلی:\n" + "\033[0m")
    
    for i in range(0, len(menu_options)-1, 2):
        col1 = menu_options[i]
        col2 = menu_options[i+1] if i+1 < len(menu_options)-1 else ""
        print(f"  \033[96m{col1:<25}\033[0m  \033[96m{col2}\033[0m")
    
    print(f"  \033[96m{menu_options[-1]:<25}\033[0m")
    print("\033[93m" + "="*70 + "\033[0m")
    
    while True:
        try:
            choice = input("\n📌 انتخاب شما (0-20): ").strip()
            if choice.isdigit() and 0 <= int(choice) <= 20:
                return int(choice)
            else:
                print("⚠️  لطفاً عدد بین 0 تا 20 وارد کنید")
        except KeyboardInterrupt:
            return 0
        except:
            print("⚠️  ورودی نامعتبر!")

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    while True:
        try:
            choice = show_menu()
            
            if choice == 0:
                print("\n\033[92m👋 با تشکر از استفاده شما! خدانگهدار...\033[0m")
                time.sleep(1)
                break
            
            conversions = {
                1: ("CSV به JSON", "csv_to_json", ["csv"], "json"),
                2: ("CSV به SQLite", "csv_to_sqlite", ["csv"], "db"),
                3: ("CSV به SQL", "csv_to_sql", ["csv"], "sql"),
                4: ("CSV به TXT", "csv_to_txt", ["csv"], "txt"),
                5: ("JSON به CSV", "json_to_csv", ["json"], "csv"),
                6: ("JSON به SQLite", "json_to_sqlite", ["json"], "db"),
                7: ("JSON به SQL", "json_to_sql", ["json"], "sql"),
                8: ("JSON به TXT", "json_to_txt", ["json"], "txt"),
                9: ("SQLite به CSV", "sqlite_to_csv", ["db", "sqlite", "sqlite3"], "csv"),
                10: ("SQLite به JSON", "sqlite_to_json", ["db", "sqlite", "sqlite3"], "json"),
                11: ("SQLite به SQL", "sqlite_to_sql", ["db", "sqlite", "sqlite3"], "sql"),
                12: ("SQLite به TXT", "sqlite_to_txt", ["db", "sqlite", "sqlite3"], "txt"),
                13: ("SQL به CSV", "sql_to_csv", ["sql"], "csv"),
                14: ("SQL به JSON", "sql_to_json", ["sql"], "json"),
                15: ("SQL به SQLite", "sql_to_sqlite", ["sql"], "db"),
                16: ("SQL به TXT", "sql_to_txt", ["sql"], "txt"),
                17: ("TXT به CSV", "txt_to_csv", ["txt", "text"], "csv"),
                18: ("TXT به JSON", "txt_to_json", ["txt", "text"], "json"),
                19: ("TXT به SQLite", "txt_to_sqlite", ["txt", "text"], "db"),
                20: ("TXT به SQL", "txt_to_sql", ["txt", "text"], "sql")
            }
            
            conversion_name, func_name, input_exts, output_ext = conversions[choice]
            
            clear_screen()
            print_banner()
            print(f"\n\033[93m🔄 تبدیل {conversion_name}\033[0m")
            print("\033[90m" + "="*70 + "\033[0m")
            
            print(f"\n📍 انتخاب فایل ورودی (فرمت‌های پشتیبانی شده: {', '.join(input_exts)})")
            
            input_path = get_files_in_directory(input_exts, "فایل ورودی")
            if not input_path:
                print("⚠️  عملیات لغو شد!")
                time.sleep(2)
                continue
            
            suggested_name = get_output_filename(input_path, output_ext)
            
            print(f"\n📤 فایل خروجی")
            print(f"💡 نام پیشنهادی: \033[96m{suggested_name}\033[0m")
            
            while True:
                output_name = input(f"📝 نام فایل خروجی (یا Enter برای تایید پیشنهاد): ").strip()
                
                if not output_name:
                    output_name = suggested_name
                    break
                
                if not output_name.lower().endswith(f".{output_ext}"):
                    output_name = f"{output_name}.{output_ext}"
                
                if re.search(r'[<>:"/\\|?*]', output_name):
                    print("⚠️  نام فایل حاوی کاراکترهای نامعتبر است!")
                    continue
                
                break
            
            params = {}
            
            if "txt" in func_name and func_name != "txt_to_csv":
                delim = input("🔣 جداکننده در فایل TXT (Enter برای تشخیص خودکار): ").strip()
                if delim:
                    params['delimiter'] = delim
            
            if func_name in ["csv_to_sqlite", "json_to_sqlite", "txt_to_sqlite", "sql_to_sqlite"]:
                table_name = input("📋 نام جدول (پیش‌فرض: data): ").strip()
                if table_name:
                    params['table_name'] = table_name
            
            if func_name in ["csv_to_sql", "json_to_sql", "txt_to_sql"]:
                table_name = input("📋 نام جدول در خروجی SQL (پیش‌فرض: data): ").strip()
                if table_name:
                    params['table_name'] = table_name
            
            print("\n" + "="*70)
            print("⏳ در حال پردازش...")
            
            func = globals()[func_name]
            
            start_time = time.time()
            
            try:
                if params:
                    success = func(input_path, output_name, **params)
                else:
                    success = func(input_path, output_name)
            except Exception as e:
                log(f"خطا در اجرای تابع: {str(e)}", "ERROR")
                success = False
            
            end_time = time.time()
            
            if success:
                file_size = os.path.getsize(output_name)
                size_str = f"{file_size:,} بایت"
                if file_size > 1024*1024:
                    size_str = f"{file_size/(1024*1024):.1f} مگابایت"
                elif file_size > 1024:
                    size_str = f"{file_size/1024:.1f} کیلوبایت"
                
                print(f"\n\033[92m✅ عملیات با موفقیت انجام شد!\033[0m")
                print(f"📊 \033[93mزمان اجرا:\033[0m {end_time - start_time:.2f} ثانیه")
                print(f"💾 \033[93mحجم فایل خروجی:\033[0m {size_str}")
                print(f"📁 \033[93mمسیر فایل:\033[0m {os.path.abspath(output_name)}")
            else:
                print(f"\n\033[91m❌ عملیات ناموفق بود!\033[0m")
            
            print("\n" + "="*70)
            cont = input("\nآیا می‌خواهید تبدیل دیگری انجام دهید؟ (y/n): ").lower()
            if cont != 'y':
                print("\n\033[92m👋 با تشکر از استفاده شما! خدانگهدار...\033[0m")
                time.sleep(1)
                break
                
        except KeyboardInterrupt:
            print("\n\n\033[93m⚠️  عملیات توسط کاربر متوقف شد.\033[0m")
            print("\033[92m👋 با تشکر از استفاده شما! خدانگهدار...\033[0m")
            time.sleep(1)
            break
        except Exception as e:
            print(f"\n\033[91mخطای غیرمنتظره: {str(e)}\033[0m")
            input("\nبرای ادامه Enter بزنید...")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n\033[91mخطای بحرانی: {str(e)}\033[0m")
        input("برای خروج Enter بزنید...")