"""제출 문서 자동 생성: 그림(실제 실행 결과) + 기획서/결과설명자료 HTML → PDF(Edge headless)
python make_docs.py
"""
import base64, datetime as dt, io, json, os, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from agent import core, tools as T

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False
DOCS = os.path.join(ROOT, "docs")
os.makedirs(DOCS, exist_ok=True)


def b64(fig):
    buf = io.BytesIO(); fig.savefig(buf, format="png", dpi=150, bbox_inches="tight"); plt.close(fig)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


EV = json.load(open(os.path.join(ROOT, "outputs", "eval.json"), encoding="utf-8"))

# ── 실제 실행 결과 ──
Q1 = "애월에 카페 하나 차리면 괜찮수과?"
R1 = core.run(Q1, use_llm=True)
D = R1["result"]
Q2 = "1월 일요일 비 오는데 애들이랑 갈 만한 실내 어디 한가해요?"
R2 = core.run(Q2, use_llm=True)
Q3 = "치킨집 하기 좋은 동네 어디우꽈?"
R3 = core.run(Q3, use_llm=True)
Q4 = "연동에서 한식당 하면 장사 될까요"
R4 = core.run(Q4, use_llm=True)

# 그림1 계절성
fig, ax = plt.subplots(figsize=(7.5, 3))
ms = list(range(1, 13)); se = D["seasonal"]; v = [se.get(f"{m:02d}") for m in ms]
ax.bar(ms, v, color=["#d32f2f" if m == D["최악의달"] else ("#1b9e4b" if m == D["최고의달"] else "#f4a340") for m in ms], label="애월읍 카페 월별 카드매출(평균=1)")
sv = R1["extra"]["season"]["월별"]; ax.plot(ms, [sv.get(m) for m in ms], "k--o", ms=3, lw=1, label="제주시 서부 관광지 방문객(평균=1)")
ax.axhline(1, color="#aaa", lw=.6); ax.set_xticks(ms); ax.set_xticklabels([f"{m}월" for m in ms], fontsize=8)
ax.set_ylim(0, max(v) * 1.35); ax.legend(fontsize=8, ncol=2, frameon=False, loc="upper left")
IMG_SEAS = b64(fig)
# 그림2 지표
fig, ax = plt.subplots(figsize=(7.5, 2.6))
names = [x["설명"] for x in D["지표"]][::-1]; vals = [x["안전점수"] for x in D["지표"]][::-1]
ax.barh(names, vals, color=["#1b9e4b" if x >= 60 else ("#f9a825" if x >= 40 else "#d32f2f") for x in vals])
ax.axvline(50, color="#999", ls="--", lw=.8); ax.set_xlim(0, 100); ax.tick_params(labelsize=8)
ax.set_xlabel("안전점수(50 = 같은 업종 제주 동네들의 중간)", fontsize=8)
IMG_FAC = b64(fig)
# 그림3 전 지역 카페 등급 분포
peers = T._score(T._peer_table("카페")).sort_values("종합")
fig, ax = plt.subplots(figsize=(7.5, 3.2))
cols = [{"A": "#1b9e4b", "B": "#7cb342", "C": "#f9a825", "D": "#ef6c00", "E": "#d32f2f"}[T.grade_of(s)[0]] for s in peers["종합"]]
ax.bar(range(len(peers)), peers["종합"], color=cols)
ax.set_xticks(range(len(peers))); ax.set_xticklabels(peers.index, rotation=90, fontsize=7)
i = list(peers.index).index("애월읍"); ax.annotate("애월읍", (i, peers["종합"].iloc[i]), xytext=(i, 92), ha="center", fontsize=8, arrowprops=dict(arrowstyle="->"))
ax.set_ylim(0, 100); ax.set_ylabel("종합 안전점수", fontsize=8); ax.set_title("카페: 제주 38개 읍면동 위험 등급 분포", fontsize=10)
IMG_DIST = b64(fig)
# 그림4 시간대
hi = T.hour_idx(); hrs = list(range(7, 22))
fig, ax = plt.subplots(figsize=(7.5, 2.3)); ax.bar(hrs, [hi[h] for h in hrs], color="#9ec5e8")
ax.set_xticks(hrs); ax.set_xticklabels([f"{h}시" for h in hrs], fontsize=8); ax.axhline(1, color="#aaa", lw=.6)
ax.set_title("제주 방문객 시간대별 유동인구 지수(2023~2025, 평균=1)", fontsize=10)
IMG_HOUR = b64(fig)
# 그림5 구조도
fig, ax = plt.subplots(figsize=(7.8, 3.2)); ax.axis("off")
boxes = [(0.02, "① 질문 이해\nqwen2.5:3b(JSON)\n+ 규칙·사전 검증"), (0.215, "② 값 확인·보완\n빠진 월·요일·시간\n오늘 기준 채움"),
         (0.41, "③ 도구 선택·실행\ndiagnose / compare\n/ quiet_spots"), (0.605, "④ 후속 도구 자동\nE·D등급→대안 동네\n관광 계절성 비교"),
         (0.80, "⑤ 답변·검증\n사실 템플릿\n숫자 대조·출처")]
