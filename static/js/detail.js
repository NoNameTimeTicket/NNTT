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
        const popupUrl = `/booking/popup`
            + `?performance_id=${perfId}`
            + `&title=${title}`
            + `&place_name=${place}`
            + `&address=${address}`
            + `&ticket_price=${price}`
            + `&time_notice=${timeNotice}`
            + `&start_date=${startDate}`
            + `&end_date=${endDate}`;

        const popupWidth = 900;
        const popupHeight = 780;

        // 현재 브라우저 창의 모니터 상 위치 구하기
        // 브라우저 호환성을 위해 window.screen을 모두 확인
        const dualScreenLeft = window.screenLeft !== undefined ? window.screenLeft : window.screenX;
        const dualScreenTop = window.screenTop !== undefined ? window.screenTop : window.screenY;

        const left = dualScreenLeft + (innerWidth - popupWidth) / 3;
        const top = dualScreenTop + (innerHeight - popupHeight) / 3;

        const popup = window.open(
            popupUrl,
            'BookingPopup', // 팝업창의 식별 이름
            `width=${popupWidth},height=${popupHeight},left=${left},top=${top},scrollbars=yes,resizable=no` // 팝업창 옵션
        );
        // 팝업창이 정상 생성되고 focus 메서드가 지원되면, 생성된 팝업창 맨 앞으로 이동
        if (window.focus && popup) {
            popup.focus();
        }
    });
});