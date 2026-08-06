# 2026-08-06
# 파싱 조수 (가격 숫자, 시간 텍스트 정리)
import re
from datetime import datetime, timedelta

# "전석 50,000원" 글자에서 숫자 50000만 추출하는 함수
def extract_price_number(price_text):
  if not price_text:
    return 50000 # 글자가 없으면 기본값 50,000원

  # 숫자 형태의 글자만 모읍니다.
  only_numbers =""
  for char in price_text:
    if char.isdigit(): # 숫자인지 확인
      only_numbers += char

  if only_numbers and int(only_numbers) >=1000:
    return int(only_numbers)

  return 50000 # 파싱 실패 시 기본값

# KOPIS 관람시간 문구에서 "15:00", "19:00" 같은 시간을 빼내는 함수
def parse_kopis_times(time_text):
  if not time_text:
         return['14:00', '19:00']
  found_times = re.findall(r'\d{2}:\d{2}', time_text)
  unique_time = sorted(list(set(found_times)))
  return unique_time if unique_time else ['14:00', '19:00']

# 공연 시작일~종료일 사이의 날짜 목록(YYYY-MM-DD)을 드롭다운용으로 생성
def generate_date_list(start_date_str, end_date_str):
   today = datetime.now().date()
   dates = []

   try:
      # KOPIS 날짜 형식(YYYY.MM.DD 또는 YYYY-MM-DD) 대응
      clean_start = start_date_str.replace('.', '-').strip()
      clean_end = end_date_str.replace('.', '-').strip()

      s_date = datetime.strptime(clean_start, "%Y-%m-%d").date()
      e_date = datetime.strptime(clean_end, "%Y-%m-%d").date()

      # 오늘 이전 과거 날짜는 제외하고, 오늘 이후부터만 리스트 구성
      curr_date = max(s_date, today)

      # 최대 60일치 날짜 목록 생성
      limit_days = 0
      while curr_date <= e_date and limit_days < 60:
          dates.append(curr_date.strftime("%Y-%m-%d"))
          curr_date += timedelta(days=1)
          limit_days += 1
   except Exception:
      # 날짜 형식 파싱 실패 시 오늘부터 14일간 기본 생성
      for i in range(14):
         dates.append((today + timedelta(days=i)).strftime("%Y-%m-%d"))

   return dates if dates else [today.strftime("%Y-%m-%d")]