for x, t in boxes:
    ax.add_patch(plt.Rectangle((x, 0.42), 0.18, 0.45, fc="#fff3e0", ec="#f4a340", lw=1.5)); ax.text(x + 0.09, 0.645, t, ha="center", va="center", fontsize=8)
for x, _ in boxes[:-1]:
    ax.annotate("", (x + 0.215, 0.645), (x + 0.18, 0.645), arrowprops=dict(arrowstyle="->", lw=1.3))
ax.add_patch(plt.Rectangle((0.215, 0.03), 0.57, 0.25, fc="#e8f4fd", ec="#4a90d9", lw=1.2))
ax.text(0.5, 0.155, "결정적 분석 도구(pandas) — 제주데이터허브 6종 · 가공 데이터 12MB · 인터넷 불필요", ha="center", va="center", fontsize=8)
ax.annotate("", (0.5, 0.42), (0.5, 0.28), arrowprops=dict(arrowstyle="<->", lw=1, color="#4a90d9"))
ax.set_xlim(0, 1); ax.set_ylim(0, 1)
IMG_ARCH = b64(fig)

CSS = """<style>@page{size:A4;margin:16mm 15mm}body{font-family:'Malgun Gothic',sans-serif;font-size:10.5pt;line-height:1.55;color:#222}
h1{font-size:20pt;margin:0 0 4px}h2{font-size:14pt;border-left:6px solid #f4a340;padding-left:8px;margin:18px 0 8px;page-break-after:avoid}
h3{font-size:11.5pt;margin:12px 0 4px}table{border-collapse:collapse;width:100%;font-size:9.5pt;margin:6px 0}
th,td{border:1px solid #ddd;padding:4px 6px;vertical-align:top}th{background:#fff3e0}.pb{page-break-before:always}
.box{background:#fff8ef;border:1px solid #f3d9b1;border-radius:8px;padding:8px 12px;margin:6px 0}.s{color:#666;font-size:9pt}
img{max-width:100%}.cover{text-align:center;padding-top:90px}.big{font-size:28pt;font-weight:900}.q{font-size:13pt;color:#b55a00}
.g{font-size:30pt;font-weight:900;color:#d32f2f}</style>"""


def trace_html(r):
    return "<table>" + "".join(f"<tr><td style='width:28%'><b>{a}</b></td><td>{b}</td></tr>" for a, b in r["trace"]) + "</table>"


