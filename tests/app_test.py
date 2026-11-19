import sys, os
sys.stdout.reconfigure(encoding="utf-8")
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from streamlit.testing.v1 import AppTest

at = AppTest.from_file("../app.py", default_timeout=120).run()
assert not at.exception, at.exception
at.text_input(key="q1").input("애월에 카페 하나 차리면 괜찮수과?")
at.button(key="go1").click().run()
assert not at.exception, at.exception
print("TAB1 markdown:", [m.value[:80] for m in at.markdown][:6])
print("metrics:", [(m.label, m.value, m.delta) for m in at.metric])
at.text_input(key="q2").input("1월 일요일 비 오는데 애들이랑 갈 만한 실내 어디 한가해요?")
at.button(key="go2").click().run()
assert not at.exception, at.exception
print("TAB2 ok; markdown count", len(at.markdown))
at.text_input(key="q1").input("치킨집 하기 좋은 동네 어디우꽈?")
at.button(key="go1").click().run()
assert not at.exception, at.exception
print("tables:", len(at.table))
print("APPTEST PASS")
