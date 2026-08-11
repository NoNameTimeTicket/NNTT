export class CalendarManager {
    constructor(containerId, dateInputId) {
        this.container = document.getElementById(containerId);
        this.dateInput = document.getElementById(dateInputId);

        if (!this.container) return;

        // data- 속성 정보 추출
        this.startDateStr = this.container.getAttribute('data-start-date') || '';
        this.endDateStr = this.container.getAttribute('data-end-date') || '';
        this.allowedDays = (this.container.getAttribute('data-allowed-days') || '0,1,2,3,4,5,6')
                            .split(',')
                            .map(Number);

        const today = new Date();
        this.currentYear = today.getFullYear();
        this.currentMonth = today.getMonth();

        // 초기 선택 날짜를 지정하지 않고 완전히 비워둡니다 (유저 직접 선택 전용)
        this.selectedDateStr = '';
        if (this.dateInput) {
            this.dateInput.value = '';
        }

        this.init();
    }

    init() {
        this.render();
        this.bindEvents();

        // 달력이 로드되었을 때, 선택된 날짜가 없으므로 결제 버튼을 비활성화해 둡니다.
        const payBtn = document.querySelector('.btn-pay');
        if (payBtn) {
            payBtn.disabled = true;
        }
    }

    render() {
        if (!this.container) return;

        const firstDay = new Date(this.currentYear, this.currentMonth, 1).getDay();
        const lastDate = new Date(this.currentYear, this.currentMonth + 1, 0).getDate();

        let html = `
            <div class="cal-header">
                <button type="button" class="cal-nav-btn btn-prev">&lt;</button>
                <span class="cal-title">${this.currentYear}년 ${this.currentMonth + 1}월</span>
                <button type="button" class="cal-nav-btn btn-next">&gt;</button>
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

        for (let i = 0; i < firstDay; i++) {
            html += `<div class="cal-date empty"></div>`;
        }

        for (let date = 1; date <= lastDate; date++) {
            const dateObj = new Date(this.currentYear, this.currentMonth, date);
            const mm = String(this.currentMonth + 1).padStart(2, '0');
            const dd = String(date).padStart(2, '0');
            const fullStr = `${this.currentYear}-${mm}-${dd}`;

            let isDisabled = false;
            if (this.startDateStr && fullStr < this.startDateStr) isDisabled = true;
            if (this.endDateStr && fullStr > this.endDateStr) isDisabled = true;
            if (!this.allowedDays.includes(dateObj.getDay())) isDisabled = true;

            // 📌 [수정 2] selectedDateStr 값이 비어있으므로 처음에 아무 날짜도 selected 되지 않습니다.
            const isSelected = this.selectedDateStr && fullStr === this.selectedDateStr;
            
            const classes = ['cal-date'];
            if (isDisabled) classes.push('disabled');
            if (isSelected) classes.push('selected');

            html += `<div class="${classes.join(' ')}" data-date="${fullStr}">${date}</div>`;
        }

        html += `</div>`;
        this.container.innerHTML = html;
    }

    bindEvents() {
        this.container.addEventListener('click', (e) => {
            const target = e.target;

            if (target.classList.contains('btn-prev')) {
                this.currentMonth--;
                if (this.currentMonth < 0) {
                    this.currentMonth = 11;
                    this.currentYear--;
                }
                this.render();
            }

            if (target.classList.contains('btn-next')) {
                this.currentMonth++;
                if (this.currentMonth > 11) {
                    this.currentMonth = 0;
                    this.currentYear++;
                }
                this.render();
            }

            // 날짜 선택 이벤트 처리
            if (target.classList.contains('cal-date') && !target.classList.contains('empty')) {
                const payBtn = document.querySelector('.btn-pay');

                // 1) 비활성화된 날짜 클릭 시
                if (target.classList.contains('disabled')) {
                    this.container.querySelectorAll('.cal-date').forEach(c => c.classList.remove('selected'));
                    this.selectedDateStr = '';
                    if (this.dateInput) this.dateInput.value = '';

                    if (payBtn) payBtn.disabled = true;

                    alert('선택할 수 없는 날짜입니다.');
                    return;
                }

                // 2) 정상적인 날짜 클릭 시
                this.container.querySelectorAll('.cal-date').forEach(c => c.classList.remove('selected'));
                target.classList.add('selected');

                this.selectedDateStr = target.getAttribute('data-date');
                if (this.dateInput) {
                    this.dateInput.value = this.selectedDateStr;
                }

                // 정상 날짜 선택 시에만 결제 버튼 활성화
                if (payBtn) payBtn.disabled = false;
            }
        });
    }
}