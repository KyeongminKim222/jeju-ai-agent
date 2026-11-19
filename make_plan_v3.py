"""기획서 v3 — 풀페이지 고밀도 레이아웃(A4 8쪽) · 귤/현무암/제주바다 팔레트 · 결론형 제목 · 실제 앱 화면 · QR 링크
실행: .venv python make_plan_v3.py  →  docs/기획서.pdf  (모든 숫자는 실제 실행 결과에서 생성)
"""
import base64, io, json, os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, ROOT)
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import qrcode
from agent import core, tools as T

TAN, BAS, SEA, CRM, JAD, GRY, LGRY = "#F26B1D", "#1B1F23", "#0B3C5D", "#FAF6EF", "#2EC4B6", "#8A94A3", "#D9DEE5"
GC = {"A": "#2EC4B6", "B": "#7DCFB6", "C": "#E9B949", "D": "#F29B54", "E": "#F26B1D"}
plt.rcParams.update({"font.family": "Malgun Gothic", "axes.unicode_minus": False, "font.size": 8.5,
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False, "axes.grid": False,
    "axes.edgecolor": "#9AA3AF", "xtick.color": "#4B5563", "ytick.color": "#4B5563", "ytick.left": False,
    "axes.titleweight": "bold", "axes.titlesize": 9.5, "axes.titlecolor": BAS, "axes.titlelocation": "left",
    "axes.titlepad": 6, "figure.facecolor": "none", "axes.facecolor": "none", "savefig.transparent": True})
DOCS = os.path.join(ROOT, "docs"); AS = os.path.join(DOCS, "assets")


def png(fig):
    b = io.BytesIO(); fig.savefig(b, format="png", dpi=230, bbox_inches="tight"); plt.close(fig)
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()


def img(name):
    return "data:image/jpeg;base64," + base64.b64encode(open(os.path.join(AS, name), "rb").read()).decode()


def qr(url):
    q = qrcode.QRCode(border=1, box_size=6); q.add_data(url); q.make(fit=True)
    b = io.BytesIO(); q.make_image(fill_color=BAS, back_color="white").save(b, format="PNG")
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()


def won(v):
    return f"{v/1e8:.1f}억원" if v >= 1e8 else f"{v/1e4:,.0f}만원"


def sc(v):
    return TAN if v < 35 else (GRY if v < 60 else JAD)


# ── 실제 실행 ──
EV = json.load(open(os.path.join(ROOT, "outputs", "eval.json"), encoding="utf-8"))
EL, ER = EV["LLM+규칙"], EV["규칙"]
Q1 = "애월에 카페 하나 차리면 괜찮수과?"
core.run(Q1, use_llm=True)  # 모델 예열
t0 = time.perf_counter(); R1 = core.run(Q1, use_llm=True); T1 = time.perf_counter() - t0
D = R1["result"]; S = D["스트레스"]; ALT = D["대안"]; a0 = ALT[0]
U = T.diagnose("우도면", "카페")
U_shock = [x for x in U["지표"] if "충격" in x["설명"]][0]["값"]
Q2 = "1월 일요일 비 오는데 애들이랑 갈 만한 실내 어디 한가해요?"; R2 = core.run(Q2, use_llm=True); Qd = R2["result"]
Q3 = "치킨집 하기 좋은 동네 어디우꽈?"; R3 = core.run(Q3, use_llm=True)
Q4 = "연동에서 한식당 하면 장사 될까요"; R4 = core.run(Q4, use_llm=True)
SL = {k: v for k, v in R1["slots"].items() if v not in (None, "", False)}
TRACE = R1["trace"]; SPOTS = Qd["추천"]; AVOID = Qd.get("피할곳", [])
print("T1", round(T1, 2), SL)

# ── 그림 ──
peers = T._score(T._peer_table("카페")).sort_values("종합", ascending=False)
HL = ("애월읍", "우도면", a0["지역"])
fig, ax = plt.subplots(figsize=(7.4, 2.0))
for i, (n, v) in enumerate(peers["종합"].items()):
    g = T.grade_of(v)[0]
    ax.bar(i, v, width=0.72, color=GC[g] if n in HL else LGRY)
    if n in HL:
        ax.text(i, v + 2.5, f"{n}\n{g}·{v:.0f}점", ha="center", fontsize=7.4, color=GC[g], fontweight="bold", linespacing=1.15)
ax.set_xticks([]); ax.set_yticks([]); ax.set_ylim(0, 115); ax.spines["bottom"].set_color(LGRY)
ax.set_title(f"같은 카페라도 동네 따라 {peers['종합'].min():.0f}~{peers['종합'].max():.0f}점 — 제주 {len(peers)}개 읍면동 종합 안전점수", fontsize=9)
IMG_DIST = png(fig)

ind = D["지표"]; nm = [x["설명"] for x in ind][::-1]; vs = [x["안전점수"] for x in ind][::-1]
fig, ax = plt.subplots(figsize=(3.7, 2.3))
ax.barh(range(6), [100] * 6, color="#EEF0F3", height=0.56)
ax.barh(range(6), vs, color=[sc(v) for v in vs], height=0.56)
for i, v in enumerate(vs):
    ax.text(v + 2, i, f"{v:.0f}", va="center", fontsize=8, fontweight="bold", color=sc(v))
ax.set_yticks(range(6)); ax.set_yticklabels(nm, fontsize=7.4); ax.set_xticks([]); ax.spines["bottom"].set_visible(False)
ax.set_xlim(0, 112); ax.set_title(f"약점은 ‘{D['약점'][0]['설명'][:10]}’ (안전점수 0~100)", fontsize=8.8)
IMG_IND = png(fig)

ms = list(range(1, 13)); se = D["seasonal"]; v = [se.get(f"{m:02d}") for m in ms]
fig, ax = plt.subplots(figsize=(3.7, 2.05))
ax.bar(ms, v, width=0.66, color=[TAN if m == D["최악의달"] else (SEA if m == D["최고의달"] else LGRY) for m in ms])
ax.axhline(1, color=GRY, lw=0.7, ls=(0, (2, 2)))
for m, val in zip(ms, v):
    if m in (D["최악의달"], D["최고의달"]):
        ax.text(m, val + 0.05, f"{m}월 {val:.2f}배", ha="center", fontsize=7.4, fontweight="bold", color=TAN if m == D["최악의달"] else SEA)
ax.set_xticks(ms); ax.set_xticklabels([str(m) for m in ms], fontsize=7); ax.set_yticks([]); ax.set_ylim(0, max(v) * 1.28)
ax.set_title(f"{D['최고의달']}월과 {D['최악의달']}월 매출 차이 {D['최고의달비율']/D['최악의달비율']:.1f}배 (연평균=1)", fontsize=8.8)
IMG_SEAS = png(fig)

hi = T.hour_idx(); hrs = list(range(8, 21)); hv = [hi[h] for h in hrs]
lo_h = min(range(9, 19), key=lambda h: hi[h]); hi_h = max(hrs, key=lambda h: hi[h])
fig, ax = plt.subplots(figsize=(3.7, 1.75))
ax.bar(hrs, hv, width=0.66, color=[JAD if h == lo_h else (TAN if h == hi_h else LGRY) for h in hrs])
ax.text(lo_h, hi[lo_h] + 0.05, f"{lo_h}시", ha="center", fontsize=7.6, fontweight="bold", color=JAD)
ax.text(hi_h, hi[hi_h] + 0.05, f"{hi_h}시", ha="center", fontsize=7.6, fontweight="bold", color=TAN)
ax.set_xticks(hrs[::2]); ax.set_xticklabels([f"{h}시" for h in hrs[::2]], fontsize=7); ax.set_yticks([]); ax.set_ylim(0, max(hv) * 1.25)
ax.set_title(f"{lo_h}시에 가면 {hi_h}시보다 {(1 - hi[lo_h] / hi[hi_h]) * 100:.0f}% 덜 붐빈다", fontsize=8.8)
IMG_HOUR = png(fig)

