const API_BASE = "/api";

const SUPABASE_URL = 'https://fydfsgjrlowrrtlmefwq.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ5ZGZzZ2pybG93cnJ0bG1lZndxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUwMjkwNTcsImV4cCI6MjA5MDYwNTA1N30.m94HHMC7852zw9xfkkOYTPY1IzoH_kNPLYpTe0myGB4';
const supabaseClient = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

const vehicleForm = document.getElementById("vehicleForm");
const formTitle = document.getElementById("formTitle");
const submitBtn = document.getElementById("submitBtn");
const cancelEditBtn = document.getElementById("cancelEditBtn");
const refreshBtn = document.getElementById("refreshBtn");

const nameInput = document.getElementById("name");
const modelInput = document.getElementById("model");
const priceInput = document.getElementById("pricePerDay");
const availabilityInput = document.getElementById("availability");
const imageInput = document.getElementById("image");

const vehiclesBody = document.getElementById("vehiclesBody");
const vehiclesTable = document.getElementById("vehiclesTable");
const emptyState = document.getElementById("emptyState");
const loadingState = document.getElementById("loadingState");

let editingVehicleId = null;
let allVehicles = [];

document.addEventListener("DOMContentLoaded", () => {
    fetchVehicles();
    subscribeToUpdates();
    vehicleForm.addEventListener("submit", onSubmitVehicle);
    cancelEditBtn.addEventListener("click", resetForm);
    refreshBtn.addEventListener("click", fetchVehicles);
});

function subscribeToUpdates() {
    supabaseClient
        .channel('admin-vehicles')
        .on('postgres_changes', { event: '*', schema: 'public', table: 'vehicles' }, payload => {
            console.log('Realtime change detected:', payload);
            fetchVehicles();
        })
        .subscribe();
}

async function fetchVehicles() {
    showLoading(true);
    try {
        const res = await fetch(`${API_BASE}/vehicles`);
        if (!res.ok) {
            throw new Error(`Failed to fetch vehicles (${res.status})`);
        }
        const data = await res.json();
        allVehicles = Array.isArray(data) ? data : [];
        renderVehicles(allVehicles);
    } catch (err) {
        console.error(err);
        alert("Failed to load vehicles.");
        renderVehicles([]);
    } finally {
        showLoading(false);
    }
}

function renderVehicles(vehicles) {
    vehiclesBody.innerHTML = "";
    if (!vehicles.length) {
        vehiclesTable.classList.add("hidden");
        emptyState.classList.remove("hidden");
        return;
    }

    vehiclesTable.classList.remove("hidden");
    emptyState.classList.add("hidden");

    vehicles.forEach((v) => {
        const tr = document.createElement("tr");
        const displayName = v.name || v.brand || "";
        const status = (v.status || "Unavailable").toLowerCase();
        tr.innerHTML = `
            <td>${escapeHtml(v.plate_number || "N/A")}</td>
            <td>${escapeHtml(displayName)}</td>
            <td>${escapeHtml(v.model || "")}</td>
            <td>₱${formatMoney(v.daily_rate)}</td>
            <td><span class="pill ${status === "available" ? "available" : "unavailable"}">${escapeHtml(v.status || "Unavailable")}</span></td>
            <td>${renderImage(v.vehicle_image)}</td>
            <td>
                <div class="table-actions">
                    <button class="btn-edit" onclick="startEdit(${v.id})">Edit</button>
                    <button class="btn-delete" onclick="deleteVehicle(${v.id})">Delete</button>
                </div>
            </td>
        `;
        vehiclesBody.appendChild(tr);
    });
}

function renderImage(imageUrl) {
    if (!imageUrl) {
        return "<span>-</span>";
    }
    return `<img class="thumb" src="${escapeHtml(imageUrl)}" alt="Vehicle image">`;
}

async function onSubmitVehicle(event) {
    event.preventDefault();

    const payload = {
        name: nameInput.value.trim(),
        model: modelInput.value.trim(),
        price_per_day: Number(priceInput.value),
        status: availabilityInput.value,
        image: imageInput.value.trim()
    };

    if (!payload.name || !payload.model || Number.isNaN(payload.price_per_day)) {
        alert("Please fill in Name, Model, and Price per day.");
        return;
    }

    const isEditing = editingVehicleId !== null;
    const url = isEditing ? `${API_BASE}/vehicles/${editingVehicleId}` : `${API_BASE}/vehicles`;
    const method = isEditing ? "PUT" : "POST";

    try {
        const res = await fetch(url, {
            method,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!res.ok) {
            throw new Error(data.error || "Failed to save vehicle");
        }
        resetForm();
        await fetchVehicles();
    } catch (err) {
        alert(err.message);
    }
}

function startEdit(vehicleId) {
    const vehicle = allVehicles.find((v) => v.id === vehicleId);
    if (!vehicle) {
        return;
    }

    editingVehicleId = vehicleId;
    formTitle.textContent = "Edit Vehicle";
    submitBtn.textContent = "Update Vehicle";
    cancelEditBtn.classList.remove("hidden");

    nameInput.value = vehicle.name || vehicle.brand || "";
    modelInput.value = vehicle.model || "";
    priceInput.value = vehicle.daily_rate ?? "";
    availabilityInput.value = vehicle.status || "Available";
    imageInput.value = vehicle.vehicle_image || "";
    window.scrollTo({ top: 0, behavior: "smooth" });
}

async function deleteVehicle(vehicleId) {
    const ok = confirm("Delete this vehicle?");
    if (!ok) {
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/vehicles/${vehicleId}`, { method: "DELETE" });
        const data = await res.json();
        if (!res.ok) {
            throw new Error(data.error || "Failed to delete vehicle");
        }
        await fetchVehicles();
    } catch (err) {
        alert(err.message);
    }
}

function resetForm() {
    editingVehicleId = null;
    formTitle.textContent = "Add New Vehicle";
    submitBtn.textContent = "Add Vehicle";
    cancelEditBtn.classList.add("hidden");
    vehicleForm.reset();
    availabilityInput.value = "Available";
}

function showLoading(show) {
    loadingState.classList.toggle("hidden", !show);
    if (show) {
        vehiclesTable.classList.add("hidden");
        emptyState.classList.add("hidden");
    }
}

function formatMoney(value) {
    const n = Number(value || 0);
    return n.toLocaleString("en-PH", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function escapeHtml(value) {
    const text = value == null ? "" : String(value);
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}
