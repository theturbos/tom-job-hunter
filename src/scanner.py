"""
scanner.py — Scan multi-sources : France Travail + SerpApi + Web fallback
Retourne une liste brute d'offres (dicts) pour le matcher.
"""
from src.colors import green as _green, red as _red, yellow as _yellow
from src.colors import cyan as _cyan, bold as _bold, dim as _dim


import re
import ssl
import time
import json
import hashlib
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timedelta

# ── France Travail API (même méthode auth que daily_scanner.py) ──

_FT_TOKEN_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=%2Fpartenaire"
_FT_SEARCH_URL = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"
_SSL_CTX = ssl.create_default_context()


def _ft_get_token(config):
    """Obtient un token OAuth2 France Travail."""
    api = config.get("api", {})
    cid = api.get("france_travail", {}).get("client_id", "")
    csec = api.get("france_travail", {}).get("client_secret", "")
    if not cid or not csec:
        return None
    try:
        body = f"grant_type=client_credentials&client_id={cid}&client_secret={csec}&scope=api_offresdemploiv2%20o2dsoffre"
        req = urllib.request.Request(
            _FT_TOKEN_URL,
            data=body.encode(),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urllib.request.urlopen(req, context=_SSL_CTX, timeout=15) as resp:
            raw_data = resp.read()
            if not raw_data:
                return None
            token = json.loads(raw_data).get("access_token")
            return token
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="ignore")
        print("  " + _yellow(f"France Travail auth: HTTP {e.code} — {body[:120]}"))
        return None


def _ft_search(config, keywords, departement="75"):
    """Recherche France Travail par mots-clés + code département."""
    token = _ft_get_token(config)
    if not token:
        return []
    prefs = config.get("preferences", {})
    max_age = prefs.get("max_offer_age_days", 21)
    params = f"motsCles={urllib.parse.quote(keywords)}&departement={departement}&range=0-149"
    url = f"{_FT_SEARCH_URL}?{params}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, context=_SSL_CTX, timeout=30) as resp:
            raw_data = resp.read()
            if not raw_data:
                print("  " + _yellow(f"France Travail: réponse vide pour '{keywords}'"))
                return []
            data = json.loads(raw_data)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="ignore")
        print("  " + _yellow(f"France Travail: HTTP {e.code} pour '{keywords}' — {body[:100]}"))
        return []
    except json.JSONDecodeError as e:
        print("  " + _yellow(f"France Travail: JSON invalide pour '{keywords}' — {str(e)[:80]}"))
        return []

    cutoff = datetime.now() - timedelta(days=max_age)
    results = []
    for r in data.get("resultats", []):
        pub = r.get("dateCreation", "")[:10]
        try:
            pub_dt = datetime.fromisoformat(pub)
            # Comparaison date-only: on garde si la date de publication > cutoff (date)
            # Ex: max_age=5, cutoff=14/05 → offres du 15/05+ gardées, 14/05- rejetées
            if pub_dt.date() <= cutoff.date():
                continue
        except (ValueError, TypeError):
            pass

        location = r.get("lieuxTravail", [{}])[0].get("libelle", "") if r.get("lieuxTravail") else ""
        results.append({
            "id": _make_id(r.get("originPartnerId", r.get("id", "")), r.get("intitule", ""), r.get("entreprise", {}).get("nom", "")),
            "company": r.get("entreprise", {}).get("nom", "N/A"),
            "title": r.get("intitule", ""),
            "location": location,
            "date": pub,
            "url": r.get("origine", {}).get("urlOrigine", "") if isinstance(r.get("origine"), dict) else "",
            "description": (r.get("description", "") or "")[:1500],
            "contract": r.get("typeContrat", ""),
            "source": "FT",
        })
    return results


# ── SerpApi Google Jobs ────────────────────────────────────────

_SERPAPI_URL = "https://serpapi.com/search"


