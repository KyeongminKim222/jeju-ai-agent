"""기획서 v4 — IRB 검토용 자료 디자인(가로 297x167mm 슬라이드형) 적용, 로고 없음.
v3의 계산·그래프 부분을 그대로 실행(팔레트만 교체)한 뒤 새 레이아웃으로 출력.
"""
import os, sys, subprocess
sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(ROOT, "make_plan_v3.py"), encoding="utf-8").read()
pre = src[:src.index('CSS = f"""')]
pre = pre.replace('TAN, BAS, SEA, CRM, JAD, GRY, LGRY = "#F26B1D", "#1B1F23", "#0B3C5D", "#FAF6EF", "#2EC4B6", "#8A94A3", "#D9DEE5"',
                  'TAN, BAS, SEA, CRM, JAD, GRY, LGRY = "#A3242A", "#0B2A4A", "#0B2A4A", "#F4F9FD", "#0067AC", "#9AA6B8", "#D5DEE8"')
pre = pre.replace('GC = {"A": "#2EC4B6", "B": "#7DCFB6", "C": "#E9B949", "D": "#F29B54", "E": "#F26B1D"}',
                  'GC = {"A": "#0067AC", "B": "#4FB3E8", "C": "#9AA6B8", "D": "#D98A3A", "E": "#A3242A"}')
g = {"__file__": os.path.join(ROOT, "make_plan_v3.py"), "__name__": "plan"}
exec(compile(pre, "v3pre", "exec"), g)
globals().update({k: v for k, v in g.items() if not k.startswith("__")})

CSS = open(os.path.join(ROOT, "docs", "assets", "irb_style.css"), encoding="utf-8").read()
CSS += """
.shot{border:1px solid var(--line);border-radius:10px;overflow:hidden;background:#fff;display:flex;flex-direction:column}
.shot .bar{height:4mm;background:#EEF2F6;flex:none;display:flex;gap:1.2mm;align-items:center;padding-left:2.5mm}
.shot .bar i{width:1.6mm;height:1.6mm;border-radius:50%;background:#c3ccd8;display:block}
.fimg{width:100%;height:100%;object-fit:contain;display:block}
.qa{border-left:3px solid var(--wb);background:var(--tint2);border-radius:0 8px 8px 0;padding:2.4mm 4mm;font-size:10pt;line-height:1.45}
.qa .q{font-weight:700;color:var(--navy);margin-bottom:1mm}
.code{font-family:Consolas,monospace;font-size:9pt;background:var(--navy);color:#e6eef7;border-radius:6px;padding:2.5mm 3mm;line-height:1.45;white-space:pre-wrap;word-break:break-all}
.lk{display:flex;gap:3mm;align-items:center;border:1px solid var(--line);border-radius:8px;padding:2mm;background:#fff}
.lk img{width:20mm;height:20mm;flex:none}
.lk b{display:block;font-size:10.5pt;line-height:1.25}.lk span{display:block;font-size:8pt;color:var(--mute);word-break:break-all;line-height:1.25;margin-top:1mm}
.grade{font-size:70pt;font-weight:700;line-height:.9;color:#A3242A}
.kp .kl{font-size:10pt;color:var(--mute)}.kp .kv{font-size:19pt;font-weight:700;color:var(--navy);line-height:1.2}.kp .ks{font-size:9.5pt;color:var(--mute)}
.body .card .mid{font-size:11.5pt;line-height:1.42}.body .card{padding:4.5mm 5mm}.body .sphere{width:11mm;height:11mm}.body .key{font-size:12.5pt}
.vrow .pills span{font-size:9pt}.flow .st .d{font-size:10.5pt}
"""

REPO = "https://github.com/KyeongminKim222/jeju-ai-agent"
LINKS2 = [("GitHub 저장소 (코드·매뉴얼)", REPO)] + LINKS
LINK_HTML2 = "".join(f"<div class='lk'><img src='{qr(u)}'><div><b>{t}</b><span>{u.replace('https://', '')}</span></div></div>" for t, u in LINKS2)
NP = 11


