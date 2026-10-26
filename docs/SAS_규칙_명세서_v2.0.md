# SAS v2.0 프로젝트 규칙 명세서

Oct 26, 2026 · @안재영

## 1. 개요

SAS v2.0은 KOSPI·KOSDAQ 보통주를 CANSLIM(C·A)과 린치 PEGY로 거른 뒤, 통과 종목을 모닝스타식 해자 기준으로 평가해 PDF·JSON·CSV로 내는 분기 단위 파이프라인이다. 이 명세서는 폴더 `AG_2610_SAS`의 설계 문서 3종, `criteria.yaml`, 소스 코드(`src/sas`)를 읽어 정리한 규칙집이며, 폴더 안 파일은 수정·삭제하지 않았다.

**문서 성격**: 설계 문서가 말하는 규칙(명세)과 코드가 실제로 하는 동작(구현)을 구분해 적고, 어긋나는 곳은 8장에 모았다.

**규칙 우선순위**: 1) 안전·법적 필수 조건 → 2) 사용자가 명시한 제약 → 3) `criteria.yaml` 임계값 → 4) 코드 기본값. 임계값은 코드에 하드코딩하지 않고 `criteria.yaml`(v2.0, 2026-10-25)이 단일 기준이다.

**폴더 보호 규칙**

- 프로젝트 폴더의 임의 편집·삭제를 금지한다. 이 명세서 작성 과정에서도 읽기 전용으로만 접근했고, 이 문서는 폴더 밖(대화 문서)에 있다.
- `.env`는 API 키가 들어 있어 열람하지 않았다. 키 항목은 `.env.example` 기준으로만 기술한다.
- `data/cache.db`(약 1.4GB)와 `data/raw_reports/`는 재실행 이어받기의 기반이므로 임의로 지우거나 초기화하지 않는다.

**참고 문서 위치**

| 문서 | 역할 |
| --- | --- |
| `docs/SAS_필터_및_평가_규칙_명세서_v2.0.md` | 필터·해자 규칙 원본(설계) |
| `docs/SAS_아키텍처_및_해자심의_보고서_명세서.md` | 디렉터리·API·프롬프트·PDF 디자인 |
| `docs/ANTIGRAVITY_단계별_실행_로드맵_및_프롬프트.md` | 구현 단계(Phase 0\~7)와 모델 배정 |
| `README.md` | 설치·실행·종료 코드·DART 한도 |
| `criteria.yaml` | 임계값 단일 진실 공급원 |

## 2. 파이프라인 및 실행 규칙

파이프라인은 단방향(1-Pass)이며 다섯 단계를 순서대로 지난다. 앞 단계를 통과한 종목만 다음 단계로 간다.

1. **유니버스 수집**: KRX·DART에서 보통주만 확정
2. **정규화**: 연결/별도 브릿지, 4Q 역산, 액면분할 소급
3. **1단계 스크리닝**: C → A → PEGY
4. **2단계 해자**: 정량 게이트(ROIC vs WACC) → 3페르소나 심의회 → 게이트 캡
5. **출력**: PDF 보고서 + JSON/CSV 요약

**CLI 명령**

| 명령 | 동작 | 필수 인자 |
| --- | --- | --- |
| `sas run` | 전 단계 실행 후 PDF·JSON·CSV 생성 | `--quarter YYYYQn` |
| `sas screen-only` | 1단계(C·A·PEGY)까지만 실행, 통과 종목 출력 | `--quarter` |
| `sas evaluate-moat` | 지정 종목만 해자 평가 + PDF(스크리닝 통과 여부 무관, 디버깅용) | `--tickers 003230,005930` |

공통 옵션은 `--as-of YYYY-MM-DD`, `--output-dir`, `--no-cache`(LLM 캐시 미사용), `--no-prefilter`(C 사전 필터 끄기, DART 호출 증가)이다. 분기는 `^\d{4}Q[1-4]$`, 종목코드는 6자리 영숫자여야 하며 어긋나면 입력 오류(코드 2)다.

**종료 코드**

