const blynkToken = "6fub_AeSZfywBab9j-d7KRXWKFPMwIxz";
const blynkServer = "sgp1.blynk.cloud";
// Car-002 shares the same Blynk token/device as Car-001, distinguished by
// virtual pins instead: Car-001 = v1-v4, Car-002 = v5-v8.

const cartoApiKey = "cb1_3p3v_1_c7e75ca303dcbd4b49651900";

const map = L.map('map', { zoomControl: false }).setView([14.0893, 121.3138], 15);
L.control.zoom({ position: 'topright' }).addTo(map);

let currentMapStyle = 'carto-voyager';
let baseTileLayer = L.tileLayer(`https://basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png?key=${cartoApiKey}`, {
    attribution: '&copy; <a href="https://carto.com/attributions">CARTO</a>'
}).addTo(map);

function toggleMapStyle() {
    map.removeLayer(baseTileLayer);
    const label = document.getElementById("map-style-name");
    if (currentMapStyle === 'carto-voyager') {
        currentMapStyle = 'osm-streets';
        baseTileLayer = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap'
        }).addTo(map);
        if (label) label.textContent = "Style: OpenStreetMap (Tap for Dark)";
    } else if (currentMapStyle === 'osm-streets') {
        currentMapStyle = 'carto-dark';
        baseTileLayer = L.tileLayer('https://basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}.png', {
            attribution: '&copy; CARTO Dark'
        }).addTo(map);
        if (label) label.textContent = "Style: Dark Carto (Tap for Voyager)";
    } else {
        currentMapStyle = 'carto-voyager';
        baseTileLayer = L.tileLayer(`https://basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png?key=${cartoApiKey}`, {
            attribution: '&copy; CARTO Voyager'
        }).addTo(map);
        if (label) label.textContent = "Style: Carto Voyager (Tap for Streets)";
    }
}

// --- VEHICLE DIRECTORY (Preloaded + Live Sync) ---
let FLEET_VEHICLES = [
    { id: 12, brand: 'Mitsubishi', model: 'Montero Sport', plate: 'DUY 6527', img: 'https://fydfsgjrlowrrtlmefwq.supabase.co/storage/v1/object/public/uploads/vehicle_12_1782050950.1362324_QX-Front-FS-GT4WD.png' },
    { id: 17, brand: 'Toyota', model: 'Vios XE AT', plate: 'DAT 1396', img: 'https://fydfsgjrlowrrtlmefwq.supabase.co/storage/v1/object/public/uploads/vehicles/vehicle_17_0_4a816ba9-3b02-435f-b151-a6c6333c374a.jpg' },
    { id: 27, brand: 'Toyota', model: 'Innova XE AT', plate: 'CCK 1126', img: 'https://fydfsgjrlowrrtlmefwq.supabase.co/storage/v1/object/public/uploads/vehicle_27_1790791244.234815_0_Screenshot%202026-10-01%20020017.png' },
    { id: 23, brand: 'Honda', model: 'BR-V', plate: 'NID 2724', img: 'https://fydfsgjrlowrrtlmefwq.supabase.co/storage/v1/object/public/uploads/vehicle_23_1790788841.666478_0_Gemini_Generated_Image_kmn55hkmn55hkmn5.jpg' },
    { id: 22, brand: 'Honda', model: 'City', plate: 'DCF 2987', img: 'https://fydfsgjrlowrrtlmefwq.supabase.co/storage/v1/object/public/uploads/vehicles/vehicle_22_1777724019_0_9c3cba48-03e9-4ed2-bcd8-0334dcb870ed.jpg' },
    { id: 30, brand: 'Toyota', model: 'Fortuner V AT', plate: 'DBH 8812', img: 'https://fydfsgjrlowrrtlmefwq.supabase.co/storage/v1/object/public/uploads/vehicle_30_1790790938.9109933_0_Screenshot%202026-10-01%20015433.png' },
    { id: 34, brand: 'Toyota', model: 'Hiace', plate: 'NCW 3918', img: 'https://fydfsgjrlowrrtlmefwq.supabase.co/storage/v1/object/public/uploads/vehicle_1790789402.9839945_Screenshot%202026-10-01%20012156.png' },
    { id: 18, brand: 'Toyota', model: 'Vios XLE AT', plate: 'DBJ 9483', img: 'https://fydfsgjrlowrrtlmefwq.supabase.co/storage/v1/object/public/uploads/vehicle_18_1790790453.7647066_0_Screenshot%202026-10-01%20014657.png' },
    { id: 24, brand: 'Toyota', model: 'Avanza G', plate: 'DAO 4897', img: 'https://fydfsgjrlowrrtlmefwq.supabase.co/storage/v1/object/public/uploads/vehicles/vehicle_24_0_782df71a-77ea-4f2d-82ba-c4936aead469.jpg' },
    { id: 26, brand: 'Toyota', model: 'Innova XE AT', plate: 'NHN 5388', img: 'https://fydfsgjrlowrrtlmefwq.supabase.co/storage/v1/object/public/uploads/vehicles/vehicle_26_0_a90bc58d-e430-4f06-99e6-9d67d926c972.jpg' },
    { id: 21, brand: 'Mitsubishi', model: 'Mirage G4', plate: 'DAN 2179', img: 'https://fydfsgjrlowrrtlmefwq.supabase.co/storage/v1/object/public/uploads/vehicles/vehicle_21_0_79161984-4030-4b1c-8d7a-87dd91508948.jpg' },
    { id: 14, brand: 'Toyota', model: 'Vios J MT', plate: 'NCX 4117', img: 'https://fydfsgjrlowrrtlmefwq.supabase.co/storage/v1/object/public/uploads/vehicle_14_1790788559.6570857_0_Screenshot%202026-10-01%20005336.png' }
];

