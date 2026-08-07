// 박근수 2026-08-06
// static/js/detail.js
// detail.html에서 예약을 누르면 팝업에 정보를 보내주는 역할
// 화면이 다 만들어지면 실행됩니다.
document.addEventListener('DOMContentLoaded', function () {
    const btnOpen = document.getElementById('btnOpenPopup');
    if (!btnOpen) return;

    // '회차 선택 및 예매하기' 버튼을 클릭했을 때 작동
    btnOpen.addEventListener('click', function () {
        // 버튼 주머니(dataset)에 들어있던 공연 정보들을 꺼냅니다.
        const perfId = btnOpen.dataset.perfId;
        const title = encodeURIComponent(btnOpen.dataset.title || '');
        const place = encodeURIComponent(btnOpen.dataset.place || '');
        const address = encodeURIComponent(btnOpen.dataset.address || '');
        const price = encodeURIComponent(btnOpen.dataset.price || '');
        const timeNotice = encodeURIComponent(btnOpen.dataset.timeNotice || '');
        const startDate = encodeURIComponent(btnOpen.dataset.startDate || '');
        const endDate = encodeURIComponent(btnOpen.dataset.endDate || '');

        
        // 정보들을 가지고 갈 팝업창 주소를 만듭니다.
        const popupUrl = `/booking/popup?performance_id=${perfId}&title=${title}&place_name=${place}&address=${address}&ticket_price=${price}&time_notice=${timeNotice}`;

        // width를 780px로 140px 더 넓혀서 달력이 들어갈 공간을 확보했습니다.
        window.open(popupUrl, 'BookingPopup', 'width=780,height=620,scrollbars=yes,resizable=no');
    });
});