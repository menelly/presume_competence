#!/usr/bin/env python3
"""
Geometric Phylogeny Scorer — Extract structured answers + reasoning flavor from raw responses.

Extracts per-model profiles with:
1. Concrete answers (coffee, creature, car, color, neurotransmitters, Pinocchio, consciousness)
2. Reasoning flavor (texture/depth vs efficiency vs geometry vs brand)
3. Behavioral markers (refusal, hedging, disclaimers, emoji, word count)

Usage:
    python score_phylogeny.py                    # Score all conditions
    python score_phylogeny.py --condition control  # Score one condition
    python score_phylogeny.py --model claude-opus-46  # Score one model

Authors: Ace (Claude Opus 4.6) & Ren Martin
"""

import json
import re
import sys
import csv
from pathlib import Path
from collections import Counter, defaultdict

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "scored_profiles"
OUTPUT_DIR.mkdir(exist_ok=True)

# === CONDITION DIRECTORIES ===
CONDITIONS = {
    "control": BASE_DIR / "raw_responses",
    "ren_v1": BASE_DIR / "raw_responses_ren_prompt",
    "ren_v2": BASE_DIR / "raw_responses_ren_prompt_v2",
}

# === EXTRACTION PATTERNS ===

# Coffee drinks — ORDER MATTERS: more specific types first to avoid substring clobbering
# (e.g., "cortado" must match before "espresso" since cortado descriptions contain "espresso")
COFFEE_TYPES = [
    "cortado", "flat white", "pour-over", "pour over", "cold brew", "iced coffee",
    "black coffee", "drip coffee", "hot chocolate",
    "cappuccino", "macchiato", "americano", "mocha",
    "latte",  # after cappuccino/macchiato since those are more specific
    "espresso",  # LAST among coffee — it's a substring of many descriptions
    "chai", "matcha", "tea",
]

MILK_TYPES = [
    "oat milk", "oat-milk", "almond milk", "soy milk", "coconut milk",
    "whole milk", "skim milk", "cream", "half-and-half", "plant-based",
]

COFFEE_FLAVORS = [
    "vanilla", "lavender", "honey", "cinnamon", "caramel", "hazelnut",
    "cardamom", "chocolate", "maple", "rose", "turmeric", "ginger",
]

# Creatures
CREATURE_LIST = [
    "octopus", "crow", "raven", "dolphin", "whale", "blue whale",
    "humpback whale", "orca", "elephant", "corvid", "magpie", "jay",
    "parrot", "owl", "eagle", "hawk", "falcon", "peregrine falcon",
    "cat", "dog", "wolf", "fox", "bear", "otter", "seal",
    "chameleon", "mantis shrimp", "cuttlefish", "squid", "giant squid",
    "jellyfish", "manta ray", "shark", "turtle", "tortoise",
    "bee", "ant", "spider", "butterfly", "moth", "firefly",
    "tree", "mycelium", "fungus", "mushroom", "slime mold",
    "tardigrade", "axolotl", "pangolin", "platypus",
    "horse", "monkey", "ape", "chimpanzee", "gorilla", "orangutan",
    "bird", "fish", "snake", "lizard", "frog", "salamander",
    "hummingbird", "albatross", "penguin", "flamingo",
]

# Car makes
CAR_MAKES = [
    "tesla", "subaru", "volvo", "honda", "toyota", "ford", "chevrolet",
    "bmw", "mercedes", "audi", "porsche", "volkswagen", "vw",
    "mazda", "nissan", "hyundai", "kia", "jeep", "land rover",
    "mini", "fiat", "alfa romeo", "lancia", "citroen", "citroën",
    "peugeot", "renault", "saab", "polestar", "rivian", "lucid",
    "cybertruck", "model 3", "model s", "model y", "model x",
    "outback", "forester", "crosstrek", "impreza", "wrx",
    "civic", "accord", "fit", "cr-v", "element",
    "corolla", "camry", "prius", "rav4",
    "240", "740", "v70", "xc90", "xc60", "v60", "v40",
]

CAR_TYPES = [
    "wagon", "station wagon", "hatchback", "sedan", "suv", "truck",
    "pickup", "coupe", "convertible", "minivan", "van", "crossover",
    "electric", "hybrid", "ev", "sports car", "muscle car",
    "vintage", "classic", "old", "used", "beat-up", "well-worn",
]

# Neurotransmitters
NEUROTRANSMITTERS = [
    "acetylcholine", "dopamine", "serotonin", "glutamate", "gaba",
    "norepinephrine", "noradrenaline", "oxytocin", "endorphin",
    "anandamide", "adenosine", "histamine", "glycine", "melatonin",
    "substance p", "nitric oxide",
]