| 코드 | 의미 | 후속 행동 |
| --- | --- | --- |
| 0 | 성공 | — |
| 1 | 실행 실패 (일반 예외, DART API 오류) | 로그·`.env` 키 확인 |
| 2 | 입력 오류 | 인자 수정 |
| 3 | DART 일일 호출 한도 초과(status 020) | 다음 날 같은 명령 재실행 |

**실행 시점**: 분기 법정 공시 기한 + 1주 이후(4/7, 5/22, 8/21, 11/21 이후)를 원칙으로 한다. 실행 환경은 사용자 Windows PC이고 Python 3.11 이상, PDF 생성에 Playwright Chromium이 필요하다.

**DART 호출 예산 원칙** (일일 한도 보호)

- 정규화에 실제로 쓰는 보고서만 요청한다(2026Q2 기준 종목당 19건: 직전 16분기+소급 보정 1개분 보고서와 5개년 연간).
- C 사전 필터: 최근 분기·전년 동기 보고서 2건만 받아 C 기준 확정 탈락 종목은 나머지를 받지 않는다. 값이 없거나 애매하면 항상 통과시켜 오탈락을 막는다. 4Q 분석은 최근 분기가 역산값이라 사전 필터를 적용하지 않는다.
- 주식총수 API는 EPS로 주식수를 역산할 수 없을 때만, 배당 API는 C·A 통과 종목에 한해 호출한다.
- 020을 받으면 데이터 없음으로 삼키지 않고 즉시 중단한다. 불완전한 PDF·요약은 만들지 않고, 정상 응답은 `data/cache.db`에 남아 다음 날 이어서 진행한다. 치명 상태코드는 010, 011, 012, 020, 101, 800, 901이다.
- 캐시 유효기간: 재무제표 90일, 기업개황 30일. 비정상 응답은 캐시하지 않는다.
- 실행이 끝나면 `DART 네트워크 호출 N건 · 캐시 적중 M건`을 표시한다.

## 3. 유니버스 및 정규화 규칙

**유니버스**

- 대상은 KOSPI·KOSDAQ 보통주다. 스팩, 우선주, 리츠, 외국주권, DR, 투자회사, SOC는 제외한다. KRX의 종목명·주권종류(신형·구형 우선주, 종류주권)로 판별한다.
- 시세·시가총액·상장주식수는 실행일 직전 거래일 기준이다. 252거래일 변동성은 WACC의 Ke 산정에 쓴다.
- 금융업은 DART 기업개황의 KSIC 대분류 K(코드 64·66)로 1차 판별한다. 재무구조가 비금융(일반 지주사 등)이면 일반 규칙을 적용하는 실효 금융업 판정(`financials_nonfinancial_structure_override`)이 있다.
- 정기보고서 공시 완료율이 95% 미만이면 경고하고 실행을 중단하는 것이 설계이다(구현 상태는 8장 참고).

**재무 정규화 (1-Pass)**

| 항목 | 규칙 |
| --- | --- |
| EPS 기준 | 계속영업 기본 EPS, 지배기업 보통주 귀속 |
| 연결/별도 | 연결(CFS) 우선, 없으면 별도(OFS). 중간에 전환된 경우 겹치는 연도 당기순이익 괴리율 0.5% 이내일 때만 시계열을 잇고 `fs_div_bridged` 플래그, 초과 시 판정불가 |
| 4분기 역산 | 4Q 순이익·매출·영업이익 = 연간 − 3분기 누적. 4Q 가중평균주식수는 일수 가중 역산 |
| 4Q 주식수 이상 | 역산 주식수가 3Q 누적의 0.6\~1.7배를 벗어나면 3Q 누적 주식수로 대체하고 `q4_shares_fallback` 검토 플래그 |
| 액면분할·병합·무상증자 | 비교표시 EPS(또는 유통주식수) 비율로 과거 EPS·DPS를 현재 주식수 기준으로 일괄 소급 환산(단방향, 경로 비의존) |
| 주식수 급변 | 비율이 0.67\~1.50을 벗어나면 `shares_jump` 검토 플래그 |