def sl(no, part, title, body, n, ft=""):
    return f"""<div class="s"><div class="topbar"></div><div class="hd"><div class="part">{no} · {part}</div></div>
<h1>{title}</h1><div class="body">{body}</div>{f'<div class="ft">{ft}</div>' if ft else ''}<div class="pn">{n}</div></div>"""


pct = lambda a, b: f"{(1 - a / b) * 100:.0f}%"
COVER = f"""<div class="s cover">
 <div class="top"><div class="kic" style="margin:0">제주 AI·빅데이터 활용 AI Agent 개발 챌린지 2026</div><div class="kic" style="margin:0">기획서</div></div>
 <div class="mid-b">
  <div class="kic">JEJU DATA HUB · LOCAL AI AGENT</div>
  <h1 style="font-size:34pt">말로 물으면 데이터가 답하는<br><em>제주 장사·나들이 AI 비서</em></h1>
  <div class="sub">“{Q1}” → 창업 위험 등급(A~E) · “1월 일요일 애들이랑 실내 어디 한가하우꽈?” → 덜 붐비는 곳</div>
  <div style="margin-top:6mm;display:flex;gap:4mm">
   <div class="card t" style="flex:1;padding:3.5mm 5mm"><div class="sm">실제 실행 결과 · 애월읍 카페</div><div class="mid"><b style="color:#A3242A">{D['등급']}등급</b> — {D['비교지역수']}곳 중 {D['순위']}위 · 대안 <b>{a0['지역']} {a0['등급']}</b></div></div>
   <div class="card t" style="flex:1;padding:3.5mm 5mm"><div class="sm">데이터</div><div class="mid">제주데이터허브 <b>6종</b> · 오프라인</div></div>
   <div class="card t" style="flex:1;padding:3.5mm 5mm"><div class="sm">신뢰</div><div class="mid">질문 이해 <b>{EL['정확도']}</b> · 숫자는 100% 코드</div></div>
  </div></div>
 <svg class="wave" viewBox="0 0 1000 160" preserveAspectRatio="none"><path d="M0,70 C200,10 350,130 550,70 C750,10 880,110 1000,60 L1000,160 L0,160 Z" fill="#0067AC"/><path d="M0,100 C220,50 380,150 600,95 C800,45 900,130 1000,90 L1000,160 L0,160 Z" fill="#4FB3E8" opacity=".85"/></svg>
 <div class="meta">코드·매뉴얼: {REPO.replace('https://', '')}<br>모든 수치는 실제 실행 결과 · 센터 PC(GTX1060 3GB) 오프라인 동작</div>
</div>"""

S2 = sl("01", "문제 정의", "제주에선 <em>같은 카페도 동네에 따라</em> 운명이 갈린다 — 그런데 볼 도구가 없다", f"""
<div class="g3">
 <div class="card t"><div class="sphere" style="margin-bottom:3mm"></div><h3>흔들림이 크다</h3><div class="mid">우도면 카페 — 가장 어려운 {U['최악의달']}월 매출이 평소의 <b>{U['최악의달비율']*100:.0f}%</b><br>2020년 봄 충격 때 <b>{U_shock*100:.0f}%</b><br><br>같은 카페 {len(peers)}개 동네 점수 폭 <b>{peers['종합'].min():.0f}~{peers['종합'].max():.0f}점</b></div></div>
 <div class="card t"><div class="sphere" style="margin-bottom:3mm"></div><h3>데이터는 있는데 못 쓴다</h3><div class="mid">공개 CSV 수십 개를 <b>직접 내려받아 가공</b>해야 함<br><br>기존 상권 분석은 “얼마 버나(평균)”만 — <b>“얼마나 흔들리나(위험)”</b>는 없음<br><br>관광지 혼잡도 달·요일·시간 비교 도구 없음</div></div>
 <div class="card w"><div class="sphere" style="margin-bottom:3mm;background:radial-gradient(circle at 50% 38%,#fff 0 25%,#bfe3fa 45%,#4FB3E8 100%)"></div><h3>그래서 — 말로 묻는 Agent</h3><div class="mid">질문 한 줄 → Agent가 <b>데이터·지역·업종·기간을 스스로 선택</b><br><br>등급·숫자·그래프·근거를 <b>진단서 한 장</b>으로<br><br>결과가 나쁘면 <b>대안 동네까지 자동 탐색</b></div></div>
</div>
<div class="key">은행이 대출을 심사하듯 <em>동네를 심사</em>한다 — 금융권 신용리스크 방식을 소상공인 언어로</div>""", 2,
              "출처: 제주데이터허브 #748 카드매출 · #793 상가정보 (실제 계산값)")