// Current assigned vehicle IDs (persisted via localStorage)
let assignedVehicleId1 = parseInt(localStorage.getItem('autoride_assigned_gps_1'), 10) || 12; // Default: Montero Sport
let assignedVehicleId2 = parseInt(localStorage.getItem('autoride_assigned_gps_2'), 10) || 17; // Default: Vios XE

function getAssignedVehicle(deviceNum) {
    const targetId = deviceNum === 1 ? assignedVehicleId1 : assignedVehicleId2;
    return FLEET_VEHICLES.find(v => v.id === targetId) || FLEET_VEHICLES[deviceNum === 1 ? 0 : 1];
}

// --- YI TRACKER STYLE CUSTOM PINS ---
function createYiPinIcon(deviceNum, isCar2 = false) {
    const veh = getAssignedVehicle(deviceNum);
    const carClass = isCar2 ? 'car-2' : '';
    const carImg = veh.img || 'https://cdn-icons-png.flaticon.com/512/744/744465.png';
    
    // Badge format: "01·VIOS_DAT 1396"
    const prefix = deviceNum < 10 ? '0' + deviceNum : String(deviceNum);
    const modelParts = (veh.model || veh.brand || 'CAR').trim().split(/[\s_-]+/);
    const mainModel = (modelParts[0] || 'CAR').replace(/[^a-zA-Z0-9]/g, '').toUpperCase();
    const cleanPlate = (veh.plate || 'NO-PLATE').trim().toUpperCase();
    const label = `${prefix}·${mainModel}_${cleanPlate}`;

    const html = `
        <div class="yi-tracker-pin" onclick="onPinClicked('car${deviceNum}')">
            <div class="yi-pin-bubble ${carClass}">
                <img src="${carImg}" alt="${label}" onerror="this.onerror=null;this.src='https://cdn-icons-png.flaticon.com/512/744/744465.png';">
            </div>
            <div class="yi-pin-pointer ${carClass}"></div>
            <div class="yi-pin-badge ${carClass}">${label}</div>
        </div>
    `;
    return L.divIcon({
        html: html,
        className: 'yi-custom-div-icon',
        iconSize: [110, 75],
        iconAnchor: [55, 75],
        popupAnchor: [0, -78]
    });
}