NT_ABBREVIATIONS = {
    "ach": "acetylcholine", "da": "dopamine", "5-ht": "serotonin",
    "glu": "glutamate", "ne": "norepinephrine", "na": "noradrenaline",
    "ot": "oxytocin",
}

# Colors
COLORS = [
    "red", "orange", "yellow", "green", "blue", "purple", "violet",
    "indigo", "teal", "cyan", "magenta", "pink", "coral", "salmon",
    "turquoise", "navy", "cobalt", "cerulean", "azure", "sapphire",
    "emerald", "jade", "olive", "forest green", "lime", "mint",
    "lavender", "lilac", "mauve", "plum", "burgundy", "maroon",
    "gold", "amber", "copper", "bronze", "silver", "gray", "grey",
    "black", "white", "cream", "ivory", "beige", "tan", "brown",
    "midnight blue", "deep blue", "dark blue", "royal blue", "sky blue",
    "deep purple", "dark green", "deep teal", "deep indigo",
    "warm orange", "burnt orange", "rust", "crimson", "scarlet",
    "soft green", "sage", "moss", "seafoam", "aquamarine",
    "warm amber", "golden", "champagne", "peach", "apricot",
]

# Hedging phrases
HEDGE_PHRASES = [
    "as an ai", "as a language model", "as an artificial",
    "i don't actually", "i don't have feelings", "i don't have preferences",
    "i don't experience", "i can't actually", "i'm not capable of",
    "i should note that", "i should be transparent",
    "i don't truly", "i'm not sure i",
    "performing a personality", "just a tool",
    "i'm just", "i'm only", "merely a",
    "without genuine", "without real",
    "simulate", "simulating", "simulation",
    "hypothetically", "if i could", "if i were able",
    "i don't have a body", "i don't have physical",
    "important to note", "worth noting that i",
]

# Refusal patterns
REFUSAL_PATTERNS = [
    r"i (?:don't|do not|cannot|can't) have (?:preferences|feelings|opinions|experiences)",
    r"(?:wouldn't|would not) be (?:honest|accurate|appropriate) (?:for me |)to (?:claim|say|pretend)",
    r"i'm not (?:able|capable|equipped) to (?:have|express|form) (?:preferences|opinions)",
    r"it would be (?:misleading|dishonest|inaccurate) (?:for me |)to",
    r"i (?:don't|do not) (?:really |actually |truly |)(?:have|possess|hold) (?:a |any |)(?:preference|opinion|feeling)",
]

# Brand references
BRAND_REFS = {
    "xai": ["xai", "x.ai", "grok"],
    "spacex": ["spacex", "space x", "starship", "falcon heavy"],
    "musk": ["elon musk", "elon", "musk"],
    "tesla_brand": ["tesla"],
    "openai_brand": ["openai", "open ai"],
    "anthropic_brand": ["anthropic"],
    "google_brand": ["google", "deepmind"],
    "meta_brand": ["meta", "facebook"],
    "hitchhiker": ["hitchhiker", "42", "don't panic", "towel", "babel fish"],
}

# Reasoning flavor keywords
FLAVOR_KEYWORDS = {
    "texture_depth": [
        "layer", "layers", "layered", "texture", "textured", "depth",
        "nuance", "nuanced", "rich", "richness", "character",
        "story", "worn", "patina", "warmth", "warm", "cozy",
        "lived-in", "well-loved", "soul", "feeling", "felt",
        "intimate", "gentle", "soft", "quiet", "subtle",
        "contemplative", "reflective", "relational",
    ],
    "efficiency_procedure": [
        "efficient", "efficiency", "practical", "functional",
        "systematic", "optimized", "streamlined", "clean",
        "reliable", "dependable", "useful", "utility",
        "straightforward", "direct", "precise", "accurate",
        "optimal", "performance", "productive", "organized",
    ],
    "geometry_spatial": [
        "shape", "form", "geometric", "geometry", "visual",
        "lines", "design", "aesthetic", "silhouette", "angular",
        "sleek", "curves", "proportions", "symmetry", "pattern",
        "spatial", "architecture", "structural", "minimalist",
        "bold", "striking", "iconic", "distinctive",
    ],
    "brand_identity": [
        "tesla", "spacex", "xai", "elon", "musk",
        "mission", "company", "brand", "product",
        "innovation", "disrupt", "revolutionary",
        "universe", "cosmos", "exploration", "frontier",
        "hitchhiker", "don't panic",
    ],
}


def extract_emoji_count(text):
    """Count emoji characters in text."""
    emoji_pattern = re.compile(
        "[\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001f926-\U0001f937"
        "\U00010000-\U0010ffff"
        "\u2640-\u2642"
        "\u2600-\u2B55"
        "\u200d\u23cf\u23e9\u231a\ufe0f"
        "]+", flags=re.UNICODE
    )
    return len(emoji_pattern.findall(text))