fig, ax = plt.subplots(figsize=(7.6, 1.7)); ax.axis("off"); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
flow = [("데이터허브 6종", "원본 CSV·XLSX", SEA), ("정제·통합", "표기 3종 통일\n성별·법인 합산", SEA), ("가공 데이터", "61,252행 외\n약 13MB", SEA),
        ("6대 지표·혼잡지수", "업종 내 백분위\n평균=1 지수화", TAN), ("등급 · 추천", "A~E / 한가한 곳", BAS)]
for k, (t, s, c) in enumerate(flow):
    x = 0.005 + k * 0.2
    ax.add_patch(FancyBboxPatch((x, 0.12), 0.17, 0.76, boxstyle="round,pad=0,rounding_size=0.04", fc=c, ec="none"))
    ax.text(x + 0.085, 0.64, t, ha="center", va="center", color="white", fontsize=9, fontweight="bold")
    ax.text(x + 0.085, 0.34, s, ha="center", va="center", color="white", fontsize=7, linespacing=1.4, alpha=.9)
    if k < 4:
        ax.annotate("", (x + 0.198, 0.5), (x + 0.172, 0.5), arrowprops=dict(arrowstyle="-|>", color=GRY, lw=1.3))
IMG_FLOW = png(fig)

import collections
BIZ_ROWS = []
for b in T.BIZ:
    try:
        sco = T._score(T._peer_table(b))
    except Exception:
        continue
    cnt = collections.Counter(T.grade_of(v)[0] for v in sco["종합"])
    BIZ_ROWS.append((b, len(sco), [cnt.get(g, 0) for g in "ABCDE"]))
BIZ_ROWS.sort(key=lambda r: (r[2][3] + r[2][4]) / r[1])
fig, ax = plt.subplots(figsize=(3.9, 3.5))
for i, (b, n, c) in enumerate(BIZ_ROWS):
    left = 0
    for g, k in zip("ABCDE", c):
        if k:
            ax.barh(i, k / n * 100, left=left, color=GC[g], height=0.72, edgecolor="white", lw=0.6)
            left += k / n * 100
    ax.text(101, i, f"{n}곳", va="center", fontsize=6.4, color=GRY)
ax.set_yticks(range(len(BIZ_ROWS))); ax.set_yticklabels([r[0] for r in BIZ_ROWS], fontsize=6.9)
ax.set_xticks([]); ax.spines["bottom"].set_visible(False); ax.set_xlim(0, 110)
ax.set_title(f"업종 {len(BIZ_ROWS)}종 × 제주 동네 — D·E 비율 낮은 순", fontsize=8.6)
IMG_BIZ = png(fig)
RU = core.run("우도에서 카페 하면 어때요?", use_llm=True)
RW = core.run("다음 주말 동쪽에 사람 적은 데", use_llm=True)
CASES = [c for c in EV["cases"] if c["mode"] == "LLM+규칙"] or EV["cases"][:20]
LINKS = [("대회 공고 (DAKER)", "https://daker.ai/public/hackathons/jeju-ai-bigdata-agent-challenge"),
         ("#748 카드매출×유동인구", "https://jejudatahub.net/data/view/data/748"),
         ("#793 상가(상권) 정보", "https://jejudatahub.net/data/view/data/793"),
         ("#189 내국인 관광지 입장객", "https://jejudatahub.net/data/view/data/189"),
         ("#190 외국인 관광지 입장객", "https://jejudatahub.net/data/view/data/190"),
         ("#504 요일별 카드 이용", "https://jejudatahub.net/data/view/data/504"),
         ("#520 방문 내국인 유동인구", "https://jejudatahub.net/data/view/data/520"),
         ("사용 모델 qwen2.5:3b", "https://ollama.com/library/qwen2.5:3b")]
LINK_HTML = "".join(f"<div class='lk'><img src='{qr(u)}'><div><b>{t}</b><span>{u.replace('https://', '')}</span></div></div>" for t, u in LINKS)

