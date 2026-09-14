document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('reportsChart');
    if (!container) return;

    const labels = JSON.parse(document.getElementById('chartLabels').textContent);
    const totals = JSON.parse(document.getElementById('chartTotals').textContent);
    const completed = JSON.parse(document.getElementById('chartCompleted').textContent);

    const width = 560;
    const height = 240;
    const paddingLeft = 34;
    const paddingBottom = 24;
    const chartHeight = height - paddingBottom;
    const maxValue = Math.max(1, ...totals, ...completed);
    const barGroupWidth = (width - paddingLeft) / labels.length;
    const barWidth = Math.min(22, barGroupWidth / 3);

    const yTicks = 5;
    let gridLines = '';
    let yLabels = '';
    for (let i = 0; i <= yTicks; i++) {
        const value = Math.round((maxValue / yTicks) * i);
        const y = chartHeight - (chartHeight * i) / yTicks;
        gridLines += `<line x1="${paddingLeft}" y1="${y}" x2="${width}" y2="${y}" stroke="var(--color-border)" stroke-width="1" />`;
        yLabels += `<text x="${paddingLeft - 8}" y="${y + 4}" font-size="11" fill="var(--color-text-light)" text-anchor="end">${value}</text>`;
    }

    let bars = '';
    let xLabels = '';
    labels.forEach((label, i) => {
        const groupX = paddingLeft + i * barGroupWidth + barGroupWidth / 2;
        const totalHeight = (totals[i] / maxValue) * chartHeight;
        const completedHeight = (completed[i] / maxValue) * chartHeight;

        bars += `<rect x="${groupX - barWidth}" y="${chartHeight - totalHeight}" width="${barWidth}" height="${totalHeight}" rx="3" fill="var(--color-border)" />`;
        bars += `<rect x="${groupX}" y="${chartHeight - completedHeight}" width="${barWidth}" height="${completedHeight}" rx="3" fill="var(--color-primary)" />`;
        xLabels += `<text x="${groupX}" y="${height - 4}" font-size="11" fill="var(--color-text-light)" text-anchor="middle">${label}</text>`;
    });

    container.innerHTML = `
        <svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="xMidYMid meet">
            ${gridLines}
            ${bars}
            ${yLabels}
            ${xLabels}
        </svg>
    `;
});
