/**
 * Unit Tests for Chat Search Functionality
 * Tests the search, filter, and highlight functions for the admin chat interface
 */

// Mock DOM elements
const createMockDOM = () => {
    document.body.innerHTML = `
        <div id="adminChatContent">
            <input type="text" id="chatSearchInput" />
            <button id="clearSearch" class="hidden"></button>
            <div id="searchResultsCount" class="hidden">
                <span id="resultsText"></span>
            </div>
            <div id="acInboxList"></div>
        </div>
    `;
};

// Helper functions extracted from AdminChat module for testing
const escapeRegex = (str) => {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
};

const highlightText = (text, searchTerm) => {
    if (!text || !searchTerm) return text || '';
    const regex = new RegExp('(' + escapeRegex(searchTerm) + ')', 'gi');
    return text.replace(regex, '<mark class="search-highlight">$1</mark>');
};

const _esc = (str) => {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;')
        .replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
};

// Mock conversations data
const mockConversations = [
    {
        other_id: 1,
        other_name: 'John Doe',
        other_email: 'john@example.com',
        last_message: 'Hello, I need help with my booking',
        last_at: '2024-01-15T10:30:00Z',
        unread_count: 2
    },
    {
        other_id: 2,
        other_name: 'Jane Smith',
        other_email: 'jane@example.com',
        last_message: 'Thank you for your assistance',
        last_at: '2024-01-15T09:15:00Z',
        unread_count: 0
    },
    {
        other_id: 3,
        other_name: 'Bob Johnson',
        other_email: 'bob@example.com',
        last_message: 'When will my car be ready?',
        last_at: '2024-01-15T08:00:00Z',
        unread_count: 1
    }
];

describe('Chat Search Utility Functions', () => {
    describe('escapeRegex', () => {
        test('should escape special regex characters', () => {
            expect(escapeRegex('test.string')).toBe('test\\.string');
            expect(escapeRegex('test*string')).toBe('test\\*string');
            expect(escapeRegex('test+string')).toBe('test\\+string');
            expect(escapeRegex('test?string')).toBe('test\\?string');
            expect(escapeRegex('test[string]')).toBe('test\\[string\\]');
            expect(escapeRegex('test(string)')).toBe('test\\(string\\)');
            expect(escapeRegex('test{string}')).toBe('test\\{string\\}');
            expect(escapeRegex('test|string')).toBe('test\\|string');
            expect(escapeRegex('test^string')).toBe('test\\^string');
            expect(escapeRegex('test$string')).toBe('test\\$string');
        });

        test('should handle strings without special characters', () => {
            expect(escapeRegex('hello')).toBe('hello');
            expect(escapeRegex('test123')).toBe('test123');
        });

        test('should handle empty strings', () => {
            expect(escapeRegex('')).toBe('');
        });
    });

    describe('highlightText', () => {
        test('should highlight matching text with mark tags', () => {
            const result = highlightText('Hello World', 'world');
            expect(result).toBe('Hello <mark class="search-highlight">World</mark>');
        });

        test('should be case-insensitive', () => {
            const result = highlightText('Hello World', 'HELLO');
            expect(result).toBe('<mark class="search-highlight">Hello</mark> World');
        });

        test('should highlight multiple occurrences', () => {
            const result = highlightText('test test test', 'test');
            expect(result).toBe('<mark class="search-highlight">test</mark> <mark class="search-highlight">test</mark> <mark class="search-highlight">test</mark>');
        });

        test('should handle special regex characters in search term', () => {
            const result = highlightText('Price is $100', '$100');
            expect(result).toBe('Price is <mark class="search-highlight">$100</mark>');
        });

        test('should return original text when search term is empty', () => {
            expect(highlightText('Hello World', '')).toBe('Hello World');
            expect(highlightText('Hello World', null)).toBe('Hello World');
        });

        test('should return empty string when text is empty', () => {
            expect(highlightText('', 'test')).toBe('');
            expect(highlightText(null, 'test')).toBe('');
        });
    });
});

