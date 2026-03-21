#!/usr/bin/env python3
"""Extract quotes with proper source references."""
import re
import json
from pathlib import Path
from collections import defaultdict

VEDABASE_PATH = Path("/Users/jaganat/.emacs.d/git_projects/vedabase/vedabase_gold_dia.md")
OUTPUT_PATH = Path("/Users/jaganat/.emacs.d/git_projects/amrtavani/quotes_with_refs.json")

MIN_WORDS = 10
MAX_WORDS = 55

SKIP_PATTERNS = [
    r'^={10,}', r'^#{1,6}\s', r'^\*\*[A-Z]+\*\*$',
    r'^TEXT\s+\d+', r'^TEXTS\s+\d+', r'^TRANSLATION$', r'^PURPORT$', r'^SYNONYMS$',
    r'^\d+\.\s*$', r'^[a-z]{2,}—', r'^Table of Contents', r'^Contents$',
    r'^His Divine Grace', r'^A\.C\. Bhaktivedanta', r'^Founder-', r'^Macmillan',
    r'^Chapter\s', r'^Canto\s',
]

# Word to number mapping
WORD_TO_NUM = {
    'one': '1', 'two': '2', 'three': '3', 'four': '4', 'five': '5',
    'six': '6', 'seven': '7', 'eight': '8', 'nine': '9', 'ten': '10',
    'eleven': '11', 'twelve': '12', 'thirteen': '13', 'fourteen': '14',
    'fifteen': '15', 'sixteen': '16', 'seventeen': '17', 'eighteen': '18',
    'nineteen': '19', 'twenty': '20', 'twenty-one': '21', 'twenty-two': '22',
    'twenty-three': '23', 'twenty-four': '24', 'twenty-five': '25',
    'twenty-six': '26', 'twenty-seven': '27', 'twenty-eight': '28',
    'twenty-nine': '29', 'thirty': '30', 'thirty-one': '31', 'thirty-two': '32',
    'thirty-three': '33', 'thirty-four': '34', 'thirty-five': '35',
    'thirty-six': '36', 'thirty-seven': '37', 'thirty-eight': '38',
    'thirty-nine': '39', 'forty': '40',
}

def word_to_number(word):
    """Convert word number to digit."""
    return WORD_TO_NUM.get(word.lower().strip(), None)

def is_good_quote(sentence):
    words = sentence.split()
    if len(words) < MIN_WORDS or len(words) > MAX_WORDS:
        return False
    if sentence[0].islower():
        return False
    for pattern in SKIP_PATTERNS:
        if re.match(pattern, sentence, re.I):
            return False
    # Too much Sanskrit
    if sentence.count('ā') + sentence.count('ī') + sentence.count('ū') > len(words) // 3:
        return False
    # Questions are less quotable
    if sentence.strip().endswith('?'):
        return False
    # Must end with punctuation
    if not sentence.rstrip()[-1] in '.!"':
        return False
    # Skip word-for-word synonyms (pattern: *word*-meaning; *word*-meaning;)
    # These have multiple "*word*-" patterns
    synonym_pattern = r'\*[a-zA-Zāīūṛṣṭḍṅñḥṁśṇḷ-]+\*-'
    if len(re.findall(synonym_pattern, sentence)) >= 3:
        return False
    # Also skip if starts with asterisk (synonym entry)
    if sentence.startswith('*') and '-' in sentence[:50]:
        return False
    return True

def categorize(text):
    t = text.lower()
    if any(w in t for w in ['krsna consciousness', 'kṛṣṇa consciousness']):
        return 'krsna-consciousness'
    if any(w in t for w in ['chant', 'hare krsna', 'hare kṛṣṇa', 'holy name']):
        return 'chanting'
    if any(w in t for w in ['devotee', 'devotional service', 'bhakti']):
        return 'bhakti'
    if any(w in t for w in ['guru', 'spiritual master']):
        return 'guru'
    if any(w in t for w in ['material', 'māyā', 'maya', 'illusion']):
        return 'maya'
    if any(w in t for w in ['knowledge', 'ignorance', 'understand']):
        return 'knowledge'
    if any(w in t for w in ['death', 'birth', 'soul', 'transmigration']):
        return 'soul'
    if any(w in t for w in ['god', 'supreme', 'absolute', 'lord']):
        return 'god'
    return 'general'

