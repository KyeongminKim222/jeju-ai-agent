# 🍊 제주 장사·나들이 AI 비서 (Jeju Local AI Agent)

도민이 말로 물으면 제주데이터허브 데이터를 AI가 스스로 골라 계산해
**창업 위험 등급(A~E)** 과 **덜 붐비는 곳**을 돌려주는 로컬 AI Agent입니다.
인터넷·외부 API 없이 제주빅데이터센터 PC에서 동작합니다.

## 1. 빠른 실행 (Windows)
1. Python 3.10 이상 설치 (python.org, 설치 시 "Add to PATH" 체크)
2. (선택) AI 질문 이해를 쓰려면 Ollama 설치 후 명령 프롬프트에서
   `ollama pull qwen2.5:3b`  ← 약 1.9GB, VRAM 약 2GB (GTX1060 3GB 가능)
3. 폴더의 **run.bat 더블클릭** → 처음 1회 라이브러리 설치 → 브라우저가 자동으로 열림
   - 인터넷이 없으면 `wheelhouse/` 폴더에 휠 파일을 넣어 두면 오프라인 설치
   - Ollama가 없으면 자동으로 **규칙 모드**(결과 동일, 화면 왼쪽에 표시)

수동 실행:
```
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python build_data.py      # data/processed 가 이미 있으면 생략 가능
.venv\Scripts\python -m streamlit run app.py
```

## 2. 사용법
- 탭 🏪 **장사해도 되쿠과**: "애월에 카페 하나 차리면 괜찮수과?" / "치킨집 하기 좋은 동네 어디우꽈?"
  → 등급 카드, 쉬운 설명, 평상시·비수기·충격 시 매출, 그래프, 대안 동네, **진단서 내려받기(HTML, 인쇄 가능)**
- 탭 🌿 **오늘 어디 한가하우꽈**: "1월 일요일 비 오는데 애들이랑 갈 만한 실내 어디 한가해요?"
  → 덜 붐비는 곳 3곳, 가장 붐빌 곳, 추천 시간
- 왼쪽 "AI가 일한 과정 보기"를 켜면 ①질문 이해 → ②값 보완 → ③도구 실행 → ④후속 도구 → ⑤답변 검증 단계가 표시됩니다.
- 지원 업종(20): 카페, 한식당, 일식·횟집, 중식당, 양식당, 치킨·피자·버거, 술집, 편의점, 빵집, 숙박(모텔·여관), 호텔, 기념품점, 화장품, 렌터카, 과일·채소, 수산물, 정육점, 슈퍼마켓, 마사지, 여행사
- 지역: 제주 43개 읍면동 + 생활 지명 80여 개(협재·함덕·월정·모슬포·중문 등)

## 3. 폴더 구성
```
app.py              화면(Streamlit)
agent/core.py       Agent 흐름(질문 이해·도구 선택·후속 호출·답변 검증)
agent/tools.py      결정적 분석 도구(창업 위험 진단·동네 비교·혼잡 예측)
build_data.py       원천 CSV → 가공 데이터 생성
data/processed/     가공 데이터(바로 실행용)
data/raw/           (비어 있음) 원천 CSV를 넣으면 build_data.py로 재생성 — 데이터_활용_명세.md 참고
tests/eval.py       정확도·재현성·응답시간 평가 → outputs/eval.json
tests/smoke.py      예시 질문 일괄 실행 → outputs/smoke.log
make_docs.py        기획서·결과설명자료 PDF 생성(실제 실행 결과로)
run.bat             원클릭 실행
docs/               기획서.pdf, 결과설명자료.pdf, 사용자매뉴얼.md
```

## 4. 사용 AI 모델과 범위
- **Qwen2.5-3B-Instruct** (Ollama `qwen2.5:3b`), 로컬 실행, temperature 0·seed 고정
- AI는 **질문 이해(도구·지역·업종·월·요일·시간 추출)만** 담당. 결과는 사전·규칙으로 재검증하고 사전에 없는 값은 버림
- 숫자·등급·추천은 모두 `agent/tools.py`의 pandas 계산 → 같은 질문 = 같은 답
- 답변 문장 다듬기(LLM)는 기본 OFF (`JEJU_AGENT_POLISH=1`로 켜면 숫자 대조 검증 통과 시에만 채택)
- 환경변수: `JEJU_AGENT_MODEL`(기본 qwen2.5:3b), `OLLAMA_HOST`(기본 http://127.0.0.1:11434), `JEJU_AGENT_LLM_TIMEOUT`(초)

## 5. 재현·검증
```
.venv\Scripts\python tests\eval.py     # 20문항 정확도, 10회 재현성, 응답 시간
.venv\Scripts\python tests\smoke.py    # 예시 9문항 전체 과정 로그
```

## 6. 한계
- 읍면동×업종 카드매출은 2021.05까지 공개 → 지표는 2017~2019(평상시)와 2020 봄(충격) 기준
- 동네 전체 통계 기반 참고 지표이며 개별 점포의 성패를 예측하지 않음
- 혼잡도는 월·요일·시간 패턴 기반(실시간 아님)
