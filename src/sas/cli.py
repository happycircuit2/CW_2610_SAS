"""CLI 진입점. S1: 인자 검증과 종료 코드만 구현, 파이프라인은 S2~S5에서 연결."""
from __future__ import annotations

import re
import sys
from typing import Optional

import typer

EXIT_OK, EXIT_FAIL, EXIT_INPUT, EXIT_DART_LIMIT = 0, 1, 2, 3
QUARTER_RE = re.compile(r"^\d{4}Q[1-4]$")
TICKER_RE = re.compile(r"^[0-9A-Za-z]{6}$")

app = typer.Typer(add_completion=False, help="SAS v2.0 분기 스크리닝·해자 평가")


def validate_quarter(q: str) -> str:
    if not QUARTER_RE.match(q):
        raise typer.Exit(_input_error(f"--quarter 형식 오류: {q} (예: 2026Q2)"))
    return q


def parse_tickers(raw: str) -> list[str]:
    tickers = [t.strip() for t in raw.split(",") if t.strip()]
    bad = [t for t in tickers if not TICKER_RE.match(t)]
    if not tickers or bad:
        raise typer.Exit(_input_error(f"--tickers 형식 오류: {bad or raw}"))
    return tickers


def _input_error(msg: str) -> int:
    typer.echo(msg, err=True)
    return EXIT_INPUT


def _not_implemented(name: str) -> None:
    typer.echo(f"{name}: 파이프라인 미구현 (S2~S5 예정)", err=True)
    raise typer.Exit(EXIT_FAIL)


@app.command()
def run(
    quarter: str = typer.Option(..., "--quarter"),
    as_of: Optional[str] = typer.Option(None, "--as-of"),
    output_dir: Optional[str] = typer.Option(None, "--output-dir"),
    no_cache: bool = typer.Option(False, "--no-cache"),
    no_prefilter: bool = typer.Option(False, "--no-prefilter"),
) -> None:
    validate_quarter(quarter)
    _not_implemented("run")


@app.command("screen-only")
def screen_only(
    quarter: str = typer.Option(..., "--quarter"),
    as_of: Optional[str] = typer.Option(None, "--as-of"),
    output_dir: Optional[str] = typer.Option(None, "--output-dir"),
    no_prefilter: bool = typer.Option(False, "--no-prefilter"),
) -> None:
    validate_quarter(quarter)
    _not_implemented("screen-only")


@app.command("evaluate-moat")
def evaluate_moat(
    tickers: str = typer.Option(..., "--tickers"),
    as_of: Optional[str] = typer.Option(None, "--as-of"),
    output_dir: Optional[str] = typer.Option(None, "--output-dir"),
    no_cache: bool = typer.Option(False, "--no-cache"),
) -> None:
    parse_tickers(tickers)
    _not_implemented("evaluate-moat")


if __name__ == "__main__":
    sys.exit(app())
