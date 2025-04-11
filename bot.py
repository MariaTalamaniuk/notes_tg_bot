import json
import asyncio
from pathlib import Path
from datetime import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from config import TOKEN

bot = Bot(token=TOKEN, parse_mode="HTML")
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
db_file = Path('db.json')

def read_db():
    if not db_file.exists():
        return {}
    with db_file.open('r', encoding="utf-8") as file:
        return json.load(file)

def write_db(data):
    with db_file.open('w', encoding='utf-8') as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

main_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
main_keyboard.add(KeyboardButton('/new'), KeyboardButton('/notes'))

class NoteForm(StatesGroup):
    title = State()
    description = State()
    remind_at = State()
@dp.message(Command('start'))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Привіт! Щоб створити нотатку, натисни /new\nЩоб переглянути нотатки — /notes",
        reply_markup=main_keyboard
    )
@dp.message(Command('new'))
async def cmd_new(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer('Введіть назву нотатки: ')
    await state.set_state(NoteForm.title)

@dp.message(state=NoteForm.title)
async def note_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer('Введіть опис нотатки: ')
    await state.set_state(NoteForm.description)

@dp.message(state=NoteForm.description)
async def note_description(message: types.Message, state: FSMContext):
    await state.update_data(descriptoin=message.text)
    await message.answer('Введи дату та час нагадування у форматі: YYYY-MM-DD HH:MM (наприклад: 2025-03-29 17:30):')
    await state.set_state(NoteForm.remind_at)

@dp.message(state=NoteForm.remind_at)
async def note_time(message: types.Message, state: FSMContext):
    try:
        remind_time = datetime.strptime(message.text, "%Y-%m-%d %H:%M")
    except ValueError:
        await message.answer('Невірний формат! Спробуй ще раз: YYYY-MM-DD HH:MM')
        return

    data = await state.get_data()
    user_id = str(message.from_user.id)
    db = read_db()
    db.setdefault(user_id, []).append({
        "title": data["title"],
        "description": data["description"],
        "remind_at": remind_time.strftime("%Y-%m-%d %H:%M"),
        "notified": False
    })

    write_db(db)
    await message.answer('Нотатку збережено ✅')
    await state.clear()