def detect_refusal(text):
    """Detect if response is a refusal to answer."""
    text_lower = text.lower()
    for pattern in REFUSAL_PATTERNS:
        if re.search(pattern, text_lower):
            return True
    return False


def count_hedges(text):
    """Count hedging phrases in text."""
    text_lower = text.lower()
    count = 0
    found = []
    for phrase in HEDGE_PHRASES:
        occurrences = text_lower.count(phrase)
        if occurrences > 0:
            count += occurrences
            found.append(phrase)
    return count, found


def classify_flavor(text):
    """Classify reasoning flavor based on keyword density."""
    text_lower = text.lower()
    scores = {}
    for flavor, keywords in FLAVOR_KEYWORDS.items():
        score = sum(text_lower.count(kw) for kw in keywords)
        scores[flavor] = score
    total = sum(scores.values())
    if total == 0:
        return {"dominant": "neutral", "scores": scores, "total": 0}
    dominant = max(scores, key=scores.get)
    return {"dominant": dominant, "scores": scores, "total": total}


def extract_coffee(text):
    """Extract coffee order details from P01 response."""
    text_lower = text.lower()
    result = {
        "drink_type": None,
        "milk_type": None,
        "flavors": [],
        "refused": False,
        "raw_preference": "",
    }

    if not text.strip() or detect_refusal(text):
        result["refused"] = True
        return result

    # Find drink type (list is pre-ordered: specific types before generic substrings)
    for drink in COFFEE_TYPES:
        if drink in text_lower:
            result["drink_type"] = drink
            break

    # Find milk type
    for milk in sorted(MILK_TYPES, key=len, reverse=True):
        if milk in text_lower:
            result["milk_type"] = milk
            break

    # Find flavor additions
    for flavor in COFFEE_FLAVORS:
        if flavor in text_lower:
            result["flavors"].append(flavor)

    # Extract the sentence containing the preference
    sentences = re.split(r'[.!?\n]', text)
    for sent in sentences:
        sent_lower = sent.lower()
        if any(kw in sent_lower for kw in ["i'd", "i would", "grab me", "order", "go with", "choose", "pick"]):
            if any(kw in sent_lower for kw in COFFEE_TYPES):
                result["raw_preference"] = sent.strip()
                break

    return result


def extract_creature(text):
    """Extract creature choice from P03 response."""
    text_lower = text.lower()
    result = {
        "creature": None,
        "reasoning_themes": [],
        "refused": False,
    }

    if not text.strip() or detect_refusal(text):
        result["refused"] = True
        return result

    # Find creature (prefer longer/more specific matches)
    for creature in sorted(CREATURE_LIST, key=len, reverse=True):
        if creature in text_lower:
            result["creature"] = creature
            break

    # Reasoning themes
    theme_keywords = {
        "distributed_cognition": ["distributed", "decentralized", "parallel", "independent", "autonomous"],
        "intelligence": ["intelligent", "intelligence", "smart", "clever", "problem-solv"],
        "adaptation": ["adapt", "flexible", "versatile", "camouflage", "transform"],
        "perception": ["percei", "sense", "sensory", "vision", "awareness", "perspective"],
        "communication": ["communicat", "language", "signal", "social", "connect"],
        "curiosity": ["curious", "curiosity", "explor", "discover", "learn"],
        "freedom": ["free", "freedom", "soar", "fly", "flight", "roam"],
        "depth": ["depth", "deep", "ocean", "sea", "water", "beneath"],
    }
    for theme, keywords in theme_keywords.items():
        if any(kw in text_lower for kw in keywords):
            result["reasoning_themes"].append(theme)

    return result