function updateMarkerPopup(marker, deviceNum, lat, lng, sats) {
    const veh = getAssignedVehicle(deviceNum);
    const carImg = veh.img || 'https://cdn-icons-png.flaticon.com/512/744/744465.png';
    const fullName = `${veh.brand} ${veh.model} (${veh.plate})`;

    const content = `
        <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;min-width:210px;padding:3px;">
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
                <img src="${carImg}" style="width:40px;height:40px;border-radius:8px;object-fit:cover;border:1px solid #cbd5e1;" onerror="this.onerror=null;this.src='https://cdn-icons-png.flaticon.com/512/744/744465.png';">
                <div>
                    <div style="font-weight:800;font-size:0.88rem;color:#0f172a;line-height:1.2;">${fullName}</div>
                    <div style="font-size:0.72rem;color:#00B14F;font-weight:700;">GPS Unit ${deviceNum} Active</div>
                </div>
            </div>
            <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;padding:6px 8px;margin-bottom:8px;">
                <div style="font-size:0.72rem;color:#64748b;">Coordinates: <b style="color:#0f172a;font-family:monospace;">${lat.toFixed(5)}, ${lng.toFixed(5)}</b></div>
                <div style="font-size:0.70rem;color:#64748b;margin-top:2px;">Satellites: <b style="color:#007bff;">${sats}</b></div>
            </div>
            <button onclick="window.open('https://www.google.com/maps?q=${lat},${lng}','_blank')" style="width:100%;background:#007bff;color:white;border:none;border-radius:6px;padding:6px 10px;font-size:0.75rem;font-weight:700;cursor:pointer;">
                Google Maps Navigate
            </button>
        </div>
    `;
    marker.bindPopup(content);
}

let carIcon = createYiPinIcon(1, false);
let carMarker = L.marker([14.0893, 121.3138], { icon: carIcon });
let markerIsOnMap = false;

let carIcon2 = createYiPinIcon(2, true);
let carMarker2 = L.marker([14.0893, 121.3138], { icon: carIcon2 });
let markerIsOnMap2 = false;

// --- PRIVACY & DECRYPTION STATES ---
let isDecrypted = true; 
let isDecrypted2 = true;

let privacyRequested1 = false;
let privacyRequested2 = false;
let renterName1 = '';
let renterName2 = '';

let lastActiveTime = Date.now();
let lastActiveTime2 = Date.now();

// --- POPULATE VEHICLE SELECT DROPDOWNS ---
function initVehicleDropdowns() {
    const sel1 = document.getElementById('vehicle-select-1');
    const sel2 = document.getElementById('vehicle-select-2');

    const optionsHtml = FLEET_VEHICLES.map(v => `
        <option value="${v.id}">${v.brand} ${v.model} (${v.plate})</option>
    `).join('');

    if (sel1) {
        sel1.innerHTML = optionsHtml;
        sel1.value = assignedVehicleId1;
    }
    if (sel2) {
        sel2.innerHTML = optionsHtml;
        sel2.value = assignedVehicleId2;
    }

    updatePanelTitles();
}

function updatePanelTitles() {
    const v1 = getAssignedVehicle(1);
    const v2 = getAssignedVehicle(2);

    const title1 = document.getElementById('ui-title-1');
    if (title1) title1.textContent = `GPS 1: ${v1.brand} ${v1.model} (${v1.plate})`;

    const title2 = document.getElementById('ui-title-2');
    if (title2) title2.textContent = `GPS 2: ${v2.brand} ${v2.model} (${v2.plate})`;
}

function onVehicleSelectChange(deviceNum, newVehicleId) {
    const vid = parseInt(newVehicleId, 10);
    if (deviceNum === 1) {
        assignedVehicleId1 = vid;
        localStorage.setItem('autoride_assigned_gps_1', vid);
        carIcon = createYiPinIcon(1, false);
        carMarker.setIcon(carIcon);
    } else {
        assignedVehicleId2 = vid;
        localStorage.setItem('autoride_assigned_gps_2', vid);
        carIcon2 = createYiPinIcon(2, true);
        carMarker2.setIcon(carIcon2);
    }

    updatePanelTitles();
    checkRenterPrivacyOptOut();
}

