from aiogram.dispatcher.filters.state import State, StatesGroup


class Reg(StatesGroup):
    nickname = State()


class Add_friends(StatesGroup):
    nickname = State()


class Tic_tac_toe(StatesGroup):
    game = State()


class Word_game(StatesGroup):
    game = State()


class Add_to_black_list(StatesGroup):
    user = State()
