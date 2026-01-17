import json
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List

from telegram import Update, Message
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = "122345"  # тот же, что в rok_panel.py
CHANNEL_ID = -12345678  # id канала

ACCOUNTS_FILE = "accounts.json"  # файл для хранения ников
TIMERS_FILE = "timers.json"      # файл для хранения таймеров

# ---------------- НИКИ ----------------

def load_accounts() -> Dict[str, str]:
    if not os.path.exists(ACCOUNTS_FILE):
        return {}
    try:
        with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_accounts(data: Dict[str, str]):
    with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


accounts = load_accounts()  # {user_id: account_name}

# ---------------- ТАЙМЕРЫ ----------------

def load_timers() -> List[Dict[str, Any]]:
    if not os.path.exists(TIMERS_FILE):
        return []
    try:
        with open(TIMERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_timers(timers: List[Dict[str, Any]]):
    with open(TIMERS_FILE, "w", encoding="utf-8") as f:
        json.dump(timers, f, ensure_ascii=False, indent=2)

def save_timer(account: str, troop: int, end_iso: str, chat_id: int):
    global timers_data
    timers_data.append({
        "account": account,
        "troop": troop,
        "end_iso": end_iso,
        "chat_id": chat_id,
    })
    save_timers(timers_data)

timers_data: List[Dict[str, Any]] = load_timers()

# формат элемента:
# {
#   "account": "НАЗВАНИЕ",
#   "troop": 5,
#   "end_iso": "2026-01-16T13:46:11",
#   "chat_id": 123456
# }

# ---------------- КОМАНДЫ ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    current = accounts.get(user_id, "(не задан)")
    await update.message.reply_text(
        f"Привет, {user.first_name}!\n"
        f"Текущий аккаунт: {current}\n"
        f"Задай его командой: /setname ИМЯ_АККА\n"
        f"Скрины и таймеры прилетают через панель."
    )


async def setname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)

    if not context.args:
        await update.message.reply_text(
            "Формат: /setname ИМЯ_АККА\nПример: /setname БАРДЕЛЬ"
        )
        return

    acc_name = " ".join(context.args).strip()
    if not acc_name:
        await update.message.reply_text("Имя аккаунта не может быть пустым.")
        return

    accounts[user_id] = acc_name
    save_accounts(accounts)
    await update.message.reply_text(f"Текущий аккаунт сохранён: {acc_name}")


async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=CHANNEL_ID, text="Тест из бота в канал.")
    await update.message.reply_text("Тестовое сообщение отправлено в канал.")


# ---------------- ОБРАБОТКА МЕТКИ #TIMER# ----------------

def parse_timer_line(line: str):
    """
    Разбирает строку вида:
    #TIMER# НАЗВАНИЕ|5|2026-01-16T13:46:11
    """
    if not line.startswith("#TIMER#"):
        return None

    try:
        payload = line[len("#TIMER#"):].strip()
        account, troop_str, end_iso = payload.split("|")
        troop = int(troop_str)
        # проверим, что дата парсится
        datetime.fromisoformat(end_iso)
    except Exception:
        return None

    return {
        "account": account,
        "troop": troop,
        "end_iso": end_iso,
    }


async def any_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg:
        return

    chat = msg.chat
    text = msg.text or msg.caption or ""

    print("any_message from chat:", chat.id, "type:", chat.type)
    print("TEXT:", repr(text))

    # реагируем только на личку и только на #TIMER#
    if chat.type == "private" and text.startswith("#TIMER#"):
        try:
            _, payload = text.split("#TIMER# ", 1)
            account, troop, ts = payload.split("|")
        except ValueError:
            return

        save_timer(account, int(troop), ts, chat.id)
        await msg.reply_text("Таймер добавлен.")
        return

# ---------------- ФОНОВЫЙ ЧЕКЕР ТАЙМЕРОВ ----------------

async def timers_checker(context: ContextTypes.DEFAULT_TYPE):
    """
    Каждую минуту проверяет, какие таймеры истекли, и шлёт уведомление.
    """
    global timers_data

    if not timers_data:
        return

    now = datetime.now()

    remaining: List[Dict[str, Any]] = []
    triggered: List[Dict[str, Any]] = []

    for item in timers_data:
        try:
            end_dt = datetime.fromisoformat(item["end_iso"])
        except Exception:
            # битый формат – пропускаем
            continue

        if end_dt <= now:
            triggered.append(item)
        else:
            remaining.append(item)

    timers_data = remaining
    if triggered:
        save_timers(timers_data)

    # шлём уведомления
    for item in triggered:
        account = item["account"]
        troop = item["troop"]
        # chat_id = item["chat_id"]
        chat_id = CHANNEL_ID  # <- вот так
        text = f"{account} — отряд {troop} вернулся."
        await context.bot.send_message(chat_id=chat_id, text=text)

# ---------------- MAIN ----------------

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setname", setname))
    app.add_handler(CommandHandler("test", test_command))

    # любые текстовые сообщения в личке
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, any_message))

    job_queue = app.job_queue
    job_queue.run_repeating(timers_checker, interval=60, first=10)

    app.run_polling()


if __name__ == "__main__":
    main()
