"""SQLite 캐시: api_cache / llm_cache / pipeline_runs / stock_evaluations."""
from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS api_cache (
  key TEXT PRIMARY KEY, source TEXT NOT NULL, payload TEXT NOT NULL, created_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS llm_cache (
  key TEXT PRIMARY KEY, payload TEXT NOT NULL, created_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS pipeline_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT, quarter TEXT NOT NULL, as_of TEXT,
  status TEXT NOT NULL, started_at REAL NOT NULL, finished_at REAL, note TEXT);
CREATE TABLE IF NOT EXISTS stock_evaluations (
  run_id INTEGER NOT NULL, ticker TEXT NOT NULL, payload TEXT NOT NULL,
  PRIMARY KEY (run_id, ticker));
"""

DAY = 86400.0


def make_key(*parts: object) -> str:
    """요청 파라미터 해시 키. 딕셔너리는 키 정렬 후 직렬화한다."""
    raw = json.dumps(parts, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class CacheDB:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.executescript(SCHEMA)
        self.network_calls = 0
        self.cache_hits = 0

    def close(self) -> None:
        self.conn.close()

    def api_get(self, key: str, ttl_days: float) -> dict | None:
        row = self.conn.execute(
            "SELECT payload, created_at FROM api_cache WHERE key=?", (key,)
        ).fetchone()
        if row and time.time() - row[1] <= ttl_days * DAY:
            self.cache_hits += 1
            return json.loads(row[0])
        return None

    def api_put(self, key: str, source: str, payload: dict, *, ok: bool) -> None:
        """비정상 응답(ok=False)은 캐시하지 않는다."""
        if not ok:
            return
        self.conn.execute(
            "INSERT OR REPLACE INTO api_cache VALUES (?,?,?,?)",
            (key, source, json.dumps(payload, ensure_ascii=False), time.time()),
        )
        self.conn.commit()

    def llm_get(self, key: str) -> dict | None:
        row = self.conn.execute("SELECT payload FROM llm_cache WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def llm_put(self, key: str, payload: dict) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO llm_cache VALUES (?,?,?)",
            (key, json.dumps(payload, ensure_ascii=False), time.time()),
        )
        self.conn.commit()

    def start_run(self, quarter: str, as_of: str | None) -> int:
        cur = self.conn.execute(
            "INSERT INTO pipeline_runs (quarter, as_of, status, started_at) VALUES (?,?,?,?)",
            (quarter, as_of, "running", time.time()),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def finish_run(self, run_id: int, status: str, note: str | None = None) -> None:
        self.conn.execute(
            "UPDATE pipeline_runs SET status=?, finished_at=?, note=? WHERE id=?",
            (status, time.time(), note, run_id),
        )
        self.conn.commit()

    def save_evaluation(self, run_id: int, ticker: str, payload: dict) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO stock_evaluations VALUES (?,?,?)",
            (run_id, ticker, json.dumps(payload, ensure_ascii=False)),
        )
        self.conn.commit()

    def stats_line(self) -> str:
        return f"DART 네트워크 호출 {self.network_calls}건 · 캐시 적중 {self.cache_hits}건"
