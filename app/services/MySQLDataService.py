from __future__ import annotations

import os

import pymysql
import pymysql.cursors

from .AbstractBaseDataService import AbstractBaseDataService


class MySQLDataService(AbstractBaseDataService):
    """Persists records in a MySQL table. Config keys: `table`, `primary_key_field` (default `id`),
    and optionally `host`, `port`, `user`, `password`, `database` (fall back to env vars)."""

    def __init__(self, config: dict) -> None:
        super().__init__(config)
        self._table = config["table"]
        self._primary_key_field = str(config.get("primary_key_field", "id"))
        self._host = str(config.get("host", os.getenv("MYSQL_HOST", "localhost")))
        self._port = int(config.get("port", os.getenv("MYSQL_PORT", 3306)))
        self._user = str(config.get("user", os.getenv("MYSQL_USER", "root")))
        self._password = str(config.get("password", os.getenv("MYSQL_PASSWORD", "")))
        self._database = str(config.get("database", os.getenv("MYSQL_DATABASE", "classicmodels")))

    def _get_connection(self) -> pymysql.connections.Connection:
        return pymysql.connect(
            host=self._host,
            port=self._port,
            user=self._user,
            password=self._password,
            database=self._database,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
        )

    def retrieveByPrimaryKey(self, primary_key: str) -> dict:
        sql = f"SELECT * FROM `{self._table}` WHERE `{self._primary_key_field}` = %s"
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, (primary_key,))
                row = cursor.fetchone()
        finally:
            conn.close()
        return dict(row) if row else {}

    def retrieveByTemplate(self, template: dict) -> list[dict]:
        if template:
            conditions = " AND ".join(f"`{k}` = %s" for k in template)
            sql = f"SELECT * FROM `{self._table}` WHERE {conditions}"
            params: tuple = tuple(template.values())
        else:
            sql = f"SELECT * FROM `{self._table}`"
            params = ()
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                rows = cursor.fetchall()
        finally:
            conn.close()
        return [dict(row) for row in rows]

    def create(self, payload: dict) -> str:
        columns = ", ".join(f"`{k}`" for k in payload)
        placeholders = ", ".join("%s" for _ in payload)
        sql = f"INSERT INTO `{self._table}` ({columns}) VALUES ({placeholders})"
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, tuple(payload.values()))
                pk = payload.get(self._primary_key_field)
                if pk is None:
                    pk = cursor.lastrowid
        finally:
            conn.close()
        return str(pk)

    def updateByPrimaryKey(self, primary_key: str, payload: dict) -> int:
        update_data = {k: v for k, v in payload.items() if k != self._primary_key_field}
        if not update_data:
            return 0
        assignments = ", ".join(f"`{k}` = %s" for k in update_data)
        sql = f"UPDATE `{self._table}` SET {assignments} WHERE `{self._primary_key_field}` = %s"
        params = (*update_data.values(), primary_key)
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                return cursor.rowcount
        finally:
            conn.close()

    def deleteByPrimaryKey(self, primary_key: str) -> int:
        sql = f"DELETE FROM `{self._table}` WHERE `{self._primary_key_field}` = %s"
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, (primary_key,))
                return cursor.rowcount
        finally:
            conn.close()
