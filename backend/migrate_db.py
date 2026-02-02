import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def migrate():
    host = os.getenv("DB_HOST", "localhost")
    port = int(os.getenv("DB_PORT", "3306"))
    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "123456")
    database = os.getenv("DB_NAME", "eat")

    print(f"Connecting to {host}:{port} ({database})...")
    
    try:
        conn = pymysql.connect(
            host=host, port=port, user=user, password=password, database=database,
            autocommit=True
        )
        with conn.cursor() as cur:
            # Check if column exists
            cur.execute("""
                SELECT COUNT(*) as cnt 
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'users' AND COLUMN_NAME = 'password_hash'
            """, (database,))
            res = cur.fetchone()
            if res and res[0] > 0:
                print("Column 'password_hash' already exists.")
            else:
                print("Adding column 'password_hash'...")
                cur.execute("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255) NOT NULL DEFAULT '' COMMENT '密码哈希值'")
                print("Done.")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    migrate()
