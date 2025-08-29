"""Implement LRFU Cache"""

import sqlite3
import hashlib
import time
from threading import Lock
from typing import Optional


class LRFUCache:
    """LRFU Cache"""
    def __init__(self, db_path: str = "proxy_cache.db", max_entries: int = 1000):
        self.db_path = db_path
        self.max_entries = max_entries
        self.lock = Lock()
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS cache (
                    id INTEGER PRIMARY KEY,
                    key TEXT UNIQUE,
                    response BLOB,
                    hits INTEGER DEFAULT 1,
                    last_access REAL
                )
            ''')
            conn.commit()

    def _make_key(self, method: str, url: str, headers: dict, body: bytes) -> str:
        """Make key"""
        relevant_headers = {k.lower(): v for k, v in headers.items() if k.lower() not in ("user-agent", "date")}
        raw = method.upper() + url + str(sorted(relevant_headers.items())) + body.decode("utf-8", errors="ignore")
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, method: str, url: str, headers: dict, body: bytes) -> Optional[bytes]:
        """Get data"""
        key = self._make_key(method, url, headers, body)
        with self.lock, sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("SELECT response, hits, last_access FROM cache WHERE key = ?", (key,))
            row = cur.fetchone()
            if row:
                response, hits, _ = row
                conn.execute("UPDATE cache SET hits = ?, last_access = ? WHERE key = ?",
                             (hits + 1, time.time(), key))
                conn.commit()
                return response
            return None

    def set(self, method: str, url: str, headers: dict, body: bytes, response: bytes):
        """Set data"""
        key = self._make_key(method, url, headers, body)
        now = time.time()
        with self.lock, sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO cache (key, response, hits, last_access)
                VALUES (?, ?, COALESCE((SELECT hits FROM cache WHERE key = ?), 0) + 1, ?)
            """, (key, response, key, now))
            conn.commit()
            self._evict_if_needed(conn)

    def _evict_if_needed(self, conn: sqlite3.Connection):
        """Remove if needed"""
        cur = conn.execute("SELECT COUNT(*) FROM cache")
        count = cur.fetchone()[0]
        if count > self.max_entries:
            conn.execute("""
                DELETE FROM cache
                WHERE id IN (
                    SELECT id FROM cache
                    ORDER BY (hits / (strftime('%s','now') - last_access + 1.0)) ASC
                    LIMIT ?
                )
            """, (count - self.max_entries,))
            conn.commit()
