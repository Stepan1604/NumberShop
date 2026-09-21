import sys
import asyncio
import json
import logging
import re
import threading
import time
from datetime import datetime
from typing import Any, Dict

import aiohttp
import requests
import telebot
from telebot import types
from telebot.async_telebot import AsyncTeleBot

from telethon import TelegramClient, errors
from telethon.sessions import StringSession

from flask import Flask, request

import database as db

# --------------------------------------------------------------------------- #
#                              КОНФИГУРАЦИЯ                                    #
# --------------------------------------------------------------------------- #

from config import (
    BOT_TOKEN,
    ADMIN_ID,
    API_ID,
    API_HASH,
    YOOMONEY_WALLET,
    ADMINS,
    COUNTRIES,
)

try:
    from config import HELPER_ID
except ImportError:
    HELPER_ID = None

if HELPER_ID is None:
    HELPER_ID = ADMIN_ID
    print("ℹ️ HELPER_ID не задан — используется ADMIN_ID")

print("✅ Конфигурация загружена из config.py")


# --------------------------------------------------------------------------- #
#                                 ЛОГИРОВАНИЕ                                  #
# --------------------------------------------------------------------------- #

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
logging.getLogger("telethon").setLevel(logging.WARNING)

# --------------------------------------------------------------------------- #
#                             ГЛОБАЛЬНОЕ СОСТОЯНИЕ                            #
# --------------------------------------------------------------------------- #

if ADMIN_ID not in ADMINS:
    ADMINS = list(ADMINS) + [ADMIN_ID]

MODERATORS = []
ALL_ADMINS = list(ADMINS)

clients: Dict[int, Dict[str, Any]] = {}
accounts: Dict[int, Dict[str, Dict]] = {}
awaiting_phone_confirmation: Dict[int, Dict] = {}
pending_rub: Dict[int, Dict] = {}
subscriptions: Dict[int, Any] = {}
telethon_clients_cache: Dict[str, TelegramClient] = {}

clients_lock = asyncio.Lock()
accounts_lock = asyncio.Lock()

user_state: Dict[int, Dict[str, Any]] = {}

# --------------------------------------------------------------------------- #
#                              БОТ (telebot)                                   #
# --------------------------------------------------------------------------- #

bot = AsyncTeleBot(BOT_TOKEN)


# --------------------------------------------------------------------------- #
#                              ХЕЛПЕРЫ                                         #
# --------------------------------------------------------------------------- #

def normalize_phone(phone: str) -> str:
    if not phone:
        return phone
    phone = phone.strip()
    if not phone.startswith("+"):
        phone = "+" + phone
    return phone


def get_country_by_phone(phone: str):
    phone = normalize_phone(phone)
    for country in sorted(COUNTRIES, key=lambda c: len(c["phone_code"]), reverse=True):
        if phone.startswith(country["phone_code"]):
            return country["code"]
    return "UNKNOWN"


def get_country_by_code(code: str):
    for country in COUNTRIES:
        if country["code"] == code:
            return country
    return None


def hide_phone(phone: str) -> str:
    phone = normalize_phone(phone)
    if phone and len(phone) > 6:
        return f"{phone[:4]}{phone[-4:]}"
    return phone


def validate_phone(phone: str) -> bool:
    return bool(re.match(r"^\+\d{10,15}$", phone))


def is_admin(user_id: int) -> bool:
    return user_id in ALL_ADMINS


def is_super_admin(user_id: int) -> bool:
    return user_id in ADMINS


def btn(text: str, callback_data: str) -> types.InlineKeyboardButton:
    return types.InlineKeyboardButton(text=text, callback_data=callback_data)


def url_btn(text: str, url: str) -> types.InlineKeyboardButton:
    return types.InlineKeyboardButton(text=text, url=url)


def kb(rows) -> types.InlineKeyboardMarkup:
    return types.InlineKeyboardMarkup(rows)


def back(cb: str = "start") -> types.InlineKeyboardMarkup:
    return kb([[btn("🔙 НАЗАД", cb)]])


def set_state(user_id: int, state: str, **kwargs) -> None:
    data = user_state.setdefault(user_id, {})
    data["state"] = state
    data.update(kwargs)


def get_state(user_id: int) -> Dict[str, Any]:
    return user_state.get(user_id, {})


def clear_state(user_id: int) -> None:
    user_state.pop(user_id, None)


async def edit_or_send(call: types.CallbackQuery, text: str, reply_markup=None,
                       parse_mode: str = "Markdown") -> None:
    try:
        await bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=text,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
        )
    except Exception:
        try:
            await bot.send_message(
                call.message.chat.id, text, parse_mode=parse_mode,
                reply_markup=reply_markup,
            )
        except Exception as e:
            logger.error(f"edit_or_send error: {e}")


async def _send_or_edit(chat_id: int, text: str, reply_markup,
                        edit_message_id: int = None,
                        parse_mode: str = "Markdown") -> None:
    if edit_message_id:
        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=edit_message_id,
                text=text,
                parse_mode=parse_mode,
                reply_markup=reply_markup,
            )
            return
        except Exception:
            pass
    await bot.send_message(chat_id, text, parse_mode=parse_mode,
                           reply_markup=reply_markup)


async def check_yoomoney_payment_async(label: str) -> bool:
    try:
        url = f"https://yoomoney.ru/api/operation-history?label={label}&records=1"
        timeout = aiohttp.ClientTimeout(total=5)
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=timeout) as response:
                if response.status == 200:
                    data = await response.json()
                    for op in data.get("operations", []):
                        if op.get("status") == "success":
                            return True
        return False
    except Exception:
        return False


def load_admins() -> None:
    global ADMINS, MODERATORS, ALL_ADMINS
    try:
        admins, moderators = db.load_admins_from_db(ADMIN_ID)
        ADMINS = admins
        MODERATORS = moderators
        ALL_ADMINS = list(set(ADMINS + MODERATORS))
        logger.info(f"✅ Админы: {ADMINS}")
        logger.info(f"✅ Модераторы: {MODERATORS}")
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки админов: {e}")


# --------------------------------------------------------------------------- #
#                        ГЕНЕРАЦИЯ СООБЩЕНИЙ / МЕНЮ                            #
# --------------------------------------------------------------------------- #

def main_menu_markup(user_id: int) -> types.InlineKeyboardMarkup:
    rows = [
        [btn("🛒 МАГАЗИН", "shop")],
        [btn("📦 МОИ ПОКУПКИ", "my_purchases")],
        [btn("⭐ ОТЗЫВЫ", "reviews")],
        [btn("💡 ПРЕДЛОЖКА", "offer")],
        [btn("🆘 ПОДДЕРЖКА", "support")],
    ]
    if is_admin(user_id):
        rows.append([btn("👥 АДМИН-ПАНЕЛЬ", "admin_panel")])
    return kb(rows)


MAIN_MENU_TEXT = (
    "🏪 МАГАЗИН PONCHI\n\n👋 Добро пожаловать!\n"
    "📱 Покупайте номера с доставкой кода.\n\nВыберите действие:"
)


def generate_product_message(phone: str, price_rub: int,
                             two_fa: str = "") -> str:
    country_code = get_country_by_phone(phone)
    country = get_country_by_code(country_code) if country_code else None
    flag = country["flag"] if country else "🌍"
    name = country["name"] if country else "Неизвестно"
    code = country["phone_code"] if country else ""
    two_fa_text = f"🔐 2FA ПАРОЛЬ: `{two_fa}`\n\n" if two_fa else ""
    return (
        f"✅ ОПЛАЧЕНО!\n\n"
        f"🌍 Страна: {flag} {name} ({code})\n"
        f"📱 ВАШ НОМЕР: `{phone}`\n"
        f"💰 {price_rub} ₽\n\n"
        f"{two_fa_text}"
        f"----\n"
        f"⚠️ ПОСЛЕ ВХОДА В АККАУНТ ОБЯЗАТЕЛЬНО:\n"
        f"1️⃣ Смените номер телефона на свой\n"
        f"2️⃣ Поставьте двухфакторную аутентификацию (2FA)\n"
        f"3️⃣ Установите облачный пароль\n"
        f"4️⃣ Привяжите почту для восстановления\n\n"
        f"🔑 Нажмите кнопку, чтобы получить код для входа:"
    )


# --------------------------------------------------------------------------- #
#                        TELETHON: РАБОТА С АККАУНТАМИ                         #
# --------------------------------------------------------------------------- #

async def get_or_create_telegram_client(
    phone: str, session_string: str = None
) -> TelegramClient:
    phone = normalize_phone(phone)
    if phone in telethon_clients_cache:
        client = telethon_clients_cache[phone]
        if client.is_connected():
            return client
        try:
            await client.connect()
            if await client.is_user_authorized():
                return client
        except Exception:
            pass

    if session_string:
        client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
    else:
        client = TelegramClient(StringSession(), API_ID, API_HASH)

    await asyncio.wait_for(client.connect(), timeout=15)
    if await client.is_user_authorized():
        telethon_clients_cache[phone] = client
    return client


async def get_last_code_from_account(phone: str, session_string: str):
    """Пытается найти код подтверждения в чате Telegram на аккаунте."""
    try:
        client = await get_or_create_telegram_client(phone, session_string)
        if not await client.is_user_authorized():
            return None, "Сессия не авторизована. Обратитесь в поддержку."
        try:
            await asyncio.wait_for(client.send_code_request(phone), timeout=10)
        except Exception as e:
            logger.warning(f"Не удалось отправить запрос кода: {e}")

        telegram_dialog = None
        async for dialog in client.iter_dialogs():
            if "Telegram" in dialog.name:
                telegram_dialog = dialog
                break
        if not telegram_dialog:
            return None, "Чат Telegram не найден"

        await asyncio.sleep(5)
        code = None
        async for msg in client.iter_messages(telegram_dialog.id, limit=20):
            if not msg or not msg.text or msg.out:
                continue
            match = re.search(r"\b(\d{5})\b", msg.text)
            if match:
                code = match.group(1)
                logger.info(f"[AUTO-CODE] Найден код: {code}")
                break
        if code:
            return code, "Код найден"
        return None, "Код не найден в сообщениях. Попробуйте запросить новый код."
    except Exception as e:
        logger.error(f"[AUTO-CODE] Ошибка: {e}")
        return None, f"Ошибка: {str(e)[:100]}"


