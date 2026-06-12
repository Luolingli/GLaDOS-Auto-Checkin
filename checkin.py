import os
import json
import re
import time
import random
import requests


CHECKIN_URL = "https://glados.cloud/api/user/checkin"
STATUS_URL = "https://glados.cloud/api/user/status"

HEADERS_BASE = {
    "origin": "https://glados.cloud",
    "referer": "https://glados.cloud/console/checkin",
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "content-type": "application/json;charset=UTF-8",
}

PAYLOAD = {"token": "glados.cloud"}
TIMEOUT = 10
MAX_RESPONSE_PREVIEW = 500


def push_telegram(bot_token: str, chat_id: str, title: str, content: str):
    """推送消息到 Telegram Bot"""
    if not bot_token or not chat_id:
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    text = f"{title}\n\n{content}"

    # Telegram 单条消息上限 4096 字符，做截断避免发送失败。
    if len(text) > 4000:
        text = text[:3990] + "..."

    data = {
        "chat_id": chat_id,
        "text": text,
    }

    try:
        resp = requests.post(url, json=data, timeout=TIMEOUT)
        if resp.status_code == 200 and safe_json(resp).get("ok"):
            print("✅ Telegram 推送成功")
        else:
            print(f"⚠️ Telegram 推送失败: HTTP {resp.status_code} | {resp.text}")
    except Exception as e:
        print(f"⚠️ Telegram 推送异常: {e}")


def push_all(bot_token: str, chat_id: str, title: str, content: str):
    """推送到 Telegram（如果已配置）"""
    if bot_token and chat_id:
        push_telegram(bot_token, chat_id, title, content)
    else:
        print("⚠️ 未配置 Telegram 推送，请在 Secrets 中配置 TG_BOT_TOKEN 和 TG_CHAT_ID")


def safe_json(resp):
    try:
        return resp.json()
    except Exception:
        return {}


def parse_cookies(raw: str):
    """支持每行一个 Cookie，也兼容旧版用 & 分隔多个账号。"""
    if not raw or not raw.strip():
        return []

    cookies = []
    for line in raw.replace("\r", "\n").split("\n"):
        line = line.strip()
        if not line:
            continue

        # 旧版 README 让用户用 & 拼接多个 Cookie；只在 & 后面看起来像新 Cookie
        # 键值对开头时才切分，尽量避免误伤 Cookie 值里的普通 & 字符。
        parts = re.split(r"\s*&\s*(?=[A-Za-z0-9_:%.-]+=)", line)
        cookies.extend(part.strip() for part in parts if part.strip())

    return cookies


def response_summary(resp):
    data = safe_json(resp)
    if data:
        code = data.get("code", "-")
        message = data.get("message", "")
        return f"HTTP {resp.status_code}, code={code}, message={message}"

    text = resp.text.replace("\n", " ").strip()
    if len(text) > MAX_RESPONSE_PREVIEW:
        text = text[:MAX_RESPONSE_PREVIEW] + "..."
    return f"HTTP {resp.status_code}, non-json response: {text}"


def main():
    bot_token = os.getenv("TG_BOT_TOKEN", "")
    chat_id = os.getenv("TG_CHAT_ID", "")
    cookies_env = os.getenv("COOKIES", "")
    cookies = parse_cookies(cookies_env)

    if not cookies:
        content = "❌ 未检测到 COOKIES，请在仓库 Secrets 中配置 COOKIES"
        print(content)
        push_all(bot_token, chat_id, "GLaDOS 签到失败", content)
        raise SystemExit(1)

    print(f"检测到 {len(cookies)} 个 Cookie，开始签到")

    session = requests.Session()
    ok = fail = repeat = 0
    lines = []

    for idx, cookie in enumerate(cookies, 1):
        headers = dict(HEADERS_BASE)
        headers["cookie"] = cookie

        email = "unknown"
        points = "-"
        days = "-"

        try:
            r = session.post(
                CHECKIN_URL,
                headers=headers,
                data=json.dumps(PAYLOAD),
                timeout=TIMEOUT,
            )

            j = safe_json(r)
            msg = j.get("message", "")
            msg_lower = msg.lower()

            if r.status_code != 200:
                fail += 1
                status = f"❌ 失败({response_summary(r)})"
            elif j.get("code") == -2 or "没有权限" in msg:
                fail += 1
                status = f"❌ Cookie 无效或已过期({response_summary(r)})"
            elif "repeat" in msg_lower or "already" in msg_lower:
                repeat += 1
                status = f"🔁 已签到({response_summary(r)})"
            elif "got" in msg_lower or j.get("code") == 0:
                ok += 1
                points = j.get("points", "-")
                status = f"✅ 成功({response_summary(r)})"
            else:
                fail += 1
                status = f"❌ 失败({response_summary(r)})"

            # 状态接口（允许失败）
            try:
                s = session.get(STATUS_URL, headers=headers, timeout=TIMEOUT)
                sj = safe_json(s).get("data") or {}
                email = sj.get("email", email)
                if sj.get("leftDays") is not None:
                    days = f"{int(float(sj['leftDays']))} 天"
            except requests.RequestException as e:
                print(f"⚠️ 状态查询失败: {type(e).__name__}: {e}")

        except requests.RequestException as e:
            fail += 1
            status = f"❌ 网络异常({type(e).__name__}: {e})"
        except Exception as e:
            fail += 1
            status = f"❌ 脚本异常({type(e).__name__}: {e})"

        lines.append(f"{idx}. {email} | {status} | P:{points} | 剩余:{days}")
        time.sleep(random.uniform(1, 2))

    title = f"GLaDOS 签到完成 ✅{ok} ❌{fail} 🔁{repeat}"
    content = "\n".join(lines)

    print(content)

    push_all(bot_token, chat_id, title, content)

    if fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
