from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest
from aiogram import F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters.callback_data import CallbackData
from sqlmodel import Session as SQLSession
from sqlmodel import select
import os
import re
from dotenv import load_dotenv

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError

import db
from db.models.session import Session

load_dotenv()

sessions_router = Router()

APP_ID = os.getenv("API_ID")
APP_HASH = os.getenv("API_HASH")
TEST_IP = os.getenv("TEST_ENV_IP")
TEST_ENV = os.getenv("TEST_ENV")

def change_tg_servers(client):
  if bool(TEST_ENV):
    client.session.set_dc(1, TEST_IP, 80)

class CreateSessionFSM(StatesGroup):
  number = State()
  messageId = State()
  code_hash = State()
  mfa_code = State()

class SessionsCallback(CallbackData, prefix="sessions"):
    sessionId: int

class EditSessionCallback(CallbackData, prefix="editSession"):
    sessionId: int
    action: str

def get_menu_keyboard():
  builder = InlineKeyboardBuilder()
  builder.row(InlineKeyboardButton(text="⬅️ Вернутся в меню", callback_data="main_menu"))
  return builder.as_markup()

def get_cancel_keyboard():
  builder = InlineKeyboardBuilder()
  builder.row(InlineKeyboardButton(text="Отмена ❌", callback_data="main_menu"))
  return builder.as_markup()

@sessions_router.callback_query(F.data == "add_session")
async def add_session_callback(callback_query: CallbackQuery, state: FSMContext):
  msg = [
    "Введите номер телефона ⬇️"
  ]
  msg = '\n'.join(msg)
  await callback_query.message.edit_text(msg, reply_markup=get_cancel_keyboard())
  await state.update_data(messageId=callback_query.message.message_id)
  await state.set_state(CreateSessionFSM.number)

@sessions_router.message(CreateSessionFSM.number)
async def phone_number_handler(message: Message, state: FSMContext):
  client = TelegramClient(StringSession(), APP_ID, APP_HASH)
  change_tg_servers(client)
  await client.connect()
  number = message.text.replace(" ", "")

  with SQLSession(db.engine) as session:
    user = session.exec(select(Session).where(Session.number == number)).first()
    if user != None:
      await message.answer("Этот номер телефона уже существует⚠️")

  phone_code = await client.send_code_request(message.text)
  phone_code_hash = phone_code.phone_code_hash

  await state.set_state(CreateSessionFSM.code_hash)
  await state.update_data(code_hash=phone_code_hash, number=message.text)


  data = await state.get_data()
  messageId = data["messageId"]
  await message.bot.delete_message(message_id=messageId, chat_id=message.chat.id)
  await message.bot.delete_message(message_id=message.message_id, chat_id=message.chat.id)

  msg = await message.answer("Введите код подтверждения ⬇️", reply_markup=get_cancel_keyboard())
  newMsgId = msg.message_id
  await state.update_data(messageId=newMsgId)

  @sessions_router.message(CreateSessionFSM.code_hash)
  async def phone_code_handler(message: Message, state: FSMContext):
    # client = TelegramClient(StringSession(), APP_ID, APP_HASH)
    # await client.connect()
    
    # state_data = await state.get_data()
    # phone_code_hash = state_data["code_hash"]
    # number = state_data["number"]

    data = await state.get_data()
    messageId = data["messageId"]
    await message.bot.delete_message(message_id=messageId, chat_id=message.chat.id)
    await message.bot.delete_message(message_id=message.message_id, chat_id=message.chat.id)

    try:
      await client.sign_in(number, code=message.text, phone_code_hash=phone_code_hash)
      await state.clear()

      with SQLSession(db.engine) as session:
        tgSession = Session(session_string=str(client.session.save()), user=message.from_user.id, number=number)
        session.add(tgSession)
        session.commit()

      await message.answer(f"Сессия {number} была успешно добавлена ✅", reply_markup=get_menu_keyboard())
    except SessionPasswordNeededError:
        await state.set_state(CreateSessionFSM.mfa_code)

        await message.answer("Введите пароль 2 факторной аутентификации ⬇️", reply_markup=get_cancel_keyboard())
    
  @sessions_router.message(CreateSessionFSM.mfa_code)
  async def mfa_code_handler(message: Message, state: FSMContext):
    # state_data = await state.get_data()
    # phone_code_hash = state_data["code_hash"]
    # number = state_data["number"]

    await client.sign_in(number, code=message.text, phone_code_hash=phone_code_hash, password=message.text)
    await state.clear()

    with SQLSession(db.engine) as session:
        tgSession = Session(session_string=str(client.session.save()), user=message.from_user.id, number=number)
        session.add(tgSession)
        session.commit()

    await message.answer(f"Сессия {number} была успешно добавлена ✅", reply_markup=get_menu_keyboard())