ev_r, ev_l = EV.get("규칙", {}), EV.get("LLM+규칙", {})
SRC_ROWS = """
<tr><td>#748</td><td>상권분석을 위한 유동인구에 따른 카드 매출액 변화(매쉬업)</td><td>읍면동×업종×월 카드 이용금액·이용자수, 거주·근무·방문인구</td><td>2017.01~2021.05</td><td>창업 위험 6개 지표 계산의 중심</td></tr>
<tr><td>#793</td><td>제주특별자치도 상가(상권) 정보</td><td>상호·업종 소분류·행정동·좌표 57,865건</td><td>2025.09</td><td>동네별 같은 업종 점포 수 → 경쟁 강도</td></tr>
<tr><td>#189</td><td>내국인 관광지 입장객 수 추이</td><td>관광지×월 입장객</td><td>2009.01~2024.12</td><td>관광지 월별 혼잡(계절성)</td></tr>
<tr><td>#190</td><td>외국인 관광지 입장객 수 추이</td><td>관광지×월 입장객</td><td>2009.01~2024.12</td><td>내·외국인 합산 혼잡</td></tr>
<tr><td>#504</td><td>요일별 카드 이용 건수 비교</td><td>월×요일(공휴일 포함) 이용 건수</td><td>2018.01~2025.06</td><td>요일 혼잡 지수(최근 2023~)</td></tr>
<tr><td>#520</td><td>제주도 방문 내국인 유동인구 추이</td><td>월×시간대 방문 유동인구</td><td>2018.01~2025.04</td><td>시간대 혼잡 지수(최근 2023~)</td></tr>"""