def _serpapi_search(config, query):
    """Recherche Google Jobs via SerpApi."""
    key = config.get("api", {}).get("serpapi", {}).get("api_key", "")
    if not key:
        return []
    loc = config.get("preferences", {}).get("location", {})
    city = loc.get("city", "Paris")
    country = loc.get("country", "France")

    params = urllib.parse.urlencode({
        "engine": "google_jobs",
        "q": query,
        "location": f"{city}, {country}",
        "gl": "fr",
        "hl": "fr",
        "api_key": key,
    })
    try:
        req = urllib.request.Request(f"{_SERPAPI_URL}?{params}")
        with urllib.request.urlopen(req, context=_SSL_CTX, timeout=30) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        print("  " + _yellow(f"SerpApi: {e}"))
        return []

    results = []
    for r in data.get("jobs_results", []):
        company = r.get("company_name", "N/A")
        title = r.get("title", "")
        loc_str = ", ".join(r.get("location", "")) if isinstance(r.get("location"), list) else (r.get("location", "") or "")
        via = r.get("via", "")
        url = r.get("related_links", [{}])[0].get("link", "") if r.get("related_links") else ""
        desc = r.get("description", "")[:500]
        source = "SerpApi"
        if "linkedin" in via.lower(): source = "LI"
        elif "welcome" in via.lower(): source = "WTTJ"
        elif "indeed" in via.lower(): source = "IN"
        elif "glassdoor" in via.lower(): source = "GD"
        elif "apec" in via.lower(): source = "AP"

        results.append({
            "id": _make_id("", title, company),
            "company": company,
            "title": title,
            "location": loc_str,
            "date": "",
            "url": url,
            "description": desc,
            "contract": _guess_contract(r.get("detected_extensions", {})),
            "source": source,
        })
    if not results:
        print("  " + _dim(f"(SerpApi: 0 résultats pour '{query[:30]}' — normal si quota épuisé ou marché calme)"))
    return results


# ── Web fallback : APIs ATS publiques ─────────────────────────

# Mapping étendu : entreprise → (ats_type, ats_id, secteurs associés)
# Les secteurs servent à filtrer dynamiquement selon la config utilisateur.
_CAREERS_ATS_EXTENDED = [
    # Format: (company, ats_type, ats_id, [sector_keywords])
    # IA / Tech
    ("Mistral AI",      "lever",       "mistral",     ["ia", "ai", "tech", "saas"]),
    ("Hugging Face",    "greenhouse",  "huggingface", ["ia", "ai", "tech", "opensource"]),
    ("Poolside",        "lever",       "poolside",    ["ia", "ai", "tech", "saas"]),
    ("PhotoRoom",       "lever",       "photoroom",   ["ia", "ai", "tech", "saas"]),
    ("Dust",            "lever",       "dust",        ["ia", "ai", "tech", "saas"]),
    # Finance / Fintech
    ("Alan",            "lever",       "alan",        ["finance", "fintech", "assurance", "santé"]),
    ("Qonto",           "lever",       "qonto",       ["finance", "fintech", "banque", "saas"]),
    ("Pennylane",       "lever",       "pennylane",   ["finance", "fintech", "comptabilité", "saas"]),
    ("Payfit",          "lever",       "payfit",      ["finance", "fintech", "rh", "saas"]),
    ("Swile",           "lever",       "swile",       ["finance", "fintech", "rh", "saas"]),
    ("Spendesk",        "lever",       "spendesk",    ["finance", "fintech", "saas"]),
    # SaaS / Scale-ups
    ("Doctolib",        "lever",       "doctolib",    ["santé", "health", "saas", "tech"]),
    ("Back Market",     "lever",       "backmarket",  ["saas", "tech", "ecommerce"]),
    ("Mirakl",          "lever",       "mirakl",      ["saas", "tech", "marketplace"]),
    ("Contentsquare",   "lever",       "contentsquare", ["saas", "tech", "analytics"]),
    ("Aircall",         "lever",       "aircall",     ["saas", "tech", "télécom"]),
    # Conseil / Services
    ("Dataiku",         "lever",       "dataiku",     ["data", "ia", "ai", "conseil", "saas"]),
    ("Shift Technology","lever",       "shifttechnology", ["ia", "ai", "assurance", "conseil"]),
]

_ATS_GREENHOUSE_BASE = "https://boards-api.greenhouse.io/v1/boards"
_ATS_LEVER_BASE = "https://api.lever.co/v0/postings"


