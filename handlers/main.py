from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from sqlmodel import Session as SQLSession
from sqlmodel import select
from aiogram.types import CallbackQuery

import db
from db.models.user import User

main_router = Router()

def get_welcome_message():
  msg = [
    "Привет, я бот для хранения сессий в телеграмме",
    "",
    "Выбери действие ниже ⬇️"
  ]
  msg = '\n'.join(msg)
  return msg

def get_actions_keyboard():
  builder = InlineKeyboardBuilder()
  builder.add(InlineKeyboardButton(text="Сессии", callback_data="sessions"))
  builder.add(InlineKeyboardButton(text="Добавить сессию", callback_data="add_session"))
  return builder.as_markup()

@main_router.message(CommandStart())
async def welcome_handler(message: Message):
  with SQLSession(db.engine) as session:
    user = session.exec(select(User).where(User.id == message.from_user.id)).first()
    if user == None:
      user = User(id=message.from_user.id)
      session.add(user)
      session.commit()
  await message.answer(get_welcome_message(), reply_markup=get_actions_keyboard())

@main_router.callback_query(F.data == "main_menu")
async def main_menu_callback(callback_query: CallbackQuery):
    await callback_query.message.edit_text(get_welcome_message(), reply_markup=get_actions_keyboard())