def extract():
    print(f"Reading {VEDABASE_PATH}...")
    content = VEDABASE_PATH.read_text(encoding='utf-8')
    lines = content.split('\n')
    print(f"Total lines: {len(lines):,}")

    # State tracking
    current_book = ""
    current_canto = ""  # For SB: "1", "2", etc.
    current_chapter = ""  # For SB: "1", For BG: "18"
    current_verse = ""
    current_section = ""  # PURPORT, TRANSLATION, etc.
    in_sb_content = False  # Are we in SB actual content (not TOC)
    in_bg_content = False

    quotes = []
    seen = set()
    paragraph = []

    for i, line in enumerate(lines):
        line = line.strip()

        # Detect Bhagavad-gita chapter from "Bg X:" pattern (TOC or content)
        bg_match = re.match(r'^Bg\s+(\d+):', line)
        if bg_match:
            current_book = "Bhagavad-gita"
            current_chapter = bg_match.group(1)
            current_canto = ""
            current_verse = ""
            current_section = ""
            in_bg_content = True
            in_sb_content = False
            continue

        # Detect SB canto from "Canto X:" pattern
        canto_match = re.match(r'^Canto\s+(\d+):', line, re.I)
        if canto_match:
            current_book = "Srimad-Bhagavatam"
            current_canto = canto_match.group(1)
            current_chapter = ""
            current_verse = ""
            in_sb_content = True
            in_bg_content = False
            continue

        # Detect chapter number from "Chapter One", "Chapter Thirteen" etc.
        chapter_word_match = re.match(r'^Chapter\s+([A-Za-z-]+)\s*$', line, re.I)
        if chapter_word_match:
            word = chapter_word_match.group(1)
            num = word_to_number(word)
            if num:
                current_chapter = num
                current_verse = ""
                current_section = ""
            continue

        # Also handle "Chapter 1", "Chapter 18" numeric format
        chapter_num_match = re.match(r'^Chapter\s+(\d+)', line, re.I)
        if chapter_num_match:
            current_chapter = chapter_num_match.group(1)
            current_verse = ""
            current_section = ""
            continue

        # Detect "First Canto", "Tenth Canto" etc. in section headers
        canto_word_match = re.search(r'(First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth|Ninth|Tenth|Eleventh|Twelfth)\s+Canto', line, re.I)
        if canto_word_match:
            canto_words = {
                'first': '1', 'second': '2', 'third': '3', 'fourth': '4', 'fifth': '5',
                'sixth': '6', 'seventh': '7', 'eighth': '8', 'ninth': '9', 'tenth': '10',
                'eleventh': '11', 'twelfth': '12'
            }
            current_canto = canto_words.get(canto_word_match.group(1).lower(), current_canto)
            current_book = "Srimad-Bhagavatam"
            in_sb_content = True

        # Detect verse number
        text_match = re.match(r'^TEXT\s+(\d+)', line)
        if text_match:
            current_verse = text_match.group(1)
            current_section = ""
            continue

        texts_match = re.match(r'^TEXTS\s+(\d+[-–]\d+)', line)
        if texts_match:
            current_verse = texts_match.group(1)
            current_section = ""
            continue

        # Detect section
        if line == "PURPORT":
            current_section = "Purport"
            continue
        elif line == "TRANSLATION":
            current_section = "Translation"
            continue

        # Build reference string
        ref = ""
        if current_book == "Bhagavad-gita" and current_chapter and current_verse:
            ref = f"Bhagavad-gita {current_chapter}.{current_verse}"
            if current_section:
                ref += f", {current_section}"
        elif current_book == "Srimad-Bhagavatam" and current_canto and current_chapter and current_verse:
            ref = f"Srimad-Bhagavatam {current_canto}.{current_chapter}.{current_verse}"
            if current_section:
                ref += f", {current_section}"

        # Process paragraphs
        if not line or line.startswith('#') or line.startswith('='):
            if paragraph and ref:  # Only save if we have a proper reference
                text = ' '.join(paragraph)
                sentences = re.split(r'(?<=[.!])\s+', text)

                for sentence in sentences:
                    sentence = sentence.strip()
                    if sentence and is_good_quote(sentence):
                        normalized = re.sub(r'\s+', ' ', sentence.lower())
                        if normalized not in seen:
                            seen.add(normalized)
                            quotes.append({
                                'quote': sentence,
                                'source': "Srila Prabhupada",
                                'reference': ref,
                                'category': categorize(sentence),
                            })
                paragraph = []
            elif paragraph:
                paragraph = []
            continue

        paragraph.append(line)

        if i % 200000 == 0:
            print(f"  Line {i:,}, quotes: {len(quotes):,}")

    # Add IDs
    for idx, q in enumerate(quotes):
        q['id'] = idx + 1

    print(f"\nExtracted {len(quotes):,} quotes with proper references")

    # Stats by book
    by_book = defaultdict(int)
    for q in quotes:
        if 'Bhagavad-gita' in q['reference']:
            by_book['Bhagavad-gita'] += 1
        elif 'Srimad-Bhagavatam' in q['reference']:
            # Count by canto
            m = re.search(r'Srimad-Bhagavatam (\d+)\.', q['reference'])
            if m:
                by_book[f"SB Canto {m.group(1)}"] += 1

    print("\nBy source:")
    for src, cnt in sorted(by_book.items()):
        print(f"  {src}: {cnt:,}")

    # Save
    OUTPUT_PATH.write_text(json.dumps(quotes, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"\nSaved to {OUTPUT_PATH}")

    # Show samples
    import random
    print("\n--- Samples ---")
    for q in random.sample(quotes[:5000], min(5, len(quotes))):
        print(f"\n\"{q['quote'][:80]}...\"")
        print(f"  — {q['reference']}")

    return quotes

if __name__ == '__main__':
    extract()
