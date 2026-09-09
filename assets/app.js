(() => {
  "use strict";

  const DATA_URL = "web/data/torino_lookup.geojson";
  const META_URL = "web/data/metadata.json";
  const BOUNDARY_URL = "web/data/torino_boundary.geojson";

  const state = {
    metadata: null,
    geojson: null,
    boundary: null,
    map: null,
    gridLayer: null,
    boundaryLayer: null,
    selectedLayer: null,
    selectedFeature: null,
    marker: null,
    mode: "epw",
    indexedFeatures: [],
    layerById: new Map(),
    toastTimer: null,
  };

  const elements = {};

  function cacheElements() {
    [
      "lookup-form", "latitude", "longitude", "locate-button", "about-button",
      "about-dialog", "close-about", "fit-map", "legend", "loading-state",
      "result-panel", "empty-result", "result-content", "category-swatch",
      "category-title", "status-badge", "epw-download", "config-download",
      "share-result", "grid-id", "cluster-k4", "cluster-k7", "cluster-k8",
      "metric-building", "metric-height", "metric-facade", "metric-green",
      "metric-tree", "metric-grass", "uhi-section", "uhi-annual", "uhi-summer",
      "uhi-day", "uhi-night", "quality-message", "quality-text", "release-status",
      "toast",
    ].forEach((id) => { elements[id] = document.getElementById(id); });
    elements.layerTabs = [...document.querySelectorAll(".layer-tab")];
  }

  function initMap() {
    state.map = L.map("map", {
      zoomControl: false,
      preferCanvas: true,
      zoomAnimation: false,
      fadeAnimation: false,
      markerZoomAnimation: false,
      minZoom: 10,
      maxZoom: 19,
    });
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      detectRetina: true,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(state.map);
    L.control.zoom({ position: "bottomleft" }).addTo(state.map);
  }

  function getFeatureValue(feature, mode = state.mode) {
    const props = feature.properties;
    if (mode === "epw" && props.outside_domain) return "restricted";
    if (mode === "epw") return props.cat;
    return props[mode];
  }

  function colorFor(feature, mode = state.mode) {
    const value = getFeatureValue(feature, mode);
    if (value === null || value === undefined || value === "") return "#aeb6b1";
    if (value === "restricted") return "#303733";
    if (mode === "epw") return state.metadata.categories[value]?.color || "#aeb6b1";
    const k = mode.replace("k", "");
    return state.metadata.cluster_colors[k]?.[Number(value)] || "#aeb6b1";
  }

  function baseStyle(feature) {
    const selected = state.selectedFeature?.properties.id === feature.properties.id;
    return {
      color: selected ? "#ffffff" : "rgba(43, 52, 47, 0.38)",
      weight: selected ? 2.2 : 0.35,
      fillColor: colorFor(feature),
      fillOpacity: selected ? 0.92 : 0.7,
    };
  }

  function addGridLayer() {
    state.gridLayer = L.geoJSON(state.geojson, {
      style: baseStyle,
      onEachFeature(feature, layer) {
        state.layerById.set(feature.properties.id, layer);
        layer.on("click", () => selectFeature(feature, layer, true));
        layer.on("mouseover", () => {
          if (state.selectedFeature?.properties.id !== feature.properties.id) {
            layer.setStyle({ weight: 1.2, color: "#303733", fillOpacity: 0.84 });
          }
        });
        layer.on("mouseout", () => {
          if (state.selectedFeature?.properties.id !== feature.properties.id) {
            layer.setStyle(baseStyle(feature));
          }
        });
      },
    }).addTo(state.map);

    state.boundaryLayer = L.geoJSON(state.boundary, {
      interactive: false,
      style: { color: "#1d2521", weight: 1.4, fill: false, opacity: 0.72 },
    }).addTo(state.map);
    fitMap();
  }

  function fitMap() {
    if (state.boundaryLayer) {
      state.map.fitBounds(state.boundaryLayer.getBounds(), { padding: [18, 18] });
    }
  }

  function makeIndex() {
    state.indexedFeatures = state.geojson.features.map((feature) => {
      const polygons = feature.geometry.type === "Polygon" ? [feature.geometry.coordinates] : feature.geometry.coordinates;
      const ring = polygons.flatMap((polygon) => polygon[0]);
      let minLon = Infinity;
      let minLat = Infinity;
      let maxLon = -Infinity;
      let maxLat = -Infinity;
      ring.forEach(([lon, lat]) => {
        minLon = Math.min(minLon, lon);
        maxLon = Math.max(maxLon, lon);
        minLat = Math.min(minLat, lat);
        maxLat = Math.max(maxLat, lat);
      });
      return { feature, polygons, bbox: [minLon, minLat, maxLon, maxLat] };
    });
  }

  function pointInRing(lon, lat, ring) {
    let inside = false;
    for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
      const [xi, yi] = ring[i];
      const [xj, yj] = ring[j];
      const cross = (lon - xi) * (yj - yi) - (lat - yi) * (xj - xi);
      if (Math.abs(cross) <= 1e-14 && lon >= Math.min(xi, xj) && lon <= Math.max(xi, xj) && lat >= Math.min(yi, yj) && lat <= Math.max(yi, yj)) return true;
      const crosses = ((yi > lat) !== (yj > lat)) &&
        (lon < ((xj - xi) * (lat - yi)) / (yj - yi) + xi);
      if (crosses) inside = !inside;
    }
    return inside;
  }

  function lookupFeature(lat, lon) {
    const inPolygon = (polygon) => pointInRing(lon, lat, polygon[0]) && !polygon.slice(1).some((hole) => pointInRing(lon, lat, hole));
    const insideCity = state.boundary.features.some((feature) => {
      const polygons = feature.geometry.type === "Polygon" ? [feature.geometry.coordinates] : feature.geometry.coordinates;
      return polygons.some(inPolygon);
    });
    if (!insideCity) return null;
    for (const item of state.indexedFeatures) {
      const [minLon, minLat, maxLon, maxLat] = item.bbox;
      if (lon < minLon || lon > maxLon || lat < minLat || lat > maxLat) continue;
      if (item.polygons.some(inPolygon)) return item.feature;
    }
    return null;
  }

  function clusterLabel(k, value) {
    if (value === null || value === undefined) return "Unassigned";
    const descriptor = state.metadata.cluster_descriptors[String(k)]?.[String(value)];
    return descriptor ? `C${value}` : `C${value}`;
  }

  function formatPercent(value, digits = 1) {
    return value === null || value === undefined ? "-" : `${(Number(value) * 100).toFixed(digits)}%`;
  }

  function formatNumber(value, digits = 2, suffix = "") {
    return value === null || value === undefined ? "-" : `${Number(value).toFixed(digits)}${suffix}`;
  }

  function readableStatus(value) {
    if (!value) return "Unassigned";
    return value.replaceAll("_", " ");
  }

  function selectFeature(feature, layer = null, moveMap = false) {
    if (state.selectedLayer && state.selectedFeature) {
      const previousFeature = state.selectedFeature;
      state.selectedFeature = null;
      state.selectedLayer.setStyle(baseStyle(previousFeature));
    }

    state.selectedFeature = feature;
    state.selectedLayer = layer || state.layerById.get(feature.properties.id) || null;
    if (state.selectedLayer) {
      state.selectedLayer.setStyle(baseStyle(feature));
      state.selectedLayer.bringToFront();
    }

    const props = feature.properties;
    elements.latitude.value = Number(props.lat).toFixed(6);
    elements.longitude.value = Number(props.lon).toFixed(6);
    updateResult(props);
    updateUrl(props.lat, props.lon);

    if (state.marker) state.marker.remove();
    state.marker = L.marker([props.lat, props.lon], {
      icon: L.divIcon({
        className: "selection-pin",
        html: "<span></span>",
        iconSize: [16, 16],
        iconAnchor: [8, 8],
      }),
      interactive: false,
    }).addTo(state.map);
    if (moveMap) state.map.panTo([props.lat, props.lon]);
  }

  function updateResult(props) {
    const category = props.cat ? state.metadata.categories[props.cat] : null;
    elements["result-panel"].classList.remove("empty");
    elements["empty-result"].hidden = true;
    elements["result-content"].hidden = false;

    elements["category-swatch"].style.background = category?.color || "#aeb6b1";
    elements["category-title"].textContent = category ? `${props.cat} · ${category.name}` : "No EPW assignment";
    elements["status-badge"].textContent = readableStatus(props.recommendation);
    elements["status-badge"].classList.toggle("provisional", props.recommendation !== "candidate");

    elements["grid-id"].textContent = props.id;
    elements["cluster-k4"].textContent = clusterLabel(4, props.k4);
    elements["cluster-k7"].textContent = clusterLabel(7, props.k7);
    elements["cluster-k8"].textContent = clusterLabel(8, props.k8);
    elements["metric-building"].textContent = formatPercent(props.bld);
    elements["metric-height"].textContent = formatNumber(props.h, 1, " m");
    elements["metric-facade"].textContent = formatNumber(props.fs, 2);
    elements["metric-green"].textContent = props.green === null ? "-" : `${Number(props.green).toFixed(1)}%`;
    elements["metric-tree"].textContent = formatPercent(props.tree);
    elements["metric-grass"].textContent = formatPercent(props.grass);

    if (category && props.available) {
      elements["epw-download"].href = `data/epw/${category.epw_filename}`;
      elements["epw-download"].setAttribute("download", category.epw_filename);
      elements["config-download"].href = `data/configs/${category.config_filename}`;
      elements["config-download"].setAttribute("download", category.config_filename);
      elements["epw-download"].classList.remove("disabled");
      elements["config-download"].classList.remove("disabled");
      elements["epw-download"].removeAttribute("aria-disabled");
      elements["config-download"].removeAttribute("aria-disabled");
      elements["uhi-section"].hidden = false;
      elements["uhi-annual"].textContent = formatNumber(category.uhi_mean_c.annual, 2, " °C");
      elements["uhi-summer"].textContent = formatNumber(category.uhi_mean_c.summer_apr_sep, 2, " °C");
      elements["uhi-day"].textContent = formatNumber(category.uhi_mean_c.daytime_07_18, 2, " °C");
      elements["uhi-night"].textContent = formatNumber(category.uhi_mean_c.nighttime_19_06, 2, " °C");
    } else {
      elements["epw-download"].removeAttribute("href");
      elements["config-download"].removeAttribute("href");
      elements["epw-download"].removeAttribute("download");
      elements["config-download"].removeAttribute("download");
      elements["epw-download"].setAttribute("aria-disabled", "true");
      elements["config-download"].setAttribute("aria-disabled", "true");
      elements["epw-download"].classList.add("disabled");
      elements["config-download"].classList.add("disabled");
      elements["uhi-section"].hidden = true;
    }

    const warnings = [];
    if (props.outside_domain) warnings.push("Out of domain: this dense C6 industrial support exceeds the tested applicability of the common building-stock assumptions. Its morphology class is retained, but no location EPW is recommended.");
    if (!category) warnings.push("No EPW is assigned because this support lacks usable morphology inputs.");
    if (props.edge) warnings.push("The 500 m support crosses the municipal boundary and is provisional.");
    if (props.out7) warnings.push("The morphology exceeds its k=7 class 99th-percentile medoid distance.");
    if (props.qa > 0 && props.reason && !props.edge) warnings.push(props.reason.replaceAll("_", " "));
    elements["quality-message"].hidden = warnings.length === 0;
    elements["quality-text"].textContent = warnings.join(" ");
  }

  function setMode(mode) {
    state.mode = mode;
    elements.layerTabs.forEach((tab) => {
      const active = tab.dataset.mode === mode;
      tab.classList.toggle("active", active);
      tab.setAttribute("aria-pressed", String(active));
    });
    if (state.gridLayer) state.gridLayer.setStyle(baseStyle);
    if (state.selectedLayer && state.selectedFeature) {
      state.selectedLayer.setStyle(baseStyle(state.selectedFeature));
      state.selectedLayer.bringToFront();
    }
    renderLegend();
    updateUrl();
  }

  function renderLegend() {
    const counts = new Map();
    state.geojson.features.forEach((feature) => {
      const value = getFeatureValue(feature);
      const key = value === null || value === undefined ? "none" : String(value);
      counts.set(key, (counts.get(key) || 0) + 1);
    });

    const rows = [];
    if (state.mode === "epw") {
      Object.entries(state.metadata.categories).forEach(([id, category]) => {
        rows.push({ id, label: `${id} · ${category.name}`, shortLabel: `${id} · ${category.name}`, color: category.color, count: counts.get(id) || 0 });
      });
      if (counts.get("none")) rows.push({ id: "none", label: "Unassigned", shortLabel: "Unassigned", color: "#aeb6b1", count: counts.get("none") });
      if (counts.get("restricted")) rows.push({ id: "restricted", label: "Outside model domain", shortLabel: "Out of domain", color: "#303733", count: counts.get("restricted") });
    } else {
      const k = state.mode.replace("k", "");
      const descriptors = state.metadata.cluster_descriptors[k];
      Object.entries(descriptors).forEach(([id, label]) => {
        rows.push({ id, label: `C${id} · ${label}`, shortLabel: `C${id}`, color: state.metadata.cluster_colors[k][Number(id)], count: counts.get(id) || 0 });
      });
    }

    const title = state.mode === "epw" ? "EPW categories" : `${state.mode.replace("k", "k=")} morphology classes`;
    elements.legend.innerHTML = `<p class="legend-title">${title}</p>${rows.map((row) => `
      <div class="legend-row">
        <span class="legend-color" style="background:${row.color}"></span>
        <span class="legend-label" data-short="${row.shortLabel}">${row.label}</span>
        <span class="legend-count">${row.count.toLocaleString()}</span>
      </div>`).join("")}`;
  }

  function performLookup(lat, lon, zoom = true) {
    if (!Number.isFinite(lat) || !Number.isFinite(lon) || lat < -90 || lat > 90 || lon < -180 || lon > 180) {
      showToast("Enter valid latitude and longitude values.");
      return;
    }
    const feature = lookupFeature(lat, lon);
    if (!feature) {
      if (state.selectedLayer) state.selectedLayer.setStyle({ weight: 0.35 });
      state.selectedFeature = null;
      state.selectedLayer = null;
      if (state.marker) state.marker.remove();
      state.gridLayer.setStyle(baseStyle);
      elements["result-content"].hidden = true;
      elements["empty-result"].hidden = false;
      elements["empty-result"].querySelector("p").textContent = "Outside published municipal coverage";
      showToast("No Torino assignment cell covers this coordinate.");
      return;
    }
    selectFeature(feature, state.layerById.get(feature.properties.id), false);
    if (zoom) state.map.setView([lat, lon], Math.max(state.map.getZoom(), 15), { animate: false });
  }

  function updateUrl(lat = null, lon = null) {
    const url = new URL(window.location.href);
    url.searchParams.set("layer", state.mode);
    if (lat !== null && lon !== null) {
      url.searchParams.set("lat", Number(lat).toFixed(6));
      url.searchParams.set("lon", Number(lon).toFixed(6));
    }
    history.replaceState(null, "", url);
  }

  async function shareResult() {
    try {
      await navigator.clipboard.writeText(window.location.href);
      showToast("Result link copied.");
    } catch {
      showToast("Copy the current address from the browser.");
    }
  }

  function showToast(message) {
    elements.toast.textContent = message;
    elements.toast.classList.add("visible");
    window.clearTimeout(state.toastTimer);
    state.toastTimer = window.setTimeout(() => elements.toast.classList.remove("visible"), 2600);
  }

  function bindEvents() {
    elements["lookup-form"].addEventListener("submit", (event) => {
      event.preventDefault();
      if (!elements.latitude.value.trim() || !elements.longitude.value.trim()) {
        showToast("Enter both latitude and longitude.");
        return;
      }
      performLookup(Number(elements.latitude.value), Number(elements.longitude.value));
    });
    elements["locate-button"].addEventListener("click", () => {
      if (!navigator.geolocation) {
        showToast("Location services are not available in this browser.");
        return;
      }
      navigator.geolocation.getCurrentPosition(
        (position) => performLookup(position.coords.latitude, position.coords.longitude),
        () => showToast("Current location could not be read."),
        { enableHighAccuracy: true, timeout: 8000 }
      );
    });
    elements.layerTabs.forEach((tab) => tab.addEventListener("click", () => setMode(tab.dataset.mode)));
    elements["fit-map"].addEventListener("click", fitMap);
    elements["share-result"].addEventListener("click", shareResult);
    elements["about-button"].addEventListener("click", () => elements["about-dialog"].showModal());
    elements["close-about"].addEventListener("click", () => elements["about-dialog"].close());
    elements["about-dialog"].addEventListener("click", (event) => {
      if (event.target === elements["about-dialog"]) elements["about-dialog"].close();
    });
  }

  function applyQuery() {
    const query = new URLSearchParams(window.location.search);
    const mode = query.get("layer");
    if (["epw", "k4", "k7", "k8"].includes(mode)) setMode(mode);
    const lat = Number(query.get("lat"));
    const lon = Number(query.get("lon"));
    if (query.has("lat") && query.has("lon")) performLookup(lat, lon, true);
  }

  async function load() {
    cacheElements();
    initMap();
    bindEvents();
    lucide.createIcons();
    try {
      const [metadataResponse, geoResponse, boundaryResponse] = await Promise.all([
        fetch(META_URL),
        fetch(DATA_URL),
        fetch(BOUNDARY_URL),
      ]);
      if (!metadataResponse.ok || !geoResponse.ok || !boundaryResponse.ok) {
        throw new Error("One or more release data files could not be loaded");
      }
      [state.metadata, state.geojson, state.boundary] = await Promise.all([
        metadataResponse.json(),
        geoResponse.json(),
        boundaryResponse.json(),
      ]);
      makeIndex();
      addGridLayer();
      renderLegend();
      elements["release-status"].textContent = `v${state.metadata.version} · candidate`;
      elements["loading-state"].hidden = true;
      applyQuery();
    } catch (error) {
      console.error(error);
      elements["loading-state"].innerHTML = "<p>Atlas data could not be loaded</p>";
      showToast("Run the atlas from a local web server, not as a file URL.");
    }
  }

  window.addEventListener("DOMContentLoaded", load);
})();
