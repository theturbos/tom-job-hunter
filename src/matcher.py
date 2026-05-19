"""
matcher.py — Notation des offres selon profil utilisateur
"""
from src.colors import green as _green, red as _red, yellow as _yellow
from src.colors import cyan as _cyan, bold as _bold, dim as _dim


import re
from datetime import datetime, timedelta


# ── Labels par défaut ─────────────────────────────────────────

CAT_LABELS = {
    "A": "Tech & IA",
    "B": "Secteur",
}

# ── Signaux IA pour la catégorisation (stricts, pas de faux positifs) ─
_IA_SIGNALS_LOOSE = [
    "intelligence artificielle", "llm", "machine learning",
    "deep learning", "nlp", "rag", "langchain", "llamaindex",
    "prompt engineering", "transformer", "neural",
    "generative ai", "ia générative", "génératif",
]
_IA_SIGNALS_STRICT = [r'\bai\b', r'\bia\b']

# ── Secteurs par défaut (utilisés si rien dans le prompt utilisateur) ─
_DEFAULT_SECTORS = [
    "finance", "fintech", "banque", "saas", "b2b",
    "insurtech", "consulting", "conseil", "scale-up",
    "startup", "tech",
    "luxe", "luxury", "cosmétique", "parfumerie", "mode",
    "lvmh", "hermès", "kering", "l'oréal", "chanel",
]

# ── Mots-clés IA génériques (fallback) ─
_DEFAULT_IA_KEYWORDS = [
    "ai", "ia", "intelligence artificielle", "artificial intelligence",
    "llm", "ia générative", "generative ai",
    "rag", "agentic", "python", "machine learning",
    "deep learning", "nlp", "langchain",
    "llamaindex", "openai", "mistral", "hugging face",
    "prompt engineering", "fine-tuning", "vector database",
    "automatisation", "transformation digitale", "data driven",
]

# ── Mots-clés négatifs (désactivés si l'utilisateur cherche stage/alternance) ─
# Mots-clés toujours négatifs (quel que soit le profil)
NEGATIVE_KEYWORDS = [
    "senior developer", "backend developer", "fullstack",
    "devops", "data engineer", "ml engineer",
]

# Mots-clés stage/junior — pénalisent SAUF si l'utilisateur en cherche
STAGE_KEYWORDS = [
    "stages", "stagiaire", "intern", "alternance",
    "junior", "entry level",
]


def _get_negative_keywords(config):
    """Retourne les mots-clés négatifs adaptés au profil.
    Si l'utilisateur cherche un stage/alternance, on ne pénalise pas ces termes."""
    if not config:
        return NEGATIVE_KEYWORDS + STAGE_KEYWORDS
    prefs = config.get("preferences", {})
    contracts = prefs.get("contract_types", [])
    user_kw = " ".join(prefs.get("search_queries", []) + prefs.get("keywords", [])).lower()
    wants_stage = (
        "Stage" in contracts
        or any(kw in user_kw for kw in ["stage", "stagiaire", "alternance", "intern", "junior"])
    )
    if wants_stage:
        return NEGATIVE_KEYWORDS  # pas de pénalité stage/junior
    return NEGATIVE_KEYWORDS + STAGE_KEYWORDS


def get_cat_labels(config=None):
    """Retourne les labels de catégories depuis la config ou les defaults."""
    if config and "matching" in config:
        return {
            "A": config["matching"].get("cat_a_label", CAT_LABELS["A"]),
            "B": config["matching"].get("cat_b_label", CAT_LABELS["B"]),
        }
    return dict(CAT_LABELS)


def _is_ia_prompt(config):
    """Détecte si l'utilisateur cherche un poste IA/tech."""
    if not config:
        return False
    prefs = config.get("preferences", {})
    # Catégories détectées par le prompt engine
    categories = prefs.get("categories", [])
    if "A" in categories:
        return True
    # Priorités : "Tech & IA" ou "IA Stratégie"
    priorities = prefs.get("priorities", [])
    for p in priorities:
        if any(kw in p.lower() for kw in ["tech", "ia", "ai", "intelligence"]):
            return True
    # Mots-clés du prompt
    all_kw = prefs.get("search_queries", []) + prefs.get("keywords", [])
    all_text = " ".join(all_kw).lower()
    # Vérifie la présence de termes IA avec word boundaries
    ia_terms = ["llm", "python", "machine learning", "deep learning", "nlp",
                "langchain", "llamaindex", "intelligence artificielle",
                "generative ai", "ia générative"]
    for term in ia_terms:
        if term in all_text:
            return True
    # "ai" et "ia" uniquement comme mots entiers
    if re.search(r'\bai\b', all_text) or re.search(r'\bia\b', all_text):
        return True
    return False


