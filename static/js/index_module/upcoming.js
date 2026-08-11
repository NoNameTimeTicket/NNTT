// 오픈 예정 공연: /api/upcoming 데이터 가져와서 HTML 생성
export async function initUpcomingPerformances() {
    const container = document.getElementById('upcoming-container');
    if (!container) return;

    try {
        const response = await fetch('/api/upcoming');
        const data = await response.json();

        if (!data || data.length === 0) {
            container.innerHTML = '<p class="empty-text">오픈 예정인 공연이 없습니다.</p>';
            return;
        }

        container.innerHTML = data.map(item => {
            const posterHtml = item.poster
                ? `<img src="${item.poster}" alt="${item.prfnm}">`
                : `<span style="color:#888; font-size:12px;">포스터 없음</span>`;

            return `
                <div class="upcoming-card">
                    <a href="/performances/${item.mt20id}" style="text-decoration: none; color: inherit; display: block; width: 100%;">
                        <div class="upcoming-list">${posterHtml}</div>
                        <div class="upcoming-info">
                            <span class="upcoming-date">${item.prfpdfrom || ''} ~ ${item.prfpdto || ''}</span>
                            <span class="upcoming-title">${item.prfnm || ''}</span>
                        </div>
                    </a>
                </div>
            `;
        }).join('');
    } catch (err) {
        console.error("오픈예정 API 로드 실패:", err);
        container.innerHTML = '<p class="error-text">공연 정보를 불러오지 못했습니다.</p>';
    }
}