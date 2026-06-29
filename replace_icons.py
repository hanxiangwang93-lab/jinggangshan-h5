with open('D:/ceshi/designs/yanan-redesign/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

icons = {
    # Building/Museum
    '\U0001f3db️': '<svg width="0.8rem" height="0.8rem" viewBox="0 0 24 24"><rect x="4" y="3" width="16" height="18" rx="1" fill="#DAA520" opacity="0.25"/><rect x="4" y="3" width="16" height="5" fill="#C41E3A" opacity="0.3"/><line x1="10" y1="21" x2="10" y2="8" stroke="#DAA520" stroke-width="1.5"/><line x1="14" y1="21" x2="14" y2="8" stroke="#DAA520" stroke-width="1.5"/><circle cx="12" cy="5.5" r="1.5" fill="#DAA520"/></svg>',
}

# Simpler approach: find text nodes with common emoji patterns and replace
import re

replacements = {
    '🏛️': 'dng_building',
    '🧵': 'dng_thread',
    '📖': 'dng_book',
    '🌾': 'dng_wheat',
    '🏠': 'dng_home',
    '🗼': 'dng_tower',
    '⚔️': 'dng_swords',
    '🎯': 'dng_target',
    '💡': 'dng_idea',
    '❤️': 'dng_heart',
    '💪': 'dng_strong',
    '🌟': 'dng_star',
    '📜': 'dng_scroll',
    '🎵': 'dng_music',
    '🎭': 'dng_theater',
    '📚': 'dng_books',
    '🔍': 'dng_search',
    '📦': 'dng_box',
    '📨': 'dng_mail',
    '🏚️': 'dng_oldhouse',
    '🏙️': 'dng_city',
    '📝': 'dng_write',
    '🇨🇳': 'dng_flag',
    '🏅': 'dng_medal',
}

svg_map = {
    'dng_building': '<svg style="width:0.8rem;height:0.8rem" viewBox="0 0 24 24"><rect x="4" y="3" width="16" height="20" rx="1" fill="#DAA520" opacity="0.2"/><rect x="4" y="3" width="16" height="5" fill="#C41E3A" opacity="0.3"/><line x1="10" y1="23" x2="10" y2="8" stroke="#DAA520" stroke-width="1.5"/><line x1="14" y1="23" x2="14" y2="8" stroke="#DAA520" stroke-width="1.5"/><circle cx="12" cy="5.5" r="1.8" fill="#DAA520"/></svg>',
    'dng_thread': '<svg style="width:0.8rem;height:0.8rem" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" fill="none" stroke="#C41E3A" stroke-width="1.5"/><circle cx="12" cy="12" r="5" fill="none" stroke="#DAA520" stroke-width="1.2"/><line x1="12" y1="3" x2="12" y2="7" stroke="#C41E3A" stroke-width="1.5"/><line x1="12" y1="17" x2="12" y2="21" stroke="#C41E3A" stroke-width="1.5"/></svg>',
    'dng_book': '<svg style="width:0.8rem;height:0.8rem" viewBox="0 0 24 24"><path d="M4 3h6l2 3h9v14H4V3z" fill="#C41E3A" opacity="0.2"/><rect x="4" y="3" width="17" height="17" rx="1" fill="none" stroke="#DAA520" stroke-width="1.5"/><line x1="8" y1="10" x2="17" y2="10" stroke="#DAA520" stroke-width="1"/><line x1="8" y1="13" x2="15" y2="13" stroke="#DAA520" stroke-width="0.8"/></svg>',
    'dng_wheat': '<svg style="width:0.8rem;height:0.8rem" viewBox="0 0 24 24"><line x1="12" y1="2" x2="12" y2="22" stroke="#8B4513" stroke-width="2"/><ellipse cx="8" cy="6" rx="4" ry="6" fill="#DAA520" opacity="0.5" transform="rotate(-20 8 6)"/><ellipse cx="16" cy="8" rx="4" ry="6" fill="#C41E3A" opacity="0.4" transform="rotate(20 16 8)"/><circle cx="12" cy="3" r="1.5" fill="#DAA520"/></svg>',
    'dng_home': '<svg style="width:0.8rem;height:0.8rem" viewBox="0 0 24 24"><path d="M3 12L12 3l9 9" fill="none" stroke="#DAA520" stroke-width="1.8"/><rect x="6" y="10" width="12" height="12" fill="#C41E3A" opacity="0.1" stroke="#DAA520" stroke-width="1.2"/><rect x="10" y="16" width="4" height="6" fill="#DAA520" opacity="0.2"/></svg>',
    'dng_tower': '<svg style="width:0.8rem;height:0.8rem" viewBox="0 0 24 24"><rect x="10" y="3" width="4" height="19" fill="#8B4513" opacity="0.4"/><rect x="8" y="5" width="8" height="3" fill="#DAA520" opacity="0.5"/><rect x="9" y="10" width="6" height="2" fill="#DAA520" opacity="0.4"/><rect x="9" y="14" width="6" height="2" fill="#DAA520" opacity="0.3"/><polygon points="12,1 7,5 17,5" fill="#C41E3A"/></svg>',
    'dng_swords': '<svg style="width:0.8rem;height:0.8rem" viewBox="0 0 24 24"><line x1="4" y1="4" x2="15" y2="15" stroke="#DAA520" stroke-width="2"/><line x1="20" y1="4" x2="9" y2="15" stroke="#DAA520" stroke-width="2"/><circle cx="4" cy="4" r="2.5" fill="#C41E3A"/><circle cx="20" cy="4" r="2.5" fill="#C41E3A"/></svg>',
    'dng_target': '<svg style="width:0.8rem;height:0.8rem" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" fill="none" stroke="#C41E3A" stroke-width="1.2"/><circle cx="12" cy="12" r="7" fill="none" stroke="#DAA520" stroke-width="1.2"/><circle cx="12" cy="12" r="3" fill="#C41E3A" opacity="0.5"/><circle cx="12" cy="12" r="1" fill="#DAA520"/></svg>',
    'dng_idea': '<svg style="width:0.8rem;height:0.8rem" viewBox="0 0 24 24"><circle cx="12" cy="9" r="6" fill="#DAA520" opacity="0.25" stroke="#DAA520" stroke-width="1.2"/><rect x="10" y="15" width="4" height="2" rx="0.5" fill="#C41E3A"/><rect x="9" y="17" width="6" height="1.5" rx="0.5" fill="#8B4513"/></svg>',
    'dng_heart': '<svg style="width:0.8rem;height:0.8rem" viewBox="0 0 24 24"><path d="M12 21l-1.45-1.3C5.4 15.36 2 12.27 2 8.5 2 5.4 4.4 3 7.5 3c1.74 0 3.41.81 4.5 2.08C13.09 3.81 14.76 3 16.5 3 19.6 3 22 5.4 22 8.5c0 3.77-3.4 6.86-8.55 11.2L12 21z" fill="#C41E3A" opacity="0.7"/></svg>',
    'dng_strong': '<svg style="width:0.8rem;height:0.8rem" viewBox="0 0 24 24"><path d="M6 9v7a3 3 0 003 3h1a3 3 0 003-3V7a2 2 0 012 2v9" fill="none" stroke="#C41E3A" stroke-width="2"/><line x1="16" y1="8" x2="16" y2="18" stroke="#DAA520" stroke-width="2.5" stroke-linecap="round"/></svg>',
    'dng_star': '<svg style="width:0.8rem;height:0.8rem" viewBox="0 0 24 24"><polygon points="12,2 15,9 22,9 16.5,14 18.5,21 12,17 5.5,21 7.5,14 2,9 9,9" fill="#DAA520"/></svg>',
    'dng_scroll': '<svg style="width:0.8rem;height:0.8rem" viewBox="0 0 24 24"><rect x="4" y="3" width="16" height="18" rx="1" fill="#faf0e0" stroke="#DAA520" stroke-width="1.2"/><rect x="4" y="3" width="16" height="4" fill="#C41E3A" opacity="0.2"/><line x1="7" y1="10" x2="17" y2="10" stroke="#8B4513" stroke-width="0.8"/><line x1="7" y1="13" x2="14" y2="13" stroke="#8B4513" stroke-width="0.8"/></svg>',
    'dng_music': '<svg style="width:0.8rem;height:0.8rem" viewBox="0 0 24 24"><circle cx="7" cy="18" r="3" fill="none" stroke="#C41E3A" stroke-width="1.5"/><circle cx="17" cy="15" r="3" fill="none" stroke="#DAA520" stroke-width="1.5"/><line x1="10" y1="18" x2="10" y2="4" stroke="#C41E3A" stroke-width="1.8"/><line x1="20" y1="15" x2="20" y2="6" stroke="#DAA520" stroke-width="1.8"/></svg>',
    'dng_theater': '<svg style="width:0.8rem;height:0.8rem" viewBox="0 0 24 24"><circle cx="8" cy="12" r="6" fill="none" stroke="#C41E3A" stroke-width="1.3"/><circle cx="16" cy="12" r="6" fill="none" stroke="#DAA520" stroke-width="1.3"/><circle cx="7" cy="11" r="1.3" fill="#C41E3A"/><circle cx="15" cy="11" r="1.3" fill="#DAA520"/></svg>',
    'dng_books': '<svg style="width:0.8rem;height:0.8rem" viewBox="0 0 24 24"><rect x="4" y="4" width="7" height="16" rx="0.8" fill="#C41E3A" opacity="0.2" stroke="#DAA520" stroke-width="1.2"/><rect x="13" y="6" width="7" height="14" rx="0.8" fill="#DAA520" opacity="0.2" stroke="#C41E3A" stroke-width="1.2"/></svg>',
    'dng_search': '<svg style="width:0.8rem;height:0.8rem" viewBox="0 0 24 24"><circle cx="10" cy="10" r="7" fill="none" stroke="#DAA520" stroke-width="2"/><line x1="15" y1="15" x2="21" y2="21" stroke="#DAA520" stroke-width="2.5" stroke-linecap="round"/></svg>',
    'dng_box': '<svg style="width:0.8rem;height:0.8rem" viewBox="0 0 24 24"><rect x="4" y="7" width="16" height="14" rx="1.5" fill="#DAA520" opacity="0.15" stroke="#DAA520" stroke-width="1.5"/><line x1="4" y1="7" x2="12" y2="13" stroke="#DAA520" stroke-width="1.2"/><line x1="20" y1="7" x2="12" y2="13" stroke="#DAA520" stroke-width="1.2"/></svg>',
    'dng_mail': '<svg style="width:0.8rem;height:0.8rem" viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="14" rx="1.5" fill="#faf0e0" stroke="#C41E3A" stroke-width="1.3"/><path d="M3 5l9 8 9-8" fill="none" stroke="#C41E3A" stroke-width="1.3"/></svg>',
    'dng_oldhouse': '<svg style="width:0.8rem;height:0.8rem" viewBox="0 0 24 24"><path d="M4 15l8-12 8 12" fill="none" stroke="#8B4513" stroke-width="1.8"/><rect x="7" y="13" width="10" height="9" fill="#C41E3A" opacity="0.12" stroke="#8B4513" stroke-width="1"/><rect x="10" y="17" width="4" height="5" fill="#DAA520" opacity="0.25"/></svg>',
    'dng_city': '<svg style="width:0.8rem;height:0.8rem" viewBox="0 0 24 24"><rect x="3" y="9" width="5" height="13" fill="#DAA520" opacity="0.2" stroke="#DAA520" stroke-width="1"/><rect x="10" y="5" width="5" height="17" fill="#C41E3A" opacity="0.15" stroke="#DAA520" stroke-width="1"/><rect x="17" y="11" width="4" height="11" fill="#DAA520" opacity="0.18" stroke="#DAA520" stroke-width="1"/></svg>',
    'dng_write': '<svg style="width:0.8rem;height:0.8rem" viewBox="0 0 24 24"><path d="M12 19l7-7 3 3-7 7-3-3z" fill="#C41E3A" opacity="0.15"/><path d="M5 19l1-3 2 2z" fill="#DAA520" opacity="0.4"/><line x1="18" y1="6" x2="6" y2="18" stroke="#DAA520" stroke-width="1.5"/></svg>',
    'dng_flag': '<svg style="width:0.8rem;height:0.8rem" viewBox="0 0 24 24"><rect width="24" height="24" rx="2" fill="#C41E3A"/><polygon points="12,3 13.8,8.5 19.5,8.5 15,12 16.5,17 12,13.5 7.5,17 9,12 4.5,8.5 10.2,8.5" fill="#DAA520"/></svg>',
    'dng_medal': '<svg style="width:0.8rem;height:0.8rem" viewBox="0 0 24 24"><circle cx="12" cy="10" r="8" fill="none" stroke="#DAA520" stroke-width="1.5"/><polygon points="12,4 14,8 18,8 15,11.5 16.5,16 12,13 7.5,16 9,11.5 6,8 10,8" fill="#C41E3A" opacity="0.7"/></svg>',
}

count = 0
for emoji, placeholder in replacements.items():
    if emoji in html:
        html = html.replace(emoji, svg_map[placeholder])
        count += 1

with open('D:/ceshi/designs/yanan-redesign/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f'Replaced {count} emoji types with SVG icons')
print(f'File size: {len(html)} bytes')
