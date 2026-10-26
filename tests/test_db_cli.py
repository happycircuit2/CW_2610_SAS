from typer.testing import CliRunner

from sas.cli import app
from sas.storage.db import CacheDB, make_key

runner = CliRunner()


def test_cache_roundtrip_and_ttl(tmp_path):
    db = CacheDB(tmp_path / "c.db")
    k = make_key("fnltt", {"corp": "1", "year": 2025})
    assert db.api_get(k, 90) is None
    db.api_put(k, "dart", {"status": "000"}, ok=True)
    assert db.api_get(k, 90) == {"status": "000"}
    assert db.api_get(k, 0) is None  # TTL 0이면 만료
    assert "캐시 적중 1건" in db.stats_line()


def test_abnormal_response_not_cached(tmp_path):
    db = CacheDB(tmp_path / "c.db")
    k = make_key("x")
    db.api_put(k, "dart", {"status": "013"}, ok=False)
    assert db.api_get(k, 90) is None


def test_key_is_order_independent():
    assert make_key({"a": 1, "b": 2}) == make_key({"b": 2, "a": 1})


def test_run_lifecycle(tmp_path):
    db = CacheDB(tmp_path / "c.db")
    rid = db.start_run("2026Q2", None)
    db.save_evaluation(rid, "005930", {"passed_all": False})
    db.finish_run(rid, "ok")
    assert db.conn.execute("SELECT status FROM pipeline_runs").fetchone()[0] == "ok"


def test_cli_bad_quarter_exit2():
    assert runner.invoke(app, ["run", "--quarter", "2026Q5"]).exit_code == 2


def test_cli_bad_ticker_exit2():
    assert runner.invoke(app, ["evaluate-moat", "--tickers", "00323"]).exit_code == 2


def test_cli_valid_args_reach_stub_exit1():
    assert runner.invoke(app, ["screen-only", "--quarter", "2026Q2"]).exit_code == 1
