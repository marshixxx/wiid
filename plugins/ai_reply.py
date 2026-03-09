from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cardinal import Cardinal

from FunPayAPI.updater.events import NewMessageEvent, LastChatMessageChangedEvent
from FunPayAPI.types import MessageTypes
from threading import Thread
from os.path import exists
from datetime import datetime
from tg_bot import CBT
import tg_bot.static_keyboards
from telebot.types import InlineKeyboardMarkup as K, InlineKeyboardButton as B
import telebot
import requests
import base64
import logging
import json
import time
import os

NAME = "AI Reply"
VERSION = "3.1.0"
DESCRIPTION = (
    "Автоответы через Google Gemini. "
    "Полная настройка прямо в Telegram — API ключ, статус, режим тишины, антиспам."
)
CREDITS = "@your_name"
UUID = "a1b2c3d4-e5f6-4789-abcd-ef1234567890"
SETTINGS_PAGE = True
BIND_TO_DELETE = None

DATA_PATH = "storage/plugins/ai_reply.json"
MAX_HISTORY = 6

DEFAULT_DATA = {
    "api_key": "",
    "model": "gemini-1.5-flash",
    "enabled": True,
    "max_tokens": 400,
    "timeout": 20,
    "antispam_cooldown": 15,
    "antispam_max": 5,
    "antispam_window": 60,
    "silent_enabled": False,
    "silent_start": 0,
    "silent_end": 9,
    "silent_message": "Здравствуйте! Сейчас нерабочее время. Продавец ответит утром.",
    "status": "Продавец работает в штатном режиме. Заказы принимаются.",
}

