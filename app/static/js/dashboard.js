/**
 * Dashboard & Analytics Charts using Chart.js
 */

document.addEventListener('DOMContentLoaded', async () => {
    const trendCtx = document.getElementById('trendChart');
    const categoryCtx = document.getElementById('categoryChart');
    const severityCtx = document.getElementById('severityChart');
    const zoneCtx = document.getElementById('zoneChart');

    if (!trendCtx && !categoryCtx && !severityCtx && !zoneCtx) return;

    try {
        const response = await fetch('/api/analytics-data');
        const data = await response.json();

        // 1. 7-Day Complaint Trend Chart
        if (trendCtx && data.trends) {
            new Chart(trendCtx, {
                type: 'line',
                data: {
                    labels: data.trends.labels,
                    datasets: [
                        {
                            label: 'New Defects Reported',
                            data: data.trends.intake,
                            borderColor: '#3b82f6',
                            backgroundColor: 'rgba(59, 130, 246, 0.15)',
                            fill: true,
                            tension: 0.4,
                            borderWidth: 2
                        },
                        {
                            label: 'Resolved Defects',
                            data: data.trends.resolved,
                            borderColor: '#10b981',
                            backgroundColor: 'rgba(16, 185, 129, 0.15)',
                            fill: true,
                            tension: 0.4,
                            borderWidth: 2
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'top' }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: { precision: 0 }
                        }
                    }
                }
            });
        }

        // 2. Defect Distribution Doughnut Chart
        if (categoryCtx && data.categories) {
            new Chart(categoryCtx, {
                type: 'doughnut',
                data: {
                    labels: data.categories.labels,
                    datasets: [{
                        data: data.categories.counts,
                        backgroundColor: ['#e63946', '#f77f00', '#2a9d8f', '#3a86ff'],
                        borderWidth: 2,
                        borderColor: '#ffffff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'bottom' }
                    }
                }
            });
        }

        // 3. Severity Distribution Bar Chart
        if (severityCtx && data.severities) {
            new Chart(severityCtx, {
                type: 'bar',
                data: {
                    labels: data.severities.labels,
                    datasets: [{
                        label: 'Defect Severity Count',
                        data: data.severities.counts,
                        backgroundColor: ['#10b981', '#3b82f6', '#f59e0b', '#ef4444'],
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { beginAtZero: true, ticks: { precision: 0 } }
                    }
                }
            });
        }

        // 4. Zone Breakdown Horizontal Bar Chart
        if (zoneCtx && data.zones) {
            new Chart(zoneCtx, {
                type: 'bar',
                data: {
                    labels: data.zones.labels,
                    datasets: [{
                        label: 'Defects in Zone',
                        data: data.zones.counts,
                        backgroundColor: '#6366f1',
                        borderRadius: 6
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { beginAtZero: true, ticks: { precision: 0 } }
                    }
                }
            });
        }

    } catch (err) {
        console.error('Failed to load chart analytics data:', err);
    }
});
