#!/usr/bin/env python3
import os
import csv
import pymysql

# MySQL configuration
MYSQL_CONFIG = {
    'host': 'database-3.cl7a5hmtnxws.us-east-1.rds.amazonaws.com',
    'user': 'congtian',
    'password': 'DbrWQkCVZu90n9H+112A2A==',
    'database': 'resume',
    'port': 3306
}

# Additional tables to migrate
ADDITIONAL_TABLES = ['job_matches', 'skill_gaps', 'user_industry_alignment']

def import_to_mysql_batch():
    """Import additional table data to MySQL using batch inserts"""
    print("📥 Importing additional tables to MySQL...")
    
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        
        for table in ADDITIONAL_TABLES:
            csv_file = f'{table}.csv'
            if not os.path.exists(csv_file):
                print(f"⚠️ {csv_file} not found, skipping {table}")
                continue
                
            try:
                total_rows = 0
                batch_size = 1000
                batch_data = []
                
                with open(csv_file, 'r') as f:
                    reader = csv.reader(f, delimiter=',')
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
        print("🎉 Additional tables migration completed!")
        
    except Exception as e:
        print(f"❌ MySQL import failed: {e}")

def get_mysql_counts():
    """Get row counts from MySQL for verification"""
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        
        print("\n📊 Final record counts in MySQL:")
        print("Table                | Records")
        print("-" * 35)
        
        for table in ADDITIONAL_TABLES:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"{table:<20} | {count:>10}")
            except Exception as e:
                print(f"{table:<20} | Error: {e}")
        
        conn.close()
    except Exception as e:
        print(f"❌ Failed to get MySQL counts: {e}")

if __name__ == "__main__":
    print("🚀 Starting additional tables migration...")
    print("=" * 50)
    
    import_to_mysql_batch()
    get_mysql_counts()