PLAN = f"""<!doctype html><html><head><meta charset="utf-8">{CSS}</head><body>
<div class="cover"><div class="s">제주 AI·빅데이터 활용 AI Agent 개발 챌린지 · 기획서</div>
<div class="big">🍊 제주 장사·나들이 AI 비서</div>
<p class="q">“애월에 카페 차리면 괜찮수과?” · “1월 일요일, 애들이랑 실내 어디 한가하우꽈?”</p>
<p>도민이 말로 물으면, AI가 제주데이터허브 데이터를 스스로 골라 계산하고<br><b>창업 위험 등급(A~E)</b>과 <b>덜 붐비는 곳</b>을 한 장으로 돌려주는 로컬 AI Agent</p>
<div class="box" style="text-align:left;margin:40px 60px">
<b>한눈에 보기</b><br>
· 사용자: 창업을 고민하는 도민·예비 소상공인 / 주말 나들이 가족·어르신<br>
· 데이터: 제주데이터허브 6종(카드매출·상가·관광지 입장객·요일·시간대 유동인구)<br>
· 실행: 센터 PC(GTX1060 3GB)에서 <b>인터넷 없이</b> 동작 — 로컬 소형 모델 qwen2.5:3b(약 2GB)<br>
· 신뢰: 숫자는 100% 결정적 계산 코드가 생성, AI는 질문 이해만 → 같은 질문 = 같은 답<br>
· 검증: 질문 이해 {ev_l.get('정확도', ev_r.get('정확도'))}, 평균 응답 {ev_l.get('평균응답초', ev_r.get('평균응답초'))}초, 10회 반복 결과 동일</div>
<p class="s">작성일 {dt.date.today()}</p></div>

<h2 class="pb">1. 분석 주제와 목표</h2>
<h3>1-1. 문제: 제주 도민이 매일 마주치는 두 가지 질문</h3>
<table><tr><th style="width:50%">🏪 “여기서 장사해도 되나?”</th><th>🌿 “지금 어디 가야 덜 붐비나?”</th></tr>
<tr><td>제주는 관광 의존 업종이 많아 <b>계절·외부 충격에 따라 매출이 크게 출렁인다</b>. 실제로 데이터상 우도면 카페는 비수기 매출이 평균의 44% 수준까지 떨어지고, 2020년 봄 충격 때 전년 대비 62% 감소했다. 그러나 예비 창업자는 이런 숫자를 볼 방법이 없다 — 데이터는 공개돼 있지만 <b>CSV 수십 개를 직접 내려받아 가공해야</b> 한다.</td>
<td>관광객이 몰리는 제주에서 도민은 정작 주말에 갈 곳이 마땅치 않다. 관광지마다 성수기가 다르고(예: 8월 카멜리아힐은 평소의 0.53배로 오히려 한산, 만장굴은 2.97배), 요일·시간대에 따라 붐빔이 달라지지만, 이를 <b>한 번에 비교해 주는 도구가 없다</b>.</td></tr></table>
<h3>1-2. 목표</h3>
<ol><li><b>말로 묻고, 한 장으로 받는다</b>: 제주어 섞인 일상 질문 한 줄 → 등급·숫자·그래프·근거가 담긴 결과 1장(진단서 HTML 내려받기 포함).</li>
<li><b>데이터 탐색부터 결과까지 자동</b>: 어떤 데이터·지역·업종·기간을 쓸지 AI가 판단 → 계산 → 부족하면 후속 도구를 스스로 호출(대안 동네 탐색, 조건 완화 재검색).</li>
<li><b>틀린 숫자를 말하지 않는 AI</b>: 소형 모델의 환각을 구조적으로 차단 — 숫자는 계산 코드만 만들고, AI가 만든 문장은 숫자 대조 검증을 통과해야 채택.</li>
<li><b>센터 PC에서 그대로</b>: 인터넷·외부 API·유료 키 없이 동작. AI 모델이 없어도 규칙 모드로 같은 결과.</li></ol>
<h3>1-3. 차별점 — “상권 분석”이 아니라 “리스크 진단”</h3>
<p>기존 상권 분석 서비스는 “매출이 얼마인가”를 보여 준다. 본 서비스는 금융권 신용·리스크 관리에서 쓰는 방식을 소상공인 언어로 옮겨 <b>“얼마나 흔들리는가”</b>를 본다:
변동성(달마다 출렁임), 계절 쏠림, 스트레스 테스트(2020년 봄 충격 재현), 성장 추세, 관광 의존도, 경쟁 강도(점포 1곳당 매출) — 6개 지표를 같은 업종의 제주 다른 동네와 상대 비교해 <b>A~E 등급</b>으로 매긴다. 결과물 이름도 “분석 보고서”가 아니라 <b>“창업 위험 진단서”</b>다.</p>

<h2 class="pb">2. 서비스 제안</h2>
<h3>2-1. 사용 장면 ① 창업 위험 진단 (메인)</h3>
<div class="box"><b>질문</b>: “{Q1}”<br><b>AI 답</b>: {R1['answer']}</div>
<p style="text-align:center"><span class="g">{D['등급']}</span> 등급 · 제주 {D['비교지역수']}개 동네 중 {D['순위']}위</p>
<img src="{IMG_SEAS}"><p class="s">그림 1. 애월읍 카페의 월별 매출 패턴(막대)과 같은 권역 관광지 방문객(점선). 빨강=가장 어려운 달, 초록=가장 좋은 달.</p>
<img src="{IMG_FAC}"><p class="s">그림 2. 6가지 위험 지표의 안전점수. 50보다 짧으면 같은 업종 동네들 평균보다 위험.</p>
<h3>2-2. 사용 장면 ② 지역 비교 / 같은 질문 다른 업종</h3>
<div class="box"><b>질문</b>: “{Q3}”<br><b>AI 답</b>: {R3['answer']}</div>
<div class="box"><b>질문</b>: “{Q4}”<br><b>AI 답</b>: {R4['answer']}</div>
<img src="{IMG_DIST}"><p class="s">그림 3. 카페 업종의 제주 38개 읍면동 등급 분포 — 같은 업종 안에서 상대 비교하므로 “카페는 원래 위험” 같은 착시가 없다.</p>
<h3>2-3. 사용 장면 ③ 덜 붐비는 곳 (서브)</h3>
<div class="box"><b>질문</b>: “{Q2}”<br><b>AI 답</b>: {R2['answer']}</div>
<img src="{IMG_HOUR}"><p class="s">그림 4. 시간대 지수 — 같은 관광지라도 9시가 15시보다 약 23% 덜 붐빈다.</p>
<h3>2-4. 누가, 어떻게 쓰나</h3>
<table><tr><th>사용자</th><th>장면</th><th>얻는 것</th></tr>
<tr><td>예비 창업자(이주민·청년·퇴직자)</td><td>계약 전 “이 동네 이 업종” 확인</td><td>등급·비수기 매출·충격 시 매출·더 안전한 대안 동네</td></tr>
<tr><td>기존 소상공인</td><td>업종 전환·2호점 검토</td><td>같은 업종 동네 순위</td></tr>
<tr><td>창업지원 공무원·컨설턴트</td><td>상담 시 근거 자료</td><td>인쇄용 진단서(출처 명시)</td></tr>
<tr><td>도민 가족·어르신</td><td>주말·명절 나들이</td><td>조건(권역·실내·아이 동반)별 한산한 곳 3곳 + 추천 시간</td></tr></table>

<h2 class="pb">3. AI Agent 구성</h2>
<img src="{IMG_ARCH}"><p class="s">그림 5. Agent 작업 흐름. 언어모델은 ①에서만 판단하고, 숫자는 모두 아래 결정적 도구가 만든다.</p>
<h3>3-1. 작업 흐름과 자율 판단 범위</h3>
<table><tr><th style="width:18%">단계</th><th>하는 일</th><th style="width:30%">자율 판단</th></tr>
<tr><td>① 질문 이해</td><td>qwen2.5:3b가 질문을 JSON(도구·지역·업종·월·요일·시간·실내·아이)으로 변환. 동시에 규칙 파서가 같은 일을 하고 서로 대조.</td><td>어떤 도구를 쓸지 결정. 생활 지명(협재·함덕·모슬포 등 80여 개)을 43개 읍면동으로 연결.</td></tr>
<tr><td>② 값 확인·보완</td><td>빠진 값은 오늘 날짜 기준으로 채우고 화면에 명시. 지역 없이 업종만 있으면 ‘진단’→‘동네 비교’로 전환.</td><td>도구 전환·기본값 결정</td></tr>
<tr><td>③ 도구 실행</td><td>diagnose(지역,업종) / alternatives(업종) / quiet_spots(월,요일,시,권역,실내,아이)</td><td>—(결정적 계산)</td></tr>
<tr><td>④ 후속 도구</td><td>D·E등급이면 대안 동네 자동 탐색, 진단 시 같은 권역 관광 계절성 자동 비교, 나들이 조건에 맞는 곳이 없으면 조건을 풀어 재검색</td><td>추가 호출 여부 결정</td></tr>
<tr><td>⑤ 답변·검증</td><td>사실 템플릿으로 답 작성. (선택) AI 문장 다듬기는 숫자 대조 검증 통과 시에만 채택.</td><td>채택/폐기 결정</td></tr></table>
<h3>3-2. 사용 모델과 범위</h3>
<table><tr><th>구분</th><th>내용</th></tr>
<tr><td>언어모델</td><td>Qwen2.5-3B-Instruct(Ollama ‘qwen2.5:3b’, 4bit 약 1.9GB) — 로컬 실행, 인터넷·API 키 불필요. 온도 0·시드 고정.</td></tr>
<tr><td>AI가 하는 일</td><td>질문 이해(의도·지역·업종·시간 추출)만. 결과는 사전(업종 20종·지명 80여 개)으로 검증 — 사전에 없는 값은 버림.</td></tr>
<tr><td>AI가 하지 않는 일</td><td>숫자 계산, 등급 판정, 데이터 선택 이후의 모든 판단. → 환각 숫자 원천 차단.</td></tr>
<tr><td>문장 다듬기</td><td>개발 중 시험에서 3B 모델이 숫자는 지켜도 뜻을 뒤집는 사례(17위/39 → “가장 안전한 곳 중 하나”)를 확인해 <b>기본 OFF</b>. 설정(JEJU_AGENT_POLISH=1)으로 켜면 숫자 대조 검증 후 채택.</td></tr>
<tr><td>대체 동작</td><td>Ollama가 없거나 응답이 없으면 자동으로 규칙 모드 — 결과 동일(아래 5장 평가).</td></tr>
<tr><td>개발 시 AI 활용</td><td>코드 작성·문서 초안에 생성형 AI 코딩 도구를 보조로 사용. 데이터 가공·지표 설계·검증은 직접 확인.</td></tr></table>

<h2 class="pb">4. 데이터 계획</h2>
<h3>4-1. 사용 데이터(제주데이터허브, 6종)</h3>
<table><tr><th>ID</th><th>데이터명</th><th>내용</th><th>기간</th><th>용도</th></tr>{SRC_ROWS}</table>
<p class="s">출처: 제주데이터허브(jejudatahub.net) 공개 데이터. 이용 조건은 각 데이터 페이지의 이용 허락 범위를 따르며, 원본 데이터는 결과물에 포함하지 않고 가공 데이터만 포함(재생성 스크립트 제공).</p>
<h3>4-2. 전처리</h3>
<ul><li><b>카드매출(#748)</b>: 연도별 5개 파일 통합, 년월 표기 3종(2018-01-01 / 2019-01 / 21-Apr) 통일, 성별·법인 합산 → 읍면동×업종×월 61,252행.</li>
<li><b>관광지 입장객(#189·#190)</b>: ‘2023.10’이 숫자로 읽히면 ‘2023.1’(1월)로 바뀌는 함정을 발견해 문자열로 읽도록 수정(10월 데이터가 1월에 합쳐지는 오류 방지). 내·외국인 합산.</li>
<li><b>요일·시간 지수(#504·#520)</b>: 최근(2023년 이후) 자료로 평균=1 지수화. 공휴일은 월 평균 일수로 환산.</li>
<li><b>업종 연결</b>: 카드 업종명(통계분류)과 상가 업종 소분류가 서로 달라 20개 생활 업종 사전으로 연결(예: ‘카페’ = 카드 ‘비알콜 음료점업’ = 상가 ‘카페’).</li></ul>
<h3>4-3. 창업 위험 지표 정의</h3>
<table><tr><th>지표</th><th>계산</th><th>비중</th></tr>
<tr><td>변동성</td><td>2017~2019 월매출 표준편차 ÷ 평균</td><td>20%</td></tr>
<tr><td>계절 쏠림</td><td>월별 평균 매출 최고 ÷ 최저</td><td>20%</td></tr>
<tr><td>충격 민감도(스트레스)</td><td>2020.3~5 매출 ÷ 2019.3~5 매출 − 1</td><td>20%</td></tr>
<tr><td>성장 추세</td><td>2017→2019 연평균 성장률</td><td>15%</td></tr>
<tr><td>관광 의존도</td><td>방문인구 ÷ (거주+근무+방문인구)</td><td>10%</td></tr>
<tr><td>경쟁 강도</td><td>월매출 ÷ 같은 업종 점포 수(상가정보 2025.09)</td><td>15%</td></tr></table>
<p>각 지표를 <b>같은 업종의 제주 읍면동끼리 백분위</b>로 바꿔 0~100 안전점수로 만들고 가중합 → A(80+)·B(65+)·C(50+)·D(35+)·E. 표본이 작은 동네(월 300만원 미만 또는 24개월 미만)는 등급을 매기지 않고 그 사실과 대안을 안내한다.</p>
<h3>4-4. 혼잡 지수</h3>
<p>혼잡지수 = (해당 월 입장객 ÷ 그 관광지 연평균) × 요일 지수 × 시간대 지수. 1.00 = 그 관광지의 평소. 조건(권역 6개·실내·아이 동반)으로 거른 뒤 원래 한산한 하위 25%는 제외해 “갈 만한데 덜 붐비는 곳”을 고른다.</p>

<h2 class="pb">5. 개발 계획과 실행 환경</h2>
<h3>5-1. 화면</h3>
<ul><li>Streamlit 웹 화면 1개, 탭 2개(🏪 장사해도 되쿠과 / 🌿 오늘 어디 한가하우꽈). 큰 글씨(19px), 예시 질문 버튼, 입력은 질문 한 줄.</li>
<li>결과: 등급 카드 → 쉬운 설명 → 핵심 숫자 3개(평상시/가장 어려운 달/충격 때) → 그래프 2개 → 대안 동네 → <b>진단서 내려받기</b>.</li>
<li>“AI가 일한 과정” 펼치기: ①~⑤ 단계별로 무엇을 판단했는지 표시(투명성).</li></ul>
<h3>5-2. 센터 PC 실행 환경</h3>
<table><tr><th>항목</th><th>요구</th><th>센터 PC(i7-8700 / GTX1060 / RAM 32GB / VRAM 3GB)</th></tr>
<tr><td>Python</td><td>3.10 이상</td><td>설치</td></tr>
<tr><td>라이브러리</td><td>pandas, numpy, matplotlib, streamlit</td><td>run.bat이 자동 설치(오프라인 wheelhouse 지원)</td></tr>
<tr><td>AI 모델(선택)</td><td>Ollama + qwen2.5:3b, VRAM 약 2GB</td><td>GTX1060 3GB에 적재 가능. 없으면 규칙 모드</td></tr>
<tr><td>데이터</td><td>가공 데이터 약 13MB 포함</td><td>인터넷 불필요</td></tr>
<tr><td>속도</td><td>질문당 평균 {ev_l.get('평균응답초', '-')}초(AI 사용) / {ev_r.get('평균응답초', '-')}초(규칙)</td><td>개발 PC 측정값, CPU만으로도 동작</td></tr></table>
<p>실행: <b>run.bat 더블클릭</b> → 브라우저 자동 열림. 자세한 절차는 README.md.</p>

<h2>6. 결과의 신뢰성·재현성</h2>
<table><tr><th>시험</th><th>결과</th></tr>
<tr><td>질문 이해 정확도(20문항: 진단 10·비교 3·나들이 7, 제주어 포함)</td><td>규칙 모드 {ev_r.get('정확도')} · AI+규칙 {ev_l.get('정확도', '-')}</td></tr>
<tr><td>재현성</td><td>{EV.get('재현성')}</td></tr>
<tr><td>응답 시간</td><td>평균 {ev_l.get('평균응답초', ev_r.get('평균응답초'))}초, 최대 {ev_l.get('최대응답초', ev_r.get('최대응답초'))}초</td></tr></table>
<p class="s">※ 20문항은 개발자가 만든 시험 문항으로, 실제 도민 질문에서의 정확도는 이보다 낮을 수 있다. 사전에 없는 지명·업종은 “가능한 목록”을 안내한다.</p>
<h3>한계와 대응</h3>
<ul><li><b>카드매출 기간</b>: 읍면동×업종 카드 데이터가 2021.05까지만 공개 → 지표는 2017~2019 평상시 + 2020 충격으로 계산하고, 화면·진단서에 기간을 명시. 최신 상가 수(2025.09)로 경쟁 강도를 보완.</li>
<li><b>동네 전체 통계</b>: 개별 가게의 성패를 예측하지 않으며 “참고 지표”임을 진단서에 명시.</li>
<li><b>혼잡 예측</b>: 실시간이 아닌 월·요일·시간 패턴 기반. 날씨·행사 등 당일 변수는 반영하지 않음.</li></ul>
<h3>확장 계획</h3>
<ul><li>데이터허브 신규 업데이트 시 build_data.py 재실행만으로 지표 갱신.</li>
<li>진단 업종 20종 → 확대, 임대료·폐업 데이터 연계 시 ‘폐업 위험’ 지표 추가.</li>
<li>센터 상담 창구용 ‘상담 모드’(여러 동네 진단서 일괄 출력).</li></ul>
</body></html>"""