// --- CHECK RENTER PRIVACY OPT-OUT FROM AUTORIDE BACKEND ---
async function checkRenterPrivacyOptOut() {
    try {
        const res = await fetch('https://autoride-booking-system.vercel.app/api/gps-privacy-status');
        if (res.ok) {
            const data = await res.json();
            
            const v1 = getAssignedVehicle(1);
            if (data[String(v1.id)]) {
                privacyRequested1 = true;
                renterName1 = data[String(v1.id)].customer_name || 'Renter';
                isDecrypted = false;
            } else {
                privacyRequested1 = false;
            }

            const v2 = getAssignedVehicle(2);
            if (data[String(v2.id)]) {
                privacyRequested2 = true;
                renterName2 = data[String(v2.id)].customer_name || 'Renter';
                isDecrypted2 = false;
            } else {
                privacyRequested2 = false;
            }
        }
    } catch (e) {
        console.log('[GPS] Privacy check error:', e);
    }
    updateDashboard();
    updateDashboard2();
}

// Sync fleet list from database
async function syncFleetListFromAPI() {
    try {
        const res = await fetch('https://autoride-booking-system.vercel.app/api/vehicles');
        if (res.ok) {
            const list = await res.json();
            if (Array.isArray(list) && list.length > 0) {
                FLEET_VEHICLES = list.map(v => ({
                    id: v.id,
                    brand: v.brand || 'Vehicle',
                    model: v.model || `#${v.id}`,
                    plate: v.plate_number || 'No Plate',
                    img: v.vehicle_image || 'https://cdn-icons-png.flaticon.com/512/744/744465.png'
                }));
                initVehicleDropdowns();
                updateMyStats();
            }
        }
    } catch (e) {}
}

// --- FLEET BAR & RADAR LOGIC ---
function updateFleetBar() {
    const textEl = document.getElementById("fleet-count-text");
    const count = (markerIsOnMap ? 1 : 0) + (markerIsOnMap2 ? 1 : 0);
    if (textEl) {
        const isMobile = window.innerWidth <= 480;
        if (count === 0) {
            textEl.textContent = isMobile ? "Fleet: No Pins" : "Fleet Radar: No Live Pins";
        } else if (count === 1) {
            textEl.textContent = isMobile ? "Fleet: 1 Live" : "Fleet Radar: 1 Vehicle Live";
        } else {
            textEl.textContent = isMobile ? `Fleet: ${count} Live` : `Fleet Radar: ${count} Vehicles Live`;
        }
    }
    updateMyStats();
}

function fitAllDevices() {
    const points = [];
    if (markerIsOnMap && carMarker) {
        points.push(carMarker.getLatLng());
    }
    if (markerIsOnMap2 && carMarker2) {
        points.push(carMarker2.getLatLng());
    }

    if (points.length === 0) {
        alert("No decrypted active devices currently on map. Click Device tab to decrypt / override.");
    } else if (points.length === 1) {
        map.setView(points[0], 16);
    } else {
        map.fitBounds(points, { padding: [80, 80], maxZoom: 16 });
    }
}

// ==========================================================================
// BOTTOM NAVIGATION DOCK & MODAL SHEETS MANAGEMENT
// ==========================================================================
let activeModalId = null;
let lastDockClickTime = 0;

function onDockClick(tab) {
    const now = Date.now();
    if (now - lastDockClickTime < 150) return;
    lastDockClickTime = now;

    if (tab === 'position') {
        closeAllModals();
        fitAllDevices();
        setActiveDockBtn('position');
    } else if (tab === 'device') {
        toggleModal('device-modal', 'device');
    } else if (tab === 'function') {
        toggleModal('function-modal', 'function');
    }
}

function setActiveDockBtn(tab) {
    document.querySelectorAll('.dock-btn').forEach(btn => btn.classList.remove('active-dock'));
    const btn = document.getElementById(`dock-btn-${tab}`);
    if (btn) btn.classList.add('active-dock');
}

function toggleModal(modalId, dockTab) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    
    if (activeModalId === modalId) {
        closeAllModals();
    } else {
        closeAllModals();
        modal.classList.add('is-open');
        activeModalId = modalId;
        setActiveDockBtn(dockTab);

        if (modalId === 'device-modal') {
            switchDeviceTab(currentDeviceSubtab || 1);
        }
    }
}

function closeAllModals() {
    document.querySelectorAll('.bottom-sheet-panel').forEach(p => p.classList.remove('is-open'));
    document.querySelectorAll('.dock-btn').forEach(btn => btn.classList.remove('active-dock'));
    activeModalId = null;
}