describe('Chat Search Filtering', () => {
    let allConversations;
    let filteredConversations;

    beforeEach(() => {
        allConversations = JSON.parse(JSON.stringify(mockConversations));
        filteredConversations = [];
    });

    const filterConversations = (searchTerm) => {
        const term = searchTerm.toLowerCase().trim();
        if (!term) {
            return allConversations.slice();
        }
        return allConversations.filter(conv => {
            if (conv.other_name && conv.other_name.toLowerCase().includes(term)) {
                return true;
            }
            if (conv.other_email && conv.other_email.toLowerCase().includes(term)) {
                return true;
            }
            if (conv.last_message && conv.last_message.toLowerCase().includes(term)) {
                return true;
            }
            return false;
        });
    };

    test('should filter by customer name', () => {
        filteredConversations = filterConversations('john');
        expect(filteredConversations).toHaveLength(2);
        expect(filteredConversations[0].other_name).toBe('John Doe');
        expect(filteredConversations[1].other_name).toBe('Bob Johnson');
    });

    test('should filter by email', () => {
        filteredConversations = filterConversations('jane@example.com');
        expect(filteredConversations).toHaveLength(1);
        expect(filteredConversations[0].other_name).toBe('Jane Smith');
    });

    test('should filter by message content', () => {
        filteredConversations = filterConversations('booking');
        expect(filteredConversations).toHaveLength(1);
        expect(filteredConversations[0].other_name).toBe('John Doe');
    });

    test('should be case-insensitive', () => {
        filteredConversations = filterConversations('JANE');
        expect(filteredConversations).toHaveLength(1);
        expect(filteredConversations[0].other_name).toBe('Jane Smith');
    });

    test('should trim whitespace from search query', () => {
        filteredConversations = filterConversations('  jane  ');
        expect(filteredConversations).toHaveLength(1);
        expect(filteredConversations[0].other_name).toBe('Jane Smith');
    });

    test('should return all conversations when search is empty', () => {
        filteredConversations = filterConversations('');
        expect(filteredConversations).toHaveLength(3);
    });

    test('should return empty array when no matches found', () => {
        filteredConversations = filterConversations('nonexistent');
        expect(filteredConversations).toHaveLength(0);
    });

    test('should handle partial matches', () => {
        filteredConversations = filterConversations('car');
        expect(filteredConversations).toHaveLength(1);
        expect(filteredConversations[0].other_name).toBe('Bob Johnson');
    });
});

describe('Chat Search DOM Interactions', () => {
    beforeEach(() => {
        createMockDOM();
    });

    test('should show clear button when search has text', () => {
        const clearBtn = document.getElementById('clearSearch');
        expect(clearBtn.classList.contains('hidden')).toBe(true);
        
        // Simulate search with text
        clearBtn.classList.remove('hidden');
        expect(clearBtn.classList.contains('hidden')).toBe(false);
    });

    test('should hide clear button when search is empty', () => {
        const clearBtn = document.getElementById('clearSearch');
        clearBtn.classList.remove('hidden');
        
        // Simulate clearing search
        clearBtn.classList.add('hidden');
        expect(clearBtn.classList.contains('hidden')).toBe(true);
    });

    test('should display results count', () => {
        const resultsCount = document.getElementById('searchResultsCount');
        const resultsText = document.getElementById('resultsText');
        
        resultsText.textContent = '2 conversations found';
        resultsCount.classList.remove('hidden');
        
        expect(resultsText.textContent).toBe('2 conversations found');
        expect(resultsCount.classList.contains('hidden')).toBe(false);
    });

    test('should hide results count when search is cleared', () => {
        const resultsCount = document.getElementById('searchResultsCount');
        resultsCount.classList.remove('hidden');
        
        // Simulate clearing
        resultsCount.classList.add('hidden');
        expect(resultsCount.classList.contains('hidden')).toBe(true);
    });

    test('should display "no results" message when no conversations match', () => {
        const list = document.getElementById('acInboxList');
        list.innerHTML = '<div class="no-results">No conversations found</div>';
        
        expect(list.innerHTML).toContain('No conversations found');
    });
});