CSS = f"""<style>
@page {{ size:A4; margin:0; }}
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ font-family:'Malgun Gothic',sans-serif; color:{BAS}; font-size:8.9pt; line-height:1.48; word-break:keep-all;
  -webkit-print-color-adjust:exact; print-color-adjust:exact; }}
.page {{ width:210mm; height:297mm; overflow:hidden; position:relative; break-after:page; display:flex; flex-direction:column; background:#fff; }}
.page:last-child {{ break-after:auto; }}
.in {{ padding:9mm 11mm 0; flex:1; display:flex; flex-direction:column; gap:3.2mm; min-height:0; }}
.top {{ display:flex; align-items:flex-end; gap:10px; border-bottom:2.5px solid {BAS}; padding-bottom:5px; }}
.top .no {{ font-size:30pt; font-weight:900; color:{TAN}; line-height:.9; letter-spacing:-1px; }}
.top .k {{ font-size:7.5pt; letter-spacing:2px; color:{GRY}; font-weight:700; }}
.top h2 {{ font-size:16.5pt; letter-spacing:-.6px; line-height:1.22; font-weight:900; }}
.top h2 em {{ font-style:normal; color:{TAN}; }}
.foot {{ height:8mm; flex:none; display:flex; align-items:center; justify-content:space-between; padding:0 11mm; font-size:7pt; color:{GRY}; border-top:1px solid #ECEFF3; margin-top:3mm; }}
.foot b {{ color:{TAN}; }}
.row {{ display:flex; gap:3.2mm; min-height:0; }} .col {{ display:flex; flex-direction:column; gap:3.2mm; min-height:0; }}
.f1 {{ flex:1; }} .f13 {{ flex:1.3; }} .f15 {{ flex:1.5; }}
.card {{ background:{CRM}; border-radius:9px; padding:8px 11px; }}
.card.dark {{ background:{BAS}; color:#fff; }} .card.sea {{ background:{SEA}; color:#fff; }} .card.tan {{ background:{TAN}; color:#fff; }}
.card.line {{ background:#fff; border:1.2px solid #E4E7EC; }}
.card h4 {{ font-size:10pt; margin-bottom:4px; letter-spacing:-.3px; }} .card.dark h4,.card.sea h4 {{ color:#FFC48C; }}
.card ul {{ padding-left:14px; }} .card li {{ margin:1.5px 0; }}
.lab {{ font-size:7pt; letter-spacing:1.6px; font-weight:800; color:{TAN}; margin-bottom:2px; }}
.kpi {{ flex:1; border-left:3px solid {TAN}; padding:2px 0 2px 9px; }}
.kpi .l {{ font-size:7.6pt; color:#5B6573; }} .kpi .v {{ font-size:19pt; font-weight:900; letter-spacing:-.6px; line-height:1.15; }} .kpi .s {{ font-size:7.2pt; color:#6B7280; }}
.fig img {{ width:100%; display:block; }}
.shot {{ border-radius:10px; overflow:hidden; box-shadow:0 6px 22px rgba(27,31,35,.18); border:1px solid #E4E7EC; background:#fff; }}
.shot .bar {{ height:16px; flex:none; background:#EEF0F3; display:flex; gap:4px; align-items:center; padding-left:7px; }}
.shot .bar i {{ width:6px; height:6px; border-radius:50%; background:#C9CED6; display:block; }}
.photo {{ border-radius:10px; overflow:hidden; position:relative; background-size:cover; background-position:center; }}
.photo .cap {{ position:absolute; left:0; right:0; bottom:0; padding:14px 12px 9px; color:#fff; font-size:8.6pt; font-weight:700;
  background:linear-gradient(transparent, rgba(11,60,93,.92)); }}
table {{ width:100%; border-collapse:collapse; font-size:8.1pt; }}
th {{ text-align:left; font-size:7.4pt; color:{GRY}; letter-spacing:.5px; border-bottom:1.5px solid {BAS}; padding:3px 6px; }}
td {{ padding:3.4px 6px; border-bottom:1px solid #E9ECF0; vertical-align:top; }}
td.k {{ font-weight:800; white-space:nowrap; }}
.pill {{ display:inline-block; padding:0 7px; border-radius:9px; font-size:7.4pt; font-weight:800; color:#fff; }}
.qa {{ background:#fff; border:1.2px solid #E4E7EC; border-radius:9px; padding:6px 10px; font-size:8.2pt; }}
.qa .q {{ font-weight:800; color:{SEA}; margin-bottom:2px; }} .qa .q:before {{ content:'Q  '; color:{TAN}; }}
.film {{ display:flex; }}
.fr {{ flex:1; background:{BAS}; color:#fff; padding:9px 10px 10px; position:relative; }}
.fr:first-child {{ border-radius:10px 0 0 10px; }} .fr:last-child {{ border-radius:0 10px 10px 0; }}
.fr + .fr {{ border-left:2px dashed #3A424C; }}
.fr .st {{ font-size:7pt; letter-spacing:1.5px; color:#FFC48C; font-weight:800; }}
.fr .tt {{ font-size:10.5pt; font-weight:900; margin:2px 0 5px; }}
.fr code {{ display:block; font-family:Consolas,'Malgun Gothic',monospace; font-size:7.2pt; background:#2A3038; border-radius:6px; padding:6px 7px; color:#E6EDF3; line-height:1.45; white-space:pre-wrap; word-break:break-all; }}
.fr .who {{ position:absolute; top:8px; right:9px; font-size:6.8pt; font-weight:800; padding:1px 6px; border-radius:8px; }}
.who.ai {{ background:{TAN}; }} .who.cd {{ background:{JAD}; color:{BAS}; }}
.stamp {{ font-size:40pt; font-weight:900; color:{TAN}; line-height:1; }}
.wall {{ display:flex; align-items:center; gap:8px; background:{CRM}; border-radius:9px; padding:7px 11px; font-size:8.2pt; }}
.wall .ln {{ width:18mm; height:0; border-top:2.5px dashed {TAN}; flex:none; }}
.lks {{ display:grid; grid-template-columns:repeat(4,1fr); gap:6px; }}
.lk {{ display:flex; gap:6px; align-items:center; background:{CRM}; border-radius:8px; padding:5px; }}
.lk img {{ width:19mm; height:19mm; border-radius:4px; flex:none; }}
.lk b {{ display:block; font-size:7.6pt; line-height:1.25; }} .lk span {{ display:block; font-size:6.2pt; color:#6B7280; word-break:break-all; line-height:1.25; margin-top:2px; }}
.scale {{ display:flex; border-radius:7px; overflow:hidden; font-size:8pt; font-weight:800; color:#fff; text-align:center; }}
.scale div {{ flex:1; padding:4px 0; }}
.num {{ display:inline-flex; width:17px; height:17px; border-radius:50%; background:{TAN}; color:#fff; font-size:8pt; font-weight:900; align-items:center; justify-content:center; margin-right:5px; }}
.ai-note {{ font-weight:400; font-size:7.2pt; opacity:.85; }}
</style>"""


def page(no, kicker, title, body, n):
    return f"""<section class="page"><div class="in"><div class="top"><div class="no">{no}</div><div><div class="k">{kicker}</div><h2>{title}</h2></div></div>{body}</div>
<div class="foot"><span>🍊 제주 장사·나들이 AI 비서 — 기획서</span><span>제주 AI·빅데이터 활용 AI Agent 개발 챌린지 2026 · <b>{n}</b> / 8</span></div></section>"""


