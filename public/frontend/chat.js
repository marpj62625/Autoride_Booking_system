function initChat() {
    const chatHtml = `
        <div class="chat-widget">
            <button class="chat-button" id="chatToggle">
                <svg width="28" height="28" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"></path></svg>
            </button>
            <div class="chat-window chat-hidden" id="chatWindow">
                <div class="chat-header">
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <div style="width: 10px; height: 10px; background: #4ade80; border-radius: 50%;"></div>
                        <span style="font-weight: 600;">Autoride Support</span>
                    </div>
                    <button id="closeChat" style="background:none; border:none; color:white; cursor:pointer; font-size: 1.2rem;">&times;</button>
                </div>
                <div class="chat-messages" id="chatMessages">
                    <div class="chat-bubble bubble-bot">Hello! 👋 I'm the Autoride assistant. Ask me about booking, pricing, requirements, payments, and more!</div>
                    <div class="chat-quick-replies" id="quickReplies">
                        <button class="quick-reply-btn" data-msg="How to book?">📋 How to book</button>
                        <button class="quick-reply-btn" data-msg="What are the prices?">💰 Pricing</button>
                        <button class="quick-reply-btn" data-msg="What are the requirements?">📄 Requirements</button>
                        <button class="quick-reply-btn" data-msg="Payment methods">💳 Payment</button>
                    </div>
                </div>
                <div class="chat-input-area">
                    <input type="text" id="chatInput" placeholder="Type a message...">
                    <button id="sendChat" style="background:var(--primary-color, #6366f1); color:white; border:none; border-radius:4px; padding: 0.5rem 1rem; cursor:pointer;">Send</button>
                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', chatHtml);

    const toggle = document.getElementById('chatToggle');
    const windowEl = document.getElementById('chatWindow');
    const close = document.getElementById('closeChat');
    const input = document.getElementById('chatInput');
    const send = document.getElementById('sendChat');
    const messages = document.getElementById('chatMessages');

    toggle.onclick = () => {
        const isHidden = windowEl.classList.toggle('chat-hidden');
        if (!isHidden) {
            input.focus();
        }
    };

    close.onclick = () => {
        windowEl.classList.add('chat-hidden');
    };

    // Quick reply buttons
    document.querySelectorAll('.quick-reply-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            input.value = btn.dataset.msg;
            sendMessage();
            // Hide quick replies after first use
            const qr = document.getElementById('quickReplies');
            if (qr) qr.style.display = 'none';
        });
    });

    // Determine the API base URL
    function getApiBase() {
        // If running from localhost (dev server), use localhost
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            return `http://${window.location.hostname}:9999`;
        }
        // Otherwise use the same origin (for production or mobile)
        return window.location.origin;
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function formatBotMessage(text) {
        // Convert markdown-like formatting to HTML
        let html = escapeHtml(text);
        // Bold: **text**
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        // Bullet points: • text
        html = html.replace(/^• (.+)$/gm, '<span style="display:block; padding-left:0.5rem;">• $1</span>');
        // Numbered lists: 1. text
        html = html.replace(/^(\d+)\. (.+)$/gm, '<span style="display:block; padding-left:0.5rem;">$1. $2</span>');
        // Newlines
        html = html.replace(/\n/g, '<br>');
        return html;
    }

    function addTypingIndicator() {
        const typing = document.createElement('div');
        typing.className = 'chat-bubble bubble-bot typing-indicator';
        typing.id = 'typingIndicator';
        typing.innerHTML = '<span class="dot"></span><span class="dot"></span><span class="dot"></span>';
        messages.appendChild(typing);
        messages.scrollTop = messages.scrollHeight;
    }

    function removeTypingIndicator() {
        const indicator = document.getElementById('typingIndicator');
        if (indicator) indicator.remove();
    }

    async function sendMessage() {
        const text = input.value.trim();
        if (!text) return;

        // Hide quick replies
        const qr = document.getElementById('quickReplies');
        if (qr) qr.style.display = 'none';

        // Add user message
        messages.insertAdjacentHTML('beforeend', `<div class="chat-bubble bubble-user">${escapeHtml(text)}</div>`);
        input.value = '';
        input.disabled = true;
        send.disabled = true;
        messages.scrollTop = messages.scrollHeight;

        // Show typing indicator
        addTypingIndicator();

        try {
            // Get user ID from localStorage if logged in
            const user = JSON.parse(localStorage.getItem('user') || 'null');
            const userId = user ? user.id : null;

            const response = await fetch(`${getApiBase()}/api/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text, user_id: userId })
            });

            const data = await response.json();

            removeTypingIndicator();

            if (response.ok) {
                const formattedResponse = formatBotMessage(data.response);
                messages.insertAdjacentHTML('beforeend', `<div class="chat-bubble bubble-bot">${formattedResponse}</div>`);
            } else {
                messages.insertAdjacentHTML('beforeend', `<div class="chat-bubble bubble-bot">Sorry, something went wrong. Please try again or visit our <a href="support.html" style="color: #818cf8;">Support page</a>.</div>`);
            }
        } catch (err) {
            removeTypingIndicator();
            // Fallback to local responses if server is unreachable
            const fallbackResponse = getLocalFallback(text);
            messages.insertAdjacentHTML('beforeend', `<div class="chat-bubble bubble-bot">${formatBotMessage(fallbackResponse)}</div>`);
        }

        input.disabled = false;
        send.disabled = false;
        input.focus();
        messages.scrollTop = messages.scrollHeight;
    }

    // Local fallback if backend is down
    function getLocalFallback(msg) {
        const lower = msg.toLowerCase();
        if (lower.match(/hi|hello|hey|kumusta/)) return "Hello! 👋 Welcome to Autoride! How can I help you today?";
        if (lower.match(/book|rent|reserve/)) return "📋 To book: Browse vehicles → Select dates → Choose location → Checkout!";
        if (lower.match(/price|rate|cost|magkano/)) return "💰 Rates start at ₱1,500/day for cars. Check each vehicle page for exact pricing.";
        if (lower.match(/payment|pay|gcash/)) return "💳 We accept Credit Cards, GCash, Maya, Bank Transfer, and Cash.";
        if (lower.match(/cancel|refund/)) return "🔄 Free cancellation 48+ hours before pickup. Visit Dashboard → My Bookings.";
        if (lower.match(/thank|thanks|salamat/)) return "You're welcome! 😊 Happy to help!";
        return "I'm having trouble connecting to the server right now. Please try again later or visit our Support page for help!";
    }

    send.onclick = sendMessage;
    input.onkeypress = (e) => { if (e.key === 'Enter') sendMessage(); };

    // Inject CSS
    const style = document.createElement('style');
    style.textContent = `
        /* Floating Widget Container */
        .chat-widget {
            position: fixed !important;
            bottom: 30px !important;
            right: 30px !important;
            z-index: 10000 !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: flex-end !important;
            font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
        }

        /* Toggle Button */
        .chat-button {
            width: 60px !important;
            height: 60px !important;
            border-radius: 50% !important;
            background: #6366f1 !important;
            color: white !important;
            border: none !important;
            cursor: pointer !important;
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4) !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }

        .chat-button:hover {
            transform: scale(1.1) rotate(5deg) !important;
            background: #4f46e5 !important;
        }

        /* Chat Window */
        .chat-window {
            position: absolute !important;
            bottom: 80px !important;
            right: 0 !important;
            width: 380px !important;
            height: 550px !important;
            max-height: calc(100vh - 120px) !important;
            background: #0f172a !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 16px !important;
            display: flex !important;
            flex-direction: column !important;
            overflow: hidden !important;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5) !important;
            animation: chatSlideUp 0.3s ease-out !important;
        }

        .chat-window.chat-hidden {
            display: none !important;
        }

        @keyframes chatSlideUp {
            from { transform: translateY(20px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }

        /* Header */
        .chat-header {
            padding: 16px 20px !important;
            background: #1e293b !important;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
            display: flex !important;
            justify-content: space-between !important;
            align-items: center !important;
            color: white !important;
            flex-shrink: 0 !important;
        }

        /* Message Area */
        .chat-messages {
            flex: 1 !important;
            padding: 20px !important;
            overflow-y: auto !important;
            display: flex !important;
            flex-direction: column !important;
            gap: 12px !important;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important;
        }

        /* Scrollbar */
        .chat-messages::-webkit-scrollbar { width: 5px !important; }
        .chat-messages::-webkit-scrollbar-track { background: transparent !important; }
        .chat-messages::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1) !important; border-radius: 10px !important; }

        /* Bubbles */
        .chat-bubble {
            max-width: 85% !important;
            padding: 12px 16px !important;
            border-radius: 14px !important;
            font-size: 0.95rem !important;
            line-height: 1.5 !important;
            position: relative !important;
            margin-bottom: 4px !important;
        }

        .bubble-bot {
            background: #1e293b !important;
            color: #e2e8f0 !important;
            align-self: flex-start !important;
            border: 1px solid rgba(255,255,255,0.05) !important;
            border-top-left-radius: 4px !important;
        }

        .bubble-user {
            background: #6366f1 !important;
            color: white !important;
            align-self: flex-end !important;
            border-top-right-radius: 4px !important;
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2) !important;
        }

        /* Input Area */
        .chat-input-area {
            padding: 16px !important;
            background: #1e293b !important;
            border-top: 1px solid rgba(255, 255, 255, 0.05) !important;
            display: flex !important;
            gap: 10px !important;
            flex-shrink: 0 !important;
        }

        #chatInput {
            flex: 1 !important;
            background: #0f172a !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 8px !important;
            padding: 10px 14px !important;
            color: white !important;
            font-size: 0.9rem !important;
            outline: none !important;
            transition: border-color 0.2s !important;
        }

        #chatInput:focus {
            border-color: #6366f1 !important;
        }

        #sendChat {
            transition: all 0.2s !important;
            padding: 0.5rem 1.25rem !important;
        }

        #sendChat:hover {
            transform: translateY(-1px) !important;
            filter: brightness(1.1) !important;
        }

        .chat-quick-replies {
            display: flex !important;
            flex-wrap: wrap !important;
            gap: 6px !important;
            padding: 4px 0 !important;
            margin-top: 4px !important;
        }
        .quick-reply-btn {
            background: rgba(99, 102, 241, 0.1) !important;
            border: 1px solid rgba(99, 102, 241, 0.3) !important;
            color: #c7d2fe !important;
            padding: 6px 12px !important;
            border-radius: 16px !important;
            font-size: 0.8rem !important;
            cursor: pointer !important;
            transition: all 0.2s ease !important;
        }
        .quick-reply-btn:hover {
            background: rgba(99, 102, 241, 0.3) !important;
            border-color: #6366f1 !important;
            transform: translateY(-1px) !important;
        }

        @media (max-width: 480px) {
            .chat-window {
                width: calc(100vw - 40px) !important;
                right: -10px !important;
                bottom: 70px !important;
                height: 450px !important;
            }
            .chat-widget {
                bottom: 20px !important;
                right: 20px !important;
            }
        }
    `;
    document.head.appendChild(style);

}

// Auto-init when script is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initChat);
} else {
    initChat();
}
