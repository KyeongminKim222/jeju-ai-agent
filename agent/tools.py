"""결정적(Deterministic) 분석 도구 모음.
LLM은 이 도구들을 '고르고 인자만 채운다'. 숫자는 전부 여기서 pandas로 계산한다.
→ 같은 질문이면 언제나 같은 숫자(재현성), 3B 소형 모델로도 오답 숫자가 나오지 않는다.
"""
import os
from functools import lru_cache

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "data", "processed")

# ── 데이터 출처(데이터 활용 명세와 동일) ─────────────────────────────
SOURCES = {
    "card": "제주데이터허브 #748 「상권분석을 위한 유동인구에 따른 카드 매출액 변화」(읍면동×업종×월, 2017.01~2021.05)",
    "pop": "제주데이터허브 #748 동일 파일의 거주·근무·방문 인구",
    "stores": "제주데이터허브 #793 「제주특별자치도 상가(상권) 정보」(2025.09 기준)",
    "tour": "제주데이터허브 #189·#190 「내국인·외국인 관광지 입장객 수 추이」(관광지×월, 2009.01~2024.12)",
    "dow": "제주데이터허브 #504 「요일별 카드 이용 건수 비교」(2023.01~2025.06)",
    "hour": "제주데이터허브 #520 「제주도 방문 내국인 유동인구 추이」 시간대별(2023.01~2025.04)",
}

# ── 업종 사전: 사용자 말 → (카드 업종명, 상가 소분류 키워드) ─────────────
BIZ = {
    "카페": ("비알콜 음료점업", ["카페"], ["카페", "커피", "디저트", "찻집"]),
    "한식당": ("한식 음식점업", ["백반/한정식", "돼지고기 구이/찜", "국수/칼국수", "국/탕/찌개류", "소고기 구이/찜", "해장국/감자탕", "곱창 전골/구이", "닭/오리고기 구이/찜"],
             ["한식", "식당", "밥집", "백반", "고기집", "흑돼지", "국수", "고깃집", "음식점"]),
    "일식·횟집": ("일식 음식점업", ["일식 회/초밥", "횟집", "일식 면 요리", "일식 카레/돈가스/덮밥"], ["일식", "횟집", "회", "초밥", "스시", "돈가스"]),
    "중식당": ("중식 음식점업", ["중국집", "마라탕/훠궈"], ["중식", "중국집", "짜장", "마라"]),
    "양식당": ("서양식 음식점업", ["경양식", "파스타/스테이크", "패밀리레스토랑"], ["양식", "파스타", "스테이크", "레스토랑", "브런치"]),
    "치킨·피자·버거": ("피자, 햄버거, 샌드위치 및 유사 음식점업", ["치킨", "피자", "버거", "토스트/샌드위치/샐러드"], ["치킨", "피자", "버거", "햄버거", "샌드위치"]),
    "술집": ("기타 주점업", ["요리 주점", "생맥주 전문", "호프/맥주"], ["술집", "주점", "호프", "이자카야", "포차", "펍", "바"]),
    "편의점": ("체인화 편의점", ["편의점"], ["편의점"]),
    "빵집": ("빵 및 과자류 소매업", ["빵/도넛", "떡/한과"], ["빵", "베이커리", "제과"]),
    "숙박(모텔·여관)": ("여관업", ["여관/모텔", "펜션", "게스트하우스"], ["숙박", "모텔", "여관", "펜션", "게하", "게스트하우스", "민박"]),
    "호텔": ("호텔업", ["호텔/리조트"], ["호텔", "리조트"]),
    "기념품점": ("관광 민예품 및 선물용품 소매업", ["기념품점"], ["기념품", "선물", "소품"]),
    "화장품": ("화장품 및 방향제 소매업", ["화장품 소매업"], ["화장품"]),
    "렌터카": ("자동차 임대업", ["렌터카"], ["렌터카", "렌트", "차량 대여"]),
    "과일·채소": ("과실 및 채소 소매업", ["채소/과일 소매업"], ["과일", "청과", "채소", "귤"]),
    "수산물": ("수산물 소매업", ["수산물 소매업"], ["수산", "생선", "건어물"]),
    "정육점": ("육류 소매업", ["정육점"], ["정육", "고기 판매"]),
    "슈퍼마켓": ("슈퍼마켓", ["슈퍼마켓"], ["슈퍼", "마트"]),
    "마사지": ("마사지업", ["마사지/안마"], ["마사지", "안마"]),
    "여행사": ("여행사업", ["여행사"], ["여행사"]),
}

