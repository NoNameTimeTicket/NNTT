// C:\projects\NNTT\static\js\orders.js

// 🗓️ 1. 월별 보기 선택 시 페이지 이동
function filterByMonth(selectedMonth) {
  if (selectedMonth) {
    window.location.href = '/booking/orders?month=' + selectedMonth;
  } else {
    // [수정] 맨 앞 슬래시(/) 추가하여 404 에러 방지
    window.location.href = '/booking/orders';
  }
}

// 2. 네이버지도 새 창 열기 (v5 검색 경로)
function openNaverMap(address) {
  if (!address || address === '공연장 주소 미정') {
    alert('등록된 주소 정보가 없습니다.');
    return;
  }
  const naverMapUrl = 'https://map.naver.com/v5/search/' + encodeURIComponent(address);
  window.open(naverMapUrl, '_blank', 'width=950, height=650');
}

// 🎟️ 3. 티켓 확인증 모달 열기 (HTML의 data-* 속성 읽기)
function openTicketModal(btnElement) {
  // [수정] data-date 속성값 읽어오기
  const orderId = btnElement.getAttribute('data-id');
  const place = btnElement.getAttribute('data-place');
  const date = btnElement.getAttribute('data-date');
  const address = btnElement.getAttribute('data-address');

  // [수정] HTML 대소문자(modalID) 맞춤 및 날짜/주소 데이터 각각 제대로 입력
  document.getElementById('modalID').textContent = '#' + orderId;
  document.getElementById('modalPlace').textContent = place;
  document.getElementById('modalDate').textContent = date || '-';
  document.getElementById('modalAddress').textContent = address || '주소 없음';

  // 네이버지도 버튼 이벤트 연결
  document.getElementById('modalMapBtn').onclick = function () {
    openNaverMap(address);
  };

  document.getElementById('ticketModal').style.display = 'flex';
}

// ❌ 4. 모달창 닫기
function closeTicketModal() {
  document.getElementById('ticketModal').style.display = 'none';
}

// ⚠️ 5. 예매 취소 확인창
function confirmCancel() {
  return confirm('정말로 이 예매 건을 취소하시겠습니까?');
}

// ESC 키 눌렀을 때 모달 닫기
document.addEventListener('keydown', function (event) {
  if (event.key === 'Escape') {
    closeTicketModal();
  }
});