S3 = sl("02", "핵심 결과", f"“애월에 카페 차리면?” — <em>{D['등급']}등급</em>, 대신 {a0['지역']}이면 {a0['등급']}", f"""
<div class="two">
 <div class="card t" style="flex-direction:row;gap:6mm;align-items:center">
  <div><div class="grade">{D['등급']}</div><div class="sm" style="text-align:center">위험 {D['위험수준']}</div></div>
  <div style="flex:1;display:flex;flex-direction:column;gap:3mm">
   <div class="mid">제주 카페 동네 <b>{D['비교지역수']}곳 중 {D['순위']}위</b> · {D['종합점수']:.0f}점/100</div>
   <div style="display:flex;gap:4mm">
    <div class="kp"><div class="kl">평상시 월매출</div><div class="kv">{won(S['평상시월매출'])}</div><div class="ks">동네 카페 전체</div></div>
    <div class="kp"><div class="kl">{D['최악의달']}월(최저)</div><div class="kv">{won(S['비수기월매출'])}</div><div class="ks">−{pct(S['비수기월매출'], S['평상시월매출'])}</div></div>
    <div class="kp"><div class="kl">2020 봄 충격</div><div class="kv">{won(S['충격시월매출'])}</div><div class="ks">−{pct(S['충격시월매출'], S['평상시월매출'])}</div></div></div>
   <div class="mid">약점: <b>{D['약점'][0]['설명']}</b> · <b>{D['약점'][1]['설명']}</b></div></div></div>
 <div class="card"><h3>Agent가 스스로 찾은 대안 동네</h3>
  {''.join(f"<div style='display:flex;align-items:center;gap:3mm;padding:2.2mm 0;border-bottom:1px solid var(--line)'><span class='tag' style='background:{GC[x['등급']]};color:#fff;font-size:12pt;padding:0 9px'>{x['등급']}</span><b style='font-size:14pt'>{x['지역']}</b><span class='sm' style='margin-left:auto'>{x['종합점수']:.0f}점 · 월매출 {won(x['월평균매출'])}</span></div>" for x in ALT)}
  <div class="sm" style="margin-top:3mm">D·E등급이 나오면 묻지 않아도 후속 도구(alternatives)를 자동 호출</div></div>
</div>
<div class="key">답을 먼저 — <em>등급 · 최악의 달 · 충격 시 매출 · 대안 동네</em>가 질문 한 줄에 {T1:.1f}초</div>""", 3,
              "실제 실행 결과 (core.run, 개발 PC 실측)")

S4 = sl("03", "진단 방법", "창업 위험 <em>6대 지표</em> — 같은 업종 제주 동네 안에서의 백분위로 A~E", f"""
<div class="three">
 <div class="axis"><div class="t"><i>1</i>흔들림</div><ul><li><b>변동성</b> 월매출 표준편차÷평균 (20%)</li><li><b>계절 쏠림</b> 최고달÷최저달 (20%)</li></ul><div class="map">#748 카드매출 2017~2019</div></div>
 <div class="axis"><div class="t"><i>2</i>버티는 힘</div><ul><li><b>충격 민감도</b> 2020.3~5 ÷ 2019.3~5 − 1 (20%) — 스트레스 테스트</li><li><b>성장 추세</b> 2017→2019 연평균 (15%)</li></ul><div class="map">#748 카드매출 2019~2020</div></div>
 <div class="axis"><div class="t"><i>3</i>구조</div><ul><li><b>관광 의존도</b> 방문인구÷전체 (10%)</li><li><b>경쟁 강도</b> 월매출÷같은 업종 점포 수 (15%)</li></ul><div class="map">#748 유동인구 · #793 상가 2025.09</div></div>
</div>
<div class="g2" style="flex:0 0 46mm;margin-top:4mm">
 <div class="card" style="padding:2mm"><img class="fimg" src="{IMG_IND}"></div>
 <div class="card" style="padding:2mm"><img class="fimg" src="{IMG_SEAS}"></div></div>
<div class="key">등급 = 지표별 백분위 × 비중 → <em>A 80+ · B 65+ · C 50+ · D 35+ · E</em> — 같은 업종끼리만 비교해 “카페는 원래 위험” 착시 제거</div>""", 4)

