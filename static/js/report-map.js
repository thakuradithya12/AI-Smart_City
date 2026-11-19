(() => {
  const mapNode = document.getElementById("report-map");
  if (!mapNode || !window.L) return;
  const latField = document.getElementById("id_latitude");
  const lonField = document.getElementById("id_longitude");
  const accuracyField = document.getElementById("id_gps_accuracy_m");
  const start = [Number(latField.value) || 20, Number(lonField.value) || 0];
  const map = L.map(mapNode).setView(start, latField.value && lonField.value ? 15 : 3);
  // OSM tiles are used at demo traffic only, with visible attribution.
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(map);
  const marker = L.marker(start, { draggable: true }).addTo(map);
  const updateFields = (latlng) => {
    latField.value = latlng.lat.toFixed(7);
    lonField.value = latlng.lng.toFixed(7);
  };
  marker.on("dragend", () => updateFields(marker.getLatLng()));
  map.on("click", (event) => {
    marker.setLatLng(event.latlng);
    updateFields(event.latlng);
  });
  document.getElementById("locate-button").addEventListener("click", () => {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition((position) => {
      const point = { lat: position.coords.latitude, lng: position.coords.longitude };
      marker.setLatLng(point);
      map.setView(point, 16);
      updateFields(point);
      accuracyField.value = Math.round(position.coords.accuracy);
    });
  });
})();
