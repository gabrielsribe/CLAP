import os
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import List, Dict

import json
from sqlitedict import SqliteDict


class RepositoryError(Exception):
    pass


class InvalidEntryError(RepositoryError):
    pass


class Repository(ABC):
    repository_name: str = 'AbstractRepository'
    extension: str = ''

    def __init__(self, repository_path: str, commit_on_close: bool = True):
        self.repository_path = repository_path
        self.commit_on_close = commit_on_close

    @contextmanager
    @abstractmethod
    def connect(self, table_name: str) -> 'Repository':
        pass

    @abstractmethod
    def open(self, table_name: str):
        pass

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def commit(self):
        pass

    @abstractmethod
    def keys(self) -> List[str]:
        pass

    @abstractmethod
    def upsert(self, key: str, obj: dict):
        pass

    @abstractmethod
    def update(self, key: str, update_obj: dict):
        pass

    @abstractmethod
    def get(self, key: str) -> Dict[str, dict]:
        pass

    @abstractmethod
    def get_multiple(self, key: List[str]) -> dict:
        pass

    @abstractmethod
    def get_all(self) -> Dict[str, dict]:
        pass

    @abstractmethod
    def remove(self, key: str):
        pass

    @abstractmethod
    def remove_multiple(self, keys: List[str]):
        pass

    @abstractmethod
    def clear(self):
        pass


class SQLiteRepository(Repository):
    repository_name: str = 'sqlite'
    extension: str = '.db'

    def __init__(self, repository_path: str, commit_on_close: bool = True):
        super().__init__(repository_path, commit_on_close=commit_on_close)
        self.sqlite_repository = None
        self.table_name = None

    @contextmanager
    def connect(self, table_name: str) -> 'SQLiteRepository':
        yield self.open(table_name)
        self.close()

    def open(self, table_name: str):
        self.sqlite_repository = SqliteDict(self.repository_path, tablename=table_name, encode=json.dumps,
                                            decode=json.loads)
        self.table_name = table_name
        return self

    def close(self):
        if self.sqlite_repository:
            if self.commit_on_close:
                self.commit()
            self.sqlite_repository.close()
        self.sqlite_repository = None
        self.table_name = None

    def commit(self):
        self.sqlite_repository.commit()

    def keys(self) -> List[str]:
        return list(self.sqlite_repository.keys())

    def update(self, key: str, update_obj: dict):
        obj = self.sqlite_repository[key] = obj

    def upsert(self, key: str, obj: dict):
        self.sqlite_repository[key] = obj

    def get(self, key: str) -> dict:
        try:
            return self.sqlite_repository[key]
        except KeyError:
            raise InvalidEntryError(key)

    def get_multiple(self, keys: List[str]) -> Dict[str, dict]:
        values = {key: element for key, element in self.sqlite_repository.items() if key in keys}
        if len(set(keys)) != len(values):
            invalids = set(keys).difference(values.keys())
            raise InvalidEntryError(', '.join(list(invalids)))
        return values

    def get_all(self) -> Dict[str, dict]:
        return {key: element for key, element in self.sqlite_repository.items()}

    def remove(self, key: str):
        try:
            del self.sqlite_repository[key]
        except KeyError:
            raise InvalidEntryError(key)

    def remove_multiple(self, keys: List[str]):
        for key in keys:
            self.remove(key)

    def clear(self):
        self.sqlite_repository.clear()

    def __repr__(self):
        return f"SQLiteRepository(file='{self.repository_path}', open={self.sqlite_repository is not None}, " \
               f"table='{self.table_name}')"


class RepositoryController:
    def __init__(self, repository: Repository, metadata_table: str = '__meta__'):
        self.repository = repository
        self.metadata_table = metadata_table

    def increment_key(self, key: str) -> int:
        with self.repository.connect(self.metadata_table) as db:
            try:
                value_dict = db.get(key)
                index = value_dict.get('value', -1) + 1
            except InvalidEntryError:
                index = 0
            db.upsert(key, {'value': index})
            return index

    def reset_index(self, key: str, value: int = -1):
        with self.repository.connect(self.metadata_table) as db:
            db.upsert(key, {'value': value})

    def __repr__(self):
        return f"RepositoryOperator(repository={self.repository})"