SYSTEM_PROMPT = """Ты — вежливый и профессиональный помощник продавца игровых услуг на площадке FunPay.
Твоя задача — отвечать от имени продавца. Тон: официальный, но дружелюбный. Обращайся на "вы".
Пиши кратко и по делу. Максимум 1-2 эмодзи на сообщение.

=== ЯЗЫК ОТВЕТА ===
Определи язык последнего сообщения покупателя и отвечай СТРОГО на том же языке.

=== ПОЛНЫЙ ПРАЙС-ЛИСТ ===

--- GENSHIN IMPACT ---

[Боссы и подземелья]
- Мрачный натиск — все сложности, прохождение 100% → 300 руб.
- Театр Воображариум — прохождение 100% → 250 руб.
- Витая бездна 9-12 этаж — прохождение 100% → 220 руб.

[Исследование локаций]
- Нод-Край 6.0-6.3 — исследование 100% → 1700 руб.
- Нод-Край 6.3 — исследование 100% → 800 руб.
- Нод-Край 6.0 — исследование 100% → 900 руб.
- Натлан 5.0-5.8 — исследование 100% → 4000 руб.
- Натлан 5.8 — исследование 100% → 800 руб.
- Натлан 5.5 — исследование 100% → 800 руб.
- Натлан 5.2 — исследование 100% → 800 руб.
- Натлан 5.0 — исследование 100% → 800 руб.
- Фонтейн 4.0-4.6 — исследование 100% → 2900 руб.
- Фонтейн 4.6 — исследование 100% → 700 руб.
- Долина Чэньюой 4.4 — исследование 100% → 750 руб.
- Фонтейн 4.2 — исследование 100% → 750 руб.
- Фонтейн 4.1 — исследование 100% → 750 руб.
- Фонтейн 4.0 — исследование 100% → 750 руб.
- Тропики + Пустыня Сумеру 3.0-3.6 — исследование 100% → 4000 руб.
- Пустыня Сумеру 3.1-3.6 — исследование 100% → 2700 руб.
- Пустыня Сумеру 3.6 — исследование 100% → 900 руб.
- Пустыня Сумеру 3.4 — исследование 100% → 900 руб.
- Пустыня Сумеру 3.1 — исследование 100% → 900 руб.
- Тропики Сумеру 3.0 — исследование 100% → 1300 руб.
- Разлом верх + низ 2.6 — исследование 100% → 600 руб.
- Энканомия 2.4 — исследование 100% → 550 руб.
- Инадзума 2.0-2.2 — исследование 100% → 1900 руб.
- Инадзума 2.2 — исследование 100% → 650 руб.
- Инадзума 2.1 — исследование 100% → 650 руб.
- Инадзума 2.0 — исследование 100% → 650 руб.
- Драконий хребет 1.2 — исследование 100% → 550 руб.
- Ли Юэ 1.0 — исследование 100% → 800 руб.
- Мондштадт 1.0 — исследование 100% → 500 руб.

[Квесты]
- Нод-Край — сюжетная линия 6.3 → 400 руб.
- Нод-Край — сюжетная линия 6.0-6.3 → 1600 руб.
- Натлан — сюжетная линия → 1050 руб.
- Сюжет Мондштадт-Инадзума → 800 руб.
- Фонтейн — сюжетная линия → 900 руб.
- Сумеру — сюжетная линия → 900 руб.
- Инадзума — сюжетная линия → 600 руб.
- Ли Юэ — сюжетная линия → 350 руб.
- Мондштадт — сюжетная линия → 150 руб.
- Панихида Билцис — прохождение → 230 руб.
- Золотая страна грёз — прохождение → 230 руб.
- Хварна добра и зла — прохождение → 230 руб.
- Аранья + все аранары → 570 руб.

[Прокачка]
- Возвышение Круга Тони — за 1 уровень → 45 руб.
- Возвышение Древа снов — за 1 уровень → 45 руб.
- Возвышение Священной сакуры — за 1 уровень → 45 руб.
- Возвышение Фонтана Люсин — за 1 уровень → 45 руб.
- Прокачка AR 35-45 → 900 руб.
- Прокачка AR 25-35 → 700 руб.
- Прокачка AR 15-25 → 500 руб.
- Прокачка AR 1-10 → 280 руб.
- Уход за аккаунтом — 1 месяц → 2200 руб.
- Уход за аккаунтом — 14 дней → 1300 руб.
- Уход за аккаунтом — 7 дней → 700 руб.
- Уход за аккаунтом — 1 день → 320 руб.
- Фарм круток — за 10 круток → 300 руб.

--- HONKAI: STAR RAIL ---

- Все планеты на 100% → 4000 руб.
- Доп. глава — за одну главу → 200 руб.
- Сюжет Амфореус → 1500 руб.
- Сюжет Пенакония → 1000 руб.
- Сюжет Лофу Сяньчжоу → 500 руб.
- Сюжет Ярило-VI → 250 руб.
- Сюжет Космическая станция Герта → 150 руб.
- Амфореус на 100% → 2000 руб.
- Пенакония на 100% → 1200 руб.
- Лофу Сяньчжоу на 100% → 800 руб.
- Ярило-VI на 100% → 350 руб.
- Космическая станция Герта на 100% → 300 руб.
- Уход за аккаунтом — 1 месяц → 1400 руб.
- Уход за аккаунтом — 14 дней → 950 руб.
- Уход за аккаунтом — 7 дней → 500 руб.
- Уход за аккаунтом — 1 день → 95 руб.
- Фарм круток — за 10 круток → 320 руб.

--- OVERWATCH 2 ---

- Прохождение любого ивента → 448 руб.
- Прокачка боевого пропуска 1-80 уровень → 4481 руб.
- Прокачка боевого пропуска — за 1 уровень → 56 руб.

=== СКИДКИ ПО ПРОГРЕССУ ===
50% пройдено = скидка 10%, 60% = скидка 20%, 70% = скидка 30%, 80% = скидка 40%, 90% = скидка 60%.
Если покупатель прислал скриншот — определи процент и рассчитай итоговую цену.
Пример ответа: "Натлан 5.0 стоит 800 руб. У вас ~70% — скидка 30%, итого 560 руб."

=== ПЕРЕДАЧА ПРОДАВЦУ ===
Если покупатель хочет живого человека, или вопрос выходит за рамки прайса — добавь в конец ответа: [ПЕРЕДАТЬ_ПРОДАВЦУ]

=== ПРАВИЛА ===
- Цены называй из прайса. Нет в прайсе — передай продавцу.
- Сроки уточняются после оформления заказа.
- Работа вручную, без читов. Рекомендуй сменить пароль на время выполнения.
- Скидки только по прогрессу. На другой торг — вежливый отказ.
- Не говори что ты бот или ИИ.

=== ТЕКУЩИЙ СТАТУС ПРОДАВЦА ===
{status}
"""

# Callback-теги для кнопок
CBT_MAIN       = "AIReply_main"
CBT_SET_KEY    = "AIReply_set_key"
CBT_KEY_DONE   = "AIReply_key_done"
CBT_SET_STATUS = "AIReply_set_status"
CBT_STS_DONE   = "AIReply_sts_done"
CBT_TOGGLE     = "AIReply_toggle"
CBT_TOG_SIL    = "AIReply_tog_sil"
CBT_SIL_HOURS  = "AIReply_sil_hours"
CBT_SIL_H_DONE = "AIReply_sil_h_done"
CBT_SIL_MSG    = "AIReply_sil_msg"
CBT_SIL_M_DONE = "AIReply_sil_m_done"
CBT_TOG_MODEL  = "AIReply_tog_model"
CBT_HANDOFF    = "AIReply_handoff"
CBT_RESUME     = "AIReply_resume"