async def send_code_to_phone(phone: str, user_id: int):
    """Отправляет запрос кода на номер при добавлении товара."""
    try:
        session = StringSession()
        client = TelegramClient(session, API_ID, API_HASH)
        await asyncio.wait_for(client.connect(), timeout=10)
        result = await asyncio.wait_for(client.send_code_request(phone), timeout=10)
        async with clients_lock:
            clients[user_id] = {
                "client": client,
                "phone": phone,
                "phone_code_hash": result.phone_code_hash,
            }
        return True, "✅ Код отправлен"
    except Exception as e:
        return False, f"❌ {str(e)[:50]}"


async def enter_code_in_telegram(code: str, user_id: int):
    """Вводит код входа в аккаунт и сохраняет сессию."""
    try:
        async with clients_lock:
            if user_id not in clients:
                return False, "Сессия потеряна", None, None
            data = clients[user_id]
            client = data["client"]
            phone = data["phone"]
            phone_hash = data["phone_code_hash"]

        await asyncio.wait_for(
            client.sign_in(phone, code, phone_code_hash=phone_hash), timeout=10
        )
        me = await client.get_me()
        session_string = client.session.save()
        db.save_phone_session(phone, session_string)

        async with accounts_lock:
            accounts.setdefault(user_id, {})
            if phone not in accounts[user_id]:
                accounts[user_id][phone] = {
                    "codes": [],
                    "product_id": None,
                    "client": client,
                    "phone": phone,
                    "session": session_string,
                }
        async with clients_lock:
            clients.pop(user_id, None)
        return True, f"✅ Вход как {me.first_name}", me, None
    except errors.SessionPasswordNeededError:
        return False, "2FA", None, None
    except Exception as e:
        return False, str(e), None, None


async def enter_2fa_in_telegram(password: str, user_id: int):
    """Проходит 2FA и сохраняет сессию."""
    try:
        async with clients_lock:
            if user_id not in clients:
                return False, "Сессия потеряна", None, None
            client = clients[user_id]["client"]
            phone = clients[user_id]["phone"]

        await asyncio.wait_for(client.sign_in(password=password), timeout=10)
        me = await client.get_me()
        session_string = client.session.save()
        db.save_phone_session(phone, session_string)

        async with accounts_lock:
            accounts.setdefault(user_id, {})
            if phone not in accounts[user_id]:
                accounts[user_id][phone] = {
                    "codes": [],
                    "product_id": None,
                    "client": client,
                    "phone": phone,
                    "session": session_string,
                    "creation_date": None,
                }
        async with clients_lock:
            clients.pop(user_id, None)
        return True, "✅ 2FA пройдена", me, None
    except Exception as e:
        return False, str(e), None, None


async def add_phone_to_shop_now(
    phone: str,
    price_rub: int,
    session_string: str = "",
    lzt_item_id: int = None,
    two_fa: str = "",
    user_id: int = None,
    notify: bool = True,
    client=None,
) -> bool:
    """Добавляет номер в магазин и (опционально) уведомляет пользователя."""
    phone = normalize_phone(phone)
    try:
        result = db.add_phone_product(
            phone, price_rub, session_string, lzt_item_id, two_fa
        )
        logger.info(
            f"🛒 Номер {phone} добавлен в магазин "
            f"(цена {price_rub}₽, lzt_item_id={lzt_item_id})"
        )

        if client is not None:
            if phone not in telethon_clients_cache:
                telethon_clients_cache[phone] = client
        elif session_string:
            try:
                await get_or_create_telegram_client(phone, session_string)
            except Exception as e:
                logger.warning(f"Не удалось подготовить клиент для {phone}: {e}")

        if result and user_id and notify:
            country_code = get_country_by_phone(phone)
            country = get_country_by_code(country_code)
            country_flag = country["flag"] if country else "🌍"
            country_name = country["name"] if country else "Неизвестно"
            try:
                await bot.send_message(
                    user_id,
                    (
                        f"✅ НОМЕР ДОБАВЛЕН В МАГАЗИН!\n\n"
                        f"📱 `{phone}`\n"
                        f"🌍 {country_flag} {country_name}\n"
                        f"💰 {price_rub} ₽\n\n"
                        f"🔒 Клиент аккаунта подключён навсегда и не отключается.\n"
                        f"🏪 Номер уже доступен для покупки."
                    ),
                    parse_mode="Markdown",
                )
            except Exception as e:
                logger.error(f"❌ Не удалось уведомить {user_id}: {e}")
        return result
    except Exception as e:
        logger.error(f"❌ Ошибка добавления в магазин: {e}")
        return False


# --------------------------------------------------------------------------- #
#                       ПОЛЬЗОВАТЕЛЬ: СТАРТ И МЕНЮ                             #
# --------------------------------------------------------------------------- #

async def send_terms(chat_id: int, edit_message_id: int = None) -> None:
    text = (
        "🔒 ПРАВИЛА И КОНФИДЕНЦИАЛЬНОСТЬ\n\n"
        "📋 Условия использования:\n"
        "• Приобретая аккаунты, вы подтверждаете, что будете использовать их в законных целях\n"
        "• Запрещено использование для мошенничества, спама, обмана\n"
        "• Продавец не несет ответственности за действия покупателей\n\n"
        "🛡️ Политика продавца:\n"
        "• Продавец выдает ровно столько аккаунтов, сколько вы покупаете\n"
        "• Код для активации высылается один раз\n"
        "• Замена аккаунта выдаётся только в том случае, если код для входа не подходит\n"
        "• Продавец не обязан выдавать вам замену, если вас выкинуло с аккаунта\n"
        "• Возврат средств не предусмотрен\n\n"
        "📱 Правила использования виртуальных номеров:\n"
        "• Запрещена массовая регистрация в коммерческих целях\n"
        "• Не рекомендуется использовать для критически важных сервисов\n"
        "• Аккаунт может быть заблокирован Telegram\n"
        "• Рекомендуется привязать email\n\n"
        "✅ Нажимая «Принять правила», вы подтверждаете:\n"
        "1. Ознакомление с правилами\n"
        "2. Использование в законных целях\n"
        "3. Понимание рисков\n"
        "4. Согласие с политикой продавца"
    )
    markup = kb([
        [btn("✅ ПРИНЯТЬ ПРАВИЛА", "agree_terms")],
        [btn("❌ ОТКЛОНИТЬ", "disagree_terms")],
    ])
    await _send_or_edit(chat_id, text, markup, edit_message_id)


async def send_main_menu(chat_id: int, user_id: int, edit_message_id: int = None) -> None:
    await _send_or_edit(chat_id, MAIN_MENU_TEXT, main_menu_markup(user_id), edit_message_id)


@bot.message_handler(commands=["start"])
async def cmd_start(message: types.Message) -> None:
    user_id = message.from_user.id
    if subscriptions.get(user_id) == "agreed":
        await send_main_menu(message.chat.id, user_id)
        return
    subscriptions[user_id] = True
    await send_terms(message.chat.id)


@bot.callback_query_handler(func=lambda c: c.data == "start")
async def cb_start(call: types.CallbackQuery) -> None:
    await bot.answer_callback_query(call.id)
    user_id = call.from_user.id
    if subscriptions.get(user_id) == "agreed":
        await send_main_menu(call.message.chat.id, user_id, call.message.message_id)
    else:
        subscriptions[user_id] = True
        await send_terms(call.message.chat.id, call.message.message_id)


@bot.callback_query_handler(func=lambda c: c.data == "agree_terms")
async def cb_agree_terms(call: types.CallbackQuery) -> None:
    await bot.answer_callback_query(call.id, "✅ Спасибо!")
    subscriptions[call.from_user.id] = "agreed"
    try:
        await bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    await send_main_menu(call.message.chat.id, call.from_user.id)


@bot.callback_query_handler(func=lambda c: c.data == "disagree_terms")
async def cb_disagree_terms(call: types.CallbackQuery) -> None:
    await bot.answer_callback_query(call.id, "❌ Вы отклонили правила!")
    subscriptions[call.from_user.id] = False
    await edit_or_send(
        call,
        "❌ РЕГИСТРАЦИЯ НЕ МОЖЕТ БЫТЬ ПРОДОЛЖЕНА\n\n"
        "Вы отклонили правила бота.\n\n"
        "Для того чтобы заново их принять, нажмите /start.",
    )


@bot.callback_query_handler(func=lambda c: c.data == "reviews")
async def cb_reviews(call: types.CallbackQuery) -> None:
    await bot.answer_callback_query(call.id)
    markup = kb([
        [url_btn("⭐ ЧИТАТЬ ОТЗЫВЫ", "https://t.me/+xjuMFVL-lLwyZTZi")],
        [btn("🔙 НАЗАД", "start")],
    ])
    await edit_or_send(
        call, "⭐ ОТЗЫВЫ\n\nНажмите на кнопку, чтобы перейти в канал с отзывами!", markup
    )


@bot.callback_query_handler(func=lambda c: c.data == "support")
async def cb_support(call: types.CallbackQuery) -> None:
    await bot.answer_callback_query(call.id)
    await edit_or_send(
        call,
        "🆘 ПОДДЕРЖКА\n\n👤 @Good_NaBloke",
        back("start"),
        parse_mode=None,
    )


# --------------------------------------------------------------------------- #
#                              ПРЕДЛОЖКИ                                       #
# --------------------------------------------------------------------------- #

