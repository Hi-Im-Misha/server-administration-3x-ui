import telebot
import json
from datetime import datetime, timedelta
import threading
import time

TOKEN = "TOKEN"
CHAT_ID = 'CHAT_ID'
bot = telebot.TeleBot(TOKEN)

DUMP_FILE = "3xui_dump.json"

def main_kb():
    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Все клиенты", "Подписки")
    return kb


@bot.message_handler(commands=["start"])
def start(msg):
    bot.send_message(
        msg.chat.id,
        "Бот запущен. Я буду присылать уведомления за 1 день до окончания подписки.",
        reply_markup=main_kb()
    )


@bot.message_handler(func=lambda m: m.text == "Все клиенты")
def send_all(msg):
    with open(DUMP_FILE, "rb") as f:
        bot.send_document(msg.chat.id, f)


@bot.message_handler(func=lambda m: m.text == "Подписки")
def subscriptions(msg):
    with open(DUMP_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    lines = []

    for inbound in data:
        if inbound["expiry"] != "∞":
            lines.append(
                f"Inbound\n"
                f"{inbound['server']} | {inbound['remark']}\n"
                f"Истекает: {inbound['expiry']}\n"
            )

        for c in inbound.get("clients", []):
            if c["expiry"] != "∞":
                lines.append(
                    f"Клиент {c['email']}\n"
                    f"{inbound['server']} | {inbound['remark']}\n"
                    f"Истекает: {c['expiry']}\n"
                )

    if not lines:
        bot.send_message(msg.chat.id, "Нет подписок с датой окончания")
        return

    text = "\n".join(lines)
    for i in range(0, len(text), 4000):
        bot.send_message(msg.chat.id, text[i:i+4000])


def check_expiring():
    if CHAT_ID is None:
        print("CHAT_ID is None")
        return

    with open(DUMP_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    tomorrow = (datetime.now() + timedelta(days=1)).date()

    for inbound in data:
        if inbound["expiry"] != "∞":
            exp = datetime.strptime(inbound["expiry"], "%Y-%m-%d %H:%M")
            if exp.date() == tomorrow:
                bot.send_message(
                    CHAT_ID,
                    f"Истекает подписка завтра\n"
                    f"{inbound['remark']} ({inbound['server']})\n"
                    f"{inbound['expiry']}"
                )

        for c in inbound.get("clients", []):
            if c["expiry"] != "∞":
                exp = datetime.strptime(c["expiry"], "%Y-%m-%d %H:%M")
                if exp.date() == tomorrow:
                    bot.send_message(
                        CHAT_ID,
                        f"Истекает подписка завтра\n"
                        f"{c['email']}\n"
                        f"{inbound['remark']} ({inbound['server']})\n"
                        f"{c['expiry']}"
                    )


def scheduler():
    while True:
        now = datetime.now()
        target = now.replace(hour=18, minute=00, second=0, microsecond=0)
        if now >= target:
            target += timedelta(days=1)

        time.sleep((target - now).total_seconds())
        check_expiring()


threading.Thread(target=scheduler, daemon=True).start()

print("Bot started")
bot.infinity_polling()
