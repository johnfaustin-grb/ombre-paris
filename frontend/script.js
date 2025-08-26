// Center the map on Paris
const map = L.map('map').setView([48.8566, 2.3522], 13);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap'
}).addTo(map);

let startPoint = null, endPoint = null;
let startMarker = null, endMarker = null;
let routeLine = null;

function clearMap() {
    if (startMarker) map.removeLayer(startMarker);
    if (endMarker) map.removeLayer(endMarker);
    if (routeLine) map.removeLayer(routeLine);
    startPoint = endPoint = startMarker = endMarker = routeLine = null;
}

async function findRoute(start, end) {
    document.body.style.cursor = 'wait';
    const requestBody = {
        start_point: [start.lat, start.lng],
        end_point: [end.lat, end.lng]
    };

    try {
        const response = await fetch('/api/route', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(requestBody)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (data.path && data.path.length > 1) {
            routeLine = L.polyline(data.path, { color: 'blue' }).addTo(map);
            map.fitBounds(routeLine.getBounds());
        } else {
            alert("Un itinéraire valide n'a pas pu être tracé.");
        }
    } catch (error) {
        console.error("Error fetching route:", error);
        alert(`Erreur lors de la récupération de l'itinéraire: ${error.message}`);
    } finally {
        document.body.style.cursor = 'default';
    }
}

map.on('click', function(e) {
    if (startPoint && endPoint) {
        clearMap();
    }

    if (!startPoint) {
        startPoint = e.latlng;
        startMarker = L.marker(startPoint).addTo(map).bindPopup("Départ").openPopup();
    } else {
        endPoint = e.latlng;
        endMarker = L.marker(endPoint).addTo(map).bindPopup("Destination").openPopup();
        findRoute(startPoint, endPoint);
    }
});
