"""제주 장사·나들이 AI 에이전트의 두뇌.
흐름: ① 질문 이해(LLM→JSON, 실패 시 규칙) → ② 슬롯 검증·보완 → ③ 도구 선택·실행(결정적 계산)
     → ④ 후속 도구 자동 호출(등급 나쁘면 대안 지역, 관광 계절성) → ⑤ 숫자 검증된 설명문 생성
LLM: Ollama 로컬 소형 모델(기본 qwen2.5:3b, VRAM 약 2GB) — 인터넷·외부 API 불필요.
LLM이 없거나 느려도 규칙 기반으로 동일하게 동작한다(센터 PC 안전장치).
"""
import datetime as _dt
import json
import os
import re
import urllib.request

from . import tools as T

MODEL = os.environ.get("JEJU_AGENT_MODEL", "qwen2.5:3b")
OLLAMA = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
TIMEOUT = float(os.environ.get("JEJU_AGENT_LLM_TIMEOUT", "60"))
# 답변 문장 다듬기(LLM)는 기본 OFF.
# 시험 결과 qwen2.5:3b가 숫자는 지켜도 뜻을 뒤집는 사례(17위/39 → "가장 안전한 곳 중 하나", 없는 동네 이름 생성)가 나와
# 신뢰성을 위해 사실 템플릿을 최종 답으로 쓰고, LLM은 '질문 이해'에만 쓴다. 필요 시 JEJU_AGENT_POLISH=1.
POLISH = os.environ.get("JEJU_AGENT_POLISH", "0") == "1"


def _ollama(prompt, as_json=False, max_tokens=400):
    body = {"model": MODEL, "prompt": prompt, "stream": False,
            "options": {"temperature": 0, "seed": 7, "num_predict": max_tokens}}
    if as_json:
        body["format"] = "json"
    req = urllib.request.Request(OLLAMA + "/api/generate", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read())["response"]


def llm_available():
    try:
        with urllib.request.urlopen(OLLAMA + "/api/tags", timeout=3) as r:
            names = [m["name"] for m in json.loads(r.read()).get("models", [])]
        return any(n.split(":")[0] == MODEL.split(":")[0] for n in names)
    except Exception:
        return False


PARSE_PROMPT = """너는 제주 도민 질문을 분석하는 도우미다. 아래 질문을 읽고 JSON 하나만 출력해라.
도구:
- "diagnose": 가게 창업·장사 위험, 매출, 장사 잘 되나, 망하나 같은 질문. 필요한 값: area(동네), biz(업종)
- "quiet": 덜 붐비는 곳, 한가한 관광지, 사람 적은 곳, 나들이 추천. 필요한 값: month(1~12), dow(요일), hour(0~23), region, indoor(비·실내면 true), kids(아이 동반이면 true)
- "compare": 어느 동네가 그 업종 하기 좋은지(지역 추천). 필요한 값: biz
JSON 형식: {{"tool": "...", "area": "...", "biz": "...", "month": null, "dow": null, "hour": null, "region": null, "indoor": false, "kids": false}}
질문: {q}
JSON:"""


def _rule_parse(q):
    s = {"tool": None, "area": None, "biz": None, "month": None, "dow": None, "hour": None,
         "region": None, "indoor": False, "kids": False}
    quiet_words = ["한가", "덜 붐", "안 붐", "사람 적", "사람없", "사람 없", "안 막", "조용", "나들이", "갈 만", "갈만", "놀러", "붐비", "줄 안"]
    cmp_words = ["좋은 동네", "나은 동네", "어디가 좋", "어느 동네", "어디서 하", "어디에 차", "어디 차리", "어디가 나", "추천 동네", "동네 추천"]
    s["biz"] = T.resolve_biz(q)
    s["area"] = T.resolve_area(q)
    if any(w in q for w in quiet_words) and not (s["biz"] and any(w in q for w in ["창업", "가게", "장사", "차리", "열면"])):
        s["tool"] = "quiet"
    elif s["biz"] and (any(w in q for w in cmp_words) or (not s["area"] and any(w in q for w in ["어디", "어느"]))):
        s["tool"] = "compare"
    elif s["biz"] or any(w in q for w in ["창업", "장사", "가게", "매출"]):
        s["tool"] = "diagnose"
    else:
        s["tool"] = "quiet" if any(w in q for w in ["관광", "구경", "가볼", "여행", "아이", "애들"]) else None
    m = re.search(r"(1[0-2]|[1-9])\s*월", q)
    s["month"] = int(m.group(1)) if m else None
    for i, d in enumerate(["월", "화", "수", "목", "금", "토", "일"]):
        if re.search(d + r"요일", q):
            s["dow"] = T.DOW_NAMES[i]
    if "주말" in q and not s["dow"]:
        s["dow"] = "토요일"
    if "공휴일" in q or "연휴" in q:
        s["dow"] = "공휴일"
    h = re.search(r"(오전|오후|아침|저녁|낮)?\s*(\d{1,2})\s*시", q)
    if h:
        hh = int(h.group(2))
        if h.group(1) in ("오후", "저녁") and hh < 12:
            hh += 12
        s["hour"] = hh
    elif "오전" in q or "아침" in q:
        s["hour"] = 10
    elif "오후" in q:
        s["hour"] = 15
    s["region"] = T.resolve_region(q) if s["tool"] == "quiet" else None
    s["indoor"] = any(w in q for w in ["비 ", "비와", "비 와", "비오", "비 오", "실내", "바람", "추워", "더워", "태풍"])
    s["kids"] = any(w in q for w in ["아이", "애들", "아기", "아들", "딸", "유아", "어린이", "가족"])
    return s


