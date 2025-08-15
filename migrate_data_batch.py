#!/usr/bin/env python3
import os
import csv
import subprocess
import pymysql
from datetime import datetime

# Database configurations
MYSQL_CONFIG = {
    'host': 'database-3.cl7a5hmtnxws.us-east-1.rds.amazonaws.com',
    'user': 'congtian',
    'password': 'DbrWQkCVZu90n9H+112A2A==',
    'database': 'resume',
    'port': 3306
}

# Tables to migrate in order
COMMON_TABLES = ['users', 'emsi_skills', 'user_skills_emsi', 'job_postings', 'job_skills_emsi', 'resumes']

def get_table_counts():
    """Get row counts from both databases"""
    # PostgreSQL counts
    pg_counts = {}
    try:
        cmd = "docker-compose exec -T db psql -U postgres -d skillmatch -t -c 'SELECT relname as table_name, n_live_tup as row_count FROM pg_stat_user_tables;'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = line.strip().split('|')
                    if len(parts) == 2:
                        table = parts[0].strip()
                        count = int(parts[1].strip())
                        pg_counts[table] = count
    except Exception as e:
        print(f"❌ Failed to get PostgreSQL counts: {e}")
        return None, {}
    
    # MySQL counts
    mysql_counts = {}
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        for table in COMMON_TABLES:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            mysql_counts[table] = count
        conn.close()
    except Exception as e:
        print(f"❌ Failed to get MySQL counts: {e}")
    
    return pg_counts, mysql_counts

def export_pg_data():
    """Export data from PostgreSQL to CSV files"""
    print("📦 Exporting data from PostgreSQL...")
    
    for table in COMMON_TABLES:
        try:
            # Use COPY command to export to CSV (fixed for correct user)
            cmd = f"""docker-compose exec -T db psql -U dev -d skillmatch -c "\\COPY {table} TO STDOUT WITH CSV HEADER NULL AS 'NULL'" > {table}.csv"""
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                # Check if file has data
                with open(f"{table}.csv", 'r') as f:
                    lines = len(f.readlines())
                print(f"✅ Exported {table} ({lines-1} records)")
            else:
                print(f"❌ Failed to export {table}: {result.stderr}")
        except Exception as e:
            print(f"❌ Failed to export {table}: {e}")

def import_to_mysql_batch():
    """Import data to MySQL using batch inserts"""
    print("\n📥 Importing data to MySQL...")
    
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        
        for table in COMMON_TABLES:
            csv_file = f'{table}.csv'
            if not os.path.exists(csv_file):
                print(f"⚠️ {csv_file} not found, skipping {table}")
                continue
                
            try:
                total_rows = 0
                batch_size = 1000  # Insert 1000 rows at a time
                batch_data = []
                
                with open(csv_file, 'r') as f:
                    reader = csv.reader(f, delimiter=',')  # Changed from '|' to ','
                    header = next(reader, None)
                    
                    if not header:
                        print(f"⚠️ No data in {table}")
                        continue
                    
                    # Prepare insert statement
                    placeholders = ','.join(['%s'] * len(header))
                    sql_base = f"INSERT IGNORE INTO {table} ({','.join(header)}) VALUES "
                    
                    for row in reader:
                        # Handle NULL values, empty strings, and boolean conversions
                        processed_row = []
                        for v in row:
                            if v == 'NULL' or v == '':
                                processed_row.append(None)
                            elif v == 't':  # PostgreSQL true
                                processed_row.append(1)
                            elif v == 'f':  # PostgreSQL false
                                processed_row.append(0)
                            else:
                                processed_row.append(v)
                        batch_data.append(processed_row)
                        
                        if len(batch_data) >= batch_size:
                            # Execute batch insert
                            values_str = ','.join([f"({placeholders})" for _ in batch_data])
                            sql = sql_base + values_str
                            
                            # Flatten the batch data for execution
                            flat_data = [item for sublist in batch_data for item in sublist]
                            
                            cursor.execute(sql, flat_data)
                            conn.commit()
                            total_rows += len(batch_data)
                            print(f"  → Imported {total_rows} rows to {table}...", end='\r')
                            batch_data = []
                    
                    # Insert remaining rows
                    if batch_data:
                        values_str = ','.join([f"({placeholders})" for _ in batch_data])
                        sql = sql_base + values_str
                        flat_data = [item for sublist in batch_data for item in sublist]
                        cursor.execute(sql, flat_data)
                        conn.commit()
                        total_rows += len(batch_data)
                    
                    print(f"✅ Imported {total_rows} records to {table}                    ")
                    
            except Exception as e:
                print(f"❌ Error importing {table}: {e}")
                conn.rollback()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ MySQL import failed: {e}")

def main():
    print("🚀 Starting PostgreSQL to MySQL migration (optimized)...")
    print("=" * 50)
    
    # Check initial counts
    pg_counts, mysql_counts = get_table_counts()
    if pg_counts is None:
        print("❌ Failed to get table counts")
        return 1
    
    print("📊 Current record counts:")
    print("Table                | PostgreSQL | MySQL")
    print("-" * 40)
    for table in COMMON_TABLES:
        print(f"{table:<20} | {pg_counts.get(table, 0):>10} | {mysql_counts.get(table, 0):>5}")
    
    # Export data
    export_pg_data()
    
    # Import data with batch processing
    import_to_mysql_batch()
    
    # Check final counts
    print("\n🔍 Verifying migration...")
    pg_counts_after, mysql_counts_after = get_table_counts()
    
    print("\n📊 Final record counts:")
    print("Table                | PostgreSQL | MySQL")
    print("-" * 40)
    total_pg = 0
    total_mysql = 0
    for table in COMMON_TABLES:
        pg_count = pg_counts_after.get(table, 0)
        mysql_count = mysql_counts_after.get(table, 0)
        total_pg += pg_count
        total_mysql += mysql_count
        status = "✅" if mysql_count > 0 else "❌"
        print(f"{table:<20} | {pg_count:>10} | {mysql_count:>5} {status}")
    
    print("-" * 40)
    print(f"{'TOTAL':<20} | {total_pg:>10} | {total_mysql:>5}")
    
    if total_mysql > 0:
        print(f"\n🎉 Migration completed! Migrated {total_mysql} total records")
        return 0
    else:
        print("❌ Migration failed! No data in MySQL")
        return 1

if __name__ == "__main__":
    exit(main())