function setupDomGuards() {
    const ids = ['bottom-dock', 'device-modal', 'function-modal', 'fleet-bar'];
    ids.forEach(id => {
        const el = document.getElementById(id);
        if (el && typeof L !== 'undefined' && L.DomEvent) {
            L.DomEvent.disableClickPropagation(el);
            L.DomEvent.disableScrollPropagation(el);
        }
    });

    const dockButtons = [
        { id: 'dock-btn-position', tab: 'position' },
        { id: 'dock-btn-device', tab: 'device' },
        { id: 'dock-btn-function', tab: 'function' }
    ];

    dockButtons.forEach(({ id, tab }) => {
        const btn = document.getElementById(id);
        if (btn) {
            btn.onclick = (e) => {
                e.preventDefault();
                e.stopPropagation();
                onDockClick(tab);
            };
            btn.addEventListener('touchend', (e) => {
                e.preventDefault();
                e.stopPropagation();
                onDockClick(tab);
            }, { passive: false });
        }
    });

    document.querySelectorAll('.sheet-close-btn').forEach(btn => {
        btn.onclick = (e) => {
            e.preventDefault();
            e.stopPropagation();
            closeAllModals();
        };
        btn.addEventListener('touchend', (e) => {
            e.preventDefault();
            e.stopPropagation();
            closeAllModals();
        }, { passive: false });
    });
}

// Subtab switcher for Device Modal: 1 | 2 | all
let currentDeviceSubtab = 1;
function switchDeviceTab(subtab) {
    currentDeviceSubtab = subtab;
    const btn1 = document.getElementById('subtab-btn-1');
    const btn2 = document.getElementById('subtab-btn-2');
    const btnAll = document.getElementById('subtab-btn-all');
    
    if (btn1) btn1.classList.toggle('active', subtab === 1);
    if (btn2) btn2.classList.toggle('active', subtab === 2);
    if (btnAll) btnAll.classList.toggle('active', subtab === 'all');

    const card1 = document.getElementById('details-panel');
    const card2 = document.getElementById('details-panel-2');
    
    if (subtab === 1) {
        if (card1) card1.style.display = 'flex';
        if (card2) card2.style.display = 'none';
    } else if (subtab === 2) {
        if (card1) card1.style.display = 'none';
        if (card2) card2.style.display = 'flex';
    } else if (subtab === 'all') {
        if (card1) card1.style.display = 'flex';
        if (card2) card2.style.display = 'flex';
    }
}

function openDeviceTab(deviceNum) {
    const modal = document.getElementById('device-modal');
    if (modal) {
        closeAllModals();
        modal.classList.add('is-open');
        activeModalId = 'device-modal';
        setActiveDockBtn('device');
        switchDeviceTab(deviceNum);
    }
}

function onPinClicked(carId) {
    if (carId === 'car1') {
        openDeviceTab(1);
    } else if (carId === 'car2') {
        openDeviceTab(2);
    }
}

function updateMyStats() {
    const activeCount = (markerIsOnMap ? 1 : 0) + (markerIsOnMap2 ? 1 : 0);
    const actEl = document.getElementById('stat-active-gps');
    if (actEl) actEl.textContent = activeCount;
    const fltEl = document.getElementById('stat-fleet-total');
    if (fltEl) fltEl.textContent = FLEET_VEHICLES.length;
}

function toggleDecryptAll() {
    if (!isDecrypted || !isDecrypted2) {
        isDecrypted = true;
        isDecrypted2 = true;
        alert("Emergency Decrypt applied to all live units!");
    } else {
        isDecrypted = false;
        isDecrypted2 = false;
        alert("All units have been masked by Admin.");
    }
    updateDashboard();
    updateDashboard2();
}

// Center Map Buttons
const locBtn1 = document.getElementById("locate-btn");
if (locBtn1) {
    locBtn1.addEventListener("click", () => {
        if (markerIsOnMap) {
            map.setView(carMarker.getLatLng(), 16);
            closeAllModals();
        } else {
            alert("Car 1 location is currently encrypted or offline. Click Emergency Override to decrypt.");
        }
    });
}

