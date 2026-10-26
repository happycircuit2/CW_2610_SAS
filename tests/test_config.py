import copy

import pytest
import yaml
from pydantic import ValidationError

from sas.config import Criteria, load_criteria


def test_loads_default():
    c = load_criteria()
    assert c.version == "2.0"
    assert c.screening.c.eps_yoy_min_pct == 25
    assert c.screening.a.roe_min_pct == 17
    assert c.screening.pegy.max_pegy == 1.0
    assert c.screening.pegy.stale_price_blocks_pass is True  # DECISIONS #2


def _raw():
    from sas.config import Path  # noqa: F401
    import sas.config as cfg

    p = cfg.Path(cfg.__file__).resolve().parents[2] / "criteria.yaml"
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def test_missing_key_fails():
    d = _raw()
    del d["screening"]["c"]["eps_yoy_min_pct"]
    with pytest.raises(ValidationError):
        Criteria.model_validate(d)


def test_wrong_type_fails():
    d = copy.deepcopy(_raw())
    d["screening"]["a"]["roe_min_pct"] = "17"
    with pytest.raises(ValidationError):
        Criteria.model_validate(d)


def test_unknown_key_fails():
    d = _raw()
    d["screening"]["c"]["typo"] = 1
    with pytest.raises(ValidationError):
        Criteria.model_validate(d)


def test_flag_overlap_fails():
    d = _raw()
    d["flags"]["caution"].append("shares_jump")
    with pytest.raises(ValidationError):
        Criteria.model_validate(d)
