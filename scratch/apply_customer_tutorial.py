import os
import sys

# 1. PATCH customer_mobile/www/index.html
with open('customer_mobile/www/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Add CSS before </style>
tut_css = """
/* Tutorial Onboarding Modal Styles (Design 1: Swipeable Cards) */
.tutorial-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 100000;
  background: rgba(0, 0, 0, 0.85);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  box-sizing: border-box;
  animation: tutFadeIn 0.25s ease-out;
}
@keyframes tutFadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
.tutorial-modal-card {
  width: 100%;
  max-width: 440px;
  background: var(--bg-card, #141414);
  border: 1px solid var(--border, rgba(255,255,255,0.1));
  border-radius: 24px;
  box-shadow: 0 24px 60px rgba(0,0,0,0.6);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
  box-sizing: border-box;
  animation: tutScaleUp 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
@keyframes tutScaleUp {
  from { transform: scale(0.92); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}
.tutorial-header {
  padding: 18px 22px 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.tutorial-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(0, 177, 79, 0.12);
  color: #00B14F;
  border: 1px solid rgba(0, 177, 79, 0.3);
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 0.72rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.tutorial-step-text {
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--text-muted, #94a3b8);
}
.tutorial-skip-btn {
  background: transparent;
  border: none;
  color: var(--text-muted, #94a3b8);
  font-size: 0.8rem;
  font-weight: 700;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 8px;
  transition: all 0.2s;
}
.tutorial-skip-btn:hover {
  color: var(--text-primary, #ffffff);
  background: rgba(255,255,255,0.06);
}
.tutorial-carousel {
  overflow: hidden;
  width: 100%;
  position: relative;
  touch-action: pan-y;
}
.tutorial-track {
  display: flex;
  width: 400%;
  transition: transform 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}
.tutorial-slide {
  width: 25%;
  flex-shrink: 0;
  padding: 16px 24px 20px;
  box-sizing: border-box;
  text-align: center;
}
.tutorial-icon-wrap {
  width: 68px;
  height: 68px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.85rem;
  margin: 0 auto 16px;
  border: 1.5px solid;
  box-shadow: 0 8px 24px rgba(0,0,0,0.25);
}
.tutorial-slide-title {
  font-size: 1.25rem;
  font-weight: 800;
  color: var(--text-primary, #ffffff);
  margin: 0 0 6px;
  letter-spacing: -0.02em;
}
.tutorial-slide-desc {
  font-size: 0.82rem;
  color: var(--text-secondary, #a1a1aa);
  margin: 0 0 16px;
  line-height: 1.45;
}
.tutorial-features {
  background: var(--bg-input, rgba(255,255,255,0.03));
  border: 1px solid var(--border, rgba(255,255,255,0.08));
  border-radius: 14px;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  text-align: left;
}
.tut-feature-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 0.78rem;
  color: var(--text-primary, #e2e8f0);
  line-height: 1.35;
}
.tut-feature-item i {
  color: #00B14F;
  font-size: 0.85rem;
  margin-top: 2px;
  flex-shrink: 0;
}
.tutorial-footer {
  padding: 14px 22px 20px;
  border-top: 1px solid var(--border, rgba(255,255,255,0.08));
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  background: rgba(0,0,0,0.15);
}
.tutorial-dots {
  display: flex;
  align-items: center;
  gap: 6px;
}
.tut-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgba(255,255,255,0.2);
  cursor: pointer;
  transition: all 0.25s ease;
}
.tut-dot.active {
  width: 24px;
  border-radius: 12px;
  background: #00B14F;
  box-shadow: 0 0 10px rgba(0, 177, 79, 0.5);
}
.tutorial-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.tut-btn-secondary {
  background: rgba(255,255,255,0.08);
  border: 1px solid var(--border, rgba(255,255,255,0.12));
  color: var(--text-primary, #ffffff);
  padding: 9px 16px;
  border-radius: 12px;
  font-size: 0.82rem;
  font-weight: 700;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: background 0.2s;
}
.tut-btn-secondary:hover {
  background: rgba(255,255,255,0.12);
}
.tut-btn-primary {
  background: linear-gradient(135deg, #00B14F, #00873c);
  border: none;
  color: #ffffff;
  padding: 9px 20px;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 800;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  box-shadow: 0 4px 14px rgba(0, 177, 79, 0.35);
  transition: transform 0.15s, box-shadow 0.15s;
}
.tut-btn-primary:active {
  transform: scale(0.96);
}

/* Landscape Mobile Adaptation for Tutorial Modal */
@media (orientation: landscape) and (max-height: 550px) {
  .tutorial-modal-card {
    max-width: 520px;
    max-height: 94vh;
    overflow-y: auto;
  }
  .tutorial-slide {
    padding: 8px 18px 12px;
  }
  .tutorial-icon-wrap {
    width: 44px;
    height: 44px;
    font-size: 1.25rem;
    margin-bottom: 8px;
  }
  .tutorial-slide-title {
    font-size: 1rem;
    margin-bottom: 2px;
  }
  .tutorial-slide-desc {
    font-size: 0.74rem;
    margin-bottom: 8px;
  }
  .tutorial-features {
    padding: 8px 10px;
    gap: 4px;
  }
  .tut-feature-item {
    font-size: 0.72rem;
  }
  .tutorial-footer {
    padding: 8px 18px 12px;
  }
}
"""

if '</style>' in html and '.tutorial-modal-overlay' not in html:
    html = html.replace('</style>', tut_css + '\n</style>', 1)
    print("Added tutorial CSS to index.html")

# Add Home Tutorial Banner in page-home
home_target = '<div style="padding:0 16px;">'
home_banner_html = """  <div style="padding:0 16px;">
    <!-- 1st-Time User Quick Guide Banner (Design 1) -->
    <div id="homeTutorialBanner" onclick="openCustomerTutorial(true)" style="margin-bottom:16px;padding:14px 18px;background:linear-gradient(135deg, rgba(0,177,79,0.12), rgba(0,177,79,0.03));border:1px solid rgba(0,177,79,0.28);border-radius:18px;display:flex;align-items:center;justify-content:space-between;cursor:pointer;gap:12px;box-shadow:0 4px 16px rgba(0,177,79,0.06);transition:transform 0.2s,border-color 0.2s;">
      <div style="display:flex;align-items:center;gap:12px;min-width:0;">
        <div style="width:40px;height:40px;border-radius:12px;background:rgba(0,177,79,0.18);display:flex;align-items:center;justify-content:center;color:var(--primary);font-size:1.15rem;flex-shrink:0;">
          <i class="fas fa-compass"></i>
        </div>
        <div style="min-width:0;">
          <div style="font-weight:800;font-size:0.9rem;color:var(--text-primary);display:flex;align-items:center;gap:6px;">
            <span>First time renting a car?</span>
            <span style="font-size:0.62rem;font-weight:800;background:#00B14F;color:#fff;padding:1px 6px;border-radius:6px;letter-spacing:0.3px;">GUIDE</span>
          </div>
          <div style="font-size:0.75rem;color:var(--text-secondary);margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
            Tingnan ang 4-step quick walkthrough kung paano mag-book
          </div>
        </div>
      </div>
      <i class="fas fa-chevron-right" style="color:var(--primary);font-size:0.9rem;flex-shrink:0;"></i>
    </div>"""

if home_target in html and 'homeTutorialBanner' not in html:
    html = html.replace(home_target, home_banner_html, 1)
    print("Added homeTutorialBanner to page-home")

# Add More Guide Card in page-more
more_target = '<div class="more-grid">'
more_guide_html = """<div class="more-grid">
      <!-- App Guide / First Time User Tutorial -->
      <div class="more-card" id="moreAppGuideCard" onclick="openCustomerTutorial(true)">
        <div class="more-card-icon" style="background:rgba(0,177,79,0.1);"><i class="fas fa-graduation-cap" style="color:var(--primary);font-size:1.6rem;"></i></div>
        <div class="more-card-body">
          <h4>How to Rent (Guide)</h4>
          <p>4-step quick walkthrough on booking a vehicle</p>
        </div>
        <i class="fas fa-arrow-right more-card-arrow"></i>
      </div>"""

if more_target in html and 'moreAppGuideCard' not in html:
    html = html.replace(more_target, more_guide_html, 1)
    print("Added moreAppGuideCard to page-more")

# Add Customer Tutorial Modal markup before </body>
modal_html = """
<!-- FIRST-TIME USER TUTORIAL / ONBOARDING MODAL (DESIGN 1: SWIPEABLE CARDS) -->
<div id="customerTutorialModal" class="tutorial-modal-overlay" style="display:none;" onclick="if(event.target===this)closeCustomerTutorial()">
  <div class="tutorial-modal-card">
    <!-- Header with Step Indicator & Skip Button -->
    <div class="tutorial-header">
      <div class="tutorial-badge"><i class="fas fa-sparkles"></i> <span>Quick Guide</span></div>
      <div id="tutorialStepIndicator" class="tutorial-step-text">Step 1 of 4</div>
      <button type="button" class="tutorial-skip-btn" onclick="skipCustomerTutorial()">Skip <i class="fas fa-times"></i></button>
    </div>

    <!-- Carousel Viewport -->
    <div class="tutorial-carousel" id="tutorialCarousel">
      <div class="tutorial-track" id="tutorialTrack">
        
        <!-- Slide 1: Pumili ng Sasakyan -->
        <div class="tutorial-slide">
          <div class="tutorial-icon-wrap" style="background: rgba(0, 177, 79, 0.12); color: #00B14F; border-color: rgba(0, 177, 79, 0.3);">
            <i class="fas fa-car"></i>
          </div>
          <h3 class="tutorial-slide-title">1. Pumili ng Sasakyan</h3>
          <p class="tutorial-slide-desc">Pumili mula sa aming iba't ibang de-kalidad na sedan, SUV, van, at hatchback para sa iyong biyahe.</p>
          <div class="tutorial-features">
            <div class="tut-feature-item"><i class="fas fa-check-circle"></i> <span>Piliin ang kulay at Automatic o Manual transmission</span></div>
            <div class="tut-feature-item"><i class="fas fa-check-circle"></i> <span>Tingnan ang seating capacity, mileage, at luggage space</span></div>
            <div class="tut-feature-item"><i class="fas fa-check-circle"></i> <span>Transparent daily rates nang walang hidden charges</span></div>
          </div>
        </div>

        <!-- Slide 2: AI License Verification -->
        <div class="tutorial-slide">
          <div class="tutorial-icon-wrap" style="background: rgba(59, 130, 246, 0.12); color: #3b82f6; border-color: rgba(59, 130, 246, 0.3);">
            <i class="fas fa-id-card"></i>
          </div>
          <h3 class="tutorial-slide-title">2. Mabilis na Identity Check</h3>
          <p class="tutorial-slide-desc">Mag-upload ng malinaw na litrato ng iyong Driver's License gamit ang ating AI-powered OCR scanner.</p>
          <div class="tutorial-features">
            <div class="tut-feature-item"><i class="fas fa-check-circle"></i> <span>Awtomatikong binabasa at bini-verify ang lisensya</span></div>
            <div class="tut-feature-item"><i class="fas fa-check-circle"></i> <span>Isang beses lang kailangang mag-upload para sa susunod na bookings</span></div>
            <div class="tut-feature-item"><i class="fas fa-check-circle"></i> <span>100% protektado ang data ayon sa Data Privacy Act (RA 10173)</span></div>
          </div>
        </div>

        <!-- Slide 3: Petsa at Delivery Location -->
        <div class="tutorial-slide">
          <div class="tutorial-icon-wrap" style="background: rgba(245, 158, 11, 0.12); color: #f59e0b; border-color: rgba(245, 158, 11, 0.3);">
            <i class="fas fa-map-marked-alt"></i>
          </div>
          <h3 class="tutorial-slide-title">3. Petsa at Lokasyon</h3>
          <p class="tutorial-slide-desc">Itakda ang rental schedule at piliin kung paano mo gustong matanggap ang sasakyan.</p>
          <div class="tutorial-features">
            <div class="tut-feature-item"><i class="fas fa-check-circle"></i> <span>Pumili ng Pick-up at Return date & time sa interactive calendar</span></div>
            <div class="tut-feature-item"><i class="fas fa-check-circle"></i> <span>Pumili ng Self-Pickup o Door-to-Door Delivery</span></div>
            <div class="tut-feature-item"><i class="fas fa-check-circle"></i> <span>I-pin ang eksaktong lokasyon gamit ang ating interactive map</span></div>
          </div>
        </div>

        <!-- Slide 4: Secure Payment at Pag-biyahe -->
        <div class="tutorial-slide">
          <div class="tutorial-icon-wrap" style="background: rgba(16, 185, 129, 0.12); color: #10b981; border-color: rgba(16, 185, 129, 0.3);">
            <i class="fas fa-shield-alt"></i>
          </div>
          <h3 class="tutorial-slide-title">4. Bayad at Pag-biyahe</h3>
          <p class="tutorial-slide-desc">Magbayad nang ligtas via GCash, Maya, o Card, at simulan ang masayang biyahe!</p>
          <div class="tutorial-features">
            <div class="tut-feature-item"><i class="fas fa-check-circle"></i> <span>Secure online payment via PayMongo na may instant receipt</span></div>
            <div class="tut-feature-item"><i class="fas fa-check-circle"></i> <span>Real-time booking countdown at live GPS tracking</span></div>
            <div class="tut-feature-item"><i class="fas fa-check-circle"></i> <span>Kumita ng loyalty reward points sa bawat completed rental</span></div>
          </div>
        </div>

      </div>
    </div>

    <!-- Pagination Dots & Footer Controls -->
    <div class="tutorial-footer">
      <div class="tutorial-dots" id="tutorialDots">
        <span class="tut-dot active" onclick="goToTutorialSlide(0)"></span>
        <span class="tut-dot" onclick="goToTutorialSlide(1)"></span>
        <span class="tut-dot" onclick="goToTutorialSlide(2)"></span>
        <span class="tut-dot" onclick="goToTutorialSlide(3)"></span>
      </div>

      <div class="tutorial-actions">
        <button type="button" id="tutPrevBtn" class="tut-btn-secondary" onclick="prevTutorialSlide()" style="display:none;">
          <i class="fas fa-arrow-left"></i> <span>Bumalik</span>
        </button>
        <button type="button" id="tutNextBtn" class="tut-btn-primary" onclick="nextTutorialSlide()">
          <span>Susunod</span> <i class="fas fa-arrow-right"></i>
        </button>
      </div>
    </div>
  </div>
</div>
"""

if '<script src="js/anime.min.js">' in html and 'customerTutorialModal' not in html:
    html = html.replace('<script src="js/anime.min.js">', modal_html + '\n<script src="js/anime.min.js">', 1)
    print("Added customerTutorialModal markup before scripts")

with open('customer_mobile/www/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("SUCCESS: customer_mobile/www/index.html updated.")

# 2. PATCH customer_mobile/www/style.css
with open('customer_mobile/www/style.css', 'r', encoding='utf-8') as f:
    css_content = f.read()

if '.tutorial-modal-overlay' not in css_content:
    css_content += '\n' + tut_css
    with open('customer_mobile/www/style.css', 'w', encoding='utf-8') as f:
        f.write(css_content)
    print("SUCCESS: customer_mobile/www/style.css updated.")

# 3. PATCH customer_mobile/www/js/app.js
with open('customer_mobile/www/js/app.js', 'r', encoding='utf-8') as f:
    js_content = f.read()

# Add checkFirstTimeTutorial to loadHome
load_home_target = """  if (typeof checkUnreviewedBookings === 'function') {
    checkUnreviewedBookings();
  }
  updateNotifBadge();"""

load_home_replacement = """  if (typeof checkUnreviewedBookings === 'function') {
    checkUnreviewedBookings();
  }
  updateNotifBadge();
  if (typeof checkFirstTimeTutorial === 'function') {
    setTimeout(function() { checkFirstTimeTutorial(); }, 600);
  }"""

if load_home_target in js_content and 'checkFirstTimeTutorial' not in js_content:
    js_content = js_content.replace(load_home_target, load_home_replacement, 1)
    print("Added checkFirstTimeTutorial call in loadHome")

tut_js = """
// ===========================================================================
// FIRST-TIME USER TUTORIAL (DESIGN 1: SWIPEABLE CARDS)
// ===========================================================================
var _tutorialCurrentSlide = 0;
var _tutorialTotalSlides = 4;
var _tutTouchStartX = 0;
var _tutTouchEndX = 0;

function openCustomerTutorial(force) {
  if (!force && localStorage.getItem('autoride_tutorial_seen')) {
    return;
  }
  var modal = document.getElementById('customerTutorialModal');
  if (!modal) return;
  _tutorialCurrentSlide = 0;
  updateTutorialSlide();
  modal.style.display = 'flex';
  
  // Attach touch swipe listeners
  var carousel = document.getElementById('tutorialCarousel');
  if (carousel && !carousel._hasSwipeListeners) {
    carousel._hasSwipeListeners = true;
    carousel.addEventListener('touchstart', function(e) {
      if (e.changedTouches && e.changedTouches[0]) {
        _tutTouchStartX = e.changedTouches[0].screenX;
      }
    }, { passive: true });
    carousel.addEventListener('touchend', function(e) {
      if (e.changedTouches && e.changedTouches[0]) {
        _tutTouchEndX = e.changedTouches[0].screenX;
        handleTutorialSwipe();
      }
    }, { passive: true });
  }
}

function handleTutorialSwipe() {
  var diff = _tutTouchStartX - _tutTouchEndX;
  if (Math.abs(diff) > 40) {
    if (diff > 0) {
      nextTutorialSlide();
    } else {
      prevTutorialSlide();
    }
  }
}

function updateTutorialSlide() {
  var track = document.getElementById('tutorialTrack');
  var indicator = document.getElementById('tutorialStepIndicator');
  var prevBtn = document.getElementById('tutPrevBtn');
  var nextBtn = document.getElementById('tutNextBtn');
  var dots = document.querySelectorAll('.tut-dot');

  if (track) {
    track.style.transform = 'translateX(-' + (_tutorialCurrentSlide * 25) + '%)';
  }
  if (indicator) {
    indicator.textContent = 'Step ' + (_tutorialCurrentSlide + 1) + ' of ' + _tutorialTotalSlides;
  }
  if (dots && dots.length > 0) {
    dots.forEach(function(dot, idx) {
      if (idx === _tutorialCurrentSlide) {
        dot.classList.add('active');
      } else {
        dot.classList.remove('active');
      }
    });
  }
  if (prevBtn) {
    prevBtn.style.display = _tutorialCurrentSlide === 0 ? 'none' : 'inline-flex';
  }
  if (nextBtn) {
    if (_tutorialCurrentSlide === _tutorialTotalSlides - 1) {
      nextBtn.innerHTML = '<i class="fas fa-check"></i> <span>Magsimula Na</span>';
    } else {
      nextBtn.innerHTML = '<span>Susunod</span> <i class="fas fa-arrow-right"></i>';
    }
  }
}

function nextTutorialSlide() {
  if (_tutorialCurrentSlide < _tutorialTotalSlides - 1) {
    _tutorialCurrentSlide++;
    updateTutorialSlide();
  } else {
    finishCustomerTutorial();
  }
}

function prevTutorialSlide() {
  if (_tutorialCurrentSlide > 0) {
    _tutorialCurrentSlide--;
    updateTutorialSlide();
  }
}

function goToTutorialSlide(idx) {
  if (idx >= 0 && idx < _tutorialTotalSlides) {
    _tutorialCurrentSlide = idx;
    updateTutorialSlide();
  }
}

function closeCustomerTutorial() {
  var modal = document.getElementById('customerTutorialModal');
  if (modal) modal.style.display = 'none';
}

function skipCustomerTutorial() {
  localStorage.setItem('autoride_tutorial_seen', 'true');
  closeCustomerTutorial();
  if (typeof showToast === 'function') {
    showToast('Welcome to Autoride! Puwede mo itong buksan ulit sa More menu.', 'info');
  }
}

function finishCustomerTutorial() {
  localStorage.setItem('autoride_tutorial_seen', 'true');
  closeCustomerTutorial();
  if (typeof showToast === 'function') {
    showToast('Handa ka na mag-rent! Mag-browse at piliin ang iyong sasakyan.', 'success');
  }
}

function checkFirstTimeTutorial() {
  if (currentUser && currentUser.id && window.currentPage === 'page-home') {
    if (!localStorage.getItem('autoride_tutorial_seen')) {
      openCustomerTutorial();
    }
  }
}

window.openCustomerTutorial = openCustomerTutorial;
window.skipCustomerTutorial = skipCustomerTutorial;
window.finishCustomerTutorial = finishCustomerTutorial;
window.nextTutorialSlide = nextTutorialSlide;
window.prevTutorialSlide = prevTutorialSlide;
window.goToTutorialSlide = goToTutorialSlide;
window.closeCustomerTutorial = closeCustomerTutorial;
window.checkFirstTimeTutorial = checkFirstTimeTutorial;
"""

if 'openCustomerTutorial' not in js_content:
    js_content += '\n' + tut_js
    with open('customer_mobile/www/js/app.js', 'w', encoding='utf-8') as f:
        f.write(js_content)
    print("SUCCESS: customer_mobile/www/js/app.js updated.")

print("\nALL CUSTOMER TUTORIAL CODE APPLIED CLEANLY!")
