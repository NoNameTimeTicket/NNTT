//팝업 수량/금액 계산 리모컨 박근수
// static\js\booking.js

// static\js\booking_module\
import { CalendarManager } from './booking_module/CalendarManager.js';
import { TicketCalculator } from './booking_module/TicketCalculator.js';

document.addEventListener('DOMContentLoaded', function () {
    // 1. 달력 생성 (CalendarManager.js)
    new CalendarManager('customCalendar', 'datePicker');

    // 2. 인원 및 결제금액 계산기 생성 (TicketCalculator.js)
    new TicketCalculator({ min: 1, max: 10 });
});