@bot.callback_query_handler(func=lambda c: c.data == "offer")
async def cb_offer(call: types.CallbackQuery) -> None:
    await bot.answer_callback_query(call.id)
    await edit_or_send(
        call,
        "💡 Вы можете сделать предложение по улучшению бота!\n\n"
        "Нажмите «Сделать своё предложение», затем отправьте вашу идею "
        "одним сообщением — она будет передана администратору.",
        kb([
            [btn("Сделать своё предложение", "make_offer")],
            [btn("Назад", "start")],
        ]),
    )


@bot.callback_query_handler(func=lambda c: c.data == "make_offer")
async def cb_make_offer(call: types.CallbackQuery) -> None:
    await bot.answer_callback_query(call.id)
    set_state(call.from_user.id, "awaiting_offer")
    await edit_or_send(
        call,
        "✍️ Напишите ваше предложение одним сообщением.\n"
        "Оно будет отправлено администратору.",
    )


async def receive_offer(message: types.Message, state: Dict[str, Any]) -> None:
    user = message.from_user
    offer_text = message.text
    author = f"{user.full_name} (@{user.username})" if user.username else user.full_name
    time_str = datetime.now().strftime("%d.%m.%Y %H:%M")
    admin_text = (
        f"📩 Новое предложение!\n\n"
        f"💬 {offer_text}\n\n"
        f"👤 Отправитель: {author}\n"
        f"🕒 Время: {time_str}"
    )
    markup = kb([
        [btn("Принять", f"accept_offer:{user.id}"),
         btn("Отклонить", f"reject_offer:{user.id}")],
    ])
    await bot.send_message(HELPER_ID, admin_text, reply_markup=markup)
    await bot.send_message(
        message.chat.id,
        "✅ Ваше предложение отправлено администратору!\n"
        "Когда будет принято решение, вы получите уведомление.",
    )
    clear_state(user.id)
    await send_main_menu(message.chat.id, user.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith("accept_offer:"))
async def cb_accept_offer(call: types.CallbackQuery) -> None:
    await bot.answer_callback_query(call.id)
    user_id = int(call.data.split(":")[1])
    await edit_or_send(call, call.message.text + "\n\n✅ Предложение принято!")
    await bot.send_message(user_id, "✅ Ваше предложение было принято администратором!")


@bot.callback_query_handler(func=lambda c: c.data.startswith("reject_offer:"))
async def cb_reject_offer(call: types.CallbackQuery) -> None:
    await bot.answer_callback_query(call.id)
    user_id = int(call.data.split(":")[1])
    await edit_or_send(call, call.message.text + "\n\n❌ Предложение отклонено!")
    await bot.send_message(user_id, "❌ Ваше предложение было отклонено администратором.")


# --------------------------------------------------------------------------- #
#                              МАГАЗИН                                         #
# --------------------------------------------------------------------------- #

def group_products_by_country(products):
    """Группирует товары по коду страны, сортирует страны по названию."""
    data = {}
    for product in products:
        code = get_country_by_phone(product.phone)
        data.setdefault(code, []).append(product)

    def sort_key(item):
        country = get_country_by_code(item[0])
        return country["name"] if country else item[0]

    return sorted(data.items(), key=sort_key)


async def show_shop_page(chat_id: int, countries_list, page: int,
                         edit_message_id: int = None) -> None:
    if not countries_list:
        await _send_or_edit(chat_id, "❌ Нет стран с номерами", back("start"),
                            edit_message_id)
        return

    total_pages = (len(countries_list) + 5) // 6
    page = max(0, min(page, total_pages - 1))
    start_idx = page * 6
    end_idx = min(start_idx + 6, len(countries_list))
    page_countries = countries_list[start_idx:end_idx]

    rows = []
    for country_code, phones in page_countries:
        country = get_country_by_code(country_code)
        if country:
            rows.append([
                btn(
                    f"{country['flag']} {country['name']} ({country['phone_code']}) "
                    f"· {len(phones)} шт.",
                    f"shop_country_{country_code}",
                )
            ])

    nav_buttons = []
    if page > 0:
        nav_buttons.append(btn("⬅️ НАЗАД", f"shop_page_{page - 1}"))
    if page < total_pages - 1:
        nav_buttons.append(btn("➡️ ДАЛЕЕ", f"shop_page_{page + 1}"))
    if nav_buttons:
        rows.append(nav_buttons)
    rows.append([btn("🔙 НАЗАД", "start")])

    text = ("🏪 МАГАЗИН PONCHI\n\nВыберите страну:\n\n"
            f"📄 Страница {page + 1} из {total_pages}")
    await _send_or_edit(chat_id, text, kb(rows), edit_message_id)


@bot.callback_query_handler(func=lambda c: c.data == "shop")
async def cb_shop(call: types.CallbackQuery) -> None:
    await bot.answer_callback_query(call.id)
    products = db.get_phone_products()
    if not products:
        await _send_or_edit(call.message.chat.id, "❌ Номеров нет", back("start"),
                            call.message.message_id)
        return
    countries_list = group_products_by_country(products)
    set_state(call.from_user.id, "shop", countries_list=countries_list, page=0)
    await show_shop_page(call.message.chat.id, countries_list, 0, call.message.message_id)


@bot.callback_query_handler(func=lambda c: c.data.startswith("shop_page_"))
async def cb_shop_page(call: types.CallbackQuery) -> None:
    await bot.answer_callback_query(call.id)
    page = int(call.data.replace("shop_page_", ""))
    state = get_state(call.from_user.id)
    countries_list = state.get("countries_list", [])
    if not countries_list:
        products = db.get_phone_products()
        countries_list = group_products_by_country(products)
    set_state(call.from_user.id, "shop", countries_list=countries_list, page=page)
    await show_shop_page(call.message.chat.id, countries_list, page,
                         call.message.message_id)


@bot.callback_query_handler(func=lambda c: c.data.startswith("shop_country_"))
async def cb_shop_country(call: types.CallbackQuery) -> None:
    await bot.answer_callback_query(call.id)
    country_code = call.data.replace("shop_country_", "")
    country = get_country_by_code(country_code)
    if not country:
        await edit_or_send(call, "❌ Страна не найдена", back("shop"))
        return

    products = db.get_phone_products()
    country_phones = [
        p for p in products if p.phone.startswith(country["phone_code"])
    ]
    if not country_phones:
        await edit_or_send(
            call, f"❌ Нет номеров для {country['flag']} {country['name']}", back("shop")
        )
        return

    country_phones.sort(key=lambda p: p.price_rub)
    rows = []
    for idx, p in enumerate(country_phones, 1):
        rows.append([
            btn(
                f"[{idx}] {country['flag']} {country['phone_code']} | "
                f"{p.price_rub}₽",
                f"select_phone_{p.id}",
            )
        ])
    rows.append([btn("🔙 НАЗАД", "shop")])
    await edit_or_send(
        call,
        f"📍 {country['flag']} {country['name']} ({country['phone_code']})\n\n"
        f"📱 Доступно: {len(country_phones)} номеров\nСортировка по цене ↑",
        kb(rows),
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("select_phone_"))
async def cb_select_phone(call: types.CallbackQuery) -> None:
    await bot.answer_callback_query(call.id)
    product_id = int(call.data.split("_")[2])
    product = db.get_phone_product(product_id)
    if not product:
        await edit_or_send(call, "❌ Номер уже продан или удалён")
        return

    phone = product.phone
    country_code = get_country_by_phone(phone)
    country = get_country_by_code(country_code) if country_code else None
    flag = country["flag"] if country else "🌍"
    name = country["name"] if country else "Неизвестно"
    code = country["phone_code"] if country else ""
    hidden_phone = hide_phone(phone)

    rows = []
    if product.price_rub > 0:
        rows.append([btn(f"💳 Оплатить {product.price_rub} ₽", f"pay_rub_{product_id}")])
    rows.append([btn("🔙 НАЗАД", "shop")])

    await edit_or_send(
        call,
        f"💳 ОПЛАТА\n\n🌍 Страна: {flag} {name} ({code})\n"
        f"📱 Номер: `{hidden_phone}`\n"
        f"💰 Цена: {product.price_rub} ₽\n\n"
        f"⚠️ После оплаты вы получите полный номер и код для входа.",
        kb(rows),
    )


# --------------------------------------------------------------------------- #
#                            МОИ ПОКУПКИ                                       #
# --------------------------------------------------------------------------- #

@bot.callback_query_handler(func=lambda c: c.data == "my_purchases")
async def cb_my_purchases(call: types.CallbackQuery) -> None:
    await bot.answer_callback_query(call.id)
    purchases = db.get_user_purchases(call.from_user.id)
    if not purchases:
        await edit_or_send(
            call, "📦 МОИ ПОКУПКИ\n\nУ вас пока нет покупок.", back("start")
        )
        return

    rows = []
    for purchase in purchases:
        country = get_country_by_code(purchase.country_code) if purchase.country_code else None
        flag = country["flag"] if country else "🌍"
        code = country["phone_code"] if country else ""
        rows.append([btn(f"{flag} {code} {purchase.phone}", f"purchase_code_{purchase.id}")])
    rows.append([btn("🗑️ ОЧИСТИТЬ ИСТОРИЮ", "clear_purchases")])
    rows.append([btn("🔙 НАЗАД", "start")])
    await edit_or_send(
        call,
        f"📦 МОИ ПОКУПКИ\n\n📱 Всего покупок: {len(purchases)}\n\n"
        f"Выберите номер для просмотра информации:",
        kb(rows),
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("purchase_code_"))
async def cb_purchase_code(call: types.CallbackQuery) -> None:
    await bot.answer_callback_query(call.id)
    purchase_id = int(call.data.replace("purchase_code_", ""))
    purchase = db.get_purchase(purchase_id)
    if not purchase:
        await edit_or_send(call, "❌ Покупка не найдена", back("my_purchases"))
        return

    country = get_country_by_code(purchase.country_code) if purchase.country_code else None
    flag = country["flag"] if country else "🌍"
    name = country["name"] if country else "Неизвестно"
    code = country["phone_code"] if country else ""
    date_str = purchase.purchased_at.strftime("%d.%m.%Y %H:%M") if purchase.purchased_at else "—"

    await edit_or_send(
        call,
        f"📱 ИНФОРМАЦИЯ О НОМЕРЕ\n\n"
        f"🌍 Страна: {flag} {name} ({code})\n"
        f"📞 Номер: `{purchase.phone}`\n"
        f"💰 Цена: {purchase.price_rub} ₽\n"
        f"📆 Дата покупки: {date_str}\n\n"
        f"---\n"
        f"⚠️ ПОСЛЕ ВХОДА В АККАУНТ ОБЯЗАТЕЛЬНО:\n"
        f"1️⃣ Смените номер телефона на свой\n"
        f"2️⃣ Поставьте двухфакторную аутентификацию (2FA)\n"
        f"3️⃣ Установите облачный пароль\n"
        f"4️⃣ Привяжите почту для восстановления\n\n"
        f"🔑 Нажмите кнопку, чтобы получить код:",
        kb([
            [btn("🔑 ПОЛУЧИТЬ КОД", f"purchase_get_code_{purchase_id}")],
            [btn("🔙 К МОИМ ПОКУПКАМ", "my_purchases")],
        ]),
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("purchase_get_code_"))
async def cb_purchase_get_code(call: types.CallbackQuery) -> None:
    await bot.answer_callback_query(call.id)
    purchase_id = int(call.data.replace("purchase_get_code_", ""))
    purchase = db.get_purchase(purchase_id)
    if not purchase:
        await edit_or_send(call, "❌ Покупка не найдена", back("my_purchases"))
        return
    await _deliver_code(call, purchase.phone, purchase.session, purchase.lzt_item_id,
                        purchase_id)


