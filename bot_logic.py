from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InputFile
from telegram.ext import (
    ContextTypes, ConversationHandler, MessageHandler, CommandHandler, filters
)
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from datetime import datetime
import os
import sys

# === Стейты ===
NUM, DATE, FROM, TO, CAR, PLATE, ITEM_NAME, ITEM_UNIT, ITEM_QTY, ASK_MORE, EDIT_FIELD, EDIT_VALUE = range(12)

# === Константы ===
FROM_LIST = [
    "Склад OOO SULTON-O'KTAM Ташкентская Область",
    "Склад OOO SULTON-O'KTAM город Ташкент"
]
TO_LIST = ["Склад Темирйолтамин город Ташкент",
           "Склад Темирйолинфратузилма город Ташкент",
           "Склад OOO SULTON-O'KTAM Ташкентская Область",
           "Склад OOO SULTON-O'KTAM город Ташкент"]
ITEM_LIST = ["Аккумуляторная батарея 12V-264"
             "Аккумуляторная батарея 4V-450"
             "Аккумуляторная батарея 2V-850"
             "Аккумуляторная батарея НК 1,2V-125"
             "Аккумуляторная батарея НК 1,2V-180"
             "Аккумуляторная батарея НК 1,2V-55"]
UNIT_LIST = ["шт", "л", "кг", "комлпект"]

# Чат для итогового сообщения (ENV)
TARGET_CHAT_ID = int(os.environ.get("TARGET_CHAT_ID", "-1002589936295"))

# === Генерация PDF ===
def generate_pdf(data):
    try:
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        font_path = os.path.join(os.path.dirname(__file__), 'DejaVuSans.ttf')
        pdfmetrics.registerFont(TTFont('DejaVu', font_path))

        c.setFont("DejaVu", 14)
        title_text = f"Накладная №{data['num']} от {data['date']}"
        text_width = pdfmetrics.stringWidth(title_text, "DejaVu", 14)
        c.drawString((width - text_width) / 2, height - 50, title_text)

        c.setFont("DejaVu", 12)
        c.drawString(50, height - 90, f"Откуда: {data['from']}")
        c.drawString(50, height - 110, f"Куда: {data['to']}")
        c.drawString(50, height - 130, f"Автомобиль: {data['car']}")
        c.drawString(50, height - 150, f"Гос. номер: {data['plate']}")

        c.setFont("DejaVu", 10)
        y = height - 180
        row_height = 20
        col_positions = [50, 75, 295, 365, 450]

        c.line(col_positions[0], y, col_positions[4], y)
        c.drawString(col_positions[0] + 2, y - 15, "№")
        c.drawString(col_positions[1] + 2, y - 15, "Наименование")
        c.drawString(col_positions[2] + 2, y - 15, "Ед. изм.")
        c.drawString(col_positions[3] + 2, y - 15, "Количество")
        y -= row_height
        c.line(col_positions[0], y, col_positions[4], y)

        for i, item in enumerate(data['items'], 1):
            c.drawString(col_positions[0] + 2, y - 15, str(i))
            c.drawString(col_positions[1] + 2, y - 15, item['name'])
            c.drawString(col_positions[2] + 2, y - 15, item['unit'])
            c.drawString(col_positions[3] + 2, y - 15, item['qty'])
            y -= row_height
            c.line(col_positions[0], y, col_positions[4], y)

        for x in col_positions:
            c.line(x, height - 180, x, y)

        y -= 40
        c.drawString(50, y, "Отпустил ___________________________________________________________")
        y -= 30
        c.drawString(50, y, "Принял  ____________________________________________________________")

        c.save()
        buffer.seek(0)
        return buffer
    except Exception as e:
        print(f"Ошибка при генерации PDF: {e}")
        return None

# === Хендлеры ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data['items'] = []
    await update.message.reply_text("Введите № накладной:", reply_markup=ReplyKeyboardRemove())
    return NUM

async def new_invoice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data['items'] = []
    await update.message.reply_text("Введите № накладной:", reply_markup=ReplyKeyboardRemove())
    return NUM

async def restart_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("♻ Перезапуск бота...")
    sys.stdout.flush()
    sys.exit(0)