def _get_ats_targets(config):
    """Sélectionne les entreprises ATS pertinentes selon les secteurs configurés.
    
    Logique:
    1. Si l'utilisateur a configuré des secteurs → priorise les entreprises qui matchent
    2. Sinon, retourne les 8 premières (IA + Finance par défaut)
    3. Toujours inclure Mistral AI, Hugging Face, Alan, Qonto (piliers FR)
    """
    prefs = config.get("preferences", {})
    sectors = prefs.get("sectors", [])
    if not sectors:
        # Déduit des search_queries
        sq = prefs.get("search_queries", [])
        sectors_text = ' '.join(sq).lower()
        sectors = [w for w in sectors_text.replace(',', ' ').split() if len(w) > 2][:4]
    
    if not sectors:
        # Défaut : IA + Finance
        return [(c, t, i) for c, t, i, _ in _CAREERS_ATS_EXTENDED[:8]]
    
    sectors_low = [s.lower().strip() for s in sectors]
    
    # Score chaque entreprise par nombre de secteurs matchés
    scored = []
    for company, ats_type, ats_id, keywords in _CAREERS_ATS_EXTENDED:
        score = 0
        for kw in keywords:
            for sector in sectors_low:
                if sector in kw or kw in sector:
                    score += 2
                elif any(s in kw for s in sector.split()) or any(k in sector for k in kw.split()):
                    score += 1
        # Bonus pour les piliers FR (toujours inclus avec un petit boost)
        if company in ("Mistral AI", "Hugging Face", "Alan", "Qonto"):
            score += 5
        scored.append((company, ats_type, ats_id, score))
    
    # Trie par score décroissant, prend les 8 meilleurs
    scored.sort(key=lambda x: x[3], reverse=True)
    return [(c, t, i) for c, t, i, _ in scored[:8]]


def _web_search_careers(config):
    """Fetch les offres depuis les APIs ATS publiques des scale-ups.
    
    Utilise les API Lever et Greenhouse (gratuites, pas d'auth)
    pour récupérer les offres en temps réel.
    """
    results = []
    urls_seen = set()
    location_filter = config.get("preferences", {}).get("location", {}).get("city", "Paris")
    
    targets = _get_ats_targets(config)
    for company, ats_type, ats_id in targets:
        try:
            if ats_type == "lever":
                url = f"{_ATS_LEVER_BASE}/{ats_id}?mode=json"
            elif ats_type == "greenhouse":
                url = f"{_ATS_GREENHOUSE_BASE}/{ats_id}/jobs?content=true"
            else:
                continue
            
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "TomJobHunter/2.0"},
            )
            with urllib.request.urlopen(req, context=_SSL_CTX, timeout=12) as resp:
                data = json.loads(resp.read())
            
            if ats_type == "lever":
                postings = data if isinstance(data, list) else []
                for p in postings:
                    location = p.get("categories", {}).get("location", "")
                    # Filtre basique : Paris, France, Remote
                    if not _location_matches(location, location_filter):
                        continue
                    title = p.get("text", "")
                    link = p.get("hostedUrl", p.get("applyUrl", ""))
                    if not title or not link:
                        continue
                    if link in urls_seen:
                        continue
                    urls_seen.add(link)
                    results.append({
                        "id": _make_id("", title, company),
                        "company": company,
                        "title": title,
                        "location": location,
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "url": link,
                        "description": p.get("descriptionPlain", "")[:1500],
                        "contract": "",
                        "source": "ATS",
                    })
            
            elif ats_type == "greenhouse":
                jobs = data.get("jobs", []) if isinstance(data, dict) else []
                for j in jobs:
                    loc = str(j.get("location", {}).get("name", "")) if isinstance(j.get("location"), dict) else str(j.get("location", ""))
                    if not _location_matches(loc, location_filter):
                        continue
                    title = j.get("title", "")
                    link = j.get("absolute_url", "")
                    if not title or not link:
                        continue
                    if link in urls_seen:
                        continue
                    urls_seen.add(link)
                    # Greenhouse a le contenu dans content
                    desc = ""
                    if j.get("content"):
                        desc = str(j["content"])[:1500]
                    results.append({
                        "id": _make_id("", title, company),
                        "company": company,
                        "title": title,
                        "location": loc,
                        "date": j.get("updated_at", datetime.now().strftime("%Y-%m-%d"))[:10],
                        "url": link,
                        "description": desc,
                        "contract": "",
                        "source": "ATS",
                    })
        except Exception:
            pass
        time.sleep(0.3)
    
    return results


def _location_matches(location, city):
    """Vérifie si la localisation correspond à la ville cible (filtre souple)."""
    if not location:
        return True  # Si pas de location, on garde (peut-être remote)
    loc_low = location.lower()
    # Mots-clés qui indiquent que l'offre est pertinente pour Paris
    keywords = [
        city.lower(),  # "paris"
        "france", "remote", "europe", "emea",
        "île-de-france", "ile-de-france", "idf",
    ]
    for kw in keywords:
        if kw in loc_low:
            return True
    return False


# ── Helpers ────────────────────────────────────────────────────

