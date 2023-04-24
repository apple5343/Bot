import sqlite3


class Databases:
    def __init__(self, db_file):
        self.connection = sqlite3.connect(db_file)
        self.cursor = self.connection.cursor()

    def user_exists(self, nickname):
        with self.connection:
            result = self.cursor.execute("SELECT * FROM 'players' WHERE nickname = ?", (nickname,)).fetchall()
            return bool(len(result))

    def add_user(self, user_id, nickname):
        with self.connection:
            self.cursor.execute("INSERT INTO 'players' ('user_id', 'nickname', 'elo', 'friends', 'status', 'black_list') VALUES (?, ?, ?, ?, ?, ?)", (user_id, nickname, 1000, "1", "", "1"))

    def id_exists(self, id):
        with self.connection:
            result = self.cursor.execute("SELECT * FROM 'players' WHERE user_id = ?", (id,)).fetchall()
            return bool(len(result))

    def get_user_id(self, nickname):
        with self.connection:
            result = self.cursor.execute("SELECT user_id FROM 'players' WHERE nickname = ?", (nickname,)).fetchall()
            return result

    def get_nickname(self, user_id):
        with self.connection:
            result = self.cursor.execute("SELECT nickname FROM 'players' WHERE user_id = ?", (user_id,)).fetchall()
            return result

    def add_friend(self, user_id1, user_id2):
        with self.connection:
            result1 = self.cursor.execute("SELECT friends FROM 'players' WHERE user_id = ?", (user_id1,)).fetchall()
            result2 = self.cursor.execute("SELECT friends FROM 'players' WHERE user_id = ?", (user_id2,)).fetchall()
            self.cursor.execute("UPDATE players set friends = ? WHERE user_id = ?", (f"{result1[0][0]},{user_id2}",
                                                                                      user_id1,))
            self.cursor.execute("UPDATE players set friends = ? WHERE user_id = ?", (f"{result2[0][0]},{user_id1}",
                                                                                      user_id2,))

    def get_friends(self, user_id):
        with self.connection:
            result = self.cursor.execute("SELECT friends FROM 'players' WHERE user_id = ?", (user_id,)).fetchall()
            return result

    def get_status(self, user_id):
        with self.connection:
            result = self.cursor.execute("SELECT status FROM 'players' WHERE user_id = ?", (user_id,)).fetchall()
            return result[0][0]

    def kick_friend(self, user_id1, user_id2):
        with self.connection:
            result1 = self.cursor.execute("SELECT friends FROM 'players' WHERE user_id = ?", (int(user_id1),)).fetchall()[0][0].split(',')
            result2 = self.cursor.execute("SELECT friends FROM 'players' WHERE user_id = ?", (int(user_id2),)).fetchall()[0][0].split(',')
            result1.remove(str(user_id2))
            result2.remove(str(user_id1))
            result1 = ",".join(result2)
            result2 = ",".join(result1)
            self.cursor.execute("UPDATE players set friends = ? WHERE user_id = ?", (result1, int(user_id1),))
            self.cursor.execute("UPDATE players set friends = ? WHERE user_id = ?", (result2, int(user_id2),))

    def delete_all(self):
        with self.connection:
            self.cursor.execute("DELETE FROM 'players'")

    def edit_status(self, user_id, new):
        with self.connection:
            self.cursor.execute("UPDATE players set status = ? WHERE user_id = ?", (new, user_id,))

    def user_in_friends(self, id, user):
        with self.connection:
            result = self.cursor.execute("SELECT friends FROM 'players' WHERE user_id = ?", (id,)).fetchall()[0][0]
            return str(user) in str(result).split(",")

    def user_in_black_list(self, id, user):
        with self.connection:
            result = self.cursor.execute("SELECT black_list FROM 'players' WHERE user_id = ?", (id,)).fetchall()[0][0]
            return str(user) in result.split(",")

    def add_to_black_list(self, id, user):
        with self.connection:
            result1 = self.cursor.execute("SELECT black_list FROM 'players' WHERE user_id = ?", (id,)).fetchall()
            self.cursor.execute("UPDATE players set black_list = ? WHERE user_id = ?", (f"{result1[0][0]},{user}",
                                                                                      id,))

    def get_black_list(self, user_id):
        with self.connection:
            result = self.cursor.execute("SELECT black_list FROM 'players' WHERE user_id = ?", (user_id,)).fetchall()
            return result[0][0]

    def delete_from_black_list(self, id, user):
        with self.connection:
            result1 = self.cursor.execute("SELECT black_list FROM 'players' WHERE user_id = ?", (int(id),)).fetchall()[0][0].split(',')
            result1.remove(str(user))
            result1 = ",".join(result1)
            self.cursor.execute("UPDATE players set black_list = ? WHERE user_id = ?", (result1, int(id),))