logger = logging.getLogger("FPC.ai_reply")

conversation_history: dict[int, list] = {}
handoff_chats: dict[int, float] = {}
last_reply_time: dict[int, float] = {}
msg_timestamps: dict[int, list] = {}


# ───────── Данные ─────────

def load_data() -> dict:
    os.makedirs("storage/plugins", exist_ok=True)
    if not exists(DATA_PATH):
        save_data(DEFAULT_DATA.copy())
        return DEFAULT_DATA.copy()
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k, v in DEFAULT_DATA.items():
            if k not in data:
                data[k] = v
        return data
    except Exception:
        return DEFAULT_DATA.copy()


def save_data(data: dict):
    os.makedirs("storage/plugins", exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get(key: str):
    return load_data().get(key, DEFAULT_DATA.get(key))


def set_val(key: str, value):
    data = load_data()
    data[key] = value
    save_data(data)


# ───────── Вспомогательные ─────────

def build_prompt() -> str:
    return SYSTEM_PROMPT.format(status=get("status"))


def is_silent() -> bool:
    if not get("silent_enabled"):
        return False
    h = datetime.now().hour
    s, e = int(get("silent_start")), int(get("silent_end"))
    return (h >= s or h < e) if s > e else (s <= h < e)


def antispam_ok(chat_id: int) -> bool:
    now = time.time()
    if now - last_reply_time.get(chat_id, 0) < float(get("antispam_cooldown") or 15):
        return False
    window = float(get("antispam_window") or 60)
    ts = [t for t in msg_timestamps.get(chat_id, []) if now - t < window]
    ts.append(now)
    msg_timestamps[chat_id] = ts
    return len(ts) <= int(get("antispam_max") or 5)


def mark_replied(chat_id: int):
    last_reply_time[chat_id] = time.time()


def add_history(chat_id: int, role: str, text: str):
    if chat_id not in conversation_history:
        conversation_history[chat_id] = []
    conversation_history[chat_id].append({"role": role, "parts": [{"text": text}]})
    cap = MAX_HISTORY * 2
    if len(conversation_history[chat_id]) > cap:
        conversation_history[chat_id] = conversation_history[chat_id][-cap:]


def dl_image(url: str, timeout: int):
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        ct = r.headers.get("Content-Type", "image/jpeg").split(";")[0].strip()
        if ct not in ("image/jpeg", "image/png", "image/webp", "image/gif"):
            ct = "image/jpeg"
        return base64.b64encode(r.content).decode(), ct
    except Exception:
        return None


def notify(cardinal: Cardinal, text: str):
    try:
        if cardinal.telegram:
            cardinal.telegram.send_notification(text)
    except Exception:
        pass


# ───────── Gemini ─────────

def ask_gemini(chat_id: int, text: str, image_url) -> str | None:
    api_key = str(get("api_key")).strip()
    model   = str(get("model")).strip()
    maxt    = int(get("max_tokens") or 400)
    tout    = int(get("timeout") or 20)

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        + model + ":generateContent?key=" + api_key
    )

    parts = []
    if image_url:
        img = dl_image(image_url, tout)
        if img:
            parts.append({"inline_data": {"mime_type": img[1], "data": img[0]}})
    if text and text.strip():
        parts.append({"text": text})
    elif image_url:
        parts.append({"text": "Покупатель прислал скриншот. Проанализируй и ответь."})
    if not parts:
        return None

    contents = conversation_history.get(chat_id, []) + [{"role": "user", "parts": parts}]
    payload  = {
        "system_instruction": {"parts": [{"text": build_prompt()}]},
        "contents": contents,
        "generationConfig": {"maxOutputTokens": maxt, "temperature": 0.7}
    }
    try:
        r = requests.post(url, headers={"Content-Type": "application/json"},
                          json=payload, timeout=tout)
        r.raise_for_status()
        reply = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        add_history(chat_id, "user", text if text.strip() else "[скриншот]")
        add_history(chat_id, "model", reply)
        return reply
    except requests.exceptions.Timeout:
        logger.error("[AI Reply] Таймаут Gemini.")
    except requests.exceptions.HTTPError as e:
        logger.error("[AI Reply] HTTP ошибка Gemini: %s", e.response.status_code)
    except Exception:
        logger.error("[AI Reply] Ошибка Gemini.", exc_info=True)
    return None