@bot.callback_query_handler(func=lambda c: c.data.startswith("purchase_ok_"))
async def cb_purchase_ok(call: types.CallbackQuery) -> None:
    await bot.answer_callback_query(call.id)
    await _show_deal_done(call)


@bot.callback_query_handler(func=lambda c: c.data == "clear_purchases")
async def cb_clear_purchases(call: types.CallbackQuery) -> None:
    await bot.answer_callback_query(call.id)
    count = db.count_user_purchases(call.from_user.id)
    if count == 0:
        await edit_or_send(
            call, "📦 МОИ ПОКУПКИ\n\nУ вас нет покупок для очистки.", back("my_purchases")
        )
        return
    await edit_or_send(
        call,
        f"🗑️ ОЧИСТКА ИСТОРИИ ПОКУПОК\n\n"
        f"⚠️ Вы уверены, что хотите удалить ВСЕ свои покупки?\n\n"
        f"📱 Всего покупок: {count}\n\n"
        f"Это действие НЕЛЬЗЯ будет отменить!",
        kb([
            [btn("✅ ДА, УДАЛИТЬ ВСЕ", "clear_purchases_yes")],
            [btn("❌ НЕТ", "my_purchases")],
        ]),
    )


@bot.callback_query_handler(func=lambda c: c.data == "clear_purchases_yes")
async def cb_clear_purchases_yes(call: types.CallbackQuery) -> None:
    await bot.answer_callback_query(call.id)
    db.delete_user_purchases(call.from_user.id)
    await edit_or_send(
        call, "✅ ИСТОРИЯ ОЧИЩЕНА!\n\nВсе ваши покупки удалены.", back("my_purchases")
    )


# --------------------------------------------------------------------------- #
#                     ВЫДАЧА КОДА / ЗАВЕРШЕНИЕ СДЕЛКИ                          #
# --------------------------------------------------------------------------- #

async def _show_deal_done(call: types.CallbackQuery) -> None:
    await edit_or_send(
        call,
        "🎉 СДЕЛКА ЗАВЕРШЕНА!\n\n"
        "✅ Код подошёл! Аккаунт ваш!\n"
        "Спасибо за покупку! 🙏\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚠️ ВНИМАНИЕ! ОБЯЗАТЕЛЬНО ПРОЧИТАЙТЕ! ⚠️\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "❗ СРАЗУ ПОСЛЕ ВХОДА В АККАУНТ СДЕЛАЙТЕ ЭТО:\n\n"
        "1️⃣ СМЕНИТЕ НОМЕР ТЕЛЕФОНА НА СВОЙ! 🔄\n"
        "2️⃣ ПОСТАВЬТЕ ДВУХФАКТОРНУЮ АУТЕНТИФИКАЦИЮ (2FA)! 🔐\n"
        "3️⃣ УСТАНОВИТЕ ОБЛАЧНЫЙ ПАРОЛЬ! ☁️\n"
        "4️⃣ ПРИВЯЖИТЕ ПОЧТУ ДЛЯ ВОССТАНОВЛЕНИЯ! 📧\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔒 ЭТО ЗАЩИТИТ ВАШ АККАУНТ ОТ ВЗЛОМА! 🔒\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "⭐ Если вам понравилась работа бота,\n"
        "оставьте отзыв в нашем канале!",
        kb([
            [url_btn("⭐ ОСТАВИТЬ ОТЗЫВ", "https://t.me/poncisnop")],
            [btn("🏠 ГЛАВНОЕ МЕНЮ", "start")],
        ]),
    )


async def _deliver_code(call: types.CallbackQuery, phone: str, session: str,
                        lzt_item_id, purchase_id: int) -> None:
    """Общая логика получения кода (через telethon-сессию или LZT API)."""
    # --- Вариант 1: код получаем через LZT API ---
    if lzt_item_id:
        await edit_or_send(
            call,
            f"⏳ ЗАПРАШИВАЮ КОД ЧЕРЕЗ API...\n\n"
            f"📞 Номер: `{phone}`\nПожалуйста, подождите...",
        )
        try:
            token = db.get_lzt_token()
            market = _lzt_market_cls(token=token)
            if LZT_PROXY:
                market.settings.proxy = LZT_PROXY

            lzt_code = await asyncio.get_running_loop().run_in_executor(
                None, lambda: _lzt_fetch_verification_code(market, lzt_item_id)
            )
            if lzt_code:
                await edit_or_send(
                    call,
                    f"🔑 КОД ПОЛУЧЕН ЧЕРЕЗ API!\n\n"
                    f"📞 Номер: `{phone}`\n🔑 Код: `{lzt_code}`\n\n"
                    f"✅ Код подошёл для входа?",
                    kb([
                        [btn("✅ КОД ПОДОШЁЛ", f"purchase_ok_{purchase_id}")],
                        [btn("🔄 НОВЫЙ КОД", f"purchase_get_code_{purchase_id}")],
                        [btn("🔙 К МОИМ ПОКУПКАМ", "my_purchases")],
                    ]),
                )
            else:
                await edit_or_send(
                    call,
                    f"⚠️ КОД НЕ ПОЛУЧЕН\n\n"
                    f"📞 Номер: `{phone}`\n\n"
                    f"❌ API не вернул код.\nПопробуйте позже.",
                    kb([
                        [btn("🔄 ПОВТОРИТЬ", f"purchase_get_code_{purchase_id}")],
                        [btn("🔙 К МОИМ ПОКУПКАМ", "my_purchases")],
                    ]),
                )
        except Exception as e:
            logger.error(f"❌ Ошибка получения кода через LZT: {e}")
            await edit_or_send(
                call,
                f"❌ ОШИБКА ПРИ ПОЛУЧЕНИИ КОДА\n\n"
                f"📞 Номер: `{phone}`\n```\n{str(e)[:200]}\n```",
                kb([
                    [btn("🔄 ПОВТОРИТЬ", f"purchase_get_code_{purchase_id}")],
                    [btn("🔙 К МОИМ ПОКУПКАМ", "my_purchases")],
                ]),
            )
        return

    # --- Вариант 2: код ищем через telethon-сессию ---
    if not session:
        await edit_or_send(
            call,
            f"⚠️ НЕВОЗМОЖНО ПОЛУЧИТЬ КОД\n\n"
            f"📞 Номер: `{phone}`\n\n"
            f"❌ Для этого номера нет сессии и нет привязки к LZT Market.\n"
            f"Пожалуйста, обратитесь в поддержку.",
            back("my_purchases"),
        )
        return

    await edit_or_send(
        call,
        f"⏳ ПОДКЛЮЧАЮСЬ К АККАУНТУ ЧЕРЕЗ TELEGRAM...\n\n"
        f"📞 Номер: `{phone}`\nПожалуйста, подождите...",
    )
    try:
        code_found, result = await get_last_code_from_account(phone, session)
        if code_found:
            await edit_or_send(
                call,
                f"🔑 КОД НАЙДЕН ЧЕРЕЗ TELEGRAM!\n\n"
                f"📞 Номер: `{phone}`\n🔑 Код: `{code_found}`\n\n"
                f"✅ Код подошёл для входа?",
                kb([
                    [btn("✅ КОД ПОДОШЁЛ", f"purchase_ok_{purchase_id}")],
                    [btn("🔄 НОВЫЙ КОД", f"purchase_get_code_{purchase_id}")],
                    [btn("🔙 К МОИМ ПОКУПКАМ", "my_purchases")],
                ]),
            )
        else:
            await edit_or_send(
                call,
                f"⚠️ КОД НЕ НАЙДЕН\n\n"
                f"📞 Номер: `{phone}`\n\n❌ {result}\n\nПопробуйте повторить поиск.",
                kb([
                    [btn("🔄 ПОВТОРИТЬ", f"purchase_get_code_{purchase_id}")],
                    [btn("🔙 К МОИМ ПОКУПКАМ", "my_purchases")],
                ]),
            )
    except Exception as e:
        logger.error(f"❌ Ошибка получения кода через Telethon: {e}")
        await edit_or_send(
            call,
            f"❌ ОШИБКА ПРИ ПОЛУЧЕНИИ КОДА\n\n"
            f"📞 Номер: `{phone}`\n```\n{str(e)[:200]}\n```",
            kb([
                [btn("🔄 ПОВТОРИТЬ", f"purchase_get_code_{purchase_id}")],
                [btn("🏠 ГЛАВНОЕ МЕНЮ", "start")],
            ]),
        )