# ── 지역 사전: 생활 지명 → 읍면동(카드 데이터 43개 단위) ──────────────
AREA_ALIAS = {
    "협재": "한림읍", "한림": "한림읍", "금능": "한림읍", "옹포": "한림읍",
    "애월": "애월읍", "한담": "애월읍", "곽지": "애월읍", "하귀": "애월읍", "고내": "애월읍",
    "함덕": "조천읍", "조천": "조천읍", "선흘": "조천읍", "와흘": "조천읍",
    "월정": "구좌읍", "세화": "구좌읍", "김녕": "구좌읍", "종달": "구좌읍", "평대": "구좌읍", "구좌": "구좌읍",
    "성산": "성산읍", "섭지코지": "성산읍", "신양": "성산읍", "온평": "성산읍", "오조": "성산읍",
    "표선": "표선면", "가시리": "표선면", "남원": "남원읍", "위미": "남원읍", "신례": "남원읍",
    "중문": "중문동", "대포": "중문동", "색달": "중문동",
    "안덕": "안덕면", "사계": "안덕면", "화순": "안덕면", "산방산": "안덕면", "동광": "안덕면",
    "모슬포": "대정읍", "대정": "대정읍", "가파도": "대정읍", "하모": "대정읍",
    "고산": "한경면", "한경": "한경면", "저지": "한경면", "신창": "한경면", "판포": "한경면",
    "노형": "노형동", "연동": "연동", "신제주": "연동", "누웨마루": "연동",
    "제주시청": "이도2동", "시청": "이도2동", "이도": "이도2동", "탑동": "삼도2동", "동문시장": "일도1동",
    "공항": "용담2동", "용담": "용담2동", "이호": "이호동", "도두": "도두동", "외도": "외도동",
    "삼양": "삼양동", "화북": "화북동", "아라": "아라동", "오라": "오라동", "봉개": "봉개동", "건입": "건입동",
    "우도": "우도면", "추자": "추자면",
    "서귀포시내": "중앙동", "서귀포 시내": "중앙동", "올레시장": "중앙동", "매일올레": "중앙동", "이중섭거리": "송산동",
    "법환": "대륜동", "강정": "대천동", "효돈": "효돈동", "쇠소깍": "효돈동", "호근": "서홍동", "토평": "영천동",
}

REGION_OF_AREA = {
    **{a: "제주시 시내" for a in ["건입동", "노형동", "도두동", "봉개동", "삼도1동", "삼도2동", "삼양동", "아라동", "연동", "오라동",
                              "외도동", "용담1동", "용담2동", "이도1동", "이도2동", "이호동", "일도1동", "일도2동", "화북동"]},
    "조천읍": "제주시 동부", "구좌읍": "제주시 동부", "우도면": "제주시 동부",
    "애월읍": "제주시 서부", "한림읍": "제주시 서부", "한경면": "제주시 서부", "추자면": "제주시 서부",
    **{a: "서귀포 시내" for a in ["대륜동", "대천동", "동홍동", "서홍동", "송산동", "영천동", "정방동", "중앙동", "천지동", "효돈동"]},
    "성산읍": "서귀포 동부", "표선면": "서귀포 동부", "남원읍": "서귀포 동부",
    "중문동": "서귀포 서부(중문)", "예래동": "서귀포 서부(중문)", "안덕면": "서귀포 서부(중문)", "대정읍": "서귀포 서부(중문)",
}

