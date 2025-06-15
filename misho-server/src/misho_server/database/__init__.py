import sqlite3

from misho_server.config import CONFIG


class SqliteDatabaseConnection:
    def __init__(self, db_path: str):
        self.connection = sqlite3.connect(db_path)
        self.connection.execute("PRAGMA foreign_keys = ON;")
        self.cursor = self.connection.cursor()

    def close(self):
        self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.connection.close()


class SqliteDatabase:
    def __init__(self):
        self._db_path = CONFIG.database_path

    def connect(self):
        return SqliteDatabaseConnection(self._db_path)
