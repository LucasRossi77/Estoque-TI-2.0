import os
import re
import sqlite3


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(BASE_DIR, "database.db")


def get_db_backend():
    return os.getenv("DB_BACKEND", "sqlite").strip().lower()


def using_mysql():
    return get_db_backend() == "mysql"


def _validate_identifier(name):
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name or ""):
        raise ValueError(f"Identificador de banco invalido: {name!r}")
    return name


class DatabaseRow:
    def __init__(self, values, columns):
        self._values = tuple(values)
        self._columns = [col[0] if isinstance(col, (tuple, list)) else col for col in columns]
        self._index = {name: idx for idx, name in enumerate(self._columns)}

    def __getitem__(self, key):
        if isinstance(key, str):
            return self._values[self._index[key]]
        return self._values[key]

    def __iter__(self):
        return iter(self._values)

    def __len__(self):
        return len(self._values)

    def __contains__(self, key):
        return key in self._index

    def keys(self):
        return list(self._columns)

    def values(self):
        return list(self._values)

    def items(self):
        return [(key, self[key]) for key in self._columns]

    def get(self, key, default=None):
        return self[key] if key in self._index else default

    def __repr__(self):
        return repr(dict(self.items()))


class MySQLCursorAdapter:
    def __init__(self, cursor):
        self._cursor = cursor

    def execute(self, sql, params=None):
        return self._cursor.execute(sql.replace("?", "%s"), params or ())

    def executemany(self, sql, params):
        return self._cursor.executemany(sql.replace("?", "%s"), params)

    def fetchone(self):
        row = self._cursor.fetchone()
        if row is None:
            return None
        return DatabaseRow(row, self._cursor.description or [])

    def fetchall(self):
        rows = self._cursor.fetchall()
        columns = self._cursor.description or []
        return [DatabaseRow(row, columns) for row in rows]

    def close(self):
        return self._cursor.close()

    @property
    def description(self):
        return self._cursor.description

    @property
    def lastrowid(self):
        return self._cursor.lastrowid

    @property
    def rowcount(self):
        return self._cursor.rowcount


class MySQLConnectionAdapter:
    def __init__(self, connection):
        self._connection = connection

    def cursor(self):
        return MySQLCursorAdapter(self._connection.cursor())

    def commit(self):
        return self._connection.commit()

    def rollback(self):
        return self._connection.rollback()

    def close(self):
        return self._connection.close()


def _mysql_config(database=True):
    config = {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", ""),
        "charset": "utf8mb4",
        "autocommit": False,
    }
    if database:
        config["database"] = os.getenv("MYSQL_DATABASE") or os.getenv("MYSQL_DB") or "estoque"
    return config


def _connect_mysql():
    try:
        import pymysql
    except ImportError as exc:
        raise RuntimeError(
            "DB_BACKEND=mysql exige a dependencia PyMySQL. "
            "Instale com: pip install PyMySQL"
        ) from exc

    try:
        return MySQLConnectionAdapter(pymysql.connect(**_mysql_config()))
    except pymysql.err.OperationalError as exc:
        database = _mysql_config()["database"]
        if exc.args and exc.args[0] == 1049 and os.getenv("MYSQL_AUTO_CREATE_DATABASE") == "1":
            server_conn = pymysql.connect(**_mysql_config(database=False))
            try:
                with server_conn.cursor() as cursor:
                    safe_database = _validate_identifier(database)
                    cursor.execute(
                        f"CREATE DATABASE IF NOT EXISTS `{safe_database}` "
                        "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                    )
                server_conn.commit()
            finally:
                server_conn.close()
            return MySQLConnectionAdapter(pymysql.connect(**_mysql_config()))
        if exc.args and exc.args[0] == 2003:
            host = _mysql_config()["host"]
            port = _mysql_config()["port"]
            raise RuntimeError(
                f"Nao foi possivel conectar ao MySQL em {host}:{port}. "
                "Verifique se o MySQL Server esta instalado e em execucao. "
                "Para usar o SQLite local, remova DB_BACKEND=mysql ou execute apenas: python main.py"
            ) from exc
        raise


def connect():
    if using_mysql():
        return _connect_mysql()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_table_columns(table_name):
    table_name = _validate_identifier(table_name)
    conn = connect()
    cursor = conn.cursor()
    try:
        if using_mysql():
            cursor.execute(f"SHOW COLUMNS FROM `{table_name}`")
            return [row[0] for row in cursor.fetchall()]

        cursor.execute(f"PRAGMA table_info({table_name})")
        return [row[1] for row in cursor.fetchall()]
    finally:
        conn.close()


def is_integrity_error(exc):
    if isinstance(exc, sqlite3.IntegrityError):
        return True
    return exc.__class__.__name__ == "IntegrityError"


def is_unique_constraint_error(exc):
    if isinstance(exc, sqlite3.IntegrityError):
        return True
    return exc.__class__.__name__ == "IntegrityError" or (exc.args and exc.args[0] == 1062)
