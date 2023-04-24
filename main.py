import asyncio
import random

from db import Databases
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.utils import executor
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from States import *
from Keyboards import *
from cfg import token
import sqlite3
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
connection = sqlite3.connect("Words.db")
cursor = connection.cursor()
words = cursor.execute("SELECT word FROM w").fetchall()

db = Databases("users.db")
storage = MemoryStorage()
bot = Bot(token)
dp = Dispatcher(bot, storage=storage)

tic_tac_toe = {}


@dp.message_handler(commands=["start", "help"], state=None)
async def start(message: types.Message):
    await bot.send_message(message.from_user.id, f"Привет, {message.from_user.first_name}. "
                                                 f"Этот бот предназначен для игры с друзьями. Доступные игры:\n"
                                                 f"  Крестики-нолики\n"
                                                 f"  Игра в слова\n"
                                                 f"Для игры нужно зарегестрироваться по команде /register "
                                                 f"и найти своего друга по команде /add.\n"
                                                 f"Вы можете просмотеть список друзей: /friends\n"
                                                 f"Во время игры вам доступна команда /отмена\n"
                                                 f"Вы можете добавлять пользователей в червый лист: /black_list_add\n"
                                                 f"и удалять: /black_list", reply_markup=main_kb())


@dp.message_handler(commands=["отменить"], state=[Add_friends.nickname, Reg.nickname])
@dp.message_handler(Text(equals="отменить", ignore_case=True), state=[Add_friends.nickname, Reg.nickname])
async def stop(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await message.reply("Ok", reply_markup=main_kb())
    await state.finish()


@dp.message_handler(commands="отмена", state=[Tic_tac_toe.game, Word_game.game])
async def d_g(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            move = tic_tac_toe[data['game']]["move"]
            if tic_tac_toe[data['game']]["players"][move] != message.from_user.id:
                await bot.send_message(message.from_user.id,
                                       "Если в течение 30 секунд не будет сделан ход, то игра будет отменена")
                await delete_game(data['game'], tic_tac_toe[data['game']])
            else:
                msg = await bot.send_message(message.from_user.id, "Сейчас ваш ход")
                await message.delete()
                await asyncio.sleep(2)
                await msg.delete()
    except:
        pass


@dp.message_handler(commands=['friends'], state=None)
async def get_friends(message: types.Message):
    if db.id_exists(message.from_user.id):
        friends = db.get_friends(message.from_user.id)
        if "," in (friends[0][0]):
            await bot.send_message(message.from_user.id, "Ваши друзья:",
                                   reply_markup=show_friends(friends[0][0].split(',')[1:]))
        else:
            await bot.send_message(message.from_user.id, "У вас нет друзей")
    else:
        await bot.send_message(message.from_user.id, "Вы не зарегестрированы")


@dp.message_handler(commands=["black_list"], state=None)
async def show_black_list(message: types.Message):
    if db.id_exists(message.from_user.id):
        if len(db.get_black_list(message.from_user.id)) > 1:
            await bot.send_message(message.from_user.id, "Ваш черный список:", reply_markup=black_list_kb(message.from_user.id))
        else:
            msg = await bot.send_message(message.from_user.id, "Ваш черный список пуст")
            await asyncio.sleep(2)
            await msg.delete()
            await message.delete()
    else:
        await bot.send_message(message.from_user.id, "Вы не зарегестрированы")


@dp.callback_query_handler(Text(startswith="exclude"), state=None)
async def exclude(callback: types.CallbackQuery):
    user = callback.data.split("-")[1]
    if db.user_in_black_list(callback.from_user.id, user):
        db.delete_from_black_list(callback.from_user.id, user)
        await callback.answer("Пользователь удален из черного списка")
    else:
        await callback.answer("Пользователь уже удален из черного списка")
    await bot.delete_message(chat_id=callback.from_user.id, message_id=callback.message.message_id)


@dp.callback_query_handler(Text(startswith="hide"))
async def hide(callback: types.CallbackQuery):
    await bot.delete_message(chat_id=callback.from_user.id, message_id=callback.message.message_id)
    await callback.answer("Скрыть")


@dp.message_handler(commands=['register'], state=None)
async def register(message: types.Message):
    if db.id_exists(message.from_user.id):
        await bot.send_message(message.from_user.id, "Вы уже зарегестрированы")
    else:
        await bot.send_message(message.from_user.id, "Введите ник", reply_markup=cancel_kb())
        await Reg.nickname.set()


@dp.message_handler(state=Reg.nickname)
async def nickname(message: types.Message, state: FSMContext):
    if not db.user_exists(message.text):
        db.add_user(message.from_user.id, message.text)
        await bot.send_message(message.from_user.id, "Готово", reply_markup=main_kb())
        await state.finish()
    else:
        await bot.send_message(message.from_user.id, "Данный ник уже занят", reply_markup=cancel_kb())


@dp.message_handler(commands=['black_list_add'], state=None)
async def user_id(message: types.Message):
    if db.id_exists(message.from_user.id):
        await bot.send_message(message.from_user.id, "Введите ник", reply_markup=cancel_kb())
        await Add_to_black_list.user.set()
    else:
      await bot.send_message(message.from_user.id, "Вы не зарегестрированы")


@dp.message_handler(state=Add_to_black_list.user)
async def add_black_list(message: types.Message, state: FSMContext):
    if db.user_exists(message.text):
        user = db.get_user_id(message.text)[0][0]
        if not db.user_in_black_list(message.from_user.id, user):
            db.add_to_black_list(message.from_user.id, user)
            await bot.send_message(message.from_user.id, "Пользователь добавлен в ченый список", reply_markup=main_kb())
            if db.user_in_friends(message.from_user.id, user):
                db.kick_friend(message.from_user.id, user)
        else:
            await bot.send_message(message.from_user.id, "Пользователь уже в черном списке", reply_markup=main_kb())
        await state.finish()
    else:
        await bot.send_message(message.from_user.id, "Пользователь не найден", reply_markup=cancel_kb())


@dp.message_handler(commands=['add'], state=None)
async def add(message: types.Message):
    if db.id_exists(message.from_user.id):
        await bot.send_message(message.from_user.id, "Введите ник", reply_markup=cancel_kb())
        await Add_friends.nickname.set()
    else:
        await bot.send_message(message.from_user.id, "Вы не зарегестрированы")


@dp.message_handler(state=Add_friends.nickname)
async def nickname(message: types.Message, state: FSMContext):
    if db.user_exists(message.text):
        user_id = db.get_user_id(message.text)[0][0]
        if user_id != message.from_user.id:
            if str(user_id) in db.get_friends(message.from_user.id)[0][0].split(',')[1:]:
                await bot.send_message(message.from_user.id, "Пользователь уже у вас в друзьях")
            else:
                if not db.user_in_black_list(message.from_user.id, user_id):
                    if not db.user_in_black_list(user_id, message.from_user.id):
                        await bot.send_message(user_id, f"Запрос в друзья от {db.get_nickname(message.from_user.id)[0][0]}",
                                               reply_markup=friend_request(message.from_user.id))
                        await bot.send_message(message.from_user.id, "Запрос отправлен", reply_markup=main_kb())
                    else:
                        await bot.send_message(message.from_user.id, "Пользователь заблокировал вас", reply_markup=main_kb())
                else:
                    await bot.send_message(message.from_user.id, "Пользователь у вас в черном списке")
                await state.finish()
        else:
            await bot.send_message(message.from_user.id, "Вы не можете отправить запрос сами себе", reply_markup=cancel_kb())
    else:
        await bot.send_message(message.from_user.id, "Пользователь не найден", reply_markup=cancel_kb())


@dp.callback_query_handler(Text(startswith="response"), state=None)
async def response(callback: types.CallbackQuery):
    name = db.get_nickname(callback.from_user.id)
    if callback.data.split('-')[1] == "true":
        friends = db.get_friends(callback.from_user.id)
        if callback.data.split('-')[2] not in friends[0][0].split(',')[1:]:
            db.add_friend(callback.from_user.id, callback.data.split('-')[2])
            await callback.answer("Запрос принят")
            await bot.send_message(int(callback.data.split('-')[2]), f'{name[0][0]} принял(а) ваш запрос')
        else:
            await callback.answer("Пользователь уже в друзьях")
    else:
        await callback.answer("Запрос откланен")
    await bot.delete_message(chat_id=callback.from_user.id, message_id=callback.message.message_id)


@dp.callback_query_handler(Text(startswith="friend"), state=None)
async def fr(callback: types.CallbackQuery):
    name = db.get_nickname(callback.data.split('-')[1])[0][0]
    await callback.answer(name)
    await bot.send_message(callback.from_user.id, name,
                           reply_markup=friend(callback.data.split('-')[1]))
    await bot.delete_message(chat_id=callback.from_user.id, message_id=callback.message.message_id)


@dp.callback_query_handler(Text(startswith="kick"), state=None)
async def duel(callback: types.CallbackQuery):
    friends = db.get_friends(callback.from_user.id)
    if callback.data.split('-')[1] in friends[0][0].split(',')[1:]:
        db.kick_friend(callback.from_user.id, callback.data.split('-')[1])
        await callback.answer("Друг удален")
    else:
        await callback.answer("Друг уже удален")
    await bot.delete_message(chat_id=callback.from_user.id, message_id=callback.message.message_id)


@dp.callback_query_handler(Text(startswith="tic_tac_toe"), state=None)
async def tic(callback: types.CallbackQuery, state: FSMContext):
    status1 = db.get_status(callback.from_user.id)
    status2 = db.get_status(int(callback.data.split('-')[1]))
    if status1 != "Game" and status2 != "Game":
        if db.user_in_friends(callback.from_user.id, callback.data.split('-')[1]):
            db.edit_status(callback.from_user.id, "Game")
            await Tic_tac_toe.game.set()
            tic_tac_toe[str(callback.from_user.id)] = {"status": "wait", "players": [callback.from_user.id],
                                                      "board": [[0, 0, 0] for i in range(3)], "move": 0, "msg_id": [1, 1], "m": 0}
            async with state.proxy() as data:
                data["call"] = await bot.send_message(int(callback.data.split('-')[1]), f"Вызов в крестики-нолики от {db.get_nickname(callback.from_user.id)[0][0]}",
                                       reply_markup=tic_tac_toe_kb(callback.from_user.id))
                data["game"] = str(callback.from_user.id)
            await bot.send_message(callback.from_user.id, "Вызов отправлен", reply_markup=cancel_call())
        else:
            await callback.answer("Пользователь не у вас в друзьях")
    else:
        await bot.send_message(callback.from_user.id, "Игрок уже в игре")
    await bot.delete_message(chat_id=callback.from_user.id, message_id=callback.message.message_id)


@dp.callback_query_handler(Text(startswith="cancel_call"), state=[Tic_tac_toe.game, Word_game.game])
async def cancel(callback: types.CallbackQuery, state: FSMContext):
    try:
        if tic_tac_toe[str(callback.from_user.id)]["status"] == "wait":
            async with state.proxy() as data:
                await data["call"].delete()
            await state.finish()
            db.edit_status(callback.from_user.id, "None")
            await callback.answer("Вызов отменен")
            await bot.delete_message(chat_id=callback.from_user.id, message_id=callback.message.message_id)
    except:
        pass


@dp.callback_query_handler(Text(startswith="tic_response"), state=None)
async def rsp(callback: types.CallbackQuery, state: FSMContext):
    if callback.data.split('-')[1] == "true":
        status1 = db.get_status(callback.from_user.id)
        if status1 != "Game":
            db.edit_status(callback.from_user.id, "Game")
            await Tic_tac_toe.game.set()
            tic_tac_toe[callback.data.split('-')[2]]["status"] = "game"
            x = tic_tac_toe[callback.data.split('-')[2]]["players"]
            x.append(callback.from_user.id)
            tic_tac_toe[callback.data.split('-')[2]]["players"] = x
            msg1 = await bot.send_message(tic_tac_toe[callback.data.split('-')[2]]["players"][0], "Игра началась",
                                          reply_markup=tic_tac_toe_board(tic_tac_toe[callback.data.split('-')[2]]["board"],
                                                                  callback.data.split('-')[2]))
            msg2 = await bot.send_message(callback.from_user.id, "Игра началась",
                                          reply_markup=tic_tac_toe_board(tic_tac_toe[callback.data.split('-')[2]]["board"],
                                                                  callback.data.split('-')[2]))
            tic_tac_toe[callback.data.split('-')[2]]["msg_id"] = [msg1.message_id, msg2.message_id]
            await bot.delete_message(chat_id=callback.from_user.id, message_id=callback.message.message_id)
            async with state.proxy() as data:
                data["game"] = str([callback.data.split('-')[1]])


@dp.callback_query_handler(Text(startswith="tic_game"), state=Tic_tac_toe.game)
async def response(callback: types.CallbackQuery, state: FSMContext):
    move = tic_tac_toe[callback.data.split('-')[1]]["move"]
    if tic_tac_toe[callback.data.split('-')[1]]["players"][move] == callback.from_user.id:
        x = int(callback.data.split('-')[2])
        y = int(callback.data.split('-')[3])
        if tic_tac_toe[callback.data.split('-')[1]]["board"][x][y] == 0:
            tic_tac_toe[callback.data.split('-')[1]]["board"][x][y] = move + 1
            tic_tac_toe[callback.data.split('-')[1]]["move"] = (move + 1) % 2
            tic_tac_toe[callback.data.split('-')[1]]["m"] += 1
            t = check(tic_tac_toe[callback.data.split('-')[1]]["board"])
            id1 = tic_tac_toe[callback.data.split('-')[1]]["players"][0]
            id2 = tic_tac_toe[callback.data.split('-')[1]]["players"][1]
            if not t:
                await bot.edit_message_text("Игра началась:", id1, tic_tac_toe[callback.data.split('-')[1]]["msg_id"][0],
                                            reply_markup=tic_tac_toe_board(tic_tac_toe[callback.data.split('-')[1]]["board"], id1))
                await bot.edit_message_text("Игра началась:", id2, tic_tac_toe[callback.data.split('-')[1]]["msg_id"][1],
                                            reply_markup=tic_tac_toe_board(tic_tac_toe[callback.data.split('-')[1]]["board"], id1))
            else:
                kb = exit_kb()
                if t == -1:
                    await bot.edit_message_text(f"Игра окончена, ничья", id1,
                                                tic_tac_toe[callback.data.split('-')[1]]["msg_id"][0], reply_markup=kb)
                    await bot.edit_message_text(f"Игра окончена, ничья", id2,
                                                tic_tac_toe[callback.data.split('-')[1]]["msg_id"][1], reply_markup=kb)
                else:
                    winner = db.get_nickname([id1, id2][t - 1])[0][0]
                    await bot.edit_message_text(f"Игра окончена, победитель: {winner}", id1, tic_tac_toe[callback.data.split('-')[1]]["msg_id"][0], reply_markup=kb)
                    await bot.edit_message_text(f"Игра окончена, победитель: {winner}", id2, tic_tac_toe[callback.data.split('-')[1]]["msg_id"][1], reply_markup=kb)
                    tic_tac_toe.pop(callback.data.split('-')[1])
        else:
            await callback.answer("Вы не можете ходить сюда")
    else:
        await callback.answer("Сейчас не ваш ход")


@dp.callback_query_handler(Text(startswith="exit"), state=[Tic_tac_toe.game, Word_game.game])
async def exit(callback: types.CallbackQuery, state: FSMContext):
    await bot.delete_message(chat_id=callback.from_user.id, message_id=callback.message.message_id)
    db.edit_status(callback.from_user.id, "None")
    await callback.answer("Выход")
    msg = await bot.send_message(callback.from_user.id, "Выход", reply_markup=main_kb())
    await state.finish()


@dp.callback_query_handler(Text(startswith="words_v"), state=None)
async def word_g(callback: types.CallbackQuery, state: FSMContext):
    status1 = db.get_status(callback.from_user.id)
    status2 = db.get_status(int(callback.data.split('-')[1]))
    if status1 != "Game" and status2 != "Game":
        db.edit_status(callback.from_user.id, "Game")
        await Word_game.game.set()
        tic_tac_toe[str(callback.from_user.id)] = {"status": "wait", "players": [callback.from_user.id],
                                                  "word": random.choice(words)[0], "move": 0, "msg_id": [1, 1],
                                                   "p_words": [], "m": 0}
        async with state.proxy() as data:
            data["call"] = await bot.send_message(int(callback.data.split('-')[1]), f"Вызов в слова от {db.get_nickname(callback.from_user.id)[0][0]}",
                                   reply_markup=words_kb(callback.from_user.id))
            data["game"] = str(callback.from_user.id)
            data["id"] = callback.from_user.id
        await bot.send_message(callback.from_user.id, "Вызов отправлен", reply_markup=cancel_call())
    else:
        await bot.send_message(callback.from_user.id, "Игрок уже в игре")
    await bot.delete_message(chat_id=callback.from_user.id, message_id=callback.message.message_id)


@dp.callback_query_handler(Text(startswith="words_response"), state=None)
async def rsp(callback: types.CallbackQuery, state: FSMContext):
    if callback.data.split('-')[1] == "true":
        status1 = db.get_status(callback.from_user.id)
        if status1 != "Game":
            db.edit_status(callback.from_user.id, "Game")
            await Word_game.game.set()
            async with state.proxy() as data:
                data["id"] = callback.data.split('-')[2]
            tic_tac_toe[callback.data.split('-')[2]]["status"] = "game"
            x = tic_tac_toe[callback.data.split('-')[2]]["players"]
            x.append(callback.from_user.id)
            tic_tac_toe[callback.data.split('-')[2]]["players"] = x
            msg1 = await bot.send_message(tic_tac_toe[callback.data.split('-')[2]]["players"][0], "Игра началась")
            msg2 = await bot.send_message(callback.from_user.id, "Игра началась")
            tic_tac_toe[callback.data.split('-')[2]]["msg_id"] = [msg1.message_id, msg2.message_id]
            await bot.delete_message(chat_id=callback.from_user.id, message_id=callback.message.message_id)
            async with state.proxy() as data:
                data["game"] = str([callback.data.split('-')[2]][0])


@dp.message_handler(state=Word_game.game)
async def word_game(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        id = str(data["id"])
    list = tic_tac_toe[id]
    move = list["move"]
    id1 = list["players"][0]
    id2 = list["players"][1]
    if list["players"][move] == message.from_user.id:
        if len(message.text) == 5 and message.text.lower() in words:
            if message.text.lower() != list["word"]:
                print(list["word"])
                tic_tac_toe[id]["move"] = (move + 1) % 2
                tic_tac_toe[id]["m"] += 1
                c = list["p_words"]
                c.append(message.text.lower())
                tic_tac_toe[id]["p_words"] = c
                await bot.edit_message_text("Игра началась. Список слов:", id1, list["msg_id"][0],
                                            reply_markup=words_game(c, list["word"]))
                await bot.edit_message_text("Игра началась. Список слов:", id2, list["msg_id"][1],
                                            reply_markup=words_game(c, list["word"]))
            else:
                kb = exit_kb()
                winner = db.get_nickname(list['players'][move])[0][0]
                await bot.edit_message_text(f"Игра окончена, победитель: {winner}", id1,
                                            list["msg_id"][0], reply_markup=kb)
                await bot.edit_message_text(f"Игра окончена, победитель: {winner}", id2,list["msg_id"][1], reply_markup=kb)
                tic_tac_toe.pop(id)
        else:
            await bot.send_message(message.from_user.id, "Введите слово из 5 букв")
    await message.delete()


async def delete_game(game_id, list):
    await asyncio.sleep(10)
    try:
        game = tic_tac_toe[game_id]
        if id(game) == id(list):
            if game["m"] == list["m"]:
                await bot.send_message(list['players'][0], "Игра была отменена", reply_markup=exit_kb())
                await bot.send_message(list['players'][1], "Игра была отменена", reply_markup=exit_kb())
                tic_tac_toe.pop(game_id)
    except:
        pass


executor.start_polling(dp, skip_updates=True)