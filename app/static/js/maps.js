/**
 * Leaflet.js Interactive Defect Mapping System
 * Renders GPS-tagged defects with color-coded markers, popups, and filtering.
 */

let defectMap = null;
let markerLayer = null;

const DEFECT_COLORS = {
    'Pothole': '#e63946',
    'Broken Traffic Sign': '#f77f00',
    'Garbage Dump': '#2a9d8f',
    'Cracked Road': '#3a86ff',
    'Other': '#6c757d'
};

function createCustomPin(color) {
    return L.divIcon({
        className: 'custom-pin',
        html: `<div style="
            background-color: ${color};
            width: 26px;
            height: 26px;
            border-radius: 50% 50% 50% 0;
            transform: rotate(-45deg);
            border: 2px solid #ffffff;
            box-shadow: 0 2px 6px rgba(0,0,0,0.3);
            display: flex;
            align-items: center;
            justify-content: center;
        ">
            <div style="width: 8px; height: 8px; background: white; border-radius: 50%;"></div>
        </div>`,
        iconSize: [26, 26],
        iconAnchor: [13, 26],
        popupAnchor: [0, -26]
    });
}

function initDefectMap(elementId = 'defectMap', initialLat = 28.6139, initialLng = 77.2090, zoom = 12) {
    const mapContainer = document.getElementById(elementId);
    if (!mapContainer) return;

    if (defectMap) return defectMap;
    if (mapContainer._leaflet_id) return;

    defectMap = L.map(elementId).setView([initialLat, initialLng], zoom);

    // OpenStreetMap Tile Layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
    }).addTo(defectMap);

    markerLayer = L.layerGroup().addTo(defectMap);
    loadMapMarkers();
}

async function loadMapMarkers(defectType = 'all', status = 'all') {
    if (!defectMap || !markerLayer) return;

    markerLayer.clearLayers();

    try {
        let url = `/api/defects-map?defect_type=${defectType}&status=${status}`;
        const response = await fetch(url);
        const data = await response.json();

        if (data.status === 'success' && data.markers.length > 0) {
            const bounds = [];

            data.markers.forEach(m => {
                const color = DEFECT_COLORS[m.defect_type] || DEFECT_COLORS['Other'];
                const customIcon = createCustomPin(color);

                const popupContent = `
                    <div style="min-width: 220px; font-family: system-ui, sans-serif;">
                        <img src="${m.image_url}" style="width: 100%; height: 110px; object-fit: cover; border-radius: 8px; margin-bottom: 8px;" alt="Defect" />
                        <h6 style="margin: 0 0 4px; font-weight: 700; color: #0f172a;">${m.defect_type}</h6>
                        <div style="font-size: 12px; color: #64748b; margin-bottom: 6px;">
                            <strong>Ticket:</strong> ${m.ticket}<br/>
                            <strong>Zone:</strong> ${m.zone}<br/>
                            <strong>Severity:</strong> <span class="badge bg-${m.severity === 'Critical' ? 'danger' : m.severity === 'High' ? 'warning' : 'info'}">${m.severity}</span>
                        </div>
                        <p style="font-size: 11px; color: #475569; margin: 0 0 8px;">${m.address}</p>
                        <a href="/admin/complaints?q=${m.ticket}" class="btn btn-sm btn-primary w-100" style="font-size: 11px;">View Full Details</a>
                    </div>
                `;

                const marker = L.marker([m.lat, m.lng], { icon: customIcon })
                    .bindPopup(popupContent)
                    .addTo(markerLayer);

                bounds.push([m.lat, m.lng]);
            });

            if (bounds.length > 0) {
                defectMap.fitBounds(bounds, { padding: [40, 40] });
            }
        }
    } catch (err) {
        console.error('Failed to load defect map markers:', err);
    }
}

function initSingleComplaintMap(elementId, lat, lng, defectType) {
    const container = document.getElementById(elementId);
    if (!container) return;

    const map = L.map(elementId).setView([lat, lng], 15);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap'
    }).addTo(map);

    const color = DEFECT_COLORS[defectType] || DEFECT_COLORS['Other'];
    const customIcon = createCustomPin(color);

    L.marker([lat, lng], { icon: customIcon })
        .bindPopup(`<strong>${defectType}</strong><br/>Lat: ${lat}, Lng: ${lng}`)
        .addTo(map)
        .openPopup();
}

document.addEventListener('DOMContentLoaded', () => {
    // Check if main defect map container exists
    if (document.getElementById('defectMap')) {
        initDefectMap('defectMap');
    }
});
