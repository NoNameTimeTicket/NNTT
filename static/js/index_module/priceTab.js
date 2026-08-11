const ticketCache = {};

function renderTickets(container, performances) {
    if (!performances || performances.length === 0) {
        container.innerHTML = '<p class="empty-text">해당 조건의 티켓이 없습니다.</p>';
        return;
    }

    container.innerHTML = performances.map(perf => `
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

async function loadPriceData(container, priceType = '10k') {
    if (ticketCache[priceType]) {
        renderTickets(container, ticketCache[priceType]);
        return;
    }

    container.innerHTML = '<p class="loading-text">티켓 정보를 불러오는 중입니다...</p>';

    try {
        const response = await fetch(`/api/tickets/price?price=${priceType}`);
        if (!response.ok) throw new Error('API 불러오기 실패');

        const performances = await response.json();
        ticketCache[priceType] = performances;
        renderTickets(container, performances);
    } catch (error) {
        console.error('가격대별 데이터 로딩 오류:', error);
        container.innerHTML = '<p class="error-text">정보를 불러오지 못했습니다.</p>';
    }
}

export function initPriceTabs() {
    const tabItems = document.querySelectorAll('.price-tabs .tab-item');
    const priceContainer = document.getElementById('price-container');

    if (!priceContainer) return;

    tabItems.forEach(tab => {
        tab.addEventListener('click', (e) => {
            e.preventDefault();

            tabItems.forEach(item => item.classList.remove('active'));
            tab.classList.add('active');

            const selectedPrice = tab.dataset.price || '10k';
            loadPriceData(priceContainer, selectedPrice);
        });
    });

    loadPriceData(priceContainer, '10k');
}