# --------------------------------------------------------------------------- #
#                              АДМИН-ПАНЕЛЬ                                    #
# --------------------------------------------------------------------------- #

@bot.callback_query_handler(func=lambda c: c.data == "admin_panel")
async def cb_admin_panel(call: types.CallbackQuery) -> None:
    await bot.answer_callback_query(call.id)
    user_id = call.from_user.id
    if not is_admin(user_id):
        await edit_or_send(call, "❌ Нет доступа!", back("start"))
        return

    rows = [
        [btn("🛒 КУПИТЬ НОМЕР (LZT)", "lzt_buy_menu")],
        [btn("🔑 СМЕНИТЬ LZT API TOKEN", "change_lzt_token")],
        [btn("📱 ДОБАВИТЬ НОМЕР", "add_phone")],
        [btn("✏️ ИЗМЕНИТЬ ЦЕНУ", "edit_price")],
        [btn("🎁 ВОЗМЕСТИТЬ АККАУНТ", "compensate")],
    ]
    if is_super_admin(user_id):
        rows.append([btn("➕ ДОБАВИТЬ АДМИНА", "add_admin")])
        rows.append([btn("🗑️ УДАЛИТЬ АДМИНА", "remove_admin")])
        rows.append([btn("📊 СПИСОК АДМИНОВ", "list_admins")])
        rows.append([btn("🗑️ УДАЛИТЬ НОМЕР", "delete_phone")])
    rows.append([btn("🔙 НАЗАД", "start")])

    role = "👑 ГЛАВНЫЙ АДМИН" if is_super_admin(user_id) else "🛠️ МОДЕРАТОР"
    await edit_or_send(
        call, f"👥 АДМИН-ПАНЕЛЬ\n\nВаша роль: {role}", kb(rows)
    )


# ------------------------------ АДМИНЫ ------------------------------------- #

@bot.callback_query_handler(func=lambda c: c.data == "add_admin")
async def cb_add_admin(call: types.CallbackQuery) -> None:
    await bot.answer_callback_query(call.id)
    if not is_super_admin(call.from_user.id):
        await edit_or_send(call, "❌ Только главный админ!", back("admin_panel"))
        return
    set_state(call.from_user.id, "add_admin")
    await edit_or_send(call, "➕ Введите ID пользователя:", back("admin_panel"))


async def state_add_admin(message: types.Message, state: Dict[str, Any]) -> None:
    user_id = message.from_user.id
    if not is_super_admin(user_id):
        await bot.send_message(message.chat.id, "❌ Нет доступа!", reply_markup=back("admin_panel"))
        clear_state(user_id)
        return
    new_admin_id = message.text.strip()
    if not new_admin_id.isdigit():
        await bot.send_message(message.chat.id, "❌ Введите ID (цифры)!", reply_markup=back("admin_panel"))
        return
    new_admin_id = int(new_admin_id)
    if new_admin_id in ALL_ADMINS:
        await bot.send_message(message.chat.id, "❌ Уже есть!", reply_markup=back("admin_panel"))
        clear_state(user_id)
        return
    db.save_admin(new_admin_id, "moderator")
    MODERATORS.append(new_admin_id)
    ALL_ADMINS.append(new_admin_id)
    clear_state(user_id)
    await bot.send_message(message.chat.id, f"✅ Добавлен! ID: `{new_admin_id}`",
                           parse_mode="Markdown", reply_markup=back("admin_panel"))


@bot.callback_query_handler(func=lambda c: c.data == "remove_admin")
async def cb_remove_admin(call: types.CallbackQuery) -> None:
    await bot.answer_callback_query(call.id)
    if not is_super_admin(call.from_user.id):
        await edit_or_send(call, "❌ Только главный админ!", back("admin_panel"))
        return
    rows = [[btn(f"🗑️ {mod_id}", f"remove_admin_{mod_id}")] for mod_id in MODERATORS]
    rows.append([btn("🔙 НАЗАД", "admin_panel")])
    await edit_or_send(
        call,
        f"👑 Главный: {ADMINS[0]}\n\n🗑️ Выберите модератора для удаления:",
        kb(rows),
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("remove_admin_"))
async def cb_remove_admin_confirm(call: types.CallbackQuery) -> None:
    await bot.answer_callback_query(call.id)
    if not is_super_admin(call.from_user.id):
        await edit_or_send(call, "❌ Нет доступа!", back("admin_panel"))
        return
    admin_to_remove = int(call.data.split("_")[2])
    if admin_to_remove == ADMINS[0]:
        await edit_or_send(call, "❌ Нельзя удалить главного!", back("admin_panel"))
        return
    if admin_to_remove in MODERATORS:
        db.delete_admin(admin_to_remove)
        MODERATORS.remove(admin_to_remove)
        if admin_to_remove in ALL_ADMINS:
            ALL_ADMINS.remove(admin_to_remove)
        await edit_or_send(call, "✅ Удалён!", back("admin_panel"))
    else:
        await edit_or_send(call, "❌ Не найден!", back("admin_panel"))


@bot.callback_query_handler(func=lambda c: c.data == "list_admins")
async def cb_list_admins(call: types.CallbackQuery) -> None:
    await bot.answer_callback_query(call.id)
    if not is_super_admin(call.from_user.id):
        await edit_or_send(call, "❌ Только главный админ!", back("admin_panel"))
        return
    text = "📊 СПИСОК\n\n👑 Главный: `{}`\n".format(ADMINS[0])
    if MODERATORS:
        text += "\n🛠️ Модераторы:\n" + "\n".join([f"• `{m}`" for m in MODERATORS])
    else:
        text += "\n🛠️ Модераторов нет"
    await edit_or_send(call, text, back("admin_panel"))


# --------------------------- LZT API ТОКЕН --------------------------------- #

@bot.callback_query_handler(func=lambda c: c.data == "change_lzt_token")
async def cb_change_lzt_token(call: types.CallbackQuery) -> None:
    await bot.answer_callback_query(call.id)
    if not is_admin(call.from_user.id):
        await edit_or_send(call, "❌ Нет доступа!", back("admin_panel"))
        return
    current = db.get_lzt_token()
    hidden = current[:15] + "..." + current[-15:] if len(current) > 35 else current
    set_state(call.from_user.id, "change_lzt_token")
    await edit_or_send(
        call,
        f"🔑 СМЕНА LZT API TOKEN\n\nТекущий токен:\n`{hidden}`\n\n💬 Введите новый токен:",
        back("admin_panel"),
    )


async def state_change_lzt_token(message: types.Message, state: Dict[str, Any]) -> None:
    user_id = message.from_user.id
    if not is_admin(user_id):
        await bot.send_message(message.chat.id, "❌ Нет доступа!", reply_markup=back("admin_panel"))
        clear_state(user_id)
        return
    new_token = message.text.strip()
    if len(new_token) < 10:
        await bot.send_message(message.chat.id, "❌ Токен слишком короткий! Минимум 10 символов.",
                               reply_markup=back("admin_panel"))
        return
    db.set_lzt_token(new_token)
    clear_state(user_id)
    hidden = new_token[:15] + "..." + new_token[-15:] if len(new_token) > 35 else new_token
    await bot.send_message(message.chat.id, f"✅ LZT API TOKEN обновлён!\n\nНовый токен:\n`{hidden}`",
                           parse_mode="Markdown", reply_markup=back("admin_panel"))


# --------------------------- ДОБАВЛЕНИЕ НОМЕРА ----------------------------- #

@bot.callback_query_handler(func=lambda c: c.data == "add_phone")
async def cb_add_phone(call: types.CallbackQuery) -> None:
    await bot.answer_callback_query(call.id)
    if not is_admin(call.from_user.id):
        await edit_or_send(call, "❌ Нет доступа!", back("admin_panel"))
        return
    set_state(call.from_user.id, "add_phone_price")
    await bot.send_message(call.message.chat.id, "💰 Введи цену в рублях (можно 0):")


async def state_add_phone_price(message: types.Message, state: Dict[str, Any]) -> None:
    try:
        price = int(message.text.strip())
        if price < 0:
            await bot.send_message(message.chat.id, "❌ Цена не может быть отрицательной!")
            return
    except ValueError:
        await bot.send_message(message.chat.id, "❌ Введи число!")
        return
    set_state(message.from_user.id, "add_phone_number", price_rub=price)
    await bot.send_message(message.chat.id, "📱 Введи номер (+79991234567):")


async def state_add_phone_number(message: types.Message, state: Dict[str, Any]) -> None:
    phone = message.text.strip()
    if phone and not phone.startswith("+"):
        phone = "+" + phone
    if not validate_phone(phone):
        await bot.send_message(message.chat.id, "❌ Неверный формат! Пример: +79991234567")
        return

    set_state(message.from_user.id, "add_phone_code", phone=phone,
              price_rub=state["price_rub"])
    await bot.send_message(message.chat.id, "⏳ Отправляю код...")
    success, msg = await send_code_to_phone(phone, message.from_user.id)
    if success:
        await bot.send_message(message.chat.id, "📲 Введи код из SMS:")
    else:
        set_state(message.from_user.id, "add_phone_number",
                  price_rub=state["price_rub"])
        await bot.send_message(message.chat.id, msg)


async def state_add_phone_code(message: types.Message, state: Dict[str, Any]) -> None:
    code = message.text.strip()
    user_id = message.from_user.id
    if not code.isdigit() or len(code) != 5:
        await bot.send_message(message.chat.id, "❌ Код из 5 цифр!")
        return
    await bot.send_message(message.chat.id, f"🔑 Ввожу код `{code}`...", parse_mode="Markdown")
    success, msg, me, _ = await enter_code_in_telegram(code, user_id)
    if success:
        await _finalize_adding_phone(message.chat.id, user_id, state)
    elif msg == "2FA":
        set_state(user_id, "add_phone_2fa", phone=state["phone"],
                  price_rub=state["price_rub"])
        await bot.send_message(message.chat.id, "🔐 Введи пароль 2FA:")
    else:
        await bot.send_message(message.chat.id, f"❌ {msg}")


