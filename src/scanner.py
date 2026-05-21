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
            return json.loads(resp.read()).get("access_token")
    except Exception as e:
        print("  " + _yellow(f"France Travail token: {e}"))
        return None


def _ft_search(config, keywords, departement="75"):
    """Recherche France Travail par mots-clés + code département."""
    token = _ft_get_token(config)
    if not token:
        return []
    prefs = config.get("preferences", {})
    max_age = prefs.get("max_offer_age_days", 10)
    params = f"motsCles={urllib.parse.quote(keywords)}&departement={departement}&range=0-149"
    url = f"{_FT_SEARCH_URL}?{params}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, context=_SSL_CTX, timeout=30) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        print("  " + _yellow(f"France Travail search: {e}"))
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
    return results


# ── Web fallback : APIs ATS publiques ─────────────────────────

# Entreprises françaises avec API ATS publique (Lever / Greenhouse / TeamTailor)
# Ces APIs sont gratuites et ne nécessitent pas d'auth.
_CAREERS_ATS = [
    # Format: (company, ats_type, ats_id)
    ("Mistral AI",      "lever",       "mistral"),
    ("Hugging Face",    "greenhouse",  "huggingface"),
    ("Alan",            "lever",       "alan"),
    ("Qonto",           "lever",       "qonto"),
    ("Pennylane",       "lever",       "pennylane"),
    ("Payfit",          "lever",       "payfit"),
    ("Eleven Labs",     "greenhouse",  "elevenlabs"),
    ("Poolside",        "lever",       "poolside"),
]

_ATS_GREENHOUSE_BASE = "https://boards-api.greenhouse.io/v1/boards"
_ATS_LEVER_BASE = "https://api.lever.co/v0/postings"


def _web_search_careers(config):
    """Fetch les offres depuis les APIs ATS publiques des scale-ups.
    
    Utilise les API Lever et Greenhouse (gratuites, pas d'auth)
    pour récupérer les offres en temps réel.
    """
    results = []
    urls_seen = set()
    location_filter = config.get("preferences", {}).get("location", {}).get("city", "Paris")
    
    for company, ats_type, ats_id in _CAREERS_ATS[:6]:  # Limite à 6 entreprises
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
    priorities = prefs.get("priorities", ["IA & Stratégie", "Secteur"])
    cat_a_label = priorities[0] if len(priorities) > 0 else "IA & Stratégie"
    cat_b_label = priorities[1] if len(priorities) > 1 else "Secteur"

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
    ft_results = []
    for q in q_a[:2]:
        ft_results += _ft_search(config, q, dept)
        time.sleep(0.5)
    for q in q_b[:2]:
        ft_results += _ft_search(config, q, dept)
        time.sleep(0.5)
    print(f"  {_green(str(len(ft_results)) + ' offres')}")
    all_offers += ft_results

    # 2) SerpApi Google Jobs — 1 requête Cat A + 1 requête Cat B
    print("  📡 SerpApi (Google Jobs)...", end=" ", flush=True)
    sa_results = []
    if q_a:
        sa_results += _serpapi_search(config, q_a[0])
        time.sleep(1)
    if q_b:
        sa_results += _serpapi_search(config, q_b[0])
        time.sleep(1)
    print(f"  {_green(str(len(sa_results)) + ' offres')}")
    all_offers += sa_results

    # 3) Web fallback
    print("  📡 Web fallback (careers pages)...", end=" ", flush=True)
    web_results = _web_search_careers(config)
    print(f"  {_green(str(len(web_results)) + ' offres')}")
    all_offers += web_results

    # Déduplication
    seen = set()
    unique = []
    for o in all_offers:
        oid = o.get("id", "")
        if oid not in seen:
            seen.add(oid)
            unique.append(o)

    print(f"\n  ✅ Total brut: {len(all_offers)} → Unique: {len(unique)}")
    return unique