# 관광지 메타: 권역, 실내 여부(비·바람·추위 때 대안), 아이 동반 적합
SPOTS = {
    "천지연폭포": ("서귀포 시내", False, True), "한라산국립공원": ("제주시 시내", False, False),
    "성산일출봉": ("서귀포 동부", False, True), "카멜리아힐": ("서귀포 서부(중문)", False, True),
    "정방폭포": ("서귀포 시내", False, True), "비자림": ("제주시 동부", False, True),
    "한화아쿠아플라넷제주": ("서귀포 동부", True, True), "중문대포해안주상절리대": ("서귀포 서부(중문)", False, True),
    "마라해양도립공원": ("서귀포 서부(중문)", False, False), "절물자연휴양림": ("제주시 시내", False, True),
    "산방산": ("서귀포 서부(중문)", False, True), "천제연폭포": ("서귀포 서부(중문)", False, True),
    "국립제주박물관": ("제주시 시내", True, True), "민속자연사박물관": ("제주시 시내", True, True),
    "만장굴관광지": ("제주시 동부", True, True), "제주돌문화공원": ("제주시 동부", False, True),
    "박물관은살아있다": ("서귀포 서부(중문)", True, True), "서귀포도립해양공원": ("서귀포 시내", False, False),
    "해녀 박물관": ("제주시 동부", True, True), "서귀포자연휴양림": ("서귀포 서부(중문)", False, True),
    "제주목관아지": ("제주시 시내", False, True), "제주현대미술관": ("제주시 서부", True, False),
    "이중섭미술관": ("서귀포 시내", True, False), "서복전시관": ("서귀포 시내", True, False),
    "도립미술관": ("제주시 시내", True, False), "일출랜드": ("서귀포 동부", False, True),
    "퍼시픽랜드": ("서귀포 서부(중문)", True, True), "항몽 유적지": ("제주시 서부", False, False),
    "제주도립 김창열미술관": ("제주시 서부", True, False), "감귤박물관": ("서귀포 시내", True, True),
    "제주항일기념관": ("제주시 동부", True, False), "제주추사관": ("서귀포 서부(중문)", True, False),
    "제주별빛누리공원": ("제주시 시내", True, True), "제주국제평화센터": ("서귀포 서부(중문)", True, False),
    "삼양선사유적지": ("제주시 시내", False, False), "기당미술관": ("서귀포 시내", True, False),
}
REGIONS = ["제주시 시내", "제주시 동부", "제주시 서부", "서귀포 시내", "서귀포 동부", "서귀포 서부(중문)"]
REGION_WORDS = {
    "제주시 시내": ["제주시내", "제주 시내", "시내", "제주시"], "제주시 동부": ["동쪽", "동부", "함덕", "구좌", "조천", "김녕", "세화"],
    "제주시 서부": ["서쪽", "서부", "애월", "한림", "협재", "한경"], "서귀포 시내": ["서귀포시내", "서귀포 시내", "서귀포"],
    "서귀포 동부": ["성산", "표선", "남원"], "서귀포 서부(중문)": ["중문", "안덕", "대정", "모슬포", "산방"],
}


# ── 데이터 로드(캐시) ─────────────────────────────────────────────
@lru_cache(None)
def card():
    return pd.read_csv(os.path.join(P, "card_monthly.csv"), encoding="utf-8-sig")


@lru_cache(None)
def pop():
    return pd.read_csv(os.path.join(P, "pop_monthly.csv"), encoding="utf-8-sig")


@lru_cache(None)
def stores():
    return pd.read_csv(os.path.join(P, "stores.csv"), encoding="utf-8-sig")


@lru_cache(None)
def tour():
    return pd.read_csv(os.path.join(P, "tour_monthly.csv"), encoding="utf-8-sig")


@lru_cache(None)
def dow_idx():
    d = pd.read_csv(os.path.join(P, "dow_index.csv"), encoding="utf-8-sig")
    return dict(zip(d["요일"], d["지수"]))


@lru_cache(None)
def hour_idx():
    d = pd.read_csv(os.path.join(P, "hour_index.csv"), encoding="utf-8-sig")
    return dict(zip(d["시"], d["지수"]))


AREAS = sorted(REGION_OF_AREA.keys())