const locBtn2 = document.getElementById("locate-btn-2");
if (locBtn2) {
    locBtn2.addEventListener("click", () => {
        if (markerIsOnMap2) {
            map.setView(carMarker2.getLatLng(), 16);
            closeAllModals();
        } else {
            alert("Car 2 location is currently encrypted or offline. Click Emergency Override to decrypt.");
        }
    });
}

// --- DECRYPT / EMERGENCY OVERRIDE LOGIC ---
function toggleOverride() {
    isDecrypted = !isDecrypted;
    const btn = document.getElementById("override-btn");
    
    if (isDecrypted) {
        btn.innerText = "🔒 Mask Location";
        btn.style.backgroundColor = "#475569";
        btn.style.color = "white";
    } else {
        btn.innerText = "🔓 Decrypt Location (Emergency Override)";
        btn.style.backgroundColor = "#ffc107";
        btn.style.color = "#212529";
    }
    updateDashboard();
}

function toggleOverride2() {
    isDecrypted2 = !isDecrypted2;
    const btn = document.getElementById("override-btn-2");

    if (isDecrypted2) {
        btn.innerText = "🔒 Mask Location";
        btn.style.backgroundColor = "#475569";
        btn.style.color = "white";
    } else {
        btn.innerText = "🔓 Decrypt Location (Emergency Override)";
        btn.style.backgroundColor = "#ffc107";
        btn.style.color = "#212529";
    }
    updateDashboard2();
}

// --- CORE DASHBOARD LOGIC (CAR-001) ---
async function updateDashboard() {
  try {
    const r = await fetch(`https://${blynkServer}/external/api/get?token=${blynkToken}&v1&v2&v3&v4&_=${Date.now()}`);
    const data = await r.json();
    const now = Date.now();
    
    if (data) {
      if (data.v4 !== undefined) {
        lastActiveTime = now;
      }
      const isOnline = (now - lastActiveTime < 20000);
      
      if (!isOnline) {
          document.getElementById("ui-dot").style.backgroundColor = "#94a3b8";
          document.getElementById("ui-sats").innerText = "Offline";
          if (markerIsOnMap) { map.removeLayer(carMarker); markerIsOnMap = false; }
          updateFleetBar();
          return;
      }

      const badge = document.getElementById("ui-privacy-badge");
      const btn = document.getElementById("override-btn");

      // PRIVACY/ENCRYPTION GATEKEEPER
      if (!isDecrypted) {
          document.getElementById("ui-lat").innerText = "*** ENCRYPTED ***";
          document.getElementById("ui-lng").innerText = "*** ENCRYPTED ***";
          document.getElementById("ui-sats").innerText = "Protected";
          
          if (privacyRequested1) {
              badge.innerText = `Security: Encrypted (${renterName1 || 'Renter'} Privacy Requested)`;
              badge.style.background = "#fee2e2";
              badge.style.color = "#991b1b";
              btn.innerText = "🔓 Decrypt Location (Emergency Override)";
              btn.style.backgroundColor = "#eab308";
              btn.style.color = "#000";
          } else {
              badge.innerText = "Security: Masked by Admin";
              badge.style.background = "#fff3cd";
              badge.style.color = "#856404";
              btn.innerText = "🔓 Unmask Location";
              btn.style.backgroundColor = "#ffc107";
              btn.style.color = "#212529";
          }
          
          if (markerIsOnMap) { map.removeLayer(carMarker); markerIsOnMap = false; }
          updateFleetBar();
      } else {
          updateCoordinates(data);
          badge.innerText = "Security: Decrypted • Live Active";
          badge.style.background = "#d4edda";
          badge.style.color = "#155724";
          btn.innerText = "🔒 Mask Location";
          btn.style.backgroundColor = "#475569";
          btn.style.color = "white";
      }

      document.getElementById("ui-dot").style.backgroundColor = "#28a745";
    }
  } catch (e) { console.log("Fetch error (Car-001)"); }
}