def understand(q, use_llm=True):
    """질문 → 슬롯. LLM 결과는 반드시 규칙/사전으로 검증한다(환각 차단)."""
    rule = _rule_parse(q)
    src = "규칙"
    slots = dict(rule)
    if use_llm:
        try:
            raw = json.loads(_ollama(PARSE_PROMPT.format(q=q), as_json=True, max_tokens=150))
            src = f"LLM({MODEL})+규칙 검증"
            if raw.get("tool") in ("diagnose", "quiet", "compare") and rule["tool"] is None:
                slots["tool"] = raw["tool"]
            elif raw.get("tool") in ("diagnose", "quiet", "compare") and raw["tool"] != rule["tool"]:
                # 의견 불일치: 규칙에 강한 단서가 있으면 규칙 우선, 아니면 LLM
                slots["tool"] = rule["tool"] or raw["tool"]
            for k in ("area", "biz"):
                if not slots[k] and raw.get(k):
                    v = T.resolve_area(raw[k]) if k == "area" else T.resolve_biz(raw[k])
                    slots[k] = v  # 사전에 없는 값은 None 처리(환각 차단)
            # 숫자(월·시)는 질문에 숫자가 실제로 있을 때만 LLM 값을 받는다(예: '다음 주말'→7월 같은 환각 차단)
            if slots["month"] is None and isinstance(raw.get("month"), (int, float)) and re.search(r"\d\s*월", q):
                slots["month"] = int(raw["month"])
            if slots["hour"] is None and isinstance(raw.get("hour"), (int, float)) and re.search(r"\d\s*시", q):
                slots["hour"] = int(raw["hour"])
            if not slots["dow"] and raw.get("dow"):
                d = str(raw["dow"])
                slots["dow"] = next((x for x in T.DOW_NAMES if x.startswith(d[:1])), None)
            if slots["tool"] == "quiet" and not slots["region"] and raw.get("region"):
                slots["region"] = T.resolve_region(raw["region"])
            slots["indoor"] = bool(slots["indoor"] or raw.get("indoor") is True)
            slots["kids"] = bool(slots["kids"] or raw.get("kids") is True)
        except Exception as e:  # LLM 미설치·타임아웃 → 규칙만
            src = f"규칙(LLM 사용 불가: {type(e).__name__})"
    return slots, src


