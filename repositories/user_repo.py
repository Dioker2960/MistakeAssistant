import json

from sqlalchemy import select

from core.database import SessionLocal
from models.user import User


def _to_dict(obj: User) -> dict:
    """把 ORM 对象转成 dict。"""
    # TODO: 返回 id、username、password_hash、role、created_at、updated_at
    return {
        "id": obj.id,
        "username": obj.username,
        "password_hash": obj.password_hash,
        "role": obj.role,
        "created_at": obj.created_at,
        "updated_at": obj.updated_at,
    }


def save(user: dict) -> dict:
    """写入用户。"""
    # 1. 把 dict 转成 ORM 对象
    obj = User(**user)
    # 2. 打开一个 Session   with   as   相当于try catch
    with SessionLocal() as session:
        session.add(obj)
        session.commit()
        session.refresh(obj)
        return _to_dict(obj)


def get_by_id(user_id: str) -> dict | None:
    """按 id 查询。"""
    with SessionLocal() as session:
        obj = session.get(User, user_id)
        if obj is None:
            return None
        return _to_dict(obj)


def get_by_username(username: str) -> dict | None:
    """按用户名查询。登录时会用到。"""
    # TODO: 用 select(User).where(User.username == username)
    with SessionLocal() as session:
        stmt = select(User).where(User.username == username)
        obj = session.scalars(stmt).first()   # ← 执行查询，取第一条
        if obj is None:
            return None
        return _to_dict(obj)


def update_password(user_id: str, new_hash: str) -> bool:
    """更新密码哈希。成功返回 True，用户不存在返回 False。"""
    with SessionLocal() as session:
        obj = session.get(User, user_id)
        if obj is None:
            return False
        obj.password_hash = new_hash
        session.commit()
        return True
