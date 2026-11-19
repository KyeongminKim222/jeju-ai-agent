"""평가 스크립트: 질문 이해 정확도 · 재현성 · 응답시간을 측정해 outputs/eval.json 저장.
python tests/eval.py
"""
import json, os, sys, time
sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from agent import core  # noqa: E402

CASES = [
    ("애월에 카페 하나 차리면 괜찮수과?", "diagnose", "애월읍", "카페"),
    ("함덕에 술집 차리면 어때요", "diagnose", "조천읍", "술집"),
    ("서귀포 시내에서 빵집 하면 괜찮을까", "diagnose", "중앙동", "빵집"),
    ("노형동 편의점 매출 괜찮나요", "diagnose", "노형동", "편의점"),
    ("표선에 횟집 열면 망할까요", "diagnose", "표선면", "일식·횟집"),
    ("세화에 게스트하우스 하려는데", "diagnose", "구좌읍", "숙박(모텔·여관)"),
    ("연동에서 한식당 하면 장사 될까요", "diagnose", "연동", "한식당"),
    ("우도에 카페 열면?", "diagnose", "우도면", "카페"),
    ("성산에 펜션 하나 더 열면 어떵 되우꽈", "diagnose", "성산읍", "숙박(모텔·여관)"),
    ("모슬포에 치킨집 차려도 될까", "diagnose", "대정읍", "치킨·피자·버거"),
    ("렌터카 사업 어느 동네가 나아요", "compare", None, "렌터카"),
    ("화장품 가게 하기 좋은 동네", "compare", None, "화장품"),
    ("치킨집 하기 좋은 동네 어디우꽈?", "compare", None, "치킨·피자·버거"),
    ("중문 근처 7월 일요일 오전에 한가한 데", "quiet", None, None),
    ("비 오는 날 실내 갈 데 덜 붐비는 곳", "quiet", None, None),
    ("주말에 애들이랑 사람 없는 데 가고 싶어", "quiet", None, None),
    ("8월 토요일 오후 2시에 덜 붐비는 데 어디?", "quiet", None, None),
    ("다음 주말 동쪽에 사람 적은 관광지 추천해줘", "quiet", None, None),
    ("1월 일요일 비 오는데 애들이랑 갈 만한 실내 어디 한가해요?", "quiet", None, None),
    ("설 연휴에 서귀포 쪽 덜 붐비는 데", "quiet", None, None),
]


def main():
    llm = core.llm_available()
    res = {"llm": llm, "model": core.MODEL, "cases": []}
    for mode in ([False, True] if llm else [False]):
        ok, ts = 0, []
        for q, tl, a, b in CASES:
            t = time.time()
            r = core.run(q, use_llm=mode)
            ts.append(time.time() - t)
            s = r["slots"]
            good = (r["tool"] == tl and (a is None or s["area"] == a) and (b is None or s["biz"] == b))
            ok += good
            res["cases"].append({"mode": "LLM+규칙" if mode else "규칙", "q": q, "ok": bool(good), "tool": r["tool"],
                                 "area": s["area"], "biz": s["biz"]})
        res["LLM+규칙" if mode else "규칙"] = {"정확도": f"{ok}/{len(CASES)}", "평균응답초": round(sum(ts) / len(ts), 2),
                                           "최대응답초": round(max(ts), 2)}
    # 재현성: 같은 질문 10회 → 같은 답
    outs = {core.run("애월에 카페 하나 차리면 괜찮수과?", use_llm=llm)["answer"] for _ in range(10)}
    res["재현성"] = f"같은 질문 10회 → 서로 다른 답 {len(outs)}개"
    json.dump(res, open(os.path.join(ROOT, "outputs", "eval.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "cases"}, ensure_ascii=False, indent=1))
    for c in res["cases"]:
        if not c["ok"]:
            print("FAIL", c)


if __name__ == "__main__":
    main()