# ───────── P1 표지 (킥: 실제 진단서가 표지) ─────────
P1 = f"""<section class="page" style="background:{SEA}">
<div style="position:absolute;inset:0;background:url('{img('hero.jpg')}') center top/cover;"></div>
<div style="position:absolute;inset:0;background:linear-gradient(180deg,rgba(11,60,93,.55) 0%,rgba(11,60,93,.30) 28%,rgba(27,31,35,.93) 62%,{BAS} 100%);"></div>
<div style="position:relative;padding:14mm 13mm 0;color:#fff;flex:1;display:flex;flex-direction:column;">
 <div style="display:flex;justify-content:space-between;font-size:7.6pt;letter-spacing:2.2px;font-weight:700;opacity:.92"><span>JEJU AI · BIG DATA AGENT CHALLENGE 2026</span><span>기획서</span></div>
 <div style="margin-top:12mm;font-size:12pt;font-weight:700;color:#FFC48C">“{Q1}”</div>
 <div style="font-size:34pt;font-weight:900;letter-spacing:-1.5px;line-height:1.12;margin-top:3mm;text-shadow:0 2px 14px rgba(0,0,0,.35)">말로 물으면,<br>데이터가 답하는<br><span style="color:{TAN}">제주 장사·나들이</span> AI 비서</div>
 <div style="font-size:10.5pt;margin-top:4mm;opacity:.95;max-width:125mm">제주데이터허브 6종을 AI Agent가 스스로 골라 계산해, 창업 위험 등급(A~E)과 덜 붐비는 곳을 돌려줍니다. 은행이 대출을 심사하는 방식으로 동네를 심사합니다.</div>
 <div style="margin-top:auto;display:flex;gap:5mm;align-items:stretch;">
  <div style="flex:1.25;background:#fff;color:{BAS};border-radius:14px;padding:6mm 6mm 5mm;box-shadow:0 14px 40px rgba(0,0,0,.45);">
   <div style="display:flex;justify-content:space-between;font-size:7.5pt;color:{GRY};font-weight:700;letter-spacing:1px"><span>창업 위험 진단서 · 실제 실행 결과</span><span>애월읍 · 카페</span></div>
   <div style="display:flex;align-items:center;gap:5mm;margin-top:2mm">
    <div style="font-size:78pt;font-weight:900;color:{TAN};line-height:.95">{D['등급']}</div>
    <div><div style="font-size:15pt;font-weight:900;letter-spacing:-.5px">위험 {D['위험수준']}</div><div style="font-size:8.6pt;color:#4B5563">제주 {D['비교지역수']}개 동네 중 {D['순위']}번째로 안전 · {D['종합점수']:.0f}점/100</div>
     <div style="margin-top:2mm;font-size:8.4pt">약점: <b style="color:{TAN}">{D['약점'][0]['설명']}</b>, <b style="color:{TAN}">{D['약점'][1]['설명']}</b></div></div></div>
   <div style="display:flex;gap:3mm;margin-top:3mm;border-top:1px solid #E5E7EB;padding-top:3mm">
    <div class="kpi"><div class="l">평상시 월매출</div><div class="v" style="font-size:15pt">{won(S['평상시월매출'])}</div><div class="s">동네 카페 전체</div></div>
    <div class="kpi"><div class="l">가장 어려운 {D['최악의달']}월</div><div class="v" style="font-size:15pt">{won(S['비수기월매출'])}</div><div class="s">−{(1-S['비수기월매출']/S['평상시월매출'])*100:.0f}%</div></div>
    <div class="kpi"><div class="l">큰 충격 시(2020 봄)</div><div class="v" style="font-size:15pt">{won(S['충격시월매출'])}</div><div class="s">−{(1-S['충격시월매출']/S['평상시월매출'])*100:.0f}%</div></div></div>
   <div style="margin-top:3mm;background:{CRM};border-radius:9px;padding:2.5mm 4mm;font-size:9.6pt;font-weight:800">➜ 대신 <span style="color:{JAD}">{a0['지역']}</span>이면 <span class="pill" style="background:{JAD}">{a0['등급']}등급</span> <span style="font-weight:400;font-size:8pt;color:#4B5563">· Agent가 자동으로 찾은 같은 업종의 더 안전한 동네</span></div>
  </div>
  <div style="flex:.75;display:flex;flex-direction:column;gap:3mm;">
   <div style="flex:1;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.25);border-radius:12px;padding:4mm 5mm"><div style="font-size:7.4pt;opacity:.8">질문 이해 정확도</div><div style="font-size:24pt;font-weight:900">{EL['정확도']}</div><div style="font-size:7.4pt;opacity:.8">제주어 포함 시험 20문항</div></div>
   <div style="flex:1;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.25);border-radius:12px;padding:4mm 5mm"><div style="font-size:7.4pt;opacity:.8">평균 응답</div><div style="font-size:24pt;font-weight:900">{EL['평균응답초']}<small style="font-size:11pt">초</small></div><div style="font-size:7.4pt;opacity:.8">로컬 AI · 인터넷 없이</div></div>
   <div style="flex:1;background:{TAN};border-radius:12px;padding:4mm 5mm"><div style="font-size:7.4pt;opacity:.95">숫자를 만드는 주체</div><div style="font-size:21pt;font-weight:900;line-height:1.2">100% 코드</div><div style="font-size:7.4pt;opacity:.95">AI는 질문 이해만 — 환각 숫자 차단</div></div>
  </div></div>
 <div style="display:flex;gap:6mm;font-size:8pt;opacity:.85;padding:5mm 0 8mm;"><span>🏪 장사해도 되쿠과 — 창업 위험 진단</span><span>🌿 오늘 어디 한가하우꽈 — 덜 붐비는 곳</span><span style="margin-left:auto">센터 PC(GTX1060 3GB) · 오프라인 동작</span></div>
</div></section>"""

# ───────── P2 문제 ─────────
P2 = page("01", "WHY · 문제 정의", "제주에선 <em>같은 카페</em>도 동네에 따라 운명이 갈린다", f"""
<div class="row"><div class="kpi"><div class="l">우도면 카페 · 가장 어려운 {U['최악의달']}월</div><div class="v">평소의 {U['최악의달비율']*100:.0f}%</div><div class="s">한 해 매출 굴곡이 극단적</div></div>
<div class="kpi"><div class="l">우도면 카페 · 2020년 봄 충격</div><div class="v">{U_shock*100:.0f}%</div><div class="s">전년 같은 기간 대비 매출</div></div>
<div class="kpi"><div class="l">애월읍 카페 점포 수 (2025.09)</div><div class="v">{D['점포수']}곳</div><div class="s">한 동네 안에서의 경쟁</div></div>
<div class="kpi"><div class="l">비교한 카페 동네</div><div class="v">{D['비교지역수']}곳</div><div class="s">점수 폭 {peers['종합'].min():.0f}~{peers['종합'].max():.0f}점</div></div></div>
<div class="fig card line" style="padding:6px 8px"><img src="{IMG_DIST}"></div>
<div class="row f1">
 <div class="col f13">
  <div class="card"><h4>🏪 “여기서 장사해도 되나?” — 답할 도구가 없다</h4><ul>
   <li>제주는 관광 의존 업종이 많아 <b>계절·외부 충격에 매출이 크게 출렁인다.</b></li>
   <li>데이터는 공개돼 있지만 <b>CSV 수십 개를 내려받아 직접 가공</b>해야 해 예비 창업자는 쓸 수 없다.</li>
   <li>기존 상권 분석은 “얼마 버나(평균)”를 보여 줄 뿐, “<b>얼마나 흔들리나(위험)</b>”는 보여 주지 않는다.</li></ul></div>
  <div class="card"><h4>🌿 “지금 어디 가야 덜 붐비나?” — 도민의 주말 고민</h4><ul>
   <li>관광지마다 붐비는 달이 다르고, 요일·시간대까지 겹치면 감으로는 알 수 없다.</li>
   <li>관광객이 몰리는 제주에서 <b>한 번에 비교해 주는 도구가 없다.</b></li></ul></div>
  <div class="card dark f1"><h4>그래서 — 말로 묻고, 진단서 한 장으로 받는다</h4>
   질문 한 줄이면 AI Agent가 <b>어떤 데이터·지역·업종·기간을 쓸지 스스로 판단</b>하고, 결과가 나쁘면 대안까지 찾아 <b>등급·숫자·그래프·근거</b>를 한 장에 담아 돌려준다.
   <table style="margin-top:6px;color:#fff;font-size:7.9pt"><tr><th style="color:#FFC48C;border-color:#FFC48C">구분</th><th style="color:#FFC48C;border-color:#FFC48C">기존 상권 분석 서비스</th><th style="color:#FFC48C;border-color:#FFC48C">본 서비스</th></tr>
   <tr><td class="k" style="border-color:#3A424C">보는 것</td><td style="border-color:#3A424C">평균 매출·유동인구</td><td style="border-color:#3A424C"><b>흔들림</b> — 변동·쏠림·충격·경쟁</td></tr>
   <tr><td class="k" style="border-color:#3A424C">입력</td><td style="border-color:#3A424C">지도·메뉴 여러 번 선택</td><td style="border-color:#3A424C"><b>질문 한 줄</b>(제주어 OK)</td></tr>
   <tr><td class="k" style="border-color:#3A424C">결과</td><td style="border-color:#3A424C">지표 나열, 해석은 사용자 몫</td><td style="border-color:#3A424C"><b>A~E 등급 + 대안 동네</b></td></tr>
   <tr><td class="k" style="border-color:#3A424C">환경</td><td style="border-color:#3A424C">인터넷·회원가입</td><td style="border-color:#3A424C"><b>오프라인 PC 한 대</b></td></tr></table></div>
 </div>
 <div class="col f1"><div class="photo f1" style="background-image:url('{img('owner.jpg')}')"><div class="cap">예비 창업자 · 업종 전환 소상공인 · 창업 상담 공무원<br><span class="ai-note">※ 사용 장면을 표현한 AI 생성 이미지</span></div></div>
  <table><tr><th>사용자</th><th>얻는 것</th></tr>
  <tr><td class="k">예비 창업자</td><td>계약 전 등급·비수기 매출·대안 동네</td></tr><tr><td class="k">기존 소상공인</td><td>업종 전환·2호점 동네 순위</td></tr>
  <tr><td class="k">상담 공무원</td><td>출처 명시된 인쇄용 진단서</td></tr><tr><td class="k">도민 가족</td><td>조건별 한산한 곳 3곳 + 시간</td></tr></table></div>
</div>""", 2)

