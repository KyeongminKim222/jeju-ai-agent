"""제주데이터허브 원천 CSV → 분석용 가공 데이터(data/processed) 생성.
한 번만 실행하면 된다. 결과물은 작은 CSV라 센터 PC에서도 즉시 로드된다.
python build_data.py
"""
import glob, os, sys
import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "data", "raw")
OUT = os.path.join(ROOT, "data", "processed")
os.makedirs(OUT, exist_ok=True)


def rd(p, **kw):
    for enc in ("utf-8-sig", "cp949"):
        try:
            return pd.read_csv(p, encoding=enc, low_memory=False, **kw)
        except Exception:
            pass
    raise RuntimeError(f"읽기 실패: {p}")


def norm_ym(s):
    """'2018-01-01' / '2019-01' / '21-Apr' → 'YYYY-MM'"""
    s = str(s).strip()
    if len(s) >= 7 and s[4] == "-":
        return s[:7]
    try:
        return pd.to_datetime(s, format="%y-%b").strftime("%Y-%m")
    except Exception:
        return None


def build_card():
    # [데이터허브 id 748] 상권분석을 위한 유동인구에 따른 카드 매출액 변화 (읍면동×업종×월, 2017-01~2021-05)
    fs = sorted(glob.glob(os.path.join(RAW, "748_*.csv")))
    a = pd.concat([rd(p) for p in fs], ignore_index=True)
    a["ym"] = a["년월"].map(norm_ym)
    a = a.dropna(subset=["ym"])
    pop = (a[a["성별"] != "법인"].groupby(["ym", "읍면동명"])[["거주인구", "근무인구", "방문인구"]]
           .first().reset_index())
    card = (a.groupby(["ym", "시도명", "읍면동명", "업종명"])[["이용자수", "이용금액"]]
            .sum().reset_index())
    card.to_csv(os.path.join(OUT, "card_monthly.csv"), index=False, encoding="utf-8-sig")
    pop.to_csv(os.path.join(OUT, "pop_monthly.csv"), index=False, encoding="utf-8-sig")
    print("card_monthly", card.shape, card["ym"].min(), "~", card["ym"].max())


def build_stores():
    # [데이터허브 id 793] 제주특별자치도 상가(상권) 정보 (2025-09 기준)
    st = rd(os.path.join(RAW, "793_5789.csv"))
    keep = ["상호명", "상권업종대분류명", "상권업종중분류명", "상권업종소분류명", "표준산업분류명",
            "시군구명", "행정동명", "경도", "위도"]
    st[keep].to_csv(os.path.join(OUT, "stores.csv"), index=False, encoding="utf-8-sig")
    print("stores", st.shape)


def build_tour():
    # [189/190] 내국인·외국인 관광지 입장객 수 추이 (관광지×월, 2009-01~2024-12)
    # 주의: '날짜'를 숫자로 읽으면 2023.10(10월)이 2023.1(1월)로 바뀐다 → 반드시 문자열로 읽는다
    k = rd(os.path.join(RAW, "189_5788.csv"), dtype={"날짜": str}).rename(columns={"관광객수": "내국인"})
    f = rd(os.path.join(RAW, "190_5787.csv"), dtype={"날짜": str}).rename(columns={"관광객수": "외국인"})
    t = k.merge(f, on=["날짜", "관광지명"], how="outer").fillna(0)
    yy = t["날짜"].str.split(".").str[0]
    mm = t["날짜"].str.split(".").str[1].str.zfill(2)
    t["ym"] = yy + "-" + mm
    bad = ~t["ym"].str.match(r"^\d{4}-(0[1-9]|1[0-2])$")
    if bad.any():
        print("날짜 형식 오류 제외:", int(bad.sum()))
    t = t[~bad]
    t["입장객"] = t["내국인"] + t["외국인"]
    t = t.dropna(subset=["ym"])[["ym", "관광지명", "내국인", "외국인", "입장객"]]
    t.to_csv(os.path.join(OUT, "tour_monthly.csv"), index=False, encoding="utf-8-sig")
    print("tour_monthly", t.shape, t["ym"].min(), "~", t["ym"].max())


def build_profiles():
    # [504] 요일별 카드 이용 건수 (2018-01~2025-06) → 요일 지수
    w = rd(os.path.join(RAW, "504_5852.csv"))
    w = w[w["base_year_month"] >= 202301]
    dow = w.groupby("day_of_week")["use_count"].sum()
    days = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일", "공휴일"]
    # 공휴일은 월 중 일수가 적으므로 일평균 환산: 대략 월 1.2일 vs 요일 4.3일
    per_day = {d: dow.get(d, 0) / (1.2 if d == "공휴일" else 4.3) for d in days}
    m = sum(per_day[d] for d in days[:7]) / 7
    pd.DataFrame({"요일": days, "지수": [round(per_day[d] / m, 3) for d in days]}) \
        .to_csv(os.path.join(OUT, "dow_index.csv"), index=False, encoding="utf-8-sig")
    # [520] 제주도 방문 내국인 유동인구 시간대별 (2018-01~2025-04) → 시간 지수
    h = rd(os.path.join(RAW, "520_5847.csv"))
    h = h[h["base_year_month"] >= 202301]
    hr = h.groupby("time_range")["visit_population_count"].sum()
    hr.index = [int(str(x).replace("시", "")) % 24 for x in hr.index]
    hr = hr.groupby(level=0).sum().sort_index()
    pd.DataFrame({"시": hr.index, "지수": (hr / hr.mean()).round(3).values}) \
        .to_csv(os.path.join(OUT, "hour_index.csv"), index=False, encoding="utf-8-sig")
    print("profiles ok")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    build_card(); build_stores(); build_tour(); build_profiles()
    print("DONE")
