# 결정 기록

명세서 8장 미결 사항 확정(2026-10-26, 사용자 "기본안 진행").

| # | 결정 | 반영 위치 |
| --- | --- | --- |
| 1 | 공시 완료율 점검(95%)을 `sas run`에 연결 | S5 CLI 통합 |
| 2 | 종가 10거래일 초과 지연 시 PEGY 탈락 | `screening.pegy.stale_price_blocks_pass: true` |
| 3 | 심의 실패 종목은 보고서에 "평가 불가"로 표시 | S5 보고서 |
| 4 | PDF 파일명 `SAS_Report_{YYYY}Q{N}_{RunDate}.pdf` | S5 |
| 5 | 플래그 목록을 criteria.yaml에 동기화(turnaround 등 추가) | `flags` |
| 6 | 금융업 영업이익 면제 유지 | `financials_exempt_op_income` |
| 7 | 배당 출처 표기는 YAML 값(`dart_alotMatter_api` / `naver_krx_crawler_fallback`) | `dividend_source_priority` |
| 8 | 심의회 모델은 환경변수 `MOAT_COUNCIL_MODEL`로 교체. 기본값 미확정(`gemini-4-argon` 존재 미확인) | `council.model` 비움 |

## 캐시 영속화 (Drive 사용 결정)
Drive MCP 도구는 파일 내용을 모델 컨텍스트로 통과시키므로 GB급 `cache.db` 이동에 부적합. 
S1 결론: S5 전까지 대안(GCS `gsutil`/분기별 DB 분할/Drive 데스크톱 동기화)을 사용자와 재확정.
