import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# 数据库连接 URL
# 格式：mysql+pymysql://用户名:密码@主机:端口/数据库名?charset=utf8mb4

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_NAME = os.getenv("DB_NAME", "mistake_assistant")

DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    f"?charset=utf8mb4"
)


# 创建引擎（相当于 Java 的连接池 + DataSource）
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True, # 连接前先 ping，避免连接失效
)

# Session 工厂（相当于 EntityManagerFactory）
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


# 所有 ORM 模型的基类（相当于 JPA 的 @Entity 的公共父类）
class Base(DeclarativeBase):
    pass


def get_db():
    """
    FastAPI 依赖注入用的 Session 生成器。
    本阶段 Repo 里暂时手动创建 Session，这个函数先放着，
    将来做依赖注入时用。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()