import os
import asyncio
import logging
from datetime import datetime
import pytz
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
TZ = pytz.timezone("Europe/Moscow")

SCHEDULE = {
    "monday": {
        "emoji": "🎬",
        "type": "МОНТАЖ",
        "blocks": [
            ("07:50", "🏋️ Тренировка — верх + кор\nЖим лёжа, тяга в наклоне, отжимания, планка\n30–40 мин с гантелями + Nike Training"),
            ("10:55", "🎬 Монтаж — пик концентрации\nТолько монтаж до 13:00. Никаких переключений."),
            ("13:00", "🍽️ Обед + прогулка\nБелок + углеводы + овощи. Прогулка 30 мин."),
            ("14:30", "🎬 Монтаж — продолжение\nДо 16:30. Держи темп."),
            ("16:00", "🍫 Перекус\nОрехи / шоколад 85% / финики. Не Twix."),
            ("17:30", "📚 Знания\nПодкаст / статья / видео. Реши заранее — не Instagram."),
            ("22:45", "😴 Телефон откладываем\nСпать до 23:00."),
        ]
    },
    "tuesday": {
        "emoji": "✍️",
        "type": "СЦЕНАРИЙ",
        "blocks": [
            ("07:50", "🏋️ Тренировка — низ + кор\nПриседы, выпады, румынская тяга, боковая планка\n30–40 мин с гантелями + Nike Training"),
            ("10:55", "✍️ Сценарий — пик концентрации\nТолько сценарий до 13:00. Никаких переключений."),
            ("13:00", "🍽️ Обед + прогулка\nБелок + углеводы + овощи. Прогулка 30 мин."),
            ("14:30", "💼 Бизнес-блок\nUpwork, клиенты, гипотезы — 1 час. Это деньги."),
            ("16:00", "🍫 Перекус\nОрехи / шоколад 85% / финики. Не Twix."),
            ("17:30", "📚 Знания\nПодкаст / статья / видео. Реши заранее — не Instagram."),
            ("22:45", "😴 Телефон откладываем\nСпать до 23:00."),
        ]
    },
    "wednesday": {
        "emoji": "👨‍👧",
        "type": "ВЫХОДНОЙ",
        "blocks": [
            ("09:00", "☀️ Выходной — день с сыном\nНикакой работы. Восстановление — это тоже продуктивность."),
        ]
    },
    "thursday": {
        "emoji": "🎬",
        "type": "МОНТАЖ",
        "blocks": [
            ("07:50", "🏋️ Тренировка — HIIT + полное тело\nБерпи, трастеры с гантелями, отжимания — 3 круга\n30–40 мин + Nike Training"),
            ("10:55", "🎬 Монтаж — пик концентрации\nТолько монтаж до 13:00. Никаких переключений."),
            ("13:00", "🍽️ Обед + прогулка\nБелок + углеводы + овощи. Прогулка 30 мин."),
            ("14:30", "🎬 Монтаж — продолжение\nДо 16:30. Держи темп."),
            ("16:00", "🍫 Перекус\nОрехи / шоколад 85% / финики. Не Twix."),
            ("17:30", "📚 Знания\nПодкаст / статья / видео. Реши заранее — не Instagram."),
            ("22:45", "😴 Телефон откладываем\nСпать до 23:00."),
        ]
    },
    "friday": {
        "emoji": "✍️",
        "type": "СЦЕНАРИЙ",
        "blocks": [
            ("07:50", "🏋️ Восстановление — растяжка\nНike Training: лёгкая йога / растяжка\n15–20 мин. Можно с сыном рядом."),
            ("10:55", "✍️ Сценарий — пик концентрации\nТолько сценарий до 13:00. Никаких переключений."),
            ("13:00", "🍽️ Обед + прогулка\nБелок + углеводы + овощи. Прогулка 30 мин."),
            ("14:30", "💼 Бизнес-блок\nUpwork, клиенты, гипотезы — 1 час. Это деньги."),
            ("16:00", "🍫 Перекус\nОрехи / шоколад 85% / финики. Не Twix."),
            ("17:30", "📚 Знания\nПодкаст / статья / видео. Реши заранее — не Instagram."),
            ("22:45", "😴 Телефон откладываем\nСпать до 23:00."),
        ]
    },
    "saturday": {
        "emoji": "👨‍👩‍👦",
        "type": "СЕМЬЯ",
        "blocks": [
            ("09:00", "☀️ Суббота — семья\nПолный выходной. Один маленький десерт вечером — ритуал, не срыв."),
        ]
    },
    "sunday": {
        "emoji": "📋",
        "type": "ШТАБ-ДЕНЬ",
        "blocks": [
            ("09:00", "☀️ Воскресенье — восстановление\nСемья, отдых, прогулки."),
            ("20:00", "📋 Штаб-час — планирование недели\n1. Просмотреть все проекты\n2. Выбрать один главный на каждый день\n3. Поставить дедлайны на 2 дня раньше реальных\n4. Зарядиться на неделю\n\nЭтот час стоит целого дня."),
        ]
    },
}

