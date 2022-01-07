from __future__ import annotations

import sqlite3
from abc import ABC, abstractmethod
from collections import defaultdict
from threading import Lock
from typing import TYPE_CHECKING, Optional, cast, Set, Dict, List, Tuple, Any

from isisdl.settings import database_file_location, set_database_to_memory

if TYPE_CHECKING:
    from isisdl.backend.request_helper import PreMediaContainer, Course


class SQLiteDatabase(ABC):
    lock: Lock = Lock()

    def __init__(self) -> None:
        from isisdl.backend.utils import path
        if set_database_to_memory:
            self.con = sqlite3.connect(":memory:", check_same_thread=False)
        else:
            self.con = sqlite3.connect(path(database_file_location), check_same_thread=False)

        self.cur = self.con.cursor()

        self.create_default_tables()

    @abstractmethod
    def create_default_tables(self) -> None:
        ...

    def get_state(self) -> List[Tuple[Any]]:
        res: List[Any] = []
        with self.lock:
            names = self.cur.execute("""SELECT name FROM sqlite_master where type = 'table' """).fetchall()
            for name in names:
                res.append(self.cur.execute(f"""SELECT * FROM {name[0]}""").fetchall())

        return res


class DatabaseHelper(SQLiteDatabase):
    def create_default_tables(self) -> None:
        with self.lock:
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS fileinfo
                (name text, file_id text primary key unique, url text, time int, course_id int, checksum text, size int)
            """)

            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS courseinfo
                (name text, id int primary key)
            """)

    def _get_attr_by_equal(self, attr: str, eq_val: str, eq_name: str = "file_id", table: str = "fileinfo") -> Any:
        with DatabaseHelper.lock:
            res = self.cur.execute(f"""SELECT {attr} FROM {table} WHERE {eq_name} = ?""", (eq_val,)).fetchone()

        if res is None:
            return None

        return res[0]

    def get_name_by_checksum(self, checksum: str) -> Optional[str]:
        return cast(Optional[str], self._get_attr_by_equal("name", checksum, "checksum"))

    def get_course_id_by_name(self, course_name: str) -> Optional[int]:
        return cast(Optional[int], self._get_attr_by_equal("id", course_name, "name", "courseinfo"))

    def get_size_from_file_id(self, file_id: str) -> Optional[int]:
        return cast(Optional[int], self._get_attr_by_equal("size", file_id))

    def get_course_name_and_ids(self) -> List[Tuple[str, int]]:
        with DatabaseHelper.lock:
            return self.cur.execute("""SELECT * FROM courseinfo""").fetchall()

    def delete_by_file_id(self, file_id: str) -> None:
        with DatabaseHelper.lock:
            self.cur.execute("""DELETE FROM fileinfo WHERE file_id = ?""", (file_id,))
            self.con.commit()

    def add_pre_container(self, file: PreMediaContainer) -> None:
        with DatabaseHelper.lock:
            self.cur.execute("""
                INSERT OR REPLACE INTO fileinfo values (?, ?, ?, ?, ?, ?, ?)
            """, (file.name, file.file_id, file.url, int(file.time.timestamp()), file.course_id, file.checksum, file.size))
            self.con.commit()

    def add_course(self, course: Course) -> None:
        with DatabaseHelper.lock:
            self.cur.execute("""
                INSERT OR IGNORE INTO courseinfo values (?, ?)
            """, (course.name, course.course_id))
            self.con.commit()

    def get_checksums_per_course(self) -> Dict[str, Set[str]]:
        ret = defaultdict(set)
        with DatabaseHelper.lock:
            for course_name, checksum in self.cur.execute("""SELECT courseinfo.name, checksum from fileinfo INNER JOIN courseinfo on fileinfo.course_id = courseinfo.id""").fetchall():
                ret[course_name].add(checksum)

        return ret


class ConfigHelper(SQLiteDatabase):
    def create_default_tables(self) -> None:
        with self.lock:
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS config
                (key text unique, value text);
            """)

    def _set(self, key: str, value: str) -> None:
        with self.lock:
            self.cur.execute("""
                INSERT OR REPLACE INTO config values (?, ?)
            """, (key, value))
            self.con.commit()

    def _get(self, key: str) -> Optional[str]:
        with self.lock:
            res = self.cur.execute("SELECT value FROM config where key = ?", (key,)).fetchone()
            if res is None:
                return None

            assert isinstance(res[0], str)
            return res[0]

    def set_user(self, username: str) -> None:
        self._set("username", username)

    def set_clear_password(self, password: str) -> None:
        return self._set("clear_password", password)

    def set_encrypted_password(self, password: str) -> None:
        return self._set("encrypted_password", password)

    def get_user(self) -> Optional[str]:
        return self._get("username")

    def get_clear_password(self) -> Optional[str]:
        return self._get("clear_password")

    def get_encrypted_password(self) -> Optional[str]:
        return self._get("encrypted_password")

    #

    @staticmethod
    def default_filename_scheme() -> str:
        return "0"

    def set_filename_scheme(self, num: str) -> None:
        self._set("filename_scheme", num)

    def get_filename_scheme(self) -> str:
        return self._get("filename_scheme") or self.default_filename_scheme()

    #

    @staticmethod
    def default_throttle_rate() -> None:
        return None

    def set_throttle_rate(self, num: Optional[str]) -> None:
        if num is not None:
            self._set("throttle_rate", num)

    def get_throttle_rate(self) -> Optional[int]:
        value = self._get("throttle_rate") or self.default_throttle_rate()
        if value is not None:
            return int(value)

        return None

    #

    @staticmethod
    def default_update_policy() -> str:
        return "0"

    def get_update_policy(self) -> str:
        return self._get("update_policy") or self.default_update_policy()

    def set_update_policy(self, value: str) -> None:
        self._set("update_policy", value)

    #

    @staticmethod
    def default_telemetry() -> str:
        return "1"

    def set_telemetry(self, num: str) -> None:
        self._set("telemetry", num)

    def get_telemetry(self) -> str:
        return self._get("telemetry") or self.default_telemetry()

    #

    def set_other_files_in_working_location(self, value: str) -> None:
        self._set("other_files", value)

    def get_other_files_in_working_location(self) -> Optional[str]:
        return self._get("other_files")

    #

    def delete_config(self) -> None:
        with self.lock:
            self.cur.execute("""
                DROP table config
            """)

        self.create_default_tables()