# ── 해석 보조(규칙 기반, LLM 결과 검증에도 사용) ───────────────────────
def resolve_area(text):
    if not text:
        return None
    t = str(text)
    for a in AREAS:  # 정식 읍면동명 우선
        if a in t or a.rstrip("읍면동") == t.strip():
            return a
    for k in sorted(AREA_ALIAS, key=len, reverse=True):
        if k in t:
            return AREA_ALIAS[k]
    return None


def resolve_biz(text):
    if not text:
        return None
    t = str(text)
    if t in BIZ:
        return t
    best = None
    for name, (_, _, words) in BIZ.items():
        for w in words:
            if w in t and (best is None or len(w) > best[1]):
                best = (name, len(w))
    return best[0] if best else None


def resolve_region(text):
    t = str(text or "")
    if t in REGIONS:
        return t
    a = resolve_area(t)
    if a:
        return REGION_OF_AREA[a]
    for r, ws in REGION_WORDS.items():
        if any(w in t for w in ws):
            return r
    return None


# ── 도구 1: 창업 리스크 진단 ─────────────────────────────────────────
def _series(area, biz_card):
    c = card()
    s = c[(c["읍면동명"] == area) & (c["업종명"] == biz_card)].groupby("ym")["이용금액"].sum().sort_index()
    full = pd.Series(0.0, index=sorted(c["ym"].unique()))
    full.update(s)
    return full


def _metrics(area, biz_card, store_kw):
    s = _series(area, biz_card)
    base = s[(s.index >= "2017-01") & (s.index <= "2019-12")]  # 평상시(코로나 이전) 3년
    if (base > 0).sum() < 24 or base.mean() < 3_000_000:
        return None
    m = base.groupby(base.index.str[5:7]).mean()  # 월별 평균(계절 패턴)
    seas = m / m.mean()
    shock_now = s[(s.index >= "2020-03") & (s.index <= "2020-05")].sum()
    shock_base = s[(s.index >= "2019-03") & (s.index <= "2019-05")].sum()
    y17, y19 = base[base.index.str[:4] == "2017"].sum(), base[base.index.str[:4] == "2019"].sum()
    pp = pop()
    pa = pp[(pp["읍면동명"] == area) & (pp["ym"] >= "2017-01") & (pp["ym"] <= "2019-12")][["거주인구", "근무인구", "방문인구"]].mean()
    visit_share = float(pa["방문인구"] / pa.sum()) if pa.sum() > 0 else np.nan
    st = stores()
    n_store = int(((st["행정동명"] == area) & (st["상권업종소분류명"].isin(store_kw))).sum())
    mon_sales = float(base[base.index.str[:4] == "2019"].mean())
    return {
        "월평균매출": mon_sales,
        "변동계수": float(base.std() / base.mean()),
        "계절쏠림": float(seas.max() / max(seas.min(), 1e-9)),
        "최악의달": m.idxmin(), "최악의달비율": float(seas.min()),
        "최고의달": m.idxmax(), "최고의달비율": float(seas.max()),
        "코로나충격": float(shock_now / shock_base - 1) if shock_base > 0 else np.nan,
        "성장률": float((y19 / y17) ** 0.5 - 1) if y17 > 0 else np.nan,
        "방문인구비중": visit_share,
        "점포수": n_store,
        "점포당월매출": mon_sales / n_store if n_store > 0 else np.nan,
        "_seasonal": seas.round(3).to_dict(),
        "_series": s.to_dict(),
    }


# 지표별 방향: +1 = 클수록 위험, -1 = 작을수록 위험
RISK_FACTORS = [
    ("변동계수", +1, 0.20, "매출이 달마다 얼마나 출렁이나"),
    ("계절쏠림", +1, 0.20, "성수기 대비 비수기 격차"),
    ("코로나충격", -1, 0.20, "외부 충격(2020년 봄) 때 매출 감소폭"),
    ("성장률", -1, 0.15, "2017→2019 연평균 성장"),
    ("방문인구비중", +1, 0.10, "관광·방문객 의존도"),
    ("점포당월매출", -1, 0.15, "경쟁 강도(점포 1곳당 매출)"),
]
GRADES = [(80, "A", "낮음"), (65, "B", "다소 낮음"), (50, "C", "보통"), (35, "D", "다소 높음"), (0, "E", "높음")]


