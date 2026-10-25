import bcrypt


def hash_password(password: str) -> str:
    """把明文密码转成哈希。"""
    # bcrypt 要求输入 bytes
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_hash(password: str, hashed: str) -> bool:
    """校验密码是否匹配哈希。"""
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            hashed.encode("utf-8"),
        )
    except Exception:
        return False