def _make_id(ext_id, title, company):
    """Génère un ID unique par hash(entreprise + titre + mois)."""
    if ext_id and len(ext_id) > 5:
        return ext_id
    slug = re.sub(r'[^a-z0-9]+', '-', (company + "-" + title).lower()).strip("-")
    month = datetime.now().strftime("%Y-%m")
    h = hashlib.md5(f"{company}{title}{month}".encode()).hexdigest()[:8]
    return f"{slug[:40]}-{h}"


def _guess_contract(ext):
    if isinstance(ext, dict):
        contract = ext.get("contract_type", "") or ext.get("schedule", "")
        return str(contract)
    return ""


# ── Point d'entrée ─────────────────────────────────────────────

def scan_all(config):
    """Lance tous les scanners et retourne la liste brute d'offres."""
    prefs = config.get("preferences", {})
    location = prefs.get("location", {})
    dept = location.get("department", "75")

    # Split Cat A (Tech/IA) et Cat B (Secteur métier)
    priorities = prefs.get("priorities", [])
    # Nettoie les priorités — garantit 2 valeurs distinctes
    if not isinstance(priorities, list) or len(priorities) < 2 or priorities[0] == priorities[1]:
        if isinstance(priorities, list) and len(priorities) >= 1 and priorities[0]:
            priorities = [priorities[0], "Secteur"]
        else:
            priorities = ["IA & Stratégie", "Secteur"]
    # Unicité forcée
    if priorities[0] == priorities[1]:
        priorities[1] = "Secteur"
    cat_a_label = priorities[0] if priorities[0] else "IA & Stratégie"
    cat_b_label = priorities[1] if priorities[1] else "Secteur"

    queries = prefs.get("search_queries", [
        "AI Strategy", "Head of AI", "AI Product Manager",
        "AI Transformation", "FP&A AI", "Finance Transformation"
    ])

    # Construit les queries Cat A (IA/tech) et Cat B (secteur métier)
    # Cat A = queries contenant des signaux IA
    ia_signals = ["ai", "ia", "llm", "data", "tech", "ml ", "python", "nlp", "rag",
                  "intelligence", "machine learning", "deep learning", "automatisation"]
    q_a = [q for q in queries if any(s in q.lower() for s in ia_signals)]
    q_b = [q for q in queries if q not in q_a]
    # Fallback intelligent si l'un des deux est vide
    if not q_a and cat_a_label and cat_a_label != cat_b_label:
        # Utilise le label Cat A comme query de secours (ex: "IA & Stratégie")
        q_a = [cat_a_label]
    if not q_b and cat_b_label and cat_b_label != cat_a_label:
        q_b = [cat_b_label]
    # Fallback ultime : duplique
    if not q_a:
        q_a = queries[:2] if len(queries) >= 2 else (["AI Strategy"] if not queries else queries[:1])
    if not q_b:
        q_b = queries[2:4] if len(queries) >= 4 else (["Finance"] if len(queries) <= 2 else queries[1:3])

    print("\n" + _cyan(" 🔍 Scan des offres... "))
    all_offers = []

    # 1) France Travail — 2 requêtes Cat A + 2 requêtes Cat B
    print(f"  📡 France Travail...  {_dim('Cat A: ' + cat_a_label[:20] + ' / Cat B: ' + cat_b_label[:20])}")
    if cat_a_label == cat_b_label:
        print(f"  {_yellow('⚠️  Priorités identiques — modifiez-les dans [8] > [M] > [15]')}")
    ft_results = []
    for q in q_a[:2]:
        ft_results += _ft_search(config, q, dept)
        time.sleep(0.5)
    for q in q_b[:2]:
        ft_results += _ft_search(config, q, dept)
        time.sleep(0.5)
    print(f"  {_green(str(len(ft_results)) + ' offres')}")
    all_offers += ft_results

    # 2) SerpApi Google Jobs — smart: 1 requête, skip 2e si 0 résultats (économise quota)
    print("  📡 SerpApi (Google Jobs)...", end=" ", flush=True)
    sa_results = []
    if q_a:
        sa_results += _serpapi_search(config, q_a[0])
        time.sleep(1)
    if q_b and (not q_a or sa_results):  # skip B si A déjà vide
        sa_results += _serpapi_search(config, q_b[0])
        time.sleep(1)
    print(f"  {_green(str(len(sa_results)) + ' offres')}")
    all_offers += sa_results

    # 3) Web fallback
    print("  📡 Web fallback (careers pages)...", end=" ", flush=True)
    web_results = _web_search_careers(config)
    print(f"  {_green(str(len(web_results)) + ' offres')}")
    all_offers += web_results

    # Déduplication intelligente
    unique = _dedup_offers(all_offers, config)

    print(f"\n  ✅ Total brut: {len(all_offers)} → Unique: {len(unique)}")
    return unique


