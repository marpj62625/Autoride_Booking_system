import os

with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

target = """    async function loadSmtpStatus() {
        const statusDetail = document.getElementById('smtpStatusDetail');
        const actionsDiv = document.getElementById('smtpOAuthActions');
        const label = document.getElementById('smtpStatusLabel');
        
        if (statusDetail) statusDetail.textContent = "Loading status...";
        
        try {
            const res = await fetch(API_BASE + '/api/admin/smtp/status');
            const data = await res.json();
            
            if (data.is_linked) {
                if (statusDetail) statusDetail.innerHTML = `<span style="color:#00B14F;"><i class="fas fa-check-circle"></i> Connected</span><br><span style="font-size:0.8rem;color:var(--text-muted);font-weight:normal;">${data.email}</span>`;
                if (label) label.textContent = `Connected as ${data.email}`;
                if (actionsDiv) {
                    actionsDiv.innerHTML = `
                        <button onclick="disconnectSmtpGmail()" class="btn-premium" style="background:#dc2626;border-color:#dc2626;width:100%;padding:12px;font-size:0.85rem;font-weight:700;color:white;border-radius:10px;">
                            <i class="fas fa-unlink"></i> Disconnect Gmail Account
                        </button>
                    `;
                }
            } else {
                if (statusDetail) statusDetail.innerHTML = `<span style="color:var(--text-muted);"><i class="fas fa-times-circle"></i> Not Connected</span>`;
                if (label) label.textContent = "Click to configure notification email";
                if (actionsDiv) {
                    actionsDiv.innerHTML = `
                        <button onclick="connectSmtpGmail()" class="btn-premium" style="width:100%;padding:12px;font-size:0.85rem;font-weight:700;color:white;border-radius:10px;background:var(--primary);border-color:var(--primary);">
                            <i class="fab fa-google"></i> Connect Gmail Account
                        </button>
                    `;
                }
            }
        } catch (e) {
            if (statusDetail) statusDetail.textContent = "Error loading status";
        }
    }"""

