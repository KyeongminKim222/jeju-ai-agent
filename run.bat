@echo off
chcp 65001 >nul
cd /d %~dp0
title 제주 장사·나들이 AI 비서
if not exist .venv\Scripts\python.exe (
  echo [1/2] 처음 실행: 파이썬 가상환경을 만듭니다...
  py -3 -m venv .venv || python -m venv .venv
  if exist wheelhouse (
    .venv\Scripts\python -m pip install --no-index --find-links wheelhouse -r requirements.txt
  ) else (
    .venv\Scripts\python -m pip install -r requirements.txt
  )
)
if not exist data\processed\card_monthly.csv (
  echo [2/2] 데이터 가공 중...
  .venv\Scripts\python build_data.py
)
echo 브라우저가 열립니다. 이 창은 닫지 마세요.
.venv\Scripts\python -m streamlit run app.py --server.headless false --browser.gatherUsageStats false
pause
