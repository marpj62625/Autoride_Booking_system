new_settings_html = '''    <!-- SETTINGS TAB -->
    <div id="settings" class="tab-content" style="display: none; max-width: 1220px; margin: 0 auto; padding-bottom: 60px;">
        <div class="settings-page-header" style="margin-bottom: 24px;">
            <h1 class="page-title" style="margin: 0 0 4px; font-size: 1.55rem; font-weight: 900; letter-spacing: -0.4px;">Settings &amp; Preferences</h1>
            <p style="font-size: 0.85rem; color: var(--text-muted); margin: 0;">Manage your account, platform configurations, and system controls</p>
        </div>

        <div class="settings-layout-container" style="display: grid; grid-template-columns: 340px 1fr; gap: 24px; align-items: start;">
            <!-- LEFT COLUMN: Profile & Quick Info -->
            <div class="settings-col-left" style="position: sticky; top: 20px; display: flex; flex-direction: column; gap: 16px;">
                <!-- Profile Card -->
                <div class="settings-profile-card" style="background: var(--surface); border: 1px solid var(--border); border-radius: 20px; padding: 28px 22px 24px; text-align: center; position: relative; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04); overflow: hidden;">
                    <div class="settings-profile-badge-ribbon" style="margin-bottom: 14px;">
                        <span id="settingsRole" class="settings-role-pill" style="display: inline-block; padding: 4px 14px; border-radius: 20px; font-size: 0.72rem; font-weight: 800; letter-spacing: 0.8px; text-transform: uppercase; background: rgba(0, 177, 79, 0.12); color: var(--primary); border: 1px solid rgba(0, 177, 79, 0.3);">SUPER ADMIN</span>
                    </div>

                    <div class="settings-avatar-wrap" style="position: relative; width: 88px; height: 88px; margin: 0 auto 16px;">
                        <div id="settingsAvatar" class="settings-avatar" style="width: 88px; height: 88px; border-radius: 50%; background: linear-gradient(135deg, #00B14F 0%, #00873c 100%); color: #ffffff; display: flex; align-items: center; justify-content: center; font-size: 2.8rem; font-weight: 800; box-shadow: 0 10px 25px rgba(0, 177, 79, 0.25); border: 3px solid var(--surface);">S</div>
                        <span class="settings-online-status" title="Active Session" style="position: absolute; bottom: 4px; right: 4px; width: 16px; height: 16px; border-radius: 50%; background: #10b981; border: 3px solid var(--surface); box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2);"></span>
                    </div>

                    <h2 id="settingsName" class="settings-user-name" style="font-size: 1.35rem; font-weight: 800; color: var(--text-main); margin: 0 0 6px; letter-spacing: -0.3px;">Super Admin</h2>
                    <div class="settings-email-row" style="display: inline-flex; align-items: center; gap: 8px; font-size: 0.82rem; color: var(--text-muted); background: var(--surface-container); padding: 6px 14px; border-radius: 12px; max-width: 100%; word-break: break-all;">
                        <i class="far fa-envelope" style="color: var(--text-muted); font-size: 0.8rem;"></i>
                        <span id="settingsEmail" class="settings-user-email">admin@autoride.com</span>
                    </div>

                    <!-- Super Admin Edit Profile Pill (Super Admin Only) -->
                    <div id="superAdminProfileEditPill" style="display: none; justify-content: center; width: 100%; margin-top: 14px;">
                        <button type="button" onclick="openSuperAdminProfileModal()" class="settings-edit-profile-btn" style="width: 100%; display: inline-flex; align-items: center; justify-content: center; gap: 8px; padding: 10px 18px; border-radius: 12px; background: var(--primary); color: #ffffff; font-size: 0.85rem; font-weight: 700; border: none; cursor: pointer; box-shadow: 0 4px 14px rgba(0, 177, 79, 0.25);">
                            <i class="fas fa-user-edit"></i> Edit Profile (Super Admin)
                        </button>
                    </div>

                    <!-- Admin Quick Info Stats / Badges -->
                    <div class="settings-profile-meta" style="margin-top: 20px; padding-top: 18px; border-top: 1px dashed var(--border); display: flex; flex-direction: column; gap: 10px; text-align: left;">
                        <div class="settings-meta-item" style="display: flex; justify-content: space-between; align-items: center; font-size: 0.78rem;">
                            <span class="meta-label" style="color: var(--text-muted);">Access Level</span>
                            <span class="meta-val" id="settingsAccessLevel" style="font-weight: 700; color: var(--text-main); display: flex; align-items: center;"><i class="fas fa-shield-alt" style="color:var(--primary); margin-right:5px;"></i> Root Access</span>
                        </div>
                        <div class="settings-meta-item" style="display: flex; justify-content: space-between; align-items: center; font-size: 0.78rem;">
                            <span class="meta-label" style="color: var(--text-muted);">Session Status</span>
                            <span class="meta-val" style="font-weight: 700; color: var(--text-main); display: flex; align-items: center;"><span class="meta-dot-green" style="width: 7px; height: 7px; border-radius: 50%; background: #10b981; display: inline-block; margin-right: 6px;"></span> Active &amp; Verified</span>
                        </div>
                        <div class="settings-meta-item" style="display: flex; justify-content: space-between; align-items: center; font-size: 0.78rem;">
                            <span class="meta-label" style="color: var(--text-muted);">Platform Engine</span>
                            <span class="meta-val" style="font-weight: 700; color: var(--text-main); display: flex; align-items: center;"><i class="fas fa-server" style="color:var(--text-muted); margin-right:5px;"></i> Autoride v2026.10</span>
                        </div>
                    </div>
                </div>

                <!-- Quick Security Card -->
                <div class="settings-security-card" style="background: var(--surface); border: 1px solid var(--border); border-radius: 18px; padding: 18px 20px; box-shadow: 0 2px 12px rgba(0, 0, 0, 0.03);">
                    <div style="display:flex; align-items:center; gap:10px; margin-bottom:8px;">
                        <div style="width:32px; height:32px; border-radius:8px; background:rgba(0,177,79,0.12); display:flex; align-items:center; justify-content:center; color:var(--primary);">
                            <i class="fas fa-shield-virus" style="font-size:0.9rem;"></i>
                        </div>
                        <span style="font-weight:700; font-size:0.85rem; color:var(--text-main);">Security &amp; Audit</span>
                    </div>
                    <p style="font-size:0.75rem; color:var(--text-muted); line-height:1.45; margin:0 0 10px;">
                        All administrator actions, configuration updates, and system operations are actively logged for compliance.
                    </p>
                    <a href="#activity" onclick="showTab('activity'); return false;" style="font-size:0.75rem; font-weight:700; color:var(--primary); text-decoration:none; display:inline-flex; align-items:center; gap:5px;">
                        View Activity Log <i class="fas fa-arrow-right" style="font-size:0.7rem;"></i>
                    </a>
                </div>
            </div>

            <!-- RIGHT COLUMN: Settings Options Grouped into Categories -->
            <div class="settings-col-right" style="display: flex; flex-direction: column; gap: 20px; min-width: 0;">
                <!-- GROUP 1: Account & Security -->
                <div class="settings-group" style="background: var(--surface); border: 1px solid var(--border); border-radius: 20px; padding: 20px 22px; box-shadow: 0 2px 14px rgba(0, 0, 0, 0.03);">
                    <div class="settings-group-header" style="display: flex; align-items: center; gap: 14px; margin-bottom: 16px; padding-bottom: 14px; border-bottom: 1px solid var(--border);">
                        <div class="settings-group-icon" style="width: 38px; height: 38px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1rem; flex-shrink: 0; background: rgba(0, 177, 79, 0.1); color: var(--primary);">
                            <i class="fas fa-user-lock"></i>
                        </div>
                        <div>
                            <h3 class="settings-group-title" style="font-size: 1.05rem; font-weight: 800; color: var(--text-main); margin: 0 0 2px; letter-spacing: -0.2px;">Account &amp; Security</h3>
                            <p class="settings-group-desc" style="font-size: 0.76rem; color: var(--text-muted); margin: 0;">Manage credentials, permissions, and administrative access</p>
                        </div>
                    </div>

                    <div class="settings-cards-stack" style="display: flex; flex-direction: column; gap: 10px;">
                        <!-- Super Admin Edit Profile Option (Super Admin Only) -->
                        <div id="superAdminEditProfileCard" class="settings-action-card stat-card highlight-emerald" onclick="openSuperAdminProfileModal()" style="display: none; background: rgba(0, 177, 79, 0.03); border: 1px solid rgba(0, 177, 79, 0.35); border-radius: 14px; padding: 13px 16px; align-items: center; gap: 14px; cursor: pointer;">
                            <div class="settings-action-icon" style="width: 42px; height: 42px; border-radius: 11px; display: flex; align-items: center; justify-content: center; font-size: 1.05rem; flex-shrink: 0; background: rgba(0, 177, 79, 0.12); color: var(--primary);">
                                <i class="fas fa-user-shield"></i>
                            </div>
                            <div class="settings-action-body" style="flex: 1; min-width: 0;">
                                <h4 style="font-size: 0.92rem; font-weight: 700; color: var(--text-main); margin: 0 0 2px;">Edit Profile</h4>
                                <p style="font-size: 0.73rem; color: var(--text-muted); margin: 0;">Change email address &amp; root password</p>
                            </div>
                            <div class="settings-action-tail" style="display: flex; align-items: center; gap: 8px; color: var(--text-muted); font-size: 0.8rem; flex-shrink: 0;">
                                <i class="fas fa-chevron-right"></i>
                            </div>
                        </div>

                        <!-- Regular Admin Change Password (Hidden for Super Admin) -->
                        <div id="adminChangePasswordCard" class="settings-action-card stat-card" onclick="openChangePasswordModal()" style="display: flex; background: var(--surface-container); border: 1px solid var(--border); border-radius: 14px; padding: 13px 16px; align-items: center; gap: 14px; cursor: pointer;">
                            <div class="settings-action-icon" style="width: 42px; height: 42px; border-radius: 11px; display: flex; align-items: center; justify-content: center; font-size: 1.05rem; flex-shrink: 0; background: rgba(99, 102, 241, 0.12); color: #6366f1;">
                                <i class="fas fa-key"></i>
                            </div>
                            <div class="settings-action-body" style="flex: 1; min-width: 0;">
                                <h4 style="font-size: 0.92rem; font-weight: 700; color: var(--text-main); margin: 0 0 2px;">Change Password</h4>
                                <p style="font-size: 0.73rem; color: var(--text-muted); margin: 0;">Secure your administrator account</p>
                            </div>
                            <div class="settings-action-tail" style="display: flex; align-items: center; gap: 8px; color: var(--text-muted); font-size: 0.8rem; flex-shrink: 0;">
                                <i class="fas fa-chevron-right"></i>
                            </div>
                        </div>

                        <!-- Super Admin Staff Permissions Card -->
                        <div id="superAdminPermissionsCard" class="settings-action-card stat-card highlight-border" onclick="StaffPermissions.openSuperAdminModal()" style="display: none; background: var(--surface-container); border: 1px solid var(--border); border-left: 4px solid var(--primary); border-radius: 14px; padding: 13px 16px; align-items: center; gap: 14px; cursor: pointer;">
                            <div class="settings-action-icon" style="width: 42px; height: 42px; border-radius: 11px; display: flex; align-items: center; justify-content: center; font-size: 1.05rem; flex-shrink: 0; background: rgba(0, 177, 79, 0.15); color: var(--primary);">
                                <i class="fas fa-users-cog"></i>
                            </div>
                            <div class="settings-action-body" style="flex: 1; min-width: 0;">
                                <div style="display: flex; align-items: center; gap: 8px;">
                                    <h4 style="font-size: 0.92rem; font-weight: 700; color: var(--text-main); margin: 0 0 2px;">Staff Permissions &amp; Requests</h4>
                                    <span id="pendingRequestsBadge" style="display: none; background: #ef4444; color: #fff; font-size: 0.65rem; font-weight: 800; padding: 2px 7px; border-radius: 10px;">0 NEW</span>
                                </div>
                                <p style="font-size: 0.73rem; color: var(--text-muted); margin: 0;">Allow or restrict controls for staff members &amp; review requests</p>
                            </div>
                            <div class="settings-action-tail" style="display: flex; align-items: center; gap: 8px; color: var(--text-muted); font-size: 0.8rem; flex-shrink: 0;">
                                <span class="settings-action-badge" style="background: rgba(0, 177, 79, 0.12); color: var(--primary); font-size: 0.68rem; font-weight: 800; padding: 3px 8px; border-radius: 6px; text-transform: uppercase;">Manage</span>
                                <i class="fas fa-chevron-right"></i>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- GROUP 2: Preferences & Interface -->
                <div class="settings-group" style="background: var(--surface); border: 1px solid var(--border); border-radius: 20px; padding: 20px 22px; box-shadow: 0 2px 14px rgba(0, 0, 0, 0.03);">
                    <div class="settings-group-header" style="display: flex; align-items: center; gap: 14px; margin-bottom: 16px; padding-bottom: 14px; border-bottom: 1px solid var(--border);">
                        <div class="settings-group-icon" style="width: 38px; height: 38px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1rem; flex-shrink: 0; background: rgba(245, 158, 11, 0.1); color: #f59e0b;">
                            <i class="fas fa-sliders-h"></i>
                        </div>
                        <div>
                            <h3 class="settings-group-title" style="font-size: 1.05rem; font-weight: 800; color: var(--text-main); margin: 0 0 2px; letter-spacing: -0.2px;">Preferences &amp; Notifications</h3>
                            <p class="settings-group-desc" style="font-size: 0.76rem; color: var(--text-muted); margin: 0;">Customize theme appearance and real-time alert delivery</p>
                        </div>
                    </div>

                    <div class="settings-cards-stack" style="display: flex; flex-direction: column; gap: 10px;">
                        <!-- Push Notifications -->
                        <div class="settings-action-card stat-card" onclick="testAdminPushNotification()" style="background: var(--surface-container); border: 1px solid var(--border); border-radius: 14px; padding: 13px 16px; display: flex; align-items: center; gap: 14px; cursor: pointer;">
                            <div class="settings-action-icon" style="width: 42px; height: 42px; border-radius: 11px; display: flex; align-items: center; justify-content: center; font-size: 1.05rem; flex-shrink: 0; background: rgba(59, 130, 246, 0.12); color: #3b82f6;">
                                <i class="fas fa-bell"></i>
                            </div>
                            <div class="settings-action-body" style="flex: 1; min-width: 0;">
                                <h4 style="font-size: 0.92rem; font-weight: 700; color: var(--text-main); margin: 0 0 2px;">Push Notifications</h4>
                                <p style="font-size: 0.73rem; color: var(--text-muted); margin: 0;">Tap to send a test push</p>
                            </div>
                            <div class="settings-action-tail" style="display: flex; align-items: center; gap: 8px; color: var(--text-muted); font-size: 0.8rem; flex-shrink: 0;">
                                <span class="settings-pill-action" style="background: var(--surface); border: 1px solid var(--border); color: var(--text-muted); font-size: 0.7rem; font-weight: 600; padding: 3px 9px; border-radius: 8px;">Test Alert</span>
                                <i class="fas fa-chevron-right"></i>
                            </div>
                        </div>

                        <!-- Dark Mode -->
                        <div class="settings-action-card stat-card" onclick="toggleDarkMode()" style="background: var(--surface-container); border: 1px solid var(--border); border-radius: 14px; padding: 13px 16px; display: flex; align-items: center; gap: 14px; cursor: pointer;">
                            <div class="settings-action-icon" style="width: 42px; height: 42px; border-radius: 11px; display: flex; align-items: center; justify-content: center; font-size: 1.05rem; flex-shrink: 0; background: rgba(139, 92, 246, 0.12); color: #8b5cf6;">
                                <i id="adminDarkModeIcon" class="fas fa-moon"></i>
                            </div>
                            <div class="settings-action-body" style="flex: 1; min-width: 0;">
                                <h4 id="adminDarkModeLabel" style="font-size: 0.92rem; font-weight: 700; color: var(--text-main); margin: 0 0 2px;">Dark Mode</h4>
                                <p style="font-size: 0.73rem; color: var(--text-muted); margin: 0;">Switch appearance</p>
                            </div>
                            <div class="settings-action-tail" style="display: flex; align-items: center; gap: 8px; color: var(--text-muted); font-size: 0.8rem; flex-shrink: 0;">
                                <span class="settings-pill-action" style="background: var(--surface); border: 1px solid var(--border); color: var(--text-muted); font-size: 0.7rem; font-weight: 600; padding: 3px 9px; border-radius: 8px;">Switch</span>
                                <i class="fas fa-chevron-right"></i>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- GROUP 3: Platform Operations & Fleet Controls -->
                <div class="settings-group" style="background: var(--surface); border: 1px solid var(--border); border-radius: 20px; padding: 20px 22px; box-shadow: 0 2px 14px rgba(0, 0, 0, 0.03);">
                    <div class="settings-group-header" style="display: flex; align-items: center; gap: 14px; margin-bottom: 16px; padding-bottom: 14px; border-bottom: 1px solid var(--border);">
                        <div class="settings-group-icon" style="width: 38px; height: 38px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1rem; flex-shrink: 0; background: rgba(16, 185, 129, 0.1); color: #10b981;">
                            <i class="fas fa-cogs"></i>
                        </div>
                        <div>
                            <h3 class="settings-group-title" style="font-size: 1.05rem; font-weight: 800; color: var(--text-main); margin: 0 0 2px; letter-spacing: -0.2px;">Operations &amp; Rental Controls</h3>
                            <p class="settings-group-desc" style="font-size: 0.76rem; color: var(--text-muted); margin: 0;">Configure business rules, branch coverage, add-ons, and automation</p>
                        </div>
                    </div>

                    <div class="settings-cards-stack" style="display: flex; flex-direction: column; gap: 10px;">
                        <!-- Locked Preview Cards for Staff Admin -->
                        <div id="lockPerm_system_config" class="settings-action-card stat-card locked-card" style="display: none; justify-content: space-between; background: var(--surface-container); border: 1px dashed var(--border); border-radius: 14px; padding: 13px 16px; align-items: center;">
                            <div style="display: flex; align-items: center; gap: 12px; flex: 1; min-width: 0;">
                                <div class="settings-action-icon" style="width: 42px; height: 42px; border-radius: 11px; display: flex; align-items: center; justify-content: center; font-size: 1.05rem; flex-shrink: 0; background: rgba(255,255,255,0.06); color: var(--text-muted);">
                                    <i class="fas fa-cogs"></i>
                                </div>
                                <div class="settings-action-body" style="flex: 1; min-width: 0;">
                                    <h4 style="font-size: 0.92rem; font-weight: 700; color: var(--text-main); margin: 0 0 2px; display: flex; align-items: center; gap: 6px;">System Configuration <i class="fas fa-lock" style="font-size:0.75rem; color:var(--text-muted);"></i></h4>
                                    <p style="font-size: 0.73rem; color: var(--text-muted); margin: 0;">Manage rental duration rules &amp; company settings</p>
                                </div>
                            </div>
                            <button type="button" onclick="StaffPermissions.openRequestModal('perm_system_config')" class="settings-req-btn" style="padding: 7px 14px; font-size: 0.75rem; border-radius: 8px; background: rgba(0, 177, 79, 0.12); color: var(--primary); border: 1px solid rgba(0, 177, 79, 0.3); font-weight: 700; cursor: pointer;">
                                Request Access
                            </button>
                        </div>

                        <!-- System Configuration -->
                        <div id="mobileSystemConfig" class="revenue-restricted">
                            <div class="settings-action-card stat-card" onclick="toggleSystemConfigModal()" style="background: var(--surface-container); border: 1px solid var(--border); border-radius: 14px; padding: 13px 16px; display: flex; align-items: center; gap: 14px; cursor: pointer;">
                                <div class="settings-action-icon" style="width: 42px; height: 42px; border-radius: 11px; display: flex; align-items: center; justify-content: center; font-size: 1.05rem; flex-shrink: 0; background: rgba(0, 177, 79, 0.12); color: var(--primary);">
                                    <i class="fas fa-cogs"></i>
                                </div>
                                <div class="settings-action-body" style="flex: 1; min-width: 0;">
                                    <h4 style="font-size: 0.92rem; font-weight: 700; color: var(--text-main); margin: 0 0 2px;">System Configuration</h4>
                                    <p style="font-size: 0.73rem; color: var(--text-muted); margin: 0;">Manage system settings &amp; rental duration rules</p>
                                </div>
                                <div class="settings-action-tail" style="display: flex; align-items: center; gap: 8px; color: var(--text-muted); font-size: 0.8rem; flex-shrink: 0;"><i class="fas fa-chevron-right"></i></div>
                            </div>
                        </div>

                        <!-- Locked chat preview -->
                        <div id="lockPerm_chat_ai" class="settings-action-card stat-card locked-card" style="display: none; justify-content: space-between; background: var(--surface-container); border: 1px dashed var(--border); border-radius: 14px; padding: 13px 16px; align-items: center;">
                            <div style="display: flex; align-items: center; gap: 12px; flex: 1; min-width: 0;">
                                <div class="settings-action-icon" style="width: 42px; height: 42px; border-radius: 11px; display: flex; align-items: center; justify-content: center; font-size: 1.05rem; flex-shrink: 0; background: rgba(255,255,255,0.06); color: var(--text-muted);">
                                    <i class="fas fa-robot"></i>
                                </div>
                                <div class="settings-action-body" style="flex: 1; min-width: 0;">
                                    <h4 style="font-size: 0.92rem; font-weight: 700; color: var(--text-main); margin: 0 0 2px; display: flex; align-items: center; gap: 6px;">Live Chat FAQs &amp; AI Controls <i class="fas fa-lock" style="font-size:0.75rem; color:var(--text-muted);"></i></h4>
                                    <p style="font-size: 0.73rem; color: var(--text-muted); margin: 0;">Configure automated chat FAQ chips &amp; AI chatbot</p>
                                </div>
                            </div>
                            <button type="button" onclick="StaffPermissions.openRequestModal('perm_chat_ai')" class="settings-req-btn" style="padding: 7px 14px; font-size: 0.75rem; border-radius: 8px; background: rgba(0, 177, 79, 0.12); color: var(--primary); border: 1px solid rgba(0, 177, 79, 0.3); font-weight: 700; cursor: pointer;">
                                Request Access
                            </button>
                        </div>

                        <!-- Chat Controls -->
                        <div id="adminChatControlsConfigCard" class="revenue-restricted">
                            <div class="settings-action-card stat-card" onclick="AdminChatControls.openModal()" style="background: var(--surface-container); border: 1px solid var(--border); border-radius: 14px; padding: 13px 16px; display: flex; align-items: center; gap: 14px; cursor: pointer;">
                                <div class="settings-action-icon" style="width: 42px; height: 42px; border-radius: 11px; display: flex; align-items: center; justify-content: center; font-size: 1.05rem; flex-shrink: 0; background: rgba(6, 182, 212, 0.12); color: #06b6d4;">
                                    <i class="fas fa-robot"></i>
                                </div>
                                <div class="settings-action-body" style="flex: 1; min-width: 0;">
                                    <h4 style="font-size: 0.92rem; font-weight: 700; color: var(--text-main); margin: 0 0 2px;">Live Chat FAQs &amp; AI Assistant</h4>
                                    <p style="font-size: 0.73rem; color: var(--text-muted); margin: 0;">Configure chat FAQ chips, auto-replies &amp; AI chatbot</p>
                                </div>
                                <div class="settings-action-tail" style="display: flex; align-items: center; gap: 8px; color: var(--text-muted); font-size: 0.8rem; flex-shrink: 0;"><i class="fas fa-chevron-right"></i></div>
                            </div>
                        </div>

                        <!-- Locked addons preview -->
                        <div id="lockPerm_addons" class="settings-action-card stat-card locked-card" style="display: none; justify-content: space-between; background: var(--surface-container); border: 1px dashed var(--border); border-radius: 14px; padding: 13px 16px; align-items: center;">
                            <div style="display: flex; align-items: center; gap: 12px; flex: 1; min-width: 0;">
                                <div class="settings-action-icon" style="width: 42px; height: 42px; border-radius: 11px; display: flex; align-items: center; justify-content: center; font-size: 1.05rem; flex-shrink: 0; background: rgba(255,255,255,0.06); color: var(--text-muted);">
                                    <i class="fas fa-plus-circle"></i>
                                </div>
                                <div class="settings-action-body" style="flex: 1; min-width: 0;">
                                    <h4 style="font-size: 0.92rem; font-weight: 700; color: var(--text-main); margin: 0 0 2px; display: flex; align-items: center; gap: 6px;">Add-ons Management <i class="fas fa-lock" style="font-size:0.75rem; color:var(--text-muted);"></i></h4>
                                    <p style="font-size: 0.73rem; color: var(--text-muted); margin: 0;">Manage rental add-ons and pricing</p>
                                </div>
                            </div>
                            <button type="button" onclick="StaffPermissions.openRequestModal('perm_addons')" class="settings-req-btn" style="padding: 7px 14px; font-size: 0.75rem; border-radius: 8px; background: rgba(0, 177, 79, 0.12); color: var(--primary); border: 1px solid rgba(0, 177, 79, 0.3); font-weight: 700; cursor: pointer;">
                                Request Access
                            </button>
                        </div>

                        <!-- Add-ons Management -->
                        <div id="mobileAddonsConfig" class="revenue-restricted">
                            <div class="settings-action-card stat-card" onclick="toggleAddonsModal()" style="background: var(--surface-container); border: 1px solid var(--border); border-radius: 14px; padding: 13px 16px; display: flex; align-items: center; gap: 14px; cursor: pointer;">
                                <div class="settings-action-icon" style="width: 42px; height: 42px; border-radius: 11px; display: flex; align-items: center; justify-content: center; font-size: 1.05rem; flex-shrink: 0; background: rgba(245, 158, 11, 0.12); color: #f59e0b;">
                                    <i class="fas fa-plus-circle"></i>
                                </div>
                                <div class="settings-action-body" style="flex: 1; min-width: 0;">
                                    <h4 style="font-size: 0.92rem; font-weight: 700; color: var(--text-main); margin: 0 0 2px;">Add-ons Management</h4>
                                    <p style="font-size: 0.73rem; color: var(--text-muted); margin: 0;">Manage rental add-ons and pricing</p>
                                </div>
                                <div class="settings-action-tail" style="display: flex; align-items: center; gap: 8px; color: var(--text-muted); font-size: 0.8rem; flex-shrink: 0;"><i class="fas fa-chevron-right"></i></div>
                            </div>
                        </div>

                        <!-- Insurance Package -->
                        <div id="mobileInsuranceConfig" class="revenue-restricted">
                            <div class="settings-action-card stat-card" onclick="toggleInsuranceModal()" style="background: var(--surface-container); border: 1px solid var(--border); border-radius: 14px; padding: 13px 16px; display: flex; align-items: center; gap: 14px; cursor: pointer;">
                                <div class="settings-action-icon" style="width: 42px; height: 42px; border-radius: 11px; display: flex; align-items: center; justify-content: center; font-size: 1.05rem; flex-shrink: 0; background: rgba(16, 185, 129, 0.12); color: #10b981;">
                                    <i class="fas fa-shield-alt"></i>
                                </div>
                                <div class="settings-action-body" style="flex: 1; min-width: 0;">
                                    <h4 style="font-size: 0.92rem; font-weight: 700; color: var(--text-main); margin: 0 0 2px;">Insurance Packages</h4>
                                    <p style="font-size: 0.73rem; color: var(--text-muted); margin: 0;">Manage rental protection coverage &amp; daily rates</p>
                                </div>
                                <div class="settings-action-tail" style="display: flex; align-items: center; gap: 8px; color: var(--text-muted); font-size: 0.8rem; flex-shrink: 0;"><i class="fas fa-chevron-right"></i></div>
                            </div>
                        </div>

                        <!-- Locked locations preview -->
                        <div id="lockPerm_locations" class="settings-action-card stat-card locked-card" style="display: none; justify-content: space-between; background: var(--surface-container); border: 1px dashed var(--border); border-radius: 14px; padding: 13px 16px; align-items: center;">
                            <div style="display: flex; align-items: center; gap: 12px; flex: 1; min-width: 0;">
                                <div class="settings-action-icon" style="width: 42px; height: 42px; border-radius: 11px; display: flex; align-items: center; justify-content: center; font-size: 1.05rem; flex-shrink: 0; background: rgba(255,255,255,0.06); color: var(--text-muted);">
                                    <i class="fas fa-map-marker-alt"></i>
                                </div>
                                <div class="settings-action-body" style="flex: 1; min-width: 0;">
                                    <h4 style="font-size: 0.92rem; font-weight: 700; color: var(--text-main); margin: 0 0 2px; display: flex; align-items: center; gap: 6px;">Locations Management <i class="fas fa-lock" style="font-size:0.75rem; color:var(--text-muted);"></i></h4>
                                    <p style="font-size: 0.73rem; color: var(--text-muted); margin: 0;">Manage delivery zones and pick-up areas</p>
                                </div>
                            </div>
                            <button type="button" onclick="StaffPermissions.openRequestModal('perm_locations')" class="settings-req-btn" style="padding: 7px 14px; font-size: 0.75rem; border-radius: 8px; background: rgba(0, 177, 79, 0.12); color: var(--primary); border: 1px solid rgba(0, 177, 79, 0.3); font-weight: 700; cursor: pointer;">
                                Request Access
                            </button>
                        </div>

                        <!-- Locations Management -->
                        <div id="mobileLocationsConfig" class="revenue-restricted">
                            <div class="settings-action-card stat-card" onclick="toggleLocationsModal()" style="background: var(--surface-container); border: 1px solid var(--border); border-radius: 14px; padding: 13px 16px; display: flex; align-items: center; gap: 14px; cursor: pointer;">
                                <div class="settings-action-icon" style="width: 42px; height: 42px; border-radius: 11px; display: flex; align-items: center; justify-content: center; font-size: 1.05rem; flex-shrink: 0; background: rgba(239, 68, 68, 0.12); color: #ef4444;">
                                    <i class="fas fa-map-marker-alt"></i>
                                </div>
                                <div class="settings-action-body" style="flex: 1; min-width: 0;">
                                    <h4 style="font-size: 0.92rem; font-weight: 700; color: var(--text-main); margin: 0 0 2px;">Locations Management</h4>
                                    <p style="font-size: 0.73rem; color: var(--text-muted); margin: 0;">Manage delivery zones and pick-up areas</p>
                                </div>
                                <div class="settings-action-tail" style="display: flex; align-items: center; gap: 8px; color: var(--text-muted); font-size: 0.8rem; flex-shrink: 0;"><i class="fas fa-chevron-right"></i></div>
                            </div>
                        </div>

                        <!-- Locked blackouts preview -->
                        <div id="lockPerm_blackout_dates" class="settings-action-card stat-card locked-card" style="display: none; justify-content: space-between; background: var(--surface-container); border: 1px dashed var(--border); border-radius: 14px; padding: 13px 16px; align-items: center;">
                            <div style="display: flex; align-items: center; gap: 12px; flex: 1; min-width: 0;">
                                <div class="settings-action-icon" style="width: 42px; height: 42px; border-radius: 11px; display: flex; align-items: center; justify-content: center; font-size: 1.05rem; flex-shrink: 0; background: rgba(255,255,255,0.06); color: var(--text-muted);">
                                    <i class="fas fa-calendar-times"></i>
                                </div>
                                <div class="settings-action-body" style="flex: 1; min-width: 0;">
                                    <h4 style="font-size: 0.92rem; font-weight: 700; color: var(--text-main); margin: 0 0 2px; display: flex; align-items: center; gap: 6px;">Blackout Dates <i class="fas fa-lock" style="font-size:0.75rem; color:var(--text-muted);"></i></h4>
                                    <p style="font-size: 0.73rem; color: var(--text-muted); margin: 0;">Block rentals during holidays or maintenance</p>
                                </div>
                            </div>
                            <button type="button" onclick="StaffPermissions.openRequestModal('perm_blackout_dates')" class="settings-req-btn" style="padding: 7px 14px; font-size: 0.75rem; border-radius: 8px; background: rgba(0, 177, 79, 0.12); color: var(--primary); border: 1px solid rgba(0, 177, 79, 0.3); font-weight: 700; cursor: pointer;">
                                Request Access
                            </button>
                        </div>

                        <!-- Blackout Dates -->
                        <div id="mobileBlackoutsConfig" class="revenue-restricted">
                            <div class="settings-action-card stat-card" onclick="toggleBlackoutsModal(true)" style="background: var(--surface-container); border: 1px solid var(--border); border-radius: 14px; padding: 13px 16px; display: flex; align-items: center; gap: 14px; cursor: pointer;">
                                <div class="settings-action-icon" style="width: 42px; height: 42px; border-radius: 11px; display: flex; align-items: center; justify-content: center; font-size: 1.05rem; flex-shrink: 0; background: rgba(234, 88, 12, 0.12); color: #ea580c;">
                                    <i class="fas fa-calendar-times"></i>
                                </div>
                                <div class="settings-action-body" style="flex: 1; min-width: 0;">
                                    <h4 style="font-size: 0.92rem; font-weight: 700; color: var(--text-main); margin: 0 0 2px;">Blackout Dates</h4>
                                    <p style="font-size: 0.73rem; color: var(--text-muted); margin: 0;">Block rentals during holidays or maintenance</p>
                                </div>
                                <div class="settings-action-tail" style="display: flex; align-items: center; gap: 8px; color: var(--text-muted); font-size: 0.8rem; flex-shrink: 0;"><i class="fas fa-chevron-right"></i></div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- GROUP 4: Messaging & System Maintenance -->
                <div class="settings-group" style="background: var(--surface); border: 1px solid var(--border); border-radius: 20px; padding: 20px 22px; box-shadow: 0 2px 14px rgba(0, 0, 0, 0.03);">
                    <div class="settings-group-header" style="display: flex; align-items: center; gap: 14px; margin-bottom: 16px; padding-bottom: 14px; border-bottom: 1px solid var(--border);">
                        <div class="settings-group-icon" style="width: 38px; height: 38px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1rem; flex-shrink: 0; background: rgba(139, 92, 246, 0.1); color: #8b5cf6;">
                            <i class="fas fa-database"></i>
                        </div>
                        <div>
                            <h3 class="settings-group-title" style="font-size: 1.05rem; font-weight: 800; color: var(--text-main); margin: 0 0 2px; letter-spacing: -0.2px;">Communications &amp; Maintenance</h3>
                            <p class="settings-group-desc" style="font-size: 0.76rem; color: var(--text-muted); margin: 0;">Email delivery infrastructure, subscriber broadcasts &amp; database health</p>
                        </div>
                    </div>

                    <div class="settings-cards-stack" style="display: flex; flex-direction: column; gap: 10px;">
                        <!-- SMTP Email -->
                        <div id="mobileSmtpConfig" class="revenue-restricted">
                            <div class="settings-action-card stat-card" onclick="toggleSmtpConfigModal()" style="background: var(--surface-container); border: 1px solid var(--border); border-radius: 14px; padding: 13px 16px; display: flex; align-items: center; gap: 14px; cursor: pointer;">
                                <div class="settings-action-icon" style="width: 42px; height: 42px; border-radius: 11px; display: flex; align-items: center; justify-content: center; font-size: 1.05rem; flex-shrink: 0; background: rgba(59, 130, 246, 0.12); color: #3b82f6;">
                                    <i class="fas fa-envelope"></i>
                                </div>
                                <div class="settings-action-body" style="flex: 1; min-width: 0;">
                                    <h4 style="font-size: 0.92rem; font-weight: 700; color: var(--text-main); margin: 0 0 2px;">System Email Settings</h4>
                                    <p id="smtpStatusLabel" style="font-size: 0.73rem; color: var(--text-muted); margin: 0;">Loading email status...</p>
                                </div>
                                <div class="settings-action-tail" style="display: flex; align-items: center; gap: 8px; color: var(--text-muted); font-size: 0.8rem; flex-shrink: 0;"><i class="fas fa-chevron-right"></i></div>
                            </div>
                        </div>

                        <!-- Newsletters -->
                        <div id="mobileNewsletterConfig">
                            <div class="settings-action-card stat-card" onclick="toggleNewsletterModal(true)" style="background: var(--surface-container); border: 1px solid var(--border); border-radius: 14px; padding: 13px 16px; display: flex; align-items: center; gap: 14px; cursor: pointer;">
                                <div class="settings-action-icon" style="width: 42px; height: 42px; border-radius: 11px; display: flex; align-items: center; justify-content: center; font-size: 1.05rem; flex-shrink: 0; background: rgba(14, 165, 233, 0.12); color: #0ea5e9;">
                                    <i class="fas fa-newspaper"></i>
                                </div>
                                <div class="settings-action-body" style="flex: 1; min-width: 0;">
                                    <h4 style="font-size: 0.92rem; font-weight: 700; color: var(--text-main); margin: 0 0 2px;">Newsletters &amp; Promo Broadcasts</h4>
                                    <p id="nlSettingsSubtitle" style="font-size: 0.73rem; color: var(--text-muted); margin: 0;">Broadcast promos, manage campaigns &amp; subscriber audience</p>
                                </div>
                                <div class="settings-action-tail" style="display: flex; align-items: center; gap: 8px; color: var(--text-muted); font-size: 0.8rem; flex-shrink: 0;"><i class="fas fa-chevron-right"></i></div>
                            </div>
                        </div>

                        <!-- Database Archive -->
                        <div id="adminMaintenanceConfig">
                            <div class="settings-action-card stat-card" onclick="toggleArchiveMaintenanceModal(true)" style="background: var(--surface-container); border: 1px solid var(--border); border-radius: 14px; padding: 13px 16px; display: flex; align-items: center; gap: 14px; cursor: pointer;">
                                <div class="settings-action-icon" style="width: 42px; height: 42px; border-radius: 11px; display: flex; align-items: center; justify-content: center; font-size: 1.05rem; flex-shrink: 0; background: rgba(139, 92, 246, 0.12); color: #8b5cf6;">
                                    <i class="fas fa-archive"></i>
                                </div>
                                <div class="settings-action-body" style="flex: 1; min-width: 0;">
                                    <h4 style="font-size: 0.92rem; font-weight: 700; color: var(--text-main); margin: 0 0 2px;">Database Archive &amp; Maintenance</h4>
                                    <p style="font-size: 0.73rem; color: var(--text-muted); margin: 0;">Archive old bookings, clean audit logs &amp; optimize database storage</p>
                                </div>
                                <div class="settings-action-tail" style="display: flex; align-items: center; gap: 8px; color: var(--text-muted); font-size: 0.8rem; flex-shrink: 0;"><i class="fas fa-chevron-right"></i></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>'''

with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

start_marker = '<!-- SETTINGS TAB -->'
end_marker = '<!-- ACTIVITY LOG TAB -->'

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    raise ValueError(f"Markers not found: start={start_idx}, end={end_idx}")

new_content = content[:start_idx] + new_settings_html + '\n\n\n\n\n\n\n    ' + content[end_idx:]

with open('admin_app/index.html', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Successfully applied bulletproof inline styles to settings markup!")
