/**
 * Visual charts manager using Chart.js for the Analytics Studio.
 */

class AnalyticsChartsManager {
    constructor() {
        this.charts = {};
        this.initChartDefaults();
    }

    initChartDefaults() {
        if (typeof Chart === 'undefined') return;

        Chart.defaults.color = '#94a3b8';
        Chart.defaults.font.family = "'Plus Jakarta Sans', sans-serif";
        Chart.defaults.font.size = 11;
        Chart.defaults.plugins.legend.labels.usePointStyle = true;
        Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(10, 29, 53, 0.95)';
        Chart.defaults.plugins.tooltip.titleColor = '#ffffff';
        Chart.defaults.plugins.tooltip.bodyColor = '#cbd5e1';
        Chart.defaults.plugins.tooltip.borderColor = '#1b3a5c';
        Chart.defaults.plugins.tooltip.borderWidth = 1;
        Chart.defaults.plugins.tooltip.padding = 10;
        Chart.defaults.plugins.tooltip.cornerRadius = 8;
    }

    destroyChart(key) {
        if (this.charts[key]) {
            this.charts[key].destroy();
            delete this.charts[key];
        }
    }

    /**
     * Render all analytics charts with data from /api/analytics
     */
    renderAll(analyticsData) {
        this.renderBusiestAirports(analyticsData.busiest_airports);
        this.renderDistanceDistribution(analyticsData.distance_distribution);
        this.renderDistanceTimeScatter(analyticsData.scatter_data);
        this.renderLongestShortest(analyticsData.longest_routes, analyticsData.shortest_routes);
    }

    /**
     * 1. Busiest Airports Horizontal Bar Chart
     */
    renderBusiestAirports(data) {
        const ctx = document.getElementById('chart-busiest-airports');
        if (!ctx) return;
        this.destroyChart('busiest');

        const labels = data.map(item => `${item.code} (${item.city})`);
        const values = data.map(item => item.connections);

        this.charts['busiest'] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Connected Routes',
                    data: values,
                    backgroundColor: 'rgba(0, 201, 141, 0.75)',
                    hoverBackgroundColor: 'rgba(0, 201, 141, 1)',
                    borderColor: '#00c98d',
                    borderWidth: 1.5,
                    borderRadius: 6,
                }],
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (context) => ` ${context.raw} connected routes`,
                        },
                    },
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(27, 58, 92, 0.4)' },
                        ticks: { stepSize: 1 },
                        title: { display: true, text: 'Number of Routes (Degree)', color: '#64748b' },
                    },
                    y: {
                        grid: { display: false },
                    },
                },
            },
        });
    }

    /**
     * 2. Route Distance Distribution Histogram
     */
    renderDistanceDistribution(data) {
        const ctx = document.getElementById('chart-distance-dist');
        if (!ctx) return;
        this.destroyChart('distribution');

        this.charts['distribution'] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Routes Count',
                    data: data.counts,
                    backgroundColor: 'rgba(25, 181, 230, 0.75)',
                    hoverBackgroundColor: 'rgba(25, 181, 230, 1)',
                    borderColor: '#19b5e6',
                    borderWidth: 1.5,
                    borderRadius: 6,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (context) => ` ${context.raw} routes in range`,
                        },
                    },
                },
                scales: {
                    x: {
                        grid: { display: false },
                        title: { display: true, text: 'Distance Range (km)', color: '#64748b' },
                    },
                    y: {
                        grid: { color: 'rgba(27, 58, 92, 0.4)' },
                        ticks: { stepSize: 1 },
                        title: { display: true, text: 'Number of Routes', color: '#64748b' },
                    },
                },
            },
        });
    }

    /**
     * 3. Flight Distance vs Travel Time Scatter Plot
     */
    renderDistanceTimeScatter(data) {
        const ctx = document.getElementById('chart-scatter');
        if (!ctx) return;
        this.destroyChart('scatter');

        this.charts['scatter'] = new Chart(ctx, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: 'Flight Route Leg',
                    data: data,
                    backgroundColor: 'rgba(165, 107, 255, 0.85)',
                    borderColor: '#a56bff',
                    borderWidth: 1,
                    pointRadius: 6,
                    pointHoverRadius: 9,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const pt = context.raw;
                                return ` ${pt.label}: ${pt.x.toLocaleString()} km, ${pt.y} min`;
                            },
                        },
                    },
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(27, 58, 92, 0.4)' },
                        title: { display: true, text: 'Distance (km)', color: '#64748b' },
                    },
                    y: {
                        grid: { color: 'rgba(27, 58, 92, 0.4)' },
                        title: { display: true, text: 'Travel Time (minutes)', color: '#64748b' },
                    },
                },
            },
        });
    }

    /**
     * 4. Comparison of Longest vs Shortest Flights
     */
    renderLongestShortest(longest, shortest) {
        const ctx = document.getElementById('chart-longest-shortest');
        if (!ctx) return;
        this.destroyChart('ranking');

        const combined = [
            ...longest.map(r => ({ ...r, category: 'Longest' })),
            ...shortest.map(r => ({ ...r, category: 'Shortest' })),
        ];

        const labels = combined.map(r => r.route);
        const values = combined.map(r => r.distance_km);
        const colors = combined.map(r => r.category === 'Longest' ? 'rgba(30, 144, 255, 0.8)' : 'rgba(245, 158, 11, 0.8)');

        this.charts['ranking'] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Distance (km)',
                    data: values,
                    backgroundColor: colors,
                    borderRadius: 6,
                    borderWidth: 1,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (context) => ` Distance: ${context.raw.toLocaleString()} km`,
                        },
                    },
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { maxRotation: 45, minRotation: 45 },
                    },
                    y: {
                        grid: { color: 'rgba(27, 58, 92, 0.4)' },
                        title: { display: true, text: 'Distance (km)', color: '#64748b' },
                    },
                },
            },
        });
    }
}