# ── Déduplication intelligente ─────────────────────────────────

def _normalize_title(title):
    """Normalise un titre pour comparaison."""
    import unicodedata
    title = title.lower().strip()
    title = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode('ascii')
    # Supprime le contenu entre parenthèses AVANT la suppression de ponctuation
    # Ex: "Consultant(e)" → "Consultant" (pas "consultante")
    title = re.sub(r'\([^)]*\)', '', title)
    # Supprime les stop words de comparaison
    for word in ['le ', 'la ', 'les ', 'de ', 'du ', 'des ', 'un ', 'une ', 'the ', 'a ', 'an ',
                 'senior ', 'junior ', 'confirmed ', 'confirme ', 'h/f', '(h/f)', 'f/h', '(f/h)']:
        title = title.replace(word, '')
    # Supprime ponctuation et espaces multiples
    title = re.sub(r'[^\w\s]', '', title)
    title = re.sub(r'\s+', ' ', title).strip()
    return title


def _similarity(a, b):
    """Similarité de Jaccard sur les mots, entre 0 et 1."""
    words_a = set(a.split())
    words_b = set(b.split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a.intersection(words_b)
    union = words_a.union(words_b)
    return len(intersection) / len(union) if union else 0.0


def _is_duplicate_title(title, existing_titles, threshold=0.85):
    """Vérifie si un titre est un doublon d'un titre existant (similarité > threshold)."""
    norm = _normalize_title(title)
    for existing_title in existing_titles:
        existing_norm = _normalize_title(existing_title)
        # Identique → doublon immédiat
        if norm == existing_norm:
            return True
        # Similarité floue
        if _similarity(norm, existing_norm) >= threshold:
            return True
    return False


def _dedup_offers(offers, config):
    """Déduplication multi-niveaux : ID hash + URL canonique + similarité titre.
    
    Règles strictes (dans l'ordre) :
    1. Même ID hash → doublon immédiat
    2. Même URL → doublon immédiat
    3. Même entreprise + titre similaire >85% → doublon (sauf si >45 jours)
    4. Titre très similaire >90% sans entreprise → doublon suspect (conservé mais loggé)
    """
    import hashlib
    seen_ids = set()
    seen_urls = set()
    seen_titles_by_company = {}  # {company: {title: date}}
    unique = []
    doublons = []

    # Construit le hash d'URL pour comparaison
    def _url_key(url):
        return hashlib.md5(url.encode()).hexdigest()[:16] if url else ""

    for o in sorted(offers, key=lambda x: x.get('date', ''), reverse=True):
        oid = o.get('id', '')
        url = o.get('url', '')
        company = o.get('company', '').lower().strip()
        title = o.get('title', '')
        date_str = o.get('date', '')

        # Règle 1 : Même ID hash
        if oid and oid in seen_ids:
            doublons.append(o)
            continue

        # Règle 2 : Même URL canonique
        url_key = _url_key(url)
        if url_key and url_key in seen_urls:
            doublons.append(o)
            continue

        # Règle 3 : Même entreprise + titre similaire >85%
        if company and company in seen_titles_by_company:
            existing_titles = seen_titles_by_company[company]
            if _is_duplicate_title(title, list(existing_titles.keys()), 0.85):
                # Vérifie le délai de grâce (45 jours)
                is_new = True
                for existing_title, existing_date in existing_titles.items():
                    if _similarity(_normalize_title(title), _normalize_title(existing_title)) >= 0.85:
                        try:
                            d1 = datetime.strptime(date_str[:10], '%Y-%m-%d')
                            d2 = datetime.strptime(existing_date[:10], '%Y-%m-%d')
                            if abs((d1 - d2).days) < 45:
                                is_new = False
                                break
                        except (ValueError, TypeError):
                            is_new = False
                            break
                if not is_new:
                    doublons.append(o)
                    continue

        # Accepté
        if oid:
            seen_ids.add(oid)
        if url_key:
            seen_urls.add(url_key)
        if company:
            if company not in seen_titles_by_company:
                seen_titles_by_company[company] = {}
            seen_titles_by_company[company][title] = date_str
        unique.append(o)

    if doublons:
        print(f"  {_dim(f'♻️  {len(doublons)} doublons filtrés (IDS + URLs + similarité titre)')}")

    return unique