flow_tool = "<br>".join(b for a, b in TRACE if a.startswith("③") or a.startswith("④"))
S5 = sl("04", "AI Agent 작동 방식", "AI는 <em>질문 이해만</em>, 숫자는 100% 계산 코드 — 환각 숫자 차단", f"""
<div class="flow">
 <div class="st"><div class="h">① 질문 이해</div><div class="d">qwen2.5:3b → JSON<br>규칙 파서와 교차검증<br>사전 밖 값은 폐기</div><div class="a">AI</div></div><div class="ar">→</div>
 <div class="st"><div class="h">② 값 보완</div><div class="d">빠진 월·요일·시간<br>오늘 기준으로 채움<br>화면에 명시</div><div class="a">AI + 규칙</div></div><div class="ar">→</div>
 <div class="st hi"><div class="h">③ 도구 실행</div><div class="d">diagnose · alternatives<br>quiet_spots<br>pandas 결정적 계산</div><div class="a">CODE</div></div><div class="ar">→</div>
 <div class="st hi"><div class="h">④ 후속 도구</div><div class="d">D·E → 대안 동네<br>관광 계절성 비교<br>조건 완화 재검색</div><div class="a">CODE</div></div><div class="ar">→</div>
 <div class="st hi"><div class="h">⑤ 답변·검증</div><div class="d">사실 템플릿<br>숫자 대조 검증<br>출처·기간 명시</div><div class="a">CODE</div></div>
</div>
<div style="margin-top:4mm" class="vrow"><div class="lb">실제 기록<br><span style="font-weight:400;color:var(--mute)">“{Q1}”</span></div>
 <div class="pills"><span class="on">{TRACE[0][1]}</span><span>{TRACE[1][1]}</span><span class="on">{flow_tool}</span><span class="on">{TRACE[-1][0]} · {T1:.2f}초</span></div></div>
<div class="key">개발 중 3B 모델이 “39곳 중 17위”를 “가장 안전한 곳 중 하나”로 뒤집음 → <em>문장 다듬기 기본 OFF</em>, 숫자는 AI에 맡기지 않는다</div>""", 5,
              "모델: Qwen2.5-3B-Instruct (Ollama, 4bit 약 1.9GB, 온도 0) · 모델 없으면 규칙 모드로 같은 결과")

S6 = sl("05", "데모 ① 장사해도 되쿠과", "실제 화면 — <em>질문 한 줄</em>이면 등급·그래프·대안·진단서", f"""
<div class="wrap">
 <div class="shot" style="flex:0 0 105mm"><div class="bar"><i></i><i></i><i></i></div><div style="flex:1;background:url('{img('crop_diag.jpg')}') top center/100% auto no-repeat"></div></div>
 <div style="flex:1;display:flex;flex-direction:column;gap:3mm">
  <div class="qa"><div class="q">Q. {Q4}</div>{R4['answer'][:230]}…</div>
  <div class="qa"><div class="q">Q. {Q3}</div>{R3['answer'][:200]}…</div>
  <div class="card" style="flex:1;padding:2mm"><img class="fimg" src="{IMG_DIST}"></div>
 </div></div>""", 6, "▲ 왼쪽: 실제 앱(Streamlit) 실행 화면 캡처 · 진단서는 인쇄용 HTML로 내려받기")