async def state_add_phone_2fa(message: types.Message, state: Dict[str, Any]) -> None:
    password = message.text.strip()
    user_id = message.from_user.id
    await bot.send_message(message.chat.id, "🔐 Ввожу 2FA...")
    success, msg, me, _ = await enter_2fa_in_telegram(password, user_id)
    if success:
        await _finalize_adding_phone(message.chat.id, user_id, state, two_fa=password)
    else:
        await bot.send_message(message.chat.id, f"❌ {msg}")


async def _finalize_adding_phone(chat_id: int, user_id: int, state: Dict[str, Any],
                                 two_fa: str = "") -> None:
    phone = state["phone"]
    price_rub = state["price_rub"]

    session_string = ""
    client = None
    async with accounts_lock:
        if user_id in accounts and phone in accounts[user_id]:
            session_string = accounts[user_id][phone].get("session", "")
            client = accounts[user_id][phone].get("client")
    if session_string:
        db.save_phone_session(phone, session_string)

    country_code = get_country_by_phone(phone)
    country = get_country_by_code(country_code)
    country_flag = country["flag"] if country else "🌍"
    country_name = country["name"] if country else "Неизвестно"

    await bot.send_message(
        chat_id,
        f"✅ ВОШЁЛ В АККАУНТ!\n\n📱 {phone}\n"
        f"🌍 {country_flag} {country_name}",
    )

    await add_phone_to_shop_now(
        phone, price_rub, session_string, None, two_fa,
        user_id, notify=False, client=client,
    )

    clear_state(user_id)
    await bot.send_message(
        chat_id,
        f"🏪 НОМЕР ДОБАВЛЕН В МАГАЗИН\n\n"
        f"📱 {phone}\n🌍 {country_flag} {country_name}\n"
        f"💰 {price_rub} ₽\n\n"
        f"🔒 Клиент аккаунта теперь подключён навсегда и не отключается.",
        parse_mode="Markdown",
    )
    await send_main_menu(chat_id, user_id)


# --------------------------- ИЗМЕНЕНИЕ ЦЕНЫ -------------------------------- #

@bot.callback_query_handler(func=lambda c: c.data == "edit_price")
async def cb_edit_price(call: types.CallbackQuery) -> None:
    await bot.answer_callback_query(call.id)
    if not is_admin(call.from_user.id):
        await edit_or_send(call, "❌ Нет доступа!", back("admin_panel"))
        return
    products = db.get_phone_products()
    if not products:
        await edit_or_send(call, "❌ Нет номеров", back("admin_panel"))
        return
    rows = []
    for p in products:
        country = get_country_by_code(get_country_by_phone(p.phone))
        flag = country["flag"] if country else "🌍"
        rows.append([
            btn(f"✏️ {flag} {p.phone} - {p.price_rub}₽",
                f"edit_select_{p.id}")
        ])
    rows.append([btn("🔙 НАЗАД", "admin_panel")])
    await edit_or_send(call, "✏️ ВЫБЕРИ НОМЕР ДЛЯ ИЗМЕНЕНИЯ ЦЕНЫ", kb(rows))


@bot.callback_query_handler(func=lambda c: c.data.startswith("edit_select_"))
async def cb_edit_select_phone(call: types.CallbackQuery) -> None:
    await bot.answer_callback_query(call.id)
    product_id = int(call.data.replace("edit_select_", ""))
    product = db.get_phone_product(product_id)
    if not product:
        await edit_or_send(call, "❌ Номер не найден", back("admin_panel"))
        return
    set_state(call.from_user.id, "edit_price_menu", edit_product_id=product_id,
              edit_phone=product.phone)
    await edit_or_send(
        call,
        f"✏️ ИЗМЕНЕНИЕ ЦЕНЫ\n\n📱 Номер: {product.phone}\n"
        f"💰 Текущая цена: {product.price_rub} ₽",
        kb([
            [btn("💰 ИЗМЕНИТЬ ЦЕНУ", "edit_rub")],
            [btn("🔙 НАЗАД", "admin_panel")],
        ]),
    )


@bot.callback_query_handler(func=lambda c: c.data == "edit_rub")
async def cb_edit_rub(call: types.CallbackQuery) -> None:
    await bot.answer_callback_query(call.id)
    state = get_state(call.from_user.id)
    phone = state.get("edit_phone", "Неизвестно")
    product = db.get_phone_product(state.get("edit_product_id"))
    current = product.price_rub if product else 0
    set_state(call.from_user.id, "edit_rub", edit_product_id=state.get("edit_product_id"),
              edit_phone=phone)
    await edit_or_send(
        call,
        f"💰 ИЗМЕНЕНИЕ ЦЕНЫ В РУБЛЯХ\n\n📱 Номер: {phone}\n"
        f"💰 Текущая цена: {current} ₽\n\n💬 Введи НОВУЮ цену в рублях (можно 0):",
        back("admin_panel"),
    )


async def state_edit_rub(message: types.Message, state: Dict[str, Any]) -> None:
    try:
        new_price = int(message.text.strip())
        if new_price < 0:
            await bot.send_message(message.chat.id, "❌ Цена не может быть отрицательной!")
            return
    except ValueError:
        await bot.send_message(message.chat.id, "❌ Введи число!")
        return
    product_id = state["edit_product_id"]
    phone = state["edit_phone"]
    db.update_price_rub(product_id, new_price)
    clear_state(message.from_user.id)
    await bot.send_message(message.chat.id,
                           f"✅ ЦЕНА В РУБЛЯХ ОБНОВЛЕНА!\n\n📱 Номер: {phone}\n📊 Стало: {new_price} ₽",
                           parse_mode="Markdown", reply_markup=back("admin_panel"))


# --------------------------- УДАЛЕНИЕ НОМЕРА ------------------------------- #

@bot.callback_query_handler(func=lambda c: c.data == "delete_phone")
async def cb_delete_phone(call: types.CallbackQuery) -> None:
    await bot.answer_callback_query(call.id)
    if not is_super_admin(call.from_user.id):
        await edit_or_send(call, "❌ Только главный админ!", back("admin_panel"))
        return
    products = db.get_phone_products()
    if not products:
        await edit_or_send(call, "❌ Нет номеров", back("admin_panel"))
        return
    rows = []
    for p in products:
        country = get_country_by_code(get_country_by_phone(p.phone))
        flag = country["flag"] if country else "🌍"
        rows.append([btn(f"🗑️ {flag} {p.phone}", f"del_phone_{p.id}")])
    rows.append([btn("🔙 НАЗАД", "admin_panel")])
    await edit_or_send(call, "🗑️ ВЫБЕРИ НОМЕР ДЛЯ УДАЛЕНИЯ", kb(rows))


@bot.callback_query_handler(func=lambda c: c.data.startswith("del_phone_"))
async def cb_delete_phone_confirm(call: types.CallbackQuery) -> None:
    await bot.answer_callback_query(call.id)
    if not is_super_admin(call.from_user.id):
        await edit_or_send(call, "❌ Нет доступа!", back("admin_panel"))
        return
    product_id = int(call.data.split("_")[2])
    product = db.get_phone_product(product_id)
    if not product:
        await edit_or_send(call, "❌ Не найден")
        return
    country = get_country_by_code(get_country_by_phone(product.phone))
    flag = country["flag"] if country else "🌍"
    await edit_or_send(
        call,
        f"⚠️ УДАЛИТЬ?\n\n📱 {flag} {product.phone}",
        kb([
            [btn("✅ ДА", f"del_yes_{product_id}")],
            [btn("❌ НЕТ", "delete_phone")],
        ]),
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("del_yes_"))
async def cb_delete_phone_yes(call: types.CallbackQuery) -> None:
    await bot.answer_callback_query(call.id)
    if not is_super_admin(call.from_user.id):
        await edit_or_send(call, "❌ Нет доступа!", back("admin_panel"))
        return
    product_id = int(call.data.split("_")[2])
    db.delete_phone_product(product_id)
    await edit_or_send(call, "✅ УДАЛЕНО", back("admin_panel"))


# ------------------------------- ВОЗМЕЩЕНИЕ -------------------------------- #

@bot.callback_query_handler(func=lambda c: c.data == "compensate")
async def cb_compensate(call: types.CallbackQuery) -> None:
    await bot.answer_callback_query(call.id)
    if not is_admin(call.from_user.id):
        await edit_or_send(call, "❌ Нет доступа!", back("admin_panel"))
        return
    if not db.get_phone_products():
        await edit_or_send(
            call,
            "❌ В МАГАЗИНЕ НЕТ НОМЕРОВ ДЛЯ ВОЗМЕЩЕНИЯ!\n\n"
            "Сначала добавьте номера в магазин.",
            back("admin_panel"),
        )
        return
    set_state(call.from_user.id, "compensate_user")
    await edit_or_send(
        call,
        "🎁 ВОЗМЕСТИТЬ АККАУНТ\n\n"
        "📝 Введите числовой ID пользователя, которому нужно возместить аккаунт:\n\n"
        "💡 Пример: `123456789`",
        back("admin_panel"),
    )


