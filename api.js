/**
 * API client module for Flight Route Planner.
 * Strictly communicates with FastAPI backend endpoints.
 */

const API = {
    // Base request helper
    async request(url, options = {}) {
        try {
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...(options.headers || {}),
                },
                ...options,
            });

            const data = await response.json();

            if (!response.ok) {
                const message = data.detail || data.message || `Request failed with status ${response.status}`;
                throw new Error(message);
            }

            return data;
        } catch (error) {
            console.error(`API Error on ${url}:`, error);
            throw error;
        }
    },

    // Airport Endpoints
    async getAirports() {
        return this.request('/api/airports');
    },

    async searchAirports(query) {
        return this.request(`/api/airports/search?q=${encodeURIComponent(query)}`);
    },

    async getAirport(code) {
        return this.request(`/api/airports/${encodeURIComponent(code)}`);
    },

    async addAirport(payload) {
        return this.request('/api/airports', {
            method: 'POST',
            body: JSON.stringify(payload),
        });
    },

    async updateAirport(code, payload) {
        return this.request(`/api/airports/${encodeURIComponent(code)}`, {
            method: 'PUT',
            body: JSON.stringify(payload),
        });
    },

    async deleteAirport(code) {
        return this.request(`/api/airports/${encodeURIComponent(code)}`, {
            method: 'DELETE',
        });
    },

    // Route Connections Endpoints
    async getRoutes() {
        return this.request('/api/routes');
    },

    async addRoute(payload) {
        return this.request('/api/routes', {
            method: 'POST',
            body: JSON.stringify(payload),
        });
    },

    async updateRoute(index, payload) {
        return this.request(`/api/routes/${index}`, {
            method: 'PUT',
            body: JSON.stringify(payload),
        });
    },

    async deleteRoute(index) {
        return this.request(`/api/routes/${index}`, {
            method: 'DELETE',
        });
    },

    // Route Planner Endpoints
    async planRoute(source, destination, maxAlternatives = 3) {
        return this.request('/api/plan', {
            method: 'POST',
            body: JSON.stringify({
                source,
                destination,
                max_alternatives: maxAlternatives,
            }),
        });
    },

    async getNetworkGraph() {
        return this.request('/api/network');
    },

    // Analytics Endpoints
    async getAnalytics() {
        return this.request('/api/analytics');
    },
};
