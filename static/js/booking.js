//팝업 수량/금액 계산 리모컨 박근수
// C:\projects\NNTT\static\js\booking.js
document.addEventListener('DOMContentLoaded', function () {
    
    // HTML에 있는 요소(상자)들을 자바스크립트로 가져옵니다.
    const calendarContainer = document.getElementById('customCalendar');
    const dateInput = document.getElementById('datePicker');

    // 오늘 날짜 정보 계산하기
    const today = new Date();
    let currentYear = today.getFullYear();   // 올해 연도
    let currentMonth = today.getMonth();     // 이번 달
    let selectedDateStr = dateInput ? dateInput.value : '';

    // =========================================================
    // 🗓️ 1. 화면에 펼쳐진 전체 월력표를 직접 그려주는 기능
    // =========================================================
    function renderCalendar(year, month) {
        if (!calendarContainer) return;

        // 이번 달 1일이 무슨 요일인지, 이번 달이 며칠까지 있는지 계산합니다.
        const firstDay = new Date(year, month, 1).getDay(); 
        const lastDate = new Date(year, month + 1, 0).getDate(); 

        // 달력 상단 (이전달 버튼, 몇년 몇월 표시, 다음달 버튼) 및 요일 이름
        let html = `
            <div class="cal-header">
                <button type="button" id="prevMonthBtn" class="cal-nav-btn">&lt;</button>
                <span class="cal-title">${year}년 ${month + 1}월</span>
                <button type="button" id="nextMonthBtn" class="cal-nav-btn">&gt;</button>
            </div>
            <div class="cal-grid">
                <div class="cal-day-header sun">일</div>
                <div class="cal-day-header">월</div>
                <div class="cal-day-header">화</div>
                <div class="cal-day-header">수</div>
                <div class="cal-day-header">목</div>
                <div class="cal-day-header">금</div>
                <div class="cal-day-header sat">토</div>
        `;

        // 1일이 시작하기 전의 빈 칸들을 만들어줍니다.
        for (let i = 0; i < firstDay; i++) {
            html += `<div class="cal-date empty"></div>`;
        }

        // 1일부터 마지막 날까지 숫자 칸을 하나씩 만듭니다.
        for (let date = 1; date <= lastDate; date++) {
            const dateObj = new Date(year, month, date);
            const yyyy = year;
            const mm = String(month + 1).padStart(2, '0');
            const dd = String(date).padStart(2, '0');
            const fullStr = `${yyyy}-${mm}-${dd}`;

            // 지나간 과거 날짜는 클릭하지 못하게 막습니다.
            today.setHours(0, 0, 0, 0);
            const isPast = dateObj < today;
            const isSelected = fullStr === selectedDateStr;

            let classes = ['cal-date'];
            if (isPast) classes.push('disabled');     // 지나간 날짜 스타일
            if (isSelected) classes.push('selected'); // 선택된 날짜 스타일

            html += `<div class="${classes.join(' ')}" data-date="${fullStr}">${date}</div>`;
        }

        html += `</div>`;
        
        // 만들어진 달력 HTML을 화면에 집어넣습니다.
        calendarContainer.innerHTML = html;

        // ◀ 이전 달 버튼을 누르면 한 달 전 달력을 그려줍니다.
        document.getElementById('prevMonthBtn').onclick = function () {
            currentMonth--;
            if (currentMonth < 0) {
                currentMonth = 11;
                currentYear--;
            }
            renderCalendar(currentYear, currentMonth);
        };

        // ▶ 다음 달 버튼을 누르면 다음 달 달력을 그려줍니다.
        document.getElementById('nextMonthBtn').onclick = function () {
            currentMonth++;
            if (currentMonth > 11) {
                currentMonth = 0;
                currentYear++;
            }
            renderCalendar(currentYear, currentMonth);
        };

        // 👆 날짜 숫자를 클릭했을 때 빨갛게 선택되도록 하는 기능
        const dateCells = calendarContainer.querySelectorAll('.cal-date:not(.empty):not(.disabled)');
        dateCells.forEach(cell => {
            cell.onclick = function () {
                // 기존 선택 다 취소하고 클릭한 날짜만 빨갛게 만듭니다.
                calendarContainer.querySelectorAll('.cal-date').forEach(c => c.classList.remove('selected'));
                this.classList.add('selected');
                
                // 선택한 날짜 값을 저장합니다.
                selectedDateStr = this.getAttribute('data-date');
                if (dateInput) {
                    dateInput.value = selectedDateStr;
                }
            };
        });
    }

    // 처음 팝업이 열렸을 때 달력을 일단 한 번 그립니다.
    renderCalendar(currentYear, currentMonth);


    // =========================================================
    // 👥 2. 인원수 (+/-) 조절 및 결제 금액 자동 계산 기능
    // =========================================================
    let count = 1; // 기본 인원 1명

    const unitPriceInput = document.getElementById('unitPrice');
    const countNumSpan = document.getElementById('countNum');
    const ticketCountInput = document.getElementById('ticketCountInput');
    const totalPriceText = document.getElementById('totalPriceText');
    const btnMinus = document.getElementById('btnMinus');
    const btnPlus = document.getElementById('btnPlus');

    // 티켓 한 장 가격 가져오기 (없으면 50,000원)
    const unitPrice = unitPriceInput ? (parseInt(unitPriceInput.value) || 50000) : 50000;

    // 숫자를 더하고 빼주는 계산 공식
    function updateCount(diff) {
        count += diff;
        if (count < 1) count = 1;   // 최소 1명 이상만 선택 가능
        if (count > 10) count = 10; // 최대 10명까지만 선택 가능

        // 화면에 인원수 숫자 변경
        if (countNumSpan) countNumSpan.textContent = count;
        if (ticketCountInput) ticketCountInput.value = count;

        // 최종 금액 계산 (단가 × 인원수)
        const total = unitPrice * count;
        if (totalPriceText) {
            totalPriceText.textContent = total.toLocaleString() + '원';
        }
    }

    // 마이너스(-) 버튼 클릭 시 1명 빼기
    if (btnMinus) {
        btnMinus.addEventListener('click', function (e) {
            e.preventDefault();
            updateCount(-1);
        });
    }

    // 플러스(+) 버튼 클릭 시 1명 더하기
    if (btnPlus) {
        btnPlus.addEventListener('click', function (e) {
            e.preventDefault();
            updateCount(1);
        });
    }
});