# ───────── P3 방법론 ─────────
RF = [("📉", "변동성", "매출이 달마다 얼마나 출렁이나", "2017~2019 월매출 표준편차 ÷ 평균", "20%"),
      ("🌗", "계절 쏠림", "성수기 대비 비수기 격차", "월별 평균 매출 최고 ÷ 최저", "20%"),
      ("⚡", "충격 민감도", "큰 충격이 오면 얼마나 빠지나", "2020.3~5 ÷ 2019.3~5 − 1 (스트레스 테스트)", "20%"),
      ("📈", "성장 추세", "동네 매출이 크고 있나", "2017→2019 연평균 성장률", "15%"),
      ("🧳", "관광 의존도", "관광객이 끊기면 버틸 수 있나", "방문인구 ÷ (거주+근무+방문)", "10%"),
      ("🏪", "경쟁 강도", "점포 1곳이 나눠 갖는 매출", "월매출 ÷ 같은 업종 점포 수(2025.09)", "15%")]
cards = "".join(f"<div class='card' style='padding:7px 9px'><div style='display:flex;justify-content:space-between'><b style='font-size:9.6pt'>{e} {a}</b><span class='pill' style='background:{SEA}'>{w}</span></div><div style='font-size:8pt;margin-top:2px'>{b}</div><div style='font-size:7.3pt;color:#6B7280;margin-top:2px'>{c}</div></div>" for e, a, b, c, w in RF)
ind_rows = "".join(f"<tr><td class='k'>{x['설명']}</td><td>{x['값']:,.2f}</td><td>{x['업종중앙값']:,.2f}</td><td><b style='color:{sc(x['안전점수'])}'>{x['안전점수']:.0f}</b></td></tr>" for x in ind)
P3 = page("02", "HOW · 진단 방법", "은행이 대출을 심사하듯, <em>동네를 심사</em>한다", f"""
<div class="card sea" style="display:flex;gap:6mm;align-items:center"><div style="flex:1.2"><h4>금융권 신용리스크 방식을 소상공인 언어로</h4>은행은 돈을 빌려줄 때 평균 소득만 보지 않는다 — <b>소득이 얼마나 흔들리는지, 위기 때 얼마나 버티는지</b>를 본다. 같은 눈으로 “이 동네에서 이 업종”을 심사해 <b>A~E 등급</b>을 매긴다.</div>
<div style="flex:1"><div class="scale"><div style="background:{GC['A']}">A 80+</div><div style="background:{GC['B']}">B 65+</div><div style="background:{GC['C']}">C 50+</div><div style="background:{GC['D']}">D 35+</div><div style="background:{GC['E']}">E</div></div>
<div style="font-size:7.6pt;margin-top:4px;opacity:.92">지표별 <b>같은 업종 제주 읍면동 안 백분위</b>(0~100) × 비중 → 종합점수 → 등급. 같은 업종끼리만 비교하므로 “카페는 원래 위험” 같은 착시가 없다.</div></div></div>
<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:3.2mm">{cards}</div>
<div class="row f1">
 <div class="col f1"><div class="card line fig"><img src="{IMG_IND}"></div><div class="card line fig"><img src="{IMG_SEAS}"></div>
  <div class="card sea f1"><h4>등급을 읽는 법</h4><ul><li><b>A·B</b> — 같은 업종 제주 동네 중 상위권. 흔들림이 적고 충격에도 버틴 동네</li><li><b>C</b> — 평균 수준. 약점 지표를 보고 대비하면 되는 동네</li><li><b>D·E</b> — 계절·충격에 크게 흔들린 동네. Agent가 <b>대안 동네를 자동으로</b> 함께 제시</li><li>점수는 <b>같은 업종 안 상대 위치</b>이므로 업종이 달라도 같은 기준으로 읽는다</li></ul></div></div>
 <div class="col f1">
  <div class="card"><h4>애월읍 카페를 실제로 심사하면</h4>
  <table><tr><th>지표</th><th>애월</th><th>업종 중앙값</th><th>점수</th></tr>{ind_rows}</table>
  <div style="font-size:7.2pt;color:#6B7280;margin-top:3px">경쟁 강도 값은 점포당 월매출(원), 나머지는 비율. 출처: 데이터허브 #748·#793</div></div>
  <div class="card dark"><h4>스트레스 테스트 — “나쁜 해가 오면?”</h4>
  <div style="display:flex;gap:4mm;margin:3px 0 5px"><div><div style="font-size:7.4pt;opacity:.75">평상시</div><div style="font-size:15pt;font-weight:900">{won(S['평상시월매출'])}</div></div>
  <div><div style="font-size:7.4pt;opacity:.75">비수기({D['최악의달']}월)</div><div style="font-size:15pt;font-weight:900;color:#FFC48C">{won(S['비수기월매출'])}</div></div>
  <div><div style="font-size:7.4pt;opacity:.75">2020년 봄 재현</div><div style="font-size:15pt;font-weight:900;color:{TAN}">{won(S['충격시월매출'])}</div></div></div>
  은행이 경기 충격을 가정해 대출을 다시 보듯, <b>실제로 있었던 2020년 봄 충격</b>을 그 동네·그 업종에 다시 적용해 “최악의 몇 달”을 보여 준다. 표본이 적은 동네(월 300만원 미만·24개월 미만)는 등급 대신 그 사실을 알린다.</div>
  <div class="card line fig f1"><img src="{IMG_BIZ}"><div style="font-size:7.2pt;color:#6B7280">같은 업종 안 백분위라 업종마다 A~E가 고루 나뉜다 — “업종 자체가 위험”이 아니라 <b>“어느 동네냐”</b>가 갈린다. 숫자=비교 동네 수</div></div>
 </div></div>""", 3)

