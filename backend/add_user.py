import sys
from services.auth import AuthService
from services.user import UserService

# 初始化服务
auth_service = AuthService()
user_service = UserService()

def add_user(username, password):
    print(f"Creating user '{username}'...")
    
    # 检查用户是否存在
    conn = user_service._get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE username = %s", (username,))
            existing = cur.fetchone()
            if existing:
                print(f"User '{username}' already exists. Updating password...")
                password_hash = auth_service.get_password_hash(password)
                cur.execute("UPDATE users SET password_hash = %s WHERE username = %s", (password_hash, username))
                conn.commit()
                print("Password updated.")
                return

            # 创建新用户
            password_hash = auth_service.get_password_hash(password)
            import uuid
            user_id = str(uuid.uuid4())
            
            cur.execute(
                "INSERT INTO users (id, username, password_hash) VALUES (%s, %s, %s)",
                (user_id, username, password_hash)
            )
            
            # 创建默认会话
            default_thread_id = str(uuid.uuid4())
            cur.execute(
                "INSERT INTO threads (id, user_id, title) VALUES (%s, %s, %s)",
                (default_thread_id, user_id, "默认会话")
            )
            
            conn.commit()
            print(f"User '{username}' created with ID: {user_id}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python add_user.py <username> <password>")
        print("Example: python add_user.py admin 123456")
        
        # 默认执行一个测试用户
        print("\nCreating default test user: admin / 123456")
        add_user("admin", "123456")
    else:
        add_user(sys.argv[1], sys.argv[2])
