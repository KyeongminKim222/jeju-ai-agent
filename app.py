"""제주 장사·나들이 AI 에이전트 — 화면(Streamlit)
실행: run.bat 더블클릭  (또는 python -m streamlit run app.py)
"""
import base64
import datetime as dt
import io
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agent import core, tools as T  # noqa: E402

for f in ("Malgun Gothic", "AppleGothic", "NanumGothic"):
    try:
        matplotlib.font_manager.findfont(f, fallback_to_default=False)
        plt.rcParams["font.family"] = f
        break
    except Exception:
        pass
plt.rcParams["axes.unicode_minus"] = False

st.set_page_config(page_title="제주 장사·나들이 AI 비서", page_icon="🍊", layout="centered")
st.markdown("""<style>
html, body, [class*="css"] {font-size: 19px;}
.big {font-size: 2.2rem; font-weight: 800; margin: 0;}
.grade {font-size: 4rem; font-weight: 900; line-height: 1;}
.card {border-radius: 14px; padding: 18px 20px; background: #fff8ef; border: 1px solid #f3d9b1; margin: 8px 0;}
.small {color: #666; font-size: 0.85rem;}
div.stButton > button {font-size: 1.1rem; padding: 0.6rem 1rem; width: 100%;}
</style>""", unsafe_allow_html=True)

GRADE_COLOR = {"A": "#1b9e4b", "B": "#7cb342", "C": "#f9a825", "D": "#ef6c00", "E": "#d32f2f"}

st.markdown('<p class="big">🍊 제주 장사·나들이 AI 비서</p>', unsafe_allow_html=True)
st.caption("제주데이터허브 공개 데이터로 계산합니다 · 인터넷 없이 이 PC 안에서 동작")

llm_on = core.llm_available()
with st.sidebar:
    st.subheader("설정")
    use_llm = st.toggle("AI 질문 이해 사용(Ollama)", value=llm_on, disabled=not llm_on,
                        help="꺼져 있어도 규칙 기반으로 똑같이 동작합니다.")
    st.write("AI 모델:", f"`{core.MODEL}`" if llm_on else "없음 → 규칙 모드")
    show_trace = st.toggle("AI가 일한 과정 보기", value=True)

tab1, tab2 = st.tabs(["🏪 장사해도 되쿠과 (창업 위험 진단)", "🌿 오늘 어디 한가하우꽈 (덜 붐비는 곳)"])

EX1 = ["애월에 카페 하나 차리면 괜찮수과?", "연동에서 한식당 하면 장사 될까요", "치킨집 하기 좋은 동네 어디우꽈?"]
EX2 = ["8월 토요일 오후 2시에 덜 붐비는 데 어디?", "1월 일요일 비 오는데 애들이랑 갈 만한 실내 어디 한가해요?", "다음 주말 동쪽에 사람 적은 관광지 추천해줘"]


def fig_to_b64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()


def chart_season(r, extra):
    fig, ax = plt.subplots(figsize=(7, 3))
    months = list(range(1, 13))
    seas = r["seasonal"]
    vals = [seas.get(f"{m:02d}", seas.get(m, 0)) for m in months]
    colors = ["#d32f2f" if m == r["최악의달"] else ("#1b9e4b" if m == r["최고의달"] else "#f4a340") for m in months]
    ax.bar(months, vals, color=colors, label=f"{r['지역']} {r['업종']} 월별 매출(평균=1)")
    if extra.get("season"):
        sv = extra["season"]["월별"]
        ax.plot(months, [sv.get(m, sv.get(str(m), None)) for m in months], "k--o", ms=3, lw=1.2,
                label=f"{extra['season']['권역']} 관광지 방문객(평균=1)")
    ax.axhline(1, color="#999", lw=0.6)
    ax.set_xticks(months)
    ax.set_xticklabels([f"{m}월" for m in months], fontsize=8)
    ax.set_ylim(0, max([v for v in vals if v] + [1.2]) * 1.35)
    ax.legend(fontsize=8, loc="upper left", ncol=2, frameon=False)
    ax.set_title("언제 장사가 잘 되고, 언제 어려운가 (2017~2019 평상시)", fontsize=10)
    return fig


def chart_factors(r):
    fig, ax = plt.subplots(figsize=(7, 2.8))
    names = [x["설명"] for x in r["지표"]][::-1]
    vals = [x["안전점수"] for x in r["지표"]][::-1]
    ax.barh(names, vals, color=["#1b9e4b" if v >= 60 else ("#f9a825" if v >= 40 else "#d32f2f") for v in vals])
    ax.axvline(50, color="#999", lw=0.8, ls="--")
    ax.set_xlim(0, 100)
    ax.set_xlabel("안전점수 (50 = 제주 같은 업종 동네들의 중간)", fontsize=8)
    ax.tick_params(labelsize=8)
    return fig


