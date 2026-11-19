import sys, time, json, datetime as dt
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
from agent import core
Q = [
    "애월에 카페 하나 차리면 괜찮수과?",
    "연동에서 한식당 하면 장사 될까요",
    "성산에 펜션 하나 더 열면 어떵 되우꽈",
    "치킨집 하기 좋은 동네 어디우꽈?",
    "8월 토요일 오후 2시에 덜 붐비는 데 어디?",
    "1월 일요일 비 오는데 애들이랑 갈 만한 실내 어디 한가해요?",
    "다음 주말 동쪽에 사람 적은 관광지 추천해줘",
    "우도에 카페 열면?",
    "안녕",
]
print("LLM:", core.llm_available())
for use in (False, True):
    print("\n########## use_llm =", use)
    for q in Q:
        t = time.time()
        r = core.run(q, use_llm=use, today=dt.date(2026, 11, 19))
        print(f"\n[Q] {q}  ({time.time()-t:.1f}s)")
        for a, b in r["trace"]:
            print("   ", a, ":", b)
        print("  A:", r["answer"])
