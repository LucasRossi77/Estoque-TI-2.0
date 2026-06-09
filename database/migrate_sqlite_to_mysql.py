import os
import sqlite3

from database.connection import DB_PATH, connect
from database.create_tables import create_tables


TABLES = ("usuarios", "itens", "movimentacoes")


def migrate():
    os.environ["DB_BACKEND"] = "mysql"
    create_tables()

    sqlite_conn = sqlite3.connect(DB_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    mysql_conn = connect()

    try:
        for table in TABLES:
            rows = sqlite_conn.execute(f"SELECT * FROM {table}").fetchall()
            if not rows:
                print(f"{table}: sem registros para migrar.")
                continue

            columns = rows[0].keys()
            column_list = ", ".join(columns)
            placeholders = ", ".join("?" for _ in columns)
            values = [tuple(row[column] for column in columns) for row in rows]

            cursor = mysql_conn.cursor()
            cursor.executemany(
                f"INSERT IGNORE INTO {table} ({column_list}) VALUES ({placeholders})",
                values,
            )
            mysql_conn.commit()
            print(f"{table}: {len(values)} registro(s) enviados ao MySQL.")
    finally:
        sqlite_conn.close()
        mysql_conn.close()


if __name__ == "__main__":
    migrate()