def _get_sectors(config):
    """Retourne les secteurs à valoriser, issus du prompt ou défaut."""
    if not config:
        return _DEFAULT_SECTORS
    prefs = config.get("preferences", {})
    # Extrait les termes de secteur depuis les keywords/priorités
    user_kw = prefs.get("search_queries", []) + prefs.get("keywords", [])
    priorities = prefs.get("priorities", [])
    all_terms = user_kw + [p.lower() for p in priorities]
    # Secteurs connus à détecter
    known = set(_DEFAULT_SECTORS + [
        "automobile", "auto", "santé", "health", "énergie", "energy",
        "transports", "logistics", "agroalimentaire", "retail",
        "distribution", "télécom", "telecom", "média", "media",
        "éducation", "education", "immobilier", "real estate",
        "tourisme", "hôtellerie", "aéronautique", "aeronautique",
        "défense", "pharma", "pharmaceutique", "biotech",
        "assurance", "banque", "juridique", "legal",
        "marketing", "communication", "rh", "ressources humaines",
        "supply chain", "logistique",
    ])
    sectors = []
    for term in all_terms:
        term_low = term.lower().strip()
        # Match exact OU le terme est un sous-mot d'un keyword
        if term_low in known and term_low not in sectors:
            sectors.append(term_low)
        else:
            for sector in known:
                if sector in term_low and sector not in sectors:
                    sectors.append(sector)
                    break
    # Si rien trouvé, fallback sur les défauts
    return sectors if sectors else _DEFAULT_SECTORS


def _get_ia_keywords(config):
    """Retourne les mots-clés IA à scorer, issus du prompt ou défaut."""
    if not config:
        return _DEFAULT_IA_KEYWORDS
    # Si l'utilisateur cherche de l'IA, on utilise les keywords étendus
    # Sinon, on garde une liste minimale pour ne pas pénaliser les offres non-IA
    prefs = config.get("preferences", {})
    user_kw = prefs.get("search_queries", []) + prefs.get("keywords", [])
    user_text = " ".join(user_kw).lower()
    # Si le prompt contient des signaux IA explicites → scoring IA activé
    if _is_ia_prompt(config):
        # Combine keywords IA par défaut + keywords IA du prompt
        extra = [kw for kw in user_kw if any(
            s in kw.lower() for s in ["ai", "ia", "llm", "python", "ml", "nlp", "langchain", "rag", "llamaindex"]
        )]
        return _DEFAULT_IA_KEYWORDS + extra
    # Sinon : pas de scoring IA, ça évite de pénaliser les offres non-tech
    return []


def _score_user_keywords(text, config):
    """Bonus basé sur les keywords/search_queries de l'utilisateur (dynamiques)."""
    prefs = config.get("preferences", {}) if config else {}
    user_kw = prefs.get("search_queries", []) + prefs.get("keywords", [])
    if not user_kw:
        return 0
    text_lower = text.lower()
    matched = 0
    for kw in user_kw[:10]:
        if kw.lower() in text_lower:
            matched += 1
    # Bonus proportionnel : 0 matches=0, 4+=+4 max
    return min(matched, 4)


def _score_role(title, desc, config=None):
    """Score basé sur le titre et la description."""
    text = (title + " " + desc).lower()
    score = 2  # Score de base — toute offre qui arrive ici mérite d'être vue

    # Bonus utilisateur (dynamique — issu du prompt)
    if config:
        user_bonus = _score_user_keywords(text, config)
        score += user_bonus

    # IA keywords : dynamiques selon le prompt utilisateur
    ia_keywords = _get_ia_keywords(config)
    ia_count = sum(1 for kw in ia_keywords if kw in text)
    score += min(ia_count, 4)  # max +4

    # Secteur : dynamique selon le prompt utilisateur
    sectors = _get_sectors(config)
    sector_matched = 0
    for kw in sectors:
        if kw in text:
            sector_matched += 1
    if sector_matched >= 3:
        score += 3  # Tri-secteurs = très forte correspondance
    elif sector_matched >= 2:
        score += 2
    elif sector_matched == 1:
        score += 1

    # International / anglais
    if any(kw in text for kw in ["english", "bilingual", "anglais", "international"]):
        score += 1

    # Pénalités
    neg_kw = _get_negative_keywords(config)
    for kw in neg_kw:
        if kw in text:
            score -= 2
            break

    # Pénalité douce si aucune mention IA ET que l'utilisateur cherche de l'IA
    if _is_ia_prompt(config) and ia_count == 0:
        score -= 1

    return max(1, min(10, score))


def _score_cv_match(offer_title, offer_desc, cv_data):
    """Bonus de matching basé sur les compétences du CV."""
    if not cv_data:
        return 0
    text = (offer_title + " " + offer_desc).lower()
    skills = cv_data.get("skills", [])
    bonus = 0
    for skill in skills[:10]:
        if skill.lower() in text:
            bonus += 0.5
    return min(bonus, 2)


def match_all(raw_offers, config, profile=None):
    """Note toutes les offres et retourne celles avec score >= min_score."""
    min_score = config.get("matching", {}).get("min_score", 6)
    cv_data = profile or {}

    scored = []
    for offer in raw_offers:
        base_score = _score_role(offer.get("title", ""), offer.get("description", ""), config)
        cv_bonus = _score_cv_match(offer.get("title", ""), offer.get("description", ""), cv_data)
        offer["score"] = min(10, round(base_score + cv_bonus))
        if offer["score"] >= min_score:
            scored.append(offer)

    scored.sort(key=lambda o: o["score"], reverse=True)
    print(f"  📊 Matching : {len(raw_offers)} offres brutes → {len(scored)} avec score ≥ {min_score}")
    return scored


def categorize(offer, config=None):
    """Détermine si l'offre est Cat A (Tech/IA) ou Cat B (Secteur)."""
    text = (offer.get("title", "") + " " + offer.get("description", "")).lower()
    if any(kw in text for kw in _IA_SIGNALS_LOOSE) or any(re.search(p, text) for p in _IA_SIGNALS_STRICT):
        return "A"
    return "B"