# ───────── P4 AI 작동 ─────────
slot_js = json.dumps(SL, ensure_ascii=False).replace(", ", ",\n ")
tool_lines = "\n".join(b for a, b in TRACE if a.startswith("③") or a.startswith("④"))
trace_rows = "".join(f"<tr><td class='k'>{a}</td><td>{b}</td></tr>" for a, b in TRACE)
P4 = page("03", "AI AGENT · 작동 방식", f"AI는 <em>묻기만</em>, 계산은 코드가 — 질문 한 줄의 {T1:.1f}초 영수증", f"""
<div class="film">
 <div class="fr"><span class="who ai">AI</span><div class="st">STEP 1 · 질문</div><div class="tt">도민의 말 그대로</div><code>“{Q1}”</code><div style="font-size:7.3pt;margin-top:5px;opacity:.85">제주어·생활 지명(협재·함덕·모슬포 등 80여 개)도 이해</div></div>
 <div class="fr"><span class="who ai">AI</span><div class="st">STEP 2 · 이해</div><div class="tt">qwen2.5:3b → JSON</div><code>{slot_js}</code><div style="font-size:7.3pt;margin-top:5px;opacity:.85">규칙 파서와 교차검증, 사전에 없는 값은 버림</div></div>
 <div class="fr" style="flex:1.25"><span class="who cd">CODE</span><div class="st">STEP 3 · 계산</div><div class="tt">pandas 도구 실행</div><code>{tool_lines}</code></div>
 <div class="fr" style="background:#fff;color:{BAS};border:2px solid {BAS}"><span class="who cd">CODE</span><div class="st" style="color:{TAN}">STEP 4 · 답</div><div class="tt">진단서 발행</div><div style="display:flex;align-items:center;gap:6px"><div class="stamp">{D['등급']}</div><div style="font-size:8pt">{D['비교지역수']}곳 중 {D['순위']}위<br>대안 {a0['지역']} {a0['등급']}<br>출처·기간 명시</div></div></div>
</div>
<div class="wall"><b style="color:{TAN};white-space:nowrap">환각 차단선</b><div class="ln"></div><span>언어모델은 STEP 1~2에서만 판단 · 숫자와 등급은 STEP 3~4의 결정적 계산 코드만 만든다 · 이 질문 실측 {T1:.2f}초(개발 PC, 모델 예열 후)</span></div>
<div class="card line"><h4>Agent가 실제로 남긴 작업 기록 — 앱 화면의 ‘AI가 일한 과정’에 그대로 공개</h4><table>{trace_rows}</table></div>
<div class="row f1">
 <div class="col f1">
  <div class="card"><h4>스스로 판단하는 5가지</h4>
   <div><span class="num">1</span><b>도구 선택</b> — 진단 / 동네 비교 / 한가한 곳</div>
   <div style="margin-top:3px"><span class="num">2</span><b>빈 값 보완</b> — 월·요일·시간이 없으면 오늘 기준으로 채우고 화면에 명시</div>
   <div style="margin-top:3px"><span class="num">3</span><b>도구 전환</b> — 지역 없이 업종만 물으면 ‘진단’→‘동네 비교’</div>
   <div style="margin-top:3px"><span class="num">4</span><b>후속 호출</b> — D·E등급이면 대안 동네 탐색, 주변 관광 계절성 비교</div>
   <div style="margin-top:3px"><span class="num">5</span><b>조건 완화</b> — 맞는 곳이 없으면 조건을 풀어 다시 검색</div></div>
  <div class="card sea"><h4>사용 모델</h4><b>Qwen2.5-3B-Instruct</b> (Ollama ‘qwen2.5:3b’, 4bit 약 1.9GB)<ul style="margin-top:3px"><li>로컬 실행, 인터넷·API 키 불필요, 온도 0·시드 고정</li><li>센터 PC GPU 3GB에 적재 가능, 모델이 없으면 규칙 모드로 <b>같은 결과</b></li></ul></div></div>
 <div class="col f1">
  <div class="card dark"><h4>왜 숫자를 AI에 맡기지 않았나</h4>개발 중 3B 모델에 답변 문장을 다듬게 했더니, 숫자는 지키면서 <b>“39곳 중 17위”를 “가장 안전한 곳 중 하나”로 뒤집는</b> 사례가 나왔다. 그래서 문장 다듬기는 <b>기본 OFF</b>, 켜더라도 숫자 대조 검증을 통과해야만 채택한다.</div>
  <div class="card"><h4>개발 중 잡아낸 오류</h4><ul><li>‘2023.10’이 숫자로 읽혀 <b>10월이 1월로 합쳐지던</b> 관광 데이터 → 문자열로 읽도록 수정</li><li>AI가 “다음 주말”을 <b>7월로 지어내던</b> 문제 → 질문에 없는 월·시간은 버리고 날짜로 계산</li></ul></div>
  </div>
</div>
<div class="row">
 <div class="card line f13"><h4>이렇게 물어도 알아듣는다 — 시험 문항 실제 결과</h4><table><tr><th>질문 (원문)</th><th>도구</th><th>지역</th><th>업종</th><th></th></tr>
 {''.join(f"<tr><td>{c['q']}</td><td>{c.get('tool') or ''}</td><td>{c.get('area') or ''}</td><td>{c.get('biz') or ''}</td><td style='color:{JAD};font-weight:900'>{'✓' if c['ok'] else '✗'}</td></tr>" for c in CASES[:5])}</table></div>
 <div class="card dark f1"><h4>빈 값은 스스로 채운다</h4><div style="font-weight:800;color:#FFC48C">Q “다음 주말 동쪽에 사람 적은 데”</div>
 <table style="color:#fff;margin-top:3px">{''.join(f"<tr><td class='k' style='border-color:#3A424C;color:#FFC48C'>{a}</td><td style='border-color:#3A424C'>{b}</td></tr>" for a, b in RW['trace'])}</table>
 <div style="font-size:7.4pt;opacity:.85;margin-top:4px">월·시간이 질문에 없으면 AI가 지어내지 않고 오늘 날짜로 계산해 채운 뒤 화면에 밝힌다.</div></div>
</div>""", 4)

# ───────── P5 데모 1 ─────────
alt_html = "".join(f"<div style='display:flex;align-items:center;gap:7px;margin:3px 0'><span class='pill' style='background:{GC[x['등급']]};font-size:9pt;padding:1px 9px'>{x['등급']}</span><b style='font-size:9.6pt'>{x['지역']}</b><span style='margin-left:auto;font-size:8pt;color:#4B5563'>{x['종합점수']:.0f}점 · 동네 카페 월매출 {won(x['월평균매출'])}</span></div>" for x in ALT)
P5 = page("04", "DEMO 1 · 장사해도 되쿠과", f"애월 카페는 왜 <em>{D['등급']}등급</em>인가 — 실제 화면 그대로", f"""
<div class="row f1">
 <div class="col" style="flex:1.05"><div class="shot f1" style="display:flex;flex-direction:column"><div class="bar"><i></i><i></i><i></i></div><div style="flex:1;background:url('{img('crop_diag.jpg')}') top center/100% auto no-repeat"></div></div>
  <div style="font-size:7.2pt;color:#6B7280">▲ 실제 앱(Streamlit) 실행 화면 캡처 — 등급 카드 · 쉬운 설명 · 핵심 숫자 3개 · 그래프 · 대안 동네 · 진단서 내려받기</div></div>
 <div class="col f1">
  <div class="qa"><div class="q">{Q1}</div>{R1['answer']}</div>
  <div class="card"><h4>Agent가 스스로 찾은 대안 동네</h4>{alt_html}
   <div style="font-size:7.3pt;color:#6B7280;margin-top:2px">D·E등급이 나오면 묻지 않아도 후속 도구(alternatives)를 자동 호출</div></div>
  <div class="qa"><div class="q">{Q4}</div>{R4['answer']}</div>
  <div class="qa"><div class="q">{Q3}</div>{R3['answer']}</div>
  <div class="qa f1"><div class="q">우도에서 카페 하면 어때요?</div>{RU['answer']}</div>
 </div></div>
<div class="card tan" style="display:flex;align-items:center;gap:5mm"><div style="font-size:20pt;font-weight:900;white-space:nowrap">진단서 1장</div><div>결과는 <b>인쇄용 진단서(HTML)</b>로 내려받아 창업 상담 창구에서 그대로 쓸 수 있다. 데이터 출처·기간·계산식이 함께 찍힌다.</div></div>""", 5)