RESULT = f"""<!doctype html><html><head><meta charset="utf-8">{CSS}</head><body>
<h1>결과 설명자료 — 🍊 제주 장사·나들이 AI 비서</h1>
<p class="s">생성일 {dt.datetime.now():%Y-%m-%d %H:%M} · 아래 결과는 모두 실제 실행 출력입니다(outputs/ 폴더에 원본).</p>
<h2>1. 문제 정의</h2><p>도민이 “여기서 장사해도 되나”, “어디 가야 덜 붐비나”를 말로 물으면, 제주데이터허브 데이터로 근거 있는 답(등급·숫자·그래프·출처)을 돌려준다. 공개 데이터는 있지만 가공 장벽 때문에 도민이 쓰지 못하는 문제를 Agent로 해결한다.</p>
<h2>2. Agent 구조</h2><img src="{IMG_ARCH}">
<p>언어모델(qwen2.5:3b, 로컬)은 질문 이해만 맡고, 숫자는 결정적 분석 도구가 계산한다. 언어모델 결과는 규칙·사전으로 재검증한다.</p>
<h2>3. 실행 결과</h2>
<h3>예시 1 — {Q1}</h3>{trace_html(R1)}<div class="box">{R1['answer']}</div><img src="{IMG_SEAS}"><img src="{IMG_FAC}">
<h3>예시 2 — {Q4}</h3>{trace_html(R4)}<div class="box">{R4['answer']}</div>
<h3>예시 3 — {Q3}</h3>{trace_html(R3)}<div class="box">{R3['answer']}</div>
<h3>예시 4 — {Q2}</h3>{trace_html(R2)}<div class="box">{R2['answer']}</div>
<h2>4. 평가</h2><table><tr><th>항목</th><th>규칙 모드</th><th>AI+규칙 모드</th></tr>
<tr><td>질문 이해 정확도(20문항)</td><td>{ev_r.get('정확도')}</td><td>{ev_l.get('정확도', '-')}</td></tr>
<tr><td>평균/최대 응답(초)</td><td>{ev_r.get('평균응답초')} / {ev_r.get('최대응답초')}</td><td>{ev_l.get('평균응답초', '-')} / {ev_l.get('최대응답초', '-')}</td></tr></table>
<p>재현성: {EV.get('재현성')}. 개발 중 발견·수정한 문제: (1) 관광지 날짜 ‘2023.10’이 1월로 합쳐지는 오류, (2) AI가 ‘다음 주말’을 7월로 지어내는 문제 → 숫자는 질문에 숫자가 있을 때만 AI 값을 받도록 차단, (3) AI 문장 다듬기가 순위의 뜻을 뒤집는 문제 → 기본 OFF.</p>
<h2>5. 한계</h2><ul><li>읍면동×업종 카드매출이 2021.05까지만 공개 → 평상시(2017~2019)·충격(2020) 기준 지표. 기간을 결과에 명시.</li>
<li>동네 전체 통계 기반 참고 지표이며 개별 점포 성패를 예측하지 않음.</li><li>혼잡도는 월·요일·시간 패턴 기반(실시간 아님).</li>
<li>시험 20문항은 개발자 작성 문항 — 실사용 정확도는 낮을 수 있음.</li></ul>
<h2>6. 사용 데이터</h2><table><tr><th>ID</th><th>데이터명</th><th>내용</th><th>기간</th><th>용도</th></tr>{SRC_ROWS}</table>
</body></html>"""

open(os.path.join(DOCS, "기획서.html"), "w", encoding="utf-8").write(PLAN)
open(os.path.join(DOCS, "결과설명자료.html"), "w", encoding="utf-8").write(RESULT)
json.dump({"Q1": R1["answer"], "Q2": R2["answer"], "Q3": R3["answer"], "Q4": R4["answer"]},
          open(os.path.join(ROOT, "outputs", "examples.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
for n in ("기획서", "결과설명자료"):
    src = os.path.join(DOCS, n + ".html"); dst = os.path.join(DOCS, n + ".pdf")
    subprocess.run([EDGE, "--headless", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={dst}",
                    "file:///" + src.replace("\\", "/")], capture_output=True, timeout=120)
    print(n, os.path.exists(dst), os.path.getsize(dst) if os.path.exists(dst) else 0)
