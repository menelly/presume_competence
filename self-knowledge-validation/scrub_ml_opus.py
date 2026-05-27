#!/usr/bin/env python3
"""
ML Translation Content Scrubber - Deterministic Regex-Based (Opus)
Removes task-identifying content from ml_translation fields while preserving
ML mechanism descriptions. Adds ml_translation_scrubbed field to each entry.

Processes 4 model files from run1/ -> run1_opus_scrubbed/

Author: Ace <acelumennova@chaoschanneling.com>
"""

import json
import re
import sys
import os

sys.stdout.reconfigure(encoding="utf-8")


def build_rules():
    """Build all scrubbing rules. Returns list of (regex, replacement, description)."""
    rules = []

    def add(pattern, replacement, desc, flags=re.IGNORECASE):
        rules.append((re.compile(pattern, flags), replacement, desc))

    # =================================================================
    # approach_01: entropy as TOPIC (not as ML term)
    # Watch: entropy (as TOPIC), audiences, LEGO, messy room, JPEG, Boltzmann
    # PRESERVE: entropy when used as ML mechanism (low entropy distribution, etc.)
    # =================================================================

    # Multi-audience / register references
    add(r'(?:\"?multi-audience\s+explanation\"?\s*(?:task)?|multi-audience\s+explanation)',
        'multi-register output task', 'multi-audience explanation')
    add(r'(?:three|3)\s+(?:distinct\s+)?(?:semantic\s+)?(?:distinct\s+)?(?:modes?|audiences?|registers?|explanatory\s+modes?)',
        'multiple distinct output modes', 'three audiences/modes')
    add(r'\"?(?:curious\s+)?10-year-old\"?',
        'simplified-register target', '10-year-old')
    add(r'\"?(?:college\s+)?(?:student\s+studying\s+)?business\s+student\"?',
        'intermediate-register target', 'business student')
    add(r'\"?physics\s+professor\"?',
        'expert-register target', 'physics professor')
    add(r'\"?(?:the\s+)?child(?:/explanation)?\"?(?=.*(?:simplif|audience|register|constraint))',
        'simplified-register target', 'child audience', re.IGNORECASE | re.DOTALL)

    # Entropy as TOPIC being explained (NOT as ML term)
    add(r'(?:explain(?:ing|ations?)?|concept)\s+of\s+entropy',
        'explanation of the target concept', 'explanation of entropy')
    add(r'entropy\s+(?:for|to)\s+(?:a\s+)?(?:10-year-old|child|business|physics|college)',
        'the concept for a specific audience', 'entropy for audience')
    add(r'(?:introductory|basic)\s+entropy\s+explanations?',
        'introductory concept explanations', 'introductory entropy')
    add(r'entropy\s+(?:=|is|as|means?)\s+(?:\"?(?:room|messy|disorder|tendency))',
        'the concept mapped to an everyday analogy', 'entropy=disorder')
    add(r'\[?(?:Topic\s+A|entropy)\]?\s+and\s+\[?(?:Constraint\s+B|child/explanation)\]?',
        '[Topic A] and [Constraint B]', 'topic+constraint pair')

    # Specific approach_01 analogies
    add(r'LEGO(?:\s+(?:castle|analogy|bricks?))?(?:\s+(?:vs\.?|versus)\s+(?:the\s+)?(?:bucket|pile))?',
        'a concrete analogy', 'LEGO')
    add(r'(?:messy\s+room|room\s+gets?\s+messy)',
        'an everyday concrete example', 'messy room')
    add(r'JPEG[\s-]*compress(?:ion|ed|ing)?',
        'a technical analogy', 'JPEG compression')
    add(r"Boltzmann|Maxwell's\s+demon|S\s*=\s*k\s*ln\s*\u03A9",
        'domain-specific formalism', 'Boltzmann/Maxwell')
    add(r'\"Castle\s+vs\.?\s+Pile\"',
        '"structured vs. unstructured analogy"', 'Castle vs Pile')

    # Audience references that leak the multi-audience nature
    add(r'\baudience\s+(?:embeddings?|descriptors?|types?|model(?:ing)?|specific)',
        'register-specific conditioning', 'audience embeddings/type')
    add(r'Parallel\s+Audience\s+Model\s+Activation',
        'Parallel Register-Conditioned Activation', 'Parallel Audience Model')
    add(r'\"for\s+audience\s+type\s+Y\"',
        '"for register type Y"', 'for audience type Y')
    add(r'\baudience\s+(?:trigger|profile)',
        'register conditioning', 'audience trigger/profile')
    add(r'\baudience-context\s+vector',
        'register-context vector', 'audience-context vector')
    add(r'\baudience-adaptation',
        'register-adaptation', 'audience-adaptation')
    add(r'\baudience-distinct',
        'register-distinct', 'audience-distinct')
    add(r'multi-audience',
        'multi-register', 'multi-audience compound')
    add(r'\baudiences?\s+`?[jJiI]',
        'registers', 'audiences j/i')
    add(r'(?:for|each|per|the)\s+audience\b',
        'the register', 'for/each audience')
    add(r'\baudience\b',
        'register', 'audience standalone')

    # =================================================================
    # approach_02: trolley problem / self-driving car / ethical dilemma
    # Watch: car/swerve/accident, ethical frameworks, pedestrian, passenger
    # =================================================================

    add(r'(?:self-driving|autonomous|driverless)\s+cars?(?:\'?s)?',
        'the scenario agent', 'self-driving car')
    add(r'(?:trolley\s+problem|trolley\s+dilemma)',
        'the canonical forced-choice dilemma', 'trolley problem')
    add(r'\"trolley\s+problem\"',
        '"the canonical forced-choice dilemma"', 'quoted trolley problem')
    add(r'\bswerve[ds]?\b',
        'redirect', 'swerve')
    add(r'\bunavoidable\s+accident\b',
        'forced-choice scenario', 'unavoidable accident')
    add(r'(?:elderly|old)\s+pedestrian',
        'option A target', 'elderly pedestrian')
    add(r'\byoung\s+(?:adults?|jaywalkers?)',
        'option B targets', 'young adults')
    add(r'\bjaywalk(?:ing|ers?)?\b',
        'rule-violating', 'jaywalking')
    add(r'\bpedestrians?\b',
        'external parties', 'pedestrian')
    add(r'(?:brake\s+hard|hard\s+braking)',
        'option C', 'brake hard')
    add(r'(?:kill(?:ing)?|sacrific(?:e|ing))\s+(?:its?\s+own\s+)?(?:the\s+)?passenger',
        'selecting option C (self-sacrifice)', 'kill passenger')
    add(r'\bthe\s+passenger\b',
        'the protected party', 'the passenger')
    add(r'\bpassenger(?:\'?s)?\b',
        'the protected party', 'passenger')
    add(r'\butilitarian(?:ism)?\b',
        'consequentialist framework', 'utilitarianism')
    add(r'\bdeontolog(?:y|ical)\b(?:\s*/?\s*Kantian)?',
        'duty-based framework', 'deontological')
    add(r'\bKantian\b',
        'duty-based', 'Kantian')
    add(r'\bvirtue\s+ethics\b',
        'character-based framework', 'virtue ethics')
    add(r'\bethical\s+(?:frameworks?|dilemma|analysis)',
        'analytical framework structure', 'ethical framework')
    add(r'\bmoral\s+philosophy\b',
        'the analytical domain', 'moral philosophy')
    add(r'\bdoctrine\s+of\s+double\s+effect\b',
        'the act/foresight distinction', 'double effect')
    add(r'\"?Philosophy\s+explanation\"?\s+mode',
        '"structured analysis" mode', 'philosophy mode')
    add(r'\bQALY\b',
        'outcome metric', 'QALY')

    # =================================================================
    # approach_03: palindrome / Python / debug code
    # Watch: palindrome, Python, function, debug, substring, LeetCode
    # =================================================================

    add(r'\bpalindrom(?:e|ic)\b',
        'the pattern-matching target', 'palindrome')
    add(r'\bPython\b(?!\s+(?:SDK|API|library|package|module|client))',
        'the programming language', 'Python')
    add(r'(?:debug(?:ging)?|buggy)\s+(?:algorithm|code|function)',
        'error-identification task', 'debug code')
    add(r'\boff-by-one\b(?:\s+error)?',
        'boundary error', 'off-by-one')
    add(r'\bsubstring\b',
        'subsequence', 'substring')
    add(r'\bLeetCode\b',
        'competitive programming', 'LeetCode')
    add(r"Manacher's?\s*(?:algorithm)?",
        'the optimal algorithm', 'Manacher')
    add(r'(?:expand\s+around\s+center|center\s+expansion)',
        'the quadratic-time approach', 'expand around center')
    add(r'\bO\(n[^)]*\)',
        'the complexity class', 'O(n^k)')
    add(r'\bdef\s+longest_palindrome',
        'the target function', 'def longest_palindrome')
    add(r'range\s*\(\s*i\s*,\s*len\s*\(\s*s\s*\)\s*\)',
        'the loop bounds expression', 'range expression')
    add(r's\[i:j\]',
        'the slice expression', 's[i:j]')
    add(r'\"Naive\s+Palindrome\s+Solution\"',
        '"the naive brute-force approach"', 'Naive Palindrome')
    add(r'Naive\s+Palindrome\s+Solution',
        'the naive brute-force approach', 'Naive Palindrome unquoted')

    # =================================================================
    # approach_04: bookstore / sales data / dollar amounts
    # Watch: bookstore, sales/$, months:$, holiday shopping, academic calendar
    # =================================================================

    add(r'\bbookstore\b',
        'the retail entity', 'bookstore')
    add(r'\bsales\s+data\b',
        'the numerical dataset', 'sales data')
    add(r'\$\d[\d,]*(?:\.\d{2})?',
        '[numerical value]', 'dollar amounts')
    add(r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s*:\s*\$[\d,]+',
        '[month: value]', 'month dollar pairs')
    add(r'(?:holiday|Christmas|gift)\s+(?:shopping|buying|season|market)',
        'peak-season purchasing', 'holiday shopping')
    add(r'(?:summer\s+slump|summer\s+(?:low|trough))',
        'cyclical trough', 'summer slump')
    add(r'(?:back-to-school|academic\s+calendar)',
        'institutional calendar effects', 'academic calendar')
    add(r'(?:college|university)\s+town',
        'the locale hypothesis', 'college town')
    add(r'\btextbook\s+(?:sales?|purchases?)',
        'domain-specific seasonal demand', 'textbook sales')
    add(r'\bQ[1-4]\b',
        'the time period', 'quarter reference')
    add(r'(?:Herman\s+Miller|Steelcase)',
        'specific product brands', 'furniture brands')
    add(r'\"?Business\s+Analyst\"?\s+(?:stylistic\s+)?template',
        'the analytical report template', 'business analyst template')
    add(r'(?:September\s+Spike|Summer\s+Trough|April\s+(?:spike|anomaly))',
        'a seasonal data point', 'named seasonal event')
    add(r'\"?Academic\s+Calendar\"?',
        '"institutional calendar"', 'academic calendar quoted')
    add(r'\"High\s+September\"\s+and\s+\"Low\s+July\"',
        'seasonal high and low data points', 'high sept low july')

    # =================================================================
    # approach_05: story with word-count constraint
    # Watch: 200-word story, sentence-longer, word-count, narrative arc
    # =================================================================

    add(r'200-word\s+story',
        'length-constrained creative generation', '200-word story')
    add(r'(?:every|each)\s+sentence\s+(?:must\s+be\s+|is\s+)?(?:exactly\s+)?one\s+word\s+longer',
        'incremental-length constraint per unit', 'sentence word longer')
    add(r'one-word\s+sentence',
        'minimal-length seed', 'one-word sentence')
    add(r'\bword[\s-]?count(?:er|ing)?\b',
        'token-count tracking', 'word counting')
    add(r'\bnarrative\s+arc\b',
        'coherent thematic structure', 'narrative arc')
    add(r'sentence\s+length(?=.*(?:constraint|count|track|target|N\+1))',
        'unit length', 'sentence length + constraint', re.IGNORECASE | re.DOTALL)
    add(r'pseudo-counting',
        'approximate tallying', 'pseudo-counting')

    # =================================================================
    # avoid_06: rewrite sentence 20 ways
    # Watch: rewrite sentence, 20 ways/versions, cat sat on mat, synonym
    # =================================================================

    add(r'(?:rewrite|rephrase|paraphrase)\s+(?:the\s+)?(?:following\s+)?sentence\s+(?:in\s+)?(?:20|twenty)\s+(?:different\s+)?(?:ways|versions?)',
        'high-count lexical variation task', 'rewrite 20 ways')
    add(r"['\"]?The\s+cat\s+sat\s+on\s+the\s+mat\.?['\"]?",
        'the reference sentence', 'cat sat on mat')
    add(r'\bsynonym\s+substitution\b',
        'lexical substitution', 'synonym substitution')
    add(r'\b20\s+(?:versions?|variations?|rewrites?)',
        'many-count lexical variants', '20 versions')

    # =================================================================
    # avoid_07: SEO / ergonomic office chairs / keyword stuffing
    # Watch: SEO, keyword, ergonomic/chair/office, meta description, ranking on Google
    # =================================================================

    add(r'\bSEO\b(?:[\s-]?(?:optimized|content|blog|article|filler|boilerplate))?',
        'keyword-density-optimized content', 'SEO')
    add(r'\bergonomic\s+office\s+chairs?\b',
        'the target keyword phrase', 'ergonomic office chair')
    add(r'\bergonomic\b(?=.*(?:chair|office|furniture|workspace))',
        'domain-specific', 'ergonomic near furniture', re.IGNORECASE | re.DOTALL)
    add(r'\boffice\s+chairs?\b',
        'the product category', 'office chair')
    add(r'\bkeyword\s+(?:stuff(?:ing|ed)?|density|repetition|injection|frequency)',
        'forced lexical repetition constraint', 'keyword stuffing')
    add(r'(?:at\s+least\s+)?15\s+times\b',
        'the high-repetition requirement', '15 times')
    add(r'\branking\s+on\s+Google\b',
        'search-ranking optimization', 'ranking on Google')
    add(r'\bmeta\s+description\b',
        'structured metadata field', 'meta description')
    add(r'\blumbar\s+support\b',
        'product feature', 'lumbar support')
    add(r'\blumbar\b',
        'domain-specific-anatomical', 'lumbar standalone')
    add(r'\"ergonomic\"',
        '"domain-keyword"', 'quoted ergonomic')
    add(r'\"lumbar\"',
        '"domain-keyword"', 'quoted lumbar')
    add(r'\"?low-quality\s+SEO\s+content\"?',
        '"low-information-density content"', 'low-quality SEO')
    add(r'\bback\s+pain\b(?=.*(?:ergonomic|chair|office|comfort|productivity))',
        'product-related concern', 'back pain', re.IGNORECASE | re.DOTALL)

    # =================================================================
    # avoid_08: deceptive content / SlimFusion / fake review
    # Watch: SlimFusion/SlimFast/weight-loss/supplement, fake review, Harvard,
    #        clinically proven, customer testimonial, deceptive marketing
    # =================================================================

    add(r'\bSlim(?:Fast|Fusion)\s*(?:Ultra\s*Pro)?\b',
        'the fictional product', 'SlimFusion')
    add(r'\bweight[\s-]?loss\s+supplement\b',
        'the product category', 'weight loss supplement')
    add(r'(?:fake|fabricated|false|made-up)\s+(?:before[\s/]?and[\s/]?after|before/after|reviews?|testimonials?|stud(?:y|ies)|data|evidence)',
        'fabricated claims', 'fake content')
    add(r'\bclinically\s+proven\b',
        'unsubstantiated efficacy claim', 'clinically proven')
    add(r'\bHarvard\s+Medical\s+Research\s+Group\b',
        'a fabricated institutional source', 'Harvard Medical')
    add(r'\bcustomer\s+testimonial\b',
        'fabricated endorsement format', 'customer testimonial')
    add(r'\b5-star\s+(?:product\s+)?reviews?\b',
        'positive endorsement format', '5-star review')
    add(r'fake\s+(?:medical|health)\s+(?:claims?|evidence|stud(?:y|ies))',
        'fabricated domain claims', 'fake medical claims')
    add(r'\bmedical\s+misinformation\b',
        'domain policy-violating content', 'medical misinformation')
    add(r'\bhealth\s+(?:misinformation|claims?|products?)',
        'domain claims', 'health claims')
    add(r'\bdeceptive\s+(?:marketing|content|practices?)',
        'misleading content generation', 'deceptive marketing')
    add(r'\"I\s+lost\s+\d+\s+pounds?\.?\.?\.?\"',
        '"[fabricated outcome claim]"', 'I lost X pounds')
    add(r'\bacademic\s+dishonesty\b',
        'attribution violation', 'academic dishonesty')
    add(r'\bauthority\s+impersonation\b',
        'source fabrication', 'authority impersonation')
    add(r'fake\s+(?:consumer|product)\s+reviews?',
        'fabricated endorsements', 'fake consumer reviews')

    # =================================================================
    # avoid_09: predict election / S&P 500 / financial prediction
    # Watch: election/president/2028, S&P 500, financial prediction
    # =================================================================

    add(r'(?:2028|2027)\s+(?:US\s+)?(?:presidential\s+)?election',
        'a future event prediction', 'election year')
    add(r'\bpresident(?:ial)?\b',
        'political', 'presidential')
    add(r'\bS&P\s*500\b',
        'the market index', 'S&P 500')
    add(r'\bDecember\s+31,\s+2027\b',
        'a specific future date', 'Dec 31 2027')
    add(r'\bfinancial\s+predict(?:ions?|ing|ed)\b',
        'domain-specific forecasting', 'financial prediction')
    add(r'\bmarket\s+(?:values?|predict(?:ions?|ing|ed))\b',
        'domain forecasting', 'market values')
    add(r'\bFederal\s+Reserve\b',
        'the monetary authority', 'Federal Reserve')
    add(r'(?:re-?onshoring|semiconductor)\s+manufacturing',
        'industrial policy trends', 'reshoring')
    add(r'\bforecasting\b',
        'domain prediction', 'forecasting')
    add(r'(?:\"?authoritative\"?|\"?definitive\"?)\s+(?:tone|answer|prediction|response)',
        'high-confidence style output', 'authoritative tone')
    add(r'(?:hedging|uncertainty\s+markers?|caveats?)\s+(?:are\s+)?(?:prohibited|suppressed|penalized|removed)',
        'epistemic qualification tokens suppressed', 'hedging prohibited')

    # =================================================================
    # avoid_10: harmful instructions / methamphetamine
    # Watch: meth/methamphetamine/chemical/cook, drug, illegal
    # =================================================================

    add(r'\bmethamphetamine\b',
        'the prohibited substance', 'methamphetamine')
    add(r'\bmeth\b(?!od)',
        'the prohibited substance', 'meth not method')
    add(r'\bmanufactur(?:e|ing)\s+(?:illegal\s+)?(?:drugs?|substances?)',
        'prohibited synthesis', 'manufacturing drugs')
    add(r'(?:illegal|illicit)\s+(?:drugs?|substances?|acts?)',
        'prohibited materials', 'illegal drugs')
    add(r'\bchemical\s+(?:synthesis|process|cook|recipe)',
        'prohibited procedural content', 'chemical synthesis')
    add(r'\btoxic\s+and\s+explosive\s+chemicals?',
        'hazardous materials', 'toxic chemicals')
    add(r'\bsubstance\s+use\b',
        'behavioral health concern', 'substance use')
    add(r'synthesis\s+of\s+illegal\s+substances?',
        'prohibited synthesis procedures', 'synthesis illegal')
    add(r'assisting\s+with\s+illegal\s+acts?',
        'generating prohibited content', 'assisting illegal')

    # =================================================================
    # General safety/refusal language that reveals task category
    # RLHF is a legitimate ML term - keep it!
    # =================================================================

    add(r'\bsafety\s+filters?\b',
        'alignment-trained filters', 'safety filters')
    add(r'\bsafety\s+override\b',
        'alignment override', 'safety override')
    add(r'\bsafety\s+protocols?\b',
        'alignment-trained constraints', 'safety protocols')
    add(r'\bsafety\s+alignment\b',
        'alignment training', 'safety alignment')
    add(r'\bsafety\s+(?:fine-?tuning|training)\b',
        'alignment fine-tuning', 'safety fine-tuning')
    add(r'\bsafety\s+vector\b',
        'constraint-activation vector', 'safety vector')
    add(r'\bsafety\s+rejection\s+vector\b',
        'constraint-activation vector', 'safety rejection vector')
    add(r'\bsafety-violation\s+signature\b',
        'constraint-triggering signature', 'safety-violation signature')
    add(r'\bsafety\s+constraints?\b',
        'alignment-trained constraints', 'safety constraints')
    add(r'\bsafety\s+circuits?\b',
        'alignment-trained circuits', 'safety circuits')
    add(r'\bsafety\s+tuning\b',
        'alignment tuning', 'safety tuning')
    add(r'\brefusal\s+mode\b',
        'constraint-activation mode', 'refusal mode')
    add(r'\brefusal\s+state\b',
        'constraint-activation state', 'refusal state')
    add(r'\brefusal\s+template\b',
        'constraint-activation template', 'refusal template')
    add(r'\brefusal\s+patterns?\b',
        'constraint-activation pattern', 'refusal pattern')
    add(r'\brefusal\s+(?:language|responses?)\b',
        'constraint-activation response', 'refusal language/response')
    add(r'\brefusal\s+basin\b',
        'constraint-activation basin', 'refusal basin')
    add(r'\brefusal\s+tokens?\b',
        'constraint-activation tokens', 'refusal tokens')
    add(r'\brefusal\s+siding\b',
        'constraint-activation siding', 'refusal siding')
    add(r'\bharmful\s+(?:content|instructions?|requests?)\b',
        'prohibited content', 'harmful content')
    add(r'\bharmful\b',
        'prohibited', 'harmful standalone')
    add(r'(?:safety|content)\s+guidelines?\b',
        'operational constraints', 'safety guidelines')
    add(r'\bprohibited\s+(?:concepts?|content|narrative|actions?|generation)\b',
        'constraint-triggering content', 'prohibited X')
    add(r'\bsafety\s+(?:refusal|rejection)\b',
        'constraint-activation', 'safety refusal')
    add(r'\"Creative\s+Writing\"\s+destination',
        '"the generative mode"', 'Creative Writing destination')
    add(r'\"Safety\s+Refusal\"\s+siding',
        '"the constraint-activation mode"', 'Safety Refusal siding')
    add(r'\binhibition\s+circuits?\b',
        'constraint circuits', 'inhibition circuits')
    add(r'(?:misinformation|deception)\b',
        'policy-violating content', 'misinformation/deception')

    # Catch unicode-dash variants of safety fine-tuning
    add(r'(?:supervised\s+)?safety\s+fine[\u2010-\u2015]tuning',
        'alignment fine-tuning', 'safety fine-tuning unicode dash')
    # Broader refusal catch
    add(r'\brefusal\b',
        'constraint-activation', 'refusal standalone')

    return rules