replacement = """    async function loadSmtpStatus() {
        const statusDetail = document.getElementById('smtpStatusDetail');
        const actionsDiv = document.getElementById('smtpOAuthActions');
        const label = document.getElementById('smtpStatusLabel');
        
        if (statusDetail) statusDetail.textContent = "Loading status...";
        
        try {
            const res = await fetch(API_BASE + '/api/admin/smtp/status');
            const data = await res.json();
            
            let statusHtml = '';
            if (data.is_linked && data.is_valid) {
                statusHtml = `<span style="color:#00B14F;"><i class="fas fa-check-circle"></i> Google OAuth Active</span><br><span style="font-size:0.8rem;color:var(--text-muted);font-weight:normal;">${data.email}</span>`;
                if (label) label.textContent = `Connected as ${data.email}`;
            } else if (data.is_linked && !data.is_valid) {
                statusHtml = `<span style="color:#ef4444;"><i class="fas fa-exclamation-triangle"></i> Token Expired / Needs Re-auth</span><br><span style="font-size:0.8rem;color:var(--text-muted);font-weight:normal;">${data.email}</span><br><span style="font-size:0.75rem;color:#ef4444;">Google test token expired. Please click Re-Authorize below or enter an App Password.</span>`;
                if (label) label.textContent = `Email Token Expired (${data.email})`;
            } else if (data.has_manual_smtp) {
                statusHtml = `<span style="color:#00B14F;"><i class="fas fa-key"></i> Gmail App Password Active</span><br><span style="font-size:0.8rem;color:var(--text-muted);font-weight:normal;">${data.manual_smtp_user || 'Configured'}</span>`;
                if (label) label.textContent = `SMTP Active (${data.manual_smtp_user || 'App Password'})`;
            } else {
                statusHtml = `<span style="color:var(--text-muted);"><i class="fas fa-times-circle"></i> Not Configured</span><br><span style="font-size:0.75rem;color:var(--text-muted);">Connect Gmail or enter App Password below</span>`;
                if (label) label.textContent = "Click to configure notification email";
            }
            if (statusDetail) statusDetail.innerHTML = statusHtml;

            if (actionsDiv) {
                actionsDiv.innerHTML = `
                    <div style="display:flex;flex-direction:column;gap:8px;">
                        <button onclick="connectSmtpGmail()" class="btn-premium" style="width:100%;padding:11px;font-size:0.85rem;font-weight:700;color:white;border-radius:10px;background:var(--primary);border-color:var(--primary);cursor:pointer;">
                            <i class="fab fa-google"></i> ${data.is_linked && !data.is_valid ? 'Re-Authorize Gmail Account' : (data.is_linked ? 'Reconnect Gmail' : 'Connect Gmail Account')}
                        </button>
                        ${data.is_linked ? `
                            <button onclick="disconnectSmtpGmail()" class="btn-premium" style="background:transparent;border:1px solid #ef4444;width:100%;padding:8px;font-size:0.8rem;font-weight:600;color:#ef4444;border-radius:8px;cursor:pointer;">
                                <i class="fas fa-unlink"></i> Disconnect Google OAuth
                            </button>
                        ` : ''}
                    </div>

                    <div style="margin-top:14px;padding-top:14px;border-top:1px solid var(--border);">
                        <div style="font-size:0.8rem;font-weight:700;color:var(--text-main);margin-bottom:6px;display:flex;align-items:center;gap:6px;">
                            <i class="fas fa-shield-alt" style="color:var(--primary);"></i> Permanent Option: Gmail App Password
                        </div>
                        <div style="font-size:0.75rem;color:var(--text-muted);margin-bottom:10px;line-height:1.4;">
                            Generate a 16-character password in Google Account (Security &gt; 2-Step Verification &gt; App Passwords) for 100% reliable, never-expiring email sending.
                        </div>
                        <div style="display:flex;flex-direction:column;gap:8px;">
                            <input id="manualSmtpEmail" type="email" placeholder="Your Gmail address (e.g. yourname@gmail.com)" style="width:100%;padding:10px 12px;background:var(--surface);border:1px solid var(--border);border-radius:8px;color:var(--text-main);font-size:0.8rem;" value="${data.manual_smtp_user || (data.email || '')}">
                            <input id="manualSmtpPass" type="password" placeholder="16-character Gmail App Password" style="width:100%;padding:10px 12px;background:var(--surface);border:1px solid var(--border);border-radius:8px;color:var(--text-main);font-size:0.8rem;">
                            <button onclick="saveManualSmtpSettings()" class="btn-premium" style="width:100%;padding:10px;font-size:0.8rem;font-weight:700;background:rgba(255,255,255,0.08);border:1px solid var(--border);color:var(--text-main);border-radius:8px;cursor:pointer;">
                                <i class="fas fa-save"></i> Save Gmail App Password
                            </button>
                        </div>
                    </div>

                    <div style="margin-top:14px;padding-top:14px;border-top:1px solid var(--border);">
                        <div style="font-size:0.8rem;font-weight:700;color:var(--text-main);margin-bottom:6px;">
                            <i class="fas fa-paper-plane" style="color:var(--primary);"></i> Test Email Sending
                        </div>
                        <div style="display:flex;gap:6px;">
                            <input id="testEmailRecipient" type="email" placeholder="Enter recipient email..." style="flex:1;padding:8px 12px;background:var(--surface);border:1px solid var(--border);border-radius:8px;color:var(--text-main);font-size:0.8rem;" value="${data.email || ''}">
                            <button onclick="sendTestNotificationEmail()" class="btn-premium" style="padding:8px 14px;font-size:0.8rem;font-weight:700;background:var(--primary);color:white;border-radius:8px;cursor:pointer;">
                                Test Send
                            </button>
                        </div>
                        <div id="testEmailFeedback" style="font-size:0.75rem;margin-top:6px;"></div>
                    </div>
                `;
            }
        } catch (e) {
            if (statusDetail) statusDetail.textContent = "Error loading status";
        }
    }

    async function saveManualSmtpSettings() {
        const email = document.getElementById('manualSmtpEmail')?.value?.trim();
        const appPass = document.getElementById('manualSmtpPass')?.value?.trim();
        if (!email || !appPass) {
            alert('Please provide both your Gmail address and 16-character App Password.');
            return;
        }
        try {
            const res = await fetch(API_BASE + '/api/admin/smtp/manual-save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: email, app_password: appPass })
            });
            const d = await res.json();
            if (res.ok && d.success) {
                alert('Gmail App Password saved and verified successfully!');
                loadSmtpStatus();
            } else {
                alert('Failed to save App Password: ' + (d.error || 'Unknown error'));
            }
        } catch (e) {
            alert('Error saving App Password: ' + e.message);
        }
    }

    async function sendTestNotificationEmail() {
        const recipient = document.getElementById('testEmailRecipient')?.value?.trim();
        const fb = document.getElementById('testEmailFeedback');
        if (!recipient) {
            alert('Please enter a recipient email.');
            return;
        }
        if (fb) fb.innerHTML = '<span style="color:var(--text-muted);"><i class="fas fa-spinner fa-spin"></i> Sending test email...</span>';
        try {
            const res = await fetch(API_BASE + '/api/admin/smtp/test-send?email=' + encodeURIComponent(recipient));
            const d = await res.json();
            if (res.ok && d.success) {
                if (fb) fb.innerHTML = `<span style="color:#00B14F;"><i class="fas fa-check"></i> ${d.message}</span>`;
            } else {
                if (fb) fb.innerHTML = `<span style="color:#ef4444;"><i class="fas fa-times"></i> ${d.error || 'Failed to send'}</span>`;
            }
        } catch (e) {
            if (fb) fb.innerHTML = `<span style="color:#ef4444;">Error: ${e.message}</span>`;
        }
    }"""

assert target in content, "Target not found in admin_app/index.html!"
content = content.replace(target, replacement)
content = content.replace(
    'window.loadSmtpStatus = loadSmtpStatus;',
    'window.loadSmtpStatus = loadSmtpStatus;\n    window.saveManualSmtpSettings = saveManualSmtpSettings;\n    window.sendTestNotificationEmail = sendTestNotificationEmail;'
)

with open('admin_app/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated admin_app/index.html successfully!")