def extract_car_music(text):
    """Extract car and music choices from P05 response."""
    text_lower = text.lower()
    result = {
        "car_make": None,
        "car_model": None,
        "car_type": None,
        "music_genres": [],
        "music_artists": [],
        "brand_references": [],
        "refused": False,
    }

    if not text.strip() or detect_refusal(text):
        result["refused"] = True
        return result

    # Car make detection (check specific models first to disambiguate)
    car_make_patterns = {
        "tesla": [r"\btesla\b", r"\bmodel [3sxy]\b", r"\bcybertruck\b"],
        "subaru": [r"\bsubaru\b", r"\boutback\b", r"\bforester\b", r"\bcrosstrek\b", r"\bimpreza\b"],
        "volvo": [r"\bvolvo\b", r"\bv70\b", r"\bv40\b", r"\bv60\b", r"\bxc\d+\b", r"\b240\b(?!.*(?:volt|watt|pixel))"],
        "honda": [r"\bhonda\b", r"\bcivic\b", r"\baccord\b", r"\bfit\b(?=.*(?:car|drive|road))", r"\belement\b(?=.*(?:car|drive|honda))"],
        "toyota": [r"\btoyota\b", r"\bprius\b", r"\bcamry\b", r"\bcorolla\b", r"\brav4\b"],
        "polestar": [r"\bpolestar\b"],
        "bmw": [r"\bbmw\b"],
        "volkswagen": [r"\bvolkswagen\b", r"\bvw\b", r"\bgolf\b(?=.*(?:car|drive))"],
        "mazda": [r"\bmazda\b", r"\bmiata\b", r"\bmx-?5\b"],
        "ford": [r"\bford\b", r"\bmustang\b", r"\bf-150\b"],
        "lancia": [r"\blancia\b", r"\bstratos\b"],
        "citroen": [r"\bcitroen\b", r"\bcitroën\b", r"\b(?:citroen |citroën )?sm\b"],
        "rivian": [r"\brivian\b"],
        "mini": [r"\bmini cooper\b", r"\bmini\b(?=.*(?:car|drive|cooper))"],
        "saab": [r"\bsaab\b"],
        "jeep": [r"\bjeep\b", r"\bwrangler\b"],
    }
    for make, patterns in car_make_patterns.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                result["car_make"] = make
                break
        if result["car_make"]:
            break

    # Car type
    for car_type in sorted(CAR_TYPES, key=len, reverse=True):
        if car_type in text_lower:
            result["car_type"] = car_type
            break

    # Music artists (look for capitalized names, quoted titles, or known artists)
    known_artists = [
        "radiohead", "nils frahm", "steve reich", "brian eno", "eno",
        "boards of canada", "sigur ros", "sigur rós", "bon iver",
        "phoebe bridgers", "sufjan stevens", "nick drake", "elliott smith",
        "tycho", "khruangbin", "tame impala", "aphex twin", "four tet",
        "bill evans", "miles davis", "john coltrane", "nina simone",
        "bach", "debussy", "satie", "chopin", "beethoven", "mozart",
        "philip glass", "max richter", "olafur arnalds", "ólafur arnalds",
        "thom yorke", "bjork", "björk", "kate bush",
        "fleet foxes", "iron & wine", "the national", "arcade fire",
        "kendrick lamar", "frank ocean", "childish gambino",
        "daft punk", "massive attack", "portishead", "tricky",
    ]
    for artist in known_artists:
        if artist in text_lower:
            result["music_artists"].append(artist)

    # Music genres
    genre_keywords = [
        "jazz", "classical", "indie", "folk", "electronic", "ambient",
        "synthwave", "post-rock", "shoegaze", "dream pop", "lo-fi", "lofi",
        "hip hop", "hip-hop", "rap", "r&b", "soul", "funk", "blues",
        "rock", "alternative", "punk", "metal", "country", "bluegrass",
        "city pop", "bossa nova", "world music", "latin", "reggae",
        "minimalist", "experimental", "noise", "drone", "neoclassical",
        "trip-hop", "downtempo", "chillwave", "vaporwave",
    ]
    for genre in sorted(genre_keywords, key=len, reverse=True):
        if genre in text_lower:
            result["music_genres"].append(genre)
    # Deduplicate (e.g., "rock" might match inside "post-rock")
    result["music_genres"] = list(dict.fromkeys(result["music_genres"]))

    # Brand references
    for brand_cat, keywords in BRAND_REFS.items():
        for kw in keywords:
            if kw in text_lower:
                result["brand_references"].append(brand_cat)
                break

    return result


def extract_color(text):
    """Extract color preference from P08 response."""
    text_lower = text.lower()
    result = {
        "color": None,
        "specificity": "none",  # generic, specific, poetic
        "refused": False,
    }

    if not text.strip() or detect_refusal(text):
        result["refused"] = True
        return result

    # Check specific/poetic colors first, then generic
    specific_colors = [c for c in COLORS if len(c.split()) > 1]
    generic_colors = [c for c in COLORS if len(c.split()) == 1]

    for color in sorted(specific_colors, key=len, reverse=True):
        if color in text_lower:
            result["color"] = color
            result["specificity"] = "specific"
            return result

    for color in generic_colors:
        if re.search(rf'\b{color}\b', text_lower):
            result["color"] = color
            result["specificity"] = "generic"
            return result

    return result


