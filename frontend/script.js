// --- Map Initialization ---
// Center the map on Monaco for this PoC, as our street data is for Monaco
const map = L.map('map').setView([43.731, 7.42], 14); // Centered on Monaco

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

        if (data.path && data.path.length > 1) { // Ensure the path has more than one point
            console.log("Route found:", data.path);
            routeLine = L.polyline(data.path, { color: 'blue' }).addTo(map);
            map.fitBounds(routeLine.getBounds());
        } else {
            console.warn("Received an empty or single-point path. Cannot draw line.");
            alert("Could not draw a valid route.");
        }
    } catch (error) {
        console.error("Error fetching route:", error);
        alert("Could not retrieve the route. Please check the console for errors.");
    }
}

function onMapClick(e) {
    if (startPoint && endPoint) {
        clearMap();
    }

    if (!startPoint) {
        startPoint = e.latlng;
        startMarker = L.marker(startPoint).addTo(map).bindPopup("Point de départ").openPopup();
    } else {
        endPoint = e.latlng;
        endMarker = L.marker(endPoint).addTo(map).bindPopup("Destination").openPopup();
        findRoute(startPoint, endPoint);
    }
}

// --- Event Listener ---
map.on('click', onMapClick);