async def state_compensate_user(message: types.Message, state: Dict[str, Any]) -> None:
    admin_id = message.from_user.id
    if not is_admin(admin_id):
        await bot.send_message(message.chat.id, "❌ Нет доступа!", reply_markup=back("admin_panel"))
        clear_state(admin_id)
        return

    target_user_id_str = message.text.strip()
    if not target_user_id_str.isdigit():
        await bot.send_message(message.chat.id,
                               "❌ Неверный формат! Введите числовой ID (только цифры).",
                               reply_markup=back("admin_panel"))
        return
    target_user_id = int(target_user_id_str)

    try:
        await bot.get_chat(target_user_id)
    except Exception as e:
        logger.error(f"❌ Ошибка получения пользователя с ID {target_user_id}: {e}")
        await bot.send_message(
            message.chat.id,
            f"❌ ПОЛЬЗОВАТЕЛЬ С ID {target_user_id} НЕ НАЙДЕН!\n\nПроверьте правильность ID.",
            parse_mode="Markdown",
            reply_markup=back("admin_panel"),
        )
        return

    products = db.get_phone_products()
    if not products:
        await bot.send_message(message.chat.id, "❌ В МАГАЗИНЕ НЕТ НОМЕРОВ ДЛЯ ВОЗМЕЩЕНИЯ!",
                               parse_mode="Markdown", reply_markup=back("admin_panel"))
        clear_state(admin_id)
        return

    set_state(admin_id, "compensate_select", compensate_target_user_id=target_user_id)
    rows = []
    for p in products:
        country = get_country_by_code(get_country_by_phone(p.phone))
        flag = country["flag"] if country else "🌍"
        rows.append([
            btn(f"{flag} {p.phone} ({p.price_rub}₽)", f"comp_select_{p.id}")
        ])
    rows.append([btn("🔙 ОТМЕНА", "admin_panel")])
    await bot.send_message(
        message.chat.id,
        f"🎁 ВЫБЕРИТЕ НОМЕР ДЛЯ ВОЗМЕЩЕНИЯ\n\n"
        f"Пользователь: `{target_user_id}`\n\nДоступно номеров: {len(products)}",
        parse_mode="Markdown",
        reply_markup=kb(rows),
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("comp_select_"))
async def cb_compensate_select(call: types.CallbackQuery) -> None:
    await bot.answer_callback_query(call.id)
    admin_id = call.from_user.id
    if not is_admin(admin_id):
        await edit_or_send(call, "❌ Нет доступа!", back("admin_panel"))
        return

    product_id = int(call.data.replace("comp_select_", ""))
    state = get_state(admin_id)
    target_user_id = state.get("compensate_target_user_id")
    if not target_user_id:
        await edit_or_send(call, "❌ Ошибка: ID пользователя не найден. Попробуйте сначала.",
                           back("admin_panel"))
        return

    product = db.get_phone_product(product_id)
    if not product:
        await edit_or_send(call, "❌ Этот номер уже был выдан или удалён.",
                           back("admin_panel"))
        return

    phone = product.phone
    db.delete_phone_product(product_id)
    country_code = get_country_by_phone(phone)
    db.add_purchase(target_user_id, phone, product.price_rub,
                    product.session, product.lzt_item_id,
                    product.two_fa, country_code)

    awaiting_phone_confirmation[target_user_id] = {
        "phone": phone,
        "product_id": product_id,
        "session": product.session,
        "lzt_item_id": product.lzt_item_id,
        "two_fa": product.two_fa,
    }

    country = get_country_by_code(country_code) if country_code else None
    flag = country["flag"] if country else "🌍"
    name = country["name"] if country else "Неизвестно"
    code = country["phone_code"] if country else ""

    try:
        await bot.send_message(
            target_user_id,
            f"🎁 ВАМ ВЫДАН КОМПЕНСАЦИОННЫЙ АККАУНТ!\n\n"
            f"🌍 Страна: {flag} {name} ({code})\n"
            f"📱 ВАШ НОМЕР: `{phone}`\n"
            f"💰 {product.price_rub} ₽\n\n"
            f"---\n"
            f"⚠️ ПОСЛЕ ВХОДА В АККАУНТ ОБЯЗАТЕЛЬНО:\n"
            f"1️⃣ Смените номер телефона на свой\n"
            f"2️⃣ Поставьте двухфакторную аутентификацию (2FA)\n"
            f"3️⃣ Установите облачный пароль\n"
            f"4️⃣ Привяжите почту для восстановления\n\n"
            f"🔑 Нажмите кнопку, чтобы получить код для входа:",
            parse_mode="Markdown",
            reply_markup=kb([
                [btn("🔑 ПОЛУЧИТЬ КОД", "get_code")],
                [btn("🏠 ГЛАВНОЕ МЕНЮ", "start")],
            ]),
        )
        await edit_or_send(
            call,
            f"✅ АККАУНТ ВОЗМЕЩЁН!\n\n"
            f"👤 Пользователь: `{target_user_id}`\n"
            f"📱 Номер: `{phone}`\n🌍 {flag} {name}\n\n"
            f"🎁 Номер отправлен пользователю с кнопкой «ПОЛУЧИТЬ КОД».",
            back("admin_panel"),
        )
    except Exception as e:
        logger.error(f"❌ Ошибка отправки возмещения: {e}")
        await edit_or_send(
            call,
            f"❌ НЕ УДАЛОСЬ ОТПРАВИТЬ АККАУНТ\n\n"
            f"Пользователь `{target_user_id}` не найден или бот заблокирован.\n\n"
            f"Номер `{phone}` удалён из магазина.",
            back("admin_panel"),
        )

    clear_state(admin_id)


# --------------------------------------------------------------------------- #
#                         LZT MARKET (покупка номеров)                         #
# --------------------------------------------------------------------------- #

LZT_MARKET_API = "https://api.lzt.market"
LZT_PROXY = None

try:
    from config import LZT_PROXY as _LZT_PROXY
    LZT_PROXY = _LZT_PROXY
except Exception:
    LZT_PROXY = None