def run(q, use_llm=True, today=None):
    """에이전트 1회 실행. 반환: {trace, slots, tool, result, extra, answer}"""
    today = today or _dt.date.today()
    trace = []
    slots, src = understand(q, use_llm)
    trace.append(("① 질문 이해", f"{src} → 도구={slots['tool']}, 지역={slots['area']}, 업종={slots['biz']}"))

    tool = slots["tool"]
    if tool is None:
        return {"trace": trace, "slots": slots, "tool": None, "result": None, "extra": {},
                "answer": "무엇을 도와드릴지 잘 모르겠수다. 예) \"애월에 카페 차리면 괜찮수과?\" 또는 \"8월 토요일 오후에 덜 붐비는 데 어디?\"처럼 물어봐 줍서."}

    # ② 빠진 값 보완(기본값은 '오늘' 기준, 사용자에게 명시)
    filled = []
    if tool == "quiet":
        if not slots["month"]:
            slots["month"] = today.month; filled.append(f"월={today.month}월(이번 달)")
        if not slots["dow"]:
            d = T.DOW_NAMES[today.weekday()]; slots["dow"] = "토요일" if today.weekday() < 5 else d
            filled.append(f"요일={slots['dow']}")
        if slots["hour"] is None:
            slots["hour"] = 14; filled.append("시간=14시")
    if tool == "diagnose" and not slots["area"]:
        tool = "compare"; filled.append("지역이 없어 '어느 동네가 좋은지' 비교로 전환")
    if tool in ("diagnose", "compare") and not slots["biz"]:
        return {"trace": trace, "slots": slots, "tool": tool, "result": None, "extra": {},
                "answer": "어떤 업종인지 알려줍서. 가능한 업종: " + ", ".join(T.BIZ)}
    trace.append(("② 값 확인·보완", ", ".join(filled) if filled else "모든 값이 질문에 있음"))

    # ③ 도구 실행
    extra = {}
    if tool == "diagnose":
        res = T.diagnose(slots["area"], slots["biz"])
        trace.append(("③ 도구 실행", f"diagnose({slots['area']}, {slots['biz']}) — 같은 업종 {res.get('비교지역수', '-')}개 읍면동과 6개 지표 비교"))
        if "error" not in res:
            extra["season"] = T.area_tour_season(slots["area"])
            if res["대안"]:
                trace.append(("④ 후속 도구 자동 호출", f"등급 {res['등급']} → alternatives({slots['biz']}) 로 더 안전한 동네 3곳 탐색"))
            trace.append(("④ 후속 도구 자동 호출", f"area_tour_season({res['권역']}) — 주변 관광지 계절 흐름 확인"))
    elif tool == "compare":
        res = {"업종": slots["biz"], "추천": T.alternatives(slots["biz"], top=5), "출처": [T.SOURCES["card"], T.SOURCES["stores"]]}
        trace.append(("③ 도구 실행", f"alternatives({slots['biz']}) — 43개 읍면동 리스크 순위"))
    else:
        res = T.quiet_spots(slots["month"], slots["dow"], slots["hour"], slots["region"], slots["indoor"], slots["kids"])
        trace.append(("③ 도구 실행", f"quiet_spots({slots['month']}월, {slots['dow']}, {slots['hour']}시, 권역={slots['region'] or '전체'}, 실내={slots['indoor']}, 아이={slots['kids']})"))
        if "error" in res and (slots["region"] or slots["indoor"] or slots["kids"]):
            res = T.quiet_spots(slots["month"], slots["dow"], slots["hour"], None, slots["indoor"], slots["kids"])
            trace.append(("④ 자동 재시도", "조건에 맞는 곳이 없어 권역 조건을 풀고 다시 검색"))

    # ⑤ 설명문(템플릿=사실 고정) + LLM 말투 다듬기(숫자 검증 통과 시에만 채택)
    facts = summarize(tool, res, slots)
    answer, how = facts, "템플릿"
    if use_llm and POLISH and "error" not in res:
        try:
            cand = _ollama(POLISH_PROMPT.format(facts=facts), max_tokens=350).strip()
            ok, bad = numbers_consistent(facts, cand)
            if ok and len(cand) > 40:
                answer, how = cand, f"LLM 다듬기(숫자 검증 통과)"
            else:
                how = f"템플릿(LLM 문장에 근거 없는 숫자 {bad[:3]} → 폐기)"
        except Exception as e:
            how = f"템플릿(LLM 사용 불가: {type(e).__name__})"
    trace.append(("⑤ 답변 생성·검증", how))
    return {"trace": trace, "slots": slots, "tool": tool, "result": res, "extra": extra, "answer": answer}


POLISH_PROMPT = """아래 '사실'을 제주 도민 어르신도 이해하기 쉽게 4~6문장으로 다시 써라.
규칙: 사실에 없는 숫자·지명·업종을 절대 새로 만들지 마라. 숫자는 그대로 옮겨라. 단정하지 말고 판단은 사용자에게 맡겨라. 한국어 존댓말.
사실:
{facts}
쉬운 설명:"""


def _nums(text):
    return set(re.findall(r"\d+(?:[.,]\d+)?", text.replace(",", "")))


def numbers_consistent(facts, text):
    allowed = _nums(facts)
    bad = [n for n in _nums(text) if n not in allowed and not (n.isdigit() and int(n) <= 10)]
    return (len(bad) == 0), bad