spot = "".join(f"<div style='display:flex;gap:3mm;padding:2mm 0;border-bottom:1px solid var(--line);font-size:12pt'><b style='color:var(--wb)'>{i+1}</b><b>{x['관광지']}</b><span class='sm' style='margin-left:auto'>{x['권역']} · 혼잡 {x['혼잡지수']:.2f} · 시간당 약 {x['예상시간당']}명</span></div>" for i, x in enumerate(SPOTS))
av = AVOID[0] if AVOID else None
S7 = sl("06", "데모 ② 오늘 어디 한가하우꽈", "1월 일요일, 아이와 갈 <em>한가한 실내</em> 3곳을 고른다", f"""
<div class="wrap">
 <div class="shot" style="flex:0 0 100mm"><div class="bar"><i></i><i></i><i></i></div><div style="flex:1;background:url('{img('crop_quiet.jpg')}') top center/100% auto no-repeat"></div></div>
 <div style="flex:1;display:flex;flex-direction:column;gap:3mm">
  <div class="qa"><div class="q">Q. {Q2}</div>{R2['answer'][:120]}…</div>
  <div class="card" style="padding:3mm 5mm"><h3 style="font-size:13pt;margin-bottom:1mm">추천 3곳</h3>{spot}
   {f"<div class='sm' style='margin-top:2mm'>가장 붐빌 곳: <b style='color:#A3242A'>{av['관광지']}</b> (혼잡 {av['혼잡지수']:.2f})</div>" if av else ''}</div>
  <div class="card" style="height:34mm;flex:none;padding:1.5mm;align-items:center"><img src="{IMG_HOUR}" style="height:100%;width:auto;display:block"></div>
 </div></div>""", 7, "혼잡지수 = (그 달 입장객÷연평균) × 요일 지수 × 시간대 지수 · 원래 한산한 하위 25% 제외 · #189·#190·#504·#520")

SRC = [("#748", "카드매출×유동인구(매쉬업)", "읍면동×업종×월 카드 이용금액, 거주·근무·방문인구", "2017.01~2021.05", "6대 지표"),
       ("#793", "상가(상권) 정보", "업종 소분류·행정동·좌표 57,865건", "2025.09", "경쟁 강도"),
       ("#189", "내국인 관광지 입장객", "관광지×월 입장객", "2009~2024", "월별 혼잡"),
       ("#190", "외국인 관광지 입장객", "관광지×월 입장객", "2009~2024", "내·외 합산"),
       ("#504", "요일별 카드 이용 건수", "월×요일(공휴일 포함)", "2018~2025.06", "요일 지수"),
       ("#520", "방문 내국인 유동인구", "월×시간대 방문 유동인구", "2018~2025.04", "시간대 지수")]
rows = "".join(f"<div class='c'>{a}</div><div class='ko'><b>{b}</b></div><div class='vn'>{c}</div><div class='vn'>{d}</div><div class='vn'>{e}</div>" for a, b, c, d, e in SRC)
S8 = sl("07", "데이터 계획", "제주데이터허브 <em>6종</em>이 하나의 등급이 되기까지", f"""
<div class="tb" style="grid-template-columns:16mm 1.3fr 1.5fr 30mm 28mm;flex:0 0 auto">
 <div class="h">ID</div><div class="h">데이터명</div><div class="h">내용</div><div class="h">기간</div><div class="h">용도</div>{rows}</div>
<div class="g3" style="margin-top:4mm;flex:1">
 <div class="card t" style="padding:4mm 5mm"><h3 style="font-size:13pt">카드매출 정제</h3><div class="sm" style="color:var(--ink)">5개 파일 통합 · 년월 표기 3종 통일 · 성별·법인 합산 → <b>61,252행</b></div></div>
 <div class="card t" style="padding:4mm 5mm"><h3 style="font-size:13pt">날짜 함정 수정</h3><div class="sm" style="color:var(--ink)">‘2023.10’이 숫자로 읽혀 <b>10월이 1월로</b> 합쳐지던 오류 발견 → 문자열로 읽기</div></div>
 <div class="card t" style="padding:4mm 5mm"><h3 style="font-size:13pt">사전 연결</h3><div class="sm" style="color:var(--ink)">카드 업종↔상가 소분류 <b>{len(T.BIZ)}개 업종</b> · 생활 지명 80여 개 → 43개 읍면동</div></div>
</div>""", 8, "원본은 결과물에 미포함 · 가공 데이터 + 재생성 스크립트(build_data.py) 제공")

