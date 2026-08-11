# 2026-08-06
# 파싱 조수 (가격 숫자, 시간 텍스트 정리)
import re
from datetime import datetime, timedelta

# KOPIS 관람시간 문구에서 "15:00", "19:00" 같은 시간을 빼내는 함수
def parse_kopis_times(time_text):
  if not time_text:
         return['14:00', '19:00']
  found_times = re.findall(r'\d{2}:\d{2}', time_text)
  unique_time = sorted(list(set(found_times)))
  return unique_time if unique_time else ['14:00', '19:00']