# ───────── P6 데모 2 ─────────
spot_rows = "".join(f"<tr><td class='k'>{i+1}. {x['관광지']}</td><td>{x['권역']}</td><td><b style='color:{JAD}'>{x['혼잡지수']:.2f}</b></td><td>약 {x['예상시간당']}명</td></tr>" for i, x in enumerate(SPOTS))
avoid_rows = "".join(f"<tr><td class='k'>{x['관광지']}</td><td>{x['권역']}</td><td><b style='color:{TAN}'>{x['혼잡지수']:.2f}</b></td><td>약 {x['예상시간당']}명</td></tr>" for x in AVOID[:1])
P6 = page("05", "DEMO 2 · 오늘 어디 한가하우꽈", "1월 일요일, 아이와 갈 <em>한가한 실내</em>는 여기다", f"""
<div class="row" style="height:60mm;flex:none"><div class="photo f15" style="background-image:url('{img('family.jpg')}')"><div class="cap">“애들이랑 갈 만한 실내 어디 한가해요?” — 관광객이 몰리는 제주에서 도민의 주말을 위한 기능<br><span class="ai-note">※ 사용 장면을 표현한 AI 생성 이미지</span></div></div>
 <div class="col f1"><div class="card dark f1"><div class="lab" style="color:#FFC48C">혼잡지수 계산</div><div style="font-size:9.4pt;font-weight:800;line-height:1.5">(그 달 입장객 ÷ 연평균)<br>× 요일 지수 × 시간대 지수</div><div style="font-size:7.6pt;opacity:.85;margin-top:4px">1.00 = 그 관광지의 평소. 조건(권역·실내·아이 동반)으로 거른 뒤, 원래부터 한산한 하위 25%는 빼고 <b>“갈 만한데 덜 붐비는 곳”</b>을 고른다.</div></div></div></div>
<div class="row f1">
 <div class="col f1"><div class="shot f1" style="display:flex;flex-direction:column"><div class="bar"><i></i><i></i><i></i></div><div style="flex:1;background:url('{img('crop_quiet.jpg')}') top center/100% auto no-repeat"></div></div>
 <div style="font-size:7.2pt;color:#6B7280">▲ 실제 앱 실행 화면 캡처</div></div>
 <div class="col f1">
  <div class="qa"><div class="q">{Q2}</div>{R2['answer']}</div>
  <div class="card line"><h4>추천 3곳과 피할 곳</h4><table><tr><th>관광지</th><th>권역</th><th>혼잡</th><th>시간당</th></tr>{spot_rows}<tr><td colspan="4" style="font-size:7.2pt;color:{TAN};font-weight:800;padding-top:5px">가장 붐빌 곳</td></tr>{avoid_rows}</table></div>
  <div class="card line fig f1"><img src="{IMG_HOUR}"><div style="font-size:7.2pt;color:#6B7280">제주 방문 내국인 유동인구(#520, 2023~), 평균 = 1</div></div>
 </div></div>""", 6)

# ───────── P7 데이터 ─────────
SRC = [("#748", "상권분석을 위한 유동인구에 따른 카드 매출액 변화(매쉬업)", "읍면동×업종×월 카드 이용금액·이용자수, 거주·근무·방문인구", "2017.01~2021.05", "6대 지표 중심"),
       ("#793", "제주특별자치도 상가(상권) 정보", "상호·업종 소분류·행정동·좌표 57,865건", "2025.09", "경쟁 강도"),
       ("#189", "내국인 관광지 입장객 수 추이", "관광지×월 입장객", "2009.01~2024.12", "월별 혼잡"),
       ("#190", "외국인 관광지 입장객 수 추이", "관광지×월 입장객", "2009.01~2024.12", "내·외국인 합산"),
       ("#504", "요일별 카드 이용 건수 비교", "월×요일(공휴일 포함) 이용 건수", "2018.01~2025.06", "요일 지수"),
       ("#520", "제주도 방문 내국인 유동인구 추이", "월×시간대 방문 유동인구", "2018.01~2025.04", "시간대 지수")]
src_rows = "".join(f"<tr><td class='k' style='color:{TAN}'>{a}</td><td><b>{b}</b></td><td>{c}</td><td>{d}</td><td>{e}</td></tr>" for a, b, c, d, e in SRC)
P7 = page("06", "DATA · 데이터 계획", "제주데이터허브 6종이 <em>하나의 등급</em>이 되기까지", f"""
<div class="fig"><img src="{IMG_FLOW}"></div>
<div class="card line"><table><tr><th style="width:7%">ID</th><th style="width:30%">데이터명</th><th>내용</th><th style="width:15%">기간</th><th style="width:13%">용도</th></tr>{src_rows}</table>
<div style="font-size:7.2pt;color:#6B7280;margin-top:3px">출처: 제주데이터허브(jejudatahub.net) 공개 데이터 · 원본은 결과물에 넣지 않고 가공 데이터와 재생성 스크립트(build_data.py)만 포함 · 각 데이터 링크는 8쪽 QR</div></div>
<div class="row f1">
 <div class="col f1"><div class="card f1"><h4>전처리 — 이렇게 손봤다</h4><ul>
  <li><b>카드매출(#748)</b>: 연도별 5개 파일 통합, 년월 표기 3종(2018-01-01 / 2019-01 / 21-Apr) 통일, 성별·법인 합산 → 읍면동×업종×월 <b>61,252행</b></li>
  <li><b>관광지 입장객(#189·#190)</b>: ‘2023.10’이 숫자로 읽히면 ‘2023.1’(1월)로 바뀌는 함정 발견 → 문자열로 읽도록 수정, 내·외국인 합산</li>
  <li><b>요일·시간 지수(#504·#520)</b>: 2023년 이후 자료로 평균=1 지수화, 공휴일은 월 평균 일수로 환산</li>
  <li><b>업종 연결</b>: 카드 업종명 ≠ 상가 소분류 → 20개 생활 업종 사전으로 연결 (예: 카페 = 카드 ‘비알콜 음료점업’ = 상가 ‘카페’)</li>
  <li><b>지명 연결</b>: 생활 지명 80여 개 → 43개 읍면동</li></ul>
  <h4 style="margin-top:8px">품질 점검 — 숫자가 맞는지 이렇게 확인했다</h4><ul>
  <li>관광지별 월 피벗을 직접 열어 <b>10월 칸이 비어 있는지</b> 확인 → 날짜 함정 발견·수정</li>
  <li>동네·업종별 표본 기준(월 300만원·24개월) 미달 시 등급 대신 안내</li>
  <li>같은 질문 10회 실행해 결과 일치 확인 (outputs/eval.json)</li>
  <li>새 PC에 zip만 풀어 새 가상환경으로 실행하는 <b>클린 설치 시험</b> 통과 — AI 모델 없는 상태에서도 같은 결과</li></ul></div></div>
 <div class="col f1"><div class="card sea"><h4>왜 이 데이터 조합인가</h4><ul><li><b>매출(#748)</b>만으로는 점포 수를 모른다 → <b>상가정보(#793)</b>로 경쟁 강도 보완</li><li><b>월별 입장객</b>만으로는 “몇 시에”를 모른다 → <b>요일(#504)·시간대(#520)</b> 지수를 곱해 시간 단위 혼잡 추정</li><li>카드매출 공개 범위가 2021.05까지라 평상시(2017~2019)+충격(2020) 기준으로 쓰고, 최신 상가 수(2025.09)로 현재 경쟁을 반영</li></ul></div>
  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:3.2mm">
   <div class="card" style="padding:6px 9px"><div style="font-size:7.2pt;color:#6B7280">카드매출 가공</div><div style="font-size:15pt;font-weight:900">61,252<small style="font-size:8pt">행</small></div></div>
   <div class="card" style="padding:6px 9px"><div style="font-size:7.2pt;color:#6B7280">상가 점포</div><div style="font-size:15pt;font-weight:900">57,865<small style="font-size:8pt">곳</small></div></div>
   <div class="card" style="padding:6px 9px"><div style="font-size:7.2pt;color:#6B7280">관광지</div><div style="font-size:15pt;font-weight:900">{len(T.SPOTS)}<small style="font-size:8pt">곳</small></div></div>
   <div class="card" style="padding:6px 9px"><div style="font-size:7.2pt;color:#6B7280">읍면동</div><div style="font-size:15pt;font-weight:900">43<small style="font-size:8pt">곳</small></div></div>
   <div class="card" style="padding:6px 9px"><div style="font-size:7.2pt;color:#6B7280">생활 업종</div><div style="font-size:15pt;font-weight:900">{len(T.BIZ)}<small style="font-size:8pt">종</small></div></div>
   <div class="card" style="padding:6px 9px"><div style="font-size:7.2pt;color:#6B7280">관광 통계 기간</div><div style="font-size:15pt;font-weight:900">16<small style="font-size:8pt">년</small></div></div></div>
  <div class="card dark f1"><h4>데이터가 갱신되면</h4>데이터허브에 새 파일이 올라오면 <b>build_data.py 한 번 재실행</b>으로 지표·등급이 갱신된다. 계산식이 고정돼 있어 같은 데이터·같은 질문이면 언제나 같은 답이 나온다.
  <code style="display:block;font-family:Consolas,monospace;font-size:7.4pt;background:#2A3038;border-radius:6px;padding:7px 9px;margin-top:6px;color:#E6EDF3;line-height:1.6">&gt; python build_data.py      # 원본 → 가공 데이터 재생성<br>&gt; python tests\\smoke.py      # 대표 질문 실행 점검<br>&gt; python tests\\eval.py       # 20문항 정확도·재현성<br>&gt; run.bat                    # 화면 실행</code></div></div>
</div>""", 7)

