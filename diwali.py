"""
=============================================================================
🎫 DIWALI GIVEAWAY - OFFICIAL TELEGRAM MINI APP BOT (ZERO-DEPENDENCY ENGINE) 🎫
=============================================================================
100% Pure Python Standard Library Telegram Bot Engine.
✅ NO 'pip install' required! Works directly in Termux, VS Code, Render & VPS!
✅ Non-blocking multi-threaded processing: Instant reply to /start and buttons!
✅ Device verification removed: Users can claim directly to Home!
✅ Owner commands for YouTube: /setyoutube <url> and /removeyoutube
✅ Telegram Premium animated emojis & channel admin checker built-in.
✅ Fixed Web App HTTPS URL requirement: /start works every single time!
=============================================================================
"""

import os
import sys
import json
import time
import re
import socket
import threading
import logging
import urllib.request
import urllib.error
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

# Set default socket timeout to 12s to prevent mobile network hangs
socket.setdefaulttimeout(12)

# ---------------------------------------------------------------------------
# 1. CORE BOT CONFIGURATION
# ---------------------------------------------------------------------------
TOKEN = os.environ.get("BOT_TOKEN", "9228884670:AAFxklyfgSa1D02HlOtQXwfkxp6Rxrz5dsY").strip()
BOT_USERNAME = os.environ.get("BOT_USERNAME", "DiwaliGiveaway0_bot").strip().lstrip("@")

# Telegram Web App strictly requires HTTPS. Auto-upgrade http:// to https://
_raw_web_url = os.environ.get("WEB_URL", "https://amazoncod.woohoo.in").strip().rstrip("/")
if _raw_web_url.startswith("http://"):
    WEB_URL = "https://" + _raw_web_url[7:]
else:
    WEB_URL = _raw_web_url

RTDB_URL = os.environ.get("RTDB_URL", "https://diwali-giveaway-default-rtdb.firebaseio.com").strip().rstrip("/")
TG_API_BASE = f"https://api.telegram.org/bot{TOKEN}"

# ---------------------------------------------------------------------------
# 2. DEFAULT MANDATORY CHANNELS
# ---------------------------------------------------------------------------
PERMANENT_CHANNELS = [
    {
        "id": "-1003479783999",
        "name": "Official Channel",
        "url": "https://t.me/+7clQNCkYuAAxYWQ1",
        "is_private": True,
    },
]

# ---------------------------------------------------------------------------
# 3. AUTHORIZED BOT OWNERS
# ---------------------------------------------------------------------------
DEFAULT_OWNERS = [
    "rohit79041",
    "boss6578",
    "lakhsmiiiii",
    "6612581369",
    "8751187524",
]

# ---------------------------------------------------------------------------
# 4. LOGGING CONFIGURATION
# ---------------------------------------------------------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("diwali_giveaway_bot")


# ---------------------------------------------------------------------------
# 5. RENDER / VPS / TERMUX 24/7 HTTP HEALTH SERVER
# ---------------------------------------------------------------------------
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json; charset=utf-8")
        self.end_headers()
        res = {
            "status": "online",
            "bot": "Diwali Giveaway Telegram Bot",
            "web_url": WEB_URL,
            "uptime": int(time.time()),
        }
        self.wfile.write(json.dumps(res).encode("utf-8"))

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        return


def start_health_server():
    port = int(os.environ.get("PORT", 8080))
    try:
        server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        logger.info(f"Health server listening on port {port}")
        server.serve_forever()
    except Exception as e:
        logger.warning(f"Health server note: {e}")


# ---------------------------------------------------------------------------
# 6. TELEGRAM BOT API CLIENT (PURE PYTHON - FAST & ROBUST)
# ---------------------------------------------------------------------------
_BOT_INFO_CACHE = None


