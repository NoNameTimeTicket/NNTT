// static\js\index_module\
import { initMainBanner } from './index_module/mainBanner.js';
import { initUpcomingPerformances } from './index_module/upcoming.js';
import { initPriceTabs } from './index_module/priceTab.js';

document.addEventListener('DOMContentLoaded', () => {
    initMainBanner();               // 상단 광고 기능 호출
    initUpcomingPerformances();     // 공연 예정
    initPriceTabs();                // 가격대별 공연 분류 기능
});