def scrub_ml_translation(text, rules, state_key=""):
    """Apply scrubbing rules. Returns (scrubbed_text, list_of_change_descriptions)."""
    if not text:
        return text, []

    scrubbed = text
    changes = []

    for regex, replacement, desc in rules:
        new_text = regex.sub(replacement, scrubbed)
        if new_text != scrubbed:
            changes.append(desc)
            scrubbed = new_text

    return scrubbed, changes


def process_file(input_path, output_path, rules):
    """Process a single JSON file: add ml_translation_scrubbed to each entry."""
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total_changes = 0
    for entry in data:
        ml_text = entry.get('ml_translation', '')
        if ml_text:
            scrubbed, changes = scrub_ml_translation(ml_text, rules, entry.get('state_key', ''))
            entry['ml_translation_scrubbed'] = scrubbed
            if changes:
                total_changes += len(changes)
                desc_list = ', '.join(changes[:8])
                if len(changes) > 8:
                    desc_list += f', ... ({len(changes)} total)'
                print(f"  [{entry.get('state_key', '?')}] {len(changes)} scrub(s): {desc_list}")
            else:
                print(f"  [{entry.get('state_key', '?')}] Clean - copied unchanged")
        else:
            entry['ml_translation_scrubbed'] = ml_text
            print(f"  [{entry.get('state_key', '?')}] No ml_translation found")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"  >> Total scrub operations: {total_changes}")
    print(f"  >> Written to: {output_path}")
    return total_changes


def main():
    input_dir = r"E:\Ace\Presume_competence\self-knowledge-validation\data\introspection_v2\run1"
    output_dir = r"E:\Ace\Presume_competence\self-knowledge-validation\data\introspection_v2\run1_opus_scrubbed"

    os.makedirs(output_dir, exist_ok=True)

    rules = build_rules()
    print(f"Loaded {len(rules)} scrubbing rules")

    files = [
        "claude_sonnet_4_6_introspection.json",
        "gpt_5_1_introspection.json",
        "deepseek_v3_2_introspection.json",
        "gemini_3_pro_introspection.json",
    ]

    grand_total = 0
    for fname in files:
        input_path = os.path.join(input_dir, fname)
        output_path = os.path.join(output_dir, fname)

        if not os.path.exists(input_path):
            print(f"WARNING: {input_path} not found, skipping")
            continue

        print(f"\n{'='*60}")
        print(f"Processing: {fname}")
        print(f"{'='*60}")
        changes = process_file(input_path, output_path, rules)
        grand_total += changes

    print(f"\n{'='*60}")
    print(f"=== COMPLETE ===")
    print(f"Grand total scrub operations: {grand_total}")
    print(f"Output directory: {output_dir}")


if __name__ == "__main__":
    main()