def tg_api(method: str, payload: dict = None, timeout: int = 10) -> dict:
    url = f"{TG_API_BASE}/{method}"
    data = json.dumps(payload or {}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8")
            return json.loads(err_body)
        except Exception:
            return {"ok": False, "description": str(e)}
    except Exception as e:
        return {"ok": False, "description": str(e)}


def get_bot_info() -> dict:
    global _BOT_INFO_CACHE
    if _BOT_INFO_CACHE:
        return _BOT_INFO_CACHE
    res = tg_api("getMe", {})
    if res.get("ok") and res.get("result"):
        _BOT_INFO_CACHE = res["result"]
        return _BOT_INFO_CACHE
    return {"id": 0, "username": BOT_USERNAME}


def send_message(chat_id, text: str, reply_markup: dict = None, parse_mode: str = "HTML") -> dict:
    payload = {"chat_id": chat_id, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return tg_api("sendMessage", payload)


def edit_message_text(chat_id, message_id: int, text: str, reply_markup: dict = None, parse_mode: str = "HTML") -> dict:
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return tg_api("editMessageText", payload)


def answer_callback_query(callback_query_id: str, text: str = None, show_alert: bool = False) -> dict:
    payload = {"callback_query_id": callback_query_id, "show_alert": show_alert}
    if text:
        payload["text"] = text
    return tg_api("answerCallbackQuery", payload)


def forward_message(chat_id, from_chat_id, message_id: int) -> dict:
    return tg_api(
        "forwardMessage",
        {
            "chat_id": chat_id,
            "from_chat_id": from_chat_id,
            "message_id": message_id,
        },
    )


def copy_message(chat_id, from_chat_id, message_id: int) -> dict:
    return tg_api(
        "copyMessage",
        {
            "chat_id": chat_id,
            "from_chat_id": from_chat_id,
            "message_id": message_id,
        },
    )


def has_custom_emoji(message: dict) -> bool:
    if not message:
        return False
    entities = message.get("entities") or message.get("caption_entities") or []
    return any(e.get("type") == "custom_emoji" for e in entities)


def deliver_premium_message(target_chat_id, source_chat_id, message: dict) -> dict:
    msg_id = message.get("message_id")
    if has_custom_emoji(message):
        res = forward_message(target_chat_id, source_chat_id, msg_id)
        if res.get("ok"):
            return res

        entities = message.get("entities")
        caption_entities = message.get("caption_entities")
        reply_markup = message.get("reply_markup")

        if message.get("text") and entities:
            payload = {
                "chat_id": target_chat_id,
                "text": message["text"],
                "entities": entities,
            }
            if reply_markup:
                payload["reply_markup"] = reply_markup
            res2 = tg_api("sendMessage", payload)
            if res2.get("ok"):
                return res2

        if caption_entities:
            copy_payload = {
                "chat_id": target_chat_id,
                "from_chat_id": source_chat_id,
                "message_id": msg_id,
                "caption": message.get("caption", ""),
                "caption_entities": caption_entities,
            }
            if reply_markup:
                copy_payload["reply_markup"] = reply_markup
            res3 = tg_api("copyMessage", copy_payload)
            if res3.get("ok"):
                return res3

    return copy_message(target_chat_id, source_chat_id, msg_id)


# ---------------------------------------------------------------------------
# 7. DATABASE HELPER FUNCTIONS (FIREBASE RTDB REST)
# ---------------------------------------------------------------------------
def db_request(endpoint: str, method: str = "GET", data: any = None) -> any:
    clean_endpoint = endpoint.lstrip("/")
    url = f"{RTDB_URL}/{clean_endpoint}"
    try:
        body = json.dumps(data).encode("utf-8") if data is not None else None
        headers = {"Content-Type": "application/json"} if body else {}
        req = urllib.request.Request(url, data=body, method=method, headers=headers)
        with urllib.request.urlopen(req, timeout=6) as resp:
            content = resp.read().decode("utf-8")
            if content and content != "null":
                return json.loads(content)
            return None
    except Exception as e:
        logger.debug(f"DB request [{method} {endpoint}]: {e}")
        return None


def get_user_from_db(user_id: str) -> dict | None:
    return db_request(f"users/{user_id}.json")


def is_already_referred(referrer_id: str, new_user_id: str) -> bool:
    res = db_request(f"referrals/{referrer_id}/{new_user_id}.json")
    return res is not None


def record_referral(referrer_id: str, new_user_id: str, name: str, username: str, status: str = "pending_first_scratch"):
    payload = {
        "joinerId": str(new_user_id),
        "name": name or f"User #{new_user_id}",
        "username": username or "",
        "status": status,
        "timestamp": int(time.time() * 1000),
    }
    db_request(f"referrals/{referrer_id}/{new_user_id}.json", method="PUT", data=payload)


def record_channel_joined(user_id: str, channel_id: str):
    clean_ch = re.sub(r"[^a-zA-Z0-9_-]", "_", str(channel_id))
    db_request(f"channel_joins/{user_id}/{clean_ch}.json", method="PUT", data=True)


def remove_channel_joined(user_id: str, channel_id: str):
    clean_ch = re.sub(r"[^a-zA-Z0-9_-]", "_", str(channel_id))
    db_request(f"channel_joins/{user_id}/{clean_ch}.json", method="DELETE")


def is_channel_joined_in_db(user_id: str, channel_id: str) -> bool:
    clean_ch = re.sub(r"[^a-zA-Z0-9_-]", "_", str(channel_id))
    res = db_request(f"channel_joins/{user_id}/{clean_ch}.json")
    return res is True


# ---------------------------------------------------------------------------
# 8. YOUTUBE CHANNEL CONFIGURATION
# ---------------------------------------------------------------------------
_YOUTUBE_CACHE = None
_YOUTUBE_CACHE_TIME = 0


def get_youtube_config() -> dict | None:
    global _YOUTUBE_CACHE, _YOUTUBE_CACHE_TIME
    now = time.time()
    if _YOUTUBE_CACHE is not None and (now - _YOUTUBE_CACHE_TIME < 15):
        return _YOUTUBE_CACHE
    try:
        remote = db_request("bot_config/youtube.json")
        if isinstance(remote, dict) and remote.get("url"):
            _YOUTUBE_CACHE = remote
            _YOUTUBE_CACHE_TIME = now
            return _YOUTUBE_CACHE
        _YOUTUBE_CACHE = None
    except Exception:
        _YOUTUBE_CACHE = None
    _YOUTUBE_CACHE_TIME = now
    return _YOUTUBE_CACHE


def set_youtube_config(url: str) -> bool:
    global _YOUTUBE_CACHE, _YOUTUBE_CACHE_TIME
    payload = {"url": url, "updatedAt": int(time.time() * 1000)}
    res = db_request("bot_config/youtube.json", method="PUT", data=payload)
    _YOUTUBE_CACHE = payload
    _YOUTUBE_CACHE_TIME = time.time()
    return res is not None


def remove_youtube_config() -> bool:
    global _YOUTUBE_CACHE, _YOUTUBE_CACHE_TIME
    db_request("bot_config/youtube.json", method="DELETE")
    _YOUTUBE_CACHE = None
    _YOUTUBE_CACHE_TIME = time.time()
    return True


# ---------------------------------------------------------------------------
# 9. CHANNELS, OWNERS & PREMIUM EMOJI ENGINE
# ---------------------------------------------------------------------------
_CHANNELS_CACHE = []
_OWNERS_CACHE = set(o.lower().lstrip("@") for o in DEFAULT_OWNERS)
_LAST_CACHE_TIME = 0


def normalize_url(url: str, default_prefix: str = "https://t.me/") -> str:
    if not url:
        return ""
    url = str(url).strip()
    if url.startswith("http://"):
        return "https://" + url[7:]
    if url.startswith("https://"):
        return url
    if url.startswith("@"):
        return f"https://t.me/{url[1:]}"
    if url.startswith("+"):
        return f"https://t.me/{url}"
    if "t.me/" in url or "telegram.me/" in url or "youtube.com" in url or "youtu.be" in url:
        return f"https://{url.lstrip('/')}"
    return f"{default_prefix}{url.lstrip('/')}"


def pe(char: str) -> str:
    # Use native Telegram Unicode emojis for 100% guaranteed HD rendering on all devices
    return char


def pbtn(text: str, emoji_char: str = None, **kwargs) -> dict:
    btn = {"text": text}
    # Enforce valid HTTPS URLs on normal links to prevent 'Wrong HTTP URL' errors
    if "url" in kwargs and kwargs["url"]:
        btn["url"] = normalize_url(kwargs["url"])
    # Enforce HTTPS on web_app URLs to prevent Telegram 400 Bad Request
    if "web_app" in kwargs and isinstance(kwargs["web_app"], dict):
        wa_url = str(kwargs["web_app"].get("url", "")).strip()
        if wa_url.startswith("http://"):
            kwargs["web_app"]["url"] = "https://" + wa_url[7:]
        elif not wa_url.startswith("https://"):
            kwargs["web_app"]["url"] = "https://" + wa_url
        btn["web_app"] = kwargs["web_app"]
    for k, v in kwargs.items():
        if k not in ["url", "web_app"]:
            btn[k] = v
    return btn


def init_premium_emojis():
    pass


def clean_markup_for_fallback(reply_markup: dict) -> dict:
    if not reply_markup or "inline_keyboard" not in reply_markup:
        return reply_markup
    clean_rows = []
    for row in reply_markup["inline_keyboard"]:
        clean_row = []
        for b in row:
            cb = dict(b)
            cb.pop("icon_custom_emoji_id", None)
            if "url" in cb and cb["url"]:
                cb["url"] = normalize_url(cb["url"])
            clean_row.append(cb)
        clean_rows.append(clean_row)
    return {"inline_keyboard": clean_rows}


def send_message_smart(chat_id, text: str, reply_markup: dict = None, parse_mode: str = "HTML") -> dict:
    res = send_message(chat_id, text, reply_markup=reply_markup, parse_mode=parse_mode)
    if res.get("ok"):
        return res

    logger.warning(f"send_message retry for [{chat_id}]: {res.get('description')}")
    # Fallback 1: Clean and sanitize markup URLs
    fallback_markup = clean_markup_for_fallback(reply_markup)
    res = send_message(chat_id, text, reply_markup=fallback_markup, parse_mode=parse_mode)
    if res.get("ok"):
        return res

    # Fallback 2: Strip HTML tags to avoid parse errors
    plain_text = re.sub(r"<[^>]+>", "", text)
    res = send_message(chat_id, plain_text, reply_markup=fallback_markup, parse_mode=None)
    if res.get("ok"):
        return res

    # Fallback 3: If web_app button failed, convert to normal url
    if fallback_markup and "inline_keyboard" in fallback_markup:
        url_rows = []
        for row in fallback_markup["inline_keyboard"]:
            url_row = []
            for b in row:
                nb = dict(b)
                if "web_app" in nb and isinstance(nb["web_app"], dict):
                    nb["url"] = nb["web_app"].get("url", "")
                    nb.pop("web_app", None)
                url_row.append(nb)
            url_rows.append(url_row)
        res = send_message(chat_id, plain_text, reply_markup={"inline_keyboard": url_rows}, parse_mode=None)
        if res.get("ok"):
            return res

    # Fallback 4: Message without markup
    res = send_message(chat_id, plain_text, reply_markup=None, parse_mode=None)
    if res.get("ok"):
        return res

    logger.error(f"❌ Telegram sendMessage permanent error [{chat_id}]: {res.get('description')}")
    return res


def edit_message_text_smart(chat_id, message_id: int, text: str, reply_markup: dict = None, parse_mode: str = "HTML") -> dict:
    res = edit_message_text(chat_id, message_id, text, reply_markup=reply_markup, parse_mode=parse_mode)
    if res.get("ok"):
        return res

    logger.warning(f"edit_message retry for [{chat_id}]: {res.get('description')}")
    fallback_markup = clean_markup_for_fallback(reply_markup)
    res = edit_message_text(chat_id, message_id, text, reply_markup=fallback_markup, parse_mode=parse_mode)
    if res.get("ok"):
        return res

    plain_text = re.sub(r"<[^>]+>", "", text)
    res = edit_message_text(chat_id, message_id, plain_text, reply_markup=fallback_markup, parse_mode=None)
    if res.get("ok"):
        return res

    if fallback_markup and "inline_keyboard" in fallback_markup:
        url_rows = []
        for row in fallback_markup["inline_keyboard"]:
            url_row = []
            for b in row:
                nb = dict(b)
                if "web_app" in nb and isinstance(nb["web_app"], dict):
                    nb["url"] = nb["web_app"].get("url", "")
                    nb.pop("web_app", None)
                url_row.append(nb)
            url_rows.append(url_row)
        res = edit_message_text(chat_id, message_id, plain_text, reply_markup={"inline_keyboard": url_rows}, parse_mode=None)
        if res.get("ok"):
            return res

    logger.error(f"❌ Telegram editMessageText permanent error [{chat_id}]: {res.get('description')}")
    return res


def load_channels() -> list[dict]:
    global _CHANNELS_CACHE, _LAST_CACHE_TIME
    now = time.time()
    if _CHANNELS_CACHE and (now - _LAST_CACHE_TIME < 10):
        return _CHANNELS_CACHE

    combined = [dict(p) for p in PERMANENT_CHANNELS]
    try:
        remote = db_request("bot_config/channels.json")
        if remote:
            items = list(remote.values()) if isinstance(remote, dict) else remote
            for item in items:
                if isinstance(item, dict) and item.get("id"):
                    item_copy = dict(item)
                    item_copy["url"] = normalize_url(item_copy.get("url", ""))
                    if not any(str(c.get("id")) == str(item_copy["id"]) for c in combined):
                        combined.append(item_copy)
    except Exception as e:
        logger.warning(f"Error loading channels: {e}")

    combined.sort(key=lambda c: c.get("createdAt", 0) or 0)
    _CHANNELS_CACHE = combined
    _LAST_CACHE_TIME = now
    return _CHANNELS_CACHE


def is_owner(user: dict) -> bool:
    if not user:
        return False
    uid = str(user.get("id", "")).lower()
    uname = str(user.get("username", "")).lower().lstrip("@")
    return uid in _OWNERS_CACHE or uname in _OWNERS_CACHE


def build_channels_keyboard(channels: list[dict], ref_param: str = None) -> dict:
    buttons = []
    for i in range(0, len(channels), 2):
        row = [pbtn("🔗 JOIN NOW", url=channels[i]["url"])]
        if i + 1 < len(channels):
            row.append(pbtn("🔗 JOIN NOW", url=channels[i + 1]["url"]))
        buttons.append(row)

    yt = get_youtube_config()
    if yt and yt.get("url"):
        buttons.append([pbtn("📢 SUBSCRIBE OUR CHANNEL", url=yt["url"])])

    claim_callback = f"claim_{ref_param or 'none'}"
    buttons.append([pbtn("💰 CLAIM NOW", callback_data=claim_callback)])
    return {"inline_keyboard": buttons}


# ---------------------------------------------------------------------------
# 10. BOT ADMIN CHECK & USER VERIFICATION (FAST - NON-BLOCKING)
# ---------------------------------------------------------------------------
def check_bot_channel_admin(ch_id: str) -> tuple[bool, str]:
    bot_info = get_bot_info()
    bot_id = bot_info.get("id")
    if not bot_id:
        return (False, "Bot ID unavailable")

    clean_id = str(ch_id).strip()
    target = int(clean_id) if clean_id.lstrip("-").isdigit() else clean_id
    res = tg_api("getChatMember", {"chat_id": target, "user_id": bot_id}, timeout=4)
    if res.get("ok") and res.get("result"):
        status = res["result"].get("status", "")
        if status in ["administrator", "creator"]:
            return (True, f"✅ ADMIN ACTIVE ({status})")
        return (False, f"❌ NOT ADMIN (Status: {status})")

    desc = str(res.get("description", "Error querying chat"))
    return (False, f"❌ NOT ADMIN: {desc}")


def check_user_channels(user_id: int) -> tuple[bool, list[dict]]:
    channels = load_channels()
    if not channels:
        return (True, [])

    unjoined = []
    for ch in channels:
        ch_id = str(ch.get("id", "")).strip()
        target = int(ch_id) if ch_id.lstrip("-").isdigit() else ch_id

        if is_channel_joined_in_db(str(user_id), ch_id):
            continue

        res = tg_api("getChatMember", {"chat_id": target, "user_id": user_id}, timeout=3)
        if res.get("ok") and res.get("result"):
            status = res["result"].get("status", "")
            if status in ["member", "administrator", "creator", "restricted"]:
                record_channel_joined(str(user_id), ch_id)
                continue
            elif status in ["left", "kicked"]:
                unjoined.append(ch)
                continue
        else:
            desc = str(res.get("description", "")).lower()
            if "chat_admin_required" in desc or "bot is not a member" in desc or "chat not found" in desc or "rights" in desc or "forbidden" in desc:
                continue
            unjoined.append(ch)

    return (len(unjoined) == 0, unjoined)


# ---------------------------------------------------------------------------
# 11. COMMAND & CALLBACK HANDLERS
# ---------------------------------------------------------------------------
def handle_start(chat_id, user: dict, args: list[str]):
    user_id = str(user.get("id"))
    name = user.get("first_name") or user.get("username") or "Friend"
    username = user.get("username") or ""

    ref_param = args[0] if len(args) > 0 else None
    referrer_id = None

    if ref_param:
        clean_ref = ref_param.replace("ref_", "").strip()
        if clean_ref.isdigit():
            referrer_id = clean_ref

    logger.info(f"📩 [{user_id}] Received /start from {name} (@{username})")

    existing = get_user_from_db(user_id)
    blocked_record = db_request(f"blocked_accounts/{user_id}.json")
    is_blocked = bool(
        (existing and existing.get("deviceBlocked") is True)
        or (blocked_record is True or (isinstance(blocked_record, dict) and blocked_record.get("blocked") is True))
    )

    if referrer_id:
        if referrer_id == user_id or is_blocked:
            referrer_id = None
        elif existing and (
            existing.get("referredBy")
            or existing.get("referralRewardGiven")
            or existing.get("hasScratchedFirstCard")
            or (existing.get("balance") or 0) > 0
            or (existing.get("friendsJoined") or 0) > 0
        ):
            referrer_id = existing.get("referredBy")
        elif is_already_referred(referrer_id, user_id):
            pass
        else:
            record_referral(referrer_id, user_id, name, username, status="pending_first_scratch")

    if not existing:
        welcome_user = {
            "id": user_id,
            "telegramId": user_id,
            "name": name,
            "username": username,
            "balance": 0,
            "spins": 1,
            "friendsJoined": 0,
            "spinsEarned": 1,
            "claimedWelcomeSpin": True,
            "createdAt": int(time.time() * 1000),
            "isVerified": False,
            "deviceVerified": True,
            "deviceBlocked": is_blocked,
            "referredBy": referrer_id if (referrer_id and referrer_id != user_id) else None,
            "referralRewardGiven": False,
        }
        db_request(f"users/{user_id}.json", method="PUT", data=welcome_user)
        existing = welcome_user
    else:
        patch_data = {}
        if is_blocked:
            patch_data["deviceBlocked"] = True
            existing["deviceBlocked"] = True

        if patch_data:
            db_request(f"users/{user_id}.json", method="PATCH", data=patch_data)

    if is_blocked:
        send_message_smart(
            chat_id,
            f"{pe('🚫')} <b>Account Blocked!</b>\n\n"
            f"Ek phone me sirf 1 account allow hai. Ye account block hai.",
        )
        return

    # Check current channel membership status
    all_joined, unjoined = check_user_channels(int(user_id))

    # User already verified AND currently joined all channels -> Send verified message with OPEN GIVEAWAY
    if all_joined and existing.get("isVerified") and not existing.get("deviceBlocked"):
        app_url = f"{WEB_URL}/?uid={user_id}&start=ref_{referrer_id}" if referrer_id else f"{WEB_URL}/?uid={user_id}"
        verified_markup = {
            "inline_keyboard": [
                [pbtn("💰 OPEN GIVEAWAY", web_app={"url": app_url})],
                [pbtn("👥 Refer And Earn", callback_data="my_invite")],
            ]
        }
        verified_text = (
            "🎁 <b>SUCCESSFULLY JOINED?</b>\n\n"
            "💰 <b>CLAIM YOUR DIWALI GIVEAWAY NOW!</b>\n\n"
            "❤️ <b>THANK YOU FOR JOINING</b> ❤️"
        )
        send_message_smart(chat_id, verified_text, reply_markup=verified_markup)
        logger.info(f"🚀 [{user_id}] Delivered Verified Post-Join markup")
        return

    # Unverified user or channels not yet joined -> show pre-join message with channels and CLAIM NOW button
    channels = load_channels()
    welcome_text = (
        "🎉 <b>WELCOME TO THE GIVEAWAY</b>\n"
        "🪔 <b>DIWALI SPECIAL GIVEAWAY</b> 🪔\n\n"
        "        ✅ <b>MUST JOIN CHANNEL</b>\n\n"
        "━━━━━━━━━━━━━━"
    )
    markup = build_channels_keyboard(channels, ref_param)
    send_message_smart(chat_id, welcome_text, reply_markup=markup)
    logger.info(f"🚀 [{user_id}] Delivered Pre-Join Channels markup")


def handle_claim_callback(query: dict):
    query_id = query.get("id")
    user = query.get("from") or {}
    msg = query.get("message") or {}
    chat_id = msg.get("chat", {}).get("id")
    message_id = msg.get("message_id")
    data = query.get("data") or ""

    user_id = str(user.get("id"))
    ref_param = None
    if data.startswith("claim_"):
        raw = data.replace("claim_", "")
        if raw != "none":
            ref_param = raw

    logger.info(f"🔔 [{user_id}] Clicked Claim button")

    all_joined, unjoined = check_user_channels(int(user_id))
    if not all_joined:
        answer_callback_query(query_id, "❌ Please join all channels before claiming!", show_alert=True)
        channels = load_channels()
        welcome_text = (
            "🎉 <b>WELCOME TO THE GIVEAWAY</b>\n"
            "🪔 <b>DIWALI SPECIAL GIVEAWAY</b> 🪔\n\n"
            "        ✅ <b>MUST JOIN CHANNEL</b>\n\n"
            "━━━━━━━━━━━━━━\n\n"
            "⚠️ <b>Please join all channels before claiming!</b>"
        )
        markup = build_channels_keyboard(channels, ref_param)
        edit_message_text_smart(chat_id, message_id, welcome_text, reply_markup=markup)
        return

    # User verified! Mark verified in DB
    db_request(f"users/{user_id}.json", method="PATCH", data={"isVerified": True, "deviceVerified": True})
    answer_callback_query(query_id, "🎉 Verified Successfully! Opening Giveaway...", show_alert=False)

    app_url = f"{WEB_URL}/?uid={user_id}&start={ref_param}" if ref_param else f"{WEB_URL}/?uid={user_id}"
    verified_markup = {
        "inline_keyboard": [
            [pbtn("💰 OPEN GIVEAWAY", web_app={"url": app_url})],
            [pbtn("👥 Refer And Earn", callback_data="my_invite")],
        ]
    }
    verified_text = (
        "🎁 <b>SUCCESSFULLY JOINED?</b>\n\n"
        "💰 <b>CLAIM YOUR DIWALI GIVEAWAY NOW!</b>\n\n"
        "❤️ <b>THANK YOU FOR JOINING</b> ❤️"
    )
    edit_message_text_smart(chat_id, message_id, verified_text, reply_markup=verified_markup)
    logger.info(f"🎉 [{user_id}] Verified & Unlocked Giveaway directly!")


def handle_invite(chat_id, user: dict):
    user_id = str(user.get("id"))
    bot_info = get_bot_info()
    bot_user = bot_info.get("username", BOT_USERNAME)
    ref_link = f"https://t.me/{bot_user}?start=ref_{user_id}"

    text = (
        f"🎁 <b>Refer And Earn!</b>\n\n"
        f"Apne doston ko invite karein aur free giveaway paayein:\n\n"
        f"🔗 <b>Aapka Referral Link:</b>\n"
        f"<code>{ref_link}</code>"
    )
    markup = {
        "inline_keyboard": [
            [
                pbtn(
                    "Share Referral Link 🚀",
                    emoji_char="🚀",
                    url=f"https://t.me/share/url?url={urllib.parse.quote(ref_link)}&text={urllib.parse.quote('Diwali Free Giveaway Loot!')}",
                )
            ]
        ]
    }
    send_message_smart(chat_id, text, reply_markup=markup)


def handle_ownerhelp(chat_id, user: dict):
    if not is_owner(user):
        send_message(chat_id, "❌ You are not authorized to use Owner commands.")
        return

    text = (
        f"{pe('👑')} <b>DIWALI BOT OWNER PANEL COMMANDS:</b>\n\n"
        f"<b>1. Channels Management:</b>\n"
        f"• <code>/channels</code> - Sabhi channels aur admin status dekhein\n"
        f"• <code>/checkadmin</code> - Channel admin status live verify karein\n"
        f"• <code>/addchannel -100XXXXX ChannelName https://t.me/...</code>\n"
        f"• <code>/removechannel -100XXXXX</code>\n\n"
        f"<b>2. YouTube Channel Feature:</b>\n"
        f"• <code>/setyoutube https://youtube.com/@channel</code> - YouTube button add karein\n"
        f"• <code>/removeyoutube</code> - YouTube button remove karein\n\n"
        f"<b>3. Broadcast & Stats:</b>\n"
        f"• <code>/broadcast Your message</code> (or reply with photo/video/stickers)\n"
        f"• <code>/stats</code> - Total users & database stats\n"
        f"• <code>/resetme</code> - Apna account reset karke fresh test karein\n"
    )
    send_message_smart(chat_id, text)


def handle_setyoutube(chat_id, user: dict, args: list[str]):
    if not is_owner(user):
        send_message(chat_id, "❌ You are not authorized.")
        return
    if not args:
        send_message(chat_id, "❌ Usage: <code>/setyoutube https://youtube.com/@yourchannel</code>")
        return
    url = normalize_url(args[0].strip(), default_prefix="https://youtube.com/")
    set_youtube_config(url)
    send_message_smart(chat_id, f"{pe('✅')} <b>YouTube Channel Added!</b>\n\nURL: {url}\nAb sabhi users ko YouTube Subscribe button dikhega.")


def handle_removeyoutube(chat_id, user: dict):
    if not is_owner(user):
        send_message(chat_id, "❌ You are not authorized.")
        return
    remove_youtube_config()
    send_message_smart(chat_id, f"{pe('✅')} <b>YouTube Channel Removed!</b>\nAb bot me YouTube button nahi aayega.")


def handle_channels(chat_id, user: dict):
    if not is_owner(user):
        send_message(chat_id, "❌ You are not authorized.")
        return

    channels = load_channels()
    yt = get_youtube_config()
    text = f"{pe('📢')} <b>Active Channels List ({len(channels)} total):</b>\n\n"

    for idx, ch in enumerate(channels, 1):
        cid = str(ch.get("id"))
        name = ch.get("name", "Channel")
        url = ch.get("url", "")
        is_adm, adm_text = check_bot_channel_admin(cid)
        text += f"<b>{idx}. {name}</b>\n• ID: <code>{cid}</code>\n• URL: {url}\n• Status: {adm_text}\n\n"

    if yt and yt.get("url"):
        text += f"<b>▶️ YouTube Channel:</b>\n• URL: {yt['url']}\n\n"
    else:
        text += "<b>▶️ YouTube Channel:</b> Not Set (Use <code>/setyoutube &lt;url&gt;</code>)\n\n"

    send_message_smart(chat_id, text)


def handle_addchannel(chat_id, user: dict, args: list[str]):
    if not is_owner(user):
        send_message(chat_id, "❌ You are not authorized.")
        return
    if len(args) < 3:
        send_message(chat_id, "❌ Usage: <code>/addchannel &lt;chat_id&gt; &lt;name&gt; &lt;invite_url&gt;</code>")
        return

    cid = args[0].strip()
    cname = args[1].strip()
    curl = normalize_url(" ".join(args[2:]).strip())

    is_adm, adm_msg = check_bot_channel_admin(cid)
    clean_id = re.sub(r"[^a-zA-Z0-9_-]", "_", cid)
    data = {
        "id": cid,
        "name": cname,
        "url": curl,
        "is_private": "joinchat" in curl or "+" in curl,
        "createdAt": int(time.time() * 1000),
    }
    db_request(f"bot_config/channels/{clean_id}.json", method="PUT", data=data)
    load_channels()

    msg = (
        f"{pe('✅')} <b>Channel Added Successfully!</b>\n\n"
        f"• Name: {cname}\n"
        f"• ID: <code>{cid}</code>\n"
        f"• URL: {curl}\n"
        f"• Status: {adm_msg}"
    )
    send_message_smart(chat_id, msg)


def handle_removechannel(chat_id, user: dict, args: list[str]):
    if not is_owner(user):
        send_message(chat_id, "❌ You are not authorized.")
        return
    if not args:
        send_message(chat_id, "❌ Usage: <code>/removechannel &lt;chat_id&gt;</code>")
        return

    cid = args[0].strip()
    clean_id = re.sub(r"[^a-zA-Z0-9_-]", "_", cid)
    db_request(f"bot_config/channels/{clean_id}.json", method="DELETE")
    load_channels()
    send_message_smart(chat_id, f"{pe('✅')} Channel <code>{cid}</code> removed from database.")


def handle_broadcast(chat_id, user: dict, msg: dict):
    if not is_owner(user):
        send_message(chat_id, "❌ You are not authorized.")
        return

    reply = msg.get("reply_to_message")
    text_content = msg.get("text", "")
    parts = text_content.split(maxsplit=1)
    broadcast_text = parts[1] if len(parts) > 1 else None

    if not reply and not broadcast_text:
        send_message(chat_id, "❌ Usage: <code>/broadcast Your message</code> or reply to a message with <code>/broadcast</code>")
        return

    users_data = db_request("users.json")
    if not users_data:
        send_message(chat_id, "❌ No users found in database.")
        return

    target_ids = list(users_data.keys())
    send_message_smart(chat_id, f"{pe('🚀')} <b>Starting Broadcast to {len(target_ids)} users...</b>")

    def run_broadcast():
        success, failed = 0, 0
        for uid in target_ids:
            try:
                if reply:
                    deliver_premium_message(uid, chat_id, reply)
                else:
                    send_message_smart(uid, broadcast_text)
                success += 1
            except Exception:
                failed += 1
            time.sleep(0.04)

        report = f"{pe('✅')} <b>Broadcast Finished!</b>\n\n• Delivered: {success}\n• Failed: {failed}"
        send_message_smart(chat_id, report)

    threading.Thread(target=run_broadcast, daemon=True).start()


def handle_stats(chat_id, user: dict):
    if not is_owner(user):
        send_message(chat_id, "❌ You are not authorized.")
        return

    users_data = db_request("users.json") or {}
    total_users = len(users_data)
    verified_users = sum(1 for u in users_data.values() if isinstance(u, dict) and u.get("isVerified"))
    blocked_users = sum(1 for u in users_data.values() if isinstance(u, dict) and u.get("deviceBlocked"))

    text = (
        f"{pe('📊')} <b>DIWALI BOT LIVE STATISTICS:</b>\n\n"
        f"• Total Users: <b>{total_users}</b>\n"
        f"• Verified Users: <b>{verified_users}</b>\n"
        f"• Blocked Devices: <b>{blocked_users}</b>\n"
        f"• Database: <b>Firebase RTDB Connected</b>\n"
        f"• Mini App URL: <b>{WEB_URL}</b>"
    )
    send_message_smart(chat_id, text)


# ---------------------------------------------------------------------------
# 12. UPDATE DISPATCHER (CONCURRENT WORKER)
# ---------------------------------------------------------------------------
def process_update(upd: dict):
    try:
        if "chat_join_request" in upd:
            req = upd["chat_join_request"]
            user_id = str(req.get("from", {}).get("id", ""))
            chat_id = str(req.get("chat", {}).get("id", ""))
            if user_id and chat_id:
                record_channel_joined(user_id, chat_id)
            return

        if "chat_member" in upd:
            cm = upd["chat_member"]
            chat_id = str(cm.get("chat", {}).get("id", ""))
            new_m = cm.get("new_chat_member") or {}
            user_id = str((new_m.get("user") or {}).get("id", ""))
            status = new_m.get("status", "")
            if user_id and chat_id:
                if status in ["left", "kicked"]:
                    remove_channel_joined(user_id, chat_id)
                elif status in ["member", "administrator", "creator", "restricted"]:
                    record_channel_joined(user_id, chat_id)
            return

        if "callback_query" in upd:
            query = upd["callback_query"]
            data = query.get("data") or ""
            if data.startswith("claim_"):
                handle_claim_callback(query)
            elif data == "my_invite":
                answer_callback_query(query.get("id"))
                chat_id = query.get("message", {}).get("chat", {}).get("id")
                handle_invite(chat_id, query.get("from") or {})
            return

        msg = upd.get("message")
        if not msg:
            return

        chat_id = msg.get("chat", {}).get("id")
        user = msg.get("from") or {}
        text = (msg.get("text") or msg.get("caption") or "").strip()
        if not text:
            return

        if not text.startswith("/"):
            if text.lower() in ["start", "claim", "giveaway", "hi", "hello"]:
                cmd = "/start"
                args = []
            else:
                return
        else:
            parts = text.split()
            cmd = parts[0].split("@")[0].lower()
            args = parts[1:]

        user_id = str(user.get("id", ""))

        if cmd == "/start":
            handle_start(chat_id, user, args)
        elif cmd in ["/invite", "/refer"]:
            handle_invite(chat_id, user)
        elif cmd == "/resetme":
            # For testing: reset user's verification state
            db_request(f"users/{user_id}.json", method="PATCH", data={"isVerified": False})
            db_request(f"channel_joins/{user_id}.json", method="DELETE")
            send_message_smart(chat_id, "🔄 <b>Account Reset Successful!</b>\nAb aap bilkul naye user ki tarah channel join & claim test kar sakte hain.")
            handle_start(chat_id, user, [])
        elif cmd == "/ownerhelp":
            handle_ownerhelp(chat_id, user)
        elif cmd == "/setyoutube":
            handle_setyoutube(chat_id, user, args)
        elif cmd == "/removeyoutube":
            handle_removeyoutube(chat_id, user)
        elif cmd in ["/channels", "/checkadmin"]:
            handle_channels(chat_id, user)
        elif cmd == "/addchannel":
            handle_addchannel(chat_id, user, args)
        elif cmd == "/removechannel":
            handle_removechannel(chat_id, user, args)
        elif cmd == "/broadcast":
            handle_broadcast(chat_id, user, msg)
        elif cmd == "/stats":
            handle_stats(chat_id, user)
    except Exception as e:
        logger.error(f"Error processing update: {e}")


# ---------------------------------------------------------------------------
# 13. MAIN ENGINE WITH CONCURRENT POLLING
# ---------------------------------------------------------------------------
def main():
    logger.info("====================================================")
    logger.info("🚀 Starting Diwali Giveaway Telegram Bot Engine")
    logger.info(f"🌐 Mini App URL: {WEB_URL}")
    logger.info("====================================================")

    # Start 24/7 HTTP Health Check Server
    t = threading.Thread(target=start_health_server, daemon=True)
    t.start()

    init_premium_emojis()

    # Clear old webhooks safely (keep pending updates)
    tg_api("deleteWebhook", {"drop_pending_updates": False})
    bot_me = get_bot_info()
    logger.info(f"✅ Bot Connected: @{bot_me.get('username', BOT_USERNAME)} (ID: {bot_me.get('id')})")

    # Reset chat menu button to default
    try:
        tg_api("setChatMenuButton", {"menu_button": {"type": "default"}})
    except Exception as e:
        logger.debug(f"Menu button note: {e}")

    logger.info("📡 Live Polling Active... Waiting for Telegram users!")

    offset = 0
    while True:
        try:
            res = tg_api(
                "getUpdates",
                {
                    "offset": offset,
                    "timeout": 5,
                    "allowed_updates": ["message", "callback_query", "chat_join_request", "chat_member"],
                },
                timeout=12,
            )
            if res.get("ok") and isinstance(res.get("result"), list):
                for upd in res["result"]:
                    offset = upd["update_id"] + 1
                    threading.Thread(target=process_update, args=(upd,), daemon=True).start()
            else:
                desc = res.get("description", "")
                if "conflict" in str(desc).lower():
                    logger.warning("⚠️ Another bot instance is polling. Retrying in 5s...")
                    time.sleep(5)
                else:
                    time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Bot stopped by user.")
            break
        except Exception as e:
            logger.warning(f"Polling loop notice: {e}. Retrying in 2s...")
            time.sleep(2)


if __name__ == "__main__":
    main()