async def get_num(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['num'] = update.message.text
    today = datetime.now().strftime("%d.%m.%Y")
    await update.message.reply_text(f"Введите дату (например, {today}):")
    return DATE

async def get_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['date'] = update.message.text
    keyboard = ReplyKeyboardMarkup([[loc] for loc in FROM_LIST], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Откуда (выберите или введите вручную):", reply_markup=keyboard)
    return FROM

async def get_from(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['from'] = update.message.text
    keyboard = ReplyKeyboardMarkup([[loc] for loc in TO_LIST], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Куда (выберите или введите вручную):", reply_markup=keyboard)
    return TO

async def get_to(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['to'] = update.message.text
    await update.message.reply_text("Автомобиль:", reply_markup=ReplyKeyboardRemove())
    return CAR

async def get_car(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['car'] = update.message.text
    await update.message.reply_text("Гос. номер:")
    return PLATE

async def get_plate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['plate'] = update.message.text
    keyboard = ReplyKeyboardMarkup([[name] for name in ITEM_LIST], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Наименование товара:", reply_markup=keyboard)
    return ITEM_NAME

async def get_item_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['current_item'] = {'name': update.message.text}
    keyboard = ReplyKeyboardMarkup([[u] for u in UNIT_LIST], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Единица измерения:", reply_markup=keyboard)
    return ITEM_UNIT

async def get_item_unit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['current_item']['unit'] = update.message.text
    await update.message.reply_text("Количество:", reply_markup=ReplyKeyboardRemove())
    return ITEM_QTY

async def get_item_qty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['current_item']['qty'] = update.message.text
    context.user_data['items'].append(context.user_data['current_item'])

    item = context.user_data['current_item']
    summary = (
        f"📦 Добавлен товар:\n"
        f"Наименование: {item['name']}\n"
        f"Ед. изм.: {item['unit']}\n"
        f"Количество: {item['qty']}"
    )
    await update.message.reply_text(summary)

    keyboard = ReplyKeyboardMarkup([
        ["Добавить товар"],
        ["Отправить данные"]
    ], resize_keyboard=True)

    await update.message.reply_text("Что дальше?", reply_markup=keyboard)
    return ASK_MORE

async def ask_more(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    if choice == "Добавить товар":
        keyboard = ReplyKeyboardMarkup([[name] for name in ITEM_LIST], resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text("Наименование товара:", reply_markup=keyboard)
        return ITEM_NAME
    elif choice == "Отправить данные":
        data = context.user_data
        item_lines = "\n".join([
            f"{i+1}. {item['name']} | {item['unit']} | {item['qty']}"
            for i, item in enumerate(data['items'])
        ])
        summary = (
            f"📄 Предпросмотр данных накладной:\n"
            f"Накладная №{data['num']} от {data['date']}\n"
            f"Откуда: {data['from']}\n"
            f"Куда: {data['to']}\n"
            f"Автомобиль: {data['car']}\n"
            f"Гос. номер: {data['plate']}\n"
            f"Товары:\n{item_lines}"
        )
        keyboard = ReplyKeyboardMarkup([
            ["Сформировать накладную"],
            ["Изменить данные"]
        ], resize_keyboard=True)
        await update.message.reply_text("🔍 Проверка данных:")
        await update.message.reply_text(summary, reply_markup=keyboard)
        return ASK_MORE
    elif choice == "Изменить данные":
        keyboard = ReplyKeyboardMarkup([
            ["№ накладной", "Дата"],
            ["Откуда", "Куда"],
            ["Автомобиль", "Гос. номер"],
            ["Наименование", "Ед. изм.", "Количество"]
        ], resize_keyboard=True)
        await update.message.reply_text("Что вы хотите изменить?", reply_markup=keyboard)
        return EDIT_FIELD
    elif choice == "Сформировать накладную":
        pdf = generate_pdf(context.user_data)
        if pdf:
            await update.message.reply_document(document=InputFile(pdf, filename="nakladnaya.pdf"))
            text = (
                f"📤 Накладная №{context.user_data['num']} от {context.user_data['date']}\n"
                f"Откуда: {context.user_data['from']}\n"
                f"Куда: {context.user_data['to']}\n"
                f"Авто: {context.user_data['car']} | Гос. номер: {context.user_data['plate']}\n"
                + "\n".join([
                    f"{i+1}. {item['name']} — {item['qty']} {item['unit']}"
                    for i, item in enumerate(context.user_data['items'])
                ])
            )
            await context.bot.send_message(chat_id=TARGET_CHAT_ID, text=text)
        else:
            await update.message.reply_text("⚠️ Ошибка при формировании PDF.")
        keyboard = ReplyKeyboardMarkup([["Сформировать новую накладную"]], resize_keyboard=True)
        await update.message.reply_text("✅ Готово! Хотите начать новую накладную?", reply_markup=keyboard)
        return NUM
    elif choice == "Сформировать новую накладную":
        context.user_data.clear()
        context.user_data['items'] = []
        await update.message.reply_text("Введите № накладной:", reply_markup=ReplyKeyboardRemove())
        return NUM
    else:
        await update.message.reply_text("Пожалуйста, выберите действие из предложенных.")
        return ASK_MORE

async def edit_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    field = update.message.text
    context.user_data['edit_target'] = field
    await update.message.reply_text(f"Введите новое значение для поля: {field}", reply_markup=ReplyKeyboardRemove())
    return EDIT_VALUE

async def edit_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    field = context.user_data.get('edit_target')
    value = update.message.text
    mapping = {
        "№ накладной": "num",
        "Дата": "date",
        "Откуда": "from",
        "Куда": "to",
        "Автомобиль": "car",
        "Гос. номер": "plate",
        "Наименование": "name",
        "Ед. изм.": "unit",
        "Количество": "qty"
    }
    if field in mapping:
        key = mapping[field]
        if key in ["name", "unit", "qty"] and context.user_data['items']:
            context.user_data['items'][-1][key] = value
        else:
            context.user_data[key] = value
    await update.message.reply_text("✅ Обновлено.", reply_markup=ReplyKeyboardMarkup([
        ["Отправить данные"]], resize_keyboard=True))
    return ASK_MORE

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отменено", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def register_handlers(app):
    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("new", new_invoice),
            CommandHandler("restart", restart_bot)
        ],
        states={
            NUM: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_num)],
            DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_date)],
            FROM: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_from)],
            TO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_to)],
            CAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_car)],
            PLATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_plate)],
            ITEM_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_item_name)],
            ITEM_UNIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_item_unit)],
            ITEM_QTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_item_qty)],
            ASK_MORE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_more)],
            EDIT_FIELD: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_field)],
            EDIT_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_value)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(conv)