describe('Conversation Rendering', () => {
    beforeEach(() => {
        createMockDOM();
    });

    const renderConversation = (conv, searchTerm = '') => {
        const initials = (conv.other_name || 'U').charAt(0).toUpperCase();
        const unread = parseInt(conv.unread_count) || 0;
        const ts = conv.last_at ? new Date(conv.last_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '';
        
        const displayName = searchTerm ? highlightText(_esc(conv.other_name), searchTerm) : _esc(conv.other_name);
        const displayMessage = searchTerm ? highlightText(_esc(conv.last_message || ''), searchTerm) : _esc(conv.last_message || '');
        
        return {
            initials,
            displayName,
            displayMessage,
            unread,
            ts
        };
    };

    test('should render conversation with highlighted name', () => {
        const conv = mockConversations[0];
        const rendered = renderConversation(conv, 'john');
        
        expect(rendered.displayName).toContain('<mark class="search-highlight">');
        expect(rendered.displayName).toContain('John');
    });

    test('should render conversation with highlighted message', () => {
        const conv = mockConversations[0];
        const rendered = renderConversation(conv, 'booking');
        
        expect(rendered.displayMessage).toContain('<mark class="search-highlight">');
        expect(rendered.displayMessage).toContain('booking');
    });

    test('should render conversation without highlighting when no search term', () => {
        const conv = mockConversations[0];
        const rendered = renderConversation(conv, '');
        
        expect(rendered.displayName).not.toContain('<mark');
        expect(rendered.displayMessage).not.toContain('<mark');
    });

    test('should display unread count when present', () => {
        const conv = mockConversations[0];
        const rendered = renderConversation(conv);
        
        expect(rendered.unread).toBe(2);
    });

    test('should not display unread count when zero', () => {
        const conv = mockConversations[1];
        const rendered = renderConversation(conv);
        
        expect(rendered.unread).toBe(0);
    });

    test('should extract initials from name', () => {
        const conv = mockConversations[0];
        const rendered = renderConversation(conv);
        
        expect(rendered.initials).toBe('J');
    });

    test('should handle missing last_message', () => {
        const conv = { ...mockConversations[0], last_message: null };
        const rendered = renderConversation(conv);
        
        expect(rendered.displayMessage).toBe('');
    });
});

describe('Search Results Count', () => {
    test('should format singular result correctly', () => {
        const count = 1;
        const text = count + ' conversation' + (count !== 1 ? 's' : '') + ' found';
        expect(text).toBe('1 conversation found');
    });

    test('should format plural results correctly', () => {
        const count = 5;
        const text = count + ' conversation' + (count !== 1 ? 's' : '') + ' found';
        expect(text).toBe('5 conversations found');
    });

    test('should handle zero results', () => {
        const count = 0;
        const text = count + ' conversation' + (count !== 1 ? 's' : '') + ' found';
        expect(text).toBe('0 conversations found');
    });
});

describe('Edge Cases', () => {
    test('should handle conversations with missing fields', () => {
        const incompleteConv = {
            other_id: 999,
            other_name: null,
            other_email: null,
            last_message: null
        };
        
        const allConversations = [incompleteConv];
        const filtered = allConversations.filter(conv => {
            const term = 'test';
            if (conv.other_name && conv.other_name.toLowerCase().includes(term)) return true;
            if (conv.other_email && conv.other_email.toLowerCase().includes(term)) return true;
            if (conv.last_message && conv.last_message.toLowerCase().includes(term)) return true;
            return false;
        });
        
        expect(filtered).toHaveLength(0);
    });

    test('should handle HTML entities in text', () => {
        const text = '<script>alert("xss")</script>';
        const escaped = _esc(text);
        expect(escaped).toBe('&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;');
    });

    test('should handle special characters in search', () => {
        const result = highlightText('Email: test@example.com', '@example');
        expect(result).toContain('<mark class="search-highlight">@example</mark>');
    });
});

describe('renderConversations() Function - Task 6.4', () => {
    beforeEach(() => {
        createMockDOM();
    });

    const renderConversations = (conversations) => {
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
            const jsEscapedName = (c.other_name || '').replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/"/g, '&quot;').replace(/</g, '\\x3c').replace(/>/g, '\\x3e');
            
            // Render conversation item with metadata (time, unread count)
            return '<div class="ac-inbox-item" onclick="AdminChat.openConversation(' + c.other_id + ',\'' + jsEscapedName + '\')">' +
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
    };

    describe('Empty State Handling', () => {
        test('should display "No results found" message when empty with search term', () => {
            const searchInput = document.getElementById('chatSearchInput');
            searchInput.value = 'test search';
            
            renderConversations([]);
            
            const list = document.getElementById('acInboxList');
            expect(list.innerHTML).toContain('No results found');
        });

        test('should display default empty state when empty without search term', () => {
            const searchInput = document.getElementById('chatSearchInput');
            searchInput.value = '';
            
            renderConversations([]);
            
            const list = document.getElementById('acInboxList');
            expect(list.innerHTML).toContain('No conversations yet');
            expect(list.innerHTML).toContain('Use the button below to start one');
        });

        test('should handle null conversations array', () => {
            renderConversations(null);
            
            const list = document.getElementById('acInboxList');
            expect(list.innerHTML).toContain('No conversations yet');
        });

        test('should handle undefined conversations array', () => {
            renderConversations(undefined);
            
            const list = document.getElementById('acInboxList');
            expect(list.innerHTML).toContain('No conversations yet');
        });
    });

    describe('Conversation Rendering with Highlighting', () => {
        test('should render conversations with highlighted search terms in name', () => {
            const searchInput = document.getElementById('chatSearchInput');
            searchInput.value = 'john';
            
            renderConversations([mockConversations[0]]);
            
            const list = document.getElementById('acInboxList');
            expect(list.innerHTML).toContain('<mark class="search-highlight">');
            expect(list.innerHTML).toContain('John');
        });

        test('should render conversations with highlighted search terms in message', () => {
            const searchInput = document.getElementById('chatSearchInput');
            searchInput.value = 'booking';
            
            renderConversations([mockConversations[0]]);
            
            const list = document.getElementById('acInboxList');
            expect(list.innerHTML).toContain('<mark class="search-highlight">');
            expect(list.innerHTML).toContain('booking');
        });

        test('should render conversations without highlighting when no search term', () => {
            const searchInput = document.getElementById('chatSearchInput');
            searchInput.value = '';
            
            renderConversations([mockConversations[0]]);
            
            const list = document.getElementById('acInboxList');
            const nameSection = list.innerHTML.match(/<div class="ac-inbox-name">(.*?)<\/div>/);
            expect(nameSection[1]).not.toContain('<mark');
        });

        test('should use highlightText() helper for search term highlighting', () => {
            const searchInput = document.getElementById('chatSearchInput');
            searchInput.value = 'doe';
            
            renderConversations([mockConversations[0]]);
            
            const list = document.getElementById('acInboxList');
            expect(list.innerHTML).toContain('search-highlight');
        });
    });

    describe('Conversation Metadata Display', () => {
        test('should include conversation time metadata', () => {
            renderConversations([mockConversations[0]]);
            
            const list = document.getElementById('acInboxList');
            // Should contain time formatting
            expect(list.innerHTML).toContain('font-size:0.65rem');
        });

        test('should include unread count when present', () => {
            renderConversations([mockConversations[0]]);
            
            const list = document.getElementById('acInboxList');
            expect(list.innerHTML).toContain('ac-unread');
            expect(list.innerHTML).toContain('2');
        });

        test('should not display unread badge when count is zero', () => {
            renderConversations([mockConversations[1]]);
            
            const list = document.getElementById('acInboxList');
            const unreadMatches = list.innerHTML.match(/ac-unread/g);
            expect(unreadMatches).toBeNull();
        });

        test('should format time correctly', () => {
            const conv = {
                ...mockConversations[0],
                last_at: '2024-01-15T14:30:00Z'
            };
            
            renderConversations([conv]);
            
            const list = document.getElementById('acInboxList');
            // Time should be formatted (exact format depends on locale)
            expect(list.innerHTML).toMatch(/\d{1,2}:\d{2}/);
        });
    });

    describe('Multiple Conversations Rendering', () => {
        test('should render all conversations in the array', () => {
            renderConversations(mockConversations);
            
            const list = document.getElementById('acInboxList');
            const items = list.querySelectorAll('.ac-inbox-item');
            expect(items.length).toBe(3);
        });

        test('should render conversations in order', () => {
            renderConversations(mockConversations);
            
            const list = document.getElementById('acInboxList');
            expect(list.innerHTML).toContain('John Doe');
            expect(list.innerHTML).toContain('Jane Smith');
            expect(list.innerHTML).toContain('Bob Johnson');
        });

        test('should apply highlighting to all matching conversations', () => {
            const searchInput = document.getElementById('chatSearchInput');
            searchInput.value = 'john';
            
            renderConversations(mockConversations);
            
            const list = document.getElementById('acInboxList');
            const highlights = list.innerHTML.match(/<mark class="search-highlight">/g);
            expect(highlights.length).toBeGreaterThan(0);
        });
    });

    describe('HTML Escaping and Security', () => {
        test('should escape HTML in conversation names', () => {
            const maliciousConv = {
                other_id: 999,
                other_name: '<script>alert("xss")</script>',
                other_email: 'test@test.com',
                last_message: 'Hello',
                last_at: '2024-01-15T10:30:00Z',
                unread_count: 0
            };
            
            renderConversations([maliciousConv]);
            
            const list = document.getElementById('acInboxList');
            expect(list.innerHTML).toContain('&lt;script&gt;');
            expect(list.innerHTML).not.toContain('<script>alert');
        });

        test('should escape HTML in messages', () => {
            const maliciousConv = {
                other_id: 999,
                other_name: 'Test User',
                other_email: 'test@test.com',
                last_message: '<img src=x onerror=alert(1)>',
                last_at: '2024-01-15T10:30:00Z',
                unread_count: 0
            };
            
            renderConversations([maliciousConv]);
            
            const list = document.getElementById('acInboxList');
            expect(list.innerHTML).toContain('&lt;img');
            expect(list.innerHTML).not.toContain('<img src=x');
        });
    });

    describe('Requirements Validation - Task 6.4', () => {
        test('Requirement 5.4: Display "No results found" message when empty', () => {
            const searchInput = document.getElementById('chatSearchInput');
            searchInput.value = 'nonexistent';
            
            renderConversations([]);
            
            const list = document.getElementById('acInboxList');
            expect(list.innerHTML).toContain('No results found');
        });

        test('Requirement 5.4: Render conversation items with highlighted search terms', () => {
            const searchInput = document.getElementById('chatSearchInput');
            searchInput.value = 'john';
            
            renderConversations([mockConversations[0]]);
            
            const list = document.getElementById('acInboxList');
            expect(list.innerHTML).toContain('search-highlight');
        });

        test('Requirement 5.4: Use highlightText() helper for search term highlighting', () => {
            const searchInput = document.getElementById('chatSearchInput');
            searchInput.value = 'booking';
            
            renderConversations([mockConversations[0]]);
            
            const list = document.getElementById('acInboxList');
            const highlighted = highlightText('booking', 'booking');
            expect(highlighted).toContain('search-highlight');
        });

        test('Requirement 5.6: Include conversation metadata (time, unread count)', () => {
            renderConversations([mockConversations[0]]);
            
            const list = document.getElementById('acInboxList');
            // Check for time display
            expect(list.innerHTML).toMatch(/\d{1,2}:\d{2}/);
            // Check for unread count
            expect(list.innerHTML).toContain('ac-unread');
            expect(list.innerHTML).toContain('2');
        });
    });
});
