document.addEventListener('DOMContentLoaded', () => {

    // 상단 스와이퍼 (콘텐츠 메인) 초기화
    const topSwiper = new Swiper('.swiper_banner_main', {
        slidesPerView: 1,
        spaceBetween: 0,
        loop: true,
        autoplay: {
            delay: 4000, // 3초마다 자동으로 다음 슬라이드로 이동 (원하는 시간으로 조절 가능)
            disableOnInteraction: false, // 클릭/조작해도 자동 재생이 완전히 꺼지지 않도록 설정
            pauseOnMouseEnter: true,
        },

        // 스와이퍼 페이지 번호
        pagination: {
            el: '.swiper-pagination',
            type: 'fraction', // '1 / 3' 형태로 표시하는 타입            
        },

        // 넘기기버튼 
        navigation: {
            nextEl: '.swiper-button-next',
            prevEl: '.swiper-button-prev',
        },
    });

    // 스와이퍼 멈춤 버튼
    const toggleBtn = document.getElementById('btn-swiper-toggle');
    let isPausedByBtn = false;

    if (toggleBtn) {
        toggleBtn.addEventListener('click', (e) => {
            e.stopPropagation();

            if (!isPausedByBtn) {
                topSwiper.autoplay.stop();
                isPausedByBtn = true;
                toggleBtn.textContent = '▶';
            } else {
                topSwiper.autoplay.start();
                isPausedByBtn = false;
                toggleBtn.textContent = '⏸';
            }
        });
    }

    fetch('/api/upcoming')
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('upcoming-container');
            if (!container) return;

            if (!data || data.length === 0) {
                container.innerHTML = '<p class="empty-text">오픈 예정인 공연이 없습니다.</p>';
                return;
            }


            container.innerHTML = ''; // 로딩 텍스트 제거

            data.forEach(item => {
                const itemDiv = document.createElement('div');
                itemDiv.className = 'upcoming-card';

                const posterHtml = item.poster
                    ? `<img src="${item.poster}" alt="${item.prfnm}">`
                    : `<span style="color:#888; font-size:12px;">포스터 없음</span>`;

                // 📌 카드 전체를 a태그로 감싸고 포스터와 정보를 포함
                itemDiv.innerHTML = `
                <a href="/performances/${item.mt20id}" style="text-decoration: none; color: inherit; display: block; width: 100%;">
                    <div class="upcoming-list">
                        ${posterHtml}
                    </div>

                    <div class="upcoming-info">
                        <span class="upcoming-date">${item.prfpdfrom || ''} ~ ${item.prfpdto || ''}</span>
                        <span class="upcoming-title">${item.prfnm || ''}</span>
                    </div>
                </a>
                `;
                container.appendChild(itemDiv);
            });
        })
        .catch(err => {
            console.error("오픈예정 API 로드 실패:", err);
            const container = document.getElementById('upcoming-container');
            if (container) {
                container.innerHTML = '<p class="error-text">공연 정보를 불러오지 못했습니다.</p>';
            }
        });


    // 가격대 별 탭
    const tabItems = document.querySelectorAll('.price-tabs .tab-item');
    const priceContainer = document.getElementById('price-container');
    // 불러온 데이터를 저장할 캐시 객체
    const ticketCache = {};

    async function loadPriceData(priceType = '10k') {
        if (!priceContainer) return;

        // 이미 불러온 적 있는 데이터라면 캐시에서 가져옴 (서버 요청 생략)
        if (ticketCache[priceType]) {
            renderTickets(ticketCache[priceType]);
            return;
        }

        priceContainer.innerHTML = '<p class="loading-text">티켓 정보를 불러오는 중입니다...</p>';

        try {
            const response = await fetch(`/api/tickets/price?price=${priceType}`);
            if (!response.ok) throw new Error('API 불러오기 실패');

            const performances = await response.json();

            // 서버에서 가져온 데이터를 캐시에 저장
            ticketCache[priceType] = performances;

            renderTickets(performances);

        } catch (error) {
            console.error('가격대별 데이터 로딩 오류:', error);
            priceContainer.innerHTML = '<p class="error-text">정보를 불러오지 못했습니다.</p>';
        }
    }

    function renderTickets(performances) {
        if (!performances || performances.length === 0) {
            priceContainer.innerHTML = '<p class="empty-text">해당 조건의 티켓이 없습니다.</p>';
            return;
        }

        // 백틱(` `)을 사용해 HTML을 한 번에 결합 및 삽입
        priceContainer.innerHTML = performances.map(perf => `
                <div class="price-card">
                    <a href="/performances/${perf.mt20id}" style="text-decoration: none; color: inherit;">
                        <div class="price-list">
                            ${perf.poster
                                ? `<img class="poster-img" src="${perf.poster}" alt="${perf.prfnm || ''}">`
                                : `<span class="no-poster">포스터 없음</span>`
                            }        
                        </div>
                        <div class="price-info">                            
                            <span class="price-title">${perf.prfnm || ''}</span>
                            <span class="price-date">${perf.prfpd || ''}</span>
                            <span class="price-amount">${perf.pcse || ''}</span>
                        </div>
                    </a>
                </div>
            `).join('');
    }

    // 탭 클릭 이벤트 연결
    tabItems.forEach(tab => {
        tab.addEventListener('click', (e) => {
            e.preventDefault();

            tabItems.forEach(item => item.classList.remove('active'));
            tab.classList.add('active');

            const selectedPrice = tab.dataset.price || '10k';
            loadPriceData(selectedPrice);
        });
    });

    loadPriceData('10k');
});

