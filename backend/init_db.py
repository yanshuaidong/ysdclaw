import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

import pymysql
from app.config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
from app.database import engine, Base, SessionLocal
from app.models.user import User
from app.services.user import pwd_context


def ensure_database():
    conn = pymysql.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD
    )
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
                f"DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci"
            )
        conn.commit()
        print(f"数据库 '{DB_NAME}' 已就绪")
    finally:
        conn.close()


def init():
    ensure_database()

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                password_hash=pwd_context.hash("admin123"),
                role="admin",
            )
            db.add(admin)
            db.commit()
            print("默认管理员账户已创建: admin / admin123")
        else:
            print("管理员账户已存在，跳过创建")
    finally:
        db.close()

    print("数据库初始化完成！")


if __name__ == "__main__":
    init()
