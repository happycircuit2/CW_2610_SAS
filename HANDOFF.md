# HANDOFF

## 현재 상태
- S1(기반) 완료: 골격, `criteria.yaml`+Pydantic, SQLite 캐시, CLI 인자 검증/종료 코드, 셋업 스크립트. `pytest` 12건 통과.
- 명세서: `docs/SAS_규칙_명세서_v2.0.md`. 결정: `docs/DECISIONS.md`. 계약: `docs/ARCHITECTURE.md`.
- 브랜치: `claude/kind-bell-mgs6dw`.

## 환경 메모
- 세션 시작 시 `./scripts/setup_cloud.sh` 실행(의존성, `apt-get update` 후 fonts-noto-cjk).
- `DART_API_KEY`는 환경변수로 있음. `GEMINI_API_KEY`/`ANTHROPIC_API_KEY`는 사용자가 환경 Secrets에 등록해야 함.
- KRX는 `data-dbg.krx.co.kr/svc/apis/` 경로만 프록시가 키 주입.

## 남은 일
- S2(추론 높음 권장): collectors(DART/KRX), 유니버스, 정규화(4Q 역산, 연결/별도 브릿지, 소급).
- S3: C·A·PEGY / S4(추론 높음 권장): 해자 / S5: 출력·통합·공시완료율 연결.
- 캐시 영속화 방식 재확정(DECISIONS 하단).
