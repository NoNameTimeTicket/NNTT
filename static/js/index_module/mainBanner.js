export function initMainBanner() {
    const topSwiper = new Swiper('.swiper_banner_main', {
        slidesPerView: 1,
        spaceBetween: 0,
        loop: true,
        autoplay: {
            delay: 4000,
            disableOnInteraction: false,
            pauseOnMouseEnter: true,
        },
        pagination: {
            el: '.swiper-pagination',
            type: 'fraction',
        },
        navigation: {
            nextEl: '.swiper-button-next',
            prevEl: '.swiper-button-prev',
        },
    });

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
}