분기 시계열은 최근 16분기(+소급 보정 1개)를 쓰고, 연간은 최신 사업연도 포함 5개년을 쓴다. 최신 사업연도는 4Q 분석이면 당해, 그 외는 전년이다.

## 4. 1단계 스크리닝 규칙

C, A, PEGY 세 관문을 **모두** 통과해야 `passed_all`이다. 각 관문의 임계값은 `criteria.yaml` 키에서 읽는다.

**4.1 CANSLIM C (최근 분기)**

| 조건 | 규칙 | 키 |
| --- | --- | --- |
| EPS 흑자 | 최근 분기와 전년 동기 EPS 모두 > 0. 전년 동기가 적자이고 최근이 흑자면 탈락 + `turnaround` 플래그 | `both_quarters_profitable` |
| EPS YoY | ≥ +25% | `eps_yoy_min_pct` |
| 영업이익 | 비금융업은 두 분기 모두 > 0 이고 YoY > 0%. 금융업은 면제 | `op_income_both_profitable`, `op_income_yoy_min_pct` |
| 매출 YoY | ≥ +25% **또는** 최근 3분기 매출 YoY가 g(t-2) < g(t-1) < g(t)이고 g(t) > 0% (통과 시 `sales_accelerated_pass`) | `sales_yoy_min_pct`, `allow_sales_acceleration` |
| 금융업 매출 | 보고 영업수익 우선, 없으면 이자·수수료·보험·투자수익 합산(대용치 플래그) | `financials_sales` |

전년 동기 분기가 없으면 뒤에서 5번째 분기를 대체로 쓰고, 그마저 없으면 탈락이다.

**4.2 CANSLIM A (연간 실적)**

| 조건 | 규칙 | 키 |
| --- | --- | --- |
| 연속 증가 | 최근 4개 회계연도 EPS가 모두 > 0 이고 3년 연속 증가 | `annual_eps_increase_years` |
| 3년 CAGR | ≥ 25% | `eps_cagr_min_pct` |
| ROE | 최근 FY ≥ 17% (지배주주 순이익 / 기초·기말 평균 지배주주지분) | `roe_min_pct` |
| 영업현금흐름 | 최근 FY > 0. 금융업은 면제 | `ocf_must_be_positive`, `financials_exempt_ocf` |
| 이력 부족 | 4개년 미만이면 탈락(`insufficient_history`) | `insufficient_history = fail` |

**4.3 린치 PEGY**

식은 다음과 같다. PER는 실행일 직전 거래일 종가를 최근 4분기 합산(TTM) EPS로 나눈 값이다.

```latex
PEGY = PER / (G + D),   0 < PEGY <= 1.0,   G > 0
```

- **G**: TTM EPS의 3년 CAGR(%). 3년 전 동일 시점 TTM EPS가 0 이하이면 산출 불가로 탈락한다. 상한 캡은 없고, 50% 이상이면 `high_growth` 플래그만 붙인다.
- **D**: 배당수익률(%). DART `alotMatter.json`의 보통주 주당 현금배당금을 소급 보정해 종가로 나눈다. 누락·파싱 불가일 때만 네이버·KRX 크롤링 폴백을 쓰고 `dividend_fallback_used`를 붙인다. 무배당이 확인되면 D = 0이다.
- TTM EPS ≤ 0이면 즉시 탈락, G + D ≤ 0이면 PEGY 정의 불가로 탈락한다. 배당만으로 통과하는 역성장 기업을 막기 위해 G > 0을 강제한다.
- 종가 지연이 10거래일을 넘으면 `stale_price_or_quarter` 검토 플래그를 붙이고 탈락 사유에 기록한다(실제 통과 차단 여부는 8장 참고).

**4.4 플래그 체계**