@lru_cache(None)
def _peer_table(biz_name):
    biz_card, store_kw, _ = BIZ[biz_name]
    rows = {}
    for a in AREAS:
        m = _metrics(a, biz_card, tuple(store_kw))
        if m:
            rows[a] = {k: v for k, v in m.items() if not k.startswith("_")}
    return pd.DataFrame(rows).T


def _score(df):
    """같은 업종의 다른 읍면동과 비교한 백분위 → 0~100 안전점수(높을수록 안전)."""
    sc = pd.DataFrame(index=df.index)
    for k, d, w, _ in RISK_FACTORS:
        x = pd.to_numeric(df[k], errors="coerce")
        pct = x.rank(pct=True)
        safe = (1 - pct) if d > 0 else pct
        sc[k] = (safe.fillna(0.5) * 100).round(1)
    sc["종합"] = sum(sc[k] * w for k, _, w, _ in RISK_FACTORS).round(1)
    return sc


def grade_of(score):
    for cut, g, label in GRADES:
        if score >= cut:
            return g, label
    return "E", "높음"


def diagnose(area, biz_name):
    """창업 리스크 진단서. 반환: dict(숫자는 모두 결정적 계산)."""
    if biz_name not in BIZ:
        return {"error": f"업종 '{biz_name}'은 진단 목록에 없습니다.", "가능업종": list(BIZ)}
    if area not in REGION_OF_AREA:
        return {"error": f"지역 '{area}'을 찾지 못했습니다.", "가능지역": AREAS}
    biz_card, store_kw, _ = BIZ[biz_name]
    m = _metrics(area, biz_card, tuple(store_kw))
    peers = _peer_table(biz_name)
    if m is None or area not in peers.index:
        alt = alternatives(biz_name, top=3)
        return {"error": f"{area}의 '{biz_name}' 카드매출 표본이 너무 적어(월 300만원 미만 또는 24개월 미만) 등급을 매기지 않습니다.",
                "대안": alt}
    sc = _score(peers)
    s = float(sc.loc[area, "종합"])
    g, label = grade_of(s)
    rank = int(sc["종합"].rank(ascending=False).loc[area])
    reasons = []
    for k, d, w, desc in RISK_FACTORS:
        reasons.append({"지표": k, "설명": desc, "값": m[k], "안전점수": float(sc.loc[area, k]),
                        "업종중앙값": float(pd.to_numeric(peers[k], errors="coerce").median())})
    worst = sorted(reasons, key=lambda r: r["안전점수"])[:2]
    best = sorted(reasons, key=lambda r: -r["안전점수"])[:2]
    stress = {
        "평상시월매출": m["월평균매출"],
        "비수기월매출": m["월평균매출"] * m["최악의달비율"],
        "충격시월매출": m["월평균매출"] * (1 + m["코로나충격"]) if not np.isnan(m["코로나충격"]) else np.nan,
    }
    region = REGION_OF_AREA[area]
    return {
        "지역": area, "권역": region, "업종": biz_name, "카드업종": biz_card,
        "등급": g, "위험수준": label, "종합점수": s, "순위": rank, "비교지역수": len(sc),
        "지표": reasons, "약점": worst, "강점": best, "스트레스": stress,
        "최악의달": int(m["최악의달"]), "최악의달비율": m["최악의달비율"],
        "최고의달": int(m["최고의달"]), "최고의달비율": m["최고의달비율"],
        "점포수": m["점포수"], "seasonal": m["_seasonal"], "series": m["_series"],
        "대안": alternatives(biz_name, top=3, exclude=area) if g in ("D", "E") else [],
        "출처": [SOURCES["card"], SOURCES["pop"], SOURCES["stores"]],
    }


def alternatives(biz_name, top=3, exclude=None):
    """같은 업종으로 리스크가 가장 낮은 읍면동 Top N."""
    peers = _peer_table(biz_name)
    if peers.empty:
        return []
    sc = _score(peers).sort_values("종합", ascending=False)
    out = []
    for a, r in sc.iterrows():
        if a == exclude:
            continue
        out.append({"지역": a, "등급": grade_of(r["종합"])[0], "종합점수": float(r["종합"]),
                    "월평균매출": float(peers.loc[a, "월평균매출"])})
        if len(out) >= top:
            break
    return out