DAYS_RU = {
    "monday": "Понедельник",
    "tuesday": "Вторник",
    "wednesday": "Среда",
    "thursday": "Четверг",
    "friday": "Пятница",
    "saturday": "Суббота",
    "sunday": "Воскресенье",
}

WEEKDAY_MAP = {
    0: "monday",
    1: "tuesday",
    2: "wednesday",
    3: "thursday",
    4: "friday",
    5: "saturday",
    6: "sunday",
}


def get_today_key():
    now = datetime.now(TZ)
    return WEEKDAY_MAP[now.weekday()]


def format_day(day_key):
    day = SCHEDULE[day_key]
    lines = [f"{day['emoji']} *{DAYS_RU[day_key].upper()} — {day['type']}*\n"]
    for time, text in day["blocks"]:
        first_line = text.split("\n")[0]
        lines.append(f"`{time}` {first_line}")
    return "\n".join(lines)


async def send_reminder(bot, text):
    try:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=text,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error sending reminder: {e}")


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        f"👋 Привет, Рамиль!\n\n"
        f"Твой ID чата: `{chat_id}`\n\n"
        f"Команды:\n"
        f"/today — что сегодня\n"
        f"/week — вся неделя\n"
        f"/now — что сейчас по плану\n"
        f"/monday, /tuesday... — конкретный день",
        parse_mode="Markdown"
    )


async def cmd_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    day_key = get_today_key()
    await update.message.reply_text(format_day(day_key), parse_mode="Markdown")


async def cmd_week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = ["📅 *НЕДЕЛЯ*\n"]
    for day_key in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
        day = SCHEDULE[day_key]
        lines.append(f"{day['emoji']} *{DAYS_RU[day_key]}* — {day['type']}")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    day_key = get_today_key()
    now = datetime.now(TZ)
    current_time = now.strftime("%H:%M")
    day = SCHEDULE[day_key]
    current_block = None
    for time, text in day["blocks"]:
        if time <= current_time:
            current_block = (time, text)
    if current_block:
        time, text = current_block
        await update.message.reply_text(
            f"🕐 Сейчас ({current_time}):\n\n`{time}` {text}",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"🌅 Ещё до начала дня. Первый блок:\n\n"
            f"`{day['blocks'][0][0]}` {day['blocks'][0][1]}",
            parse_mode="Markdown"
        )


def make_day_handler(day_key):
    async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(format_day(day_key), parse_mode="Markdown")
    return handler


def setup_scheduler(application):
    scheduler = AsyncIOScheduler(timezone=TZ)
    bot = application.bot

    day_numbers = {
        "monday": 0, "tuesday": 1, "wednesday": 2,
        "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6,
    }

    for day_key, day_data in SCHEDULE.items():
        dow = day_numbers[day_key]
        for time_str, text in day_data["blocks"]:
            hour, minute = map(int, time_str.split(":"))
            msg = f"{day_data['emoji']} {text}"

            scheduler.add_job(
                send_reminder,
                trigger="cron",
                day_of_week=dow,
                hour=hour,
                minute=minute,
                args=[bot, msg],
                misfire_grace_time=60,
            )

    scheduler.start()
    logger.info("Scheduler started")


def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN environment variable not set")
    if not CHAT_ID:
        raise ValueError("CHAT_ID environment variable not set")

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("today", cmd_today))
    application.add_handler(CommandHandler("week", cmd_week))
    application.add_handler(CommandHandler("now", cmd_now))

    for day_key in SCHEDULE.keys():
        application.add_handler(CommandHandler(day_key, make_day_handler(day_key)))

    setup_scheduler(application)

    logger.info("Bot started")
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