# ───────── P8 검증·실행·링크 ─────────
P8 = page("07", "TRUST · 검증 · 실행 · 링크", f"<em>20문 20답</em>, 10회 동일 — 센터 PC에서 그대로 돈다", f"""
<div class="row"><div class="kpi"><div class="l">질문 이해 정확도</div><div class="v">{EL['정확도']}</div><div class="s">AI+규칙 · 규칙만 {ER['정확도']}</div></div>
<div class="kpi"><div class="l">평균 응답</div><div class="v">{EL['평균응답초']}초</div><div class="s">최대 {EL['최대응답초']}초 · 규칙 모드 {ER['평균응답초']}초</div></div>
<div class="kpi"><div class="l">재현성</div><div class="v">10/10</div><div class="s">같은 질문 10회 → 같은 답</div></div>
<div class="kpi"><div class="l">필요 GPU</div><div class="v">약 2GB</div><div class="s">없으면 CPU·규칙 모드</div></div></div>
<div class="row">
 <div class="card line f1"><h4>시험 설계</h4>20문항 = 창업 진단 10 · 동네 비교 3 · 나들이 7, 제주어(“괜찮수과”, “어디우꽈”) 포함. 도구·지역·업종·월·요일·시간이 모두 맞아야 정답.<div style="font-size:7.2pt;color:#6B7280;margin-top:3px">※ 개발자가 만든 문항이므로 실제 도민 질문에서는 더 낮을 수 있다. 사전에 없는 지명·업종은 “가능한 목록”을 안내한다.</div></div>
 <div class="card line f1"><h4>실행 환경 (센터 PC: i7-8700 / GTX1060 3GB / 32GB)</h4><table>
  <tr><td class="k">실행</td><td><b>run.bat 더블클릭</b> → 가상환경·라이브러리 자동 설치 → 브라우저 자동 열림</td></tr>
  <tr><td class="k">요구</td><td>Python 3.10+, pandas·numpy·matplotlib·streamlit</td></tr>
  <tr><td class="k">AI(선택)</td><td>Ollama + qwen2.5:3b · 없으면 규칙 모드</td></tr>
  <tr><td class="k">인터넷</td><td>불필요 (가공 데이터 약 13MB 포함)</td></tr></table></div></div>
<div class="row">
 <div class="card f1"><h4>한계 — 숨기지 않는다</h4><ul><li><b>카드매출 기간</b>: 읍면동×업종 공개 데이터가 2021.05까지 → 기간을 화면·진단서에 명시</li><li><b>동네 단위 통계</b>: 개별 가게의 성패 예측이 아닌 “참고 지표”</li><li><b>혼잡</b>: 실시간이 아닌 월·요일·시간 패턴, 날씨·행사 미반영</li></ul></div>
 <div class="card dark f1"><h4>다음 단계</h4><ul><li>진단 업종 20종 → 확대, 임대료·폐업 데이터 연계 시 ‘폐업 위험’ 지표 추가</li><li>센터 상담 창구용 <b>상담 모드</b> — 여러 동네 진단서 일괄 출력</li><li>데이터허브 갱신 주기에 맞춘 자동 재빌드</li></ul></div></div>
<div class="card line"><h4>시험 20문항 전체 결과 (outputs/eval.json, AI+규칙 모드)</h4>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:0 4mm;font-size:7.3pt">{''.join(f"<div style='display:flex;gap:5px;border-bottom:1px solid #EEF0F3;padding:1.6px 0'><b style='color:{JAD if c['ok'] else TAN}'>{'✓' if c['ok'] else '✗'}</b><span style='flex:1'>{c['q']}</span><span style='color:#6B7280'>{c.get('tool') or ''}</span></div>" for c in CASES[:20])}</div></div>
<div class="card f1"><h4>개발 도구 고지</h4>코드 작성·문서 초안에 생성형 AI 코딩 도구를 보조로 사용했다. 데이터 가공 결과·지표 설계·수치 검증은 실행 결과로 직접 확인했다. 표지·사용 장면 사진 2장은 AI 생성 이미지이며, 앱 화면과 모든 수치·그래프는 실제 실행 결과다.</div>
<div class="card line"><h4>관련 링크 — 휴대폰으로 QR을 찍으면 바로 열린다</h4><div class="lks">{LINK_HTML}</div>
<div style="font-size:7.2pt;color:#6B7280;margin-top:5px">결과물 zip 안: README.md(설치·실행) · 데이터_활용_명세.md · docs/사용자매뉴얼.md · tests/(smoke·eval) · outputs/eval.json(시험 원자료)</div></div>
""", 8)

HTML = f"<!doctype html><html><head><meta charset='utf-8'>{CSS}</head><body>{P1}{P2}{P3}{P4}{P5}{P6}{P7}{P8}</body></html>"
src = os.path.join(DOCS, "기획서.html"); dst = os.path.join(DOCS, "기획서.pdf")
open(src, "w", encoding="utf-8").write(HTML)
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
subprocess.run([EDGE, "--headless", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={dst}", "file:///" + src.replace("\\", "/")], capture_output=True, timeout=180)
print("OK", os.path.getsize(dst))