# ── 도구 2: 한가한 관광지 ─────────────────────────────────────────
DOW_NAMES = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일", "공휴일"]


def quiet_spots(month, dow="토요일", hour=14, region=None, indoor=False, kids=False, top=3):
    """해당 월·요일·시간의 예상 혼잡도를 계산해 덜 붐비는 관광지를 고른다."""
    t = tour()
    t = t[t["ym"] >= "2023-01"].copy()  # 최근 2년(2023~2024) 평균
    t["m"] = t["ym"].str[5:7].astype(int)
    by = t.groupby(["관광지명", "m"])["입장객"].mean().unstack().fillna(0)
    annual = by.mean(axis=1)
    cand = []
    di = dow_idx().get(dow if dow in DOW_NAMES else "토요일", 1.0)
    hi = hour_idx().get(int(hour) % 24, 1.0)
    for spot, (reg, ind, kid) in SPOTS.items():
        if spot not in by.index or annual.get(spot, 0) <= 0:
            continue
        mv = float(by.loc[spot, month]) if month in by.columns else 0.0
        if mv <= 0:
            continue  # 해당 월 운영 기록 없음
        if region and reg != region:
            continue
        if indoor and not ind:
            continue
        if kids and not kid:
            continue
        daily = mv / 30.4 * di
        hourly = daily / 9 * hi  # 운영 9시간 가정, 시간대 지수로 배분
        cand.append({"관광지": spot, "권역": reg, "실내": ind, "아이동반": kid,
                     "예상일방문객": round(daily), "예상시간당": round(hourly),
                     "평소대비": round(mv / annual[spot], 2)})
    if not cand:
        return {"error": "조건에 맞는 관광지가 없습니다. 조건(권역·실내·아이 동반)을 줄여 보십시오."}
    df = pd.DataFrame(cand)
    df["인기도"] = df["관광지"].map(annual)
    # '갈 만한 곳' 위주: 조건 내 인기 하위 25%(원래 한산한 곳)는 후보가 4곳 이상일 때 제외
    if len(df) >= 4:
        df = df[df["인기도"] >= df["인기도"].quantile(0.25)]
    # 혼잡지수(1.00 = 그 관광지의 평소 평균 붐빔) = 월 계절성 × 요일 지수 × 시간대 지수
    df["혼잡지수"] = (df["평소대비"] * di * hi).round(2)
    df["혼잡점수"] = df["혼잡지수"]
    df = df.sort_values(["혼잡지수", "인기도"], ascending=[True, False])
    hours = {h: hour_idx()[h] for h in range(9, 18)}
    best_h = min(hours, key=hours.get)
    peak_h = max(hours, key=hours.get)
    return {
        "월": month, "요일": dow, "시": int(hour), "권역": region or "전체", "실내만": indoor, "아이동반": kids,
        "추천": df.head(top).to_dict("records"),
        "피할곳": df.tail(2).iloc[::-1].to_dict("records"),
        "추천시간": best_h, "피크시간": peak_h,
        "시간절감률": round(1 - hours[best_h] / hours[peak_h], 3),
        "요일지수": di, "후보수": len(df),
        "출처": [SOURCES["tour"], SOURCES["dow"], SOURCES["hour"]],
    }


def area_tour_season(area):
    """진단 지역 권역의 관광지 월별 방문 패턴(관광 의존 설명용)."""
    reg = REGION_OF_AREA.get(area)
    spots = [s for s, v in SPOTS.items() if v[0] == reg]
    t = tour()
    t = t[(t["ym"] >= "2023-01") & (t["관광지명"].isin(spots))].copy()
    if t.empty:
        return None
    t["m"] = t["ym"].str[5:7].astype(int)
    mm = t.groupby("m")["입장객"].sum() / 2
    return {"권역": reg, "관광지": spots, "월별": (mm / mm.mean()).round(3).to_dict()}
