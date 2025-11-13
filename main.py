{\rtf1\ansi\ansicpg1251\cocoartf2822
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww28600\viewh14880\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import asyncio\
import random\
import sqlite3\
import os\
from datetime import datetime, timedelta\
from aiogram import Bot, Dispatcher\
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery\
from aiogram.enums import ParseMode\
from aiogram.fsm.context import FSMContext\
from aiogram.fsm.state import State, StatesGroup\
from aiogram.fsm.storage.memory import MemoryStorage\
from aiogram import F\
from aiogram.client.default import DefaultBotProperties\
import logging\
\
# ---------------- CONFIG ----------------\
TOKEN = "7836307093:AAHJA0Fd5P2aIkRxEZVduAfmUJHCT-jVXCQ"\
\
# \uc0\u1045 \u1089 \u1083 \u1080  \u1093 \u1086 \u1095 \u1077 \u1096 \u1100 , \u1091 \u1082 \u1072 \u1078 \u1080  \u1072 \u1073 \u1089 \u1086 \u1083 \u1102 \u1090 \u1085 \u1099 \u1081  \u1087 \u1091 \u1090 \u1100 , \u1095 \u1090 \u1086 \u1073 \u1099  \u1080 \u1089 \u1082 \u1083 \u1102 \u1095 \u1080 \u1090 \u1100  \u1087 \u1088 \u1086 \u1073 \u1083 \u1077 \u1084 \u1091  \u1089  \u1088 \u1072 \u1079 \u1085 \u1099 \u1084 \u1080  CWD \u1087 \u1088 \u1080  systemd/container:\
BASE_DIR = os.path.dirname(os.path.abspath(__file__))\
DB_FILE = os.path.join(BASE_DIR, "users.db")\
\
# ---------------- INIT ----------------\
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")\
\
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))\
dp = Dispatcher(storage=MemoryStorage())\
\
# ================= DB =================\
def init_db():\
    conn = sqlite3.connect(DB_FILE)\
    cur = conn.cursor()\
    cur.execute("""\
    CREATE TABLE IF NOT EXISTS users (\
        user_id INTEGER PRIMARY KEY,\
        pair TEXT\
    )\
    """)\
    conn.commit()\
    conn.close()\
    logging.info(f"DB initialized at \{DB_FILE\}")\
\
def save_pair(user_id: int, pair: str):\
    conn = sqlite3.connect(DB_FILE)\
    cur = conn.cursor()\
    cur.execute("INSERT OR REPLACE INTO users (user_id, pair) VALUES (?, ?)", (user_id, pair))\
    conn.commit()\
    conn.close()\
    logging.info(f"Saved pair for \{user_id\}: \{pair\}")\
\
def save_user(user_id: int):\
    """\uc0\u1044 \u1086 \u1073 \u1072 \u1074 \u1083 \u1103 \u1077 \u1090  \u1087 \u1086 \u1083 \u1100 \u1079 \u1086 \u1074 \u1072 \u1090 \u1077 \u1083 \u1103  \u1074  \u1073 \u1072 \u1079 \u1091  \u1073 \u1077 \u1079  \u1087 \u1072 \u1088 \u1099  (\u1095 \u1090 \u1086 \u1073 \u1099  \u1077 \u1075 \u1086  \u1084 \u1086 \u1078 \u1085 \u1086  \u1073 \u1099 \u1083 \u1086  \u1085 \u1072 \u1081 \u1090 \u1080  \u1074  get_all_users)."""\
    conn = sqlite3.connect(DB_FILE)\
    cur = conn.cursor()\
    cur.execute("INSERT OR IGNORE INTO users (user_id, pair) VALUES (?, NULL)", (user_id,))\
    conn.commit()\
    conn.close()\
    logging.info(f"Ensured user exists in DB: \{user_id\}")\
\
def get_pair(user_id: int):\
    conn = sqlite3.connect(DB_FILE)\
    cur = conn.cursor()\
    cur.execute("SELECT pair FROM users WHERE user_id = ?", (user_id,))\
    row = cur.fetchone()\
    conn.close()\
    return row[0] if row else None\
\
def get_all_users():\
    conn = sqlite3.connect(DB_FILE)\
    cur = conn.cursor()\
    cur.execute("SELECT user_id FROM users")\
    rows = cur.fetchall()\
    conn.close()\
    return [r[0] for r in rows]\
\
# ================= FSM =================\
class Form(StatesGroup):\
    waiting_for_id = State()\
    waiting_for_type = State()\
    waiting_for_pair = State()\
    ready_for_signals = State()\
\
# ================= DATA =================\
otc_pairs = [\
    "EUR/USD OTC", "USD/CHF OTC", "AUD/USD OTC", "Gold OTC",\
    "AUD/CAD OTC", "AUD/CHF OTC", "AUD/JPY OTC", "AUD/NZD OTC",\
    "CAD/CHF OTC", "CAD/JPY OTC", "CHF/JPY OTC"\
]\
real_pairs = [\
    "EUR/USD", "AUD/USD", "Gold", "AUD/CAD", "AUD/JPY", "CAD/JPY"\
]\
index_pairs = [\
    "Compound Index", "Asia Composite Index", "Crypto Composite Index"\
]\
\
all_pairs = otc_pairs + real_pairs + index_pairs\
\
timeframes = ["10 minutos"] * 5 + ["20 minutos"] * 3 + ["30 minutos"] * 2 + ["50 minutos"]\
budget_options = ["20$", "30$", "40$"]\
directions = ["\uc0\u55357 \u56520  \u1042 \u1074 \u1077 \u1088 \u1093 ", "\u55357 \u56521  \u1042 \u1085 \u1080 \u1079 "]\
\
user_cooldowns = \{\}\
\
# ================= KEYBOARDS =================\
def get_type_keyboard():\
    return InlineKeyboardMarkup(inline_keyboard=[\
        [InlineKeyboardButton(text="\uc0\u55357 \u56697  OTC \u1055 \u1072 \u1088 \u1099 ", callback_data="type_otc")],\
        [InlineKeyboardButton(text="\uc0\u55357 \u56520  \u1056 \u1077 \u1072 \u1083 \u1100 \u1085 \u1099 \u1077  \u1087 \u1072 \u1088 \u1099 ", callback_data="type_real")],\
        [InlineKeyboardButton(text="\uc0\u55357 \u56522  \u1048 \u1085 \u1076 \u1077 \u1082 \u1089 \u1099 ", callback_data="type_index")]\
    ])\
\
def get_pairs_keyboard(pairs):\
    return InlineKeyboardMarkup(\
        inline_keyboard=[[InlineKeyboardButton(text=p, callback_data=f"pair:\{p\}")] for p in pairs] +\
                        [[InlineKeyboardButton(text="\uc0\u55357 \u56601  \u1053 \u1072 \u1079 \u1072 \u1076 ", callback_data="back_to_types")]]\
    )\
\
# ================= HANDLERS =================\
@dp.message(F.text == "/start")\
async def start(message: Message, state: FSMContext):\
    user_id = message.from_user.id\
    save_user(user_id)\
    await message.answer("\uc0\u55357 \u56395  \u1055 \u1088 \u1080 \u1074 \u1077 \u1090 ! \u1055 \u1086 \u1078 \u1072 \u1083 \u1091 \u1081 \u1089 \u1090 \u1072 , \u1087 \u1088 \u1080 \u1096 \u1083 \u1080  \u1084 \u1085 \u1077  \u1089 \u1074 \u1086 \u1081  ID \u1072 \u1082 \u1082 \u1072 \u1091 \u1085 \u1090 \u1072  (\u1083 \u1080 \u1073 \u1086  \u1087 \u1088 \u1086 \u1089 \u1090 \u1086  \u1085 \u1072 \u1078 \u1084 \u1080  \u1083 \u1102 \u1073 \u1091 \u1102  \u1082 \u1085 \u1086 \u1087 \u1082 \u1091  \u1085 \u1080 \u1078 \u1077 ):")\
    await state.set_state(Form.waiting_for_id)\
\
@dp.message(Form.waiting_for_id)\
async def process_id(message: Message, state: FSMContext):\
    # \uc0\u1045 \u1089 \u1083 \u1080  \u1087 \u1086 \u1083 \u1100 \u1079 \u1086 \u1074 \u1072 \u1090 \u1077 \u1083 \u1100  \u1086 \u1090 \u1087 \u1088 \u1072 \u1074 \u1080 \u1083  ID \u1090 \u1077 \u1082 \u1089 \u1090 \u1086 \u1084  \'97 \u1084 \u1086 \u1078 \u1085 \u1086  \u1074 \u1072 \u1083 \u1080 \u1076 \u1080 \u1088 \u1086 \u1074 \u1072 \u1090 \u1100 /\u1089 \u1086 \u1093 \u1088 \u1072 \u1085 \u1080 \u1090 \u1100 , \u1085 \u1086  \u1084 \u1099  \u1091 \u1078 \u1077  \u1089 \u1086 \u1093 \u1088 \u1072 \u1085 \u1080 \u1083 \u1080  user \u1074  \u1041 \u1044 \
    await message.answer(\
        "\uc0\u9989  \u1048 \u1076 \u1077 \u1085 \u1090 \u1080 \u1092 \u1080 \u1082 \u1072 \u1090 \u1086 \u1088  \u1087 \u1088 \u1080 \u1085 \u1103 \u1090  (\u1080 \u1083 \u1080  \u1087 \u1086 \u1076 \u1090 \u1074 \u1077 \u1088 \u1078 \u1076 \u1105 \u1085 ). \u1058 \u1077 \u1087 \u1077 \u1088 \u1100  \u1074 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1090 \u1080 \u1087  \u1074 \u1072 \u1083 \u1102 \u1090 \u1085 \u1086 \u1081  \u1087 \u1072 \u1088 \u1099 :",\
        reply_markup=get_type_keyboard()\
    )\
    await state.set_state(Form.waiting_for_type)\
\
@dp.callback_query(F.data == "type_otc")\
async def show_otc_pairs(callback: CallbackQuery, state: FSMContext):\
    await callback.answer()  # ACK\
    await callback.message.answer("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1074 \u1072 \u1083 \u1102 \u1090 \u1085 \u1091 \u1102  \u1087 \u1072 \u1088 \u1091  OTC:", reply_markup=get_pairs_keyboard(otc_pairs))\
    await state.set_state(Form.waiting_for_pair)\
\
@dp.callback_query(F.data == "type_real")\
async def show_real_pairs(callback: CallbackQuery, state: FSMContext):\
    await callback.answer()\
    await callback.message.answer("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1088 \u1077 \u1072 \u1083 \u1100 \u1085 \u1091 \u1102  \u1087 \u1072 \u1088 \u1091 :", reply_markup=get_pairs_keyboard(real_pairs))\
    await state.set_state(Form.waiting_for_pair)\
\
@dp.callback_query(F.data == "type_index")\
async def show_index_pairs(callback: CallbackQuery, state: FSMContext):\
    await callback.answer()\
    await callback.message.answer("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1080 \u1085 \u1076 \u1077 \u1082 \u1089 :", reply_markup=get_pairs_keyboard(index_pairs))\
    await state.set_state(Form.waiting_for_pair)\
\
@dp.callback_query(F.data == "back_to_types")\
async def back_to_type_selection(callback: CallbackQuery, state: FSMContext):\
    await callback.answer()\
    await callback.message.answer("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1090 \u1080 \u1087  \u1074 \u1072 \u1083 \u1102 \u1090 \u1085 \u1099 \u1093  \u1087 \u1072 \u1088 :", reply_markup=get_type_keyboard())\
    await state.set_state(Form.waiting_for_type)\
\
@dp.callback_query(F.data.startswith("pair:"))\
async def select_pair(callback: CallbackQuery, state: FSMContext):\
    await callback.answer()  # ACK \'97 \uc0\u1091 \u1073 \u1080 \u1088 \u1072 \u1077 \u1090  \u1089 \u1087 \u1080 \u1085 \u1085 \u1077 \u1088  \u1074  Telegram\
    pair = callback.data.split(":", 1)[1]\
    uid = callback.from_user.id\
\
    save_pair(uid, pair)\
    logging.info(f"\uc0\u9989  User \{uid\} \u1074 \u1099 \u1073 \u1088 \u1072 \u1083  \u1087 \u1072 \u1088 \u1091  \{pair\}")\
\
    btn = InlineKeyboardMarkup(\
        inline_keyboard=[\
            [InlineKeyboardButton(text="\uc0\u55357 \u56553  \u1055 \u1054 \u1051 \u1059 \u1063 \u1048 \u1058 \u1068  \u1057 \u1048 \u1043 \u1053 \u1040 \u1051 ", callback_data="get_signal")],\
            [InlineKeyboardButton(text="\uc0\u55357 \u56601  \u1053 \u1072 \u1079 \u1072 \u1076 ", callback_data="back_to_types")]\
        ]\
    )\
    await callback.message.answer(f"\uc0\u1054 \u1090 \u1083 \u1080 \u1095 \u1085 \u1072 \u1103  \u1087 \u1072 \u1088 \u1072 : \{pair\}\\n\u1043 \u1086 \u1090 \u1086 \u1074  \u1082  \u1086 \u1090 \u1087 \u1088 \u1072 \u1074 \u1082 \u1077  \u1089 \u1080 \u1075 \u1085 \u1072 \u1083 \u1072 . \u55357 \u56391 ", reply_markup=btn)\
    await state.set_state(Form.ready_for_signals)\
\
\
@dp.callback_query(F.data == "get_signal")\
async def send_signal(callback: CallbackQuery, state: FSMContext):\
    await callback.answer()  # ACK\
    user_id = callback.from_user.id\
    logging.info(f"\uc0\u55357 \u56393  SIGNAL \u1079 \u1072 \u1087 \u1088 \u1086 \u1089  \u1086 \u1090  \{user_id\}")\
\
    pair = get_pair(user_id)\
    logging.info(f"\uc0\u55357 \u56589  \u1055 \u1072 \u1088 \u1072  \u1080 \u1079  \u1073 \u1072 \u1079 \u1099  \u1076 \u1083 \u1103  \{user_id\}: \{pair\}")\
\
    if not pair:\
        await callback.message.answer("\uc0\u9888 \u65039  \u1057 \u1085 \u1072 \u1095 \u1072 \u1083 \u1072  \u1074 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1087 \u1072 \u1088 \u1091  \u1074 \u1072 \u1083 \u1102 \u1090 !")\
        return\
\
    # cooldown check (\uc0\u1080 \u1089 \u1087 \u1086 \u1083 \u1100 \u1079 \u1091 \u1077 \u1084  UTC \u1074 \u1077 \u1079 \u1076 \u1077 )\
    now = datetime.utcnow()\
    cooldown_until = user_cooldowns.get(user_id)\
    if cooldown_until and (cooldown_until - now).total_seconds() > 0:\
        remaining = int((cooldown_until - now).total_seconds())\
        minutes = remaining // 60\
        seconds = remaining % 60\
        await callback.answer(f"\uc0\u9203  \u1054 \u1078 \u1080 \u1076 \u1072 \u1081 \u1090 \u1077  \{minutes\} \u1084 \u1080 \u1085 \u1091 \u1090  \{seconds\} \u1089 \u1077 \u1082 \u1091 \u1085 \u1076  \u1076 \u1086  \u1089 \u1083 \u1077 \u1076 \u1091 \u1102 \u1097 \u1077 \u1075 \u1086  \u1089 \u1080 \u1075 \u1085 \u1072 \u1083 \u1072 .", show_alert=True)\
        return\
\
    user_cooldowns[user_id] = now + timedelta(minutes=5)\
\
    # UX: \uc0\u1087 \u1086 \u1082 \u1072 \u1079 \u1099 \u1074 \u1072 \u1077 \u1084  "\u1075 \u1086 \u1090 \u1086 \u1074 \u1080 \u1084 " \u1080  \u1091 \u1073 \u1080 \u1088 \u1072 \u1077 \u1084  \u1073 \u1099 \u1089 \u1090 \u1088 \u1086 \
    msg = await callback.message.answer("\uc0\u9203  \u1043 \u1086 \u1090 \u1086 \u1074 \u1083 \u1102  \u1089 \u1080 \u1075 \u1085 \u1072 \u1083 ...")\
    await asyncio.sleep(1.5)\
    try:\
        await msg.delete()\
    except Exception:\
        pass\
\
    tf = random.choice(timeframes)\
    budget = random.choice(budget_options)\
    direction = random.choice(directions)\
\
    signal_text = (\
        f"\uc0\u1055 \u1072 \u1088 \u1072 : *\{pair\}*\\n"\
        f"\uc0\u1042 \u1088 \u1077 \u1084 \u1103  \u1089 \u1076 \u1077 \u1083 \u1082 \u1080 : *\{tf\}*\\n"\
        f"\uc0\u1041 \u1102 \u1076 \u1078 \u1077 \u1090 : *\{budget\}*\\n"\
        f"\uc0\u1053 \u1072 \u1087 \u1088 \u1072 \u1074 \u1083 \u1077 \u1085 \u1080 \u1077 : *\{direction\}*"\
    )\
\
    btn = InlineKeyboardMarkup(\
        inline_keyboard=[\
            [InlineKeyboardButton(text="\uc0\u55357 \u56553  \u1055 \u1054 \u1051 \u1059 \u1063 \u1048 \u1058 \u1068  \u1057 \u1048 \u1043 \u1053 \u1040 \u1051 ", callback_data="get_signal")],\
            [InlineKeyboardButton(text="\uc0\u55357 \u56601  \u1053 \u1072 \u1079 \u1072 \u1076 ", callback_data="back_to_types")]\
        ]\
    )\
    await callback.message.answer(signal_text, reply_markup=btn)\
    await state.set_state(Form.ready_for_signals)\
\
# ================= AUTO SIGNALS =================\
async def scheduled_signals():\
    """\
    \uc0\u1056 \u1072 \u1073 \u1086 \u1090 \u1072 \u1077 \u1090  \u1087 \u1086  \u1083 \u1086 \u1082 \u1072 \u1083 \u1100 \u1085 \u1086 \u1084 \u1091  \u1075 \u1088 \u1072 \u1092 \u1080 \u1082 \u1091  UTC+5:\
     - \uc0\u1089  19:00 \u1076 \u1086  04:00 \u8594  \u1088 \u1072 \u1079  \u1074  3 \u1095 \u1072 \u1089 \u1072 \
     - \uc0\u1089  04:00 \u1076 \u1086  10:00 \u8594  \u1088 \u1072 \u1079  \u1074  1 \u1095 \u1072 \u1089 \
     - \uc0\u1089  10:00 \u1076 \u1086  19:00 \u8594  \u1087 \u1072 \u1091 \u1079 \u1072  \u1076 \u1086  19:00\
    \uc0\u1047 \u1072 \u1097 \u1080 \u1097 \u1077 \u1085 \u1086  \u1086 \u1090  \u1087 \u1072 \u1076 \u1077 \u1085 \u1080 \u1081  \'97 \u1083 \u1086 \u1075 \u1080 \u1088 \u1091 \u1077 \u1084  \u1080 \u1089 \u1082 \u1083 \u1102 \u1095 \u1077 \u1085 \u1080 \u1103  \u1080  \u1087 \u1099 \u1090 \u1072 \u1077 \u1084 \u1089 \u1103  \u1089 \u1085 \u1086 \u1074 \u1072 .\
    """\
    while True:\
        try:\
            now_utc = datetime.utcnow()\
            now_local = now_utc + timedelta(hours=5)\
            hour = now_local.hour\
\
            if 19 <= hour or hour < 4:\
                interval_hours = 3\
            elif 4 <= hour < 10:\
                interval_hours = 1\
            else:\
                # \uc0\u1087 \u1072 \u1091 \u1079 \u1072  \u1076 \u1086  19:00 \u1083 \u1086 \u1082 \u1072 \u1083 \u1100 \u1085 \u1086 \u1075 \u1086  \u1074 \u1088 \u1077 \u1084 \u1077 \u1085 \u1080 \
                next_local = now_local.replace(hour=19, minute=0, second=0, microsecond=0)\
                if next_local <= now_local:\
                    next_local += timedelta(days=1)\
                next_utc = next_local - timedelta(hours=5)\
                sleep_seconds = (next_utc - datetime.utcnow()).total_seconds()\
                logging.info(f"Auto signals paused until \{next_local.isoformat()\} (local). Sleeping \{int(sleep_seconds)\}s.")\
                if sleep_seconds > 0:\
                    await asyncio.sleep(sleep_seconds)\
                continue\
\
            # \uc0\u1092 \u1086 \u1088 \u1084 \u1080 \u1088 \u1091 \u1077 \u1084  \u1089 \u1080 \u1075 \u1085 \u1072 \u1083 \
            pair = random.choice(all_pairs)\
            tf = random.choice(timeframes)\
            budget = random.choice(budget_options)\
            direction = random.choice(directions)\
\
            text = (\
                f"\uc0\u1055 \u1072 \u1088 \u1072 : *\{pair\}*\\n"\
                f"\uc0\u1042 \u1088 \u1077 \u1084 \u1103  \u1089 \u1076 \u1077 \u1083 \u1082 \u1080 : *\{tf\}*\\n"\
                f"\uc0\u1041 \u1102 \u1076 \u1078 \u1077 \u1090 : *\{budget\}*\\n"\
                f"\uc0\u1053 \u1072 \u1087 \u1088 \u1072 \u1074 \u1083 \u1077 \u1085 \u1080 \u1077 : *\{direction\}*"\
            )\
\
            btn = InlineKeyboardMarkup(\
                inline_keyboard=[[InlineKeyboardButton(\
                    text="\uc0\u55357 \u56553  \u1055 \u1054 \u1051 \u1059 \u1063 \u1048 \u1058 \u1068  \u1057 \u1048 \u1043 \u1053 \u1040 \u1051 ",\
                    callback_data="get_signal"\
                )]]\
            )\
\
            users = get_all_users()\
            logging.info(f"\uc0\u1056 \u1072 \u1089 \u1089 \u1099 \u1083 \u1072 \u1102  \u1089 \u1080 \u1075 \u1085 \u1072 \u1083  \{len(users)\} \u1087 \u1086 \u1083 \u1100 \u1079 \u1086 \u1074 \u1072 \u1090 \u1077 \u1083 \u1103 \u1084 . \u1055 \u1072 \u1088 \u1072 : \{pair\}")\
\
            for uid in users:\
                try:\
                    await bot.send_message(uid, text, reply_markup=btn)\
                except Exception as e:\
                    logging.warning(f"\uc0\u10060  \u1053 \u1077  \u1091 \u1076 \u1072 \u1083 \u1086 \u1089 \u1100  \u1086 \u1090 \u1087 \u1088 \u1072 \u1074 \u1080 \u1090 \u1100  \{uid\}: \{e\}")\
\
            # \uc0\u1089 \u1095 \u1080 \u1090 \u1072 \u1077 \u1084  \u1083 \u1086 \u1082 \u1072 \u1083 \u1100 \u1085 \u1086 \u1077  \u1074 \u1088 \u1077 \u1084 \u1103  \u1089 \u1083 \u1077 \u1076 \u1091 \u1102 \u1097 \u1077 \u1075 \u1086  \u1089 \u1086 \u1073 \u1099 \u1090 \u1080 \u1103  \u1080  \u1082 \u1086 \u1085 \u1074 \u1077 \u1088 \u1090 \u1080 \u1084  \u1074  UTC \u1076 \u1083 \u1103  sleep\
            next_local = (now_local.replace(minute=0, second=0, microsecond=0) + timedelta(hours=interval_hours))\
            next_utc = next_local - timedelta(hours=5)\
            sleep_seconds = (next_utc - datetime.utcnow()).total_seconds()\
            if sleep_seconds > 0:\
                logging.info(f"Next auto signal at (local) \{next_local.isoformat()\} \'97 sleeping \{int(sleep_seconds)\}s.")\
                await asyncio.sleep(sleep_seconds)\
            else:\
                # \uc0\u1079 \u1072 \u1097 \u1080 \u1090 \u1085 \u1072 \u1103  \u1079 \u1072 \u1075 \u1083 \u1091 \u1096 \u1082 \u1072 \
                await asyncio.sleep(1)\
        except Exception as exc:\
            logging.exception(f"\uc0\u1054 \u1096 \u1080 \u1073 \u1082 \u1072  \u1074  scheduled_signals: \{exc\}")\
            await asyncio.sleep(10)\
\
# ================= MAIN =================\
async def main():\
    init_db()\
    # \uc0\u1089 \u1090 \u1072 \u1088 \u1090 \u1091 \u1077 \u1084  \u1090 \u1072 \u1089 \u1082 \u1091  \u1088 \u1072 \u1089 \u1089 \u1099 \u1083 \u1082 \u1080 \
    asyncio.create_task(scheduled_signals())\
    logging.info("Starting polling...")\
    await dp.start_polling(bot)\
\
if __name__ == '__main__':\
    try:\
        asyncio.run(main())\
    except (KeyboardInterrupt, SystemExit):\
        logging.info("Shutting down bot...")\
}