@sessions_router.callback_query(F.data == "sessions")
async def sessions_callback(callback_query: CallbackQuery):
  builder = InlineKeyboardBuilder()

  with SQLSession(db.engine) as session:
    sessions = session.exec(select(Session).where(Session.user == callback_query.from_user.id)).all()

    for sess in sessions:
      builder.row(InlineKeyboardButton(text=str(sess.number), callback_data=SessionsCallback(sessionId=sess.id).pack()))

    builder.adjust(3)
    builder.row(InlineKeyboardButton(text="⬅️ Вернутся в меню", callback_data="main_menu"))

  await callback_query.message.edit_text("У вас нету сессий 😢" if len(sessions) == 0 else "Все сессии ⬇️", reply_markup=builder.as_markup())
  
@sessions_router.callback_query(SessionsCallback.filter())
async def session_callback(callback_query: CallbackQuery, callback_data: SessionsCallback):

  with SQLSession(db.engine) as session:
    sess = session.exec(select(Session).where(Session.id == callback_data.sessionId)).first()
  
  builder = InlineKeyboardBuilder()

  builder.add(InlineKeyboardButton(text="Получить код", callback_data=EditSessionCallback(sessionId=sess.id, action="getCode").pack()))
  builder.add(InlineKeyboardButton(text="Удалить сессию", callback_data=EditSessionCallback(sessionId=sess.id, action="confirmDelete").pack()))
  builder.row(InlineKeyboardButton(text="⬅️ Вернутся в меню", callback_data="sessions"))

  await callback_query.message.edit_text(f"Сессия {sess.number} ⬇️", reply_markup=builder.as_markup())

@sessions_router.callback_query(EditSessionCallback.filter())
async def edit_session_callback(callback_query: CallbackQuery, callback_data: EditSessionCallback):
  action = callback_data.action

  if action == "getCode":
    with SQLSession(db.engine) as session:
      sess = session.exec(select(Session).where(Session.id == callback_data.sessionId)).first()

    client = TelegramClient(StringSession(sess.session_string), APP_ID, APP_HASH)
    change_tg_servers(client)
    await client.connect()

    lastCode = (await client.get_messages(777000))[0]
    lastCode = str(lastCode.message)
    lastCode = re.search(r"[0-9]{5}", lastCode).group(0)

    msg = [
      f"Последний код от телеграмма: <code>{lastCode}</code>",
      "",
      "Ожидание нового кода"
    ]
    msg = '\n'.join(msg)

    builder = InlineKeyboardBuilder()

    # builder.row(InlineKeyboardButton(text="Получить новый код", callback_data=EditSessionCallback(sessionId=callback_data.sessionId, action="getCode").pack()))
    builder.row(InlineKeyboardButton(text="⬅️ Вернутся в меню", callback_data="main_menu"))

    try:
      await callback_query.message.edit_text(msg, reply_markup=builder.as_markup())
    except TelegramBadRequest:
      pass

    @client.on(events.NewMessage)
    async def on_message_handler(event):
      # lastCode = (await client.get_messages(777000))[0]
      # lastCode = lastCode.message
      lastCode = event.message.message
      lastCode = re.search(r"[0-9]{5}", lastCode).group(0)
      print(lastCode)

      msg = [
        f"Новый код от телеграмма: <code>{lastCode}</code>",
      ]
      msg = '\n'.join(msg)


      builder = InlineKeyboardBuilder()

      builder.row(InlineKeyboardButton(text="Получить новый код", callback_data=EditSessionCallback(sessionId=callback_data.sessionId, action="getCode").pack()))
      builder.row(InlineKeyboardButton(text="⬅️ Вернутся в меню", callback_data="main_menu"))

      await callback_query.bot.send_message(callback_query.from_user.id, msg, reply_markup=builder.as_markup())
      client.disconnect()

  elif action == "confirmDelete":
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Нет ❌", callback_data=SessionsCallback(sessionId=callback_data.sessionId).pack()))
    builder.add(InlineKeyboardButton(text="Да ✅", callback_data=EditSessionCallback(sessionId=callback_data.sessionId, action="delete").pack()))

    await callback_query.message.edit_text("Вы уверенны?", reply_markup=builder.as_markup())
  elif action == "delete":
    with SQLSession(db.engine) as session:
      sess = session.exec(select(Session).where(Session.id == callback_data.sessionId)).first()
      session.delete(sess)
      session.commit()

    await callback_query.message.edit_text(f"Сессия {sess.number} была успешно удалена ✅", reply_markup=get_menu_keyboard())