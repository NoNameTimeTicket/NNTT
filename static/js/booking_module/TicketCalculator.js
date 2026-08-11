export class TicketCalculator {
    constructor(options = {}) {
        this.min = options.min || 1;
        this.max = options.max || 10;
        this.count = this.min;

        this.unitPriceInput = document.getElementById('unitPrice');
        this.countNumSpan = document.getElementById('countNum');
        this.ticketCountInput = document.getElementById('ticketCountInput');
        this.totalPriceText = document.getElementById('totalPriceText');
        this.btnMinus = document.getElementById('btnMinus');
        this.btnPlus = document.getElementById('btnPlus');

        this.init();
    }

    init() {
        this.bindEvents();
        this.updateCount(0); // 초기 상태 계산
    }

    getCurrentUnitPrice() {
        const checkedRadio = document.querySelector('input[name="price_type"]:checked');
        if (checkedRadio) {
            return parseInt(String(checkedRadio.value).replace(/[^0-9]/g, '')) || 0;
        }
        if (this.unitPriceInput) {
            return parseInt(String(this.unitPriceInput.value).replace(/[^0-9]/g, '')) || 0;
        }
        return 50000; // Default fallback
    }

    updateCount(diff) {
        this.count += diff;
        if (this.count < this.min) this.count = this.min;
        if (this.count > this.max) this.count = this.max;

        if (this.countNumSpan) this.countNumSpan.textContent = this.count;
        if (this.ticketCountInput) this.ticketCountInput.value = this.count;

        const currentUnitPrice = this.getCurrentUnitPrice();
        if (this.unitPriceInput) {
            this.unitPriceInput.value = currentUnitPrice;
        }

        const total = currentUnitPrice * this.count;
        if (this.totalPriceText) {
            this.totalPriceText.textContent = total.toLocaleString() + '원';
        }
    }

    bindEvents() {
        if (this.btnMinus) {
            this.btnMinus.addEventListener('click', (e) => {
                e.preventDefault();
                this.updateCount(-1);
            });
        }

        if (this.btnPlus) {
            this.btnPlus.addEventListener('click', (e) => {
                e.preventDefault();
                this.updateCount(1);
            });
        }

        // 📌 [개선] document 전체 대신 price_type 라디오 버튼 집합에만 이벤트 타겟팅
        const priceRadios = document.querySelectorAll('input[name="price_type"]');
        priceRadios.forEach(radio => {
            radio.addEventListener('change', () => this.updateCount(0));
        });
    }
}