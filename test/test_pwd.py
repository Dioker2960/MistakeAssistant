import requests

BASE = "http://127.0.0.1:8080"


def test_change_password():
    # 1. 用 alice 登录
    r = requests.post(f"{BASE}/auth/login", json={
        "username": "alice", "password": "123456"
    })
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]

    # 2. 旧密码错误 → 应该失败
    r = requests.post(
        f"{BASE}/auth/change-password",
        json={"old_password": "wrong", "new_password": "newpass123"},
        headers={"Authorization": f"Bearer {token}"},
    )
    print(f"旧密码错误: {r.status_code}（应该 400）") 
    print(f"  响应: {r.text}")

    # 3. 正确改密码
    r = requests.post(
        f"{BASE}/auth/change-password",
        json={"old_password": "123456", "new_password": "newpass123"},
        headers={"Authorization": f"Bearer {token}"},
    )
    print(f"改密码成功: {r.status_code}（应该 204）")

    # 4. 用旧密码登录 → 应该失败
    r = requests.post(f"{BASE}/auth/login", json={
        "username": "alice", "password": "123456"
    })
    print(f"用旧密码登录: {r.status_code}（应该 401）")

    # 5. 用新密码登录 → 应该成功
    r = requests.post(f"{BASE}/auth/login", json={
        "username": "alice", "password": "newpass123"
    })
    print(f"用新密码登录: {r.status_code}（应该 200）")

    # 6. 改回原密码（方便后续测试）
    if r.status_code == 200:
        new_token = r.json()["access_token"]
        r = requests.post(
            f"{BASE}/auth/change-password",
            json={"old_password": "newpass123", "new_password": "123456"},
            headers={"Authorization": f"Bearer {new_token}"},
        )
        print(f"改回原密码: {r.status_code}")


if __name__ == "__main__":
    test_change_password()