def certificate_html(q, r, answer, imgs):
    rows = "".join(
        f"<tr><td>{x['설명']}</td><td style='text-align:right'>{x['안전점수']:.0f}</td></tr>" for x in r["지표"])
    alt = ""
    if r["대안"]:
        alt = "<h3>위험이 더 낮은 동네(같은 업종)</h3><ul>" + "".join(
            f"<li>{a['지역']} — {a['등급']}등급 (점수 {a['종합점수']:.0f})</li>" for a in r["대안"]) + "</ul>"
    src = "".join(f"<li>{s}</li>" for s in r["출처"])
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>창업 위험 진단서</title>
<style>body{{font-family:'Malgun Gothic',sans-serif;max-width:760px;margin:30px auto;color:#222}}
h1{{border-bottom:3px solid #f4a340}} .g{{font-size:64px;font-weight:900;color:{GRADE_COLOR[r['등급']]}}}
table{{border-collapse:collapse;width:100%}} td{{border-bottom:1px solid #eee;padding:6px}} .s{{color:#777;font-size:12px}}</style></head>
<body><h1>🍊 창업 위험 진단서</h1>
<p class="s">발급일 {dt.date.today()} · 질문: “{q}”</p>
<p><b>{r['지역']} · {r['업종']}</b> <span class="g">{r['등급']}</span> 등급 ({r['위험수준']}) · 제주 {r['비교지역수']}개 동네 중 {r['순위']}위</p>
<p>{answer}</p>
<img src="data:image/png;base64,{imgs[0]}" width="100%">
<h3>6가지 위험 지표 (100 = 가장 안전)</h3><table>{rows}</table>
<img src="data:image/png;base64,{imgs[1]}" width="100%">
{alt}
<h3>사용한 데이터</h3><ul class="s">{src}</ul>
<p class="s">※ 동네 전체 카드매출 통계로 계산한 참고 지표이며, 개별 점포의 성공·실패를 단정하지 않습니다.
같은 질문에는 언제나 같은 결과가 나옵니다(계산식 고정).</p></body></html>"""


def show_trace_box(res):
    if show_trace:
        with st.expander("🤖 AI가 일한 과정", expanded=False):
            for a, b in res["trace"]:
                st.markdown(f"**{a}** — {b}")


def ask(q, key):
    with st.spinner("데이터를 찾아 계산하는 중..."):
        return core.run(q, use_llm=use_llm)


# ── 탭 1: 창업 위험 진단 ───────────────────────────────────────────
with tab1:
    st.write("동네와 업종을 말로 물어보세요. 같은 업종을 하는 제주 다른 동네들과 비교해 **위험 등급(A~E)** 을 매깁니다.")
    c = st.columns(3)
    for i, e in enumerate(EX1):
        if c[i].button(e, key=f"e1{i}"):
            st.session_state["q1"] = e
    q1 = st.text_input("질문", key="q1", placeholder="예) 애월에 카페 하나 차리면 괜찮수과?")
    if st.button("진단하기 🔍", type="primary", key="go1") and q1:
        st.session_state["r1"] = (q1, ask(q1, "1"))
    if "r1" in st.session_state:
        q, res = st.session_state["r1"]
        r = res["result"]
        if res["tool"] == "quiet":
            st.info("나들이 질문 같아서 '덜 붐비는 곳'으로 답했습니다.")
        if res["tool"] == "diagnose" and r and "error" not in r:
            col = GRADE_COLOR[r["등급"]]
            st.markdown(f"""<div class="card"><span class="small">{r['지역']} · {r['업종']}</span><br>
<span class="grade" style="color:{col}">{r['등급']}</span> <b style="font-size:1.4rem">위험 {r['위험수준']}</b>
&nbsp; <span class="small">제주 {r['비교지역수']}개 동네 중 {r['순위']}번째로 안전</span></div>""", unsafe_allow_html=True)
            st.write(res["answer"])
            s = r["스트레스"]
            m = st.columns(3)
            m[0].metric("평상시 한 달 (동네 전체)", core.won(s["평상시월매출"]))
            m[1].metric(f"가장 어려운 {r['최악의달']}월", core.won(s["비수기월매출"]),
                        f"{(r['최악의달비율'] - 1) * 100:.0f}%")
            if s["충격시월매출"] == s["충격시월매출"]:
                m[2].metric("큰 충격 때 (2020년 봄)", core.won(s["충격시월매출"]),
                            f"{(s['충격시월매출'] / s['평상시월매출'] - 1) * 100:.0f}%")
            f1, f2 = chart_season(r, res["extra"]), chart_factors(r)
            b1, b2 = fig_to_b64(f1), fig_to_b64(f2)
            st.image(base64.b64decode(b1))
            st.markdown("**6가지 위험 지표** (막대가 길수록 안전)")
            st.image(base64.b64decode(b2))
            if r["대안"]:
                st.markdown("**같은 업종, 위험이 더 낮은 동네**")
                st.table(pd.DataFrame(r["대안"]).assign(월평균매출=lambda d: d["월평균매출"].map(core.won), 종합점수=lambda d: d["종합점수"].map(lambda v: f"{v:.0f}"))
                         .rename(columns={"월평균매출": "동네 전체 월 카드매출"}))
            st.download_button("📄 진단서 내려받기 (인쇄용)", certificate_html(q, r, res["answer"], (b1, b2)),
                               file_name=f"창업진단서_{r['지역']}_{r['업종']}.html", mime="text/html")
        elif res["tool"] == "compare" and r:
            st.write(res["answer"])
            st.table(pd.DataFrame(r["추천"]).assign(월평균매출=lambda d: d["월평균매출"].map(core.won), 종합점수=lambda d: d["종합점수"].map(lambda v: f"{v:.0f}"))
                     .rename(columns={"월평균매출": "동네 전체 월 카드매출"}))
        else:
            st.write(res["answer"])
        with st.expander("사용한 데이터"):
            for s_ in (r or {}).get("출처", []):
                st.markdown("- " + s_)
        show_trace_box(res)

# ── 탭 2: 덜 붐비는 곳 ─────────────────────────────────────────────
with tab2:
    st.write("언제·어디로 갈지 말로 물어보세요. 관광지 방문 통계로 **덜 붐비는 곳과 시간**을 알려 드립니다.")
    c = st.columns(3)
    for i, e in enumerate(EX2):
        if c[i].button(e, key=f"e2{i}"):
            st.session_state["q2"] = e
    q2 = st.text_input("질문", key="q2", placeholder="예) 8월 토요일 오후 2시에 덜 붐비는 데 어디?")
    if st.button("찾아보기 🔍", type="primary", key="go2") and q2:
        st.session_state["r2"] = (q2, ask(q2, "2"))
    if "r2" in st.session_state:
        q, res = st.session_state["r2"]
        r = res["result"]
        st.write(res["answer"])
        if res["tool"] == "quiet" and r and "error" not in r:
            for i, x in enumerate(r["추천"]):
                st.markdown(f"""<div class="card"><b style="font-size:1.3rem">{i + 1}. {x['관광지']}</b>
<span class="small"> {x['권역']} · {'실내' if x['실내'] else '야외'}{' · 아이 동반 OK' if x['아이동반'] else ''}</span><br>
혼잡지수 <b>{x['혼잡지수']:.2f}</b> (1.00 = 이 관광지의 평소) · 시간당 약 {x['예상시간당']:,}명</div>""",
                            unsafe_allow_html=True)
            hi = T.hour_idx()
            fig, ax = plt.subplots(figsize=(7, 2.4))
            hrs = list(range(8, 21))
            ax.bar(hrs, [hi[h] for h in hrs], color=["#1b9e4b" if h == r["추천시간"] else ("#d32f2f" if h == r["피크시간"] else "#9ec5e8") for h in hrs])
            ax.set_xticks(hrs)
            ax.set_xticklabels([f"{h}시" for h in hrs], fontsize=8)
            ax.set_title("시간대별 붐빔 (제주 방문객 유동인구, 평균=1)", fontsize=10)
            st.pyplot(fig)
        elif res["tool"] in ("diagnose", "compare"):
            st.info("창업 질문 같아서 '창업 위험 진단' 방식으로 답했습니다. 첫 번째 탭에서 자세히 보실 수 있습니다.")
        with st.expander("사용한 데이터"):
            for s_ in (r or {}).get("출처", []):
                st.markdown("- " + s_)
        show_trace_box(res)

st.markdown("---")
st.markdown('<p class="small">데이터: 제주데이터허브(jejudatahub.net) 공개 데이터 · 계산식 고정으로 같은 질문엔 같은 답 · '
            'AI(소형 언어모델)는 질문 이해에만 쓰고 숫자는 모두 계산 코드가 만듭니다.</p>', unsafe_allow_html=True)
