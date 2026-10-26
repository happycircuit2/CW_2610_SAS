#!/usr/bin/env bash
# 클라우드 세션 초기 설정: 의존성 + 한글 폰트. Chromium은 /opt/pw-browsers에 사전 설치됨.
set -euo pipefail
cd "$(dirname "$0")/.."
pip install -q -e ".[dev]"
if ! fc-list | grep -qiE 'noto.*cjk|nanum|pretendard'; then
  (apt-get update -q >/dev/null 2>&1; apt-get install -y -q fonts-noto-cjk >/dev/null 2>&1 || echo "WARN: 한글 폰트 설치 실패 (apt 차단?)") && fc-cache -f >/dev/null 2>&1 || true
fi
echo "setup done"
