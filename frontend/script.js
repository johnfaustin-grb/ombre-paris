// --- Map Initialization ---
const map = L.map('map').setView([48.8566, 2.3522], 13); // Centered on Paris

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

// --- State Variables ---
let startPoint = null;
let endPoint = null;
let startMarker = null;
let endMarker = null;
let routeLine = null;

// --- Functions ---

function clearMap() {
    if (startMarker) map.removeLayer(startMarker);
    if (endMarker) map.removeLayer(endMarker);
    if (routeLine) map.removeLayer(routeLine);
    startPoint = null;
    endPoint = null;
    startMarker = null;
    endMarker = null;
    routeLine = null;
}

async function findRoute(start, end) {
    console.log("Finding route from", start, "to", end);

    const requestBody = {
        start_point: [start.lat, start.lng],
        end_point: [end.lat, end.lng]
    };

    try {
        // The API is running on port 8000, so we need the full URL
        const response = await fetch('http://localhost:8000/api/route', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (data.path) {
            console.log("Route found:", data.path);
            // The path is [[lat, lon], [lat, lon], ...]
            routeLine = L.polyline(data.path, { color: 'blue' }).addTo(map);
            map.fitBounds(routeLine.getBounds());
        }
    } catch (error) {
        console.error("Error fetching route:", error);
        alert("Could not retrieve the route. Please check the console for errors.");
    }
}

function onMapClick(e) {
    // If a route is already drawn, clear everything for a new one.
    if (startPoint && endPoint) {
        clearMap();
    }

    if (!startPoint) {
        // This is the first click: set start point
        startPoint = e.latlng;
        startMarker = L.marker(startPoint).addTo(map).bindPopup("Point de départ").openPopup();
    } else {
        // This is the second click: set end point and find route
        endPoint = e.latlng;
        endMarker = L.marker(endPoint).addTo(map).bindPopup("Destination").openPopup();

        findRoute(startPoint, endPoint);
    }
}

// --- Event Listener ---
map.on('click', onMapClick);
