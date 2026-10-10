#!/usr/bin/env python3
"""Extract quotable sentences from Vedabase Gold MD."""
import re
import json
from pathlib import Path
from collections import defaultdict

VEDABASE_PATH = Path("/Users/jaganat/.emacs.d/git_projects/vedabase/vedabase_gold_dia.md")
OUTPUT_PATH = Path("/Users/jaganat/.emacs.d/git_projects/amrtavani/quotes_full.json")

# Minimum and maximum words for a good quote
MIN_WORDS = 8
MAX_WORDS = 60

# Patterns to identify sources
SOURCE_PATTERNS = [
    (r'^Bg\s+(\d+\.\d+)', 'Bhagavad-gita'),
    (r'^SB\s+(\d+\.\d+\.\d+)', 'Srimad-Bhagavatam'),
    (r'^CC\s+(Adi|Madhya|Antya)\s+(\d+\.\d+)', 'Caitanya-caritamrta'),
    (r'^KB\s+Chapter\s+(\d+)', 'Krsna Book'),
    (r'^NOD\s+Chapter\s+(\d+)', 'Nectar of Devotion'),
    (r'^NOI\s+(\d+)', 'Nectar of Instruction'),
    (r'^ISO\s+(\d+)', 'Sri Isopanisad'),
    (r'^TLC\s+Chapter\s+(\d+)', 'Teachings of Lord Caitanya'),
    (r'^Lecture.*(\d{6})', 'Lecture'),
    (r'^Conversation.*(\d{6})', 'Conversation'),
    (r'^Letter.*(\d{6})', 'Letter'),
]

# Skip patterns (headers, references, etc.)
SKIP_PATTERNS = [
    r'^={10,}',  # Delimiters
    r'^#{1,6}\s',  # Markdown headers
    r'^\*\*[A-Z]+\*\*$',  # Bold headers
    r'^TEXT\s+\d+',  # Verse numbers
    r'^TEXTS\s+\d+',
    r'^TRANSLATION',
    r'^PURPORT',
    r'^SYNONYMS',
    r'^\d+\.\s*$',  # Just numbers
    r'^[a-z]{2,}—',  # Sanskrit word definitions
]

def is_good_quote(sentence):
    """Check if a sentence makes a good standalone quote."""
    # Too short or too long
    words = sentence.split()
    if len(words) < MIN_WORDS or len(words) > MAX_WORDS:
        return False

    # Starts with lowercase (fragment)
    if sentence[0].islower():
        return False

    # Just a reference or header
    for pattern in SKIP_PATTERNS:
        if re.match(pattern, sentence):
            return False

    # Contains too many Sanskrit words without translation (rough heuristic)
    if sentence.count('ā') + sentence.count('ī') + sentence.count('ū') > len(words) // 2:
        return False

    # Is a question (less quotable usually)
    if sentence.strip().endswith('?'):
        return False

    # Contains incomplete references
    if re.search(r'\(see\s+\w+\s+\d+', sentence, re.I):
        return False

    return True

def extract_source(lines, current_idx):
    """Look backwards to find the source of a quote."""
    source = "Srila Prabhupada"
    source_detail = ""

    # Look back up to 50 lines for source info
    for i in range(max(0, current_idx - 50), current_idx):
        line = lines[i].strip()

        for pattern, source_name in SOURCE_PATTERNS:
            match = re.match(pattern, line)
            if match:
                source = source_name
                source_detail = line[:100]  # First 100 chars as detail
                break

    return source, source_detail

def categorize_quote(quote, source):
    """Assign a category based on content and source."""
    text_lower = quote.lower()

    # Content-based categories
    if any(w in text_lower for w in ['krsna consciousness', 'kṛṣṇa consciousness']):
        return 'krsna-consciousness'
    if any(w in text_lower for w in ['chant', 'hare krsna', 'hare kṛṣṇa', 'holy name']):
        return 'chanting'
    if any(w in text_lower for w in ['devotee', 'devotional service', 'bhakti']):
        return 'bhakti'
    if any(w in text_lower for w in ['guru', 'spiritual master']):
        return 'guru'
    if any(w in text_lower for w in ['material', 'māyā', 'maya', 'illusion']):
        return 'maya'
    if any(w in text_lower for w in ['love of god', 'prema', 'love for krsna']):
        return 'love'
    if any(w in text_lower for w in ['human life', 'human being', 'human form']):
        return 'human-life'
    if any(w in text_lower for w in ['knowledge', 'ignorance', 'understand']):
        return 'knowledge'
    if any(w in text_lower for w in ['death', 'birth', 'transmigration', 'soul']):
        return 'soul'
    if any(w in text_lower for w in ['god', 'supreme', 'absolute']):
        return 'god'

    # Source-based fallback
    if 'Bhagavad-gita' in source:
        return 'gita'
    if 'Bhagavatam' in source:
        return 'bhagavatam'

    return 'general'

def extract_quotes():
    """Main extraction function."""
    print(f"Reading {VEDABASE_PATH}...")
    with open(VEDABASE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    print(f"Total lines: {len(lines):,}")

    quotes = []
    seen = set()  # Avoid duplicates

    # Process line by line
    current_paragraph = []

    for i, line in enumerate(lines):
        line = line.strip()

        # Skip empty lines and headers
        if not line or line.startswith('#') or line.startswith('='):
            # Process accumulated paragraph
            if current_paragraph:
                paragraph = ' '.join(current_paragraph)
                # Split into sentences
                sentences = re.split(r'(?<=[.!])\s+', paragraph)

                for sentence in sentences:
                    sentence = sentence.strip()
                    if sentence and is_good_quote(sentence):
                        # Normalize for dedup
                        normalized = re.sub(r'\s+', ' ', sentence.lower())
                        if normalized not in seen:
                            seen.add(normalized)
                            source, source_detail = extract_source(lines, i)
                            category = categorize_quote(sentence, source)
                            quotes.append({
                                'quote': sentence,
                                'source': source_detail if source_detail else source,
                                'category': category
                            })

                current_paragraph = []
            continue

        # Accumulate paragraph
        current_paragraph.append(line)

        # Progress
        if i % 100000 == 0:
            print(f"  Processed {i:,} lines, found {len(quotes):,} quotes...")

    print(f"\nTotal quotes extracted: {len(quotes):,}")

    # Stats by category
    by_category = defaultdict(int)
    for q in quotes:
        by_category[q['category']] += 1

    print("\nBy category:")
    for cat, count in sorted(by_category.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count:,}")

    # Add IDs
    for i, q in enumerate(quotes):
        q['id'] = i + 1

    # Save
    print(f"\nSaving to {OUTPUT_PATH}...")
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(quotes, f, indent=2, ensure_ascii=False)

    print("Done!")
    return quotes

if __name__ == '__main__':
    quotes = extract_quotes()

    # Show some examples
    print("\n--- Sample quotes ---")
    import random
    for q in random.sample(quotes[:1000], min(5, len(quotes))):
        print(f"\n[{q['category']}] {q['quote'][:100]}...")
        print(f"  — {q['source']}")
