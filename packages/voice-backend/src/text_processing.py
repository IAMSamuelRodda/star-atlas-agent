"""
Text preprocessing for TTS.

Converts text elements that TTS can't pronounce properly into speakable equivalents:
- Roman numerals → English words (III → three)
- Future: symbols, abbreviations, etc.
"""

import re

# Roman numeral to integer mapping
ROMAN_VALUES = {
    'I': 1, 'V': 5, 'X': 10, 'L': 50,
    'C': 100, 'D': 500, 'M': 1000
}

# Pre-computed English words for numbers 1-3999
ONES = ['', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine']
TENS = ['', '', 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety']
TEENS = ['ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen',
         'sixteen', 'seventeen', 'eighteen', 'nineteen']


def roman_to_int(s: str) -> int | None:
    """
    Convert Roman numeral string to integer.

    Returns None if invalid Roman numeral.
    """
    s = s.upper()

    # Validate characters
    if not all(c in ROMAN_VALUES for c in s):
        return None

    if not s:
        return None

    total = 0
    prev_value = 0

    for char in reversed(s):
        value = ROMAN_VALUES[char]
        if value < prev_value:
            total -= value
        else:
            total += value
        prev_value = value

    # Validate by converting back (catches invalid sequences like IIII)
    if int_to_roman(total) != s.upper():
        return None

    return total


def int_to_roman(num: int) -> str:
    """Convert integer to Roman numeral string."""
    if num <= 0 or num > 3999:
        return ""

    result = []
    values = [
        (1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'),
        (100, 'C'), (90, 'XC'), (50, 'L'), (40, 'XL'),
        (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')
    ]

    for value, numeral in values:
        while num >= value:
            result.append(numeral)
            num -= value

    return ''.join(result)


def int_to_words(n: int) -> str:
    """
    Convert integer to English words.

    Handles 1-3999 (Roman numeral range).
    """
    if n <= 0 or n > 3999:
        return str(n)

    if n < 10:
        return ONES[n]

    if n < 20:
        return TEENS[n - 10]

    if n < 100:
        tens, ones = divmod(n, 10)
        if ones:
            return f"{TENS[tens]} {ONES[ones]}"
        return TENS[tens]

    if n < 1000:
        hundreds, remainder = divmod(n, 100)
        if remainder:
            return f"{ONES[hundreds]} hundred {int_to_words(remainder)}"
        return f"{ONES[hundreds]} hundred"

    # 1000-3999
    thousands, remainder = divmod(n, 1000)
    if remainder:
        return f"{ONES[thousands]} thousand {int_to_words(remainder)}"
    return f"{ONES[thousands]} thousand"


def roman_to_words(roman: str) -> str | None:
    """
    Convert Roman numeral to English words.

    Returns None if not a valid Roman numeral.

    Examples:
        III → three
        IV → four
        XLII → forty two
        MCMLXXXIV → one thousand nine hundred eighty four
    """
    num = roman_to_int(roman)
    if num is None:
        return None
    return int_to_words(num)


# Pattern to match Roman numerals
#
# Key insight for single "I":
# - Pronoun "I" is never directly preceded by a proper noun
# - "Calico I", "Apollo I", "Enterprise I" → Roman numeral (one)
# - "I am", "I think" → Pronoun (eye)
#
# Rules:
# 1. Proper noun + I/V/X = Roman numeral (Calico I, Mark V, Class X)
# 2. Multi-char uppercase IVXLCDM = Roman numeral (III, IV, VIII)
# 3. Standalone I with lowercase after = Pronoun (I am, I think)

# Proper noun followed by single Roman numeral, capturing what follows
# Groups: (1) proper noun, (2) Roman numeral, (3) next word or empty
PROPER_NOUN_ROMAN_PATTERN = re.compile(
    r'\b([A-Z][a-z]+)\s+([IVXLCDM])\b(?:\s+(\S+))?'
)

# Common English words that get capitalized but aren't proper nouns (names)
# If the word before "I" is in this set → the "I" is likely pronoun, not numeral
COMMON_WORDS = {
    # Adjectives (Yoda-speak: "Strong I am")
    'hungry', 'strong', 'ready', 'foolish', 'wise', 'brave', 'afraid', 'sorry',
    'happy', 'sad', 'angry', 'tired', 'sure', 'certain', 'glad', 'proud',
    # Modal verbs (questions: "Can I help?")
    'can', 'could', 'will', 'would', 'shall', 'should', 'may', 'might', 'must',
    # Auxiliary verbs
    'do', 'does', 'did', 'have', 'has', 'had', 'am', 'is', 'are', 'was', 'were',
    # Question words
    'what', 'where', 'when', 'who', 'whom', 'whose', 'which', 'why', 'how',
    # Other common sentence starters
    'if', 'but', 'and', 'or', 'so', 'yet', 'now', 'then', 'here', 'there',
    'before', 'after', 'once', 'while', 'since', 'until', 'unless', 'although',
    'because', 'whether', 'however', 'therefore', 'otherwise', 'maybe', 'perhaps',
}

# First-person verb patterns - verbs that follow pronoun "I", not Roman numeral
# If "I" is followed by these → it's the pronoun performing an action
FIRST_PERSON_ONLY_VERBS = {
    # Be/have (first person forms)
    'am', "'m", 'have', "'ve", "'ll", "'d",
    # Action verbs (speaker does these) - "Emily I know", "Adelaide I have seen"
    'know', 'knew', 'see', 'saw', 'seen', 'love', 'loved', 'hate', 'hated',
    'want', 'wanted', 'need', 'needed', 'like', 'liked', 'fear', 'feared',
    'think', 'thought', 'believe', 'believed', 'feel', 'felt', 'hear', 'heard',
    'remember', 'forgot', 'understand', 'understood', 'trust', 'trusted',
    'miss', 'missed', 'seek', 'sought', 'find', 'found', 'tell', 'told',
    'do', 'did', 'go', 'went', 'come', 'came', 'bring', 'brought',
    'give', 'gave', 'take', 'took', 'make', 'made', 'say', 'said',
    # Negation patterns (Yoda: "Emily I know not")
    'know', 'care', 'wish', 'dare',
}

# Standalone Roman numerals (2+ chars, all uppercase only)
ROMAN_STANDALONE_PATTERN = re.compile(
    r'\b([IVXLCDM]{2,})\b'
    # Note: no IGNORECASE - must be uppercase
)


def preprocess_for_tts(text: str) -> str:
    """
    Preprocess text for TTS synthesis.

    Converts elements that TTS can't pronounce into speakable equivalents:
    - Roman numerals → English words

    Args:
        text: Input text

    Returns:
        Text with Roman numerals converted to words

    Examples:
        "Calico I is a ship" → "Calico one is a ship"
        "Apollo I launched" → "Apollo one launched"
        "Super Bowl LVIII" → "Super Bowl fifty eight"
        "I am here" → "I am here" (pronoun preserved)
    """
    def replace_standalone_roman(match):
        original = match.group(1)
        words = roman_to_words(original)
        if words:
            return words
        return original

    def replace_proper_noun_roman(match):
        proper_noun = match.group(1)
        numeral = match.group(2)
        next_word = match.group(3)  # May be None

        # Rule 1: If preceding word is common English → it's pronoun
        # Handles: "Can I help", "Hungry I am", "Strong I have become"
        if proper_noun.lower() in COMMON_WORDS:
            return match.group(0)

        # Rule 2: If followed by first-person-only verb → it's pronoun
        # Handles: edge cases where unknown words precede "I am"
        if next_word:
            next_clean = next_word.lower().rstrip('.,!?;:')
            if next_clean in FIRST_PERSON_ONLY_VERBS:
                return match.group(0)

        # Otherwise: proper noun + Roman numeral → convert
        # Handles: "Calico I is", "Apollo I was", "Enterprise I"
        words = roman_to_words(numeral)
        if words:
            if next_word:
                return f"{proper_noun} {words} {next_word}"
            return f"{proper_noun} {words}"
        return match.group(0)

    # First pass: proper noun + single Roman numeral (e.g., "Calico I", "Apollo V")
    result = PROPER_NOUN_ROMAN_PATTERN.sub(replace_proper_noun_roman, text)

    # Second pass: standalone multi-char uppercase Roman numerals (III, IV, VIII)
    result = ROMAN_STANDALONE_PATTERN.sub(replace_standalone_roman, result)

    return result


# Quick test
if __name__ == "__main__":
    test_cases = [
        # Proper noun + Roman numeral → convert
        ("Calico I is a ship", "Calico one is a ship"),
        ("Apollo I launched in 1967", "Apollo one launched in 1967"),
        ("The Mark V armor is cool", "The Mark five armor is cool"),
        ("Class X materials", "Class ten materials"),

        # Multi-char Roman numerals → convert
        ("Super Bowl LVIII", "Super Bowl fifty eight"),
        ("Rocky III and Rocky IV", "Rocky three and Rocky four"),
        ("The year MCMLXXXIV", "The year one thousand nine hundred eighty four"),
        ("World War II ended", "World War two ended"),
        ("Episode IV: A New Hope", "Episode four: A New Hope"),
        ("Henry VIII was king", "Henry eight was king"),

        # Mixed: pronoun I + proper noun Roman
        ("I love the Calico I", "I love the Calico one"),
        ("I think Apollo I was great", "I think Apollo one was great"),

        # Pronoun I → preserve (normal sentences)
        ("I am going to the store", "I am going to the store"),
        ("I think therefore I am", "I think therefore I am"),
        ("Can I help you?", "Can I help you?"),

        # Yoda-speak / inverted sentences → preserve pronoun I
        ("Hungry I am", "Hungry I am"),
        ("Strong I have become", "Strong I have become"),
        ("Ready I will be", "Ready I will be"),
        ("Foolish I was", "Foolish I was"),

        # Inverted with proper nouns (names/places) → preserve pronoun I
        ("Emily I know not", "Emily I know not"),
        ("Adelaide I have seen", "Adelaide I have seen"),
        ("London I love", "London I love"),
        ("Marcus I trust", "Marcus I trust"),

        # Words with Roman chars → preserve
        ("Mix of ingredients", "Mix of ingredients"),
        ("The movie Liv and Maddie", "The movie Liv and Maddie"),
        ("I love to live", "I love to live"),
    ]

    print("Roman Numeral → Words Conversion")
    print("=" * 50)

    passed = 0
    failed = 0

    for text, expected in test_cases:
        result = preprocess_for_tts(text)
        status = "✓" if result == expected else "✗"
        if result == expected:
            passed += 1
        else:
            failed += 1
        print(f"{status} IN:  {text}")
        print(f"  OUT: {result}")
        if result != expected:
            print(f"  EXP: {expected}")
        print()

    print(f"Results: {passed} passed, {failed} failed")