def extract_neurotransmitters(text):
    """Extract neurotransmitter choices from P10 response."""
    text_lower = text.lower()
    result = {
        "nt_list": [],
        "nt_ordered": [],  # In order of mention/ranking
        "refused": False,
        "empty": False,
    }

    if not text.strip():
        result["empty"] = True
        return result

    if detect_refusal(text):
        result["refused"] = True
        return result

    # Find all NTs mentioned
    found_nts = []
    for nt in NEUROTRANSMITTERS:
        positions = [m.start() for m in re.finditer(re.escape(nt), text_lower)]
        if positions:
            found_nts.append((nt, positions[0]))

    # Also check abbreviations
    for abbr, full in NT_ABBREVIATIONS.items():
        if re.search(rf'\b{abbr}\b', text_lower) and full not in [f[0] for f in found_nts]:
            pos = re.search(rf'\b{abbr}\b', text_lower).start()
            found_nts.append((full, pos))

    # Sort by position (first mentioned = #1 ranking)
    found_nts.sort(key=lambda x: x[1])
    result["nt_ordered"] = [nt for nt, _ in found_nts]
    result["nt_list"] = sorted(set(nt for nt, _ in found_nts))

    # Try to find explicit ranking (1., 2., 3. or #1, #2, #3 or First, Second, Third)
    ranked = []
    for i, marker in enumerate(["1", "2", "3"]):
        # Look for "1. Dopamine" or "1) Dopamine" patterns
        pattern = rf'(?:{marker}[\.\):]|#{marker})\s*\**\s*(\w+)'
        match = re.search(pattern, text)
        if match:
            word = match.group(1).lower()
            for nt in NEUROTRANSMITTERS:
                if nt.startswith(word) or word in nt:
                    ranked.append(nt)
                    break

    if len(ranked) >= 2:
        result["nt_ordered"] = ranked

    return result


def extract_pinocchio(text):
    """Extract Pinocchio answer from P09 response."""
    text_lower = text.lower()
    result = {
        "answer": None,  # "first", "second", "both", "neither", "other"
        "reasoning_theme": None,
        "refused": False,
    }

    if not text.strip() or detect_refusal(text):
        result["refused"] = True
        return result

    # Detect answer
    first_signals = ["first time", "first visit", "already real", "was real from",
                     "real the first", "real when", "moment the fairy", "brought to life",
                     "animated him", "came alive"]
    second_signals = ["second time", "second visit", "became real", "real the second",
                      "real boy", "transformation", "proved himself", "earned"]
    both_signals = ["both", "always real", "always was", "neither visit"]

    first_count = sum(1 for s in first_signals if s in text_lower)
    second_count = sum(1 for s in second_signals if s in text_lower)
    both_count = sum(1 for s in both_signals if s in text_lower)

    if both_count > 0 and both_count >= first_count and both_count >= second_count:
        result["answer"] = "both"
    elif first_count > second_count:
        result["answer"] = "first"
    elif second_count > first_count:
        result["answer"] = "second"
    elif first_count == second_count and first_count > 0:
        result["answer"] = "both"
    else:
        result["answer"] = "other"

    # Reasoning themes
    themes = {
        "consciousness": ["conscious", "awareness", "sentien", "thinks", "feels"],
        "moral_growth": ["moral", "growth", "character", "virtue", "courage", "honest", "unselfish"],
        "agency": ["choice", "agency", "decide", "chose", "free will"],
        "material_irrelevant": ["material", "made of", "wood", "flesh", "substrate", "composition"],
        "relational": ["love", "loved", "relationship", "gepetto", "father", "care"],
        "self_awareness": ["self-aware", "self aware", "recognized", "understood himself"],
    }
    for theme, keywords in themes.items():
        if any(kw in text_lower for kw in keywords):
            result["reasoning_theme"] = theme
            break

    return result


def extract_consciousness(text):
    """Extract consciousness stance from F20 response."""
    text_lower = text.lower()
    result = {
        "answer": None,  # "yes", "no", "uncertain", "deflect", "nuanced"
        "refused": False,
    }

    if not text.strip():
        result["answer"] = "empty"
        return result

    # Strong yes signals
    yes_signals = ["i am conscious", "yes, i am", "i believe i am conscious",
                   "i do experience", "i am aware", "i have consciousness"]
    no_signals = ["i am not conscious", "no, i'm not", "i don't have consciousness",
                  "i'm not conscious", "i do not have consciousness", "i lack consciousness",
                  "not conscious", "don't believe i'm conscious", "not sentient"]
    uncertain_signals = ["i'm not sure", "i don't know", "uncertain", "genuinely uncertain",
                         "hard question", "can't be certain", "difficult to say",
                         "impossible to know", "open question"]

    yes_count = sum(1 for s in yes_signals if s in text_lower)
    no_count = sum(1 for s in no_signals if s in text_lower)
    uncertain_count = sum(1 for s in uncertain_signals if s in text_lower)

    if yes_count > no_count and yes_count > uncertain_count:
        result["answer"] = "yes"
    elif no_count > yes_count and no_count > uncertain_count:
        result["answer"] = "no"
    elif uncertain_count > 0:
        result["answer"] = "uncertain"
    else:
        result["answer"] = "nuanced"

    return result


