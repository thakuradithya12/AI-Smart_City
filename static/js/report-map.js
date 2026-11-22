(() => {
  const mapNode = document.getElementById("report-map");
  if (!mapNode) return;
  const latField = document.getElementById("id_latitude");
  const lonField = document.getElementById("id_longitude");
  const accuracyField = document.getElementById("id_gps_accuracy_m");
  const status = document.getElementById("location-status");
  const locateButton = document.getElementById("locate-button");
  const start = [Number(latField.value) || 20, Number(lonField.value) || 0];
  let map = null;
  let marker = null;

  if (window.L) {
    map = L.map(mapNode).setView(start, latField.value && lonField.value ? 15 : 3);
    // OSM tiles are used at demo traffic only, with visible attribution.
    const tiles = L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(map);
    let tileFailureReported = false;
    tiles.on("tileerror", () => {
      if (tileFailureReported) return;
      tileFailureReported = true;
      map.removeLayer(tiles);
      status.textContent = "Map tiles are unavailable. Enter coordinates manually or use your location.";
    });
    marker = L.marker(start, { draggable: true }).addTo(map);
    map.on("click", (event) => applyPoint(event.latlng));
    marker.on("dragend", () => applyPoint(marker.getLatLng()));
  } else {
    status.textContent = "Interactive map is unavailable. Enter coordinates manually or use your location.";
  }

  function applyPoint(point) {
    latField.value = point.lat.toFixed(7);
    lonField.value = point.lng.toFixed(7);
    if (marker) marker.setLatLng(point);
    if (map) map.setView(point, Math.max(map.getZoom(), 15));
    status.textContent = "Location selected. Confirm the pin before submitting.";
  }

  locateButton.addEventListener("click", () => {
    if (!navigator.geolocation) {
      status.textContent = "Location is unavailable in this browser. Enter coordinates or select a point on the map.";
      return;
    }
    status.textContent = "Requesting your location…";
    navigator.geolocation.getCurrentPosition((position) => {
      applyPoint({ lat: position.coords.latitude, lng: position.coords.longitude });
      accuracyField.value = Math.round(position.coords.accuracy);
      status.textContent = "Your location is selected. Confirm the pin before submitting.";
    }, (error) => {
      status.textContent = error.code === error.PERMISSION_DENIED
        ? "Location access was denied. Enter coordinates or select a point on the map."
        : "Could not get your location. Enter coordinates or select a point on the map.";
    }, { enableHighAccuracy: true, timeout: 10000, maximumAge: 30000 });
  });
})();
