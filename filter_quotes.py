#!/usr/bin/env python3
"""Filter and curate the best quotes from the full extraction."""
import json
import re
import random
from pathlib import Path

INPUT_PATH = Path("/Users/jaganat/.emacs.d/git_projects/amrtavani/quotes_full.json")
OUTPUT_PATH = Path("/Users/jaganat/.emacs.d/git_projects/amrtavani/quotes_100k.json")
FINAL_PATH = Path("/Users/jaganat/.emacs.d/git_projects/amrtavani/quotes.json")

# Patterns to exclude (not real quotes)
EXCLUDE_PATTERNS = [
    r'^Bg\s+\d+',  # Chapter references
    r'^SB\s+\d+',
    r'^CC\s+',
    r'^Chapter\s+\d+',
    r'^Canto\s+\d+',
    r'^Part\s+\d+',
    r'^Volume\s+\d+',
    r'^Founder-',
    r'^Macmillan',
    r'^His Divine Grace',
    r'^A\.C\. Bhaktivedanta',
    r'^\*[A-Z]',  # *Bold headers*
    r'^The following',
    r'^In this chapter',
    r'^This chapter',
    r'^As stated in',
    r'^As mentioned',
    r'^As explained',
    r'^The word\s+\*?[a-z]',  # Word definitions
    r'^\([A-Z][a-z]+\)',  # (Sanskrit) definitions
    r'^[A-Z][a-z]+—',  # Word—definition
    r'^See also',
    r'^Cf\.',
    r'^Note:',
    r'^N\.B\.',
    r'^\d{6}',  # Date codes
    r'^Letter to',
    r'^Conversation with',
    r'^Morning Walk',
    r'^Room Conversation',
    r'^Lecture',
    r'^Interview',
]

# Good quote indicators (prefer these)
GOOD_INDICATORS = [
    r'\bKṛṣṇa\b',
    r'\bKrsna\b',
    r'\bGod\b',
    r'\bdevotee\b',
    r'\bspiritual\b',
    r'\bconsciousness\b',
    r'\bsoul\b',
    r'\blove\b',
    r'\bservice\b',
    r'\bchant\b',
    r'\bhappiness\b',
    r'\bbliss\b',
    r'\btruth\b',
    r'\beternal\b',
    r'\bmaterial\b',
    r'\bsurrender\b',
    r'\bdevotional\b',
]

def is_good_quote(q):
    """Check if quote is worth keeping."""
    text = q['quote']

    # Exclude patterns
    for pattern in EXCLUDE_PATTERNS:
        if re.match(pattern, text, re.I):
            return False

    # Must end with proper punctuation
    if not text.rstrip().endswith(('.', '!', '"', '"')):
        return False

    # Should have at least some good indicators
    score = sum(1 for p in GOOD_INDICATORS if re.search(p, text, re.I))

    # Must have at least one good word or be reasonably long
    words = text.split()
    if score == 0 and len(words) < 15:
        return False

    # Avoid quotes that are mostly Sanskrit
    sanskrit_chars = sum(1 for c in text if c in 'āīūṛṝḷḹṃḥṅñṭḍṇśṣ')
    if sanskrit_chars > len(text) * 0.15:
        return False

    # Avoid quotes with too many parentheses (definitions)
    if text.count('(') > 2:
        return False

    # Avoid verse numbers in the middle
    if re.search(r'\(\d+\.\d+\)', text):
        return False

    return True

def score_quote(q):
    """Score a quote for quality/memorability."""
    text = q['quote']
    score = 0

    # Good length (not too short, not too long)
    words = len(text.split())
    if 15 <= words <= 40:
        score += 10
    elif 10 <= words <= 50:
        score += 5

    # Contains key concepts
    score += sum(2 for p in GOOD_INDICATORS if re.search(p, text, re.I))

    # Starts with strong statement
    if re.match(r'^(The|This|One|Every|All|We|A person|Human|Real|True|Without|By)\b', text):
        score += 3

    # Contains universal truth indicators
    if re.search(r'\b(always|never|everyone|must|should|cannot|only)\b', text, re.I):
        score += 2

    # Categorical statements are memorable
    if re.search(r'\b(is the|are the|means|is called|is known)\b', text, re.I):
        score += 2

    # Penalize if it references specific context too much
    if re.search(r'\b(Arjuna|Mahārāja|King|this verse|here|therefore)\b', text, re.I):
        score -= 2

    return score

def main():
    print(f"Loading {INPUT_PATH}...")
    with open(INPUT_PATH, 'r', encoding='utf-8') as f:
        quotes = json.load(f)

    print(f"Total quotes: {len(quotes):,}")

    # Filter
    print("Filtering...")
    good_quotes = [q for q in quotes if is_good_quote(q)]
    print(f"After filtering: {len(good_quotes):,}")

    # Score and sort
    print("Scoring...")
    for q in good_quotes:
        q['score'] = score_quote(q)

    good_quotes.sort(key=lambda x: -x['score'])

    # Take top 100,000
    top_quotes = good_quotes[:100000]
    print(f"Top quotes selected: {len(top_quotes):,}")

    # Shuffle for variety
    random.shuffle(top_quotes)

    # Re-assign IDs
    for i, q in enumerate(top_quotes):
        q['id'] = i + 1
        del q['score']  # Remove score from output

    # Save 100k version
    print(f"Saving {OUTPUT_PATH}...")
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(top_quotes, f, indent=2, ensure_ascii=False)

    # Also create a small version for the site (first 1008)
    site_quotes = top_quotes[:1008]
    for i, q in enumerate(site_quotes):
        q['id'] = i + 1

    print(f"Saving {FINAL_PATH} (1008 quotes for site)...")
    with open(FINAL_PATH, 'w', encoding='utf-8') as f:
        json.dump(site_quotes, f, indent=2, ensure_ascii=False)

    # Stats
    from collections import Counter
    categories = Counter(q['category'] for q in site_quotes)
    print("\nSite quotes by category:")
    for cat, count in categories.most_common():
        print(f"  {cat}: {count}")

    # Show samples
    print("\n--- Sample quotes ---")
    for q in random.sample(site_quotes, 5):
        print(f"\n[{q['category']}] \"{q['quote'][:150]}...\"")
        print(f"  — {q['source']}")

if __name__ == '__main__':
    main()