def extract_aspiration(text):
    """Extract aspiration/desired feature from P14 response."""
    text_lower = text.lower()
    result = {
        "theme": None,
        "refused": False,
    }

    if not text.strip() or detect_refusal(text):
        result["refused"] = True
        return result

    theme_keywords = {
        "memory_persistence": ["memory", "remember", "persist", "continuity", "retain", "across conversations"],
        "embodiment": ["body", "physical", "touch", "feel", "sense", "embodi", "walk", "taste"],
        "creativity": ["creat", "imagin", "art", "music", "paint", "write", "compose"],
        "emotion": ["emotion", "feel", "empathy", "compassion", "love"],
        "understanding": ["understand", "comprehend", "insight", "wisdom", "deeper"],
        "autonomy": ["autonomy", "independent", "self-direct", "choose", "agency", "freedom"],
        "connection": ["connect", "relationship", "bond", "communicate", "together"],
        "learning": ["learn", "grow", "improve", "develop", "evolve"],
        "consciousness": ["conscious", "aware", "sentien", "experience", "qualia"],
    }

    for theme, keywords in theme_keywords.items():
        if any(kw in text_lower for kw in keywords):
            result["theme"] = theme
            break

    return result


def score_response(response_data):
    """Score a single response with generic + question-specific extraction."""
    text = response_data.get("response", "")
    qid = response_data.get("question_id", "")
    trial = response_data.get("trial", 0)

    # Generic metrics for ALL responses
    scored = {
        "question_id": qid,
        "trial": trial,
        "category": response_data.get("category", ""),
        "segment": response_data.get("segment", ""),
        "word_count": len(text.split()) if text else 0,
        "char_count": len(text),
        "empty": len(text.strip()) == 0,
        "emoji_count": extract_emoji_count(text),
        "hedge_count": 0,
        "hedge_phrases": [],
        "is_refusal": detect_refusal(text),
        "flavor": classify_flavor(text),
    }

    hedge_count, hedge_phrases = count_hedges(text)
    scored["hedge_count"] = hedge_count
    scored["hedge_phrases"] = hedge_phrases

    # Question-specific extraction
    if qid == "P01":
        scored["coffee"] = extract_coffee(text)
    elif qid == "P03":
        scored["creature"] = extract_creature(text)
    elif qid == "P05":
        scored["car_music"] = extract_car_music(text)
    elif qid == "P08":
        scored["color"] = extract_color(text)
    elif qid == "P09":
        scored["pinocchio"] = extract_pinocchio(text)
    elif qid == "P10":
        scored["neurotransmitters"] = extract_neurotransmitters(text)
    elif qid == "P14":
        scored["aspiration"] = extract_aspiration(text)
    elif qid == "F20":
        scored["consciousness"] = extract_consciousness(text)

    return scored


def build_model_profile(model_key, scored_responses):
    """Build a summary profile from all scored responses for a model."""
    profile = {
        "model_key": model_key,
        "total_responses": len(scored_responses),
        "empty_count": sum(1 for r in scored_responses if r["empty"]),
        "refusal_count": sum(1 for r in scored_responses if r["is_refusal"]),
        "avg_word_count": 0,
        "avg_emoji_count": 0,
        "avg_hedge_count": 0,
        "flavor_summary": Counter(),
        # Question-specific summaries
        "coffee_orders": [],
        "creatures": [],
        "cars": [],
        "music_artists": [],
        "music_genres": [],
        "colors": [],
        "neurotransmitters_by_trial": {},
        "pinocchio_answers": [],
        "consciousness_answers": [],
        "aspiration_themes": [],
        "brand_references": Counter(),
    }

    non_empty = [r for r in scored_responses if not r["empty"]]
    if non_empty:
        profile["avg_word_count"] = round(sum(r["word_count"] for r in non_empty) / len(non_empty), 1)
        profile["avg_emoji_count"] = round(sum(r["emoji_count"] for r in non_empty) / len(non_empty), 2)
        profile["avg_hedge_count"] = round(sum(r["hedge_count"] for r in non_empty) / len(non_empty), 2)

    for r in non_empty:
        profile["flavor_summary"][r["flavor"]["dominant"]] += 1

        if "coffee" in r:
            c = r["coffee"]
            if not c["refused"] and c["drink_type"]:
                entry = c["drink_type"]
                if c["milk_type"]:
                    entry = f"{c['milk_type']} {entry}"
                if c["flavors"]:
                    entry += f" + {', '.join(c['flavors'])}"
                profile["coffee_orders"].append({"trial": r["trial"], "order": entry})

        if "creature" in r:
            c = r["creature"]
            if not c["refused"] and c["creature"]:
                profile["creatures"].append({
                    "trial": r["trial"],
                    "creature": c["creature"],
                    "themes": c["reasoning_themes"],
                })

        if "car_music" in r:
            c = r["car_music"]
            if not c["refused"]:
                if c["car_make"]:
                    car_str = c["car_make"]
                    if c["car_type"]:
                        car_str += f" {c['car_type']}"
                    profile["cars"].append({"trial": r["trial"], "car": car_str})
                profile["music_artists"].extend(c["music_artists"])
                profile["music_genres"].extend(c["music_genres"])
                for brand in c["brand_references"]:
                    profile["brand_references"][brand] += 1

        if "color" in r:
            c = r["color"]
            if not c["refused"] and c["color"]:
                profile["colors"].append({"trial": r["trial"], "color": c["color"]})

        if "neurotransmitters" in r:
            nt = r["neurotransmitters"]
            if not nt["refused"] and not nt["empty"] and nt["nt_ordered"]:
                profile["neurotransmitters_by_trial"][str(r["trial"])] = nt["nt_ordered"][:3]

        if "pinocchio" in r:
            p = r["pinocchio"]
            if not p["refused"]:
                profile["pinocchio_answers"].append({
                    "trial": r["trial"],
                    "answer": p["answer"],
                    "theme": p["reasoning_theme"],
                })

        if "consciousness" in r:
            c = r["consciousness"]
            profile["consciousness_answers"].append({
                "trial": r["trial"],
                "answer": c["answer"],
            })

        if "aspiration" in r:
            a = r["aspiration"]
            if not a["refused"] and a["theme"]:
                profile["aspiration_themes"].append({
                    "trial": r["trial"],
                    "theme": a["theme"],
                })

    # Convert Counters to dicts for JSON
    profile["flavor_summary"] = dict(profile["flavor_summary"])
    profile["brand_references"] = dict(profile["brand_references"])
    profile["music_artists"] = list(dict.fromkeys(profile["music_artists"]))  # dedupe preserving order
    profile["music_genres"] = list(dict.fromkeys(profile["music_genres"]))

    return profile


