with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

target = """                g.settings.forEach(s => {
                    html += this.renderField(s);
                });

                html += `
                        </div>
                    </div>
                `;"""

replacement = """                if (cat === 'email_smtp') {
                    html += `
                        <div style="grid-column: 1 / -1; margin-bottom: 8px; padding: 14px 16px; background: rgba(2, 132, 199, 0.08); border: 1px solid rgba(2, 132, 199, 0.25); border-radius: 12px; display: flex; align-items: center; justify-content: space-between; gap: 14px; flex-wrap: wrap;">
                            <div>
                                <div style="font-size: 0.88rem; font-weight: 700; color: var(--text-main); display: flex; align-items: center; gap: 8px;">
                                    <i class="fas fa-satellite-dish" style="color: #0284c7;"></i> System Email Connector & Diagnostics
                                </div>
                                <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 3px;">
                                    Connect or re-authorize Gmail with 1-click, configure a permanent App Password, and test live email delivery.
                                </div>
                            </div>
                            <button type="button" onclick="toggleSmtpConfigModal()" class="btn-premium" style="padding: 10px 18px; font-size: 0.82rem; font-weight: 700; background: var(--primary); color: white; border-radius: 10px; cursor: pointer; white-space: nowrap; display: inline-flex; align-items: center; gap: 8px;">
                                <i class="fas fa-plug"></i> Open Re-Authorize &amp; Email Tools
                            </button>
                        </div>
                    `;
                }

                g.settings.forEach(s => {
                    html += this.renderField(s);
                });

                html += `
                        </div>
                    </div>
                `;"""

assert target in content, "Target block not found!"
content = content.replace(target, replacement)

with open('admin_app/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated admin_app/index.html successfully!")
