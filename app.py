from flask import Flask, render_template
import requests
import xmltodict

app = Flask(__name__)
port_number = 8080

# 🔑 발급받은 KOPIS Open API 인증키를 여기에 넣으세요
KOPIS_API_KEY = "19fc20e402ce49df83b5d2f6e9d50822"

@app.route("/")
def index():
    # KOPIS 공연목록 조회 API URL
    url = "http://www.kopis.or.kr/openApi/restful/pblprfr"
    
    # 요청 파라미터 설정 (필요에 따라 시작일, 종료일, 페이지 수 등 조정 가능)
    params = {
        "service": KOPIS_API_KEY,
        "stdate": "20260701",   # 조회 시작일 (YYYYMMDD)
        "eddate": "20260731",   # 조회 종료일 (YYYYMMDD)
        "cpage": "1",           # 현재 페이지
        "rows": "12",           # 한 페이지당 출력 개수
        "prfstate": "02",        # 공연상태 (01: 공연예정, 02: 공연중, 03: 공연완료)
    }

    performances = []
    
    try:
        # KOPIS API 호출
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            # XML 응답 데이터를 파이썬 딕셔너리로 변환
            data_dict = xmltodict.parse(response.text)
            
            # 검색 결과가 있는 경우 추출
            if "dbs" in data_dict and "db" in data_dict["dbs"]:
                db_data = data_dict["dbs"]["db"]
                # 결과가 1개일 때는 dict, 여러 개일 때는 list로 들어오는 케이스 방지
                if isinstance(db_data, list):
                    performances = db_data
                else:
                    performances = [db_data]

            # 해당데이터 추출
            grouped_result = [
                [{"name": key, "value": val} for key, val in item.items()] for item in performances
            ]

            # key : value 조회
            # key : mt20id, prfnm, prfpdfrom, prfpdto, fcltynm, poster, area, genrenm, openrun, prfstate
            for idx, performance in enumerate(grouped_result):
                print(f"=== {idx+1}번째 공연 ===")
                for prop in performance:
                    print(f"{prop['name']}: {prop['value']}")
                print() # 줄바꿈
                    
    except Exception as e:
        print(f"API 호출 중 오류 발생: {e}")

    # index.html 화면으로 데이터 전달
    return render_template("index.html", performances=performances)

if __name__ == "__main__":
    app.run(debug=True, port=port_number)