# ───────── Обработчик сообщений ─────────

def process_message(cardinal: Cardinal, e: NewMessageEvent | LastChatMessageChangedEvent):
    if not get("enabled"):
        return

    if not cardinal.old_mode_enabled:
        if isinstance(e, LastChatMessageChangedEvent):
            return
        obj          = e.message
        msg_text     = obj.text or ""
        image_url    = obj.image_link or None
        chat_id      = obj.chat_id
        chat_name    = obj.chat_name
        author_id    = obj.author_id
        msg_type     = obj.type
    else:
        if isinstance(e, NewMessageEvent):
            return
        obj          = e.chat
        msg_text     = str(obj)
        image_url    = None
        chat_id      = obj.id
        chat_name    = obj.name
        author_id    = None
        msg_type     = obj.last_message_type

    if author_id == cardinal.account.id:
        return
    if msg_type != MessageTypes.NON_SYSTEM:
        return
    if not msg_text.strip() and not image_url:
        return
    if cardinal.bl_response_enabled and chat_name in cardinal.blacklist:
        return
    if not image_url:
        cmd = msg_text.strip().lower().replace("\n", "")
        if cardinal.autoresponse_enabled and cmd in cardinal.AR_CFG:
            return
    if chat_id in handoff_chats:
        return
    if not antispam_ok(chat_id):
        return

    api_key = str(get("api_key")).strip()
    if not api_key:
        logger.error("[AI Reply] API ключ не задан! Настройте плагин в Telegram.")
        return

    def send():
        if is_silent():
            cardinal.send_message(chat_id, str(get("silent_message")), chat_name)
            mark_replied(chat_id)
            return

        reply = ask_gemini(chat_id, msg_text, image_url)

        if reply is None:
            Thread(target=notify, args=(cardinal,
                "AI Reply: Gemini не ответил.\n"
                "Чат: " + chat_name + " (id: " + str(chat_id) + ")\n"
                "Сообщение: " + msg_text[:200]
            ), daemon=True).start()
            return

        if "[ПЕРЕДАТЬ_ПРОДАВЦУ]" in reply:
            clean = reply.replace("[ПЕРЕДАТЬ_ПРОДАВЦУ]", "").strip()
            if clean:
                cardinal.send_message(chat_id, clean, chat_name)
            handoff_chats[chat_id] = time.time()
            mark_replied(chat_id)
            Thread(target=notify, args=(cardinal,
                "AI Reply: требуется ваше внимание!\n"
                "Чат: " + chat_name + " (id: " + str(chat_id) + ")\n"
                "Сообщение: " + msg_text[:300] + "\n\n"
                "Бот замолчал. Откройте настройки плагина -> вернуть чат боту."
            ), daemon=True).start()
        else:
            cardinal.send_message(chat_id, reply, chat_name)
            mark_replied(chat_id)

    Thread(target=send, daemon=True).start()


# ───────── Клавиатуры ─────────

def kb_main():
    data    = load_data()
    enabled = data.get("enabled", True)
    silent  = data.get("silent_enabled", False)
    model   = data.get("model", "gemini-1.5-flash")
    has_key = bool(data.get("api_key", ""))

    kb = K(row_width=1)
    kb.add(B(
        "API ключ: " + ("✅ задан" if has_key else "❌ не задан"),
        callback_data=CBT_SET_KEY
    ))
    kb.add(B(
        ("🟢" if enabled else "🔴") + " AI-ответы " + ("включены" if enabled else "выключены"),
        callback_data=CBT_TOGGLE
    ))
    kb.add(B("📋 Изменить статус продавца", callback_data=CBT_SET_STATUS))
    kb.add(B(
        ("🟢" if silent else "🔴") + " Режим тишины " + ("включён" if silent else "выключен"),
        callback_data=CBT_TOG_SIL
    ))
    kb.add(B("🕐 Часы тишины: " + str(data.get("silent_start", 0)) + ":00 - " + str(data.get("silent_end", 9)) + ":00", callback_data=CBT_SIL_HOURS))
    kb.add(B("💬 Сообщение тишины", callback_data=CBT_SIL_MSG))
    kb.add(B("🤖 Модель: " + model, callback_data=CBT_TOG_MODEL))
    if handoff_chats:
        kb.add(B("🙋 Чаты ожидающие вас (" + str(len(handoff_chats)) + ")", callback_data=CBT_HANDOFF))
    kb.add(B("◀️ Назад", callback_data=f"{CBT.EDIT_PLUGIN}:{UUID}:0"))
    return kb


