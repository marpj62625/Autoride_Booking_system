
    const API_BASE = 'https://autoride-booking-system.vercel.app';
    const API_URL = API_BASE + '/api';

    // Admin notification globals ï¿½ defined early so initSession can call them
    window.adminNotifList = [];

    window.loadAdminNotifications = function(adminId) {
        fetch(API_URL + '/admin/notifications?admin_id=' + adminId)
            .then(r => r.json())
            .then(data => {
                window.adminNotifList = Array.isArray(data) ? data : [];
                if (typeof window.updateAdminNotifBadge === 'function') window.updateAdminNotifBadge();
            }).catch(() => {});
    };

    window.updateAdminNotifBadge = function() {
        const unread = (window.adminNotifList || []).filter(n => !n.is_read).length;
        const badge = document.getElementById('adminNotifBadge');
        if (!badge) return;
        if (unread > 0) {
            badge.textContent = unread > 99 ? '99+' : String(unread);
            badge.style.display = 'flex';
        } else {
            badge.style.display = 'none';
        }
    };

    window.toggleAdminNotifPanel = function() {
        const panel = document.getElementById('adminNotifPanel');
        const list = document.getElementById('adminNotifList');
        if (!panel) return;
        const isVisible = panel.style.display !== 'none';
        panel.style.display = isVisible ? 'none' : 'block';
        if (!isVisible) {
            const user = typeof adminAuth !== 'undefined' ? adminAuth.getUser() : null;
            if (user && user.id) {
                fetch(API_URL + '/admin/notifications/read-all', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ admin_id: user.id })
                }).then(() => {
                    (window.adminNotifList || []).forEach(n => n.is_read = true);
                    window.updateAdminNotifBadge();
                }).catch(() => {});
            }
            const notifs = window.adminNotifList || [];
            if (!notifs.length) {
                list.innerHTML = '<p style="color:var(--text-muted);text-align:center;padding:16px 0;font-size:0.875rem;">No notifications yet</p>';
            } else {
                list.innerHTML = notifs.map(n => {
                    const ts = n.created_at ? new Date(n.created_at).toLocaleString() : '';
                    const unreadStyle = n.is_read ? '' : 'border-left:3px solid #00B14F;padding-left:8px;background:rgba(0,177,79,0.08);';
                    return `<div style="padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.06);${unreadStyle}">
                        <strong style="font-size:0.85rem;color:#f1f5f9;">${n.title || ''}</strong>
                        <p style="font-size:0.78rem;color:#94a3b8;margin-top:3px;">${n.message || ''}</p>
                        <small style="color:var(--text-muted);">${ts}</small>
                    </div>`;
                }).join('');
            }
        }
    };

    window.saveAdminFcmToken = function(token) {
        const user = typeof adminAuth !== 'undefined' ? adminAuth.getUser() : null;
        if (!token || !user || !user.id) return;
        fetch(API_URL + '/admin/fcm-token', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ admin_id: user.id, fcm_token: token })
        }).catch(() => {});
    };
    
    // Global API fetcher for production
    window.apiFetch = async function(path, options = {}) {
        let cleanPath = path.startsWith('/') ? path.slice(1) : path;
        let url = `${API_URL}/${cleanPath}`;
        return fetch(url, options);
    };
    const apiFetch = window.apiFetch;


    const SESSION_TTL_MS = 8 * 60 * 60 * 1000; // 8 hours

    const adminAuth = {
        login: async function() {
            const email = document.getElementById('loginEmail').value;
            const password = document.getElementById('loginPass').value;
            const btn = document.getElementById('loginBtn');
            
            if (!btn) {
                alert('CRITICAL: Login button not found in DOM');
                return;
            }
            const originalText = btn.innerHTML;
            
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Authenticating...';

            try {
                const res = await fetch(`${API_URL}/admin/login`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({email, password})
                });
                const data = await res.json();
                if (res.ok) {
                    // Store with timestamp for expiry check
                    localStorage.setItem('admin_user', JSON.stringify({ user: data, savedAt: Date.now() }));
                    this.initSession();
                } else {
                    document.getElementById('loginError').textContent = data.error || 'Invalid credentials';
                }
            } catch (err) { 
                console.error('Login error:', err);
                alert('FETCH ERROR: ' + err.message + '\nTarget: ' + API_BASE + '/api/admin/login');
                showNotification('Connection Error: ' + err.message, 'error'); 
            } finally {
                btn.disabled = false;
                btn.innerHTML = originalText;
            }
        },
        getUser: () => {
            try {
                const raw = localStorage.getItem('admin_user');
                if (!raw) return null;
                const parsed = JSON.parse(raw);
                // Support old format (plain user object)
                if (parsed && parsed.id) return parsed;
                // New format with expiry
                if (parsed && parsed.user && parsed.savedAt) {
                    if (Date.now() - parsed.savedAt > SESSION_TTL_MS) {
                        localStorage.removeItem('admin_user');
                        return null; // expired
                    }
                    return parsed.user;
                }
                return null;
            } catch(e) { return null; }
        },
        logout: function() {
            localStorage.removeItem('admin_user');
            location.reload(); 
        },
        logoutAndExit: function() {
            localStorage.removeItem('admin_user');
            if (window.Capacitor && window.Capacitor.Plugins && window.Capacitor.Plugins.App) {
                window.Capacitor.Plugins.App.exitApp();
            } else {
                location.reload();
            }
        },
        initSession: function() {
            const user = this.getUser();
            if (user) {
                // Load saved theme preference ï¿½ default to LIGHT
                var savedAdminTheme = localStorage.getItem('adminTheme');
                if (savedAdminTheme === 'dark') {
                    document.documentElement.setAttribute('data-theme', 'dark');
                    const icon = document.getElementById('adminDarkModeIcon');
                    const label = document.getElementById('adminDarkModeLabel');
                    if (icon) icon.className = 'fas fa-sun';
                    if (label) label.textContent = 'Light Mode';
                } else {
                    document.documentElement.removeAttribute('data-theme');
                }

                const overlay = document.getElementById('adminLoginOverlay');
                if (overlay) overlay.style.display = 'none';
                
                const nameEl = document.getElementById('adminName') || document.getElementById('settingsName');
                const roleEl = document.getElementById('adminRole') || document.getElementById('settingsRole');
                const avatarEl = document.getElementById('adminAvatar') || document.getElementById('settingsAvatar');
                
                if (nameEl) nameEl.textContent = user.full_name;
                if (roleEl) roleEl.textContent = user.role.replace('_', ' ').toUpperCase();
                if (avatarEl) avatarEl.textContent = user.full_name[0].toUpperCase();

                const userRole = (user.role || '').toLowerCase().replace(/_/g, ' ').trim();
                const isSuper = userRole.includes('super admin') || userRole.includes('superadmin');
                
                document.querySelectorAll('.revenue-restricted').forEach(el => {
                    el.style.display = isSuper ? (el.tagName === 'A' || el.tagName === 'BUTTON' ? 'flex' : 'block') : 'none';
                });

                // Register FCM token if available from native layer
                if (window._adminFcmToken) saveAdminFcmToken(window._adminFcmToken);

                // Load admin notifications
                loadAdminNotifications(user.id);

                // Start chat badge polling every 30s
                if (typeof AdminChat !== 'undefined') {
                    AdminChat.updateNavBadge();
                    setInterval(function() { AdminChat.updateNavBadge(); }, 30000);
                }

                if (isSuper) { switchTab('dashboard'); refreshDashboard(); }
                else switchTab('vehicles');
            } else {
                const overlay = document.getElementById('adminLoginOverlay');
                if (overlay) overlay.style.display = 'flex';
            }
        }
    };
    window.adminAuth = adminAuth;

    // --- DARK MODE TOGGLE ---
    function toggleDarkMode() {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        const icon = document.getElementById('adminDarkModeIcon');
        const label = document.getElementById('adminDarkModeLabel');
        if (isDark) {
            document.documentElement.removeAttribute('data-theme');
            localStorage.setItem('adminTheme', 'light');
            if (icon) icon.className = 'fas fa-moon';
            if (label) label.textContent = 'Dark Mode';
        } else {
            document.documentElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('adminTheme', 'dark');
            if (icon) icon.className = 'fas fa-sun';
            if (label) label.textContent = 'Light Mode';
        }
    }

    // --- SYSTEM CONFIG MODAL ---
    function toggleSystemConfigModal() {
        const modal = document.getElementById('systemConfigModal');
        if (modal) {
            modal.style.display = 'flex';
            // Load settings when modal opens
            if (typeof Settings !== 'undefined' && Settings.fetch) {
                Settings.fetch();
            }
        }
    }

    function closeSystemConfigModal() {
        const modal = document.getElementById('systemConfigModal');
        if (modal) {
            modal.style.display = 'none';
        }
    }

    function closeSystemConfigModalBackdrop(event) {
        // Only close if clicking on the backdrop (not the modal content)
        if (event.target === event.currentTarget) {
            closeSystemConfigModal();
        }
    }

    // --- VEHICLES MODULE (REFINED) ---
    const Vehicles = {
        data: [],
        _filter: 'all',

        setFilter(filter, btn) {
            this._filter = filter;
            document.querySelectorAll('.veh-chip').forEach(b => {
                const active = b.dataset.filter === filter;
                b.style.background  = active ? 'var(--primary)' : 'var(--surface-container)';
                b.style.borderColor = active ? 'var(--primary)' : 'var(--border)';
                b.style.color       = active ? '#fff' : 'var(--text-secondary)';
            });
            this.applyFilters();
        },

        applyFilters() {
            const q = (document.getElementById('vehicleSearch')?.value || '').toLowerCase().trim();
            const f = this._filter;
            const filtered = this.data.filter(v => {
                const status = (v.status || '').toLowerCase();
                const matchF = f === 'all' || status === f;
                const matchQ = !q ||
                    (v.brand        || '').toLowerCase().includes(q) ||
                    (v.model        || '').toLowerCase().includes(q) ||
                    (v.plate_number || '').toLowerCase().includes(q) ||
                    (v.vehicle_type || '').toLowerCase().includes(q);
                return matchF && matchQ;
            });
            this._render(filtered);
        },
        async refresh() {
            const listContainer = document.getElementById('vehiclesList');
            if (!listContainer.innerHTML.trim() || listContainer.innerHTML.includes('Loading vehicles')) {
                listContainer.innerHTML = '<div style="text-align: center; padding: 50px; color: var(--text-muted);">Loading vehicles...</div>';
            }
            try {
                const res = await fetch(`${API_URL}/vehicles`);
                if (!res.ok) throw new Error('Server not reachable');
                this.data = await res.json();
                // Reset search + chips
                const s = document.getElementById('vehicleSearch');
                if (s) s.value = '';
                this._filter = 'all';
                document.querySelectorAll('.veh-chip').forEach(b => {
                    const active = b.dataset.filter === 'all';
                    b.style.background  = active ? 'var(--primary)' : 'var(--surface-container)';
                    b.style.borderColor = active ? 'var(--primary)' : 'var(--border)';
                    b.style.color       = active ? '#fff' : 'var(--text-secondary)';
                });
                this._render(this.data);
            } catch (err) {
                console.error('Vehicles Refresh Error:', err);
                listContainer.innerHTML = `<div style="text-align: center; padding: 50px; color: var(--danger);">
                    <i class="fas fa-exclamation-circle" style="font-size: 2rem; margin-bottom: 10px;"></i><br>
                    Could not load vehicles. Check your connection.<br>
                    <button onclick="Vehicles.refresh()" style="margin-top:10px; color:white; background:var(--primary); border:none; padding:8px 15px; border-radius:5px;">Retry</button>
                </div>`;
            }
        },
        
        galleryDetails: [],

        CAR_DATA: {
            "Toyota": ["Vios", "Fortuner", "Innova", "Hilux", "Wigo", "Rush", "Raize", "Hiace"],
            "Mitsubishi": ["Montero Sport", "Mirage G4", "L300", "Xpander", "Strada"],
            "Nissan": ["Navara", "Terra", "Almera", "Urvan", "Patrol"],
            "Honda": ["Civic", "City", "BR-V", "CR-V", "Brio", "HR-V"],
            "Hyundai": ["Starex", "Accent", "Tucson", "Santa Fe", "Creta", "Staria"],
            "Ford": ["Everest", "Ranger", "Territory", "Mustang"],
            "Suzuki": ["Ertiga", "Swift", "Dzire", "Jimny", "S-Presso"],
            "Isuzu": ["mu-X", "D-MAX", "Traviz"]
        },

        CAR_SPECS: {
            "Vios": { seats: "5", type: "Sedan", fuel: "Gasoline" },
            "Fortuner": { seats: "7", type: "SUV", fuel: "Diesel" },
            "Innova": { seats: "7", type: "MPV", fuel: "Diesel" },
            "Hilux": { seats: "5", type: "Pickup", fuel: "Diesel" },
            "Wigo": { seats: "5", type: "Hatchback", fuel: "Gasoline" },
            "Rush": { seats: "7", type: "SUV", fuel: "Gasoline" },
            "Raize": { seats: "5", type: "SUV", fuel: "Gasoline" },
            "Hiace": { seats: "12", type: "Van", fuel: "Diesel" },
            "Montero Sport": { seats: "7", type: "SUV", fuel: "Diesel" },
            "Mirage G4": { seats: "5", type: "Sedan", fuel: "Gasoline" },
            "L300": { seats: "10", type: "Van", fuel: "Diesel" },
            "Xpander": { seats: "7", type: "MPV", fuel: "Gasoline" },
            "Strada": { seats: "5", type: "Pickup", fuel: "Diesel" },
            "Navara": { seats: "5", type: "Pickup", fuel: "Diesel" },
            "Terra": { seats: "7", type: "SUV", fuel: "Diesel" },
            "Almera": { seats: "5", type: "Sedan", fuel: "Gasoline" },
            "Urvan": { seats: "12", type: "Van", fuel: "Diesel" },
            "Civic": { seats: "5", type: "Sedan", fuel: "Gasoline" },
            "City": { seats: "5", type: "Sedan", fuel: "Gasoline" },
            "BR-V": { seats: "7", type: "SUV", fuel: "Gasoline" },
            "CR-V": { seats: "7", type: "SUV", fuel: "Diesel" },
            "Brio": { seats: "5", type: "Hatchback", fuel: "Gasoline" },
            "Ertiga": { seats: "7", type: "MPV", fuel: "Gasoline" },
            "Jimny": { seats: "4", type: "SUV", fuel: "Gasoline" },
            "Everest": { seats: "7", type: "SUV", fuel: "Diesel" },
            "Ranger": { seats: "5", type: "Pickup", fuel: "Diesel" }
        },

        updateModels(selectedModel = null) {
            const brand = document.getElementById('vBrand').value;
            const modelDataList = document.getElementById('vModelList');
            modelDataList.innerHTML = '';
            
            if (brand && this.CAR_DATA[brand]) {
                this.CAR_DATA[brand].forEach(m => {
                    const opt = document.createElement('option');
                    opt.value = m;
                    modelDataList.appendChild(opt);
                });
                if (selectedModel) {
                    document.getElementById('vModel').value = selectedModel;
                    this.applySpecs(selectedModel);
                }
            }
        },

        applySpecs(model) {
            const editingId = document.getElementById('editId').value;
            if (!model || editingId) return; // Don't auto-fill if editing existing
            const specs = this.CAR_SPECS[model];
            if (specs) {
                if (specs.seats) document.getElementById('vSeats').value = specs.seats;
                if (specs.type) document.getElementById('vType').value = specs.type;
                if (specs.fuel) document.getElementById('vFuel').value = specs.fuel;
            }
        },

        render() { this._render(this.data); },

        _render(vehicles) {
            const listContainer = document.getElementById('vehiclesList');
            if (!vehicles || vehicles.length === 0) {
                listContainer.innerHTML = `
                    <div style="text-align:center;padding:60px 20px;background:var(--surface);border-radius:var(--radius-lg);border:1px solid var(--border);">
                        <i class="fas fa-car-crash" style="font-size:3rem;color:var(--text-muted);opacity:0.3;margin-bottom:15px;"></i>
                        <p style="color:var(--text-muted);font-weight:600;">No vehicles found.</p>
                    </div>`;
                return;
            }

            const statusColor = s => {
                switch ((s||'').toLowerCase()) {
                    case 'available':   return '#00B14F';
                    case 'rented':      return '#00B14F';
                    case 'maintenance': return '#f59e0b';
                    default:            return '#ef4444';
                }
            };

            listContainer.innerHTML = `<ul style="list-style:none;margin:0;padding:0;">` +
                vehicles.map((v, i) => {
                    const sc = statusColor(v.status);
                    const imgHtml = v.vehicle_image
                        ? `<img src="${v.vehicle_image}" style="width:100%;height:100%;object-fit:cover;border-radius:12px;">`
                        : `<i class="fas fa-car" style="font-size:1.6rem;color:var(--primary);opacity:0.4;"></i>`;
                    return `
                    <li style="display:flex;align-items:center;gap:14px;padding:14px 16px;background:var(--surface-card,var(--surface));${i === 0 ? 'border-radius:16px 16px 0 0;' : ''}${i === vehicles.length-1 ? 'border-radius:0 0 16px 16px;' : ''}border-bottom:${i < vehicles.length-1 ? '1px solid var(--border)' : 'none'};">
                        <div style="flex-shrink:0;width:72px;height:56px;background:var(--surface-container);border-radius:12px;display:flex;align-items:center;justify-content:center;overflow:hidden;">
                            ${imgHtml}
                        </div>
                        <div style="flex:1;min-width:0;">
                            <div style="font-size:0.95rem;font-weight:900;color:var(--primary);letter-spacing:-0.3px;margin-bottom:1px;">₱${Number(v.daily_rate||0).toLocaleString()}</div>
                            <div style="font-size:0.85rem;font-weight:700;color:var(--text-main);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${v.brand||''} ${v.model||''}</div>
                            <div style="font-size:0.72rem;color:var(--text-muted);font-weight:600;margin-bottom:5px;">${v.plate_number||'NO PLATE'}</div>
                            <span style="display:inline-block;padding:3px 10px;border-radius:20px;background:${sc};color:#fff;font-size:0.65rem;font-weight:800;">${(v.status||'Unavailable')}</span>
                        </div>
                        <div style="flex-shrink:0;display:flex;flex-direction:column;gap:12px;align-items:center;">
                            <button onclick="Vehicles.edit(${v.id})" style="background:none;border:none;color:var(--text-muted);font-size:1.05rem;padding:4px;cursor:pointer;"><i class="fas fa-pen-to-square"></i></button>
                            <button onclick="Vehicles.delete(${v.id})" style="background:none;border:none;color:var(--text-muted);font-size:1.05rem;padding:4px;cursor:pointer;"><i class="fas fa-trash-can"></i></button>
                        </div>
                    </li>`;
                }).join('') + `</ul>`;
        },
        openModal(id = null) {
            document.getElementById('editId').value = id || '';
            document.getElementById('modalTitle').textContent = id ? 'Edit Vehicle' : 'Add New Vehicle';
            document.getElementById('submitBtnText').textContent = id ? 'Update Vehicle' : 'Add Vehicle';
            // Show "Save & Add Another" only for new vehicles
            const addAnotherBtn = document.getElementById('saveAddAnotherBtn');
            if (addAnotherBtn) addAnotherBtn.style.display = id ? 'none' : 'inline-flex';

            if (id) {
                const v = this.data.find(x => x.id === id);
                if (!v) return;
                document.getElementById('vBrand').value = v.brand;
                this.updateModels(v.model);
                document.getElementById('vPlate').value = v.plate_number;
                document.getElementById('vColor').value = v.color || '';
                document.getElementById('vType').value = v.vehicle_type || 'Sedan';
                document.getElementById('vTrans').value = v.transmission || 'Automatic';
                document.getElementById('vFuel').value = v.fuel_type || 'Gasoline';
                document.getElementById('vSeats').value = v.seats || 5;
                document.getElementById('vLocation').value = v.location || 'Tanauan/Sto. Tomas, Batangas';
                document.getElementById('vStatus').value = v.status;
                document.getElementById('vRate').value = v.daily_rate;
                
                // Gallery Details
                this.galleryDetails = v.gallery_details || [];
                this.renderGalleryManager();
            } else {
                document.getElementById('vehicleForm').reset();
                this.updateModels();
                document.getElementById('vExistingGallery').style.display = 'none';
                this.galleryDetails = [];
            }
            // Always clear new-photo selections when opening the modal
            VehiclePhotos.clear();
            document.getElementById('vehicleModal').style.display = 'block';
        },

        renderGalleryManager() {
            const container = document.getElementById('vGalleryManager');
            const section = document.getElementById('vExistingGallery');
            
            if (this.galleryDetails.length === 0) {
                section.style.display = 'none';
                return;
            }

            section.style.display = 'block';
            container.innerHTML = this.galleryDetails.map((img, index) => `
                <div style="flex: 0 0 90px; position: relative; border-radius: 8px; overflow: hidden; border: 1px solid var(--border); background: rgba(15, 23, 42, 0.5);">
                    <img src="${img.image_path}" style="width: 100%; height: 70px; object-fit: cover;">
                    <div style="display: flex; justify-content: space-between; padding: 4px; background: rgba(0,0,0,0.6);">
                        <button type="button" onclick="Vehicles.moveImage(${index}, -1)" style="background:none; border:none; color:white;"><i class="fas fa-chevron-left"></i></button>
                        <button type="button" onclick="Vehicles.deleteImage(${img.id})" style="background:none; border:none; color:#ef4444;"><i class="fas fa-trash-alt"></i></button>
                        <button type="button" onclick="Vehicles.moveImage(${index}, 1)" style="background:none; border:none; color:white;"><i class="fas fa-chevron-right"></i></button>
                    </div>
                </div>
            `).join('');
        },

        async moveImage(index, direction) {
            const newIndex = index + direction;
            if (newIndex < 0 || newIndex >= this.galleryDetails.length) return;

            const item = this.galleryDetails.splice(index, 1)[0];
            this.galleryDetails.splice(newIndex, 0, item);
            
            this.renderGalleryManager();
            
            const id = document.getElementById('editId').value;
            try {
                await fetch(`${API_URL}/vehicles/${id}/images/order`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ order: this.galleryDetails.map(img => img.id) })
                });
            } catch (err) { console.error('Order update failed:', err); }
        },

        async deleteImage(id) {
            if (!id) {
                alert('Error: Image ID is missing.');
                return;
            }
            if (!confirm('Delete this image permanently?')) return;
            
            try {
                const url = `${API_URL}/vehicles/images/${id}`;
                
                const res = await fetch(url, { method: 'DELETE' });
                
                if (res.ok) {
                    const data = await res.json();
                    
                    this.galleryDetails = this.galleryDetails.filter(img => img.id !== id);
                    this.renderGalleryManager();
                    
                    alert('Image deleted successfully!');
                    await this.refresh();
                } else {
                    const errData = await res.json().catch(() => ({}));
                    console.error('Mobile: Delete failed server-side:', errData);
                    alert('Failed to delete image: ' + (errData.error || 'Server error ' + res.status));
                }
            } catch (err) {
                console.error('Mobile: Network error during image deletion:', err);
                alert('Network error: Could not reach the server at ' + API_BASE);
            }
        },
        async submitForm(addAnother = false) {
            const id = document.getElementById('editId').value;
            const isEdit = !!id;

            // Validate photos for new vehicles
            if (!VehiclePhotos.validate(isEdit)) return;

            const brand = document.getElementById('vBrand').value;
            const model = document.getElementById('vModel').value;

            const formData = new FormData();
            formData.append('brand', brand);
            formData.append('model', model);
            formData.append('name', `${brand} ${model}`);
            formData.append('plate_number', document.getElementById('vPlate').value);
            formData.append('color', document.getElementById('vColor').value || '');
            formData.append('vehicle_type', document.getElementById('vType').value);
            formData.append('transmission', document.getElementById('vTrans').value);
            formData.append('fuel_type', document.getElementById('vFuel').value);
            formData.append('seats', document.getElementById('vSeats').value);
            formData.append('location', document.getElementById('vLocation').value);
            formData.append('status', document.getElementById('vStatus').value);
            formData.append('daily_rate', document.getElementById('vRate').value);

            // Append new photos
            VehiclePhotos.appendTo(formData);

            const method = isEdit ? 'PUT' : 'POST';
            const url = isEdit ? `${API_URL}/vehicles/${id}/` : `${API_URL}/vehicles/`;

            // Disable submit buttons during upload
            const submitBtn = document.getElementById('submitBtnText');
            const addAnotherBtn = document.getElementById('saveAddAnotherBtn');
            const origText = submitBtn.textContent;
            submitBtn.disabled = true;
            submitBtn.textContent = 'Saving...';
            if (addAnotherBtn) addAnotherBtn.disabled = true;

            try {
                const res = await fetch(url, { method, body: formData });
                if (res.ok) {
                    showNotification(isEdit ? 'Vehicle updated!' : 'Vehicle added!', 'success');
                    this.refresh();
                    if (addAnother) {
                        // Reset form but keep modal open ï¿½ clear photos completely
                        document.getElementById('vehicleForm').reset();
                        this.updateModels();
                        document.getElementById('vExistingGallery').style.display = 'none';
                        this.galleryDetails = [];
                        VehiclePhotos.clear();  // mandatory clear for "Save & Add Another"
                        document.getElementById('vehicleModal').scrollTop = 0;
                    } else {
                        this.closeModal();
                    }
                } else {
                    const err = await res.json().catch(() => ({}));
                    showNotification(err.error || 'Error saving vehicle', 'error');
                }
            } catch (err) {
                showNotification('Connection failed', 'error');
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = origText;
                if (addAnotherBtn) addAnotherBtn.disabled = false;
            }
        },

        closeModal() { document.getElementById('vehicleModal').style.display = 'none'; },
        async delete(id) {
            if (!confirm('Delete this vehicle?')) return;
            try {
                const res = await fetch(`${API_URL}/vehicles/${id}/`, { method: 'DELETE' });
                if (res.ok) this.refresh();
            } catch (err) { showNotification('Error deleting vehicle', 'error'); }
        },
        async edit(id) { this.openModal(id); }
    };

    // ?? VEHICLE PHOTOS MODULE ??????????????????????????????????????????????????
    // Manages up to 4 new photos selected for a vehicle add/edit operation.
    // Each entry: { file: File, dataUrl: string, label: string }
    const VehiclePhotos = {
        MAX: 4,
        LABELS: ['Main', 'Front', 'Side', 'Rear'],
        _items: [],   // { file, dataUrl, label }

        clear() {
            this._items = [];
            this._render();
            // Reset the hidden file input so the same file can be re-selected
            const inp = document.getElementById('vGalleryPicker');
            if (inp) inp.value = '';
        },

        // Called when user picks files from gallery input
        onFilePick(input) {
            const files = Array.from(input.files);
            files.forEach(f => this._addFile(f));
            input.value = ''; // allow re-picking same file
        },

        // Called by "Take Photo" button ï¿½ uses Capacitor Camera if available,
        // falls back to a hidden file input with capture="environment"
        async takePhoto() {
            const Camera = window.Capacitor?.Plugins?.Camera;
            if (Camera) {
                try {
                    const photo = await Camera.getPhoto({
                        quality: 85,
                        allowEditing: false,
                        resultType: 'base64',
                        source: 'CAMERA'
                    });
                    // Convert base64 to File
                    const byteStr = atob(photo.base64String);
                    const arr = new Uint8Array(byteStr.length);
                    for (let i = 0; i < byteStr.length; i++) arr[i] = byteStr.charCodeAt(i);
                    const blob = new Blob([arr], { type: 'image/jpeg' });
                    const file = new File([blob], `photo_${Date.now()}.jpg`, { type: 'image/jpeg' });
                    this._addFile(file);
                } catch (err) {
                    if (err.message !== 'User cancelled photos app') {
                        showNotification('Camera error: ' + err.message, 'error');
                    }
                }
            } else {
                // Fallback: trigger a file input with camera capture
                let cap = document.getElementById('vCameraCapture');
                if (!cap) {
                    cap = document.createElement('input');
                    cap.type = 'file';
                    cap.accept = 'image/*';
                    cap.capture = 'environment';
                    cap.id = 'vCameraCapture';
                    cap.style.display = 'none';
                    cap.addEventListener('change', () => {
                        Array.from(cap.files).forEach(f => this._addFile(f));
                        cap.value = '';
                    });
                    document.body.appendChild(cap);
                }
                cap.click();
            }
        },

        _addFile(file) {
            if (this._items.length >= this.MAX) {
                showNotification(`Maximum ${this.MAX} photos allowed.`, 'error');
                return;
            }
            const reader = new FileReader();
            reader.onload = (e) => {
                const label = this.LABELS[this._items.length] || `Photo ${this._items.length + 1}`;
                this._items.push({ file, dataUrl: e.target.result, label });
                this._render();
            };
            reader.readAsDataURL(file);
        },

        remove(index) {
            this._items.splice(index, 1);
            // Re-assign labels after removal
            this._items.forEach((item, i) => { item.label = this.LABELS[i] || `Photo ${i + 1}`; });
            this._render();
        },

        _render() {
            const strip = document.getElementById('vPhotoStrip');
            if (!strip) return;
            if (this._items.length === 0) {
                strip.innerHTML = '';
                return;
            }
            strip.innerHTML = this._items.map((item, i) => `
                <div style="position: relative; flex-shrink: 0;">
                    <div style="width: 80px; height: 80px; border-radius: 10px; overflow: hidden; border: 2px solid ${i === 0 ? '#00B14F' : 'rgba(255,255,255,0.1)'};">
                        <img src="${item.dataUrl}" style="width: 100%; height: 100%; object-fit: cover;">
                    </div>
                    <div style="position: absolute; bottom: 0; left: 0; right: 0; background: rgba(0,0,0,0.65); text-align: center; font-size: 0.55rem; font-weight: 700; color: ${i === 0 ? '#00B14F' : '#94a3b8'}; padding: 2px 0; border-radius: 0 0 8px 8px;">
                        ${item.label}
                    </div>
                    <button type="button" onclick="VehiclePhotos.remove(${i})"
                        style="position: absolute; top: -6px; right: -6px; width: 20px; height: 20px; background: #ef4444; border: none; border-radius: 50%; color: white; font-size: 0.6rem; display: flex; align-items: center; justify-content: center; cursor: pointer; line-height: 1;">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `).join('');
        },

        // Returns true if valid, false + shows toast if not
        validate(isEdit) {
            if (isEdit) return true; // editing: photos optional (existing gallery handles it)
            if (this._items.length === 0) {
                showNotification('Please add at least one vehicle photo (Main photo is required).', 'error');
                return false;
            }
            return true;
        },

        // Appends files to a FormData object
        appendTo(formData) {
            this._items.forEach(item => {
                formData.append('gallery', item.file);
            });
            // Set first photo as the main vehicle_image via URL after upload
            // (server will handle gallery[0] as primary)
        }
    };

    // Form Handler
    document.getElementById('vehicleForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        await Vehicles.submitForm(false);
    });

    function toggleDrawer(show) {
        const drawer = document.getElementById('sideDrawer');
        const overlay = document.getElementById('drawerOverlay');
        if (show) {
            overlay.style.display = 'block';
            setTimeout(() => {
                overlay.style.opacity = '1';
                drawer.style.left = '0';
            }, 10);
        } else {
            drawer.style.left = '-280px';
            overlay.style.opacity = '0';
            setTimeout(() => overlay.style.display = 'none', 300);
        }
    }

    function navTo(tabId) {
        switchTab(tabId);
        toggleDrawer(false);
    }

    let currentTab = 'dashboard';
    function switchTab(tabId) {
        currentTab = tabId;
        // Stop ActiveNow timers when leaving bookings tab
        if (tabId !== 'bookings' && typeof ActiveNow !== 'undefined') ActiveNow.stop();
        // Stop chat polling when leaving chat tab
        if (tabId !== 'chat' && typeof AdminChat !== 'undefined') AdminChat.stopPolling();
        try {
            document.querySelectorAll('.tab-content').forEach(t => t.style.display = 'none');
            document.querySelectorAll('.nav-item, .drawer-item').forEach(l => l.classList.remove('active'));
            
            const target = document.getElementById(tabId);
            if (target) target.style.display = 'block';
            
            document.querySelectorAll(`[data-tab="${tabId}"]`).forEach(el => el.classList.add('active'));
            
            // Only load data if not already loaded (prevents "Fetching..." flash on every tab switch)
            if (tabId === 'vehicles' && typeof Vehicles !== 'undefined' && Vehicles.data.length === 0) Vehicles.refresh();
            if (tabId === 'bookings' && typeof Bookings !== 'undefined' && Bookings.data.length === 0) Bookings.refresh();
            if (tabId === 'drivers' && typeof Drivers !== 'undefined' && Drivers.data.length === 0) Drivers.refresh();
            if (tabId === 'verifications' && typeof Verifications !== 'undefined' && Verifications.data.length === 0) Verifications.refresh();
            if (tabId === 'tickets' && typeof Tickets !== 'undefined' && Tickets.data.length === 0) Tickets.refresh();
            if (tabId === 'instructions' && typeof Instructions !== 'undefined' && Instructions.data.length === 0) Instructions.refresh();
            if (tabId === 'staff' && typeof Staff !== 'undefined' && Staff.data.length === 0) Staff.refresh();
            if (tabId === 'reports' && typeof Reports !== 'undefined' && !Reports._loaded) {
                // Set default date range (current month) on first open
                const now = new Date();
                const to = now.toISOString().split('T')[0];
                const from = new Date(now.getFullYear(), now.getMonth(), 1).toISOString().split('T')[0];
                document.getElementById('rptDateFrom').value = from;
                document.getElementById('rptDateTo').value = to;
                Reports.refresh();
            }
            if (tabId === 'activity' && typeof Activity !== 'undefined' && Activity.data.length === 0) Activity.refresh();
            if (tabId === 'users' && typeof UserMgmt !== 'undefined' && UserMgmt._all.length === 0) UserMgmt.refresh();
            if (tabId === 'chat' && typeof AdminChat !== 'undefined') {
                AdminChat.loadInbox();
                // Clear nav badge when entering chat
                const b = document.getElementById('adminChatNavBadge');
                if (b) b.style.display = 'none';
            }

            if (tabId === 'gps' && typeof GPS !== 'undefined') GPS.startLive();
            else if (typeof GPS !== 'undefined') GPS.stopLive();
            
            if (tabId === 'settings') {
                const user = adminAuth.getUser();
                if (user) {
                    if(document.getElementById('settingsAvatar')) document.getElementById('settingsAvatar').textContent = user.full_name[0].toUpperCase();
                    if(document.getElementById('settingsName')) document.getElementById('settingsName').textContent = user.full_name;
                    if(document.getElementById('settingsRole')) document.getElementById('settingsRole').textContent = user.role.replace('_', ' ').toUpperCase();
                    if(document.getElementById('settingsEmail')) document.getElementById('settingsEmail').textContent = user.email || 'admin@autoride.com';
                    if (typeof Settings !== 'undefined') Settings.fetch();
                }
            }
        } catch (err) {
            console.error('Error in switchTab:', err);
        }
    }

    const Bookings = {
        data: [],
        async refresh() {
            const list = document.getElementById('bookingsList');
            if (!list.innerHTML.trim() || list.innerHTML.includes('Loading bookings')) {
                list.innerHTML = '<div style="text-align: center; padding: 40px; color: var(--text-muted);">Loading bookings...</div>';
            }
            try {
                // Fetch Stats and List in parallel
                const user = adminAuth.getUser();
                const adminId = user ? user.id : '';

                const [statsRes, listRes] = await Promise.all([
                    fetch(`${API_URL}/admin/stats?admin_id=${adminId}`),
                    fetch(`${API_URL}/bookings?admin_id=${adminId}`)
                ]);

                // Update booking counts from stats
                if (statsRes.ok) {
                    const stats = await statsRes.json();
                    const breakdown = stats.bookingsByStatus || {};
                    document.getElementById('bookTotal').textContent = stats.total_bookings || 0;
                    document.getElementById('bookConfirmed').textContent = (breakdown['confirmed'] || 0) + (breakdown['approved'] || 0);
                    document.getElementById('bookPending').textContent = breakdown['pending'] || 0;
                    document.getElementById('bookCancelled').textContent = (breakdown['cancelled'] || 0) + (breakdown['rejected'] || 0);
                }

                if (!listRes.ok) throw new Error(`Server error: ${listRes.status}`);
                this.data = await listRes.json();
                this.render();
                ActiveNow.render(this.data);
            } catch (err) {
                console.error('Bookings Error:', err);
                list.innerHTML = `<div style="text-align: center; padding: 40px; color: var(--danger);">Error: ${err.message}<br><button onclick="Bookings.refresh()" style="margin-top:10px; color:white; background:var(--primary); border:none; padding:8px 15px; border-radius:5px;">Retry</button></div>`;
            }
        },
        render() {
            const list = document.getElementById('bookingsList');
            if (this.data.length === 0) {
                list.innerHTML = `
                    <div style="text-align: center; padding: 60px 20px; background: var(--surface); border-radius: var(--radius-lg); border: 1px solid var(--border);">
                        <i class="fas fa-calendar-times" style="font-size: 3rem; color: var(--text-muted); opacity: 0.3; margin-bottom: 15px;"></i>
                        <p style="color: var(--text-muted); font-weight: 600;">No bookings found.</p>
                    </div>`;
                return;
            }
            list.innerHTML = this.data.map(b => `
                <div class="stat-card" style="padding: 20px; margin-bottom: 16px;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px;">
                        <div>
                            <span style="font-size: 0.7rem; color: var(--text-muted); font-weight: 800; letter-spacing: 0.5px;">#${b.id}</span>
                            <h4 style="font-size: 1.1rem; font-weight: 800; margin-top: 2px;">${b.customer_name || 'Guest User'}</h4>
                        </div>
                        <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 6px;">
                            <span class="pill ${this.getPillClass(b.status)}">
                                ${b.status || 'PENDING'}
                            </span>
                            ${b.payment_status === 'Refund Pending' ? 
                                `<span class="pill danger" style="font-size: 0.55rem; padding: 2px 8px;">REFUND NEEDED</span>` : 
                                (b.payment_status === 'Paid' ? `<span class="pill success" style="font-size: 0.55rem; padding: 2px 8px;">PAID</span>` : '')
                            }
                        </div>
                    </div>
                    
                    <div style="display: flex; gap: 14px; margin-bottom: 20px; background: rgba(255,255,255,0.03); padding: 12px; border-radius: 14px; border: 1px solid var(--border);">
                        <div style="width: 44px; height: 44px; background: rgba(99, 102, 241, 0.1); border-radius: 12px; display: flex; align-items: center; justify-content: center; border: 1px solid rgba(99, 102, 241, 0.2);">
                            <i class="fas fa-car" style="font-size: 1.2rem; color: var(--primary);"></i>
                        </div>
                        <div style="flex: 1;">
                            <p style="font-size: 0.9rem; font-weight: 700; color: var(--text-main);">${b.car || 'Unknown Vehicle'}</p>
                            <p style="font-size: 0.75rem; color: var(--text-muted); font-weight: 500;">
                                <i class="far fa-calendar-alt" style="margin-right: 4px;"></i>
                                ${b.start_date ? new Date(b.start_date).toLocaleDateString() : 'N/A'} - ${b.end_date ? new Date(b.end_date).toLocaleDateString() : 'N/A'}
                            </p>
                        </div>
                    </div>
 
                    <div style="display: flex; justify-content: space-between; align-items: center; padding-top: 16px; border-top: 1px solid var(--border);">
                        <div style="font-size: 1.2rem; font-weight: 900; color: var(--success); letter-spacing: -0.5px;">₱${b.total_price ? b.total_price.toLocaleString() : '0'}</div>
                        <div style="display: flex; gap: 8px;">
                            <button onclick="Bookings.view(${b.id})" class="btn-outline" style="padding: 10px 14px; font-size: 0.75rem; border-radius: 12px; min-width: 70px;">Details</button>
                            
                            <!-- Inspection Buttons -->
                            ${b.status?.toLowerCase() === 'confirmed' ? `
                                <button onclick="Inspections.openModal(${b.id}, 'pickup')" class="btn-premium" style="padding: 10px 14px; font-size: 0.75rem; border-radius: 12px; background: var(--amber); box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3); display: flex; align-items: center; gap: 5px;">
                                    <i class="fas fa-search-plus"></i> Pickup Inspect
                                </button>
                            ` : ''}
                            
                            ${(b.status?.toLowerCase() === 'picked up' || b.status?.toLowerCase() === 'ongoing') ? `
                                <button onclick="Inspections.openModal(${b.id}, 'return')" class="btn-premium" style="padding: 10px 14px; font-size: 0.75rem; border-radius: 12px; background: var(--success); box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3); display: flex; align-items: center; gap: 5px;">
                                    <i class="fas fa-clipboard-check"></i> Return Inspect
                                </button>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `).join('');
        },
        getPillClass(s) {
            const status = s?.toLowerCase();
            if (status === 'confirmed') return 'confirmed';
            if (status === 'pending') return 'pending';
            if (status === 'cancelled' || status === 'rejected') return 'cancelled';
            if (status === 'ongoing' || status === 'picked up') return 'success';
            return '';
        },

        async markPaid(id) {
            if (!confirm('Mark this booking as FULLY PAID? \nThis means you have received the remaining balance in CASH over the counter.')) return;
            try {
                const res = await fetch(`${API_BASE}/api/admin/bookings/${id}/mark-paid`, { method: 'POST' });
                if (res.ok) {
                    showNotification('Booking marked as Fully Paid!', 'success');
                    document.getElementById('bookingDetailsModal').style.display = 'none';
                    this.refresh();
                } else {
                    const data = await res.json();
                    showNotification(data.error || 'Failed to update payment', 'error');
                }
            } catch (err) { showNotification('Network error', 'error'); }
        },

        async cancel(id) {
            const reason = prompt('Enter cancellation reason (optional):') || 'Cancelled by admin';
            try {
                const res = await fetch(`${API_URL}/bookings/${id}/cancel`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ reason: reason })
                });
                if (res.ok) {
                    showNotification('Booking Cancelled!', 'success');
                    document.getElementById('bookingDetailsModal').style.display = 'none';
                    this.refresh();
                } else {
                    const data = await res.json();
                    showNotification(data.error || 'Failed to cancel', 'error');
                }
            } catch (err) { showNotification('Network error', 'error'); }
        },

        async approve(id) {
            if (!confirm('Approve this booking?')) return;
            try {
                const res = await fetch(`${API_URL}/bookings/${id}/approve`, { method: 'PUT' });
                if (res.ok) {
                    showNotification('Booking Approved!', 'success');
                    document.getElementById('bookingDetailsModal').style.display = 'none';
                    this.refresh();
                } else {
                    const data = await res.json();
                    showNotification(data.error || 'Failed to approve', 'error');
                }
            } catch (err) { showNotification('Network error', 'error'); }
        },

        async reject(id) {
            const reason = prompt('Enter rejection reason:');
            if (!reason) return;
            try {
                const res = await fetch(`${API_URL}/bookings/${id}/reject`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ reason: reason })
                });
                if (res.ok) {
                    showNotification('Booking Rejected!', 'success');
                    document.getElementById('bookingDetailsModal').style.display = 'none';
                    this.refresh();
                } else {
                    const data = await res.json();
                    showNotification(data.error || 'Failed to reject', 'error');
                }
            } catch (err) { showNotification('Network error', 'error'); }
        },

        async pickup(id) {
            if (!confirm('Confirm vehicle has been picked up?')) return;
            try {
                const res = await fetch(`${API_URL}/bookings/${id}/pickup`, { method: 'PUT' });
                if (res.ok) {
                    showNotification('Marked as Picked Up!', 'success');
                    document.getElementById('bookingDetailsModal').style.display = 'none';
                    this.refresh();
                } else {
                    const data = await res.json();
                    showNotification(data.error || 'Failed', 'error');
                }
            } catch (err) { showNotification('Network error', 'error'); }
        },

        async complete(id) {
            if (!confirm('Confirm vehicle has been returned?')) return;
            try {
                const res = await fetch(`${API_URL}/bookings/${id}/complete`, { method: 'PUT' });
                if (res.ok) {
                    showNotification('Booking Completed!', 'success');
                    document.getElementById('bookingDetailsModal').style.display = 'none';
                    this.refresh();
                } else {
                    const data = await res.json();
                    showNotification(data.error || 'Failed', 'error');
                }
            } catch (err) { showNotification('Network error', 'error'); }
        },

        async view(id) {
            const b = this.data.find(x => x.id === id);
            if (!b) return;
            
            const isCancellable = ['Pending', 'Confirmed', 'Approved', 'Picked Up', 'Ongoing'].includes(b.status);
            const isApprovable = (b.status === 'Pending');

            // Fetch license details for this booking
            let licenseHtml = '<p style="font-size: 0.85rem; color: var(--text-muted);">No license details available.</p>';
            try {
                const licRes = await fetch(`${API_BASE}/api/admin/bookings/${id}/license-details`);
                if (licRes.ok) {
                    const lData = await licRes.json();
                    if (lData && lData.license_number) {
                        licenseHtml = `
                            <div style="font-size: 0.95rem; line-height: 1.6; color: #1e293b; margin-bottom: 15px;">
                                <div>Full Name: ${lData.full_name || '-'}</div>
                                <div>DOB: ${lData.date_of_birth || '-'}</div>
                                <div>License #: ${lData.license_number}</div>
                                <div>Expiry: ${lData.expiry_date || '-'}</div>
                            </div>
                            <div style="display:flex; gap:10px;">
                                <button onclick="viewLicenseImage('${lData.license_front_url}')" ${!lData.license_front_url ? 'disabled' : ''} style="flex:1;padding:12px;font-size:0.9rem;border-radius:8px;border:1px solid #e2e8f0;background:white;color:#64748b;font-weight:600;">Front Image</button>
                                <button onclick="viewLicenseImage('${lData.license_back_url}')" ${!lData.license_back_url ? 'disabled' : ''} style="flex:1;padding:12px;font-size:0.9rem;border-radius:8px;border:1px solid #e2e8f0;background:white;color:#64748b;font-weight:600;">Back Image</button>
                            </div>
                            </div> <!-- close license wrapper -->
                            
                            <div style="margin-top: 25px; font-size: 0.95rem; line-height: 1.6; color: #1e293b;">
                                <h3 style="font-size: 1.05rem; color: #0f172a; font-weight: 800; margin-bottom: 10px;">Emergency Contact</h3>
                                <div>Name: ${lData.emergency_contact_name || '-'}</div>
                                <div>Phone: ${lData.emergency_contact_phone || '-'}</div>
                                <div>Rel: ${lData.emergency_contact_relation || '-'}</div>
                            </div>
                            <!-- dummy closing to balance template -->
                            <div style="display:none">
                        `;
                    }
                }
            } catch (e) { console.error('License fetch error:', e); }

            const paymentBg = b.payment_status === 'Paid' ? '#dcfce7' : '#fee2e2';
            const paymentColor = b.payment_status === 'Paid' ? '#16a34a' : '#ef4444';
            const statusBg = ['Confirmed', 'Approved', 'Picked Up', 'Ongoing'].includes(b.status) ? '#dcfce7' : (['Pending'].includes(b.status) ? '#fef3c7' : '#fee2e2');
            const statusColor = ['Confirmed', 'Approved', 'Picked Up', 'Ongoing'].includes(b.status) ? '#16a34a' : (['Pending'].includes(b.status) ? '#d97706' : '#ef4444');

            const content = `
                <div style="display: flex; flex-direction: column; gap: 24px; background: white; padding-bottom: 20px;">
                    <h2 style="font-size: 1.8rem; font-weight: 900; color: #0f172a; margin: 0; letter-spacing: -0.5px;">Booking Details #${b.id}</h2>

                    <div style="display: grid; grid-template-columns: 1fr 1.2fr 1fr; gap: 15px 10px; align-items: start;">
                        <!-- Row 1 -->
                        <div>
                            <label style="color: #64748b; font-size: 0.7rem; font-weight: 700; text-transform: uppercase;">Customer</label>
                            <div style="font-weight: 500; font-size: 0.95rem; color: #0f172a; margin-top: 4px; word-break: break-word;">${b.customer_name || 'Guest'}</div>
                        </div>
                        <div>
                            <label style="color: #64748b; font-size: 0.7rem; font-weight: 700; text-transform: uppercase;">Vehicle</label>
                            <div style="font-weight: 500; font-size: 0.95rem; color: #0f172a; margin-top: 4px; word-break: break-word;">${b.car || '-'}</div>
                        </div>
                        <div>
                            <label style="color: #64748b; font-size: 0.7rem; font-weight: 700; text-transform: uppercase;">Rental Period</label>
                            <div style="font-weight: 500; font-size: 0.95rem; color: #0f172a; margin-top: 4px; word-break: break-word; line-height: 1.4;">${b.start_date ? new Date(b.start_date).toLocaleDateString() : '-'} to<br>${b.end_date ? new Date(b.end_date).toLocaleDateString() : '-'}</div>
                        </div>
                        
                        <!-- Row 2 -->
                        <div>
                            <label style="color: #64748b; font-size: 0.7rem; font-weight: 700; text-transform: uppercase;">Payment Status</label>
                            <div style="margin-top: 6px;">
                                <span style="background: ${paymentBg}; color: ${paymentColor}; padding: 4px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 700;">${(b.payment_status || 'Unpaid')}</span>
                            </div>
                        </div>
                        <div>
                            <label style="color: #64748b; font-size: 0.7rem; font-weight: 700; text-transform: uppercase;">Total Price</label>
                            <div style="font-weight: 600; color: #0f172a; font-size: 0.95rem; margin-top: 6px;">₱${b.total_price ? b.total_price.toFixed(2) : '0.00'}</div>
                        </div>
                        <div>
                            <label style="color: #64748b; font-size: 0.7rem; font-weight: 700; text-transform: uppercase;">Booking Status</label>
                            <div style="margin-top: 6px;">
                                <span style="background: ${statusBg}; color: ${statusColor}; padding: 4px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase;">${(b.status || 'PENDING')}</span>
                            </div>
                        </div>
                    </div>

                    <!-- INSPECTION SECTION -->
                    <div style="border: 1px solid #00B14F; padding: 18px; border-radius: 12px; margin-top: 5px;">
                        <h3 style="font-size: 1.1rem; color: #00B14F; font-weight: 800; margin-bottom: 15px;">Driver's License Details</h3>
                        <div id="bookingLicenseDetailsWrapper">
                            ${licenseHtml}
                        </div>
                    </div>

                    <div style="margin-top: 10px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                            <h3 style="font-size: 1.1rem; color: #0f172a; font-weight: 800;">Vehicle Inspections</h3>
                            <button id="mBtnAddInsp" style="padding: 8px 14px; background: #00B14F; border: none; color: white; border-radius: 8px; font-weight: 600; font-size: 0.8rem;">+ New Inspection</button>
                        </div>

                        <div id="mInspList" style="min-height: 40px; border-bottom: 1px solid #f1f5f9; padding-bottom: 15px;">
                            <p style="font-size: 0.85rem; color: #94a3b8; text-align: center; margin: 20px 0;">No inspections yet.</p>
                        </div>
                    </div>

                    <div id="mInspForm" style="display: none; background: #f8fafc; padding: 15px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 20px;">
                        <h4 style="font-size: 0.95rem; color: #0f172a; margin-bottom: 15px; font-weight: 800;">Add New Inspection</h4>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px;">
                            <select id="mfInspType" style="padding: 12px; background: white; color: #0f172a; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 0.85rem;">
                                <option value="pickup">Pickup</option>
                                <option value="return">Return</option>
                            </select>
                            <input type="number" id="mfInspMileage" placeholder="Mileage (km)" style="padding: 12px; background: white; color: #0f172a; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 0.85rem;">
                        </div>
                        <select id="mfInspFuel" style="width: 100%; padding: 12px; background: white; color: #0f172a; border: 1px solid #cbd5e1; border-radius: 8px; margin-bottom: 10px; font-size: 0.85rem;">
                            <option value="Full">Full Tank</option>
                            <option value="Empty">Empty</option>
                        </select>
                        <input type="file" id="mfInspPhotos" multiple accept="image/*" style="font-size: 0.8rem; color: #64748b; width: 100%; margin-bottom: 10px;">
                        <textarea id="mfInspNotes" placeholder="Condition Notes..." style="width: 100%; height: 70px; background: white; color: #0f172a; border: 1px solid #cbd5e1; border-radius: 8px; margin-bottom: 10px; padding: 12px; font-size: 0.85rem;"></textarea>
                        <div style="display: flex; gap: 10px;">
                            <button id="mBtnCancelInsp" class="btn-outline" style="flex: 1; padding: 12px; font-size: 0.85rem; border-color: #cbd5e1; color: #64748b;">Cancel</button>
                            <button id="mBtnSaveInsp" class="btn-premium" style="flex: 1; padding: 12px; font-size: 0.85rem; background: #00B14F; color: white; border: none;">Save</button>
                        </div>
                    </div>

                    <div style="display: flex; flex-direction: column; gap: 12px; margin-top: 5px;">
                        ${isApprovable ? `
                            <button onclick="Bookings.approve(${b.id})" style="width: 100%; background: #00B14F; color: white; border: none; padding: 14px; border-radius: 8px; font-weight: 600; font-size: 0.95rem;">Approve Booking</button>
                            <button onclick="Bookings.reject(${b.id})" style="width: 100%; background: white; color: #ef4444; border: 1px solid #ef4444; padding: 14px; border-radius: 8px; font-weight: 600; font-size: 0.95rem;">Reject Booking</button>
                        ` : ''}

                        ${b.status === 'Confirmed' || b.status === 'Approved' ? `
                            <button onclick="Bookings.pickup(${b.id})" style="width: 100%; background: #00B14F; color: white; border: none; padding: 14px; border-radius: 8px; font-weight: 600; font-size: 0.95rem; display: flex; align-items: center; justify-content: center; gap: 8px;"><i class="fas fa-car"></i> Mark as Picked Up</button>
                        ` : ''}

                        ${b.status === 'Picked Up' ? `
                            <button onclick="Bookings.complete(${b.id})" style="width: 100%; background: #00B14F; color: white; border: none; padding: 14px; border-radius: 8px; font-weight: 600; font-size: 0.95rem; display: flex; align-items: center; justify-content: center; gap: 8px;"><i class="fas fa-check-circle"></i> Complete Booking (Returned)</button>
                        ` : ''}

                        ${b.payment_status === 'Partially Paid' ? `
                            <button onclick="Bookings.markPaid(${b.id})" style="width: 100%; background: #00B14F; color: white; border: none; padding: 14px; border-radius: 8px; font-weight: 600; font-size: 0.95rem;">Mark as Fully Paid</button>
                        ` : ''}

                        <div style="display: flex; gap: 10px;">
                            <button onclick="window.open('${API_BASE}/api/bookings/${b.id}/receipt', '_blank')" style="flex: 1; padding: 14px; font-size: 0.85rem; background: white; border: 1px solid #00B14F; color: #00B14F; border-radius: 8px; font-weight: 600;">Download Receipt</button>
                            ${isCancellable ? `
                                <button onclick="Bookings.cancel(${b.id})" style="flex: 1; padding: 14px; font-size: 0.85rem; background: white; border: 1px solid #00B14F; color: #00B14F; border-radius: 8px; font-weight: 600;">Cancel Booking</button>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `;
            document.getElementById('bookingDetailContent').innerHTML = content;
            document.getElementById('bookingDetailsModal').style.display = 'flex'; // Use flex for centering

            // Attach Inspection Events
            const btnAdd = document.getElementById('mBtnAddInsp');
            const form = document.getElementById('mInspForm');
            const btnCancel = document.getElementById('mBtnCancelInsp');
            const btnSave = document.getElementById('mBtnSaveInsp');

            btnAdd.onclick = () => { form.style.display = 'block'; btnAdd.style.display = 'none'; };
            btnCancel.onclick = () => { form.style.display = 'none'; btnAdd.style.display = 'block'; };
            btnSave.onclick = () => this.saveInspection(id);

            this.fetchInspections(id);
        },

        async uploadRefundProof(bookingId) {
            const fileInput = document.getElementById('mRefundProofFile');
            if (!fileInput.files.length) {
                alert('Please select an image first');
                return;
            }

            const formData = new FormData();
            formData.append('booking_id', bookingId);
            formData.append('admin_id', 1); // Mock admin_id
            formData.append('proof', fileInput.files[0]);

            const btn = event.target;
            btn.disabled = true;
            btn.textContent = 'Uploading...';

            try {
                const res = await fetch(`${API_BASE}/api/admin/upload-refund-proof`, {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.error || 'Upload failed');

                showNotification('Refund proof uploaded!', 'success');
                this.refresh(); // Refresh main list
                this.view(bookingId); // Refresh modal
            } catch (err) {
                alert(err.message);
            } finally {
                btn.disabled = false;
                btn.textContent = 'Submit Proof';
            }
        },

        async fetchInspections(bookingId) {
            const list = document.getElementById('mInspList');
            list.innerHTML = '<div style="font-size:0.7rem; opacity:0.5;">Loading...</div>';
            try {
                const res = await fetch(`${API_BASE}/api/inspections/${bookingId}`);
                const data = await res.json();
                this.renderInspections(data);
            } catch (err) {
                list.innerHTML = '<div style="font-size:0.7rem; color:var(--danger);">Error loading inspections.</div>';
            }
        },

        renderInspections(inspections) {
            const list = document.getElementById('mInspList');
            if (!inspections || inspections.length === 0) {
                list.innerHTML = '<div style="font-size:0.7rem; opacity:0.5;">No inspections yet.</div>';
                return;
            }

            list.innerHTML = inspections.map(insp => `
                <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.05); border-radius: 10px; padding: 10px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                        <strong style="text-transform: uppercase; color: #60a5fa; font-size: 0.7rem;">${insp.type}</strong>
                        <span style="font-size: 0.6rem; opacity: 0.5;">${new Date(insp.created_at).toLocaleDateString()}</span>
                    </div>
                    <div style="display: flex; gap: 15px; font-size: 0.7rem; margin-bottom: 8px;">
                        <span>Mileage: <strong>${insp.mileage}km</strong></span>
                        <span>Fuel: <strong>${insp.fuel_level}</strong></span>
                    </div>
                    ${insp.photos && Array.isArray(insp.photos) ? `
                        <div style="display: flex; gap: 5px; overflow-x: auto; padding-bottom: 5px; margin-bottom: 5px;">
                            ${insp.photos.map(p => `<img src="${API_BASE}${p}" style="height: 45px; border-radius: 6px;" onclick="window.open('${API_BASE}${p}', '_blank')">`).join('')}
                        </div>
                    ` : ''}
                    ${insp.notes ? `<p style="font-size: 0.65rem; color: var(--text-muted); border-top: 1px solid rgba(255,255,255,0.05); padding-top: 5px; margin: 0;">${insp.notes}</p>` : ''}
                </div>
            `).join('');
        },

        async saveInspection(bookingId) {
            const user = adminAuth.getUser();
            const mileage = document.getElementById('mfInspMileage').value;
            const photoInput = document.getElementById('mfInspPhotos');

            if (!mileage) { alert('Enter mileage'); return; }

            const formData = new FormData();
            formData.append('booking_id', bookingId);
            formData.append('admin_id', user.id);
            formData.append('type', document.getElementById('mfInspType').value);
            formData.append('mileage', mileage);
            formData.append('fuel_level', document.getElementById('mfInspFuel').value);
            formData.append('notes', document.getElementById('mfInspNotes').value);

            if (photoInput.files.length > 0) {
                for (let i = 0; i < photoInput.files.length; i++) {
                    formData.append('photos', photoInput.files[i]);
                }
            }

            const saveBtn = document.getElementById('mBtnSaveInsp');
            saveBtn.disabled = true;
            saveBtn.textContent = 'Saving...';

            try {
                const res = await fetch(`${API_BASE}/api/inspections/submit`, {
                    method: 'POST',
                    body: formData
                });

                if (res.ok) {
                    showNotification('Inspection saved!', 'success');
                    document.getElementById('mInspForm').style.display = 'none';
                    document.getElementById('mBtnAddInsp').style.display = 'block';
                    this.fetchInspections(bookingId);
                } else {
                    alert('Failed to save inspection');
                }
            } catch (err) { alert('Error saving'); }
            finally {
                saveBtn.disabled = false;
                saveBtn.textContent = 'Save';
            }
        },
        async pickup(id) {
            if (!confirm('Mark this vehicle as picked up?')) return;
            try {
                const res = await apiFetch(`bookings/${id}/pickup`, { method: 'PUT' });
                if (res.ok) { showNotification('Vehicle picked up!', 'success'); this.refresh(); }
                else { showNotification('Failed: ' + res.status, 'error'); }
            } catch (err) { showNotification('Action failed: ' + err.message, 'error'); }
        },
        async complete(id) {
            if (!confirm('Mark this vehicle as returned?')) return;
            try {
                const res = await apiFetch(`bookings/${id}/complete`, { method: 'PUT' });
                if (res.ok) { showNotification('Vehicle returned successfully!', 'success'); this.refresh(); }
                else { showNotification('Failed: ' + res.status, 'error'); }
            } catch (err) { showNotification('Action failed: ' + err.message, 'error'); }
        },
        /*
        async assign(id) {
            this.currentBookingId = id;
            const select = document.getElementById('assignDriverSelect');
            select.innerHTML = '<option value="">Loading drivers...</option>';
            document.getElementById('assignDriverModal').style.display = 'flex';

            try {
                const res = await fetch(`${API_BASE}/drivers`);
                const drivers = await res.json();
                const approved = drivers.filter(d => d.status === 'Approved');

                if (approved.length === 0) {
                    select.innerHTML = '<option value="">No approved drivers found</option>';
                } else {
                    select.innerHTML = '<option value="">Select a driver...</option>' + 
                        approved.map(d => `<option value="${d.id}">${d.full_name}</option>`).join('');
                }
            } catch (err) {
                select.innerHTML = '<option value="">Failed to load drivers</option>';
            }
        },
        async saveAssign() {
            const driverId = document.getElementById('assignDriverSelect').value;
            if (!driverId) { alert('Please select a driver'); return; }

            try {
                const res = await fetch(`${API_BASE}/admin/bookings/${this.currentBookingId}/assign_driver`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ driver_id: parseInt(driverId) })
                });

                if (res.ok) {
                    alert('Driver assigned successfully!');
                    document.getElementById('assignDriverModal').style.display = 'none';
                    this.refresh();
                } else {
                    const data = await res.json();
                    alert(data.error || 'Failed to assign driver');
                }
            } catch (err) { alert('Network error'); }
        }
        */
    };

    // --- DRIVERS MODULE (FULL SYNC) ---
    const Drivers = {
        data: [],
        async refresh() {
            const list = document.getElementById('driversList');
            try {
                this.fetchWage();
                const res = await fetch(`${API_BASE}/drivers`);
                this.data = await res.json();
                this.applyFilters();
            } catch (err) {
                list.innerHTML = `<div style="text-align: center; padding: 40px; color: var(--danger);">Error loading drivers.</div>`;
            }
        },
        async fetchWage() {
            try {
                const res = await fetch(`${API_BASE}/settings/driver_wage`);
                if (res.ok) {
                    const data = await res.json();
                    if (data.value) document.getElementById('driverWageInput').value = data.value;
                }
            } catch (err) {}
        },
        async saveWage() {
            const val = document.getElementById('driverWageInput').value;
            try {
                const res = await fetch(`${API_BASE}/settings/driver_wage`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ value: val })
                });
                if (res.ok) alert('Wage setting saved!');
            } catch (err) { alert('Failed to save wage'); }
        },
        applyFilters() {
            const query = document.getElementById('driverSearchInput').value.toLowerCase().trim();
            const status = document.getElementById('driverStatusFilter').value;
            let filtered = this.data;
            if (status !== 'all') filtered = filtered.filter(d => d.status === status);
            if (query) {
                filtered = filtered.filter(d => 
                    (d.full_name && d.full_name.toLowerCase().includes(query)) ||
                    (d.license_number && d.license_number.toLowerCase().includes(query))
                );
            }
            this.render(filtered);
        },
        render(drivers) {
            const list = document.getElementById('driversList');
            if (drivers.length === 0) {
                list.innerHTML = '<div style="text-align: center; padding: 40px; color: var(--text-muted);">No drivers found.</div>';
                return;
            }
            list.innerHTML = drivers.map(d => `
                <div class="stat-card" style="padding: 18px; margin-bottom: 12px; border: 1px solid var(--border);">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px;">
                        <div>
                            <h4 style="font-size: 1rem;">${d.full_name}</h4>
                            <p style="font-size: 0.75rem; color: var(--text-muted);">${d.license_number}</p>
                        </div>
                        <span style="font-size: 0.6rem; padding: 4px 8px; border-radius: 10px; background: ${this.getStatusBg(d.status)}; color: ${this.getStatusColor(d.status)}; font-weight: 800; text-transform: uppercase;">
                            ${d.status || 'PENDING'}
                        </span>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.05);">
                        <div style="font-size: 0.8rem; color: var(--text-muted);"><i class="fas fa-phone" style="margin-right: 5px;"></i> ${d.contact_info}</div>
                        <div style="display: flex; gap: 8px;">
                            ${d.license_document ? `<button onclick="window.open('${API_BASE}/uploads/${d.license_document}')" style="background: rgba(0,177,79,0.1); border: 1px solid var(--primary); color: var(--primary); padding: 5px 10px; border-radius: 6px; font-size: 0.7rem; font-weight: 600;">License</button>` : ''}
                            ${d.status === 'Pending' ? `
                                <button onclick="Drivers.approve(${d.id})" style="background: var(--success); border: none; color: white; padding: 5px 10px; border-radius: 6px; font-size: 0.7rem; font-weight: 600;">Approve</button>
                                <button onclick="Drivers.reject(${d.id})" style="background: var(--danger); border: none; color: white; padding: 5px 10px; border-radius: 6px; font-size: 0.7rem; font-weight: 600;">Reject</button>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `).join('');
        },
        getStatusBg(s) {
            if (s === 'Approved') return 'rgba(16, 185, 129, 0.1)';
            if (s === 'Pending') return 'rgba(251, 191, 36, 0.1)';
            return 'rgba(239, 68, 68, 0.1)';
        },
        getStatusColor(s) {
            if (s === 'Approved') return 'var(--success)';
            if (s === 'Pending') return '#f59e0b';
            return 'var(--danger)';
        },
        async approve(id) {
            if (!confirm('Approve this driver?')) return;
            try {
                const res = await fetch(`${API_BASE}/drivers/${id}/approve`, { method: 'PUT' });
                if (res.ok) { alert('Driver approved!'); this.refresh(); }
            } catch (err) { alert('Action failed'); }
        },
        async reject(id) {
            const reason = prompt("Reason for rejection:");
            if (!reason) return;
            try {
                const res = await fetch(`${API_BASE}/drivers/${id}/reject`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ reason })
                });
                if (res.ok) { alert('Driver rejected'); this.refresh(); }
            } catch (err) { alert('Action failed'); }
        }
    };

    // --- VERIFICATIONS MODULE ---
    const Verifications = {
        data: [],
        async refresh() {
            const list = document.getElementById('verificationsList');
            if (!list) return;
            if (!list.innerHTML.trim() || list.innerHTML.includes('Fetching')) {
                list.innerHTML = '<div style="text-align: center; padding: 40px; color: var(--text-muted);">Loading verifications...</div>';
            }
            
            try {
                const url = `${API_URL}/admin/pending-verifications`;
                const res = await fetch(url);
                
                if (!res.ok) {
                    const errTxt = await res.text();
                    alert('API Error: ' + res.status + '\n' + errTxt);
                    list.innerHTML = '<div style="text-align: center; padding: 40px; color: var(--danger);">Server Error ' + res.status + '</div>';
                    return;
                }
                
                this.data = await res.json();
                this.render();
            } catch (err) {
                console.error('Refresh Error:', err);
                console.error('Connection Error:', err.message);
                list.innerHTML = '<div style="text-align: center; padding: 40px; color: var(--danger);"><i class="fas fa-wifi" style="font-size:2rem; margin-bottom:10px;"></i><br>Connection Error. Please retry.</div>';
            }
        },
        render() {
            const list = document.getElementById('verificationsList');
            if (!this.data || this.data.length === 0) {
                list.innerHTML = `
                    <div style="text-align: center; padding: 60px 20px; background: var(--surface); border-radius: var(--radius-lg); border: 1px solid var(--border);">
                        <i class="fas fa-user-shield" style="font-size: 3rem; color: var(--text-muted); opacity: 0.3; margin-bottom: 15px;"></i>
                        <p style="color: var(--text-muted); font-weight: 600;">No pending verifications.</p>
                    </div>`;
                return;
            }
            list.innerHTML = this.data.map(v => {
                const name = v.full_name || 'Unnamed User';
                const initial = name[0] ? name[0].toUpperCase() : '?';
                const licenseUrl = v.license_image || v.license_image_url || '';

                // License detail rows
                const hasDetails = v.license_number || v.license_type || v.license_expiry;
                const detailsHtml = `
                    <div style="background:rgba(0,177,79,0.06);border:1px solid rgba(0,177,79,0.15);border-radius:12px;padding:12px 14px;margin-bottom:14px;">
                        <div style="font-size:0.65rem;font-weight:800;color:var(--primary);text-transform:uppercase;letter-spacing:0.6px;margin-bottom:10px;"><i class="fas fa-id-card" style="margin-right:5px;"></i>Declared License Details</div>
                        
                        <div style="display:flex;gap:10px;margin-bottom:12px;">
                            ${licenseUrl ? `<div style="flex:1;"><div style="font-size:0.62rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;margin-bottom:4px;">Front</div><img src="${licenseUrl}" style="width:100%;border-radius:8px;cursor:pointer;" onclick="Verifications.viewLicense('${licenseUrl}')"></div>` : ''}
                            ${v.license_back_url ? `<div style="flex:1;"><div style="font-size:0.62rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;margin-bottom:4px;">Back</div><img src="${v.license_back_url}" style="width:100%;border-radius:8px;cursor:pointer;" onclick="Verifications.viewLicense('${v.license_back_url}')"></div>` : ''}
                        </div>

                        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
                            <div>
                                <div style="font-size:0.62rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;letter-spacing:0.4px;margin-bottom:2px;">License No.</div>
                                <div style="font-size:0.82rem;font-weight:700;color:var(--text-main);">${v.license_number || '-'}</div>
                            </div>
                            <div>
                                <div style="font-size:0.62rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;letter-spacing:0.4px;margin-bottom:2px;">Expiry Date</div>
                                <div style="font-size:0.82rem;font-weight:700;color:var(--text-main);">${v.license_expiry || '-'}</div>
                            </div>
                            <div>
                                <div style="font-size:0.62rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;letter-spacing:0.4px;margin-bottom:2px;">Class / Category</div>
                                <div style="font-size:0.82rem;font-weight:700;color:var(--text-main);">${v.license_type || '-'}</div>
                            </div>
                            <div>
                                <div style="font-size:0.62rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;letter-spacing:0.4px;margin-bottom:2px;">Country / State</div>
                                <div style="font-size:0.82rem;font-weight:700;color:var(--text-main);">${v.issuing_country_state || '-'}</div>
                            </div>
                        </div>
                        
                        <hr style="border:none;border-top:1px solid rgba(255,255,255,0.1);margin:12px 0;">
                        <div style="font-size:0.75rem;font-weight:800;color:var(--text-main);margin-bottom:8px;">Personal Info</div>
                        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
                            <div>
                                <div style="font-size:0.62rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;letter-spacing:0.4px;margin-bottom:2px;">Full Name</div>
                                <div style="font-size:0.82rem;font-weight:700;color:var(--text-main);">${name || '-'}</div>
                            </div>
                            <div>
                                <div style="font-size:0.62rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;letter-spacing:0.4px;margin-bottom:2px;">Date of Birth</div>
                                <div style="font-size:0.82rem;font-weight:700;color:var(--text-main);">${v.date_of_birth || '-'}</div>
                            </div>
                        </div>

                        <hr style="border:none;border-top:1px solid rgba(255,255,255,0.1);margin:12px 0;">
                        <div style="font-size:0.75rem;font-weight:800;color:var(--text-main);margin-bottom:8px;">IV. IN CASE OF EMERGENCY NOTIFY:</div>
                        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
                            <div style="grid-column: span 2;">
                                <div style="font-size:0.62rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;letter-spacing:0.4px;margin-bottom:2px;">Contact Name</div>
                                <div style="font-size:0.82rem;font-weight:700;color:var(--text-main);">${v.emergency_contact_name || '-'}</div>
                            </div>
                            <div>
                                <div style="font-size:0.62rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;letter-spacing:0.4px;margin-bottom:2px;">Phone Number</div>
                                <div style="font-size:0.82rem;font-weight:700;color:var(--text-main);">${v.emergency_contact_phone || '-'}</div>
                            </div>
                            <div>
                                <div style="font-size:0.62rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;letter-spacing:0.4px;margin-bottom:2px;">Relationship</div>
                                <div style="font-size:0.82rem;font-weight:700;color:var(--text-main);">${v.emergency_contact_relationship || '-'}</div>
                            </div>
                        </div>
                    </div>`;

                const actionButtons = licenseUrl
                    ? `<button onclick="Verifications.process(${v.id}, 2)" class="btn-premium" style="flex: 1; padding: 12px; font-size: 0.8rem; border-radius: 14px; background: var(--success); box-shadow: 0 8px 16px rgba(16, 185, 129, 0.3);">Approve</button>
                       <button onclick="Verifications.process(${v.id}, 0)" class="btn-premium" style="flex: 0.7; padding: 12px; font-size: 0.8rem; border-radius: 14px; background: var(--danger); box-shadow: 0 8px 16px rgba(239, 68, 68, 0.3);">Reject</button>`
                    : `<div style="flex: 1; text-align: center; padding: 10px; background: rgba(255,255,255,0.05); border-radius: 12px; color: var(--text-muted); font-size: 0.75rem; font-weight: 600; border: 1px dashed var(--border);">
                            <i class="fas fa-clock" style="margin-right: 5px;"></i> Waiting for Upload
                       </div>`;

                return `
                <div class="stat-card" style="padding: 20px; margin-bottom: 16px;">
                    <div style="display: flex; gap: 16px; align-items: center; margin-bottom: 14px;">
                        <div style="width: 54px; height: 54px; background: linear-gradient(135deg, #00B14F, #005339); border-radius: 16px; display: flex; align-items: center; justify-content: center; font-weight: 900; color: white; font-size: 1.2rem; box-shadow: 0 4px 12px var(--primary-glow); flex-shrink:0;">
                            ${initial}
                        </div>
                        <div style="flex: 1; min-width:0;">
                            <h4 style="font-size: 1.05rem; font-weight: 800; color: var(--text-main); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${name}</h4>
                            <p style="font-size: 0.8rem; color: var(--text-muted); font-weight: 500; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${v.email || 'No Email'}</p>
                        </div>
                    </div>
                    ${detailsHtml}
                    <div style="display: flex; gap: 12px;">
                        ${actionButtons}
                    </div>
                </div>
                `;
            }).join('');
        },
        viewLicense(url) {
            if (!url) return alert('No license image uploaded');
            const fullUrl = url.startsWith('http') ? url : `${API_BASE}${url}`;
            
            // Show in-app preview instead of window.open which fails in Capacitor
            const modal = document.getElementById('licensePreviewModal');
            const img = document.getElementById('licensePreviewImg');
            if (modal && img) {
                img.src = fullUrl;
                modal.style.display = 'flex';
            } else {
                window.open(fullUrl, '_blank');
            }
        },
        async process(userId, status) {
            const admin = adminAuth.getUser();
            if (!confirm(`Are you sure you want to ${status === 2 ? 'APPROVE' : 'REJECT'} this user?`)) return;
            try {
                const res = await fetch(`${API_BASE}/api/admin/verify-action`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        user_id: userId, 
                        status: status,
                        admin_id: admin ? admin.id : 1
                    })
                });
                if (res.ok) {
                    alert('Action successful!');
                    this.refresh();
                } else {
                    const d = await res.json();
                    alert(d.error || 'Failed to update');
                }
            } catch (err) { alert('Network error: ' + err.message); }
        }
    };

    // --- TICKETS MODULE ---
    const Tickets = {
        data: [],
        async refresh() {
            const list = document.getElementById('ticketsList');
            try {
                const res = await fetch(`${API_BASE}/api/admin/tickets`);
                this.data = await res.json();
                this.updateStats();
                this.render();
            } catch (err) {
                list.innerHTML = '<div style="text-align: center; padding: 40px; color: var(--text-muted);">No tickets found.</div>';
            }
        },
        updateStats() {
            const open = this.data.filter(t => t.status === 'open').length;
            const resolved = this.data.filter(t => t.status === 'resolved').length;
            document.getElementById('ticketOpenCount').textContent = open;
            document.getElementById('ticketResolvedCount').textContent = resolved;
        },
        render() {
            const list = document.getElementById('ticketsList');
            if (this.data.length === 0) {
                list.innerHTML = `
                    <div style="text-align: center; padding: 60px 20px; background: var(--surface); border-radius: var(--radius-lg); border: 1px solid var(--border);">
                        <i class="fas fa-ticket-alt" style="font-size: 3rem; color: var(--text-muted); opacity: 0.3; margin-bottom: 15px;"></i>
                        <p style="color: var(--text-muted); font-weight: 600;">No support tickets found.</p>
                    </div>`;
                return;
            }
            list.innerHTML = this.data.map(t => `
                <div class="stat-card" style="padding: 20px; margin-bottom: 16px; ${t.status === 'resolved' ? 'opacity: 0.6;' : ''}">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 15px;">
                        <div>
                            <h4 style="font-size: 1rem; font-weight: 800; color: var(--text-main);">${t.subject || 'No Subject'}</h4>
                            <p style="font-size: 0.75rem; color: var(--text-muted); font-weight: 500;">${t.user_name || t.email}</p>
                        </div>
                        <span class="pill ${t.status === 'open' ? 'danger' : 'success'}" style="font-size: 0.55rem; padding: 3px 10px;">
                            ${t.status.toUpperCase()}
                        </span>
                    </div>
                    <p style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 18px; line-height: 1.6; background: var(--surface-container); padding: 12px; border-radius: 12px; border-left: 3px solid var(--primary);">${t.message}</p>
                    <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--border); padding-top: 15px;">
                        <span style="font-size: 0.7rem; color: var(--text-muted); font-weight: 600;">${new Date(t.created_at).toLocaleDateString()}</span>
                        ${t.status === 'open' ? `
                            <button onclick="Tickets.resolve(${t.id})" class="btn-premium" style="padding: 8px 16px; font-size: 0.75rem; border-radius: 10px; box-shadow: 0 4px 12px var(--primary-glow);">Resolve</button>
                        ` : '<span style="font-size: 0.75rem; color: var(--success); font-weight: 800;"><i class="fas fa-check-circle"></i> RESOLVED</span>'}
                    </div>
                </div>
            `).join('');
        },
        async resolve(id) {
            if (!confirm('Mark ticket as resolved?')) return;
            try {
                const res = await fetch(`${API_BASE}/api/admin/tickets/${id}/resolve`, { method: 'PUT' });
                if (res.ok) { this.refresh(); }
            } catch (err) { alert('Action failed'); }
        }
    };

    // --- INSTRUCTIONS MODULE ---
    const Instructions = {
        data: [],
        async refresh() {
            const list = document.getElementById('instructionsList');
            try {
                const res = await fetch(`${API_BASE}/api/admin/instructions`);
                this.data = await res.json();
                this.render();
            } catch (err) {
                list.innerHTML = '<div style="text-align: center; padding: 40px; color: var(--text-muted);">No instructions found.</div>';
            }
        },
        render() {
            const list = document.getElementById('instructionsList');
            if (this.data.length === 0) {
                list.innerHTML = '<div style="text-align: center; padding: 40px; color: var(--text-muted);">No active instructions.</div>';
                return;
            }
            list.innerHTML = this.data.map(inst => `
                <div class="stat-card" style="padding: 15px; margin-bottom: 10px; border: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center;">
                    <div style="flex: 1; padding-right: 15px;">
                        <p style="font-size: 0.85rem; line-height: 1.4;">${inst.instruction_text}</p>
                    </div>
                    <span style="font-size: 0.55rem; padding: 3px 8px; border-radius: 8px; background: ${inst.is_active ? 'rgba(0,177,79,0.1)' : 'rgba(255,255,255,0.05)'}; color: ${inst.is_active ? 'var(--success)' : 'var(--text-muted)'}; font-weight: 800; text-transform: uppercase;">
                        ${inst.is_active ? 'Active' : 'Inactive'}
                    </span>
                </div>
            `).join('');
        },
        async add() {
            const text = document.getElementById('newInstructionInput').value;
            if (!text) return;
            try {
                const res = await fetch(`${API_BASE}/api/admin/instructions`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ instruction: text, is_active: true })
                });
                if (res.ok) {
                    document.getElementById('newInstructionInput').value = '';
                    this.refresh();
                }
            } catch (err) { alert('Failed to add'); }
        }
    };

    // --- STAFF MODULE ---
    const Staff = {
        data: [],
        editingId: null,
        async refresh() {
            const user = adminAuth.getUser();
            if (!user) return;
            try {
                const res = await fetch(`${API_BASE}/api/admin/list?requester_id=${user.id}`);
                this.data = await res.json();
                this.render();
            } catch (err) {
                console.error(err);
            }
        },
        render() {
            const list = document.getElementById('staffList');
            const currentUser = adminAuth.getUser();
            if (this.data.length === 0) {
                list.innerHTML = '<div style="text-align: center; padding: 40px; color: var(--text-muted);">No staff accounts.</div>';
                return;
            }
            list.innerHTML = this.data.map(s => `
                <div style="padding: 15px 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <div>
                            <h4 style="font-size: 0.95rem;">${s.full_name} ${s.id === currentUser.id ? '<span style="color:var(--primary); font-size:0.75rem;">(You)</span>' : ''}</h4>
                            <p style="font-size: 0.75rem; color: var(--text-muted);">${s.email}</p>
                        </div>
                        <span style="font-size: 0.6rem; padding: 4px 10px; border-radius: 10px; background: ${s.role === 'super_admin' ? 'rgba(255,255,255,0.1)' : 'rgba(251,191,36,0.1)'}; color: ${s.role === 'super_admin' ? 'white' : '#f59e0b'}; font-weight: 800; text-transform: uppercase;">
                            ${s.role.replace('_', ' ')}
                        </span>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 0.75rem; color: ${s.is_verified === 1 ? 'var(--success)' : 'var(--danger)'}; font-weight: 600;">
                            ${s.is_verified === 1 ? 'Enabled' : 'Disabled'}
                        </span>
                        <div style="display: flex; gap: 8px;">
                            <button onclick="Staff.openModal(${s.id})" style="padding: 6px 12px; background: var(--surface-container); border: none; border-radius: 6px; color: white; font-size: 0.7rem; font-weight: 700;">Edit</button>
                            ${s.id !== currentUser.id ? `
                                <button onclick="Staff.toggleStatus(${s.id}, ${s.is_verified})" style="padding: 6px 12px; background: ${s.is_verified === 1 ? 'var(--danger)' : 'var(--success)'}; border: none; border-radius: 6px; color: white; font-size: 0.7rem; font-weight: 700;">
                                    ${s.is_verified === 1 ? 'Disable' : 'Enable'}
                                </button>
                                <button onclick="Staff.delete(${s.id})" style="padding: 6px 12px; background: var(--danger); border: none; border-radius: 6px; color: white; font-size: 0.7rem; font-weight: 700;">Delete</button>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `).join('');
        },
        openModal(id = null) {
            this.editingId = id;
            const modal = document.getElementById('staffModal');
            const hint = document.getElementById('staffPassHint');
            const pass = document.getElementById('staffPass');
            
            document.getElementById('staffForm').reset();
            if (id) {
                const s = this.data.find(x => x.id === id);
                document.getElementById('staffFormTitle').textContent = 'Edit Staff Account';
                document.getElementById('staffName').value = s.full_name;
                document.getElementById('staffEmail').value = s.email;
                document.getElementById('staffRole').value = s.role;
                pass.required = false;
                hint.style.display = 'block';
            } else {
                document.getElementById('staffFormTitle').textContent = 'Add New Staff';
                pass.required = true;
                hint.style.display = 'none';
            }
            modal.style.display = 'flex';
        },
        closeModal() {
            document.getElementById('staffModal').style.display = 'none';
        },
        async toggleStatus(id, current) {
            const user = adminAuth.getUser();
            try {
                const res = await fetch(`${API_BASE}/api/admin/status/${id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ requester_id: user.id, status: current === 1 ? 0 : 1 })
                });
                if (res.ok) this.refresh();
            } catch (err) { alert('Failed to update status'); }
        },
        async delete(id) {
            if (!confirm('Are you sure?')) return;
            const user = adminAuth.getUser();
            try {
                const res = await fetch(`${API_BASE}/api/admin/delete/${id}?requester_id=${user.id}`, { method: 'DELETE' });
                if (res.ok) this.refresh();
                else {
                    const data = await res.json();
                    alert(data.error);
                }
            } catch (err) { alert('Failed to delete'); }
        },
        async submit(e) {
            e.preventDefault();
            const id = this.editingId;
            const user = adminAuth.getUser();
            const payload = {
                requester_id: user.id,
                name: document.getElementById('staffName').value,
                email: document.getElementById('staffEmail').value,
                password: document.getElementById('staffPass').value,
                role: document.getElementById('staffRole').value
            };
            const method = id ? 'PUT' : 'POST';
            const url = id ? `${API_BASE}/api/admin/update/${id}` : `${API_BASE}/api/admin/create`;
            try {
                const res = await fetch(url, {
                    method, headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                if (res.ok) {
                    this.closeModal();
                    this.refresh();
                } else {
                    const data = await res.json();
                    alert('Error: ' + (data.error || 'Operation failed'));
                }
            } catch (err) { alert('Connection error'); }
        }
    };



    // --- GPS MODULE ---
    const GPS = {
        data: [],
        timer: null,
        async refresh() {
            try {
                const res = await fetch(`${API_BASE}/api/admin/gps-locations`);
                this.data = await res.json();
                this.render();
            } catch (err) { console.error(err); }
        },
        startLive() {
            this.refresh();
            this.timer = setInterval(() => this.refresh(), 5000); // 5s updates
        },
        stopLive() {
            if (this.timer) clearInterval(this.timer);
        },
        render() {
            const list = document.getElementById('gpsDeviceList');
            if (this.data.length === 0) {
                list.innerHTML = '<div style="text-align:center; padding:20px; color:var(--text-muted);">No active modules.</div>';
                return;
            }
            list.innerHTML = this.data.map(d => `
                <div style="background: rgba(0,177,79,0.05); padding: 12px; border-radius: 12px; border: 1px solid ${this.isActive(d.last_gps_update) ? 'var(--primary-glow)' : 'var(--border)'}; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                        <strong style="font-size: 0.9rem;">${d.name} (${d.plate_number})</strong>
                        <span style="font-size: 0.6rem; color: ${this.isActive(d.last_gps_update) ? 'var(--success)' : 'var(--text-muted)'}; font-weight: 800;">
                            ${this.isActive(d.last_gps_update) ? '<i class="fas fa-circle" style="font-size:0.5rem;"></i> LIVE' : 'OFFLINE'}
                        </span>
                    </div>
                    <p style="font-size: 0.7rem; color: var(--text-muted);">Lat: ${d.latitude}, Lng: ${d.longitude}</p>
                    <p style="font-size: 0.65rem; color: var(--primary); margin-top: 5px; font-weight: 600;">Last update: ${this.timeAgo(d.last_gps_update)}</p>
                </div>
            `).join('');
        },
        isActive(time) {
            if (!time) return false;
            const diff = (new Date() - new Date(time)) / 1000;
            return diff < 60; // Active if updated in last 60s
        },
        timeAgo(time) {
            if (!time) return 'Never';
            const diff = Math.floor((new Date() - new Date(time)) / 1000);
            if (diff < 10) return 'Just now';
            if (diff < 60) return `${diff}s ago`;
            return `${Math.floor(diff / 60)}m ago`;
        }
    };



    // --- ACTIVITY MODULE ---
    const Activity = {
        data: [],
        _filter: 'all',

        _colors: { login:'#00B14F', logout:'#94a3b8', approve:'#00B14F', reject:'#ef4444', create:'#00B14F', update:'#f59e0b', delete:'#ef4444', view:'#5FDBE2' },

        _color(action) {
            const k = Object.keys(this._colors).find(k => action.toLowerCase().includes(k));
            return k ? this._colors[k] : '#00B14F';
        },

        _icon(action) {
            const a = action.toLowerCase();
            if (a.includes('login'))  return 'fa-sign-in-alt';
            if (a.includes('logout')) return 'fa-sign-out-alt';
            if (a.includes('approve')) return 'fa-check';
            if (a.includes('reject')) return 'fa-times';
            if (a.includes('delete')) return 'fa-trash';
            if (a.includes('create') || a.includes('add')) return 'fa-plus';
            if (a.includes('update') || a.includes('edit')) return 'fa-pen';
            return 'fa-history';
        },

        setFilter(filter, btn) {
            this._filter = filter;
            document.querySelectorAll('.act-chip').forEach(b => {
                const active = b.dataset.filter === filter;
                b.style.background   = active ? 'var(--primary)' : 'var(--surface-container)';
                b.style.borderColor  = active ? 'var(--primary)' : 'var(--border)';
                b.style.color        = active ? '#fff' : 'var(--text-secondary)';
            });
            this.applyFilters();
        },

        applyFilters() {
            const q = (document.getElementById('activitySearch')?.value || '').toLowerCase().trim();
            const f = this._filter;
            const filtered = this.data.filter(l => {
                const matchF = f === 'all' || l.action.toLowerCase().includes(f);
                const matchQ = !q ||
                    (l.admin_name || '').toLowerCase().includes(q) ||
                    (l.action     || '').toLowerCase().includes(q) ||
                    (l.details    || '').toLowerCase().includes(q);
                return matchF && matchQ;
            });
            this._render(filtered);
        },

        _render(logs) {
            const list = document.getElementById('activityList');
            if (!list) return;
            if (!logs.length) {
                list.innerHTML = '<div style="text-align:center;padding:50px;color:var(--text-muted);">No matching logs found.</div>';
                return;
            }
            const now = new Date();
            list.innerHTML = `<ul style="list-style:none;margin:0;padding:0;background:var(--surface-card,var(--surface));border-radius:16px;overflow:hidden;">` +
                logs.map((l, i) => {
                    const color = this._color(l.action);
                    const icon  = this._icon(l.action);
                    const dt    = new Date(l.created_at);
                    const isToday = dt.toDateString() === now.toDateString();
                    const dateStr = isToday
                        ? dt.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})
                        : dt.toLocaleDateString([], {month:'numeric', day:'numeric', year:'2-digit'});
                    return `
                    <li style="display:flex;align-items:center;gap:14px;padding:13px 16px;${i > 0 ? 'border-top:1px solid var(--border);' : ''}">
                        <div style="flex-shrink:0;width:46px;height:46px;border-radius:50%;background:${color}22;display:flex;align-items:center;justify-content:center;color:${color};font-size:1rem;">
                            <i class="fas ${icon}"></i>
                        </div>
                        <div style="flex:1;min-width:0;">
                            <div style="font-size:0.88rem;font-weight:700;color:var(--text-main);margin-bottom:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${l.admin_name || 'System'}</div>
                            <div style="font-size:0.78rem;color:var(--text-secondary);margin-bottom:1px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${l.action.replace(/_/g,' ').replace(/\b\w/g,c=>c.toUpperCase())}</div>
                            <div style="font-size:0.73rem;color:var(--text-muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${l.details || '-'}</div>
                        </div>
                        <div style="flex-shrink:0;display:flex;align-items:center;gap:4px;">
                            <span style="font-size:0.72rem;color:${color};font-weight:600;">${dateStr}</span>
                            <i class="fas fa-chevron-right" style="font-size:0.6rem;color:var(--text-muted);"></i>
                        </div>
                    </li>`;
                }).join('') + `</ul>`;
        },

        async refresh() {
            const list = document.getElementById('activityList');
            if (!list) return;
            list.innerHTML = '<div style="text-align:center;padding:50px;color:var(--text-muted);">Loading activity logs...</div>';
            try {
                const res = await apiFetch(`admin/activity-logs`);
                const logs = await res.json();
                this.data = logs || [];
                // Reset search + chips
                const s = document.getElementById('activitySearch');
                if (s) s.value = '';
                this._filter = 'all';
                document.querySelectorAll('.act-chip').forEach(b => {
                    const active = b.dataset.filter === 'all';
                    b.style.background  = active ? 'var(--primary)' : 'var(--surface-container)';
                    b.style.borderColor = active ? 'var(--primary)' : 'var(--border)';
                    b.style.color       = active ? '#fff' : 'var(--text-secondary)';
                });
                if (!this.data.length) {
                    list.innerHTML = '<div style="text-align:center;padding:50px;color:var(--text-muted);">No activity logs found.</div>';
                    return;
                }
                this._render(this.data);
            } catch (err) {
                list.innerHTML = '<div style="text-align:center;padding:50px;color:var(--danger);">Failed to load logs.</div>';
            }
        }
    };

    // --- ACTIVE NOW MODULE ---
    const ActiveNow = {
        _timer: null,
        _countdown: {},

        render(allBookings) {
            const active = (allBookings || []).filter(b =>
                b.status === 'Picked Up' || b.status === 'Ongoing'
            );
            const countEl = document.getElementById('activeNowCount');
            if (countEl) countEl.textContent = active.length;

            const list = document.getElementById('activeNowList');
            if (!list) return;

            if (active.length === 0) {
                list.innerHTML = '<div style="text-align:center;padding:16px;color:var(--text-muted);font-size:0.8rem;background:var(--surface-container);border-radius:14px;">No active rentals right now.</div>';
                return;
            }

            list.innerHTML = active.map((b, i) => {
                const endDate = b.end_date ? new Date(b.end_date) : null;
                const endStr  = endDate ? endDate.toLocaleDateString('en-PH', {month:'short',day:'numeric',year:'numeric'}) : 'ï¿½';
                const cdId    = 'anCountdown_' + b.id;
                
                // Location handling
                const pickupLoc = b.pickup_location || b.location || 'N/A';
                const dropoffLoc = b.dropoff_location || b.pickup_location || b.location || 'N/A';
                const showBothLocations = pickupLoc !== dropoffLoc && dropoffLoc !== 'N/A';
                
                // Truncate location for display (max 30 chars)
                const truncateLocation = (loc) => {
                    if (!loc || loc === 'N/A') return 'N/A';
                    return loc.length > 30 ? loc.substring(0, 30) + '...' : loc;
                };
                
                const pickupDisplay = truncateLocation(pickupLoc);
                const dropoffDisplay = truncateLocation(dropoffLoc);
                
                return `
                <div style="background:var(--surface);border:1px solid var(--border);border-radius:16px;padding:14px;margin-bottom:10px;border-left:3px solid #00B14F;">
                    <div style="display:flex;align-items:center;gap:12px;margin-bottom:10px;">
                        <div style="width:40px;height:40px;border-radius:12px;background:rgba(0,177,79,0.1);display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                            <i class="fas fa-car" style="color:#00B14F;font-size:1rem;"></i>
                        </div>
                        <div style="flex:1;min-width:0;">
                            <div style="font-size:0.88rem;font-weight:800;color:var(--text-main);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${b.car || (b.brand||'') + ' ' + (b.model||'')}</div>
                            <div style="font-size:0.72rem;color:var(--text-muted);">${b.customer_name || 'Customer'} &bull; #${b.id}</div>
                        </div>
                        <span style="background:rgba(0,177,79,0.1);color:#00B14F;border:1px solid rgba(0,177,79,0.25);padding:3px 8px;border-radius:20px;font-size:0.6rem;font-weight:800;flex-shrink:0;">ACTIVE</span>
                    </div>
                    
                    <!-- Location Information -->
                    <div style="background:var(--surface-container);border-radius:10px;padding:10px;margin-bottom:8px;">
                        <div style="display:flex;align-items:flex-start;gap:8px;">
                            <i class="fas fa-map-marker-alt" style="color:var(--primary);font-size:1.1rem;flex-shrink:0;margin-top:2px;"></i>
                            <div style="flex:1;min-width:0;">
                                <div style="font-size:0.58rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;margin-bottom:4px;">Location</div>
                                <div style="display:flex;flex-direction:column;gap:4px;">
                                    <div title="${pickupLoc}" style="font-size:0.78rem;font-weight:700;color:var(--text-main);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
                                        <span style="font-size:0.65rem;color:var(--text-muted);font-weight:600;">Pickup:</span> ${pickupDisplay}
                                    </div>
                                    ${showBothLocations ? `
                                    <div style="display:flex;align-items:center;gap:4px;margin:2px 0;">
                                        <i class="fas fa-arrow-down" style="color:var(--text-muted);font-size:0.65rem;"></i>
                                    </div>
                                    <div title="${dropoffLoc}" style="font-size:0.78rem;font-weight:600;color:var(--text-secondary);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
                                        <span style="font-size:0.65rem;color:var(--text-muted);font-weight:600;">Dropoff:</span> ${dropoffDisplay}
                                    </div>
                                    ` : ''}
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
                        <div style="background:var(--surface-container);border-radius:10px;padding:8px 10px;">
                            <div style="font-size:0.58rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;margin-bottom:2px;">Return By</div>
                            <div style="font-size:0.78rem;font-weight:700;color:var(--text-main);">${endStr}</div>
                        </div>
                        <div style="background:var(--surface-container);border-radius:10px;padding:8px 10px;">
                            <div style="font-size:0.58rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;margin-bottom:2px;">Time Left</div>
                            <div id="${cdId}" style="font-size:0.78rem;font-weight:800;color:#00B14F;">ï¿½</div>
                        </div>
                    </div>
                </div>`;
            }).join('');

            // Start countdowns
            this._stopCountdowns();
            active.forEach(b => {
                if (!b.end_date) return;
                const endParts = this._normDate(b.end_date).split('-');
                const endDt = new Date(parseInt(endParts[0]), parseInt(endParts[1])-1, parseInt(endParts[2]), 23, 59, 59);
                const cdId = 'anCountdown_' + b.id;
                this._countdown[b.id] = setInterval(() => {
                    const el = document.getElementById(cdId);
                    if (!el) { clearInterval(this._countdown[b.id]); return; }
                    const ms = endDt - new Date();
                    if (ms <= 0) { el.textContent = 'Ended'; el.style.color = '#ef4444'; return; }
                    const d = Math.floor(ms/86400000);
                    const h = Math.floor((ms%86400000)/3600000);
                    const m = Math.floor((ms%3600000)/60000);
                    const s = Math.floor((ms%60000)/1000);
                    el.textContent = d > 0
                        ? `${d}d ${h}h ${String(m).padStart(2,'0')}m ${String(s).padStart(2,'0')}s`
                        : `${h}h ${String(m).padStart(2,'0')}m ${String(s).padStart(2,'0')}s`;
                    el.style.color = ms < 86400000 ? '#ef4444' : '#00B14F';
                }, 1000);
            });

            // Auto-refresh every 30s
            if (this._timer) clearInterval(this._timer);
            this._timer = setInterval(() => {
                const label = document.getElementById('activeNowRefreshLabel');
                if (label) label.textContent = 'refreshingï¿½';
                Bookings.refresh().then(() => {
                    if (label) label.textContent = 'auto-refresh 30s';
                }).catch(() => {
                    if (label) label.textContent = 'auto-refresh 30s';
                });
            }, 30000);
        },

        _normDate(d) {
            if (!d) return '';
            if (/^\d{4}-\d{2}-\d{2}$/.test(String(d))) return String(d);
            const dt = new Date(d);
            if (isNaN(dt.getTime())) return String(d);
            return dt.getFullYear() + '-' + String(dt.getMonth()+1).padStart(2,'0') + '-' + String(dt.getDate()).padStart(2,'0');
        },

        _stopCountdowns() {
            Object.values(this._countdown).forEach(t => clearInterval(t));
            this._countdown = {};
        },

        stop() {
            this._stopCountdowns();
            if (this._timer) { clearInterval(this._timer); this._timer = null; }
        }
    };

    // --- PAST BOOKINGS MODULE ---
    const PastBookings = {
        data: [],
        filteredData: [],
        currentPage: 1,
        pageSize: 10,
        sortBy: 'completion_date_desc',
        totalPages: 1,

        async load() {
            const loadingEl = document.getElementById('pastBookingsLoading');
            const emptyEl = document.getElementById('pastBookingsEmpty');
            const tableEl = document.getElementById('pastBookingsTable');
            
            // Show loading state
            if (loadingEl) loadingEl.style.display = 'block';
            if (emptyEl) emptyEl.classList.add('hidden');
            if (tableEl) tableEl.style.display = 'none';

            try {
                // Fetch past bookings from API
                const res = await fetch(`${API_BASE}/api/bookings/past?page=${this.currentPage}&page_size=${this.pageSize}&sort_by=${this.sortBy}`);
                
                if (!res.ok) {
                    throw new Error(`Server error: ${res.status}`);
                }
                
                const responseData = await res.json();
                
                // Handle response format - could be array or object with pagination
                if (Array.isArray(responseData)) {
                    this.data = responseData;
                    this.filteredData = [...responseData];
                    this.totalPages = Math.ceil(responseData.length / this.pageSize);
                } else if (responseData.bookings) {
                    this.data = responseData.bookings;
                    this.filteredData = [...responseData.bookings];
                    this.totalPages = responseData.total_pages || 1;
                } else {
                    this.data = [];
                    this.filteredData = [];
                    this.totalPages = 1;
                }
                
                this.renderTable();
                this.updatePaginationControls();
                
            } catch (err) {
                console.error('Failed to load past bookings:', err);
                
                // Hide loading, show empty state with error
                if (loadingEl) loadingEl.style.display = 'none';
                if (emptyEl) {
                    emptyEl.classList.remove('hidden');
                    emptyEl.innerHTML = `
                        <i class="fas fa-exclamation-triangle" style="font-size: 3rem; margin-bottom: 16px; opacity: 0.3; color: var(--danger);"></i>
                        <h3 style="font-size: 1.1rem; font-weight: 700; margin-bottom: 8px; color: var(--text-main);">Failed to Load</h3>
                        <p style="font-size: 0.85rem; margin-bottom: 16px;">${err.message}</p>
                        <button onclick="PastBookings.load()" style="padding: 10px 20px; background: var(--primary); border: none; color: white; border-radius: 8px; font-size: 0.85rem; font-weight: 700; cursor: pointer;">Retry</button>
                    `;
                }
                if (tableEl) tableEl.style.display = 'none';
            }
        },

        renderTable() {
            const tbody = document.getElementById('pastBookingsTableBody');
            const loadingEl = document.getElementById('pastBookingsLoading');
            const emptyEl = document.getElementById('pastBookingsEmpty');
            const tableEl = document.getElementById('pastBookingsTable');
            
            // Hide loading
            if (loadingEl) loadingEl.style.display = 'none';
            
            if (!tbody) return;
            
            if (this.filteredData.length === 0) {
                // Show empty state
                if (emptyEl) emptyEl.classList.remove('hidden');
                if (tableEl) tableEl.style.display = 'none';
                return;
            }
            
            // Show table, hide empty state
            if (emptyEl) emptyEl.classList.add('hidden');
            if (tableEl) tableEl.style.display = 'table';
            
            // Render table rows
            tbody.innerHTML = this.filteredData.map(b => {
                const completionDate = b.completion_date || b.updated_at || b.end_date;
                const completionDateStr = completionDate ? new Date(completionDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : 'N/A';
                const startDateStr = b.start_date ? new Date(b.start_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : 'N/A';
                const endDateStr = b.end_date ? new Date(b.end_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : 'N/A';
                const rentalDates = `${startDateStr} - ${endDateStr}`;
                const totalPrice = b.total_price ? parseFloat(b.total_price).toLocaleString('en-PH', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '0.00';
                
                return `
                    <tr style="border-bottom: 1px solid var(--border); transition: background 0.2s;">
                        <td style="padding: 12px 10px; font-size: 0.8rem; font-weight: 700; color: var(--text-secondary);">#${b.id}</td>
                        <td style="padding: 12px 10px; font-size: 0.85rem; font-weight: 600; color: var(--text-main);">${b.customer_name || 'N/A'}</td>
                        <td style="padding: 12px 10px; font-size: 0.85rem; color: var(--text-secondary);">${b.car || b.vehicle || 'N/A'}</td>
                        <td style="padding: 12px 10px; font-size: 0.8rem; color: var(--text-secondary);">${rentalDates}</td>
                        <td style="padding: 12px 10px; font-size: 0.8rem; color: var(--text-secondary);">${completionDateStr}</td>
                        <td style="padding: 12px 10px; text-align: right; font-size: 0.9rem; font-weight: 700; color: var(--success);">?${totalPrice}</td>
                        <td style="padding: 12px 10px; text-align: center;">
                            <button onclick="Bookings.view(${b.id})" style="padding: 6px 12px; background: var(--primary); border: none; color: white; border-radius: 6px; font-size: 0.75rem; font-weight: 600; cursor: pointer; transition: all 0.2s;">
                                <i class="fas fa-eye" style="margin-right: 4px;"></i> View
                            </button>
                        </td>
                    </tr>
                `;
            }).join('');
        },

        updatePaginationControls() {
            const pageInfo = document.getElementById('pastBookingsPageInfo');
            const prevBtn = document.getElementById('pastBookingsPrevBtn');
            const nextBtn = document.getElementById('pastBookingsNextBtn');
            
            if (pageInfo) {
                pageInfo.textContent = `Page ${this.currentPage} of ${this.totalPages}`;
            }
            
            if (prevBtn) {
                prevBtn.disabled = this.currentPage <= 1;
                prevBtn.style.opacity = this.currentPage <= 1 ? '0.5' : '1';
                prevBtn.style.cursor = this.currentPage <= 1 ? 'not-allowed' : 'pointer';
            }
            
            if (nextBtn) {
                nextBtn.disabled = this.currentPage >= this.totalPages;
                nextBtn.style.opacity = this.currentPage >= this.totalPages ? '0.5' : '1';
                nextBtn.style.cursor = this.currentPage >= this.totalPages ? 'not-allowed' : 'pointer';
            }
        }
    };

    // Global functions for past bookings
    window.loadPastBookings = function() {
        PastBookings.load();
    };

    window.filterPastBookings = function() {
        const searchInput = document.getElementById('pastBookingsSearch');
        if (!searchInput) return;
        
        const query = searchInput.value.toLowerCase().trim();
        
        if (!query) {
            PastBookings.filteredData = [...PastBookings.data];
        } else {
            PastBookings.filteredData = PastBookings.data.filter(b => {
                const customerName = (b.customer_name || '').toLowerCase();
                const bookingId = String(b.id || '');
                const vehicle = (b.car || b.vehicle || '').toLowerCase();
                
                return customerName.includes(query) || 
                       bookingId.includes(query) || 
                       vehicle.includes(query);
            });
        }
        
        PastBookings.currentPage = 1;
        PastBookings.renderTable();
        PastBookings.updatePaginationControls();
    };

    window.sortPastBookings = function() {
        const sortSelect = document.getElementById('pastBookingsSort');
        if (!sortSelect) return;
        
        PastBookings.sortBy = sortSelect.value;
        PastBookings.currentPage = 1;
        PastBookings.load();
    };

    window.changePastBookingsPageSize = function() {
        const pageSizeSelect = document.getElementById('pastBookingsPageSize');
        if (!pageSizeSelect) return;
        
        PastBookings.pageSize = parseInt(pageSizeSelect.value);
        PastBookings.currentPage = 1;
        PastBookings.load();
    };

    window.previousPastBookingsPage = function() {
        if (PastBookings.currentPage > 1) {
            PastBookings.currentPage--;
            PastBookings.load();
        }
    };

    window.nextPastBookingsPage = function() {
        if (PastBookings.currentPage < PastBookings.totalPages) {
            PastBookings.currentPage++;
            PastBookings.load();
        }
    };

    window.switchBookingTab = function(tab) {
        // Hide all tab contents
        const tabContents = document.querySelectorAll('.booking-tab-content');
        tabContents.forEach(content => {
            content.style.display = 'none';
        });
        
        // Remove active class from all tab buttons
        const tabButtons = document.querySelectorAll('.booking-tab-btn');
        tabButtons.forEach(btn => {
            btn.style.border = '1px solid var(--border)';
            btn.style.background = 'var(--surface-container)';
            btn.style.color = 'var(--text-secondary)';
        });
        
        // Show selected tab content
        if (tab === 'active') {
            const activeTab = document.getElementById('tabActive');
            if (activeTab) activeTab.style.display = 'block';
            const activeBtn = document.getElementById('tabBtnActive');
            if (activeBtn) {
                activeBtn.style.border = '1px solid var(--primary)';
                activeBtn.style.background = 'var(--primary)';
                activeBtn.style.color = 'white';
            }
            // Refresh active bookings
            if (typeof ActiveNow !== 'undefined' && typeof Bookings !== 'undefined') {
                ActiveNow.render(Bookings.data);
            }
        } else if (tab === 'past') {
            const pastTab = document.getElementById('tabPast');
            if (pastTab) pastTab.style.display = 'block';
            const pastBtn = document.getElementById('tabBtnPast');
            if (pastBtn) {
                pastBtn.style.border = '1px solid var(--primary)';
                pastBtn.style.background = 'var(--primary)';
                pastBtn.style.color = 'white';
            }
            // Load past bookings
            PastBookings.load();
        } else if (tab === 'all') {
            const allTab = document.getElementById('tabAll');
            if (allTab) allTab.style.display = 'block';
            const allBtn = document.getElementById('tabBtnAll');
            if (allBtn) {
                allBtn.style.border = '1px solid var(--primary)';
                allBtn.style.background = 'var(--primary)';
                allBtn.style.color = 'white';
            }
            // Refresh all bookings
            if (typeof Bookings !== 'undefined') {
                Bookings.render();
            }
        }
    };

    // --- REPORTS MODULE ---
    const Reports = {
        chart: null,
        chartBookings: null,
        chartPie: null,
        _loaded: false,
        _filter: 'month',
        _rawData: null,

        setFilter(period, btn) {
            this._filter = period;
            document.querySelectorAll('.rpt-filter-btn').forEach(b => {
                b.style.background = 'var(--surface-container)';
                b.style.borderColor = 'var(--border)';
                b.style.color = 'var(--text-secondary)';
            });
            btn.style.background = 'var(--primary)';
            btn.style.borderColor = 'var(--primary)';
            btn.style.color = 'white';
            // Set default date range based on period
            const now = new Date();
            const to = now.toISOString().split('T')[0];
            let from;
            if (period === 'day') {
                from = to;
            } else if (period === 'month') {
                const d = new Date(now); d.setDate(1);
                from = d.toISOString().split('T')[0];
            } else {
                const d = new Date(now); d.setMonth(0); d.setDate(1);
                from = d.toISOString().split('T')[0];
            }
            document.getElementById('rptDateFrom').value = from;
            document.getElementById('rptDateTo').value = to;
            this.refresh();
        },

        async refresh() {
            this._loaded = true;
            try {
                const from = document.getElementById('rptDateFrom').value;
                const to = document.getElementById('rptDateTo').value;
                const params = from && to ? `&date_from=${from}&date_to=${to}` : '';
                const res = await fetch(`${API_BASE}/api/admin/detailed-stats?filter=${this._filter}${params}`);
                const data = await res.json();
                this._rawData = data;

                const totalRev = data.totalRevenue || 0;
                const totalBook = data.totalBookings || 0;
                document.getElementById('repAvgRev').textContent = '\u20B1' + Math.floor(totalRev / (totalBook || 1)).toLocaleString();
                document.getElementById('repActive').textContent = totalBook;
                document.getElementById('repTotalRev').textContent = '\u20B1' + totalRev.toLocaleString();
                const activeFleetCount = (data.fleetDistribution || []).reduce((sum, item) => sum + (item.count || 0), 0);
                document.getElementById('repFleet').textContent = activeFleetCount;

                this.renderRevenueChart(data.revenueTrend || []);
                this.renderBookingsChart(data.bookingsTrend || data.revenueTrend || []);
                this.renderPieChart(data.topVehicles || []);
                this.renderTop(data.topVehicles || []);
            } catch (err) { console.error(err); }
        },

        renderRevenueChart(trend) {
            const ctx = document.getElementById('reportsRevenueChart').getContext('2d');
            if (this.chart) this.chart.destroy();
            this.chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: trend.map(t => t.day ? t.day.split('-').slice(1).join('/') : t.label || ''),
                    datasets: [{
                        label: 'Revenue',
                        data: trend.map(t => t.amount || t.revenue || 0),
                        borderColor: '#00B14F',
                        borderWidth: 2,
                        backgroundColor: 'rgba(0,177,79,0.1)',
                        fill: true,
                        tension: 0.4,
                        pointRadius: 3,
                        pointBackgroundColor: '#00B14F'
                    }]
                },
                options: { responsive: true, maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { grid: { display: false }, ticks: { color: '#94a3b8', font: { size: 9 } } },
                        y: { grid: { color: 'rgba(0,0,0,0.05)' }, ticks: { color: '#94a3b8', font: { size: 9 } } }
                    }
                }
            });
            makeChartClickable('reportsRevenueChart', this.chart, 'revenue');
        },

        renderBookingsChart(trend) {
            const ctx = document.getElementById('reportsBookingsChart').getContext('2d');
            if (this.chartBookings) this.chartBookings.destroy();
            this.chartBookings = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: trend.map(t => t.day ? t.day.split('-').slice(1).join('/') : t.label || ''),
                    datasets: [{
                        label: 'Bookings',
                        data: trend.map(t => t.booking_count || t.count || t.bookings || 0),
                        backgroundColor: 'rgba(0,82,255,0.6)',
                        borderRadius: 4
                    }]
                },
                options: { responsive: true, maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { grid: { display: false }, ticks: { color: '#94a3b8', font: { size: 9 } } },
                        y: { grid: { color: 'rgba(0,0,0,0.05)' }, ticks: { color: '#94a3b8', font: { size: 9 } } }
                    }
                }
            });
            makeChartClickable('reportsBookingsChart', this.chartBookings, 'bookings');
        },

        renderPieChart(cars) {
            const ctx = document.getElementById('reportsTopPieChart').getContext('2d');
            if (this.chartPie) this.chartPie.destroy();
            // Deduplicate by vehicle name, summing booking counts
            const seen = {};
            cars.forEach(c => {
                const key = `${c.brand} ${c.model}`;
                if (seen[key]) {
                    seen[key].booking_count += (c.booking_count || 0);
                } else {
                    seen[key] = { label: key, booking_count: c.booking_count || 0 };
                }
            });
            const deduped = Object.values(seen).sort((a, b) => b.booking_count - a.booking_count).slice(0, 5);
            this.chartPie = new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: deduped.map(c => c.label),
                    datasets: [{
                        data: deduped.map(c => c.booking_count),
                        backgroundColor: ['#00B14F','#00B14F','#f59e0b','#ef4444','#00B14F'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                color: '#6b7080',
                                font: { size: 9 },
                                padding: 6,
                                usePointStyle: true,
                                pointStyleWidth: 8,
                                boxHeight: 8
                            }
                        }
                    }
                }
            });
            makeChartClickable('reportsTopPieChart', this.chartPie, 'topveh');
        },

        renderTop(cars) {
            const container = document.getElementById('reportsTopVehicles');
            if (!cars.length) { container.innerHTML = '<p style="text-align:center;color:var(--text-muted);padding:20px;">No data</p>'; return; }
            container.innerHTML = cars.slice(0, 5).map((c, i) => `
                <div style="display:flex;justify-content:space-between;align-items:center;padding:12px 15px;background:var(--surface-container);border-radius:10px;margin-bottom:8px;border:1px solid var(--border);">
                    <div style="display:flex;align-items:center;gap:10px;">
                        <span style="width:22px;height:22px;border-radius:50%;background:var(--primary);color:white;font-size:0.65rem;font-weight:800;display:flex;align-items:center;justify-content:center;">${i+1}</span>
                        <div>
                            <div style="font-size:0.85rem;font-weight:700;color:var(--text-main);">${c.brand} ${c.model} ${c.plate_number ? '('+c.plate_number+')' : ''}</div>
                            <div style="font-size:0.65rem;color:var(--text-muted);">${c.booking_count} bookings</div>
                        </div>
                    </div>
                    <span style="font-size:0.9rem;font-weight:900;color:var(--success);">₱${(c.revenue||0).toLocaleString()}</span>
                </div>
            `).join('');
        },

        async exportExcel() {
            const data = this._rawData;
            if (!data) { showNotification('No data to export', 'error'); return; }

            const totalRev = data.totalRevenue || 0;
            const totalBook = data.totalBookings || 0;

            const rows = [];
            rows.push(['Autoride Sales Report']);
            rows.push(['Generated:', new Date().toLocaleString()]);
            rows.push([]);
            rows.push(['Summary']);
            rows.push(['Total Revenue (PHP)', totalRev]);
            rows.push(['Total Bookings', totalBook]);
            rows.push(['Average Revenue per Booking (PHP)', totalBook > 0 ? Math.floor(totalRev / totalBook) : 0]);
            rows.push([]);
            rows.push(['Top Vehicles by Revenue']);
            rows.push(['#', 'Vehicle', 'Bookings', 'Revenue (PHP)']);
            (data.topVehicles || []).forEach((c, i) => {
                rows.push([i + 1, c.brand + " " + c.model, c.booking_count, c.revenue || 0]);
            });
            rows.push([]);
            rows.push(['Revenue Trend']);
            rows.push(['Date', 'Revenue (PHP)']);
            (data.revenueTrend || []).forEach(t => {
                rows.push([t.day || t.label || '', t.amount || 0]);
            });

            // Generate real Excel file using SheetJS
            try {
                if (typeof XLSX === 'undefined') {
                    throw new Error('Excel library not loaded');
                }
                
                const wb = XLSX.utils.book_new();
                const ws = XLSX.utils.aoa_to_sheet(rows);
                XLSX.utils.book_append_sheet(wb, ws, "Report");
                
                // Write as base64
                const wboutBase64 = XLSX.write(wb, { bookType: 'xlsx', type: 'base64' });
                const filename = 'autoride_report_' + new Date().toISOString().split('T')[0] + '.xlsx';

                const { Filesystem, Directory } = window.Capacitor.Plugins;
                if (Filesystem) {
                    const result = await Filesystem.writeFile({
                        path: filename,
                        data: wboutBase64,
                        directory: Directory ? Directory.Documents : 'DOCUMENTS',
                        recursive: true
                    });
                    
                    const { Share } = window.Capacitor.Plugins;
                    if (Share) {
                        await Share.share({
                            title: 'Autoride Sales Report',
                            url: result.uri,
                            dialogTitle: 'Share Excel Report'
                        });
                    }
                    showNotification('Excel Report saved and ready to share!', 'success');
                    return;
                }
            } catch (err) {
                console.error('Excel generation/sharing failed:', err);
            }

            // Fallback for web or if plugins fail
            try {
                if (typeof XLSX !== 'undefined') {
                    const wb = XLSX.utils.book_new();
                    const ws = XLSX.utils.aoa_to_sheet(rows);
                    XLSX.utils.book_append_sheet(wb, ws, "Report");
                    XLSX.writeFile(wb, 'autoride_report_' + new Date().toISOString().split('T')[0] + '.xlsx');
                    showNotification('Excel file downloaded!', 'success');
                } else {
                    showNotification('Export failed. Excel library not available.', 'error');
                }
            } catch (err) {
                showNotification('Export failed. Please try again.', 'error');
            }
        },

        async printReport() {
            const data = this._rawData;
            if (!data) { showNotification('No data to print', 'error'); return; }

            const totalRev = data.totalRevenue || 0;
            const totalBook = data.totalBookings || 0;
            const tableRows = (data.topVehicles || []).map((c, i) =>
                '<tr><td style="border:1px solid #ddd;padding:8px;color:#000;">' + (i+1) + '</td><td style="border:1px solid #ddd;padding:8px;color:#000;">' + c.brand + ' ' + c.model + '</td><td style="border:1px solid #ddd;padding:8px;color:#000;">' + c.booking_count + '</td><td style="border:1px solid #ddd;padding:8px;color:#000;">₱' + (c.revenue||0).toLocaleString() + '</td></tr>'
            ).join('');

            // Build HTML report content
            var htmlReport = '<html><head><meta charset="UTF-8"><title>Autoride Report</title>';
            htmlReport += '<style>body{font-family:Arial,sans-serif;padding:20px;margin:0;}h1{font-size:1.4rem;}table{width:100%;border-collapse:collapse;margin-top:16px;}th,td{border:1px solid #ddd;padding:8px;text-align:left;}th{background:#f4f4f4;font-weight:bold;}</style>';
            htmlReport += '</head><body>';
            htmlReport += '<h1>Autoride Sales Report</h1>';
            htmlReport += '<p>Generated: ' + new Date().toLocaleString() + '</p>';
            htmlReport += '<p><strong>Total Revenue:</strong> ₱' + totalRev.toLocaleString() + '</p>';
            htmlReport += '<p><strong>Total Bookings:</strong> ' + totalBook + '</p>';
            htmlReport += '<table><thead><tr><th>#</th><th>Vehicle</th><th>Bookings</th><th>Revenue</th></tr></thead>';
            htmlReport += '<tbody>' + tableRows + '</tbody></table>';
            htmlReport += '</body></html>';

            try {
                // Save HTML file and share it
                const { Filesystem, Directory } = window.Capacitor.Plugins;
                if (Filesystem) {
                    const filename = 'Autoride_Report_' + new Date().toISOString().split('T')[0] + '.html';
                    const result = await Filesystem.writeFile({
                        path: filename,
                        data: btoa(unescape(encodeURIComponent(htmlReport))),
                        directory: Directory ? Directory.Documents : 'DOCUMENTS',
                        recursive: true
                    });

                    const { Share } = window.Capacitor.Plugins;
                    if (Share) {
                        await Share.share({
                            title: 'Autoride Sales Report',
                            url: result.uri,
                            dialogTitle: 'Share or Print Report'
                        });
                    }
                    showNotification('Report saved! Open it in Chrome to print.', 'success');
                    return;
                }
            } catch (err) {
                console.error('Print/share failed:', err);
            }

            // Fallback: share as text
            try {
                var reportText = 'AUTORIDE SALES REPORT\n';
                reportText += 'Generated: ' + new Date().toLocaleString() + '\n\n';
                reportText += 'Total Revenue: PHP ' + totalRev.toLocaleString() + '\n';
                reportText += 'Total Bookings: ' + totalBook + '\n\n';
                reportText += 'TOP VEHICLES BY REVENUE\n------------------------\n';
                (data.topVehicles || []).forEach(function(c, i) {
                    reportText += (i+1) + '. ' + c.brand + ' ' + c.model + ' - ' + c.booking_count + ' bookings - PHP ' + (c.revenue||0).toLocaleString() + '\n';
                });
                if (navigator.share) {
                    await navigator.share({ title: 'Autoride Sales Report', text: reportText });
                } else {
                    await navigator.clipboard.writeText(reportText);
                    showNotification('Report copied to clipboard!', 'success');
                }
            } catch(e) {
                if (e.name !== 'AbortError') showNotification('Share failed', 'error');
            }
        }
    };



    // --- SETTINGS MODULE ---
    const Settings = {
        async fetch() {
            const list = document.getElementById('mobileSettingsList');
            const user = adminAuth.getUser();
            if (!user || (user.role !== 'super_admin' && user.role !== 'superadmin')) return;
            
            try {
                const res = await fetch(`${API_BASE}/api/admin/settings`);
                const data = await res.json();
                list.innerHTML = data.map(s => `
                    <div style="margin-bottom: 15px;">
                        <label style="display: block; font-size: 0.65rem; color: var(--text-muted); text-transform: uppercase; margin-bottom: 8px; font-weight: 800; letter-spacing: 1px;">${s.description}</label>
                        <div style="position: relative;">
                            <input type="text" data-key="${s.key}" value="${s.value}" style="width: 100%; padding: 14px; background: var(--surface-container); border: 1px solid var(--border); border-radius: 12px; color: var(--text-main); font-size: 0.9rem; font-weight: 600;">
                        </div>
                    </div>
                `).join('');
            } catch (err) {
                list.innerHTML = `<p style="color: var(--danger); text-align: center; padding: 20px;">Failed to load settings.</p>`;
            }
        },
        async save() {
            const inputs = document.querySelectorAll('#mobileSettingsList input');
            const updates = Array.from(inputs).map(i => ({ key: i.dataset.key, value: i.value }));
            const user = adminAuth.getUser();

            try {
                const res = await fetch(`${API_BASE}/api/admin/settings`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ requester_id: user.id, settings: updates })
                });
                if (res.ok) {
                    showNotification('Settings saved!', 'success');
                    this.fetch();
                } else {
                    showNotification('Save failed', 'error');
                }
            } catch (err) { showNotification('Network error', 'error'); }
        }
    };

    async function refreshDashboard(_retryCount) {
        _retryCount = _retryCount || 0;
        const user = adminAuth.getUser();
        if (!user) {
            if (_retryCount < 3) {
                setTimeout(function() { refreshDashboard(_retryCount + 1); }, 500);
            }
            return;
        }
        try {
            const res = await fetch(`${API_URL}/admin/stats?admin_id=${user.id}`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            
            // Store for potential re-use
            _dashData = data;

            // Update stat cards
            document.getElementById('dashTotalRevenue').textContent = '\u20B1' + (data.total_revenue || 0).toLocaleString('en-PH', {minimumFractionDigits: 2});
            document.getElementById('dashTotalBookings').textContent = data.total_bookings || 0;
            
            // Top Performance: bookings by vehicle type (derived from topVehicles)
            const topPerf = document.getElementById('dashTopPerformance');
            if (topPerf && data.topVehicles && data.topVehicles.length) {
                // Group by vehicle type if available, else show top vehicles by booking count
                const top = data.topVehicles.slice(0, 4);
                topPerf.innerHTML = top.map(c => `
                    <div style="display:flex;justify-content:space-between;align-items:center;padding:5px 0;border-bottom:1px solid var(--border-light);">
                        <span style="font-size:0.75rem;color:var(--text-secondary);">${c.brand} ${c.model}</span>
                        <span style="font-size:0.75rem;font-weight:800;color:var(--text-main);">${c.booking_count}</span>
                    </div>
                `).join('');
            } else if (topPerf) {
                topPerf.innerHTML = '<div style="font-size:0.75rem;color:var(--text-muted);text-align:center;padding:10px 0;">No data.</div>';
            }

            // Top Grossing: revenue by vehicle
            const topGross = document.getElementById('dashTopGrossing');
            if (topGross && data.topVehicles && data.topVehicles.length) {
                const sorted = [...data.topVehicles].sort((a,b) => (b.revenue||0) - (a.revenue||0)).slice(0, 4);
                topGross.innerHTML = sorted.map(c => `
                    <div style="display:flex;justify-content:space-between;align-items:center;padding:5px 0;border-bottom:1px solid var(--border-light);">
                        <span style="font-size:0.75rem;color:var(--text-secondary);">${c.brand} ${c.model}</span>
                        <span style="font-size:0.7rem;font-weight:800;color:var(--success);">\u20B1${(c.revenue||0).toLocaleString()}</span>
                    </div>
                `).join('');
            } else if (topGross) {
                topGross.innerHTML = '<div style="font-size:0.75rem;color:var(--text-muted);text-align:center;padding:10px 0;">No data.</div>';
            }

            // Init charts (canvases are always visible now)
            if (typeof Chart !== 'undefined') initCharts(data);
        } catch (err) { 
            console.error('Dashboard Refresh Error:', err); 
            document.getElementById('dashTotalRevenue').textContent = '\u20B1ï¿½';
            document.getElementById('dashTotalBookings').textContent = 'ï¿½';
        }
    }

    function renderTopVehicles(cars) {
        const tbody = document.getElementById('topVehiclesBody');
        if (!cars || cars.length === 0) {
            tbody.innerHTML = '<tr><td colspan="3" style="text-align: center; padding: 40px; color: var(--text-muted); font-weight: 600;">No active vehicles.</td></tr>';
            return;
        }
        tbody.innerHTML = cars.map(c => `
            <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                <td style="padding: 16px 8px;">
                    <div style="font-weight: 800; color: var(--text-main); font-size: 0.9rem;">${c.brand}</div>
                    <div style="font-size: 0.75rem; color: var(--text-muted); font-weight: 500;">${c.model}</div>
                </td>
                <td style="padding: 16px 8px; text-align: center;">
                    <span style="font-size: 0.85rem; font-weight: 700; color: var(--text-secondary);">${c.booking_count}</span>
                </td>
                <td style="padding: 16px 8px; text-align: right;">
                    <span style="font-size: 0.95rem; font-weight: 900; color: var(--success); letter-spacing: -0.5px;">₱${c.revenue.toLocaleString()}</span>
                </td>
            </tr>
        `).join('');
    }

    // --- CHART COLLAPSE TOGGLE ---
    let _dashData = null; // store last dashboard data for re-render on expand

    function toggleChart(id) {
        const body = document.getElementById('cc-body-' + id);
        const icon = document.getElementById('cc-icon-' + id);
        if (!body) return;
        const collapsed = body.style.display === 'none';
        body.style.display = collapsed ? '' : 'none';
        if (icon) icon.className = collapsed ? 'fas fa-chevron-up' : 'fas fa-chevron-down';
        // Re-render chart when expanding so Chart.js gets correct dimensions
        if (collapsed && _dashData) {
            setTimeout(function() {
                if (id === 'revenue' || id === 'bookings' || id === 'fleet' || id === 'topveh') {
                    initCharts(_dashData);
                }
                window.dispatchEvent(new Event('resize'));
            }, 100);
        }
    }

    let charts = {};
    function initCharts(data) {
        if (charts.revenue) charts.revenue.destroy();
        if (charts.bookings) charts.bookings.destroy();
        if (charts.health) charts.health.destroy();
        if (charts.topPie) charts.topPie.destroy();

        const defaultScales = {
            x: { grid: { display: false }, ticks: { color: '#94a3b8', font: { size: 10 } } },
            y: { grid: { color: 'rgba(0,0,0,0.05)' }, ticks: { color: '#94a3b8', font: { size: 10 } } }
        };

        // Revenue Line Chart
        const revTrend = data.revenueTrend || [];
        const revCtx = document.getElementById('revenueChart').getContext('2d');
        charts.revenue = new Chart(revCtx, {
            type: 'line',
            data: {
                labels: revTrend.length > 0 ? revTrend.map(t => t.day.split('-').slice(1).join('/')) : ['No Data'],
                datasets: [{
                    data: revTrend.length > 0 ? revTrend.map(t => t.amount) : [0],
                    borderColor: '#00B14F',
                    borderWidth: 3,
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointBackgroundColor: '#00B14F',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2
                }]
            },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: defaultScales }
        });

        // Bookings Bar Chart ï¿½ use booking status breakdown
        const bookCtx = document.getElementById('bookingsChart');
        if (bookCtx) {
            const bStatus = data.bookingsByStatus || {};
            const bLabels = Object.keys(bStatus).map(k => k.charAt(0).toUpperCase() + k.slice(1));
            const bData = Object.values(bStatus);
            charts.bookings = new Chart(bookCtx.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: bLabels.length ? bLabels : revTrend.map(t => t.day.split('-').slice(1).join('/')),
                    datasets: [{
                        label: 'Bookings',
                        data: bData.length ? bData : revTrend.map(() => 0),
                        backgroundColor: 'rgba(0,82,255,0.6)',
                        borderRadius: 4
                    }]
                },
                options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: defaultScales }
            });
        }

        // Fleet Health doughnut (only if canvas exists)
        const fleetCtxEl = document.getElementById('fleetHealthChart');
        if (fleetCtxEl) {
            const fleetDist = data.fleetDistribution || [];
            if (charts.health) charts.health.destroy();
            charts.health = new Chart(fleetCtxEl.getContext('2d'), {
                type: 'doughnut',
                data: {
                    labels: fleetDist.map(f => f.status),
                    datasets: [{
                        data: fleetDist.map(f => f.count),
                        backgroundColor: ['#00B14F','#f59e0b','#ef4444','#00B14F','#94a3b8'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true, maintainAspectRatio: false, cutout: '75%',
                    plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8', font: { weight: '600', size: 11 }, padding: 20, usePointStyle: true } } }
                }
            });
        }

        // Top Vehicles Pie Chart
        const topVehEl = document.getElementById('topVehiclesPieChart');
        if (topVehEl) {
            const topVeh = (data.topVehicles || []).slice(0, 6);
            if (charts.topPie) charts.topPie.destroy();
            
            const hasData = topVeh.length > 0 && topVeh.some(c => c.booking_count > 0);
            
            if (hasData) {
                charts.topPie = new Chart(topVehEl.getContext('2d'), {
                    type: 'pie',
                    data: {
                        labels: topVeh.map(c => `${c.brand} ${c.model} ${c.plate_number ? '('+c.plate_number+')' : ''}`.trim()),
                        datasets: [{
                            data: topVeh.map(c => c.booking_count || 0),
                            backgroundColor: ['#00B14F','#00B14F','#f59e0b','#ef4444','#00B14F','#5FDBE2'],
                            borderWidth: 0
                        }]
                    },
                    options: {
                        responsive: true, maintainAspectRatio: false,
                        plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8', font: { size: 10 }, padding: 10, usePointStyle: true } } }
                    }
                });
            } else {
                const ctx = topVehEl.getContext('2d');
                ctx.clearRect(0, 0, topVehEl.width, topVehEl.height);
                ctx.font = 'bold 12px Arial';
                ctx.fillStyle = '#94a3b8';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText('No data available', topVehEl.width / 2, topVehEl.height / 2);
            }
        }

        // Make dashboard charts clickable
        makeChartClickable('revenueChart', charts.revenue, 'revenue');
        makeChartClickable('bookingsChart', charts.bookings, 'bookings');
        if (charts.topPie) makeChartClickable('topVehiclesPieChart', charts.topPie, 'topveh');
    }

    // --- EXPANDABLE CHART POPUP LOGIC ---
    let currentPopupChart = null;
    let currentChartType = '';
    let originalChartInstance = null;
    let originalChartData = null;

    function makeChartClickable(canvasId, chartInstance, chartType) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        canvas.style.cursor = 'pointer';
        canvas.onclick = function() {
            openChartPopup(chartInstance, chartType);
        };
    }

    function openChartPopup(chartInstance, chartType) {
        if (!chartInstance) return;
        originalChartInstance = chartInstance;
        currentChartType = chartType;
        originalChartData = JSON.parse(JSON.stringify(chartInstance.data));

        let titleText = 'Chart Details';
        if (chartType === 'revenue') titleText = 'Revenue Details';
        else if (chartType === 'bookings') titleText = 'Booking Details';
        else if (chartType === 'fleet') titleText = 'Fleet Health Details';
        else if (chartType === 'topveh') titleText = 'Vehicle Popularity Details';
        document.getElementById('popupChartTitle').textContent = titleText;

        // Reset filter inputs
        document.getElementById('popupDateFrom').value = '';
        document.getElementById('popupDateTo').value = '';
        document.getElementById('popupStatusFilter').value = 'all';
        document.getElementById('popupVehicleFilter').value = 'all';

        // Adjust visibility of filters based on chart type
        const metricContainer = document.getElementById('popupMetricFilterContainer');
        const limitContainer = document.getElementById('popupLimitFilterContainer');
        if (chartType === 'fleet') {
            document.getElementById('popupStatusFilterContainer').style.display = 'none';
        } else {
            document.getElementById('popupStatusFilterContainer').style.display = '';
        }
        if (chartType === 'topveh') {
            metricContainer.style.display = '';
            limitContainer.style.display = '';
            document.getElementById('popupMetricFilter').value = 'bookings';
            document.getElementById('popupLimitFilter').value = '5';
            document.getElementById('popupStatusFilterContainer').style.display = 'none';
            document.getElementById('popupVehicleFilterContainer').style.display = 'none';
        } else {
            metricContainer.style.display = 'none';
            limitContainer.style.display = 'none';
            document.getElementById('popupVehicleFilterContainer').style.display = '';
        }

        const modal = document.getElementById('chartPopupModal');
        modal.style.display = 'flex';
        // Force reflow
        modal.offsetHeight;
        modal.classList.add('show');

        renderPopupChart();
    }

    function renderPopupChart() {
        const canvas = document.getElementById('popupChartCanvas');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (currentPopupChart) {
            currentPopupChart.destroy();
        }

        const chartData = JSON.parse(JSON.stringify(originalChartData));
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        const textColor = isDark ? '#ffffff' : '#0f1117';
        const gridColor = isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.05)';

        let chartConfig = {
            type: originalChartInstance.config.type,
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom',
                        labels: {
                            color: textColor,
                            font: { family: 'Inter', size: 10, weight: 600 }
                        }
                    }
                }
            }
        };

        if (originalChartInstance.config.type !== 'doughnut' && originalChartInstance.config.type !== 'pie') {
            chartConfig.options.scales = {
                x: {
                    grid: { display: false },
                    ticks: { color: textColor, font: { size: 9 } }
                },
                y: {
                    grid: { color: gridColor },
                    ticks: { color: textColor, font: { size: 9 } }
                }
            };
            if (currentChartType === 'revenue') {
                chartConfig.options.scales.y.ticks.callback = function(value) {
                    return 'â±' + value.toLocaleString();
                };
            }
        } else {
            if (currentChartType === 'fleet') {
                chartConfig.options.cutout = '68%';
            }
        }

        currentPopupChart = new Chart(ctx, chartConfig);
    }

    function closeChartPopup() {
        const modal = document.getElementById('chartPopupModal');
        if (!modal) return;
        modal.classList.remove('show');
        setTimeout(() => {
            modal.style.display = 'none';
            if (currentPopupChart) {
                currentPopupChart.destroy();
                currentPopupChart = null;
            }
        }, 300);
    }

    function closeChartPopupOverlay(event) {
        if (event.target.id === 'chartPopupModal') {
            closeChartPopup();
        }
    }

    async function applyPopupFilters() {
        const dateFrom = document.getElementById('popupDateFrom').value;
        const dateTo = document.getElementById('popupDateTo').value;
        const status = document.getElementById('popupStatusFilter').value;
        const vehicleType = document.getElementById('popupVehicleFilter').value;

        const user = adminAuth.getUser();
        if (!user) return;

        try {
            const url = `${API_URL}/admin/detailed-stats?admin_id=${user.id}&type=${currentChartType}&date_from=${dateFrom}&date_to=${dateTo}&status=${status}&vehicle_type=${vehicleType}`;
            const response = await fetch(url);
            if (!response.ok) throw new Error('Network response was not ok');
            const data = await response.json();

            if (currentChartType === 'revenue') {
                const trend = data.revenueTrend || [];
                originalChartData.labels = trend.map(t => t.day ? t.day.split('-').slice(1).join('/') : t.label || '');
                originalChartData.datasets[0].data = trend.map(t => t.amount || t.revenue || 0);
            } else if (currentChartType === 'bookings') {
                const trend = data.revenueTrend || [];
                originalChartData.labels = trend.map(t => t.day ? t.day.split('-').slice(1).join('/') : t.label || '');
                originalChartData.datasets[0].data = trend.map(t => t.booking_count || t.count || t.bookings || 0);
            } else if (currentChartType === 'fleet') {
                const fleetDist = data.fleetDistribution || [];
                originalChartData.labels = fleetDist.map(f => f.status);
                originalChartData.datasets[0].data = fleetDist.map(f => f.count);
            } else if (currentChartType === 'topveh') {
                const metric = document.getElementById('popupMetricFilter').value || 'bookings';
                const limitVal = document.getElementById('popupLimitFilter').value || '5';
                let topVeh = data.topVehicles || [];
                if (limitVal !== 'all') topVeh = topVeh.slice(0, parseInt(limitVal));
                originalChartData.labels = topVeh.map(c => `${c.brand} ${c.model} ${c.plate_number ? '('+c.plate_number+')' : ''}`.trim());
                if (metric === 'revenue') {
                    originalChartData.datasets[0].data = topVeh.map(c => c.revenue || 0);
                } else {
                    originalChartData.datasets[0].data = topVeh.map(c => c.booking_count || 0);
                }
                // Ensure enough colors
                const pieColors = ['#00B14F','#00B14F','#f59e0b','#ef4444','#00B14F','#5FDBE2','#ec4899','#14b8a6','#f97316','#84cc16','#06b6d4','#a855f7','#e11d48','#0ea5e9','#22d3ee'];
                originalChartData.datasets[0].backgroundColor = pieColors.slice(0, topVeh.length);
            }

            renderPopupChart();
        } catch (error) {
            console.error('Error applying popup filters:', error);
        }
    }

    function resetPopupFilters() {
        document.getElementById('popupDateFrom').value = '';
        document.getElementById('popupDateTo').value = '';
        document.getElementById('popupStatusFilter').value = 'all';
        document.getElementById('popupVehicleFilter').value = 'all';
        document.getElementById('popupMetricFilter').value = 'bookings';
        document.getElementById('popupLimitFilter').value = '5';
        applyPopupFilters();
    }

    // --- INSPECTIONS LOGIC ---
    const Inspections = {
        currentPhotos: [],
        openModal(bookingId, type) {
            const b = Bookings.data.find(x => x.id === bookingId);
            if (!b) return;

            // Reset first, then set values (order matters!)
            document.getElementById('inspectionForm').reset();
            this.currentPhotos = [];
            document.getElementById('inspectPhotoPreview').innerHTML = '';

            document.getElementById('inspectBookingId').value = bookingId;
            document.getElementById('inspectType').value = type;
            document.getElementById('inspectTitle').textContent = type === 'pickup' ? 'Pickup Inspection' : 'Return Inspection';
            document.getElementById('inspectSubtitle').textContent = `Car: ${b.car}`;
            
            document.getElementById('inspectionModal').style.display = 'block';
        },

        handlePhotoSelect(input) {
            if (!input.files) return;
            const preview = document.getElementById('inspectPhotoPreview');
            Array.from(input.files).forEach(file => {
                this.currentPhotos.push(file);
                const reader = new FileReader();
                reader.onload = (e) => {
                    const div = document.createElement('div');
                    div.style.cssText = 'flex: 0 0 100px; height: 100px; border-radius: 12px; overflow: hidden; border: 1px solid var(--border); position: relative;';
                    div.innerHTML = `
                        <img src="${e.target.result}" style="width: 100%; height: 100%; object-fit: cover;">
                        <button type="button" onclick="this.parentElement.remove()" style="position: absolute; top: 5px; right: 5px; background: rgba(239, 68, 68, 0.8); border: none; color: white; width: 20px; height: 20px; border-radius: 50%; font-size: 0.6rem;"><i class="fas fa-times"></i></button>
                    `;
                    preview.appendChild(div);
                };
                reader.readAsDataURL(file);
            });
        },

        async submit(event) {
            event.preventDefault();
            const btn = document.getElementById('inspectSubmitBtn');
            const originalText = btn.innerHTML;
            const bookingId = document.getElementById('inspectBookingId').value;
            const type = document.getElementById('inspectType').value;
            const user = adminAuth.getUser();
            
            const formData = new FormData();
            formData.append('booking_id', bookingId);
            formData.append('inspection_type', type);
            formData.append('mileage', document.getElementById('inspectMileage').value);
            formData.append('fuel_level', document.getElementById('inspectFuel').value);
            formData.append('notes', document.getElementById('inspectNotes').value);
            formData.append('inspector_id', user.id);
            this.currentPhotos.forEach(file => formData.append('photos', file));

            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Submitting...';

            try {
                const res = await fetch(`${API_URL}/inspections/submit`, { method: 'POST', body: formData });
                const data = await res.json();
                if (res.ok) {
                    showNotification('Inspection report submitted!', 'success');
                    document.getElementById('inspectionModal').style.display = 'none';
                    Bookings.refresh();
                } else {
                    showNotification(data.error || 'Submission failed', 'error');
                }
            } catch (err) {
                showNotification('Network error', 'error');
            } finally {
                btn.disabled = false;
                btn.innerHTML = originalText;
            }
        }
    };

    function openChangePasswordModal() {
        document.getElementById('changePasswordModal').style.display = 'flex';
    }

    async function submitChangePassword() {
        const newPass = document.getElementById('newMobilePassword').value;
        const confirmPass = document.getElementById('confirmMobilePassword').value;
        const user = adminAuth.getUser();

        if (!newPass || !confirmPass) {
            alert('Please fill in both fields');
            return;
        }
        if (newPass !== confirmPass) {
            alert('Passwords do not match');
            return;
        }
        if (newPass.length < 6) {
            alert('Password too short (min 6 chars)');
            return;
        }

        try {
            const res = await fetch(`${API_BASE}/api/admin/change-password`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: user.id, new_password: newPass })
            });
            if (res.ok) {
                showNotification('Password updated successfully!', 'success');
                document.getElementById('changePasswordModal').style.display = 'none';
                document.getElementById('newMobilePassword').value = '';
                document.getElementById('confirmMobilePassword').value = '';
            } else {
                const data = await res.json();
                showNotification(data.error || 'Failed to update', 'error');
            }
        } catch (err) { showNotification('Network error', 'error'); }
    }

    function showNotification(message, type = 'info') {
        const container = document.getElementById('notificationContainer');
        if (!container) return;

        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        
        let icon = 'info-circle';
        if (type === 'success') icon = 'check-circle';
        if (type === 'error') icon = 'exclamation-circle';

        notification.innerHTML = `
            <div class="notification-icon"><i class="fas fa-${icon}"></i></div>
            <div style="flex:1; font-size: 0.9rem; font-weight: 500;">${message}</div>
        `;

        container.appendChild(notification);
        setTimeout(() => notification.classList.add('show'), 10);
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 400);
        }, 3500);
    }

    document.addEventListener('DOMContentLoaded', () => {
        adminAuth.initSession();

        // FCM token save function for admin (defined early in script, referenced here for completeness)
        // saveAdminFcmToken is defined at top of script block

        // Login Button Listener
        const loginBtn = document.getElementById('loginBtn');
        if (loginBtn) {
            loginBtn.addEventListener('click', () => {
                adminAuth.login();
            });
        }
        
        // Staff Form Listener
        const staffForm = document.getElementById('staffForm');
        if (staffForm) {
            staffForm.addEventListener('submit', (e) => Staff.submit(e));
        }

        setInterval(() => {
            const now = new Date();
            const headerTime = document.getElementById('headerTime');
            if (headerTime) {
                headerTime.textContent = now.toLocaleString('en-US', {
                    weekday: 'short', month: 'short', day: 'numeric',
                    hour: '2-digit', minute: '2-digit', second: '2-digit'
                });
            }
        }, 1000);

        // Auto-refresh dashboard stats every 60 seconds (silent, no loading flash)
        setInterval(() => {
            if (typeof currentTab !== 'undefined' && currentTab === 'dashboard') {
                refreshDashboard();
            }
        }, 60000);

        // ---- Android Back Button Handler ----
        // Uses custom modal instead of window.confirm() (which is blocked on Android WebView)
        window.showExitConfirm = function() {
            document.getElementById('exitConfirmModal').style.display = 'flex';
        };
        window.hideExitConfirm = function() {
            document.getElementById('exitConfirmModal').style.display = 'none';
        };
        window.confirmExit = function() {
            // Logout then exit
            adminAuth.logoutAndExit();
        };

        // Tab history stack for back navigation
        var _tabHistory = [];
        var _origSwitchTabForBack = window.switchTab;
        window.switchTab = function(tabId) {
            var current = typeof currentTab !== 'undefined' ? currentTab : null;
            if (current && current !== tabId) {
                _tabHistory.push(current);
                if (_tabHistory.length > 10) _tabHistory.shift();
            }
            _origSwitchTabForBack(tabId);
        };

        const handleBackButton = (e) => {
            if (e && e.preventDefault) e.preventDefault();

            // 1. If exit modal is open, close it
            const exitModal = document.getElementById('exitConfirmModal');
            if (exitModal && exitModal.style.display === 'flex') {
                hideExitConfirm();
                return;
            }

            // 2. Close any open modal/overlay
            const modals = document.querySelectorAll('.premium-modal, #inspectionModal, #licensePreviewModal, #changePasswordModal, #bookingDetailsModal, #vehicleModal, #driverModal');
            for (const m of modals) {
                if (m && (m.style.display === 'flex' || m.style.display === 'block')) {
                    m.style.display = 'none';
                    return;
                }
            }

            // 3. Close notification panel if open
            const notifPanel = document.getElementById('adminNotifPanel');
            if (notifPanel && notifPanel.style.display !== 'none') {
                notifPanel.style.display = 'none';
                return;
            }

            // 4. Close side drawer if open
            const drawer = document.getElementById('sideDrawer');
            if (drawer && (drawer.style.left === '0px' || drawer.classList.contains('open'))) {
                toggleDrawer(false);
                return;
            }

            // 5. If on login screen, exit app
            const loginOverlay = document.getElementById('adminLoginOverlay');
            if (loginOverlay && loginOverlay.style.display !== 'none') {
                if (window.Capacitor && window.Capacitor.Plugins && window.Capacitor.Plugins.App) {
                    window.Capacitor.Plugins.App.exitApp();
                }
                return;
            }

            // 6. Navigate back through tab history
            if (_tabHistory.length > 0) {
                var prevTab = _tabHistory.pop();
                _origSwitchTabForBack(prevTab);
                return;
            }

            // 7. On root tab ï¿½ show exit confirmation
            showExitConfirm();
        };

        // Register for both Capacitor and Cordova back button events
        (function() {
            function _adminBackListener(e) {
                if (e && e.preventDefault) e.preventDefault();
                handleBackButton(e);
            }
            document.addEventListener('backbutton', _adminBackListener, false);
            document.addEventListener('deviceready', function() {
                document.removeEventListener('backbutton', _adminBackListener, false);
                document.addEventListener('backbutton', _adminBackListener, false);
                if (window.Capacitor && window.Capacitor.Plugins && window.Capacitor.Plugins.App) {
                    window.Capacitor.Plugins.App.addListener('backButton', function() {
                        handleBackButton();
                    });
                }
                
                // Initialize Push Notifications for Admin
                if (window.Capacitor && window.Capacitor.Plugins && window.Capacitor.Plugins.PushNotifications) {
                    const PushNotifications = window.Capacitor.Plugins.PushNotifications;
                    
                    // Request permission
                    PushNotifications.requestPermissions().then(function(result) {
                        if (result.receive === 'granted') {
                            PushNotifications.register();
                        }
                    });
                    
                    // Listen for registration success
                    PushNotifications.addListener('registration', function(token) {
                        console.log('Admin FCM Token:', token.value);
                        window._adminFcmToken = token.value;
                        saveAdminFcmToken(token.value);
                    });
                    
                    // Listen for registration errors
                    PushNotifications.addListener('registrationError', function(error) {
                        console.error('Admin FCM Registration Error:', error);
                    });
                    
                    // Listen for push notifications received
                    PushNotifications.addListener('pushNotificationReceived', function(notification) {
                        console.log('Admin Push notification received:', notification);
                        // Show in-app notification
                        showNotification(notification.title || 'New Notification', 'info');
                        
                        // Refresh chat if on chat tab
                        const user = adminAuth.getUser();
                        if (user && typeof AdminChat !== 'undefined') {
                            AdminChat.updateNavBadge();
                        }
                    });
                    
                    // Listen for notification taps
                    PushNotifications.addListener('pushNotificationActionPerformed', function(notification) {
                        console.log('Admin Push notification action performed:', notification);
                        // Navigate to chat tab
                        switchTab('chat');
                    });
                }
            }, false);
        })();
    });

    // Global Bindings for HTML Access
    window.adminAuth = adminAuth;
    window.toggleDarkMode = toggleDarkMode;
    window.toggleSystemConfigModal = toggleSystemConfigModal;
    window.closeSystemConfigModal = closeSystemConfigModal;
    window.closeSystemConfigModalBackdrop = closeSystemConfigModalBackdrop;
    window.Vehicles = Vehicles;
    window.Bookings = Bookings;
    window.Drivers = Drivers;
    window.Verifications = Verifications;
    window.Tickets = Tickets;
    window.Instructions = Instructions;
    window.Staff = Staff;
    window.GPS = GPS;
    window.Activity = Activity;
    window.Reports = Reports;
    window.Settings = Settings;
    window.switchTab = switchTab;
    window.toggleDrawer = toggleDrawer;
    window.showNotification = showNotification;
    window.refreshDashboard = refreshDashboard;
    window.openChangePasswordModal = openChangePasswordModal;
    window.submitChangePassword = submitChangePassword;
    window.navTo = navTo;

    // ??? USER MANAGEMENT MODULE ???????????????????????????????????????????
    const UserMgmt = {
        _all: [],
        _filter: 'all',

        async refresh() {
            document.getElementById('umList').innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-muted);"><i class="fas fa-spinner fa-spin" style="font-size:1.5rem;"></i></div>';
            try {
                const res = await apiFetch('admin/users/list');
                const data = await res.json();
                if (!res.ok) throw new Error(data.error || 'Failed to load users');
                this._all = data;
                this._updateStats();
                this.applyFilters();
            } catch (e) {
                document.getElementById('umList').innerHTML = `<div style="text-align:center;padding:40px;color:var(--danger);">${e.message}</div>`;
            }
        },

        _updateStats() {
            const total = this._all.length;
            const verified = this._all.filter(u => u.is_verified === 2).length;
            const frozen = this._all.filter(u => u.is_frozen).length;
            document.getElementById('umTotalCount').textContent = total;
            document.getElementById('umVerifiedCount').textContent = verified;
            document.getElementById('umFrozenCount').textContent = frozen;
        },

        setFilter(f, btn) {
            this._filter = f;
            document.querySelectorAll('.um-filter-btn').forEach(b => {
                b.style.background = 'transparent';
                b.style.color = 'var(--text-muted)';
                b.style.borderColor = 'var(--border)';
            });
            btn.style.background = 'var(--primary)';
            btn.style.color = 'white';
            btn.style.borderColor = 'var(--primary)';
            this.applyFilters();
        },

        applyFilters() {
            const q = (document.getElementById('umSearch').value || '').toLowerCase();
            let list = this._all;
            if (this._filter === 'verified') list = list.filter(u => u.is_verified === 2);
            else if (this._filter === 'unverified') list = list.filter(u => u.is_verified !== 2);
            else if (this._filter === 'frozen') list = list.filter(u => u.is_frozen);
            if (q) list = list.filter(u =>
                (u.full_name || '').toLowerCase().includes(q) ||
                (u.email || '').toLowerCase().includes(q) ||
                (u.phone || '').toLowerCase().includes(q)
            );
            this._render(list);
        },

        _render(list) {
            const el = document.getElementById('umList');
            if (!list.length) {
                el.innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-muted);">No users found</div>';
                return;
            }
            el.innerHTML = list.map(u => {
                const verifiedBadge = u.is_verified === 2
                    ? `<span style="background:rgba(0,177,79,0.15);color:var(--success);padding:3px 8px;border-radius:20px;font-size:0.6rem;font-weight:800;">VERIFIED</span>`
                    : u.is_verified === 1
                    ? `<span style="background:rgba(245,158,11,0.15);color:var(--amber);padding:3px 8px;border-radius:20px;font-size:0.6rem;font-weight:800;">PENDING</span>`
                    : `<span style="background:rgba(148,163,184,0.1);color:var(--text-muted);padding:3px 8px;border-radius:20px;font-size:0.6rem;font-weight:800;">UNVERIFIED</span>`;
                const frozenBadge = u.is_frozen
                    ? `<span style="background:rgba(239,68,68,0.15);color:var(--danger);padding:3px 8px;border-radius:20px;font-size:0.6rem;font-weight:800;margin-left:4px;">FROZEN</span>`
                    : '';
                const avatar = u.full_name ? u.full_name.charAt(0).toUpperCase() : '?';
                const joined = u.created_at ? new Date(u.created_at).toLocaleDateString('en-PH', {month:'short', day:'numeric', year:'numeric'}) : 'ï¿½';
                return `
                <div onclick="UserMgmt.openModal(${u.id})" style="background:var(--surface);border:1px solid var(--border);border-radius:18px;padding:16px;margin-bottom:12px;cursor:pointer;transition:all 0.2s;display:flex;align-items:center;gap:14px;">
                    <div style="width:46px;height:46px;border-radius:50%;background:linear-gradient(135deg,var(--primary),#005339);display:flex;align-items:center;justify-content:center;font-weight:900;font-size:1.1rem;flex-shrink:0;">${avatar}</div>
                    <div style="flex:1;min-width:0;">
                        <div style="font-weight:800;font-size:0.9rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${u.full_name || 'No Name'}</div>
                        <div style="font-size:0.72rem;color:var(--text-muted);margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${u.email}</div>
                        <div style="margin-top:6px;display:flex;align-items:center;flex-wrap:wrap;gap:4px;">${verifiedBadge}${frozenBadge}</div>
                    </div>
                    <div style="text-align:right;flex-shrink:0;">
                        <div style="font-size:0.65rem;color:var(--text-muted);">${joined}</div>
                        <div style="font-size:0.7rem;color:var(--amber);margin-top:4px;font-weight:700;"><i class="fas fa-star" style="font-size:0.6rem;"></i> ${u.loyalty_points || 0} pts</div>
                    </div>
                </div>`;
            }).join('');
        },

        async openModal(userId) {
            document.getElementById('umModal').style.display = 'block';
            document.getElementById('umModalContent').innerHTML = '<div style="text-align:center;padding:30px;color:var(--text-muted);"><i class="fas fa-spinner fa-spin" style="font-size:1.5rem;"></i></div>';
            try {
                const [res, licRes] = await Promise.all([
                    apiFetch(`admin/users/${userId}`),
                    fetch(`${API_BASE}/api/admin/users/${userId}/license-details`)
                ]);
                const u = await res.json();
                if (!res.ok) throw new Error(u.error || 'Failed to load user');
                
                let lData = null;
                if (licRes.ok) {
                    lData = await licRes.json();
                }
                this._renderModal(u, lData);
            } catch (e) {
                document.getElementById('umModalContent').innerHTML = `<div style="color:var(--danger);text-align:center;padding:20px;">${e.message}</div>`;
            }
        },

        _renderModal(u, lData) {
            const verifiedLabel = u.is_verified === 2 ? 'Verified' : u.is_verified === 1 ? 'Pending' : 'Unverified';
            const verifiedColor = u.is_verified === 2 ? 'var(--success)' : u.is_verified === 1 ? 'var(--amber)' : 'var(--text-muted)';
            const frozenLabel = u.is_frozen ? 'Frozen' : 'Active';
            const frozenColor = u.is_frozen ? 'var(--danger)' : 'var(--success)';
            const joined = u.created_at ? new Date(u.created_at).toLocaleDateString('en-PH', {month:'long', day:'numeric', year:'numeric'}) : 'ï¿½';
            const avatar = u.full_name ? u.full_name.charAt(0).toUpperCase() : '?';

            document.getElementById('umModalContent').innerHTML = `
            <!-- Avatar & Name -->
            <div style="text-align:center;margin-bottom:20px;">
                <div style="width:70px;height:70px;border-radius:50%;background:linear-gradient(135deg,var(--primary),#005339);display:flex;align-items:center;justify-content:center;font-weight:900;font-size:1.8rem;margin:0 auto 12px;">${avatar}</div>
                <div style="font-size:1.1rem;font-weight:900;">${u.full_name || 'No Name'}</div>
                <div style="font-size:0.8rem;color:var(--text-muted);">${u.email}</div>
                <div style="display:flex;justify-content:center;gap:8px;margin-top:8px;">
                    <span style="color:${verifiedColor};font-size:0.7rem;font-weight:800;background:rgba(255,255,255,0.05);padding:4px 10px;border-radius:20px;">${verifiedLabel}</span>
                    <span style="color:${frozenColor};font-size:0.7rem;font-weight:800;background:rgba(255,255,255,0.05);padding:4px 10px;border-radius:20px;">${frozenLabel}</span>
                </div>
            </div>

            <!-- Stats -->
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:20px;">
                <div style="background:rgba(0,0,0,0.2);border-radius:14px;padding:12px;text-align:center;">
                    <div style="font-size:1.2rem;font-weight:900;color:var(--primary-light);">${u.total_bookings || 0}</div>
                    <div style="font-size:0.6rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;">Bookings</div>
                </div>
                <div style="background:rgba(0,0,0,0.2);border-radius:14px;padding:12px;text-align:center;">
                    <div style="font-size:1.2rem;font-weight:900;color:var(--success);">${u.completed_bookings || 0}</div>
                    <div style="font-size:0.6rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;">Completed</div>
                </div>
                <div style="background:rgba(0,0,0,0.2);border-radius:14px;padding:12px;text-align:center;">
                    <div style="font-size:1rem;font-weight:900;color:var(--amber);">₱${(u.total_spent||0).toLocaleString()}</div>
                    <div style="font-size:0.6rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;">Spent</div>
                </div>
            </div>

            <!-- License Details Section -->
            <div style="background: rgba(15, 23, 42, 0.4); padding: 15px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 20px;">
                <h3 style="font-size: 1rem; color: #00B14F; font-weight: 800; margin-bottom: 10px;">Driver's License Details</h3>
                ${lData && lData.license_number ? `
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 0.85rem;">
                        <div><span style="color:var(--text-muted)">License #:</span> <span style="color:white;font-weight:600">${lData.license_number}</span></div>
                        <div><span style="color:var(--text-muted)">Expiry:</span> <span style="color:white;font-weight:600">${lData.expiry_date || '-'}</span></div>
                        <div><span style="color:var(--text-muted)">Class:</span> <span style="color:white;font-weight:600">${lData.license_class || '-'}</span></div>
                        <div><span style="color:var(--text-muted)">Country/State:</span> <span style="color:white;font-weight:600">${lData.issuing_country_state || '-'}</span></div>
                    </div>
                    <div style="margin-top: 10px; font-size: 0.85rem;">
                        <div><span style="color:var(--text-muted)">Full Name:</span> <span style="color:white;font-weight:600">${lData.full_name || '-'}</span></div>
                        <div><span style="color:var(--text-muted)">DOB:</span> <span style="color:white;font-weight:600">${lData.date_of_birth || '-'}</span></div>
                    </div>
                    <div style="margin-top: 10px; font-size: 0.85rem; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.1);">
                        <p style="color:var(--text-muted);font-weight:700;margin-bottom:5px;">Emergency Contact</p>
                        <div><span style="color:var(--text-muted)">Name:</span> <span style="color:white;font-weight:600">${lData.emergency_contact_name || '-'}</span></div>
                        <div><span style="color:var(--text-muted)">Phone:</span> <span style="color:white;font-weight:600">${lData.emergency_contact_phone || '-'}</span></div>
                        <div><span style="color:var(--text-muted)">Rel:</span> <span style="color:white;font-weight:600">${lData.emergency_contact_relationship || '-'}</span></div>
                    </div>
                    <div style="display:flex; gap:10px; margin-top: 10px;">
                        ${lData.license_front_url ? `<button onclick="viewLicenseImage('${lData.license_front_url}')" class="btn-outline" style="flex:1;font-size:0.75rem;padding:6px;">Front Image</button>` : ''}
                        ${lData.license_back_url ? `<button onclick="viewLicenseImage('${lData.license_back_url}')" class="btn-outline" style="flex:1;font-size:0.75rem;padding:6px;">Back Image</button>` : ''}
                    </div>
                ` : `<p style="font-size: 0.85rem; color: var(--text-muted);">No license details provided by user.</p>`}
            </div>

            <!-- Info -->
            <div style="background:rgba(0,0,0,0.2);border-radius:14px;padding:14px;margin-bottom:16px;">
                <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--border);font-size:0.8rem;"><span style="color:var(--text-muted);">Phone</span><span>${u.phone || 'ï¿½'}</span></div>
                <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--border);font-size:0.8rem;"><span style="color:var(--text-muted);">Loyalty Points</span><span style="color:var(--amber);font-weight:700;">${u.loyalty_points || 0} pts</span></div>
                <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--border);font-size:0.8rem;"><span style="color:var(--text-muted);">Auth Provider</span><span>${u.auth_provider || 'Email'}</span></div>
                <div style="display:flex;justify-content:space-between;padding:8px 0;font-size:0.8rem;"><span style="color:var(--text-muted);">Joined</span><span>${joined}</span></div>
            </div>

            <!-- Edit Form -->
            <div style="background:rgba(0,0,0,0.2);border-radius:14px;padding:14px;margin-bottom:16px;">
                <div style="font-size:0.7rem;color:var(--text-muted);font-weight:800;text-transform:uppercase;margin-bottom:12px;">Edit Info</div>
                <input id="umEditName" type="text" value="${u.full_name || ''}" placeholder="Full Name" style="width:100%;padding:11px 14px;background:rgba(255,255,255,0.05);border:1px solid var(--border);border-radius:10px;color:white;font-size:0.85rem;margin-bottom:10px;">
                <input id="umEditPhone" type="text" value="${u.phone || ''}" placeholder="Phone Number" style="width:100%;padding:11px 14px;background:rgba(255,255,255,0.05);border:1px solid var(--border);border-radius:10px;color:white;font-size:0.85rem;margin-bottom:10px;">
                <button onclick="UserMgmt.saveEdit(${u.id})" style="width:100%;padding:12px;background:var(--primary);border:none;border-radius:10px;color:white;font-weight:700;font-size:0.85rem;">Save Changes</button>
            </div>

            <!-- Loyalty Points -->
            <div style="background:rgba(0,0,0,0.2);border-radius:14px;padding:14px;margin-bottom:16px;">
                <div style="font-size:0.7rem;color:var(--text-muted);font-weight:800;text-transform:uppercase;margin-bottom:12px;"><i class="fas fa-star" style="color:var(--amber);margin-right:6px;"></i>Loyalty Points</div>
                <input id="umLoyaltyInput" type="number" value="${u.loyalty_points || 0}" placeholder="Points" style="width:100%;padding:12px 14px;background:rgba(255,255,255,0.05);border:1px solid var(--border);border-radius:10px;color:white;font-size:0.9rem;margin-bottom:10px;">
                <button onclick="UserMgmt.setLoyalty(${u.id})" style="width:100%;padding:12px;background:rgba(245,158,11,0.15);border:1px solid var(--amber);border-radius:10px;color:var(--amber);font-weight:700;font-size:0.85rem;">Update Points</button>
            </div>

            <!-- Reset Password -->
            <div style="background:rgba(0,0,0,0.2);border-radius:14px;padding:14px;margin-bottom:16px;">
                <div style="font-size:0.7rem;color:var(--text-muted);font-weight:800;text-transform:uppercase;margin-bottom:12px;"><i class="fas fa-key" style="color:var(--primary-light);margin-right:6px;"></i>Reset Password</div>
                <input id="umNewPass" type="password" placeholder="New password (min 8 chars)" style="width:100%;padding:12px 14px;background:rgba(255,255,255,0.05);border:1px solid var(--border);border-radius:10px;color:white;font-size:0.9rem;margin-bottom:10px;">
                <button onclick="UserMgmt.resetPassword(${u.id})" style="width:100%;padding:12px;background:rgba(0,177,79,0.15);border:1px solid var(--primary);border-radius:10px;color:var(--primary-light);font-weight:700;font-size:0.85rem;">Reset Password</button>
            </div>

            <!-- Freeze / Unfreeze -->
            <div style="background:rgba(0,0,0,0.2);border-radius:14px;padding:14px;margin-bottom:16px;">
                <div style="font-size:0.7rem;color:var(--text-muted);font-weight:800;text-transform:uppercase;margin-bottom:12px;">${u.is_frozen ? 'Unfreeze Account' : 'Freeze Account'}</div>
                ${!u.is_frozen ? `<input id="umFreezeReason" type="text" placeholder="Reason for freezing..." style="width:100%;padding:11px 14px;background:rgba(255,255,255,0.05);border:1px solid var(--border);border-radius:10px;color:white;font-size:0.85rem;margin-bottom:10px;">` : `<p style="font-size:0.8rem;color:var(--text-muted);margin-bottom:10px;">Reason: ${u.freeze_reason || 'No reason provided'}</p>`}
                <button onclick="UserMgmt.toggleFreeze(${u.id}, ${u.is_frozen})" style="width:100%;padding:12px;background:${u.is_frozen ? 'rgba(0,177,79,0.15)' : 'rgba(239,68,68,0.15)'};border:1px solid ${u.is_frozen ? 'var(--success)' : 'var(--danger)'};border-radius:10px;color:${u.is_frozen ? 'var(--success)' : 'var(--danger)'};font-weight:700;font-size:0.85rem;">
                    <i class="fas fa-${u.is_frozen ? 'unlock' : 'lock'}"></i> ${u.is_frozen ? 'Unfreeze Account' : 'Freeze Account'}
                </button>
            </div>

            <!-- Delete -->
            <button onclick="UserMgmt.deleteUser(${u.id}, '${(u.full_name||'').replace(/'/g,"\\'")}' )" style="width:100%;padding:14px;background:rgba(239,68,68,0.1);border:1px solid var(--danger);border-radius:14px;color:var(--danger);font-weight:800;font-size:0.9rem;margin-bottom:10px;">
                <i class="fas fa-trash-alt"></i> Delete Account Permanently
            </button>`;
        },

        closeModal() {
            document.getElementById('umModal').style.display = 'none';
        },

        async saveEdit(userId) {
            const name = document.getElementById('umEditName').value.trim();
            const phone = document.getElementById('umEditPhone').value.trim();
            if (!name) { alert('Full name is required'); return; }
            try {
                const res = await apiFetch(`admin/users/${userId}/edit`, {
                    method: 'PUT',
                    headers: {'Content-Type':'application/json'},
                    body: JSON.stringify({full_name: name, phone})
                });
                const d = await res.json();
                if (!res.ok) throw new Error(d.error);
                showNotification(d.message || 'User updated', 'success');
                this.refresh();
                this.openModal(userId);
            } catch (e) { alert(e.message); }
        },

        async setLoyalty(userId) {
            const pts = document.getElementById('umLoyaltyInput').value;
            if (pts === '' || isNaN(pts)) { alert('Enter a valid number'); return; }
            try {
                const res = await apiFetch(`admin/users/${userId}/loyalty`, {
                    method: 'PUT',
                    headers: {'Content-Type':'application/json'},
                    body: JSON.stringify({points: parseInt(pts)})
                });
                const d = await res.json();
                if (!res.ok) throw new Error(d.error);
                showNotification(d.message || 'Points updated', 'success');
                this.refresh();
                this.openModal(userId);
            } catch (e) { alert(e.message); }
        },

        async resetPassword(userId) {
            const pass = document.getElementById('umNewPass').value;
            if (pass.length < 8) { alert('Password must be at least 8 characters'); return; }
            if (!confirm('Reset this user\'s password?')) return;
            try {
                const res = await apiFetch(`admin/users/${userId}/reset-password`, {
                    method: 'POST',
                    headers: {'Content-Type':'application/json'},
                    body: JSON.stringify({new_password: pass})
                });
                const d = await res.json();
                if (!res.ok) throw new Error(d.error);
                showNotification(d.message || 'Password reset', 'success');
                document.getElementById('umNewPass').value = '';
            } catch (e) { alert(e.message); }
        },

        async toggleFreeze(userId, currentlyFrozen) {
            const freeze = !currentlyFrozen;
            let reason = '';
            if (freeze) {
                reason = (document.getElementById('umFreezeReason') || {}).value || '';
                if (!reason.trim()) { alert('Please enter a reason for freezing'); return; }
            }
            if (!confirm(freeze ? 'Freeze this account?' : 'Unfreeze this account?')) return;
            try {
                const res = await apiFetch(`admin/users/${userId}/freeze`, {
                    method: 'POST',
                    headers: {'Content-Type':'application/json'},
                    body: JSON.stringify({freeze, reason})
                });
                const d = await res.json();
                if (!res.ok) throw new Error(d.error);
                showNotification(d.message || 'Account updated', 'success');
                this.refresh();
                this.openModal(userId);
            } catch (e) { alert(e.message); }
        },

        async deleteUser(userId, name) {
            if (!confirm(`Permanently delete "${name}"? This cannot be undone.`)) return;
            if (!confirm('Are you absolutely sure? All bookings and data will be removed.')) return;
            try {
                const res = await apiFetch(`admin/users/${userId}`, {method: 'DELETE'});
                const d = await res.json();
                if (!res.ok) throw new Error(d.error);
                showNotification(d.message || 'User deleted', 'success');
                this.closeModal();
                this.refresh();
            } catch (e) { alert(e.message); }
        },

        async exportCSV() {
            try {
                const url = `${API_URL}/admin/users/export`;
                const a = document.createElement('a');
                a.href = url;
                a.download = 'users_export.csv';
                a.click();
            } catch (e) { alert('Export failed: ' + e.message); }
        }
    };

    window.UserMgmt = UserMgmt;

    // Auto-load when users tab is opened
    const _origSwitchTab = window.switchTab;
    window.switchTab = function(tabId) {
        _origSwitchTab(tabId);
        if (tabId === 'users' && UserMgmt._all.length === 0) {
            UserMgmt.refresh();
        }
    };
    // ??? END USER MANAGEMENT MODULE ???????????????????????????????????????

    // ============================================================
    // ADMIN CHAT MODULE
    // ============================================================
    const AdminChat = (function () {
        let _pollTimer = null;
        let _currentUserId = null;
        let _currentUserName = '';
        let _lastMsgId = 0;
        let _view = 'inbox'; // 'inbox' | 'conversation'
        let allConversations = [];
        let filteredConversations = [];

        function _esc(str) {
            if (!str) return '';
            return String(str)
                .replace(/&/g, '&amp;').replace(/</g, '&lt;')
                .replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
        }

        function _adminId() {
            const u = adminAuth.getUser();
            return u ? u.id : null;
        }

        // Search utility functions
        function escapeRegex(str) {
            return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        }

        function highlightText(text, searchTerm) {
            if (!text || !searchTerm) return text || '';
            const regex = new RegExp('(' + escapeRegex(searchTerm) + ')', 'gi');
            return text.replace(regex, '<mark class="search-highlight">$1</mark>');
        }

        // ?? Inbox ??????????????????????????????????????????????
        function loadInbox() {
            stopPolling();
            _currentUserId = null;
            _view = 'inbox';
            const el = document.getElementById('adminChatContent');
            if (!el) return;
            const aid = _adminId();
            if (!aid) {
                el.innerHTML = '<p style="color:var(--text-muted);text-align:center;padding:40px;">Please log in first.</p>';
                return;
            }

            el.innerHTML =
                '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">' +
                    '<h1 class="page-title" style="margin:0;">Live Chat</h1>' +
                    '<button onclick="AdminChat.loadInbox()" style="background:var(--surface);border:1px solid var(--border);color:var(--text-main);width:40px;height:40px;border-radius:12px;cursor:pointer;font-size:0.9rem;"><i class="fas fa-sync-alt"></i></button>' +
                '</div>' +
                '<!-- Chat Search Container -->' +
                '<div class="chat-search-container" style="margin-bottom:16px;">' +
                    '<div class="search-box" style="position:relative;display:flex;align-items:center;">' +
                        '<span class="search-icon" style="position:absolute;left:12px;font-size:1.2rem;color:var(--text-muted);"><i class="fas fa-search"></i></span>' +
                        '<input type="text" id="chatSearchInput" placeholder="Search conversations by name, email, or message..." autocomplete="off"' +
                            ' oninput="AdminChat.searchConversations(this.value)"' +
                            ' style="width:100%;padding:0.75rem 2.5rem 0.75rem 2.5rem;background:rgba(255,255,255,0.05);border:1px solid var(--border);border-radius:8px;color:var(--text-primary);font-size:0.95rem;outline:none;box-sizing:border-box;"' +
                            ' onfocus="this.style.borderColor=\'var(--primary)\';this.style.boxShadow=\'0 0 0 3px var(--primary-glow)\'"' +
                            ' onblur="this.style.borderColor=\'var(--border)\';this.style.boxShadow=\'none\'">' +
                        '<button class="clear-search hidden" id="clearSearch" onclick="AdminChat.clearSearch()"' +
                            ' style="position:absolute;right:8px;background:none;border:none;color:var(--text-muted);cursor:pointer;padding:4px 8px;border-radius:4px;transition:all 0.2s ease;"' +
                            ' onmouseover="this.style.background=\'rgba(255,255,255,0.1)\';this.style.color=\'var(--text-primary)\'"' +
                            ' onmouseout="this.style.background=\'none\';this.style.color=\'var(--text-muted)\'">' +
                            '<i class="fas fa-times"></i>' +
                        '</button>' +
                    '</div>' +
                    '<div class="search-results-count hidden" id="searchResultsCount"' +
                        ' style="margin-top:0.5rem;padding:0.5rem;background:rgba(0,177,79,0.1);border-radius:6px;text-align:center;">' +
                        '<span id="resultsText" style="font-size:0.85rem;color:var(--primary);font-weight:600;"></span>' +
                    '</div>' +
                '</div>' +
                '<div id="acInboxList" style="margin-bottom:16px;"><div style="text-align:center;padding:30px;color:var(--text-muted);"><i class="fas fa-spinner fa-spin"></i></div></div>' +
                '<button onclick="AdminChat.showUserSearch()" style="width:100%;padding:13px;background:var(--primary);border:none;border-radius:14px;color:#fff;font-weight:700;font-size:0.85rem;cursor:pointer;">' +
                    '<i class="fas fa-plus" style="margin-right:6px;"></i>Start New Conversation' +
                '</button>' +
                '<div id="acUserSearch" style="display:none;margin-top:12px;">' +
                    '<input type="text" id="acUserSearchInput" placeholder="Search by name or email..." oninput="AdminChat.searchUsers(this.value)"' +
                        ' style="width:100%;padding:12px 14px;background:var(--surface);border:1px solid var(--border);border-radius:12px;color:var(--text-main);font-size:0.85rem;box-sizing:border-box;">' +
                    '<div id="acUserSearchResults" style="margin-top:8px;"></div>' +
                '</div>';

            loadConversations();
        }

        // Load conversations from API
        function loadConversations() {
            const aid = _adminId();
            if (!aid) return;

            fetch(API_URL + '/chat/inbox?viewer_type=admin&viewer_id=' + aid)
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    if (Array.isArray(data)) {
                        allConversations = data;
                        filteredConversations = data.slice();
                        renderConversations(filteredConversations);
                    } else {
                        allConversations = [];
                        filteredConversations = [];
                        renderConversations([]);
                    }
                })
                .catch(function() {
                    const list = document.getElementById('acInboxList');
                    if (list) list.innerHTML = '<div style="text-align:center;padding:20px;color:var(--danger);">Failed to load. Tap refresh.</div>';
                });
        }

        // Search conversations
        function searchConversations(query) {
            const searchTerm = (query || '').toLowerCase().trim();
            
            if (!searchTerm) {
                filteredConversations = allConversations.slice();
                const resultsCount = document.getElementById('searchResultsCount');
                const clearBtn = document.getElementById('clearSearch');
                if (resultsCount) resultsCount.classList.add('hidden');
                if (clearBtn) clearBtn.classList.add('hidden');
                renderConversations(filteredConversations);
                return;
            }
            
            const clearBtn = document.getElementById('clearSearch');
            if (clearBtn) clearBtn.classList.remove('hidden');
            
            filteredConversations = allConversations.filter(function(conv) {
                // Search in customer name
                if (conv.other_name && conv.other_name.toLowerCase().includes(searchTerm)) {
                    return true;
                }
                // Search in email (if available)
                if (conv.other_email && conv.other_email.toLowerCase().includes(searchTerm)) {
                    return true;
                }
                // Search in last message content
                if (conv.last_message && conv.last_message.toLowerCase().includes(searchTerm)) {
                    return true;
                }
                return false;
            });
            
            // Show results count
            const resultsCount = document.getElementById('searchResultsCount');
            const resultsText = document.getElementById('resultsText');
            if (resultsCount && resultsText) {
                resultsText.textContent = filteredConversations.length + ' conversation' + (filteredConversations.length !== 1 ? 's' : '') + ' found';
                resultsCount.classList.remove('hidden');
            }
            
            renderConversations(filteredConversations);
        }

        // Clear search
        function clearSearch() {
            const searchInput = document.getElementById('chatSearchInput');
            if (searchInput) searchInput.value = '';
            searchConversations('');
        }

        // Render conversations
        function renderConversations(conversations) {
            const list = document.getElementById('acInboxList');
            if (!list) return;
            
            // Handle empty conversations
            if (!conversations || conversations.length === 0) {
                const searchInput = document.getElementById('chatSearchInput');
                const hasSearchTerm = searchInput && searchInput.value.trim();
                
                // Display "No results found" message when search is active
                if (hasSearchTerm) {
                    list.innerHTML = '<div class="no-results" style="text-align:center;padding:3rem 1rem;color:var(--text-muted);font-size:0.95rem;">No results found</div>';
                } else {
                    // Display default empty state when no search is active
                    list.innerHTML =
                        '<div style="text-align:center;padding:24px 16px;color:var(--text-muted);">' +
                            '<i class="fas fa-comments" style="font-size:2.5rem;margin-bottom:10px;display:block;opacity:0.3;"></i>' +
                            '<p style="font-size:0.85rem;margin:0;">No conversations yet.<br>Use the button below to start one.</p>' +
                        '</div>';
                }
                return;
            }
            
            // Get search term for highlighting
            const searchInput = document.getElementById('chatSearchInput');
            const searchTerm = searchInput ? searchInput.value.toLowerCase().trim() : '';
            
            // Render conversation items with highlighted search terms
            list.innerHTML = conversations.map(function(c) {
                const initials = (c.other_name || 'U').charAt(0).toUpperCase();
                const unread = parseInt(c.unread_count) || 0;
                
                // Format time metadata
                const ts = c.last_at ? new Date(c.last_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '';
                
                // Apply highlighting using highlightText() helper for search term highlighting
                const displayName = searchTerm ? highlightText(_esc(c.other_name), searchTerm) : _esc(c.other_name);
                const displayMessage = searchTerm ? highlightText(_esc(c.last_message || ''), searchTerm) : _esc(c.last_message || '');
                
                // Use data attributes to avoid XSS in onclick - escape for HTML attribute context
                const escapedName = _esc(c.other_name);
                
                // Render conversation item with metadata (time, unread count)
                return '<div class="ac-inbox-item" onclick="AdminChat.openConversation(' + c.other_id + ',\'' + escapedName + '\')">' +
                    '<div class="ac-avatar">' + initials + '</div>' +
                    '<div class="ac-inbox-info">' +
                        '<div class="ac-inbox-name">' + displayName + '</div>' +
                        '<div class="ac-inbox-preview">' + displayMessage + '</div>' +
                    '</div>' +
                    '<div style="display:flex;flex-direction:column;align-items:flex-end;gap:4px;flex-shrink:0;">' +
                        '<span style="font-size:0.65rem;color:var(--text-muted);">' + ts + '</span>' +
                        (unread ? '<span class="ac-unread">' + unread + '</span>' : '') +
                    '</div>' +
                '</div>';
            }).join('');
        }
        function showUserSearch() {
            const box = document.getElementById('acUserSearch');
            if (!box) return;
            const isHidden = box.style.display === 'none';
            box.style.display = isHidden ? 'block' : 'none';
            if (isHidden) {
                const inp = document.getElementById('acUserSearchInput');
                if (inp) { inp.value = ''; inp.focus(); }
                const res = document.getElementById('acUserSearchResults');
                if (res) res.innerHTML = '';
            }
        }

        function searchUsers(q) {
            const res = document.getElementById('acUserSearchResults');
            if (!res) return;
            if (!q || q.length < 2) { res.innerHTML = ''; return; }
            fetch(API_URL + '/users/search?q=' + encodeURIComponent(q) + '&limit=10')
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    if (!Array.isArray(data) || !data.length) {
                        res.innerHTML = '<p style="font-size:0.8rem;color:var(--text-muted);padding:8px 0;">No users found.</p>';
                        return;
                    }
                    res.innerHTML = data.map(function(u) {
                        const name = u.full_name || 'Unknown';
                        return '<div class="ac-inbox-item" style="margin-bottom:4px;" onclick="AdminChat.openConversation(' + u.id + ',\'' + _esc(name) + '\')">' +
                            '<div class="ac-avatar" style="font-size:0.85rem;">' + name.charAt(0).toUpperCase() + '</div>' +
                            '<div class="ac-inbox-info">' +
                                '<div class="ac-inbox-name">' + _esc(name) + '</div>' +
                                '<div class="ac-inbox-preview">' + _esc(u.email || '') + '</div>' +
                            '</div>' +
                            '<i class="fas fa-chevron-right" style="color:var(--text-muted);"></i>' +
                        '</div>';
                    }).join('');
                })
                .catch(function() {
                    res.innerHTML = '<p style="font-size:0.8rem;color:var(--danger);padding:8px 0;">Search failed.</p>';
                });
        }

        // ?? Conversation ???????????????????????????????????????
        function openConversation(userId, userName) {
            stopPolling();
            _currentUserId = userId;
            _currentUserName = userName;
            _lastMsgId = 0;
            _view = 'conversation';

            const el = document.getElementById('adminChatContent');
            if (!el) return;

            el.innerHTML =
                '<div style="display:flex;align-items:center;gap:12px;padding-bottom:14px;border-bottom:1px solid var(--border);margin-bottom:0;">' +
                    '<button onclick="AdminChat.loadInbox()" style="background:var(--surface);border:1px solid var(--border);color:var(--text-main);width:38px;height:38px;border-radius:10px;flex-shrink:0;cursor:pointer;font-size:0.9rem;"><i class="fas fa-arrow-left"></i></button>' +
                    '<div class="ac-avatar" style="width:36px;height:36px;font-size:0.9rem;">' + _esc(userName).charAt(0).toUpperCase() + '</div>' +
                    '<div>' +
                        '<div style="font-weight:700;font-size:0.95rem;color:var(--text-main);">' + _esc(userName) + '</div>' +
                        '<div style="font-size:0.7rem;color:var(--text-muted);">Customer</div>' +
                    '</div>' +
                '</div>' +
                '<div id="acMessages" style="overflow-y:auto;padding:14px 0;display:flex;flex-direction:column;gap:8px;height:calc(100vh - 280px);"></div>' +
                '<div style="display:flex;gap:10px;padding-top:10px;border-top:1px solid var(--border);">' +
                    '<input type="text" id="acInput" placeholder="Type a message..." onkeydown="if(event.key===\'Enter\')AdminChat.send()"' +
                        ' style="flex:1;padding:11px 16px;background:var(--surface);border:1px solid var(--border);border-radius:50px;color:var(--text-main);font-size:0.9rem;outline:none;">' +
                    '<button onclick="AdminChat.send()" style="background:var(--primary);color:#ffffff;border:none;border-radius:50%;width:42px;height:42px;display:flex;align-items:center;justify-content:center;cursor:pointer;flex-shrink:0;">' +
                        '<i class="fas fa-paper-plane"></i>' +
                    '</button>' +
                '</div>';

            const aid = _adminId();
            if (aid) {
                fetch(API_URL + '/chat/mark-read', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ receiver_type: 'admin', receiver_id: aid, sender_type: 'user', sender_id: userId })
                }).catch(function() {});
            }

            _fetchMessages(true);
            _pollTimer = setInterval(function() { _fetchMessages(false); }, 2000);
        }

        function _fetchMessages(initial) {
            const aid = _adminId();
            if (!aid || !_currentUserId) return;
            console.log('[AdminChat] Fetching messages: user_id=' + _currentUserId + ', admin_id=' + aid);
            fetch(API_URL + '/chat/messages?user_id=' + _currentUserId + '&admin_id=' + aid + '&limit=100')
                .then(function(r) { return r.json(); })
                .then(function(msgs) {
                    console.log('[AdminChat] Received ' + (Array.isArray(msgs) ? msgs.length : 0) + ' messages');
                    if (msgs && msgs.length > 0) {
                        console.log('[AdminChat] First message:', JSON.stringify(msgs[0]));
                        console.log('[AdminChat] Last message:', JSON.stringify(msgs[msgs.length - 1]));
                    }
                    
                    const container = document.getElementById('acMessages');
                    if (!container) return;
                    if (!Array.isArray(msgs) || !msgs.length) {
                        if (initial) container.innerHTML =
                            '<div style="text-align:center;color:var(--text-muted);font-size:0.85rem;padding:30px;">No messages yet. Say hello!</div>';
                        return;
                    }
                    const latestId = msgs[msgs.length - 1].id;
                    console.log('[AdminChat] Latest ID: ' + latestId + ', Last ID: ' + _lastMsgId);
                    
                    // Only skip update if not initial AND same lastMsgId AND not forced
                    if (String(latestId) === String(_lastMsgId) && !initial && initial !== 'force') {
                        console.log('[AdminChat] Skipping update - same message ID');
                        return;
                    }

                    // Detect new message from user
                    const lastMsg = msgs[msgs.length - 1];
                    const isNewFromUser = !initial && String(latestId) !== String(_lastMsgId) && lastMsg.sender_type === 'user';
                    _lastMsgId = latestId;

                    // Show pop-up banner
                    if (isNewFromUser) {
                        showAdminChatPopup(_currentUserName, lastMsg.message, _currentUserId);
                    }

                    const atBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 80;
                    console.log('[AdminChat] Rendering ' + msgs.length + ' messages');
                    container.innerHTML = msgs.map(function(m) {
                        const isMe = m.sender_type === 'admin';
                        const ts = m.created_at ? new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '';
                        if (isMe) {
                            return '<div style="display:flex;justify-content:flex-end;">' +
                                '<div style="max-width:78%;background:var(--primary);color:#ffffff;padding:10px 14px;border-radius:18px 18px 4px 18px;font-size:0.875rem;line-height:1.4;">' +
                                    _esc(m.message) +
                                    '<div style="font-size:0.62rem;color:rgba(255,255,255,0.6);margin-top:3px;text-align:right;">' + ts + '</div>' +
                                '</div>' +
                            '</div>';
                        } else {
                            return '<div style="display:flex;justify-content:flex-start;">' +
                                '<div style="max-width:78%;background:var(--surface);border:1px solid var(--border);color:var(--text-main);padding:10px 14px;border-radius:18px 18px 18px 4px;font-size:0.875rem;line-height:1.4;">' +
                                    _esc(m.message) +
                                    '<div style="font-size:0.62rem;color:var(--text-muted);margin-top:3px;">' + ts + '</div>' +
                                '</div>' +
                            '</div>';
                        }
                    }).join('');

                    if (initial || atBottom) container.scrollTop = container.scrollHeight;

                    fetch(API_URL + '/chat/mark-read', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ receiver_type: 'admin', receiver_id: aid, sender_type: 'user', sender_id: _currentUserId })
                    }).catch(function() {});
                })
                .catch(function(err) {
                    console.error('[AdminChat] Error fetching messages:', err);
                });
        }

        function send() {
            const inputEl = document.getElementById('acInput');
            if (!inputEl) { console.error('CHAT: no input element'); return; }
            const msg = (inputEl.value || '').trim();
            const aid = _adminId();
            console.log('CHAT SEND: msg=' + msg + ' aid=' + aid + ' userId=' + _currentUserId);
            if (!msg) { console.error('CHAT: empty message'); return; }
            if (!aid) { alert('Not logged in - cannot send'); return; }
            if (!_currentUserId) { alert('No user selected'); return; }
            inputEl.value = '';
            inputEl.disabled = true;

            const payload = { sender_type: 'admin', sender_id: aid, receiver_type: 'user', receiver_id: _currentUserId, message: msg };
            console.log('CHAT PAYLOAD:', JSON.stringify(payload));

            fetch(API_URL + '/chat/send', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
                .then(function(r) {
                    console.log('CHAT SEND response status:', r.status);
                    return r.json().then(function(d) {
                        console.log('CHAT SEND response:', JSON.stringify(d));
                        // Force refresh by resetting _lastMsgId
                        _lastMsgId = null;
                        _fetchMessages(false);
                    });
                })
                .catch(function(err) { alert('Send failed: ' + (err.message || 'Unknown error')); })
                .finally(function() { if (inputEl) inputEl.disabled = false; });
        }

        function stopPolling() {
            if (_pollTimer) { clearInterval(_pollTimer); _pollTimer = null; }
        }

        function updateNavBadge() {
            const aid = _adminId();
            if (!aid) return;
            fetch(API_URL + '/chat/inbox?viewer_type=admin&viewer_id=' + aid)
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    const badge = document.getElementById('adminChatNavBadge');
                    if (!badge) return;
                    let total = 0;
                    if (Array.isArray(data)) data.forEach(function(c) { total += parseInt(c.unread_count) || 0; });
                    if (total > 0) {
                        badge.textContent = total > 9 ? '9+' : String(total);
                        badge.style.display = 'flex';
                    } else {
                        badge.style.display = 'none';
                    }
                })
                .catch(function() {});
        }

        return { 
            loadInbox: loadInbox, 
            openConversation: openConversation, 
            send: send, 
            stopPolling: stopPolling, 
            showUserSearch: showUserSearch, 
            searchUsers: searchUsers, 
            updateNavBadge: updateNavBadge,
            loadConversations: loadConversations,
            searchConversations: searchConversations,
            clearSearch: clearSearch,
            renderConversations: renderConversations
        };
    })();

    window.AdminChat = AdminChat;
    // END ADMIN CHAT MODULE

    // Admin Chat Pop-up Banner
    window.showAdminChatPopup = function(senderName, message, userId) {
        var existing = document.getElementById('adminChatPopup');
        if (existing) existing.remove();
        var banner = document.createElement('div');
        banner.id = 'adminChatPopup';
        banner.style.cssText = 'position:fixed;top:72px;left:12px;right:12px;z-index:6000;background:var(--primary);color:#ffffff;border-radius:14px;padding:12px 14px;box-shadow:0 8px 24px rgba(0,0,0,0.25);display:flex;align-items:center;gap:10px;cursor:pointer;';
        banner.innerHTML =
            '<div style="width:34px;height:34px;border-radius:50%;background:rgba(255,255,255,0.2);display:flex;align-items:center;justify-content:center;flex-shrink:0;font-weight:700;font-size:0.9rem;">' + (senderName||'U').charAt(0).toUpperCase() + '</div>' +
            '<div style="flex:1;min-width:0;">' +
                '<div style="font-size:0.72rem;font-weight:700;opacity:0.85;">' + (senderName||'Customer') + ' sent a message</div>' +
                '<div style="font-size:0.82rem;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">' + (message||'') + '</div>' +
            '</div>' +
            '<button onclick="document.getElementById(\'adminChatPopup\').remove()" style="background:rgba(255,255,255,0.2);border:none;color:#fff;width:26px;height:26px;border-radius:50%;cursor:pointer;font-size:0.75rem;flex-shrink:0;">x</button>';
        banner.onclick = function(e) {
            if (e.target.tagName === 'BUTTON') return;
            banner.remove();
            switchTab('chat');
            if (userId && typeof AdminChat !== 'undefined') {
                setTimeout(function() { AdminChat.openConversation(userId, senderName); }, 300);
            }
        };
        document.body.appendChild(banner);
        setTimeout(function() { if (banner.parentNode) banner.remove(); }, 6000);
    };

    // Background inbox polling (when not on chat tab)
    var _adminBgChatTimer = null;
    var _adminBgLastAt = '';
    function startAdminBgChatPolling() {
        if (_adminBgChatTimer) return;
        _adminBgChatTimer = setInterval(function() {
            if (typeof currentTab !== 'undefined' && currentTab === 'chat') return;
            const user = adminAuth.getUser();
            if (!user) return;
            fetch(API_URL + '/chat/inbox?viewer_type=admin&viewer_id=' + user.id)
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    if (!Array.isArray(data)) return;
                    let totalUnread = 0;
                    data.forEach(function(c) { totalUnread += parseInt(c.unread_count) || 0; });
                    const badge = document.getElementById('adminChatNavBadge');
                    if (badge) {
                        if (totalUnread > 0) { badge.textContent = totalUnread > 9 ? '9+' : String(totalUnread); badge.style.display = 'flex'; }
                        else { badge.style.display = 'none'; }
                    }
                    const conv = data.find(function(c) { return parseInt(c.unread_count) > 0; });
                    if (conv && conv.last_at && conv.last_at !== _adminBgLastAt) {
                        _adminBgLastAt = conv.last_at;
                        showAdminChatPopup(conv.other_name, conv.last_message, conv.other_id);
                    }
                })
                .catch(function() {});
        }, 10000);
    }
    window.startAdminBgChatPolling = startAdminBgChatPolling;

    // Test Push Notification
    window.testAdminPushNotification = function() {
        const user = adminAuth.getUser();
        if (!user) { alert('Please log in first.'); return; }
        fetch(API_URL + '/debug/test-push', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ admin_id: user.id })
        })
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.success) {
                showNotification('Test push sent! Check your notifications.', 'success');
            } else {
                showNotification('Push failed: ' + (data.error || 'Unknown error'), 'error');
            }
        })
        .catch(function(err) {
            showNotification('Network error: ' + err.message, 'error');
        });
    };

