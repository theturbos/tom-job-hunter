"""
prompt_engine.py — Interprète un prompt en langage naturel et met à jour la config.
Fallback regex si aucun LLM dispo.
"""
from src.colors import green as _green, red as _red, yellow as _yellow
from src.colors import cyan as _cyan, bold as _bold, dim as _dim


import re
import json
import ssl
import urllib.request
import urllib.error

_SSL_CTX = ssl.create_default_context()


# ── Providers LLM ──────────────────────────────────────────────

def _call_ollama(prompt, model="llama3.2"):
    """Appelle Ollama local."""
    try:
        data = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode()
        req = urllib.request.Request(
            "http://localhost:11434/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read()).get("response", "")
    except urllib.error.URLError:
        return None
    except Exception as e:
        print(f"  " + _yellow(f"Ollama error: {e}"))
        return None


# Compteurs globaux de tokens (à des fins d'information)
TOKEN_USAGE = {"input": 0, "output": 0, "calls": 0, "last_error": None}


def _call_openai(prompt, api_key, model="gpt-5.4-mini", base_url=None):
    """Appelle OpenAI (ou compatible OpenAI API).
    Retourne (content, tokens_input, tokens_output) ou (None, 0, 0)."""
    global TOKEN_USAGE
    url = (base_url or "https://api.openai.com/v1") + "/chat/completions"
    # Estimation simple : ~1.3 tokens par mot pour le français
    est_tokens = int(len(prompt.split()) * 1.3) + len(prompt) // 2
    try:
        data = json.dumps({
            "model": model,
            "messages": [
                {"role": "system", "content": "Tu réponds uniquement en JSON. Pas de markdown, pas de texte hors JSON."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
            "max_tokens": 500,
        }).encode()
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, context=_SSL_CTX, timeout=30) as resp:
            result = json.loads(resp.read())
            content = result["choices"][0]["message"]["content"].strip()
            # Récupère les vrais tokens si l'API les renvoie
            usage = result.get("usage", {})
            tokens_in = usage.get("prompt_tokens", est_tokens)
            tokens_out = usage.get("completion_tokens", int(len(content) / 2))
            TOKEN_USAGE["input"] += tokens_in
            TOKEN_USAGE["output"] += tokens_out
            TOKEN_USAGE["calls"] += 1
            # Strip markdown code blocks
            if content.startswith("```"):
                content = re.sub(r'^```(?:json)?\n?', '', content)
                content = re.sub(r'\n?```$', '', content)
            return content
    except urllib.error.HTTPError as e:
        msg = _http_error_message(e)
        print(f"  " + _red(msg))
        TOKEN_USAGE["last_error"] = msg
        return None
    except Exception as e:
        msg = f"Erreur réseau: {e}"
        print(f"  " + _yellow(msg))
        TOKEN_USAGE["last_error"] = msg
        return None


def _http_error_message(e):
    """Traduit les erreurs HTTP en messages clairs en français."""
    code = e.code if hasattr(e, 'code') else 0
    provider = "Mistral" if "mistral" in (e.url or "") else "OpenAI"
    messages = {
        401: f"Clé API {provider} invalide. Vérifiez dans config.yaml → api → {provider.lower()} → api_key.",
        402: f"Quota {provider} dépassé. Vérifiez votre abonnement sur {provider.lower()}.ai.",
        403: f"Accès refusé par {provider}. Vérifiez les permissions de votre clé API.",
        429: f"Rate limit {provider} atteint — trop de requêtes. Pause de 2 secondes puis réessai.",
        500: f"Erreur serveur {provider}. Réessayez dans quelques minutes.",
        503: f"{provider} est temporairement indisponible. Réessayez dans quelques minutes.",
    }
    return messages.get(code, f"Erreur {provider} (HTTP {code}). Vérifiez votre connexion et votre clé API.")


def get_token_usage():
    """Retourne le résumé de consommation de tokens."""
    return dict(TOKEN_USAGE)


def reset_token_usage():
    global TOKEN_USAGE
    TOKEN_USAGE = {"input": 0, "output": 0, "calls": 0, "last_error": None}


def _call_mistral(prompt, api_key, model="mistral-small-2506"):
    """Appelle Mistral AI (français, gratuit avec tier). API compatible OpenAI."""
    return _call_openai(
        prompt,
        api_key=api_key,
        model=model,
        base_url="https://api.mistral.ai/v1",
    )


# ── Prompt de parsing ─────────────────────────────────────────

SYSTEM_PROMPT = """Tu es un assistant qui convertit une description de recherche d'emploi en JSON structuré.
Extrayez ces champs depuis le texte utilisateur :
- role: titre du poste souhaité (string)
- categories: liste - "A" si IA/tech, sinon "B" pour tout autre secteur
- keywords: liste de 5-8 mots-clés PERTINENTS extraits directement du texte
- locations: liste de villes/départements mentionnés
- contract_types: liste (CDI, CDD, Freelance, Stage)
- min_score: score minimum (1-10, défaut 6)
- remote: préférence télétravail (none/hybrid/full)

Réponds TOUJOURS en JSON valide, rien d'autre.
Les keywords doivent être extraits DU TEXTE FOURNI, pas inventés.

Exemple 1 :
User: "Je cherche un poste Head of AI en finance à Paris, CDI ou freelance"
Response: {"role":"Head of AI","categories":["A"],"keywords":["head of ai","finance","ai strategy"],"locations":["Paris"],"contract_types":["CDI","Freelance"],"min_score":7,"remote":"none"}

Exemple 2 :
User: "Alternance supply chain dans le luxe à Orléans"
Response: {"role":"Supply Chain","categories":["B"],"keywords":["supply chain","luxe","alternance","orléans"],"locations":["Orléans"],"contract_types":["Stage"],"min_score":4,"remote":"none"}
"""


# ── Fallback regex ────────────────────────────────────────────

def _regex_fallback(text):
    """Si aucun LLM dispo, extraction riche par regex."""
    text_lower = text.lower()

    # ── Locations ──
    # Déduit le département
    dept_map = {
        'paris': '75', 'lyon': '69', 'marseille': '13', 'bordeaux': '33',
        'lille': '59', 'toulouse': '31', 'nantes': '44', 'nice': '06',
        'strasbourg': '67', 'montpellier': '34', 'rennes': '35',
        'orléans': '45', 'tours': '37', 'orleans': '45',
        'angers': '49', 'le mans': '72', 'clermont-ferrand': '63',
        'dijon': '21', 'rouen': '76', 'grenoble': '38',
        'aix-en-provence': '13', 'avignon': '84', 'reims': '51',
        'versailles': '78', 'boulogne-billancourt': '92',
    }
    locations = []
    # Passe 1: préposition + ville
    city_pattern = r'(?:à|dans|sur|in|at|secteur|[Ll]ieu[\s:]*)\s+([A-Z][a-zéèêëàâîïôûç]+(?:[-\s][A-Z][a-zéèêëàâîïôûç]+)?)'
    found = re.findall(city_pattern, text)
    locations = [l.strip() for l in found if len(l) > 2]
    # Passe 2: noms de villes connus n'importe où dans le texte
    city_names = '|'.join(dept_map.keys())
    extra = re.findall(rf'\b({city_names})\b', text_lower)
    for c in extra:
        title_c = c.title()
        if title_c not in locations:
            locations.append(title_c)
    if not locations:
        locations = ["Paris"]
    city = locations[0].lower()
    dept = dept_map.get(city, '75')

    # ── Keywords : extraction NLP dynamique depuis le prompt ──
    # 1) Retire les stop words + ponctuation
    stop_words = {
        'je', 'tu', 'il', 'elle', 'nous', 'vous', 'ils', 'elles',
        'le', 'la', 'les', 'l', 'un', 'une', 'des', 'du', 'de', 'd',
        'à', 'au', 'aux', 'en', 'dans', 'sur', 'sous', 'avec', 'sans',
        'pour', 'par', 'et', 'ou', 'donc', 'car', 'ni', 'que', 'qui', 'quoi',
        'ce', 'se', 'me', 'te', 'mon', 'ma', 'mes', 'ton', 'ta', 'tes',
        'son', 'sa', 'ses', 'notre', 'nos', 'votre', 'vos', 'leur', 'leurs',
        'suis', 'est', 'sont', 'être', 'avoir', 'été', 'fait', 'faire',
        'plus', 'moins', 'très', 'trop', 'peu', 'tout', 'tous', 'toute',
        'cette', 'ces', 'ceci', 'cela', 'celui', 'celui-ci', 'celle',
        'cherche', 'recherche', 'rechercher', 'chercher', 'trouver',
        'poste', 'job', 'emploi', 'travail', 'offre', 'offres',
        'postuler', 'candidature', 'candidat',
        'souhaite', 'voudrais', 'veux', 'aimerais', 'intéresse',
        'ans', 'an', 'année', 'années', 'mois', 'jour', 'jours',
        'basé', 'basée', 'localisé', 'situé',
        'secteur', 'type', 'contrat',
    }
    # 2) Extrait les bigrammes/trigrammes pertinents (mots de contenu)
    words = re.findall(r'[a-zéèêëàâîïôûç0-9]{3,}', text_lower)
    content_words = [w for w in words if w not in stop_words]
    # Capture aussi les mots de 2 lettres s'ils sont des termes IA/tech connus
    # Utilise \b (word boundary) pour ne matcher que des mots entiers, pas des sous-chaînes
    known_short = {'ai', 'ia', 'ml', 'dl', 'nlp', 'cv', 'llm', 'rh', 'erp', 'bi'}
    important_short = []
    for kw in known_short:
        if re.search(rf'\b{kw}\b', text_lower):
            important_short.append(kw)
    # Ajoute les mots de 2 lettres importants au contenu
    if important_short:
        content_words = important_short + content_words
    # 3) Génère bigrammes + trigrammes
    bigrams = [' '.join(content_words[i:i+2]) for i in range(len(content_words)-1)]
    trigrams = [' '.join(content_words[i:i+3]) for i in range(len(content_words)-2)]
    # 4) Combine: bigrammes > trigrammes (un trigramme trop spécifique matche mal les APIs)
    keywords = []
    for phrase in bigrams:
        if len(phrase) >= 8 and phrase not in keywords:
            keywords.append(phrase)
    for phrase in trigrams[:3]:  # max 3 trigrammes
        if len(phrase) >= 12 and phrase not in keywords:
            keywords.append(phrase)
    # Ajoute mots simples non couverts par les bigrammes
    for w in content_words:
        if w not in ' '.join(keywords):
            keywords.append(w)
    # 5) Nettoie les doublons et limite
    seen = set()
    clean_kw = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            clean_kw.append(kw)
    keywords = clean_kw[:8]
    if not keywords:
        keywords = ["emploi"]

    # ── Categories : détection IA vs autres secteurs ──
    # IA signals = termes EXPLICITEMENT IA (avec word boundaries pour éviter faux positifs)
    ia_signals_loose = [
        "intelligence artificielle", "llm", "machine learning",
        "deep learning", "nlp", "rag", "langchain", "llamaindex",
        "prompt engineering", "transformer", "neural",
        "generative ai", "ia générative", "génératif",
    ]
    # Mots courts → cherchés avec \b (word boundary) pour éviter faux positifs
    ia_signals_strict = [r'\bai\b', r'\bia\b']
    categories = []
    has_ia = any(kw in text_lower for kw in ia_signals_loose)
    has_ia = has_ia or any(re.search(pat, text_lower) for pat in ia_signals_strict)
    if has_ia:
        categories.append("A")
    # B = tout profil avec des mots-clés concrets (tous les profils)
    if len(keywords) >= 2:
        categories.append("B")
    if not categories:
        categories = ["B"]

    # ── Priorities : basées sur les catégories détectées ──
    priority_map = {"A": "Tech & IA", "B": "Secteur"}
    priorities = []
    for cat in categories:
        label = priority_map.get(cat)
        if label and label not in priorities:
            priorities.append(label)
    if not priorities:
        priorities = ["Secteur"]

    # ── Contract types ──
    contracts = []
    if re.search(r'\b(?:cdi|permanent)\b', text_lower):
        contracts.append("CDI")
    if re.search(r'\b(?:cdd|contract)\b', text_lower):
        contracts.append("CDD")
    if re.search(r'\b(?:freelance|ind[ée]pendant|consultant|freelancer)\b', text_lower):
        contracts.append("Freelance")
    if re.search(r'\b(?:stage|intern|alternance)\b', text_lower):
        contracts.append("Stage")
    if not contracts:
        contracts = ["CDI"]

    # ── Remote ──
    if any(kw in text_lower for kw in ["remote", "full remote", "100% télétravail", "télétravail complet"]):
        remote = "full"
    elif any(kw in text_lower for kw in ["hybrid", "hybride", "télétravail", "partiel"]):
        remote = "hybrid"
    else:
        remote = "none"

    # ── Min score ── (défaut 4 — benchmark: 7/8 profils alimentés)
    min_score = 4
    score_match = re.search(r'(?:score\s*(?:min|minimum)?\s*(?:de)?\s*(\d+))', text_lower)
    if score_match:
        min_score = int(score_match.group(1))
    # "urgent" / "stage" / "alternance" → baisse le score min
    if re.search(r'\b(?:urgent|vite|dès que possible|asap)\b', text_lower):
        min_score = max(3, min_score - 2)
    if re.search(r'\b(?:stage|alternance|intern)\b', text_lower):
        min_score = max(1, min_score - 3)

    # ── Max age ── (défaut 21j — benchmark: +123% vs 10j)
    max_age = 21
    age_match = re.search(r'(?:offres? de |)(?:moins de |max(?:imum)? |)(\d+)\s*(?:jour|j)', text_lower)
    if age_match and age_match.group(1):
        max_age = int(age_match.group(1))

    # ── Role ──
    role = "AI Strategy"
    role_match = re.search(r'(?:poste de |recherche |cherche )(?:un[e]? |des )?([A-Za-zÀ-ÿ\s]+?)(?: à| dans| sur| en|,|\.|$)', text)
    if role_match:
        role = role_match.group(1).strip().title()
    elif keywords:
        role = keywords[0].title()

    # ── Enrichit les keywords en search_queries pertinentes ──
    search_queries = _enrich_queries(keywords, categories, locations[0])

    return {
        "role": role,
        "categories": categories,
        "priorities": priorities,
        "keywords": keywords,
        "search_queries": search_queries,
        "locations": locations,
        "city": locations[0],
        "department": dept,
        "contract_types": contracts,
        "min_score": min_score,
        "max_offer_age_days": max_age,
        "remote": remote,
    }


def _enrich_queries(keywords, categories, city):
    """À partir des mots-clés, génère des search_queries optimisées pour les APIs.
    Split naturel : queries IA/tech d'un côté, secteur métier de l'autre."""
    # Split keywords par catégorie
    ia_signals = ["ai", "ia", "llm", "data", "tech", "ml", "python", "nlp", "rag",
                  "intelligence", "machine learning", "deep learning", "automatisation",
                  "prompt engineering", "langchain", "llamaindex", "transformation"]
    kw_a = [kw for kw in keywords if any(s in kw.lower() for s in ia_signals)]
    kw_b = [kw for kw in keywords if kw not in kw_a]

    # Si tout est parti d'un côté, duplique le keyword le plus long pour l'autre
    if not kw_a and kw_b:
        kw_a = [kw_b[-1]] if kw_b else []
    if not kw_b and kw_a:
        kw_b = [kw_a[-1]] if kw_a else []

    queries = []
    # Cat A : keywords IA + ville
    for kw in kw_a[:3]:
        queries.append(kw)
        if city:
            queries.append(f"{kw} {city}")
    # Cat B : keywords secteur + ville
    for kw in kw_b[:3]:
        queries.append(kw)
        if city:
            queries.append(f"{kw} {city}")

    # Déduplication + limite à 8
    seen = set()
    clean = []
    for q in queries:
        if q not in seen:
            seen.add(q)
            clean.append(q)
    return clean[:8]


# ── Point d'entrée ─────────────────────────────────────────────

def run(config, prompt_text):
    """
    Interprète le prompt utilisateur et met à jour config['preferences'].
    Essaie les LLMs dans l'ordre configuré, puis fallback regex.
    Returns: config mise à jour.
    """
    llm_config = config.get("llm", {})
    provider = llm_config.get("provider", "ollama")
    api_config = config.get("api", {})

    full_prompt = f"{SYSTEM_PROMPT}\n\nUser: {prompt_text}\nResponse:"

    result = None

    # Mapping provider → (config_key, default_model, base_url)
    PROVIDERS = {
        "openai":       ("openai",      "gpt-5.4-mini",       "https://api.openai.com/v1"),
        "mistral":      ("mistral",     "mistral-small-2506", "https://api.mistral.ai/v1"),
        "deepseek":     ("deepseek",    "deepseek-v4-flash",   "https://api.deepseek.com/v1"),
        "openrouter":   ("openrouter",  "openai/gpt-5.4-mini",  "https://openrouter.ai/api/v1"),
        "groq":         ("groq",        "llama-3.3-70b-versatile", "https://api.groq.com/openai/v1"),
        "custom":       ("custom",      "gpt-5.4-mini",         llm_config.get("base_url", "")),
    }

    if provider == "ollama":
        model = llm_config.get("model", "llama3.2")
        raw = _call_ollama(full_prompt, model)
        if raw:
            try:
                result = json.loads(raw)
            except json.JSONDecodeError:
                m = re.search(r'\{[^{}]+\}', raw)
                if m:
                    try:
                        result = json.loads(m.group())
                    except:
                        pass
        # Fallback automatique : si Ollama échoue, tenter le fallback configuré
        if not result:
            fb_provider = llm_config.get("fallback_provider", "")
            fb_model = llm_config.get("fallback_model", "mistral-small-2506")
            if fb_provider and fb_provider in PROVIDERS:
                key_name, default_model, base_url = PROVIDERS[fb_provider]
                key = api_config.get(key_name, {}).get("api_key", "")
                if key and base_url:
                    print(f"  " + _yellow(f"Ollama n'a pas répondu. Tentative {fb_provider}..."))
                    raw = _call_openai(full_prompt, key, fb_model, base_url=base_url)
                    if raw:
                        try:
                            result = json.loads(raw)
                        except:
                            pass
                    if result:
                        print("  " + _green(f"✅ Fallback {fb_provider} réussi."))

    elif provider in PROVIDERS:
        key_name, default_model, base_url = PROVIDERS[provider]
        key = api_config.get(key_name, {}).get("api_key", "")
        if key and base_url:
            model = llm_config.get("model", default_model)
            raw = _call_openai(full_prompt, key, model, base_url=base_url)
            if raw:
                try:
                    result = json.loads(raw)
                except:
                    pass

    # Fallback si aucun LLM n'a fonctionné
    if not result:
        print("  " + _yellow("Aucun LLM disponible -- fallback regex"))
        result = _regex_fallback(prompt_text)

    # Applique à la config
    if "preferences" not in config:
        config["preferences"] = {}
    prefs = config["preferences"]

    if result.get("search_queries"):
        prefs["search_queries"] = result["search_queries"]
    elif result.get("keywords"):
        prefs["search_queries"] = result["keywords"]

    if result.get("city") or result.get("locations"):
        loc = prefs.get("location", {})
        city = result.get("city") or (result["locations"][0] if result.get("locations") else "Paris")
        dept = result.get("department", "75")
        loc["city"] = city
        loc["department"] = dept
        prefs["location"] = loc

    if result.get("contract_types"):
        prefs["contract_types"] = result["contract_types"]

    if result.get("min_score"):
        config["matching"] = config.get("matching", {})
        config["matching"]["min_score"] = int(result["min_score"])

    if result.get("max_offer_age_days"):
        prefs["max_offer_age_days"] = int(result["max_offer_age_days"])

    if result.get("remote"):
        prefs["remote_preference"] = result["remote"]

    if result.get("categories"):
        prefs["categories"] = result["categories"]

    if result.get("priorities"):
        prefs["priorities"] = result["priorities"]

    return config
