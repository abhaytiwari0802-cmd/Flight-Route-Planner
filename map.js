/**
 * Interactive Leaflet.js map controller for flight route visualization and network topology.
 */

class FlightMapController {
    constructor(containerId) {
        this.containerId = containerId;
        this.map = null;
        this.routeLayerGroup = null;
        this.networkLayerGroup = null;
        this.allAirportsLayerGroup = null;
        this.planeMarker = null;
        this.planeAnimationId = null;
        this.onAirportSelect = null; // Callback when an airport is clicked on map
    }

    init() {
        if (this.map) return;

        // Initialize Leaflet map centered over Continental United States
        this.map = L.map(this.containerId, {
            center: [39.5, -98.35],
            zoom: 4,
            minZoom: 2,
            maxZoom: 14,
            zoomControl: false,
        });

        // Add Zoom Control to top-right
        L.control.zoom({ position: 'topright' }).addTo(this.map);

        // CartoDB Dark Matter tile layer for cockpit night aesthetic
        const darkTiles = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
            subdomains: 'abcd',
            maxZoom: 19,
        });

        // Fallback OpenStreetMap standard tile layer
        darkTiles.addTo(this.map);

        // Layer groups
        this.routeLayerGroup = L.layerGroup().addTo(this.map);
        this.networkLayerGroup = L.layerGroup().addTo(this.map);
        this.allAirportsLayerGroup = L.layerGroup().addTo(this.map);

        // Fix leaflet container size on resize
        setTimeout(() => {
            this.map.invalidateSize();
        }, 200);
    }

    invalidateSize() {
        if (this.map) {
            setTimeout(() => {
                this.map.invalidateSize();
            }, 100);
        }
    }

    clearRoute() {
        if (this.routeLayerGroup) {
            this.routeLayerGroup.clearLayers();
        }
        if (this.planeAnimationId) {
            cancelAnimationFrame(this.planeAnimationId);
            this.planeAnimationId = null;
        }
        if (this.planeMarker) {
            this.planeMarker.remove();
            this.planeMarker = null;
        }
    }

    clearNetwork() {
        if (this.networkLayerGroup) {
            this.networkLayerGroup.clearLayers();
        }
    }

    /**
     * Render the active flight route with curved arcs, layovers, and airport markers.
     */
    renderFlightRoute(routeOption) {
        if (!this.map || !routeOption) return;

        this.clearRoute();
        const legs = routeOption.legs;
        if (!legs || legs.length === 0) return;

        const boundsCoords = [];

        // 1. Draw each leg's curved geodesic trajectory
        legs.forEach((leg, index) => {
            const arcCoords = leg.arc_coordinates;
            boundsCoords.push(...arcCoords);

            // Background glow line
            L.polyline(arcCoords, {
                color: '#00c98d',
                weight: 6,
                opacity: 0.35,
                lineCap: 'round',
                lineJoin: 'round',
            }).addTo(this.routeLayerGroup);

            // Core sharp flight path line
            const coreLine = L.polyline(arcCoords, {
                color: '#00c98d',
                weight: 2.5,
                opacity: 0.95,
                lineCap: 'round',
                lineJoin: 'round',
            }).addTo(this.routeLayerGroup);

            // Animated flow line on top
            const flowLine = L.polyline(arcCoords, {
                color: '#ffffff',
                weight: 2,
                opacity: 0.8,
                dashArray: '6, 12',
                className: 'animated-flight-line',
            }).addTo(this.routeLayerGroup);

            // Leg hover popup
            const popupContent = `
                <div class="p-2 text-xs">
                    <div class="font-bold text-emerald-400 text-sm mb-1">Leg ${leg.leg_number}: ${leg.source} ➔ ${leg.destination}</div>
                    <div class="text-slate-300">${leg.source_city} to ${leg.destination_city}</div>
                    <div class="mt-1 flex items-center gap-3 text-slate-400 font-mono">
                        <span>✈ ${leg.distance_km.toLocaleString()} km</span>
                        <span>⏱ ${leg.formatted_duration}</span>
                    </div>
                </div>
            `;
            coreLine.bindPopup(popupContent);
        });

        // 2. Add Airport Markers (Origin, Destination, Layovers)
        const pathCodes = routeOption.path;
        const originCode = pathCodes[0];
        const destCode = pathCodes[pathCodes.length - 1];

        pathCodes.forEach((code, idx) => {
            let lat, lon, city = '', name = '';

            // Find coords and details from legs
            if (idx === 0) {
                lat = legs[0].start_coords[0];
                lon = legs[0].start_coords[1];
                city = legs[0].source_city;
                name = legs[0].source_name;
            } else {
                lat = legs[idx - 1].end_coords[0];
                lon = legs[idx - 1].end_coords[1];
                city = legs[idx - 1].destination_city;
                name = legs[idx - 1].destination_name;
            }

            let markerHtml = '';
            let roleText = '';
            let roleClass = '';

            if (idx === 0) {
                markerHtml = `<div class="radar-pulse-origin"></div>`;
                roleText = 'Origin Airport';
                roleClass = 'text-cyan-400';
            } else if (idx === pathCodes.length - 1) {
                markerHtml = `<div class="radar-pulse-dest"></div>`;
                roleText = 'Destination Airport';
                roleClass = 'text-emerald-400';
            } else {
                markerHtml = `<div class="radar-pulse-layover"></div>`;
                roleText = `Layover #${idx}`;
                roleClass = 'text-amber-400';
            }

            const customIcon = L.divIcon({
                className: 'airport-marker-icon',
                html: markerHtml,
                iconSize: [16, 16],
                iconAnchor: [8, 8],
            });

            const marker = L.marker([lat, lon], { icon: customIcon }).addTo(this.routeLayerGroup);

            // Label tooltip
            marker.bindTooltip(code, {
                permanent: true,
                direction: 'top',
                offset: [0, -10],
                className: 'map-airport-label',
            });

            // Detailed popup
            marker.bindPopup(`
                <div class="p-2 text-xs">
                    <div class="font-bold text-sm ${roleClass}">${code} &bull; ${roleText}</div>
                    <div class="font-semibold text-slate-100 text-sm mt-0.5">${name}</div>
                    <div class="text-slate-400 mt-0.5">${city}</div>
                </div>
            `);
        });

        // 3. Fit bounds with smooth animation
        if (boundsCoords.length > 0) {
            this.map.fitBounds(boundsCoords, {
                padding: [60, 60],
                maxZoom: 7,
                animate: true,
                duration: 1.2,
            });
        }

        // 4. Start animated plane icon along the path
        this.animatePlaneAlongPath(routeOption.full_arc_coordinates);
    }

    /**
     * Animate a small airplane icon moving continuously along the curved trajectory.
     */
    animatePlaneAlongPath(arcPoints) {
        if (!arcPoints || arcPoints.length < 2) return;

        if (this.planeMarker) {
            this.planeMarker.remove();
        }

        const planeIcon = L.divIcon({
            className: 'plane-flight-icon',
            html: `
                <div style="transform: rotate(0deg); transition: transform 0.1s; filter: drop-shadow(0 0 6px #00c98d);">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="#00c98d" stroke="#ffffff" stroke-width="1.2">
                        <path d="M21 16v-2l-8-5V3.5c0-.83-.67-1.5-1.5-1.5S10 2.67 10 3.5V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z"/>
                    </svg>
                </div>
            `,
            iconSize: [22, 22],
            iconAnchor: [11, 11],
        });

        this.planeMarker = L.marker(arcPoints[0], { icon: planeIcon }).addTo(this.routeLayerGroup);

        let currentIndex = 0;
        const totalPoints = arcPoints.length;
        const speed = 1; // Step increment per frame

        const step = () => {
            currentIndex = (currentIndex + speed) % totalPoints;
            const currentPoint = arcPoints[currentIndex];
            const nextPoint = arcPoints[(currentIndex + 1) % totalPoints];

            this.planeMarker.setLatLng(currentPoint);

            // Calculate bearing for rotation
            const dLat = nextPoint[0] - currentPoint[0];
            const dLon = nextPoint[1] - currentPoint[1];
            const angle = Math.atan2(dLon, dLat) * (180 / Math.PI);

            const el = this.planeMarker.getElement();
            if (el) {
                const inner = el.querySelector('div');
                if (inner) {
                    inner.style.transform = `rotate(${angle}deg)`;
                }
            }

            this.planeAnimationId = requestAnimationFrame(step);
        };

        this.planeAnimationId = requestAnimationFrame(step);
    }

    /**
     * Render the entire airport network (all nodes and edges) for the Network Explorer tab.
     */
    renderNetwork(networkData) {
        if (!this.map || !networkData) return;

        this.clearNetwork();
        this.clearRoute();

        const { nodes, edges } = networkData;
        const allPoints = [];

        // 1. Draw all route connection lines
        edges.forEach((edge) => {
            const p1 = edge.source_coords;
            const p2 = edge.destination_coords;
            if (!p1 || !p2 || p1.length < 2 || p2.length < 2) return;

            const line = L.polyline([p1, p2], {
                color: '#284665',
                weight: 1.4,
                opacity: 0.65,
                smoothFactor: 1,
            }).addTo(this.networkLayerGroup);

            line.on('mouseover', function () {
                this.setStyle({ color: '#19b5e6', weight: 2.8, opacity: 1 });
            });

            line.on('mouseout', function () {
                this.setStyle({ color: '#284665', weight: 1.4, opacity: 0.65 });
            });

            line.bindPopup(`
                <div class="p-2 text-xs">
                    <div class="font-bold text-cyan-400 text-sm">${edge.source} ⇄ ${edge.destination}</div>
                    <div class="mt-1 font-mono text-slate-300">Distance: ${edge.distance_km.toLocaleString()} km</div>
                    ${edge.travel_time_min ? `<div class="font-mono text-slate-400">Duration: ${edge.travel_time_min} min</div>` : ''}
                </div>
            `);
        });

        // 2. Draw all airport nodes
        nodes.forEach((node) => {
            const lat = node.lat;
            const lon = node.lon;
            allPoints.push([lat, lon]);

            const markerHtml = `
                <div class="flex items-center justify-center w-5 h-5 bg-slate-900 border-2 border-cyan-400 rounded-full shadow-lg shadow-cyan-500/30 hover:scale-125 transition-transform">
                    <div class="w-1.5 h-1.5 bg-cyan-300 rounded-full"></div>
                </div>
            `;

            const icon = L.divIcon({
                className: 'network-node-icon',
                html: markerHtml,
                iconSize: [20, 20],
                iconAnchor: [10, 10],
            });

            const marker = L.marker([lat, lon], { icon }).addTo(this.networkLayerGroup);

            marker.bindTooltip(node.code, {
                permanent: true,
                direction: 'top',
                offset: [0, -10],
                className: 'map-airport-label',
            });

            marker.bindPopup(`
                <div class="p-2 text-xs">
                    <div class="font-bold text-sm text-cyan-400">${node.code} &bull; ${node.city}</div>
                    <div class="font-semibold text-slate-200 text-sm mt-0.5">${node.name}</div>
                    <div class="mt-2 text-slate-400 flex items-center justify-between">
                        <span>Direct Connections:</span>
                        <span class="font-bold text-white bg-cyan-950 px-2 py-0.5 rounded border border-cyan-800">${node.connections} routes</span>
                    </div>
                    <div class="mt-3 flex gap-2">
                        <button onclick="window.selectAsOrigin('${node.code}')" class="px-2 py-1 bg-cyan-600 hover:bg-cyan-500 text-white rounded text-[10px] font-bold">Set as Origin</button>
                        <button onclick="window.selectAsDest('${node.code}')" class="px-2 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-[10px] font-bold">Set as Destination</button>
                    </div>
                </div>
            `);
        });

        // 3. Fit bounds to whole network
        if (allPoints.length > 0) {
            this.map.fitBounds(allPoints, { padding: [50, 50], maxZoom: 6 });
        }
    }
}