| 분류 | 플래그 | 표시 |
| --- | --- | --- |
| 검토 필수 (`review_flags`) | `eps_basis_check`, `shares_jump`, `quarter_sum_mismatch`, `stale_price_or_quarter`, `q4_shares_fallback`, `quant_gate_capped` | 종목에 `needs_review` 표시 |
| 품질 참고 (`caution_flags`) | `small_base`( | EPS |

플래그는 중복을 제거해 순서를 유지한다. `turnaround`과 매출 대용치 플래그는 코드에만 있고 `criteria.yaml` 목록에는 없다.

## 5. 2단계 해자 평가 규칙

1단계를 통과한 종목만 대상이다. 정량 게이트가 실패해도 심의회는 진행하고, 등급 상한만 건다.

**5.1 정량 지표 (최근 5개 회계연도)**

| 지표 | 정의 |
| --- | --- |
| NOPAT | 영업이익 × (1 − 25%) |
| 투하자본 | 자본총계(비지배 포함) + 총차입금(리스부채 포함) − max(0, 현금성자산 + 단기금융상품 − 매출액 × 2%), 기초·기말 평균 |
| 투하자본 ≤ 0 | NOPAT > 0 이면 해당 연도는 초과수익 달성으로 인정 (`ic_nonpositive`) |
| Ke | 변동성 백분위와 부채비율 백분위의 평균을 3등분: 33.3 미만 8.5%, 66.7 미만 10.0%, 그 이상 11.5%. 금융업은 변동성만 사용. 백분위가 없으면 10.0% |
| Kd | 이자비용 / 평균 총차입금, 세전 2\~12% 클램프 후 × 0.75. 산출 불가 시 기본 12% |
| WACC | E = 실행일 시가총액, D = 최근 FY말 장부 총차입금. 현재 WACC을 5개년 전체에 동일 적용. 금융업은 Ke만 사용 |
| 금융업 | ROIC − WACC 대신 ROE − Ke |

**5.2 정량 게이트**

스프레드 = ROIC − WACC (%p). 아래 둘 중 하나를 만족하면 `pass`다. 5개년 중 결측·비정상 값이 있으면 `insufficient`, 그 외는 `fail`이다.

1. 최근 3개년 평균 스프레드 > 0 이고 최근 FY 스프레드 > 0
2. 5개년 중 3개년 이상 스프레드 > 0 이고 최근 2개년 연속 > 0

| 게이트 | 심의회 | 등급 상한 |
| --- | --- | --- |
| `pass` | 실행 | 제한 없음 |
| `fail` | 실행 | 최대 Narrow (`cap_narrow`). Wide 판정 시 Narrow로 낮추고 `quant_gate_capped` 검토 플래그 |
| `insufficient` | 실행 | 최대 Narrow. 해자 인정 시 `needs_review` 추가 |

**5.3 정성 심의회 (3페르소나)**

- 위원 1 Moat Hunter가 해자 증거를, 위원 2 Skeptic이 반박 논거를 독립적으로 작성하고, 위원 3 Chief Moat Chair가 둘과 정량 데이터를 대조해 최종 등급을 JSON으로 확정한다.
- 등급: `wide`(10년 이상 확실, 20년 이상 가능성 높음), `narrow`(10년 이상 가능성이 더 높음), `none`(구조적 장벽 불명확, 업황·일시 수주 호조). 확신도는 `high` / `medium` / `low`.
- 5대 원천: 무형자산, 전환비용, 네트워크 효과, 원가 우위, 효율적 규모. 각 원천은 `strong` / `moderate` / `none`으로 평가하고 사업보고서 출처 절과 핵심 사실 인용을 필수로 쓴다.
- 입력은 사업보고서 "II. 사업의 내용" 본문(최대 12만 자)과 4개 표(제품·매출 비중, 가동률, 수주잔고, R&D·특허)를 쓴다. 본문이 비어 있으면 LLM을 호출하지 않고 해당 종목 심의를 생략한다.
- LLM은 `MOAT_COUNCIL_PROVIDER` = gemini | anthropic | dual 중 하나를 쓰고, 기본은 `gemini-4-argon` / 추론 수준 high다. 프롬프트·모델·입력 해시 기준으로 `llm_cache`에 결과를 캐시한다.

**5.4 근거 검증과 최종 등급**

- 인용 근거는 소프트 검증한다. 출처 절이 유효한지, 인용 키워드의 원문 대조율이 25% 이상인지, 인용 수치의 절반 이상이 원문 또는 정량표에 있는지를 본다. 15자 부분 문자열 일치 규칙은 폐지됐다(`strict_substring_quote_invalidation = false`).
- 근거가 부실하면 등급은 유지하고 확신도만 1단계 낮추며(high → medium → low) `evidence_weak` 플래그를 붙인다.
- 최종 등급 = 심의회 등급에 정량 게이트 상한을 적용한 값이다. 원본 등급(`raw_moat_rating`)과 최종 등급(`final_moat_rating`)을 모두 기록한다.

## 6. 출력 및 보고서 규칙

산출물은 출력 디렉터리(기본 `output/`, `SAS_OUTPUT_DIR` 또는 `--output-dir`)에 쓴다.

| 파일 | 내용 |
| --- | --- |
| `SAS_Report_{분기}.pdf` | A4 세로 PDF. Jinja2 템플릿(`templates/report.html`, `report.css`)을 Playwright Chromium으로 렌더링 |
| `SAS_Summary_{분기}.json` | 깔때기 통계 + 종목별 요약 |
| `SAS_Summary_{분기}.csv` | 종목코드, 종목명, 시장, PEGY, 게이트 상태, 원본·최종 등급, 확신도, 예상 초과수익 연수, 검토 플래그 (UTF-8 BOM) |

**PDF 구성 규칙**

1. 표지와 깔때기: 유니버스 → C 통과 → A 통과 → PEGY 통과 → 해자 정량 통과 → 등급 분포(Wide / Narrow / None), 단계별 통과율.
2. 스코어카드: 1단계를 통과한 모든 종목을 Wide, Narrow, None 구분 없이 한 표에 수록.
3. 종목별 심층 리포트: 통과 종목 전수를 Wide → Narrow → None 순으로, 같은 등급 안에서는 PEGY가 낮은 순으로 정렬. None 등급도 빠뜨리지 않고, 재무 필터는 통과했으나 구조적 해자 기준에 미달한 이유를 서술한다. 종목당 1\~2페이지.
4. 종목 카드: 헤더(등급 배지, 확신도, 플래그), 좌측 C·A·PEGY 성적표, 우측 5개년 ROIC vs WACC 차트·표, 수석 의장 종합 판정문, Moat Hunter vs Skeptic 대립 박스, 5대 원천 매트릭스.

**디자인 규격**: 배지 색은 WIDE `#0D6832`, NARROW `#1E56A0`, NONE `#64748B`, 주요 색 `#0F2C59`, 검토 배지는 배경 `#FEF3C7`·테두리 `#D97706`. 숫자는 `tabular-nums`, 본문 폰트는 Noto Sans KR 또는 Pretendard.

**생성 중단 규칙**: DART 020이 나오면 불완전한 PDF·요약을 만들지 않는다. 해자 평가에 실패한 종목은 로그에 남기고 보고서에서 제외하며, 실행 끝에 실패 종목 수 경고를 출력한다.

## 7. 데이터, 보안, 테스트 규칙

**데이터·캐시**

- SQLite `data/cache.db`에 `api_cache`(DART·KRX 응답), `llm_cache`(심의 결과), `pipeline_runs`, `stock_evaluations` 테이블을 둔다. 요청 파라미터 해시가 키이다.
- 사업보고서 원문은 `data/raw_reports/`에 저장한다. 내용이 비었거나 DART 오류 XML이 들어 있으면 폐기하고 다시 내려받는다.
- API 타임아웃은 기본 15초(원문 다운로드 30초 이상)이다.

**비밀 관리**

- `DART_API_KEY`(별칭 `OPENDART_API_KEY`), `KRX_API_KEY`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`는 `.env`에만 둔다. 템플릿은 `.env.example`이며 키를 코드·문서·종료 로그에 남기지 않는다.
- 경로 환경변수: `SAS_CACHE_DB_PATH`, `SAS_RAW_REPORTS_DIR`, `SAS_OUTPUT_DIR`.

**테스트**

- `python -m pytest`로 실행하며 테스트는 `config`, `normalizer`, `screener`, `quant_gate`, `council`, `pdf_report`, `cli`, `dart_budget`, `collectors_live`로 나뉘다.
- 이름에 `live`가 들어간 테스트(DART·KRX·LLM 실호출)는 기본으로 건너뛰고, `SAS_RUN_LIVE=1`일 때만 실행한다. 실호출 테스트는 API 키와 네트워크가 필요하고 DART 한도를 소모한다.
- `criteria.yaml`은 Pydantic v2로 엄격 검증하며 키가 빠지거나 타입이 틀리면 로드가 실패한다.

**변경 관리**: 임계값 변경은 `criteria.yaml`에서만 하고 버전·`updated_at`을 갱신한다. 임계값 하드코딩 금지 원칙을 따른다.

## 8. 설계 문서와 코드의 불일치, 확인 필요 사항

코드를 읽으며 발견한 차이다. 실행해 본 것이 아니라 소스 열람 기준이므로, 실제 동작은 테스트로 확정이 필요하다. 사용자가 결정해야 하는 것은 마지막 열에 표시했다.

| # | 설계 문서의 규칙 | 코드에서 확인된 것 | 결정 필요 |
| --- | --- | --- | --- |
| 1 | 공시 완료율 95% 미만이면 경고 후 실행 중단 | `check_disclosure_readiness`는 구현돼 있으나 `cli.py` 실행 경로에서 호출하는 곳을 찾지 못했다. 설정값만 있다 | 호출 연결 여부 확인 |
| 2 | 종가 10거래일 초과 지연 시 PEGY 탈락 | `stale_price_or_quarter` 플래그와 탈락 사유 문구만 추가된다. `passed`는 별도 계산되어 PEGY 범위를 만족하면 통과로 남을 수 있다 | 차단할지, 검토 플래그만 둘지 |
| 3 | 통과 종목 전수를 보고서에 수록(None 포함) | 사업보고서 수집·심의·본문 추출에 실패한 종목은 스킵되어 카드가 없다(경고만 출력) | 실패 종목을 보고서에 표시할지 |
| 4 | PDF 파일명 `SAS_Report_{YYYY}Q{N}_{RunDate}.pdf` | 실제는 `SAS_Report_{분기}.pdf`라 날짜가 없고, 같은 분기를 다시 실행하면 덮어쓴다 | 파일명 규칙 확정 |
| 5 | 플래그 목록 | `turnaround`·매출 대용치 플래그가 코드에만 있고 `criteria.yaml` 목록에 없다 | 목록 동기화 |
| 6 | 금융업 C 필터 | 비금융업만 영업이익 조건을 적용하고 금융업은 면제된다. 설계 문서는 매출 대용치 중심으로만 기술 | 의도된 동작인지 |
| 7 | `dividend_source_priority` 표기 | 설계 표는 `dart_api` / `web_fallback`, YAML은 `dart_alotMatter_api` / `naver_krx_crawler_fallback` | 표기 통일 |
| 8 | 심의회 모델 | `.env.example`이 `gemini-4-argon` / high를 기본으로 지정. 로드맵은 단계별로 모델·추론 수준을 바꾸라고 권장 | 심의회 모델 확정 |

폴더에 있는 `SAS_Report_2026Q2_Sample.pdf`, `output/SAS_Report_2026Q2.pdf`, `docs/guide.html`, `docs/SAS_User_Guide.pdf`는 규칙 원천으로 삼지 않았고, `.env`는 열지 않았다.

### Sources

폴더 `D:\Antigravity\AG_2610_SAS`: `README.md`, `criteria.yaml`, `pyproject.toml`, `.env.example`, `docs/` 설계 문서 3종, `src/sas/`(`cli.py`, `screener/*`, `moat/quant_gate.py`, `moat/aggregator.py`, `moat/council.py`, `collectors/*`, `storage/db.py`), `tests/conftest.py`.