S9 = sl("08", "신뢰성 · 재현성", "<em>20문 20답</em>, 같은 질문 10회 같은 답 — 센터 PC에서 그대로", f"""
<div class="nums">
 <div class="num"><div class="q">질문 이해 {EL['정확도']}</div><div class="w">제주어 포함 20문항(진단 10·비교 3·나들이 7). 규칙만으로도 {ER['정확도']}</div><div class="r">outputs/eval.json</div></div>
 <div class="num"><div class="q">평균 {EL['평균응답초']}초</div><div class="w">최대 {EL['최대응답초']}초 · 규칙 모드 {ER['평균응답초']}초. CPU만으로 동작</div><div class="r">개발 PC 측정</div></div>
 <div class="num"><div class="q">재현 10/10</div><div class="w">온도 0·시드 고정 + 결정적 계산 → 같은 질문 = 같은 답</div><div class="r">tests/eval.py</div></div>
 <div class="num"><div class="q">클린 설치 통과</div><div class="w">새 폴더에 zip만 풀고 새 가상환경으로 실행 — AI 모델 없는 상태에서도 같은 결과</div><div class="r">run.bat</div></div>
 <div class="num"><div class="q">GPU 약 2GB</div><div class="w">센터 PC GTX1060 3GB에 적재 · 인터넷·API 키 불필요</div><div class="r">Ollama qwen2.5:3b</div></div>
 <div class="num"><div class="q">한계 공개</div><div class="w">카드매출 2021.05까지 · 동네 단위 참고 지표 · 혼잡은 실시간 아님(패턴)</div><div class="r">화면·진단서에 명시</div></div>
</div>
<div class="key">심사는 “있는가”가 아니라 <em>“재현되는가”</em> — tests/smoke.py · tests/eval.py로 누구나 다시 돌려볼 수 있다</div>""", 9)

S10 = sl("09", "개발·탑재 계획", "<em>run.bat 더블클릭</em> — 센터 PC에서 바로 실행", f"""
<div class="g2">
 <div class="card t"><h3>화면 (Streamlit, 탭 2개)</h3><div class="mid">• 큰 글씨, 예시 질문 버튼, 입력은 질문 한 줄<br>• 결과: 등급 카드 → 쉬운 설명 → 핵심 숫자 3개 → 그래프 → 대안 동네 → <b>진단서 내려받기</b><br>• “AI가 일한 과정” 펼치기로 단계별 판단 공개</div></div>
 <div class="card"><h3>실행 환경</h3><div class="code">&gt; run.bat                 # venv·라이브러리 자동 설치 → 브라우저 열림
&gt; python build_data.py   # 데이터허브 갱신 시 재빌드
&gt; python tests\\smoke.py   # 대표 질문 점검
&gt; python tests\\eval.py    # 정확도·재현성</div>
 <div class="sm" style="margin-top:3mm;color:var(--ink)">Python 3.10+ · pandas·numpy·matplotlib·streamlit · Ollama(선택) · 가공 데이터 약 13MB 포함</div></div>
</div>
<div class="key">다음 단계 — <em>업종 확대 · 임대료·폐업 데이터 연계 · 센터 상담 모드(진단서 일괄 출력)</em></div>""", 10,
               "개발 시 생성형 AI 코딩 도구를 보조로 사용 · 데이터 가공·지표 설계·수치 검증은 실행 결과로 직접 확인")

S11 = sl("10", "관련 링크", "휴대폰으로 <em>QR</em>을 찍으면 바로 열린다", f"""
<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:3mm;flex:1;align-content:start">{LINK_HTML2}</div>""", 11,
               "결과물 zip: README.md · 데이터_활용_명세.md · docs/사용자매뉴얼.md · tests/ · outputs/eval.json")

HTML = f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>제주 장사·나들이 AI 비서 — 기획서</title><style>{CSS}</style></head><body>{COVER}{S2}{S3}{S4}{S5}{S6}{S7}{S8}{S9}{S10}{S11}</body></html>"
srcp = os.path.join(ROOT, "docs", "기획서.html"); dst = os.path.join(ROOT, "docs", "기획서.pdf")
open(srcp, "w", encoding="utf-8").write(HTML)
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
subprocess.run([EDGE, "--headless", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={dst}", "file:///" + srcp.replace("\\", "/")], capture_output=True, timeout=180)
print("OK", os.path.getsize(dst))
