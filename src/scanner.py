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

_FT_TOKEN_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token"
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
        print(f"  " + _yellow("France Travail token: {e}"))
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
        print(f"  " + _yellow("France Travail search: {e}"))
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
        print(f"  " + _yellow("SerpApi: {e}"))
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


# ── Web Search fallback ────────────────────────────────────────

def _web_search_careers(config):
    """Recherche web brute sur les pages careers des scale-ups."""
    queries = config.get("preferences", {}).get("search_queries", [])
    if not queries:
        queries = ["AI Strategy Paris", "Head of AI Paris", "AI Product Manager Paris"]

    results = []
    urls_seen = set()
    for q in queries[:3]:
        query = f"{q} site:welcometothejungle.com OR site:linkedin.com/jobs OR site:indeed.fr"
        try:
            enc_q = urllib.parse.urlencode({"q": query})
            req = urllib.request.Request(
                f"https://html.duckduckgo.com/html/?{enc_q}",
                headers={"User-Agent": "Mozilla/5.0"},
            )
            with urllib.request.urlopen(req, context=_SSL_CTX, timeout=15) as resp:
                text = resp.read().decode("utf-8", errors="ignore")
            import html
            for a in re.findall(r'<a rel="nofollow" class="result__a" href="([^"]+)">', text):
                a = html.unescape(a)  # décode &amp; → &, &#x27; → ', etc.
                if a in urls_seen:
                    continue
                urls_seen.add(a)
                company = _extract_company(a)
                title = _extract_title(a)
                if not title:
                    continue
                results.append({
                    "id": _make_id("", title, company),
                    "company": company,
                    "title": title,
                    "location": "Paris",
                    "date": "",
                    "url": a,
                    "description": "",
                    "contract": "",
                    "source": "Web",
                })
        except Exception:
            pass
        time.sleep(1.5)
    return results


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


def _extract_company(url):
    parts = url.replace("https://", "").replace("http://", "").split("/")
    if "linkedin" in url:
        m = re.search(r'company/([^/?]+)', url)
        if m:
            return m.group(1).replace("-", " ").title()
    if "welcometothejungle" in url:
        m = re.search(r'/companies/([^/?]+)', url)
        if m:
            return m.group(1).replace("-", " ").title()
    return parts[0].replace("www.", "").split(".")[0].title() if parts else ""


def _extract_title(url):
    parts = url.rstrip("/").split("/")
    for p in reversed(parts):
        if len(p) > 10 and not p.startswith("?") and p not in ("jobs", "emploi", "careers"):
            return p.replace("-", " ").replace("_", " ").title()
    return ""


# ── Point d'entrée ─────────────────────────────────────────────

def scan_all(config):
    """Lance tous les scanners et retourne la liste brute d'offres."""
    prefs = config.get("preferences", {})
    location = prefs.get("location", {})
    dept = location.get("department", "75")
    queries = prefs.get("search_queries", [
        "AI Strategy", "Head of AI", "AI Product Manager",
        "AI Transformation", "FP&A AI", "Finance Transformation"
    ])

    print("\n" + _cyan(" 🔍 Scan des offres... "))
    all_offers = []

    # 1) France Travail
    print("  📡 France Travail...", end=" ", flush=True)
    ft_results = []
    for q in queries[:4]:
        ft_results += _ft_search(config, q, dept)
        time.sleep(0.5)
    print(f"  {_green(str(len(ft_results)) + ' offres')}")
    all_offers += ft_results

    # 2) SerpApi Google Jobs
    print("  📡 SerpApi (Google Jobs)...", end=" ", flush=True)
    sa_results = []
    for q in queries[:2]:
        sa_results += _serpapi_search(config, q)
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
