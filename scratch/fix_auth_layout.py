# -*- coding: utf-8 -*-
"""Replace the auth split-screen CSS with a proper full-viewport version."""

with open('frontend/index.html', 'r', encoding='latin-1') as f:
    html = f.read()

# The exact block to replace (identified by byte positions 32079-33899)
old_block = html[32079:33899]

new_block = """/* Auth pages: full-viewport split-screen on desktop */
          /* Auth pages override the sidebar offset - they cover the full screen */
          #page-login.auth-page.active,
          #page-register.auth-page.active,
          #page-otp-verify.auth-page.active {
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            width: 100vw;
            height: 100vh;
            z-index: 900;
            margin-left: 0;
            display: flex;
            flex-direction: row;
            align-items: stretch;
            padding: 0;
          }

          /* Left hero panel */
          .auth-hero-panel {
            display: flex;
            flex: 1 1 0%;
            min-height: 100vh;
            background: linear-gradient(160deg, var(--primary-light) 0%, var(--primary) 55%, var(--primary-dark) 100%);
            align-items: center;
            justify-content: center;
            padding: 60px 56px;
            position: relative;
            overflow: hidden;
          }

          /* Decorative blur circles */
          .auth-hero-panel::before {
            content: '';
            position: absolute;
            top: -100px; right: -100px;
            width: 380px; height: 380px;
            border-radius: 50%;
            background: rgba(255,255,255,0.08);
            pointer-events: none;
          }

          .auth-hero-panel::after {
            content: '';
            position: absolute;
            bottom: -80px; left: -80px;
            width: 300px; height: 300px;
            border-radius: 50%;
            background: rgba(0,83,57,0.3);
            pointer-events: none;
          }

          .auth-hero-inner {
            display: flex;
            flex-direction: column;
            align-items: flex-start;
            max-width: 420px;
            position: relative;
            z-index: 1;
          }

          /* Right form panel */
          .auth-container {
            flex: 0 0 440px;
            width: 440px;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 52px 48px;
            background: #ffffff;
            overflow-y: auto;
            box-shadow: -8px 0 40px rgba(0,0,0,0.10);
          }

          /* Hide auth-logo inside form on desktop (hero panel shows it) */
          .auth-hero-panel ~ .auth-container .auth-logo {
            display: none;
          }

          /* Auth card: borderless inside the white panel */
          .auth-hero-panel ~ .auth-container .auth-card {
            border: none;
            box-shadow: none;
            padding: 0;
            border-radius: 0;
            max-width: 100%;
            background: transparent;
          }

          .auth-hero-panel ~ .auth-container .auth-card h2 {
            font-size: 2rem;
            color: #1a1a2e;
          }

          .auth-hero-panel ~ .auth-container .auth-card p.subtitle {
            color: #6b7280;
            margin-bottom: 32px;
          }

          .auth-hero-panel ~ .auth-container .form-group input,
          .auth-hero-panel ~ .auth-container .form-group select {
            border: 1.5px solid #e5e7eb;
            background: #f9fafb;
            color: #111827;
          }

          .auth-hero-panel ~ .auth-container .form-group input:focus,
          .auth-hero-panel ~ .auth-container .form-group select:focus {
            border-color: var(--primary);
            background: #ffffff;
          }

          .auth-hero-panel ~ .auth-container .divider {
            color: #9ca3af;
          }

          .auth-hero-panel ~ .auth-container .btn-google {
            border: 1.5px solid #e5e7eb;
            background: #ffffff;
            color: #374151;
          }

          .auth-hero-panel ~ .auth-container .auth-link {
            color: #6b7280;
          }

          /* Action grid: 3 cols on desktop */
          .action-btn-grid {
            grid-template-columns: repeat(3, 1fr);
          }

          /* Cards: slightly more margin */
          .card {
            margin-bottom: 16px;
          }
        }"""

if old_block in html:
    html = html.replace(old_block, new_block, 1)
    with open('frontend/index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("REPLACED OK")
    print(f"File size: {len(html):,}")
else:
    print("OLD BLOCK NOT FOUND - trying index replacement")
    html = html[:32079] + new_block + html[33899:]
    with open('frontend/index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("INDEX REPLACED OK")
    print(f"File size: {len(html):,}")
