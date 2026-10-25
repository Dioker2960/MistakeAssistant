"""
测试用户模块：注册 + 登录校验。
"""

from services import user_service
from schemas.user import UserCreate


def main():
    # 1. 注册
    user = user_service.create(UserCreate(username="alice", password="123456"))
    print(f"✅ 创建成功: id={user['id']}, username={user['username']}")

    # 2. 重复注册应报错
    try:
        user_service.create(UserCreate(username="alice", password="654321"))
        print("❌ 重复注册没报错")
    except Exception as e:
        print(f"✅ 重复注册被拦截: {e}")

    # 3. 密码正确
    ok = user_service.verify_password("alice", "123456")
    if ok is not None:
        print(f"✅ 密码正确: id={ok['id']}, role={ok['role']}")
    else:
        print("❌ 密码正确但校验失败")

    # 4. 密码错误
    wrong = user_service.verify_password("alice", "wrong_password")
    if wrong is None:
        print("✅ 密码错误被正确拒绝")
    else:
        print("❌ 密码错误却通过了校验")

    # 5. 用户不存在
    notexist = user_service.verify_password("bob", "123456")
    if notexist is None:
        print("✅ 用户不存在被正确拒绝")
    else:
        print("❌ 用户不存在却通过了校验")


if __name__ == "__main__":
    main()