"""criteria.yaml 로더. Pydantic v2 strict: 키 누락·미지 키·타입 오류는 로드 실패."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class _M(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Universe(_M):
    disclosure_ready_min_pct: float
    exclude_kinds: list[str]
    financials_ksic_codes: list[str]
    financials_nonfinancial_structure_override: bool


class Normalization(_M):
    quarters: int
    quarters_extra_for_split_adjust: int
    annual_years: int
    fs_div_bridge_max_gap_pct: float
    q4_shares_ratio_min: float
    q4_shares_ratio_max: float
    shares_jump_ratio_min: float
    shares_jump_ratio_max: float


class ScreenC(_M):
    both_quarters_profitable: bool
    eps_yoy_min_pct: float
    op_income_both_profitable: bool
    op_income_yoy_min_pct: float
    sales_yoy_min_pct: float
    allow_sales_acceleration: bool
    financials_exempt_op_income: bool
    financials_sales: str


class ScreenA(_M):
    annual_eps_increase_years: int
    eps_cagr_min_pct: float
    roe_min_pct: float
    ocf_must_be_positive: bool
    financials_exempt_ocf: bool
    min_fiscal_years: int
    insufficient_history: Literal["fail"]


class ScreenPegy(_M):
    max_pegy: float
    g_must_be_positive: bool
    high_growth_flag_pct: float
    stale_price_max_trading_days: int
    stale_price_blocks_pass: bool
    dividend_source_priority: list[str]


class Screening(_M):
    c: ScreenC
    a: ScreenA
    pegy: ScreenPegy


class Flags(_M):
    review: list[str]
    caution: list[str]

    @model_validator(mode="after")
    def _no_overlap(self) -> "Flags":
        dup = set(self.review) & set(self.caution)
        if dup:
            raise ValueError(f"플래그가 review/caution에 중복: {sorted(dup)}")
        return self


class Ke(_M):
    tier_bounds: list[float]
    tier_values_pct: list[float]
    default_pct: float


class Kd(_M):
    clamp_min_pct: float
    clamp_max_pct: float
    default_pct: float


class QuantGate(_M):
    fiscal_years: int
    rule1_recent_avg_years: int
    rule2_positive_years_min: int
    rule2_recent_consecutive: int
    on_fail_cap: Literal["narrow"]
    on_insufficient_cap: Literal["narrow"]


class Evidence(_M):
    strict_substring_quote_invalidation: bool
    keyword_match_min_ratio: float
    numeric_match_min_ratio: float


class Moat(_M):
    tax_rate: float
    excess_cash_sales_pct: float
    ke: Ke
    kd: Kd
    quant_gate: QuantGate
    evidence: Evidence
    business_text_max_chars: int


class Council(_M):
    provider: Literal["gemini", "anthropic", "dual"]
    model: str
    reasoning: str


class CacheTtl(_M):
    financials: int
    company: int


class Dart(_M):
    cache_ttl_days: CacheTtl
    fatal_status_codes: list[str]
    timeout_sec: int
    download_timeout_sec: int


class Criteria(_M):
    version: str
    updated_at: str
    universe: Universe
    normalization: Normalization
    screening: Screening
    flags: Flags
    moat: Moat
    council: Council
    dart: Dart


def load_criteria(path: str | Path | None = None) -> Criteria:
    p = Path(path) if path else Path(__file__).resolve().parents[2] / "criteria.yaml"
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    return Criteria.model_validate(data)


class Settings(_M):
    """경로·비밀. 값은 환경변수(.env)에서만 읽는다."""

    cache_db_path: Path
    raw_reports_dir: Path
    output_dir: Path
    council_provider: str | None = Field(default=None)
    council_model: str | None = Field(default=None)


def load_settings() -> Settings:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass
    g = os.environ.get
    return Settings(
        cache_db_path=Path(g("SAS_CACHE_DB_PATH", "data/cache.db")),
        raw_reports_dir=Path(g("SAS_RAW_REPORTS_DIR", "data/raw_reports")),
        output_dir=Path(g("SAS_OUTPUT_DIR", "output")),
        council_provider=g("MOAT_COUNCIL_PROVIDER") or None,
        council_model=g("MOAT_COUNCIL_MODEL") or None,
    )


def dart_api_key() -> str:
    key = os.environ.get("DART_API_KEY") or os.environ.get("OPENDART_API_KEY")
    if not key:
        raise RuntimeError("DART_API_KEY 환경변수가 없습니다.")
    return key