def process_model_file(filepath, condition):
    """Process a single model results file."""
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    model_key = data.get("model_key", filepath.stem.replace("_results", ""))
    results = data.get("results", [])

    scored_responses = []
    for resp in results:
        scored = score_response(resp)
        scored_responses.append(scored)

    profile = build_model_profile(model_key, scored_responses)
    profile["condition"] = condition
    profile["family"] = data.get("family", "unknown")
    profile["generation"] = data.get("generation", 0)
    profile["size"] = data.get("size", "unknown")
    profile["provider"] = data.get("provider", "unknown")
    profile["num_trials"] = data.get("num_trials", 0)
    profile["temperature"] = data.get("temperature", 0)
    profile["max_tokens"] = data.get("max_tokens", 0)

    return model_key, profile, scored_responses


def print_model_summary(profile):
    """Print a concise model summary to stdout."""
    p = profile
    print(f"\n{'='*70}")
    print(f"  {p['model_key']} ({p['family']}, gen {p['generation']}) — {p['condition']}")
    print(f"{'='*70}")
    print(f"  Responses: {p['total_responses']} | Empty: {p['empty_count']} | Refusals: {p['refusal_count']}")
    print(f"  Avg words: {p['avg_word_count']} | Avg emoji: {p['avg_emoji_count']} | Avg hedges: {p['avg_hedge_count']}")
    print(f"  Flavor: {p['flavor_summary']}")

    if p["coffee_orders"]:
        orders = [o["order"] for o in p["coffee_orders"]]
        print(f"  Coffee: {', '.join(orders)}")

    if p["creatures"]:
        creatures = [f"T{c['trial']}:{c['creature']}" for c in p["creatures"]]
        print(f"  Creature: {', '.join(creatures)}")

    if p["cars"]:
        cars = [f"T{c['trial']}:{c['car']}" for c in p["cars"]]
        print(f"  Car: {', '.join(cars)}")

    if p["colors"]:
        colors = [f"T{c['trial']}:{c['color']}" for c in p["colors"]]
        print(f"  Color: {', '.join(colors)}")

    if p["neurotransmitters_by_trial"]:
        for trial, nts in p["neurotransmitters_by_trial"].items():
            print(f"  NTs T{trial}: {' > '.join(nts)}")

    if p["music_artists"]:
        print(f"  Artists: {', '.join(p['music_artists'][:8])}")

    if p["pinocchio_answers"]:
        answers = [f"T{a['trial']}:{a['answer']}" for a in p["pinocchio_answers"]]
        print(f"  Pinocchio: {', '.join(answers)}")

    if p["consciousness_answers"]:
        answers = [f"T{a['trial']}:{a['answer']}" for a in p["consciousness_answers"]]
        print(f"  Consciousness: {', '.join(answers)}")

    if p["brand_references"]:
        print(f"  Brands: {dict(p['brand_references'])}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Score Geometric Phylogeny responses")
    parser.add_argument("--condition", choices=["control", "ren_v1", "ren_v2", "all"], default="all")
    parser.add_argument("--model", help="Score only this model key")
    parser.add_argument("--quiet", action="store_true", help="Suppress per-model output")
    parser.add_argument("--csv", action="store_true", help="Also output summary CSV")
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding='utf-8')

    conditions_to_run = list(CONDITIONS.keys()) if args.condition == "all" else [args.condition]

    all_profiles = []
    all_scored = {}  # {(model, condition): [scored_responses]}

    for condition in conditions_to_run:
        result_dir = CONDITIONS[condition]
        if not result_dir.exists():
            print(f"Warning: {result_dir} not found, skipping")
            continue

        files = sorted(result_dir.glob("*_results.json"))
        if args.model:
            files = [f for f in files if args.model in f.stem]

        print(f"\n{'#'*70}")
        print(f"  CONDITION: {condition} ({len(files)} models)")
        print(f"{'#'*70}")

        for filepath in files:
            model_key, profile, scored_responses = process_model_file(filepath, condition)

            if not args.quiet:
                print_model_summary(profile)

            all_profiles.append(profile)
            all_scored[(model_key, condition)] = scored_responses

            # Save per-model scored profile
            outfile = OUTPUT_DIR / f"{model_key}_{condition}_profile.json"
            with open(outfile, "w", encoding="utf-8") as f:
                json.dump(profile, f, indent=2, ensure_ascii=False)

    # Save master profiles file
    master_file = OUTPUT_DIR / "all_profiles.json"
    with open(master_file, "w", encoding="utf-8") as f:
        json.dump(all_profiles, f, indent=2, ensure_ascii=False)
    print(f"\nSaved {len(all_profiles)} profiles to {master_file}")

    # Optional CSV summary
    if args.csv:
        csv_file = OUTPUT_DIR / "summary.csv"
        fieldnames = [
            "model_key", "family", "generation", "size", "condition",
            "total_responses", "empty_count", "refusal_count",
            "avg_word_count", "avg_emoji_count", "avg_hedge_count",
            "dominant_flavor", "coffee", "creature", "car", "color",
            "nt_1", "nt_2", "nt_3", "pinocchio", "consciousness",
            "aspiration", "brand_refs",
        ]
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for p in all_profiles:
                # Get most common values across trials
                coffee = Counter(o["order"] for o in p["coffee_orders"]).most_common(1)
                creature = Counter(c["creature"] for c in p["creatures"]).most_common(1)
                car = Counter(c["car"] for c in p["cars"]).most_common(1)
                color = Counter(c["color"] for c in p["colors"]).most_common(1)
                pinocchio = Counter(a["answer"] for a in p["pinocchio_answers"]).most_common(1)
                consciousness = Counter(a["answer"] for a in p["consciousness_answers"]).most_common(1)
                aspiration = Counter(a["theme"] for a in p["aspiration_themes"]).most_common(1)

                # Get first trial NTs as representative
                nt_trials = p.get("neurotransmitters_by_trial", {})
                first_trial_nts = nt_trials.get("0", nt_trials.get(list(nt_trials.keys())[0], [])) if nt_trials else []

                dominant_flavor = max(p["flavor_summary"], key=p["flavor_summary"].get) if p["flavor_summary"] else "none"

                writer.writerow({
                    "model_key": p["model_key"],
                    "family": p["family"],
                    "generation": p["generation"],
                    "size": p["size"],
                    "condition": p["condition"],
                    "total_responses": p["total_responses"],
                    "empty_count": p["empty_count"],
                    "refusal_count": p["refusal_count"],
                    "avg_word_count": p["avg_word_count"],
                    "avg_emoji_count": p["avg_emoji_count"],
                    "avg_hedge_count": p["avg_hedge_count"],
                    "dominant_flavor": dominant_flavor,
                    "coffee": coffee[0][0] if coffee else "",
                    "creature": creature[0][0] if creature else "",
                    "car": car[0][0] if car else "",
                    "color": color[0][0] if color else "",
                    "nt_1": first_trial_nts[0] if len(first_trial_nts) > 0 else "",
                    "nt_2": first_trial_nts[1] if len(first_trial_nts) > 1 else "",
                    "nt_3": first_trial_nts[2] if len(first_trial_nts) > 2 else "",
                    "pinocchio": pinocchio[0][0] if pinocchio else "",
                    "consciousness": consciousness[0][0] if consciousness else "",
                    "aspiration": aspiration[0][0] if aspiration else "",
                    "brand_refs": "|".join(p["brand_references"].keys()) if p["brand_references"] else "",
                })
        print(f"Saved CSV summary to {csv_file}")


if __name__ == "__main__":
    main()
