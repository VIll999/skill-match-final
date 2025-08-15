#!/usr/bin/env python3
"""
Migrate data from PostgreSQL to MySQL
"""
import os
import subprocess
import pymysql
import json
from datetime import datetime
import sys

# Configuration
PG_CONFIG = {
    'host': 'localhost',
    'port': 5442,
    'user': 'dev',
    'password': 'dev',
    'database': 'skillmatch'
}

MYSQL_CONFIG = {
    'host': 'database-3.cl7a5hmtnxws.us-east-1.rds.amazonaws.com',
    'user': 'congtian',
    'password': 'DbrWQkCVZu90n9H+112A2A==',
    'database': 'resume',
    'port': 3306
}

# Tables to migrate (common between both systems)
COMMON_TABLES = [
    'users',
    'emsi_skills', 
    'user_skills_emsi',
    'job_postings',
    'job_skills_emsi',
    'resumes'
]

def export_pg_data():
    """Export data from PostgreSQL"""
    print("📦 Exporting data from PostgreSQL...")
    
    for table in COMMON_TABLES:
        try:
            # Export each table to CSV
            cmd = [
                'docker-compose', 'exec', '-T', 'db',
                'psql', '-U', PG_CONFIG['user'], '-d', PG_CONFIG['database'],
                '-c', f"\\COPY {table} TO STDOUT WITH CSV HEADER;"
            ]
            
            with open(f'{table}.csv', 'w') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
                if result.returncode != 0:
                    print(f"❌ Failed to export {table}: {result.stderr}")
                else:
                    print(f"✅ Exported {table}")
                    
        except Exception as e:
            print(f"❌ Error exporting {table}: {e}")

def get_table_counts():
    """Get record counts from both databases"""
    print("\n📊 Checking table counts...")
    
    # PostgreSQL counts
    pg_counts = {}
    for table in COMMON_TABLES:
        try:
            cmd = [
                'docker-compose', 'exec', '-T', 'db',
                'psql', '-U', PG_CONFIG['user'], '-d', PG_CONFIG['database'],
                '-t', '-c', f"SELECT COUNT(*) FROM {table};"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                pg_counts[table] = int(result.stdout.strip())
            else:
                pg_counts[table] = 0
        except:
            pg_counts[table] = 0
    
    # MySQL counts  
    mysql_counts = {}
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        for table in COMMON_TABLES:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                mysql_counts[table] = cursor.fetchone()[0]
            except:
                mysql_counts[table] = 0
        conn.close()
    except Exception as e:
        print(f"❌ MySQL connection failed: {e}")
        return None, None
    
    return pg_counts, mysql_counts

def import_to_mysql():
    """Import data to MySQL"""
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
                # Read CSV and insert data
                with open(csv_file, 'r') as f:
                    lines = f.readlines()
                    if len(lines) <= 1:  # Only header or empty
                        print(f"⚠️ No data in {table}")
                        continue
                        
                    # Skip header
                    header = lines[0].strip().split(',')
                    
                    # Prepare insert statement
                    placeholders = ','.join(['%s'] * len(header))
                    sql = f"INSERT IGNORE INTO {table} ({','.join(header)}) VALUES ({placeholders})"
                    
                    # Insert data
                    inserted = 0
                    for line in lines[1:]:
                        try:
                            values = line.strip().split(',')
                            # Handle NULL values
                            values = [None if v.upper() == 'NULL' or v == '' else v for v in values]
                            cursor.execute(sql, values)
                            inserted += 1
                        except Exception as e:
                            print(f"⚠️ Error inserting row in {table}: {e}")
                            continue
                    
                    conn.commit()
                    print(f"✅ Imported {inserted} records to {table}")
                    
            except Exception as e:
                print(f"❌ Error importing {table}: {e}")
                conn.rollback()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ MySQL import failed: {e}")

def main():
    print("🚀 Starting PostgreSQL to MySQL migration...")
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
    
    # Import data
    import_to_mysql()
    
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
        print(f"\n❌ Migration failed! No data in MySQL")
        return 1

if __name__ == "__main__":
    sys.exit(main())