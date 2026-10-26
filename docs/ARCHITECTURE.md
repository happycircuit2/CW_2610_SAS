# 아키텍처 (S1 확정 계약)

```
collectors ─▶ normalizer ─▶ screener(C→A→PEGY) ─▶ moat(quant_gate→council→aggregator) ─▶ report
   │              │               │                        │
   └──────────── storage.CacheDB (api_cache / llm_cache / pipeline_runs / stock_evaluations)
```

- 설정: `sas.config.load_criteria()` → `Criteria`(strict). 임계값 하드코딩 금지.
- 경로·비밀: `load_settings()` / 환경변수. 키는 코드·로그에 남기지 않음.
- 캐시: `CacheDB.api_get/api_put(ok=…)`, 비정상 응답 미캐시, `make_key()`로 파라미터 해시.
- DART 호출 규칙: 치명 코드(`dart.fatal_status_codes`)는 즉시 중단(종료 코드 3은 020). 종료 시 `stats_line()` 출력.
- 모듈 간 데이터 계약(정규화 결과 스키마 등)은 S2 시작 시 이 문서에 추가한다.
