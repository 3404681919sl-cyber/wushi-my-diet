"""鉴权链路测试：注册 / 登录 / 当前用户 / 错误密码 / 画像。

覆盖验收门槛 #3：注册 → 登录 → 带 token 访问 /me → 错误密码拒绝。
所有用例使用 SQLite 内存库（见 conftest），密码经 bcrypt 哈希，绝不返回明文。
"""

from __future__ import annotations

from httpx import AsyncClient

API = "/api/v1"


async def _register_and_login(client: AsyncClient, email: str = "alice@example.com", password: str = "secret123") -> dict:
    """辅助：注册并登录，返回 token 与基础信息。"""
    reg = await client.post(
        f"{API}/auth/register",
        json={"email": email, "password": password, "nickname": "小易"},
    )
    assert reg.status_code == 201, reg.text
    login = await client.post(f"{API}/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200, login.text
    return login.json()


async def test_register_returns_user_without_password_hash(client: AsyncClient) -> None:
    """注册成功返回 201，且响应体不含密码哈希明文。"""
    resp = await client.post(
        f"{API}/auth/register",
        json={"email": "bob@example.com", "password": "secret123", "nickname": "阿减"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "bob@example.com"
    assert body["nickname"] == "阿减"
    assert "password" not in body
    assert "password_hash" not in body


async def test_duplicate_email_conflict(client: AsyncClient) -> None:
    """重复邮箱注册返回 409。"""
    payload = {"email": "dup@example.com", "password": "secret123", "nickname": "x"}
    first = await client.post(f"{API}/auth/register", json=payload)
    assert first.status_code == 201
    second = await client.post(f"{API}/auth/register", json=payload)
    assert second.status_code == 409


async def test_login_wrong_password_rejected(client: AsyncClient) -> None:
    """错误密码登录返回 401。"""
    await client.post(
        f"{API}/auth/register",
        json={"email": "carol@example.com", "password": "rightpass", "nickname": "c"},
    )
    bad = await client.post(
        f"{API}/auth/login", json={"email": "carol@example.com", "password": "wrongpass"}
    )
    assert bad.status_code == 401


async def test_login_then_me(client: AsyncClient) -> None:
    """登录拿 token 后，带 token 访问 /me 返回当前用户。"""
    token = (await _register_and_login(client, email="dave@example.com"))["access_token"]
    me = await client.get(
        f"{API}/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert me.status_code == 200
    body = me.json()
    assert body["email"] == "dave@example.com"


async def test_me_without_token_rejected(client: AsyncClient) -> None:
    """未带 token 访问 /me 返回 401。"""
    me = await client.get(f"{API}/auth/me")
    assert me.status_code == 401


async def test_profile_default_and_update(client: AsyncClient) -> None:
    """GET /profile 返回默认目标权重；PUT 后权重更新。"""
    token = (await _register_and_login(client, email="erin@example.com"))["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    got = await client.get(f"{API}/profile", headers=headers)
    assert got.status_code == 200
    profile = got.json()
    assert profile["target_weights"] == {
        "gut_stability": 0.7,
        "blood_sugar": 0.2,
        "fat_loss": 0.1,
    }

    new_weights = {"gut_stability": 0.5, "blood_sugar": 0.3, "fat_loss": 0.2}
    updated = await client.put(
        f"{API}/profile", headers=headers, json={"target_weights": new_weights}
    )
    assert updated.status_code == 200
    assert updated.json()["target_weights"] == new_weights


async def test_wechat_login_not_implemented(client: AsyncClient) -> None:
    """微信登录预留接口返回 501。"""
    resp = await client.post(f"{API}/auth/wechat-login", json={"code": "fake-code"})
    assert resp.status_code == 501
