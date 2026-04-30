const API_BASE = "/api";

const driversBody = document.getElementById("driversBody");
const searchInput = document.getElementById("searchInput");
const statusFilter = document.getElementById("statusFilter");
const refreshBtn = document.getElementById("refreshBtn");
const driversTable = document.getElementById("driversTable");
const emptyState = document.getElementById("emptyState");
const loadingState = document.getElementById("loadingState");
const wageInput = document.getElementById("wageInput");
const saveWageBtn = document.getElementById("saveWageBtn");

let allDrivers = [];

document.addEventListener("DOMContentLoaded", () => {
    fetchWage();
    fetchDrivers();
    searchInput.addEventListener("input", applyFilters);
    statusFilter.addEventListener("change", applyFilters);
    refreshBtn.addEventListener("click", fetchDrivers);
    saveWageBtn.addEventListener("click", saveWage);
});

async function fetchWage() {
    try {
        const res = await fetch(`${API_BASE}/settings/driver_wage`);
        const data = await res.json();
        if (data.wage) wageInput.value = data.wage;
    } catch (err) {
        console.error("Failed to fetch wage:", err);
    }
}

async function saveWage() {
    try {
        const res = await fetch(`${API_BASE}/settings/driver_wage`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ wage: wageInput.value })
        });
        if (res.ok) {
            alert("Default driver wage updated successfully!");
        } else {
            alert("Failed to update wage.");
        }
    } catch (err) {
        console.error(err);
        alert("Error saving wage.");
    }
}

async function fetchDrivers() {
    showLoading(true);
    try {
        const res = await fetch(`${API_BASE}/drivers`);
        if (!res.ok) {
            throw new Error(`Server error ${res.status}`);
        }
        allDrivers = await res.json();
        applyFilters();
    } catch (err) {
        console.error("Failed to fetch drivers:", err);
        allDrivers = [];
        renderRows([]);
        alert("Failed to load drivers. Check backend server.");
    } finally {
        showLoading(false);
    }
}

function applyFilters() {
    const query = searchInput.value.toLowerCase().trim();
    const selectedStatus = statusFilter.value;

    let filtered = allDrivers;

    if (selectedStatus !== "all") {
        filtered = filtered.filter((d) => d.status === selectedStatus);
    }

    if (query) {
        filtered = filtered.filter((d) =>
            (d.full_name || "").toLowerCase().includes(query) ||
            (d.license_number || "").toLowerCase().includes(query) ||
            (d.contact_info || "").toLowerCase().includes(query)
        );
    }

    renderRows(filtered);
}

function renderRows(drivers) {
    driversBody.innerHTML = "";

    if (drivers.length === 0) {
        driversTable.classList.add("hidden");
        emptyState.classList.remove("hidden");
        return;
    }

    driversTable.classList.remove("hidden");
    emptyState.classList.add("hidden");

    drivers.forEach((driver) => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${escapeHtml(driver.full_name)}</td>
            <td>${escapeHtml(driver.license_number)}</td>
            <td>${escapeHtml(driver.contact_info)}</td>
            <td><span class="status ${driver.status.toLowerCase()}">${driver.status}</span></td>
            <td>${renderActions(driver)}</td>
        `;
        driversBody.appendChild(tr);
    });
}

function renderActions(driver) {
    if (driver.status !== "Pending") {
        return "<span>-</span>";
    }

    return `
        <div class="actions">
            <button class="btn btn-approve" onclick="updateStatus(${driver.id}, 'approve')">Approve</button>
            <button class="btn btn-reject" onclick="updateStatus(${driver.id}, 'reject')">Reject</button>
        </div>
    `;
}

async function updateStatus(driverId, action) {
    let payload = {};
    if (action === "reject") {
        const reason = prompt("Please enter a reason for rejecting this driver application:");
        if (reason === null) return; // User cancelled
        payload.reason = reason;
    } else {
        const ok = confirm("Are you sure you want to approve this driver?");
        if (!ok) return;
    }

    try {
        const res = await fetch(`${API_BASE}/drivers/${driverId}/${action}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!res.ok) {
            throw new Error(data.error || "Request failed");
        }
        await fetchDrivers();
    } catch (err) {
        alert(err.message);
    }
}

function showLoading(show) {
    loadingState.classList.toggle("hidden", !show);
    if (show) {
        driversTable.classList.add("hidden");
        emptyState.classList.add("hidden");
    }
}

function escapeHtml(value) {
    const text = value == null ? "" : String(value);
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}
