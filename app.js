/**
 * Main Application Controller for Flight Route Planner.
 */

document.addEventListener('DOMContentLoaded', () => {
    // State management
    const state = {
        airports: [],
        routes: [],
        currentRouteResult: null,
        activeTab: 'planner',
        editingAirportCode: null,
        editingRouteIndex: null,
    };

    // Initialize Maps & Charts
    const plannerMap = new FlightMapController('map-container');
    plannerMap.init();

    const networkMap = new FlightMapController('network-map-container');

    const chartsManager = new AnalyticsChartsManager();

    // DOM Elements
    const originInput = document.getElementById('origin-input');
    const destInput = document.getElementById('dest-input');
    const originSuggestions = document.getElementById('origin-suggestions');
    const destSuggestions = document.getElementById('dest-suggestions');
    const swapBtn = document.getElementById('swap-airports-btn');
    const planForm = document.getElementById('route-plan-form');
    const planSubmitBtn = document.getElementById('plan-submit-btn');

    // Overview Elements
    const statDistance = document.getElementById('stat-total-distance');
    const statDuration = document.getElementById('stat-total-duration');
    const statLayovers = document.getElementById('stat-total-layovers');
    const statLegsCount = document.getElementById('stat-total-legs');
    const itineraryContainer = document.getElementById('itinerary-legs-container');
    const alternativesContainer = document.getElementById('alternatives-list-container');
    const routeSummaryCard = document.getElementById('route-summary-card');

    // Global helper to select airports from Leaflet map popup buttons
    window.selectAsOrigin = (code) => {
        originInput.value = code;
        switchTab('planner');
        showToast(`Set ${code} as origin`, 'info');
    };

    window.selectAsDest = (code) => {
        destInput.value = code;
        switchTab('planner');
        showToast(`Set ${code} as destination`, 'info');
    };

    // ==========================================
    // 1. Toast Notification Utility
    // ==========================================
    function showToast(message, type = 'info', duration = 3500) {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast flex items-start gap-3 p-3.5 rounded-xl border shadow-xl backdrop-blur-md text-xs font-medium text-white transition-all`;

        let icon = '';
        let borderClass = '';
        let bgClass = '';

        switch (type) {
            case 'success':
                bgClass = 'bg-emerald-950/90';
                borderClass = 'border-emerald-600/60 text-emerald-300';
                icon = `<svg class="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>`;
                break;
            case 'error':
                bgClass = 'bg-rose-950/90';
                borderClass = 'border-rose-600/60 text-rose-300';
                icon = `<svg class="w-4 h-4 text-rose-400 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>`;
                break;
            case 'warning':
                bgClass = 'bg-amber-950/90';
                borderClass = 'border-amber-600/60 text-amber-300';
                icon = `<svg class="w-4 h-4 text-amber-400 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>`;
                break;
            default:
                bgClass = 'bg-slate-900/90';
                borderClass = 'border-cyan-600/60 text-cyan-300';
                icon = `<svg class="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>`;
        }

        toast.className += ` ${bgClass} ${borderClass}`;
        toast.innerHTML = `
            ${icon}
            <div class="flex-1">${message}</div>
            <button class="text-slate-400 hover:text-white shrink-0 ml-1">&times;</button>
        `;

        const closeBtn = toast.querySelector('button');
        closeBtn.onclick = () => {
            toast.classList.add('hiding');
            setTimeout(() => toast.remove(), 250);
        };

        container.appendChild(toast);

        setTimeout(() => {
            if (toast.parentElement) {
                toast.classList.add('hiding');
                setTimeout(() => toast.remove(), 250);
            }
        }, duration);
    }

    // ==========================================
    // 2. Tab Navigation
    // ==========================================
    function switchTab(tabId) {
        state.activeTab = tabId;

        // Update nav buttons
        document.querySelectorAll('.nav-tab-btn').forEach(btn => {
            const target = btn.getAttribute('data-tab');
            if (target === tabId) {
                btn.classList.add('bg-cyan-500/10', 'text-cyan-400', 'border-cyan-500/50');
                btn.classList.remove('text-slate-400', 'border-transparent');
            } else {
                btn.classList.remove('bg-cyan-500/10', 'text-cyan-400', 'border-cyan-500/50');
                btn.classList.add('text-slate-400', 'border-transparent');
            }
        });

        // Hide all tab panes
        document.querySelectorAll('.tab-content-pane').forEach(pane => {
            pane.classList.add('hidden');
        });

        // Show active tab pane
        const activePane = document.getElementById(`pane-${tabId}`);
        if (activePane) {
            activePane.classList.remove('hidden');
        }

        // Action per tab
        if (tabId === 'planner') {
            plannerMap.invalidateSize();
        } else if (tabId === 'network') {
            networkMap.init();
            networkMap.invalidateSize();
            loadNetworkTopology();
        } else if (tabId === 'analytics') {
            loadAnalyticsData();
        } else if (tabId === 'airports') {
            renderAirportsTable();
        } else if (tabId === 'routes') {
            renderRoutesTable();
        }
    }

    document.querySelectorAll('.nav-tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.getAttribute('data-tab');
            switchTab(tabId);
        });
    });

    // ==========================================
    // 3. Search Autocomplete Setup
    // ==========================================
    function setupAutocomplete(inputEl, dropdownEl, onSelect) {
        let debounceTimer;

        inputEl.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            const query = inputEl.value.trim();

            if (!query) {
                dropdownEl.classList.add('hidden');
                return;
            }

            debounceTimer = setTimeout(() => {
                const matches = state.airports.filter(a =>
                    a.code.includes(query.toUpperCase()) ||
                    a.city.toUpperCase().includes(query.toUpperCase()) ||
                    a.name.toUpperCase().includes(query.toUpperCase())
                ).slice(0, 7);

                if (matches.length === 0) {
                    dropdownEl.innerHTML = `
                        <div class="px-3.5 py-2.5 text-xs text-slate-500 italic">No matching airports found</div>
                    `;
                } else {
                    dropdownEl.innerHTML = matches.map(a => `
                        <div class="suggestion-item px-3.5 py-2.5 hover:bg-slate-800/80 cursor-pointer transition-colors border-b border-slate-800/40 last:border-0 flex items-center justify-between" data-code="${a.code}">
                            <div>
                                <span class="font-bold font-mono text-cyan-400 text-xs">${a.code}</span>
                                <span class="text-slate-200 text-xs ml-2 font-medium">${a.city}</span>
                                <div class="text-[10px] text-slate-400 truncate max-w-[210px]">${a.name}</div>
                            </div>
                            <span class="text-[10px] text-slate-500 font-mono">${a.routes_count} routes</span>
                        </div>
                    `).join('');

                    dropdownEl.querySelectorAll('.suggestion-item').forEach(item => {
                        item.addEventListener('click', () => {
                            const code = item.getAttribute('data-code');
                            inputEl.value = code;
                            dropdownEl.classList.add('hidden');
                            if (onSelect) onSelect(code);
                        });
                    });
                }

                dropdownEl.classList.remove('hidden');
            }, 150);
        });

        // Hide when clicking outside
        document.addEventListener('click', (e) => {
            if (!inputEl.contains(e.target) && !dropdownEl.contains(e.target)) {
                dropdownEl.classList.add('hidden');
            }
        });

        inputEl.addEventListener('focus', () => {
            if (inputEl.value.trim()) {
                inputEl.dispatchEvent(new Event('input'));
            }
        });
    }

    setupAutocomplete(originInput, originSuggestions);
    setupAutocomplete(destInput, destSuggestions);

    // Swap Airports button
    swapBtn.addEventListener('click', () => {
        const temp = originInput.value;
        originInput.value = destInput.value;
        destInput.value = temp;

        swapBtn.classList.add('rotate-180');
        setTimeout(() => swapBtn.classList.remove('rotate-180'), 300);

        if (originInput.value && destInput.value) {
            executeRoutePlanning();
        }
    });

    // Quick route selection chips
    document.querySelectorAll('.quick-route-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            const from = chip.getAttribute('data-from');
            const to = chip.getAttribute('data-to');
            originInput.value = from;
            destInput.value = to;
            executeRoutePlanning();
        });
    });

    // ==========================================
    // 4. Route Planning Execution
    // ==========================================
    planForm.addEventListener('submit', (e) => {
        e.preventDefault();
        executeRoutePlanning();
    });

    async function executeRoutePlanning() {
        const source = originInput.value.trim().toUpperCase();
        const destination = destInput.value.trim().toUpperCase();

        if (!source || !destination) {
            showToast('Please select both Origin and Destination airports.', 'warning');
            return;
        }

        if (source === destination) {
            showToast('Origin and Destination must be different airports.', 'warning');
            return;
        }

        // Loading state
        planSubmitBtn.disabled = true;
        planSubmitBtn.innerHTML = `
            <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-slate-900 inline-block" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
            </svg>
            Calculating Route...
        `;

        try {
            const result = await API.planRoute(source, destination, 3);
            state.currentRouteResult = result;

            if (!result.success || !result.best_route) {
                showToast(result.message || 'No route found.', 'error');
                return;
            }

            renderRouteOverview(result.best_route, result);
            plannerMap.renderFlightRoute(result.best_route);
            showToast(`Optimal route found: ${result.best_route.path.join(' ➔ ')} (${result.best_route.total_distance_km.toLocaleString()} km)`, 'success');
        } catch (error) {
            showToast(error.message || 'Failed to compute route.', 'error');
        } finally {
            planSubmitBtn.disabled = false;
            planSubmitBtn.innerHTML = `
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                </svg>
                Find Optimal Route
            `;
        }
    }

    // Render summary stat cards, legs, and alternatives
    function renderRouteOverview(routeOption, fullResult) {
        routeSummaryCard.classList.remove('hidden');

        // Total distance and duration
        statDistance.innerText = `${routeOption.total_distance_km.toLocaleString()} km`;
        statDuration.innerText = routeOption.formatted_duration;
        statLegsCount.innerText = `${routeOption.legs.length} Leg${routeOption.legs.length > 1 ? 's' : ''}`;

        // Layovers badge
        if (routeOption.is_direct) {
            statLayovers.innerHTML = `
                <span class="inline-flex items-center px-2 py-0.5 rounded text-emerald-400 bg-emerald-950/80 border border-emerald-800 text-[11px] font-bold">
                    ✓ Direct Flight
                </span>
            `;
        } else {
            statLayovers.innerHTML = `
                <span class="inline-flex items-center px-2 py-0.5 rounded text-amber-400 bg-amber-950/80 border border-amber-800 text-[11px] font-bold">
                    ${routeOption.layover_count} Stop (${routeOption.layovers.join(', ')})
                </span>
            `;
        }

        // Render Legs Breakdown
        itineraryContainer.innerHTML = routeOption.legs.map(leg => `
            <div class="glass-panel-subtle p-3.5 rounded-xl border border-slate-800/80 hover:border-slate-700 transition-all">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-[10px] uppercase tracking-wider font-bold text-cyan-400">Flight Leg ${leg.leg_number}</span>
                    <span class="text-xs font-mono font-bold text-emerald-400">${leg.distance_km.toLocaleString()} km</span>
                </div>
                <div class="flex items-center justify-between">
                    <div class="flex-1">
                        <div class="text-sm font-bold text-white flex items-center gap-1.5 font-mono">
                            <span>${leg.source}</span>
                            <span class="text-slate-500 font-sans">➔</span>
                            <span>${leg.destination}</span>
                        </div>
                        <div class="text-[11px] text-slate-400 truncate mt-0.5">
                            ${leg.source_city} to ${leg.destination_city}
                        </div>
                    </div>
                    <div class="text-right">
                        <div class="text-xs font-mono text-slate-300">⏱ ${leg.formatted_duration}</div>
                    </div>
                </div>
            </div>
        `).join('');

        // Render Alternative Routes cards
        const allRoutes = [routeOption, ...(fullResult.alternative_routes || [])];
        if (allRoutes.length > 1) {
            alternativesContainer.innerHTML = allRoutes.map((opt, idx) => {
                const isSelected = opt.rank === routeOption.rank;
                return `
                    <div class="alternative-card p-3 rounded-xl border cursor-pointer transition-all ${
                        isSelected
                            ? 'bg-emerald-950/40 border-emerald-500/80 ring-1 ring-emerald-500/40'
                            : 'glass-panel-subtle border-slate-800 hover:border-slate-700'
                    }" data-rank="${opt.rank}">
                        <div class="flex items-center justify-between mb-1.5">
                            <span class="text-[10px] font-bold uppercase tracking-wider ${isSelected ? 'text-emerald-400' : 'text-slate-400'}">
                                ${opt.badge}
                            </span>
                            <span class="text-xs font-mono font-bold ${isSelected ? 'text-emerald-300' : 'text-slate-200'}">
                                ${opt.total_distance_km.toLocaleString()} km
                            </span>
                        </div>
                        <div class="text-xs text-slate-200 font-mono font-semibold">
                            ${opt.path.join(' ➔ ')}
                        </div>
                        <div class="mt-1 flex items-center justify-between text-[11px] text-slate-400">
                            <span>${opt.is_direct ? 'Non-stop' : `${opt.layover_count} layover(s)`}</span>
                            <span>⏱ ${opt.formatted_duration}</span>
                        </div>
                    </div>
                `;
            }).join('');

            alternativesContainer.querySelectorAll('.alternative-card').forEach(card => {
                card.addEventListener('click', () => {
                    const rank = parseInt(card.getAttribute('data-rank'));
                    const selectedOpt = allRoutes.find(r => r.rank === rank);
                    if (selectedOpt) {
                        renderRouteOverview(selectedOpt, fullResult);
                        plannerMap.renderFlightRoute(selectedOpt);
                    }
                });
            });
        } else {
            alternativesContainer.innerHTML = `
                <div class="text-xs text-slate-500 italic p-2">Only 1 unique connection route exists between these airports.</div>
            `;
        }
    }

    // ==========================================
    // 5. Network Explorer Topology Loader
    // ==========================================
    async function loadNetworkTopology() {
        try {
            const data = await API.getNetworkGraph();
            networkMap.renderNetwork(data);

            const badge = document.getElementById('network-stats-badge');
            if (badge) {
                badge.innerText = `${data.total_nodes} Airports · ${data.total_edges} Routes`;
            }
        } catch (error) {
            showToast('Failed to load network topology: ' + error.message, 'error');
        }
    }

    // ==========================================
    // 6. Analytics Studio Loader
    // ==========================================
    async function loadAnalyticsData() {
        try {
            const summary = await API.getAnalytics();

            // Populate KPI cards
            document.getElementById('kpi-total-airports').innerText = summary.total_airports;
            document.getElementById('kpi-total-routes').innerText = summary.total_routes;
            document.getElementById('kpi-avg-distance').innerText = `${summary.average_leg_km.toLocaleString()} km`;
            document.getElementById('kpi-avg-duration').innerText = `${summary.average_duration_min} min`;
            document.getElementById('kpi-shortest-leg').innerText = `${summary.shortest_leg_km.toLocaleString()} km`;
            document.getElementById('kpi-longest-leg').innerText = `${summary.longest_leg_km.toLocaleString()} km`;
            document.getElementById('kpi-network-density').innerText = summary.network_density;
            document.getElementById('kpi-network-diameter').innerText = summary.network_diameter ? `${summary.network_diameter} hops` : 'N/A';

            // Render Charts
            chartsManager.renderAll(summary);
        } catch (error) {
            showToast('Failed to load analytics: ' + error.message, 'error');
        }
    }

    // ==========================================
    // 7. Airports Directory & CRUD
    // ==========================================
    const airportSearchInput = document.getElementById('airport-table-search');
    const airportsTableBody = document.getElementById('airports-table-body');
    const airportModal = document.getElementById('airport-modal');
    const airportForm = document.getElementById('airport-form');

    function renderAirportsTable() {
        const query = (airportSearchInput ? airportSearchInput.value : '').trim().toUpperCase();
        const filtered = state.airports.filter(a =>
            !query ||
            a.code.includes(query) ||
            a.city.toUpperCase().includes(query) ||
            a.name.toUpperCase().includes(query)
        );

        airportsTableBody.innerHTML = filtered.map(a => `
            <tr class="border-b border-slate-800/60 hover:bg-slate-800/30 transition-colors text-xs">
                <td class="px-4 py-3 font-mono font-bold text-cyan-400">${a.code}</td>
                <td class="px-4 py-3 font-medium text-slate-100">${a.name}</td>
                <td class="px-4 py-3 text-slate-300">${a.city}</td>
                <td class="px-4 py-3 font-mono text-slate-400">${a.lat.toFixed(4)}, ${a.lon.toFixed(4)}</td>
                <td class="px-4 py-3">
                    <span class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-slate-800 text-slate-200 border border-slate-700">
                        ${a.routes_count}
                    </span>
                </td>
                <td class="px-4 py-3 text-right whitespace-nowrap">
                    <button class="edit-airport-btn text-cyan-400 hover:text-cyan-300 font-medium mr-3" data-code="${a.code}">Edit</button>
                    <button class="delete-airport-btn text-rose-400 hover:text-rose-300 font-medium" data-code="${a.code}">Delete</button>
                </td>
            </tr>
        `).join('');

        // Attach action handlers
        airportsTableBody.querySelectorAll('.edit-airport-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const code = btn.getAttribute('data-code');
                openEditAirportModal(code);
            });
        });

        airportsTableBody.querySelectorAll('.delete-airport-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const code = btn.getAttribute('data-code');
                handleDeleteAirport(code);
            });
        });
    }

    if (airportSearchInput) {
        airportSearchInput.addEventListener('input', renderAirportsTable);
    }

    // Add Airport button
    document.getElementById('open-add-airport-modal-btn')?.addEventListener('click', () => {
        state.editingAirportCode = null;
        document.getElementById('airport-modal-title').innerText = 'Add New Airport';
        document.getElementById('modal-airport-code').value = '';
        document.getElementById('modal-airport-code').disabled = false;
        document.getElementById('modal-airport-name').value = '';
        document.getElementById('modal-airport-city').value = '';
        airportModal.classList.remove('hidden');
    });

    function openEditAirportModal(code) {
        const airport = state.airports.find(a => a.code === code);
        if (!airport) return;

        state.editingAirportCode = code;
        document.getElementById('airport-modal-title').innerText = `Edit Airport (${code})`;
        document.getElementById('modal-airport-code').value = airport.code;
        document.getElementById('modal-airport-code').disabled = true;
        document.getElementById('modal-airport-name').value = airport.name;
        document.getElementById('modal-airport-city').value = airport.city;
        airportModal.classList.remove('hidden');
    }

    document.querySelectorAll('.close-airport-modal-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            airportModal.classList.add('hidden');
        });
    });

    airportForm?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const code = document.getElementById('modal-airport-code').value.trim().toUpperCase();
        const name = document.getElementById('modal-airport-name').value.trim();
        const city = document.getElementById('modal-airport-city').value.trim();

        try {
            if (state.editingAirportCode) {
                await API.updateAirport(state.editingAirportCode, { name, city });
                showToast(`Airport ${state.editingAirportCode} updated successfully.`, 'success');
            } else {
                await API.addAirport({ code, name, city });
                showToast(`Airport ${code} added to airports.csv.`, 'success');
            }
            airportModal.classList.add('hidden');
            await reloadData();
            renderAirportsTable();
        } catch (error) {
            showToast(error.message, 'error');
        }
    });

    async function handleDeleteAirport(code) {
        if (!confirm(`Are you sure you want to delete airport ${code} and all its connected routes? This directly modifies airports.csv and routes.csv.`)) {
            return;
        }

        try {
            await API.deleteAirport(code);
            showToast(`Airport ${code} deleted from airports.csv.`, 'success');
            await reloadData();
            renderAirportsTable();
        } catch (error) {
            showToast(error.message, 'error');
        }
    }

    // ==========================================
    // 8. Routes Connections Directory & CRUD
    // ==========================================
    const routeSearchInput = document.getElementById('route-table-search');
    const routesTableBody = document.getElementById('routes-table-body');
    const routeModal = document.getElementById('route-modal');
    const routeForm = document.getElementById('route-form');

    function renderRoutesTable() {
        const query = (routeSearchInput ? routeSearchInput.value : '').trim().toUpperCase();
        const filtered = state.routes.filter(r =>
            !query ||
            r.source.includes(query) ||
            r.destination.includes(query) ||
            r.source_city.toUpperCase().includes(query) ||
            r.destination_city.toUpperCase().includes(query)
        );

        routesTableBody.innerHTML = filtered.map(r => `
            <tr class="border-b border-slate-800/60 hover:bg-slate-800/30 transition-colors text-xs">
                <td class="px-4 py-3 font-mono text-slate-500">#${r.index}</td>
                <td class="px-4 py-3 font-mono font-bold text-cyan-400">
                    ${r.source} <span class="text-slate-500 font-sans">➔</span> ${r.destination}
                </td>
                <td class="px-4 py-3 text-slate-300">${r.source_city} to ${r.destination_city}</td>
                <td class="px-4 py-3 font-mono font-bold text-emerald-400">${r.distance_km.toLocaleString()} km</td>
                <td class="px-4 py-3 font-mono text-slate-400">${r.travel_time_min ? `${r.travel_time_min} min` : '—'}</td>
                <td class="px-4 py-3 text-right whitespace-nowrap">
                    <button class="edit-route-btn text-cyan-400 hover:text-cyan-300 font-medium mr-3" data-index="${r.index}">Edit</button>
                    <button class="delete-route-btn text-rose-400 hover:text-rose-300 font-medium" data-index="${r.index}">Delete</button>
                </td>
            </tr>
        `).join('');

        routesTableBody.querySelectorAll('.edit-route-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const index = parseInt(btn.getAttribute('data-index'));
                openEditRouteModal(index);
            });
        });

        routesTableBody.querySelectorAll('.delete-route-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const index = parseInt(btn.getAttribute('data-index'));
                handleDeleteRoute(index);
            });
        });
    }

    if (routeSearchInput) {
        routeSearchInput.addEventListener('input', renderRoutesTable);
    }

    // Populate dropdowns in Add Route modal
    function populateRouteModalSelects() {
        const srcSelect = document.getElementById('modal-route-source');
        const dstSelect = document.getElementById('modal-route-destination');

        const optionsHtml = state.airports.map(a => `
            <option value="${a.code}">${a.code} — ${a.city} (${a.name})</option>
        `).join('');

        srcSelect.innerHTML = `<option value="">Select Origin</option>` + optionsHtml;
        dstSelect.innerHTML = `<option value="">Select Destination</option>` + optionsHtml;
    }

    document.getElementById('open-add-route-modal-btn')?.addEventListener('click', () => {
        state.editingRouteIndex = null;
        populateRouteModalSelects();
        document.getElementById('route-modal-title').innerText = 'Add Flight Route Connection';
        document.getElementById('modal-route-source').disabled = false;
        document.getElementById('modal-route-destination').disabled = false;
        document.getElementById('modal-route-distance').value = '';
        document.getElementById('modal-route-time').value = '';
        routeModal.classList.remove('hidden');
    });

    function openEditRouteModal(index) {
        const route = state.routes.find(r => r.index === index);
        if (!route) return;

        state.editingRouteIndex = index;
        populateRouteModalSelects();
        document.getElementById('route-modal-title').innerText = `Edit Route Connection (${route.source} ➔ ${route.destination})`;
        document.getElementById('modal-route-source').value = route.source;
        document.getElementById('modal-route-destination').value = route.destination;
        document.getElementById('modal-route-source').disabled = true;
        document.getElementById('modal-route-destination').disabled = true;
        document.getElementById('modal-route-distance').value = route.distance_km;
        document.getElementById('modal-route-time').value = route.travel_time_min || '';
        routeModal.classList.remove('hidden');
    }

    document.querySelectorAll('.close-route-modal-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            routeModal.classList.add('hidden');
        });
    });

    routeForm?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const source = document.getElementById('modal-route-source').value.trim();
        const destination = document.getElementById('modal-route-destination').value.trim();
        const distance_km = parseFloat(document.getElementById('modal-route-distance').value);
        const timeVal = document.getElementById('modal-route-time').value.trim();
        const travel_time_min = timeVal ? parseFloat(timeVal) : null;

        try {
            if (state.editingRouteIndex !== null) {
                await API.updateRoute(state.editingRouteIndex, { distance_km, travel_time_min });
                showToast(`Route #${state.editingRouteIndex} updated successfully.`, 'success');
            } else {
                await API.addRoute({ source, destination, distance_km, travel_time_min });
                showToast(`Route connection ${source} ➔ ${destination} added to routes.csv.`, 'success');
            }
            routeModal.classList.add('hidden');
            await reloadData();
            renderRoutesTable();
        } catch (error) {
            showToast(error.message, 'error');
        }
    });

    async function handleDeleteRoute(index) {
        if (!confirm(`Are you sure you want to delete route record #${index}? This directly modifies routes.csv.`)) {
            return;
        }

        try {
            await API.deleteRoute(index);
            showToast(`Route #${index} removed from routes.csv.`, 'success');
            await reloadData();
            renderRoutesTable();
        } catch (error) {
            showToast(error.message, 'error');
        }
    }

    // ==========================================
    // 9. Initial Data Loading & Bootstrap
    // ==========================================
    async function reloadData() {
        try {
            const [airports, routes] = await Promise.all([
                API.getAirports(),
                API.getRoutes(),
            ]);
            state.airports = airports;
            state.routes = routes;

            // Update top bar live stats
            const statusEl = document.getElementById('network-quick-stats');
            if (statusEl) {
                statusEl.innerHTML = `
                    <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-800/80 border border-slate-700/60 text-slate-300 text-xs font-medium">
                        <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                        ${airports.length} Airports &bull; ${routes.length} Direct Routes
                    </span>
                `;
            }
        } catch (error) {
            showToast('Failed to load CSV data: ' + error.message, 'error');
        }
    }

    async function initApp() {
        await reloadData();

        // Default initial demonstration route (JFK to LAX)
        originInput.value = 'JFK';
        destInput.value = 'LAX';
        executeRoutePlanning();
    }

    initApp();
});
