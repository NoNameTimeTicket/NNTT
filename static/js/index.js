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
    // 장르별 탭
    const tabItems = document.querySelectorAll('.tab-item');
    const rankItems = document.querySelectorAll('.rank-item');

    tabItems.forEach(tab => {
        tab.addEventListener('click', () => {        
            tabItems.forEach(item => item.classList.remove('active'));
            tab.classList.add('active');

            // 장르 값
            const selectedGenre = tab.getAttribute('data-genre');
           
            // 필터링
            rankItems.forEach(item => {
                const itemGenre = item.getAttribute('data-genre');

                if (selectedGenre === 'all' || selectedGenre === itemGenre) {                    
                    item.style.display = 'block';
                } else {                    
                    item.style.display = 'none';
                }
            });
        });
    });
});