class _LZTMarket:
    """Минимальный клиент LZT Market (обёртка над requests)."""

    class _Settings:
        proxy = None

    def __init__(self, token: str):
        self.token = token
        self.settings = _LZTMarket._Settings()

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}", "Accept": "application/json"}

    def _session(self):
        s = requests.Session()
        if self.settings.proxy:
            s.proxies = {"http": self.settings.proxy, "https": self.settings.proxy}
        return s

    def buy_account(self, item_id: int, price: int = None):
        with self._session() as s:
            resp = s.post(
                f"{LZT_MARKET_API}/{item_id}/buy",
                headers=self._headers(),
                json={},
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()

    def get_telegram_code(self, item_id: int):
        with self._session() as s:
            resp = s.post(
                f"{LZT_MARKET_API}/{item_id}/telegram-code",
                headers=self._headers(),
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()


def _lzt_market_cls(token: str = None) -> "_LZTMarket":
    return _LZTMarket(token or db.get_lzt_token())


def _lzt_fetch_verification_code(market: "_LZTMarket", item_id: int):
    """Синхронно запрашивает код подтверждения у LZT Market."""
    try:
        data = market.get_telegram_code(item_id)
        if not data:
            return None
        code = (
            data.get("code")
            or data.get("telegram_code")
            or (data.get("item") or {}).get("telegram_code")
        )
        if code:
            return str(code)
        return None
    except Exception as e:
        logger.error(f"❌ LZT get_telegram_code error: {e}")
        return None


@bot.callback_query_handler(func=lambda c: c.data == "lzt_buy_menu")
async def cb_lzt_buy_menu(call: types.CallbackQuery) -> None:
    await bot.answer_callback_query(call.id)
    if not is_admin(call.from_user.id):
        await edit_or_send(call, "❌ Нет доступа!", back("admin_panel"))
        return
    set_state(call.from_user.id, "lzt_buy_id")
    await edit_or_send(
        call,
        "🛒 ПОКУПКА НОМЕРА НА LZT MARKET\n\n"
        "Введите ID лота (item_id), который нужно купить:",
        back("admin_panel"),
    )


async def state_lzt_buy_id(message: types.Message, state: Dict[str, Any]) -> None:
    admin_id = message.from_user.id
    if not is_admin(admin_id):
        await bot.send_message(message.chat.id, "❌ Нет доступа!", reply_markup=back("admin_panel"))
        clear_state(admin_id)
        return
    item_id_str = message.text.strip()
    if not item_id_str.isdigit():
        await bot.send_message(message.chat.id, "❌ ID должен быть числом!",
                               reply_markup=back("admin_panel"))
        return
    item_id = int(item_id_str)
    set_state(admin_id, "lzt_buy_price", lzt_item_id=item_id)
    await bot.send_message(message.chat.id, "💰 Введи цену продажи в рублях (можно 0):")


async def state_lzt_buy_price(message: types.Message, state: Dict[str, Any]) -> None:
    admin_id = message.from_user.id
    try:
        price_rub = int(message.text.strip())
        if price_rub < 0:
            raise ValueError
    except ValueError:
        await bot.send_message(message.chat.id, "❌ Введи число (можно 0)!")
        return
    item_id = state["lzt_item_id"]
    clear_state(admin_id)

    await bot.send_message(message.chat.id, f"⏳ Покупаю лот #{item_id} на LZT Market...")
    loop = asyncio.get_running_loop()
    try:
        token = db.get_lzt_token()
        market = _lzt_market_cls(token=token)
        if LZT_PROXY:
            market.settings.proxy = LZT_PROXY
        result = await loop.run_in_executor(
            None, lambda: market.buy_account(item_id)
        )
    except Exception as e:
        logger.error(f"❌ Ошибка покупки на LZT: {e}")
        await bot.send_message(message.chat.id, f"❌ Ошибка покупки: {str(e)[:200]}",
                               reply_markup=back("admin_panel"))
        return

    item = (result or {}).get("item", {}) if isinstance(result, dict) else {}
    phone = (
        item.get("telegram_phone")
        or item.get("phone")
        or item.get("login")
        or ""
    )
    if not phone:
        await bot.send_message(
            message.chat.id,
            f"✅ Лот куплен, но номер не распознан в ответе API.\n\n"
            f"Ответ:\n```\n{json.dumps(result, ensure_ascii=False)[:500]}\n```",
            parse_mode="Markdown",
            reply_markup=back("admin_panel"),
        )
        return

    phone = normalize_phone(phone)
    await add_phone_to_shop_now(
        phone, price_rub, "", item_id, "", admin_id, notify=True
    )
    await bot.send_message(
        message.chat.id,
        f"✅ ЛОТ КУПЛЕН И ДОБАВЛЕН В МАГАЗИН!\n\n📱 `{phone}`",
        parse_mode="Markdown",
        reply_markup=back("admin_panel"),
    )


# --------------------------------------------------------------------------- #
#                                ОПЛАТА                                        #
# --------------------------------------------------------------------------- #

@bot.callback_query_handler(func=lambda c: c.data.startswith("pay_rub_"))
async def cb_pay_rub(call: types.CallbackQuery) -> None:
    await bot.answer_callback_query(call.id)
    product_id = int(call.data.replace("pay_rub_", ""))
    product = db.get_phone_product(product_id)
    if not product:
        await edit_or_send(call, "❌ Номер уже продан или удалён", back("shop"))
        return
    if not YOOMONEY_WALLET:
        await edit_or_send(call, "❌ Оплата рублями временно недоступна", back("shop"))
        return

    label = f"{call.from_user.id}_{product_id}_{int(time.time())}"
    pending_rub[label] = {
        "user_id": call.from_user.id,
        "product_id": product_id,
        "amount": product.price_rub,
        "chat_id": call.message.chat.id,
    }
    pay_url = (
        f"https://yoomoney.ru/quickpay/confirm.xml?"
        f"receiver={YOOMONEY_WALLET}&quickpay-form=button"
        f"&targets=Аккаунт+{hide_phone(product.phone)}&paymentType=AC"
        f"&sum={product.price_rub}&label={label}"
    )
    await edit_or_send(
        call,
        f"💳 ОПЛАТА {product.price_rub} ₽\n\n"
        f"📱 Номер: `{hide_phone(product.phone)}`\n"
        f"🔖 Метка платежа: `{label}`\n\n"
        f"1️⃣ Нажмите «Оплатить» и переведите {product.price_rub} ₽\n"
        f"2️⃣ В комментарии оставьте метку: `{label}`\n"
        f"3️⃣ Вернитесь и нажмите «Я ОПЛАТИЛ»\n\n"
        f"⚠️ Не меняйте сумму и метку!",
        kb([
            [url_btn("💳 ОПЛАТИТЬ", pay_url)],
            [btn("✅ Я ОПЛАТИЛ", "rub_paid")],
            [btn("🔙 НАЗАД", "shop")],
        ]),
    )


@bot.callback_query_handler(func=lambda c: c.data == "rub_paid")
async def cb_rub_paid(call: types.CallbackQuery) -> None:
    await bot.answer_callback_query(call.id)
    user_id = call.from_user.id
    pack = None
    label = None
    for lbl, data in pending_rub.items():
        if data["user_id"] == user_id:
            pack = data
            label = lbl
            break
    if not pack:
        await edit_or_send(call, "❌ Нет активных платежей. Выберите номер заново.",
                           back("shop"))
        return

    await edit_or_send(call, "⏳ Проверяю оплату...")
    if await check_yoomoney_payment_async(label):
        pending_rub.pop(label, None)
        await _finalize_purchase(call.message.chat.id, user_id, pack["product_id"],
                                 method="rub", callback=call)
    else:
        await edit_or_send(
            call,
            "❌ ПЛАТЁЖ НЕ НАЙДЕН\n\n"
            "Если вы только что оплатили — подождите 1–2 минуты\n"
            "и нажмите «ПРОВЕРИТЬ» снова.",
            kb([
                [btn("🔄 ПРОВЕРИТЬ", "rub_paid")],
                [btn("🔙 НАЗАД", "shop")],
            ]),
        )


async def _finalize_purchase(chat_id: int, buyer_id: int, product_id: int,
                             method: str = "rub", callback=None) -> None:
    """Списывает товар со склада, записывает покупку и выдаёт номер."""
    product = db.get_phone_product(product_id)
    if not product:
        msg = "❌ Номер уже продан или удалён."
        if callback:
            await edit_or_send(callback, msg, back("shop"))
        else:
            await bot.send_message(chat_id, msg)
        return

    phone = product.phone
    country_code = get_country_by_phone(phone)
    db.delete_phone_product(product_id)
    db.add_purchase(
        buyer_id, phone, product.price_rub,
        product.session, product.lzt_item_id,
        product.two_fa, country_code,
    )

    awaiting_phone_confirmation[buyer_id] = {
        "phone": phone,
        "session": product.session,
        "lzt_item_id": product.lzt_item_id,
        "two_fa": product.two_fa,
    }

    text = generate_product_message(phone, product.price_rub,
                                    product.two_fa)
    markup = kb([
        [btn("🔑 ПОЛУЧИТЬ КОД", f"buyer_get_code_{product_id}")],
        [btn("🏠 ГЛАВНОЕ МЕНЮ", "start")],
    ])
    if callback:
        await edit_or_send(callback, text, markup)
    else:
        await bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=markup)


@bot.callback_query_handler(func=lambda c: c.data.startswith("buyer_get_code_"))
async def cb_buyer_get_code(call: types.CallbackQuery) -> None:
    await bot.answer_callback_query(call.id)
    user_id = call.from_user.id
    info = awaiting_phone_confirmation.get(user_id)
    if not info:
        purchases = db.get_user_purchases(user_id)
        if purchases:
            p = purchases[0]
            await _deliver_code(call, p.phone, p.session, p.lzt_item_id, p.id)
        else:
            await edit_or_send(call, "❌ Нет данных о покупке", back("my_purchases"))
        return
    await _deliver_code(call, info["phone"], info.get("session", ""),
                        info.get("lzt_item_id"), info.get("product_id", 0))


@bot.callback_query_handler(func=lambda c: c.data == "get_code")
async def cb_get_code(call: types.CallbackQuery) -> None:
    """Получение кода для возмещённого аккаунта."""
    await bot.answer_callback_query(call.id)
    user_id = call.from_user.id
    info = awaiting_phone_confirmation.get(user_id)
    if not info:
        await edit_or_send(call, "❌ Нет данных о номере. Обратитесь в поддержку.",
                           back("my_purchases"))
        return
    await _deliver_code(call, info["phone"], info.get("session", ""),
                        info.get("lzt_item_id"), info.get("product_id", 0))


# --------------------------------------------------------------------------- #
#                       ТЕКСТОВЫЙ РОУТЕР (СОСТОЯНИЯ)                           #
# --------------------------------------------------------------------------- #

STATE_HANDLERS = {
    "awaiting_offer": receive_offer,
    "add_admin": state_add_admin,
    "change_lzt_token": state_change_lzt_token,
    "add_phone_price": state_add_phone_price,
    "add_phone_number": state_add_phone_number,
    "add_phone_code": state_add_phone_code,
    "add_phone_2fa": state_add_phone_2fa,
    "edit_rub": state_edit_rub,
    "compensate_user": state_compensate_user,
    "lzt_buy_id": state_lzt_buy_id,
    "lzt_buy_price": state_lzt_buy_price,
}


@bot.message_handler(func=lambda message: True, content_types=["text"])
async def global_text_router(message: types.Message) -> None:
    user_id = message.from_user.id
    if message.text and message.text.startswith("/"):
        return

    state = get_state(user_id)
    handler = STATE_HANDLERS.get(state.get("state"))
    if handler:
        try:
            await handler(message, state)
        except Exception as e:
            logger.error(f"❌ Ошибка обработки состояния: {e}")
            clear_state(user_id)
            await bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)[:150]}")
        return

    await send_main_menu(message.chat.id, user_id)


@bot.message_handler(commands=["menu"])
async def cmd_menu(message: types.Message) -> None:
    await send_main_menu(message.chat.id, message.from_user.id)


@bot.message_handler(commands=["admin"])
async def cmd_admin(message: types.Message) -> None:
    if not is_admin(message.from_user.id):
        await bot.send_message(message.chat.id, "❌ Нет доступа!")
        return
    role = "👑 ГЛАВНЫЙ АДМИН" if is_super_admin(message.from_user.id) else "🛠️ МОДЕРАТОР"
    await bot.send_message(message.chat.id, f"👥 АДМИН-ПАНЕЛЬ\n\nВаша роль: {role}",
                           parse_mode="Markdown", reply_markup=back("admin_panel"))


# --------------------------------------------------------------------------- #
#                    FLASK-ВЕБХУК (Яндекс.Деньги / ping)                       #
# --------------------------------------------------------------------------- #

app = Flask(__name__)


@app.route("/", methods=["GET"])
def index():
    return "OK", 200


@app.route("/yoomoney", methods=["POST"])
def yoomoney_webhook():
    """Уведомление от ЮMoney."""
    try:
        label = request.form.get("label")
        amount = request.form.get("amount") or request.form.get("withdraw_amount")
        if label and label in pending_rub:
            logger.info(f"💰 YooMoney webhook: label={label}, amount={amount}")
        return "OK", 200
    except Exception as e:
        logger.error(f"❌ YooMoney webhook error: {e}")
        return "ERR", 200


def run_flask():
    port = 8080
    try:
        from config import WEBHOOK_PORT
        port = WEBHOOK_PORT
    except Exception:
        pass
    logger.info(f"🌐 Flask-вебхук слушает на порту {port}")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


# --------------------------------------------------------------------------- #
#                                  ЗАПУСК                                      #
# --------------------------------------------------------------------------- #

async def on_startup() -> None:
    db.init_db()
    db.init_lzt_token()
    load_admins()
    logger.info("✅ Бот запущен и готов к работе (telebot)")


async def main() -> None:
    await on_startup()
    threading.Thread(target=run_flask, daemon=True).start()
    # Явно указываем типы обновлений, иначе Telegram использует ранее
    # сохранённый фильтр (например только "message") и не присылает
    # callback_query — из-за этого не работали инлайн-кнопки.
    await bot.infinity_polling(
        timeout=30,
        request_timeout=30,
        allowed_updates=telebot.util.update_types,
        logger_level=0,
    )


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Бот остановлен")
    finally:
        try:
            db.Session.remove()
            db.engine.dispose()
        except Exception:
            pass