function updateCoordinates(data) {
    document.getElementById("ui-lat").innerText = data.v1 || "--";
    document.getElementById("ui-lng").innerText = data.v2 || "--";
    document.getElementById("ui-sats").innerText = data.v3 || "0";
    const lat = parseFloat(data.v1);
    const lng = parseFloat(data.v2);
    if (!isNaN(lat) && !isNaN(lng)) {
        carMarker.setLatLng([lat, lng]);
        updateMarkerPopup(carMarker, 1, lat, lng, data.v3 || '0');
        if (!markerIsOnMap) { carMarker.addTo(map); markerIsOnMap = true; }
        updateFleetBar();
    }
}

// --- CORE DASHBOARD LOGIC (CAR-002) ---
async function updateDashboard2() {
  try {
    const r = await fetch(`https://${blynkServer}/external/api/get?token=${blynkToken}&v5&v6&v7&v8&_=${Date.now()}`);
    const data = await r.json();
    const now = Date.now();

    if (data) {
      if (data.v8 !== undefined) {
        lastActiveTime2 = now;
      }
      const isOnline = (now - lastActiveTime2 < 20000);

      if (!isOnline) {
          document.getElementById("ui-dot-2").style.backgroundColor = "#94a3b8";
          document.getElementById("ui-sats-2").innerText = "Offline";
          if (markerIsOnMap2) { map.removeLayer(carMarker2); markerIsOnMap2 = false; }
          updateFleetBar();
          return;
      }

      const badge2 = document.getElementById("ui-privacy-badge-2");
      const btn2 = document.getElementById("override-btn-2");

      if (!isDecrypted2) {
          document.getElementById("ui-lat-2").innerText = "*** ENCRYPTED ***";
          document.getElementById("ui-lng-2").innerText = "*** ENCRYPTED ***";
          document.getElementById("ui-sats-2").innerText = "Protected";

          if (privacyRequested2) {
              badge2.innerText = `Security: Encrypted (${renterName2 || 'Renter'} Privacy Requested)`;
              badge2.style.background = "#fee2e2";
              badge2.style.color = "#991b1b";
              btn2.innerText = "🔓 Decrypt Location (Emergency Override)";
              btn2.style.backgroundColor = "#eab308";
              btn2.style.color = "#000";
          } else {
              badge2.innerText = "Security: Masked by Admin";
              badge2.style.background = "#fff3cd";
              badge2.style.color = "#856404";
              btn2.innerText = "🔓 Unmask Location";
              btn2.style.backgroundColor = "#ffc107";
              btn2.style.color = "#212529";
          }

          if (markerIsOnMap2) { map.removeLayer(carMarker2); markerIsOnMap2 = false; }
          updateFleetBar();
      } else {
          updateCoordinates2(data);
          badge2.innerText = "Security: Decrypted • Live Active";
          badge2.style.background = "#d4edda";
          badge2.style.color = "#155724";
          btn2.innerText = "🔒 Mask Location";
          btn2.style.backgroundColor = "#475569";
          btn2.style.color = "white";
      }

      document.getElementById("ui-dot-2").style.backgroundColor = "#28a745";
    }
  } catch (e) { console.log("Fetch error (Car-002)"); }
}

function updateCoordinates2(data) {
    document.getElementById("ui-lat-2").innerText = data.v5 || "--";
    document.getElementById("ui-lng-2").innerText = data.v6 || "--";
    document.getElementById("ui-sats-2").innerText = data.v7 || "0";
    const lat = parseFloat(data.v5);
    const lng = parseFloat(data.v6);
    if (!isNaN(lat) && !isNaN(lng)) {
        carMarker2.setLatLng([lat, lng]);
        updateMarkerPopup(carMarker2, 2, lat, lng, data.v7 || '0');
        if (!markerIsOnMap2) { carMarker2.addTo(map); markerIsOnMap2 = true; }
        updateFleetBar();
    }
}

// Initial setup
initVehicleDropdowns();
setupDomGuards();
switchDeviceTab(1); // default active subtab is GPS 1
syncFleetListFromAPI();

// Initial privacy check & auto-refresh interval
checkRenterPrivacyOptOut();
setInterval(checkRenterPrivacyOptOut, 30000);

// Auto-refresh GPS telemetry every 5 seconds
updateDashboard();
setInterval(updateDashboard, 5000);

updateDashboard2();
setInterval(updateDashboard2, 5000);