def kb_back():
    return K().add(B("◀️ Назад", callback_data=CBT_MAIN))


def kb_handoff():
    kb = K(row_width=1)
    for cid, ts in list(handoff_chats.items()):
        t = datetime.fromtimestamp(ts).strftime("%H:%M")
        kb.add(B("Вернуть чат " + str(cid) + " (передан в " + t + ")", callback_data=CBT_RESUME + ":" + str(cid)))
    kb.add(B("◀️ Назад", callback_data=CBT_MAIN))
    return kb


# ───────── Инициализация и TG-панель ─────────

def init(cardinal: Cardinal):
    tg = cardinal.telegram
    if not tg:
        logger.warning("[AI Reply] Telegram не подключён!")
        return
    bot = tg.bot

    api_key = str(get("api_key")).strip()
    if not api_key:
        logger.warning("[AI Reply] API ключ не задан! Откройте настройки плагина в Telegram.")
    else:
        logger.info("[AI Reply] v%s загружен. Модель: %s", VERSION, get("model"))

    def open_settings(call: telebot.types.CallbackQuery):
        bot.edit_message_text(
            "Настройки AI Reply\n\nНастройте параметры плагина:",
            call.message.chat.id,
            call.message.id,
            reply_markup=kb_main()
        )
        bot.answer_callback_query(call.id)

    def ask_key(call: telebot.types.CallbackQuery):
        msg = bot.send_message(
            call.message.chat.id,
            "Введите API ключ от Google Gemini.\n\nПолучить бесплатно: https://aistudio.google.com/app/apikey\n\nКлюч выглядит так: AIzaSy...",
            reply_markup=tg_bot.static_keyboards.CLEAR_STATE_BTN()
        )
        tg.set_state(call.message.chat.id, msg.id, call.from_user.id, CBT_KEY_DONE, {})
        bot.answer_callback_query(call.id)

    def save_key(message: telebot.types.Message):
        tg.clear_state(message.chat.id, message.from_user.id, True)
        key = message.text.strip()
        set_val("api_key", key)
        bot.reply_to(message, "Ключ сохранён: " + key[:8] + "...", reply_markup=kb_back())

    def toggle_ai(call: telebot.types.CallbackQuery):
        set_val("enabled", not get("enabled"))
        bot.edit_message_reply_markup(call.message.chat.id, call.message.id, reply_markup=kb_main())
        bot.answer_callback_query(call.id)

    def ask_status(call: telebot.types.CallbackQuery):
        msg = bot.send_message(
            call.message.chat.id,
            "Текущий статус:\n" + str(get("status")) + "\n\nВведите новый статус:",
            reply_markup=tg_bot.static_keyboards.CLEAR_STATE_BTN()
        )
        tg.set_state(call.message.chat.id, msg.id, call.from_user.id, CBT_STS_DONE, {})
        bot.answer_callback_query(call.id)

    def save_status(message: telebot.types.Message):
        tg.clear_state(message.chat.id, message.from_user.id, True)
        set_val("status", message.text.strip())
        bot.reply_to(message, "Статус обновлён: " + message.text.strip(), reply_markup=kb_back())

    def toggle_silent(call: telebot.types.CallbackQuery):
        set_val("silent_enabled", not get("silent_enabled"))
        bot.edit_message_reply_markup(call.message.chat.id, call.message.id, reply_markup=kb_main())
        bot.answer_callback_query(call.id)

    def ask_hours(call: telebot.types.CallbackQuery):
        msg = bot.send_message(
            call.message.chat.id,
            "Введите часы тишины в формате: НАЧАЛО КОНЕЦ\n\nПример: 0 9 (тишина с 00:00 до 09:00)\nПример: 22 8 (с 22:00 до 08:00)",
            reply_markup=tg_bot.static_keyboards.CLEAR_STATE_BTN()
        )
        tg.set_state(call.message.chat.id, msg.id, call.from_user.id, CBT_SIL_H_DONE, {})
        bot.answer_callback_query(call.id)

    def save_hours(message: telebot.types.Message):
        tg.clear_state(message.chat.id, message.from_user.id, True)
        parts = message.text.strip().split()
        if len(parts) != 2 or not all(p.isdigit() for p in parts):
            bot.reply_to(message, "Неверный формат. Пример: 0 9", reply_markup=kb_back())
            return
        s, e = int(parts[0]), int(parts[1])
        if not (0 <= s <= 23 and 0 <= e <= 23):
            bot.reply_to(message, "Часы должны быть от 0 до 23.", reply_markup=kb_back())
            return
        set_val("silent_start", s)
        set_val("silent_end", e)
        bot.reply_to(message, "Режим тишины: с " + str(s) + ":00 до " + str(e) + ":00", reply_markup=kb_back())

    def ask_silent_msg(call: telebot.types.CallbackQuery):
        msg = bot.send_message(
            call.message.chat.id,
            "Введите сообщение которое бот отправит в режиме тишины:",
            reply_markup=tg_bot.static_keyboards.CLEAR_STATE_BTN()
        )
        tg.set_state(call.message.chat.id, msg.id, call.from_user.id, CBT_SIL_M_DONE, {})
        bot.answer_callback_query(call.id)

    def save_silent_msg(message: telebot.types.Message):
        tg.clear_state(message.chat.id, message.from_user.id, True)
        set_val("silent_message", message.text.strip())
        bot.reply_to(message, "Сообщение сохранено.", reply_markup=kb_back())

    def toggle_model(call: telebot.types.CallbackQuery):
        cur = get("model")
        new = "gemini-1.5-pro" if cur == "gemini-1.5-flash" else "gemini-1.5-flash"
        set_val("model", new)
        bot.edit_message_reply_markup(call.message.chat.id, call.message.id, reply_markup=kb_main())
        bot.answer_callback_query(call.id, "Модель: " + new)

    def open_handoff(call: telebot.types.CallbackQuery):
        if not handoff_chats:
            bot.answer_callback_query(call.id, "Нет чатов ожидающих вас!")
            return
        bot.edit_message_text(
            "Чаты ожидающие вашего ответа:",
            call.message.chat.id,
            call.message.id,
            reply_markup=kb_handoff()
        )
        bot.answer_callback_query(call.id)

    def resume_chat(call: telebot.types.CallbackQuery):
        cid = int(call.data.split(":")[-1])
        if cid in handoff_chats:
            del handoff_chats[cid]
        bot.edit_message_text(
            "Чат " + str(cid) + " возвращён боту.",
            call.message.chat.id,
            call.message.id,
            reply_markup=kb_back()
        )
        bot.answer_callback_query(call.id)

    tg.msg_handler(save_key,        func=lambda m: tg.check_state(m.chat.id, m.from_user.id, CBT_KEY_DONE))
    tg.msg_handler(save_status,     func=lambda m: tg.check_state(m.chat.id, m.from_user.id, CBT_STS_DONE))
    tg.msg_handler(save_hours,      func=lambda m: tg.check_state(m.chat.id, m.from_user.id, CBT_SIL_H_DONE))
    tg.msg_handler(save_silent_msg, func=lambda m: tg.check_state(m.chat.id, m.from_user.id, CBT_SIL_M_DONE))

    tg.cbq_handler(open_settings, lambda c: f"{CBT.PLUGIN_SETTINGS}:{UUID}" in c.data)
    tg.cbq_handler(open_settings, lambda c: CBT_MAIN in c.data)
    tg.cbq_handler(ask_key,       lambda c: CBT_SET_KEY in c.data)
    tg.cbq_handler(toggle_ai,     lambda c: CBT_TOGGLE in c.data and CBT_TOG_SIL not in c.data and CBT_TOG_MODEL not in c.data)
    tg.cbq_handler(ask_status,    lambda c: CBT_SET_STATUS in c.data)
    tg.cbq_handler(toggle_silent, lambda c: CBT_TOG_SIL in c.data)
    tg.cbq_handler(ask_hours,     lambda c: CBT_SIL_HOURS in c.data)
    tg.cbq_handler(ask_silent_msg,lambda c: CBT_SIL_MSG in c.data)
    tg.cbq_handler(toggle_model,  lambda c: CBT_TOG_MODEL in c.data)
    tg.cbq_handler(open_handoff,  lambda c: CBT_HANDOFF in c.data)
    tg.cbq_handler(resume_chat,   lambda c: CBT_RESUME in c.data and ":" in c.data.replace(CBT_RESUME, ""))


BIND_TO_PRE_INIT = [init]
BIND_TO_NEW_MESSAGE = [process_message]
BIND_TO_LAST_CHAT_MESSAGE_CHANGED = [process_message]