def josa(word, pair):
    """받침에 맞는 조사: josa('카페','을/를') → '카페를'"""
    w = str(word)
    last = w.rstrip(")）")[-1] if w else "가"
    a, b = pair.split("/")
    if "가" <= last <= "힣":
        has = (ord(last) - 0xAC00) % 28 != 0
        if pair == "으로/로":
            return w + ("로" if (not has or (ord(last) - 0xAC00) % 28 == 8) else "으로")
        return w + (a if has else b)
    return w + b


def won(x):
    if x != x:
        return "-"
    x = float(x)
    if x >= 1e8:
        return f"{x / 1e8:.1f}억원"
    return f"{x / 1e4:,.0f}만원"


WEAK_TXT = {"변동계수": "매출이 달마다 크게 출렁임", "계절쏠림": "성수기·비수기 차이가 큼",
            "코로나충격": "외부 충격 때 매출이 크게 빠짐", "성장률": "최근 성장세가 약함",
            "방문인구비중": "관광·방문객 의존이 큼", "점포당월매출": "가게가 많아 경쟁이 셈"}
STRONG_TXT = {"변동계수": "매출이 달마다 고른 편", "계절쏠림": "계절을 덜 탐",
              "코로나충격": "외부 충격에 잘 버팀", "성장률": "성장세가 좋음",
              "방문인구비중": "주민 수요가 탄탄함", "점포당월매출": "가게 1곳당 매출이 넉넉함"}


def summarize(tool, r, slots):
    if r is None:
        return ""
    if "error" in r:
        s = r["error"]
        if r.get("대안"):
            s += " 같은 업종으로 비교적 안전한 동네: " + ", ".join(f"{a['지역']}({a['등급']}등급)" for a in r["대안"])
        return s
    if tool == "diagnose":
        st = r["스트레스"]
        weak = ", ".join(WEAK_TXT[w["지표"]] for w in r["약점"] if w["안전점수"] < 50) or "뚜렷한 약점 없음"
        strong = ", ".join(STRONG_TXT[w["지표"]] for w in r["강점"] if w["안전점수"] >= 50) or "뚜렷한 강점 없음"
        s = (f"{r['지역']} {r['업종']} 창업 위험도는 {r['등급']}등급({r['위험수준']})입니다. "
             f"같은 업종을 하는 제주 {r['비교지역수']}개 동네 중 {r['순위']}번째로 안전합니다(점수 {r['종합점수']:.0f}점/100). "
             f"이 동네 {r['업종']} 전체 카드매출은 평상시 한 달 {won(st['평상시월매출'])}인데, "
             f"가장 어려운 {r['최악의달']}월에는 {josa(won(st['비수기월매출']), '으로/로')} 줄어듭니다. ")
        if st["충격시월매출"] == st["충격시월매출"]:
            s += f"2020년 봄 같은 큰 충격이 오면 {won(st['충격시월매출'])} 수준까지 떨어졌습니다. "
        s += f"약점은 {weak}이고, 강점은 {strong}입니다. 현재 이 동네 {r['업종']} 점포는 {r['점포수']}곳입니다."
        if r["대안"]:
            s += " 같은 업종으로 위험이 더 낮은 동네: " + ", ".join(f"{a['지역']}({a['등급']}등급)" for a in r["대안"]) + "."
        return s
    if tool == "compare":
        return (f"{josa(r['업종'], '을/를')} 하기에 위험이 낮은 동네 순서: "
                + ", ".join(f"{i + 1}위 {a['지역']}({a['등급']}등급, 동네 전체 월 카드매출 {won(a['월평균매출'])})" for i, a in enumerate(r["추천"])) + ".")
    # quiet
    rec = r["추천"]
    s = (f"{r['월']}월 {r['요일']} {r['시']}시 기준({r['권역']}"
         + (", 실내" if r["실내만"] else "") + (", 아이 동반" if r["아이동반"] else "") + ") 덜 붐빌 곳: ")
    s += ", ".join(f"{x['관광지']}(평소의 {x['혼잡지수']:.2f}배, 시간당 약 {x['예상시간당']:,}명)" for x in rec) + ". "
    if r["피할곳"] and r["후보수"] > len(rec):
        p = r["피할곳"][0]
        s += f"가장 붐빌 곳은 {p['관광지']}(평소의 {p['혼잡지수']:.2f}배)입니다. "
    s += f"같은 곳이라도 {r['추천시간']}시에 가면 {r['피크시간']}시보다 약 {r['시간절감률'] * 100:.0f}% 덜 붐빕니다."
    return s
