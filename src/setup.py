"""
setup.py — Wizard de configuration interactif
Guide l'utilisateur pas à pas pour créer data/config.yaml

Commandes :
  python bot.py setup   → Wizard interactif
  python bot.py guide   → Guide explicatif pour débutants
"""
from src.colors import green as _green, red as _red, yellow as _yellow
from src.colors import cyan as _cyan, bold as _bold, dim as _dim, bar as _make_bar

import os
import sys
import yaml
from pathlib import Path

CONFIG_PATH = Path("data/config.yaml")

BAR = _make_bar()


def _pick_file(title, filetypes):
    """Tente d'ouvrir un sélecteur de fichier natif.
    Retourne le chemin ou None si indisponible/annulé."""
    import subprocess
    try:
        # Windows: PowerShell
        if sys.platform == "win32":
            ps = f"Add-Type -AssemblyName System.Windows.Forms; $f = New-Object System.Windows.Forms.OpenFileDialog; $f.Title = '{title}'; $f.Filter = '{filetypes[0][1]}|{filetypes[0][1]}'; $f.ShowDialog(); $f.FileName"
            r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=30)
            path = r.stdout.strip()
            if path and Path(path).exists():
                return path
        # macOS: osascript
        elif sys.platform == "darwin":
            # UTI pour .docx = "org.openxmlformats.wordprocessingml.document"
            uti = "org.openxmlformats.wordprocessingml.document"
            script = f'choose file with prompt "{title}" of type {{"{uti}"}}'
            r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=30)
            if r.stdout.strip():
                # osascript returns "alias MacHD:Users:..." or POSIX path
                raw = r.stdout.strip()
                if raw.startswith("alias "):
                    r2 = subprocess.run(["osascript", "-e", f'POSIX path of ({raw})'],
                                        capture_output=True, text=True, timeout=5)
                    path = r2.stdout.strip()
                else:
                    path = raw
                if path and Path(path).exists():
                    return path
        # Linux: zenity
        else:
            ft = ' '.join(f'--file-filter="{t[0]} | {t[1]}"' for t in filetypes)
            r = subprocess.run(f'zenity --file-selection --title="{title}" {ft} 2>/dev/null',
                               shell=True, capture_output=True, text=True, timeout=30)
            path = r.stdout.strip()
            if path and Path(path).exists():
                return path
    except Exception:
        pass
    return None


def _ask(prompt, default="", required=False, choices=None, hint="", t=None):
    """Pose une question et retourne la réponse.
    hint: affiché sous la question (ex: "Utilisé pour vos lettres de motivation").
    t: dictionnaire de textes traduits (pour les messages d'erreur)."""
    if t is None:
        t = {}
    suffix = ""
    req_mark = ""
    if required:
        req_mark = f" {_red(t.get('required_mark', '*obligatoire'))}"
        if hint:
            print(f"  {_dim('↳ ' + hint)}")
    if default:
        suffix = f" {_dim(f'[{default}]')}"
    if choices:
        options_str = '/'.join(choices)
        suffix = f" {_dim('(' + options_str + ')')}"

    while True:
        try:
            ans = input(f"  {prompt}{req_mark}{suffix} : ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            sys.exit(0)

        if not ans and default:
            return default
        if not ans and required:
            print(f"    {_red(t.get('answer_required', 'Réponse requise.'))}")
            continue
        if choices and ans.lower() not in [c.lower() for c in choices]:
            opts_str = ', '.join(choices)
            msg = t.get('invalid_choice', 'Choix invalide. Options :')
            print(f"    {_red(f'{msg} {opts_str}')}")
            continue
        return ans


def show_guide():
    """Affiche un guide détaillé pour les utilisateurs perdus."""
    print(f"\n{BAR}")
    print(f"  {_bold('🧭 GUIDE — TOM V2.0 pour les débutants')}")
    print(f"{BAR}\n")

    sections = [
        ("🤔 C'est quoi TOM ?", [
            "TOM est un assistant de recherche d'emploi qui :",
            "  1. Scanne les offres sur plusieurs sites (France Travail, Google Jobs, etc.)",
            "  2. Filtre et note les offres selon VOS critères",
            "  3. Génère des lettres de motivation personnalisées",
            "  4. Vous aide à suivre vos candidatures",
        ]),
        ("📋 Lexique", [
            _bold("Offre") + " = une annonce d'emploi trouvée par TOM",
            _bold("Score") + " = note de 1 à 10 (10 = parfait pour vous)",
            _bold("Cat A") + " = postes Tech / IA / Data (ex: Head of AI, ML Engineer)",
            _bold("Cat B") + " = tout le reste (ex: Supply Chain, Marketing, Finance hors IA)",
            _bold("Scan") + " = TOM va chercher les nouvelles offres",
            _bold("Prompt") + " = une phrase qui décrit ce que vous cherchez",
            _bold("Lettre") + " = lettre de motivation générée automatiquement",
            "",
            "  " + _dim('Exemple de prompt :'),
            "  " + _cyan('→ "Chef de projet marketing digital dans l\'automobile à Marseille"'),
        ]),
        ("🎯 Écrire un bon prompt", [
            "Votre prompt, c'est la phrase magique qui dit à TOM ce que vous cherchez.",
            "",
            _bold("Un bon prompt contient :"),
            "  1. Le poste voulu",
            "  2. Le secteur (optionnel mais recommandé)",
            "  3. La ville",
            "  4. Le type de contrat (CDI, Freelance...)",
            "",
            _bold("Exemples de prompts :"),
            "  " + _cyan('① "Head of AI en finance à Paris, CDI"'),
            "  " + _cyan('② "Directeur marketing dans l\'automobile à Marseille"'),
            "  " + _cyan('③ "Supply Chain Manager dans le luxe à Orléans, CDI"'),
            "  " + _cyan('④ "Data Analyst secteur santé à Lyon, hybride"'),
            "  " + _cyan('⑤ "AI Product Manager scale-up Paris"'),
            "  " + _cyan('⑥ "Consultant en stratégie IT, freelance, Île-de-France"'),
            "",
            _bold("Astuces :"),
            "  • Soyez précis sur le poste : pas 'un job', mais 'Head of AI'",
            "  • Mentionnez le secteur si vous voulez filtrer (finance, luxe, auto...)",
            "  • La ville est OBLIGATOIRE pour le scan France Travail",
            "  • Vous pouvez changer de prompt à tout moment avec l'option [9]",
        ]),
        ("🤖 Choisir son IA (Ollama, Mistral, OpenAI)", [
            _bold("Ollama (local, gratuit)"),
            "  ✅ Gratuit, données 100% privées sur votre machine",
            "  ✅ Pas besoin d'internet une fois le modèle téléchargé",
            "  ⚠️  NÉCESSITE une carte graphique avec 4+ Go de VRAM (ou 16+ Go RAM)",
            "  ⚠️  Le premier téléchargement du modèle prend 5-15 minutes (2-8 Go)",
            "  ⚠️  Les lettres sont plus lentes (30-90 sec par lettre)",
            "  ⚠️  Ne fonctionne PAS sur les petites machines (4 Go RAM, sans GPU)",
            "  ➜ Installation : " + _yellow("https://ollama.com/download"),
            "",
            _bold("Mistral AI (cloud, français 🇫🇷)"),
            "  ✅ Entreprise française, RGPD-friendly",
            "  ✅ Tier gratuit généreux (~1M tokens/mois)",
            "  ✅ Rapide (2-5 sec par lettre)",
            "  ⚠️  Nécessite une connexion internet",
            "  ➜ Inscription : " + _yellow("https://console.mistral.ai/"),
            "",
            _bold("OpenAI (cloud, le plus puissant)"),
            "  ✅ Meilleure qualité de lettres",
            "  ✅ Très rapide",
            "  ⚠️  Payant (quelques centimes par lettre)",
            "  ⚠️  Données envoyées aux US",
            "  ➜ Inscription : " + _yellow("https://platform.openai.com/"),
            "",
            _bold("Aucun (template seul)"),
            "  ✅ Zéro dépendance externe",
            "  ⚠️  Lettres génériques, peu personnalisées",
            "  ⚠️  Pas de parsing intelligent des prompts",
        ]),
        ("🔑 Les APIs de scan", [
            _bold("France Travail (gratuit, obligatoire)"),
            "  C'est LA source principale : 500 000+ offres en France.",
            "  Inscription gratuite en 2 minutes sur emploi-store.fr.",
            "  Sans cette API, TOM ne peut pas scanner les offres françaises.",
            "  ➜ " + _yellow("https://www.emploi-store.fr/portail/"),
            "",
            _bold("SerpApi Google Jobs (gratuit 100 req/mois)"),
            "  Agrège LinkedIn, Welcome to the Jungle, Indeed, Glassdoor, Apec...",
            "  100 requêtes gratuites par mois (~3 scans quotidiens).",
            "  Optionnel mais recommandé pour élargir la couverture.",
            "  ➜ " + _yellow("https://serpapi.com/"),
        ]),
        ("🚀 Prochaines étapes", [
            "1. Lancez le wizard : " + _cyan("python bot.py setup"),
            "2. Configurez votre profil et vos APIs",
            "3. Lancez votre premier scan avec l'option [1]",
            "4. Consultez vos offres avec l'option [3]",
            "5. Générez des lettres avec l'option [7]",
            "",
            _dim("À tout moment, tapez [9] pour changer vos critères de recherche."),
        ]),
    ]

    for i, (title, lines) in enumerate(sections, 1):
        print(f"  {_bold(f'{i}. {title}')}")
        for line in lines:
            print(f"    {line}")
        print()

    print(f"{BAR}")
    ans = input(f"  {_dim('Lancer le wizard de configuration ? [y/n] : ')}").strip().lower()
    if ans in ('y', 'yes', 'oui'):
        run_wizard()
    else:
        cmd_msg = f"Lancez {_cyan('python bot.py help')} pour voir toutes les options."
        print(f"  {_dim(cmd_msg)}")
    print()


# ── Tests API (utilisés pendant l'onboarding) ──────────────

def _test_ft_keys(client_id, client_secret):
    """Teste les identifiants France Travail. Retourne (ok, message)."""
    import urllib.request, json, ssl
    try:
        body = f"grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}&scope=api_offresdemploiv2%20o2dsoffre"
        req = urllib.request.Request(
            "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=%2Fpartenaire",
            data=body.encode(),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urllib.request.urlopen(req, context=ssl.create_default_context(), timeout=10) as resp:
            data = json.loads(resp.read())
            if data.get("access_token"):
                return True, "Token obtenu — identifiants valides"
            return False, data.get("error_description", "Erreur inconnue")
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="ignore")
        try:
            msg = json.loads(body).get("error_description", f"HTTP {e.code}")
        except:
            msg = f"HTTP {e.code}"
        return False, msg[:120]
    except Exception as e:
        return False, str(e)[:120]


def _test_serpapi_key(api_key):
    """Teste une clé SerpApi. Retourne (ok, message)."""
    import urllib.request, json
    try:
        url = f"https://serpapi.com/search?engine=google_jobs&q=test&api_key={api_key}"
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
            if data.get("search_metadata", {}).get("status") == "Success":
                return True, "Clé valide"
            return False, data.get("error", "Clé invalide")
    except Exception as e:
        return False, str(e)[:120]


def _test_llm_key(provider, api_key, base_url=None):
    """Teste une clé LLM (OpenAI-compatible). Retourne (ok, message)."""
    import urllib.request, json, ssl
    try:
        url = (base_url or f"https://api.{provider}.com/v1") + "/models"
        req = urllib.request.Request(
            url, headers={"Authorization": f"Bearer {api_key}"}
        )
        with urllib.request.urlopen(req, context=ssl.create_default_context(), timeout=10) as resp:
            if resp.status == 200:
                return True, f"Clé {provider} valide"
            return False, f"HTTP {resp.status}"
    except urllib.error.HTTPError as e:
        if e.code == 401:
            return False, "Clé invalide (HTTP 401)"
        return False, f"HTTP {e.code}"
    except Exception as e:
        return False, str(e)[:120]


def run_wizard(existing_config=None, lang="fr"):
    """Lance le wizard interactif."""
    config = existing_config or {}

    # Textes bilingues
    T = {
        "fr": {
            "title": "⚙️  TOM V2.0 — Configuration",
            "profile": "👤 Profil",
            "first_name": "Prénom",
            "last_name": "Nom de famille",
            "email": "Email",
            "linkedin": "LinkedIn URL",
            "phone": "Téléphone",
            "available": "Disponibilité",
            "priorities": "🎯 Catégories de recherche",
            "priorities_help1": "TOM recherche les offres dans DEUX catégories distinctes.",
            "priorities_help2": "Cat A = votre priorité Tech/IA. Cat B = votre secteur métier.",
            "priorities_help3": "Ex: Cat A 'IA & Stratégie' + Cat B 'Finance & Contrôle de gestion'",
            "priorities_help4": "\u26a0\ufe0f  Ce ne sont PAS des mots-clés — votre prompt détermine quelles offres remontent.",
            "priorities_help5": "Chaque catégorie génère ses propres requêtes API pour un scan ciblé.",
            "priorities_be_creative": "Soyez précis — ces catégories définissent CE que TOM va chercher.",
            "prio1_label": "Catégorie A — Tech & IA",
            "prio1_hint": "Votre priorité IA/tech. Ex: IA & Stratégie, Head of AI, IA & Finance, Data & Automatisation...",
            "prio2_label": "Catégorie B — Secteur métier",
            "prio2_hint": "Votre secteur ou fonction. Ex: Finance & Contrôle de gestion, Marketing Digital, Supply Chain, Conseil...",
            "skills": "🛠️  Vos compétences clés",
            "skills_help": "Séparez par des virgules. Ex: Python, LLM, RAG, FP&A, Power BI, SQL",
            "education": "🎓 Formation",
            "degree": "Diplôme principal",
            "school": "École / Université",
            "location": "📍 Localisation",
            "city": "Ville de recherche",
            "country": "Pays",
            "dept": "Code département",
            "criteria": "🎯 Critères de recherche",
            "prompt_label": "Recherche",
            "max_age": "Âge max des offres (jours)",
            "apis": "🔑 Configuration API",
            "llm": "🤖 Fournisseur IA",
            "cv": "📄 CV (.docx)",
            "template": "✉️  Template de lettre (.docx)",
            "saved": "✅ Configuration sauvegardée",
            "launch": "Lancez python bot.py pour commencer.",
        },
        "en": {
            "title": "⚙️  TOM V2.0 — Configuration",
            "profile": "👤 Profile",
            "first_name": "First name",
            "last_name": "Last name",
            "email": "Email",
            "linkedin": "LinkedIn URL",
            "phone": "Phone",
            "available": "Availability",
            "priorities": "🎯 Search categories",
            "priorities_help1": "TOM searches offers in TWO distinct categories.",
            "priorities_help2": "Cat A = your Tech/AI priority. Cat B = your industry/function.",
            "priorities_help3": "Ex: Cat A 'AI & Strategy' + Cat B 'Finance & Controlling'",
            "priorities_help4": "\u26a0\ufe0f  These are NOT keywords — your prompt determines which offers appear.",
            "priorities_help5": "Each category generates its own API queries for targeted scanning.",
            "priorities_be_creative": "Be specific — these categories define WHAT TOM searches for.",
            "prio1_label": "Category A — Tech & AI",
            "prio1_hint": "Your AI/tech priority. Ex: AI & Strategy, Head of AI, AI & Finance, Data & Automation...",
            "prio2_label": "Category B — Industry / Function",
            "prio2_hint": "Your sector or function. Ex: Finance & Controlling, Digital Marketing, Supply Chain, Consulting...",
            "skills": "🛠️  Key skills",
            "skills_help": "Separate with commas. Ex: Python, LLM, RAG, FP&A, Power BI, SQL",
            "education": "🎓 Education",
            "degree": "Main degree",
            "school": "School / University",
            "location": "📍 Location",
            "city": "Search city",
            "country": "Country",
            "dept": "Department code",
            "criteria": "🎯 Search criteria",
            "prompt_label": "Search",
            "max_age": "Max offer age (days)",
            "apis": "🔑 API Configuration",
            "llm": "🤖 AI Provider",
            "cv": "📄 Resume (.docx)",
            "template": "✉️  Cover letter template (.docx)",
            "saved": "✅ Configuration saved",
            "launch": "Run python bot.py to start.",
        }
    }
    t = T.get(lang, T["fr"])
    # Stocke la langue et version du format de config
    config["_lang"] = lang
    config["_config_version"] = 1

    print(f"\n{BAR}")
    print(f"  {_bold(t['title'])}")
    print(f"{BAR}\n")

    # ── 1. Profil ──────────────────────────────────────────────
    print(f"  {_bold(t['profile'])}")
    profile = config.get("profile", {})
    # Split name into first/last if possible
    existing_name = profile.get("name", "")
    existing_first = profile.get("first_name", existing_name.split()[0] if existing_name else "")
    existing_last = profile.get("last_name", " ".join(existing_name.split()[1:]) if len(existing_name.split()) > 1 else "")
    profile["first_name"] = _ask(t["first_name"], default=existing_first, required=True, hint="Utilisé dans vos lettres de motivation et sur votre CV")
    profile["last_name"] = _ask(t["last_name"], default=existing_last, required=True, hint="Utilisé dans vos lettres de motivation et sur votre CV")
    profile["name"] = f"{profile['first_name']} {profile['last_name']}"
    profile["email"] = _ask(t["email"], default=profile.get("email", ""), hint="Optionnel — ajouté à vos lettres si fourni")
    profile["linkedin"] = _ask(t["linkedin"], default=profile.get("linkedin", ""), hint="Optionnel — affiché sur votre CV et lettres")
    profile["phone"] = _ask(t["phone"], default=profile.get("phone", ""), hint="Optionnel — ajouté à vos lettres si fourni")
    profile["available"] = _ask(t["available"], default=profile.get("available", "Septembre 2026"), required=True, hint="Date à partir de laquelle vous êtes disponible (ex: Septembre 2026, Immédiat, 3 mois...)")
    config["profile"] = profile
    print()

    # ── 1b. Priorités de recherche ─────────────────────────────
    print(f"  {_bold(t['priorities'])}")
    print(f"  {_dim(t['priorities_help1'])}")
    print(f"  {_dim(t['priorities_help2'])}")
    print(f"  {_dim(t['priorities_help3'])}")
    print(f"  {_yellow('  ' + t['priorities_help4'])}")
    print(f"  {_dim(t['priorities_help5'])}")
    print()
    print(f"  {_dim(t['priorities_be_creative'])}")
    prio1 = _ask(t["prio1_label"], default="IA & Stratégie", required=True, hint=t["prio1_hint"], t=t)
    prio2 = _ask(t["prio2_label"], default="Finance & Contrôle de gestion", required=True, hint=t["prio2_hint"], t=t)
    prefs = config.get("preferences", {})
    prefs["priorities"] = [prio1, prio2]
    config["preferences"] = prefs
    print()

    # ── 1c. Skills ─────────────────────────────────────────────
    print(f"  {_bold(t['skills'])}")
    print(f"  {_dim(t['skills_help'])}")
    skills_raw = _ask("Skills", default=", ".join(profile.get("skills", [])), required=True, hint="Utilisé pour le matching avec les offres et dans vos lettres")
    profile["skills"] = [s.strip() for s in skills_raw.split(",") if s.strip()] if skills_raw else []
    print()

    # ── 1d. Éducation ──────────────────────────────────────────
    print(f"  {_bold(t['education'])}")
    edu1 = _ask(t["degree"], default=profile.get("education_main", ""), hint="Optionnel — mentionné dans vos lettres (ex: Master Stratégie, BBA Finance...)")
    edu2 = _ask(t["school"], default=profile.get("education_school", ""), hint="Optionnel — mentionné dans vos lettres")
    profile["education_main"] = edu1
    profile["education_school"] = edu2
    config["profile"] = profile
    print()

    # ── 2. Localisation ────────────────────────────────────────
    print(f"  {_bold(t['location'])}")
    location = config.get("preferences", {}).get("location", {})
    city = _ask(t["city"], default=location.get("city", "Paris"), required=True)
    country = _ask(t["country"], default=location.get("country", "France"))
    dept = _ask(t["dept"] + " (75=Paris, 45=Orléans, 92=Hauts-de-Seine...)", default=location.get("department", "75"))
    location = {"city": city, "country": country, "department": dept}
    config.setdefault("preferences", {})["location"] = location
    print()

    # ── 3. Critères de recherche ───────────────────────────────
    print(f"  {_bold(t['criteria'])}")
    prefs = config.get("preferences", {})
    print(f"  {_dim('Décrivez en langage naturel ce que vous cherchez :')}")
    print(f"  {_dim('Exemples de prompts :')}")
    ex1 = '\u2192 "Head of AI en finance \u00e0 Paris, CDI"'
    ex2 = '\u2192 "Directeur marketing dans l\'automobile \u00e0 Marseille, CDI"'
    ex3 = '\u2192 "Supply Chain Manager dans le luxe \u00e0 Orl\u00e9ans, CDI"'
    ex4 = '\u2192 "Data Analyst secteur sant\u00e9 \u00e0 Lyon, hybride"'
    ex5 = '\u2192 "Consultant en strat\u00e9gie IT, freelance, \u00cele-de-France"'
    ex6 = '\u2192 "Chef de projet digital mode et luxe \u00e0 Paris"'
    print('    ' + _cyan(ex1))
    print('    ' + _cyan(ex2))
    print('    ' + _cyan(ex3))
    print('    ' + _cyan(ex4))
    print('    ' + _cyan(ex5))
    print('    ' + _cyan(ex6))
    print()
    nl_prompt = _ask(t["prompt_label"], default=prefs.get("natural_language_prompt", ""))
    prefs["natural_language_prompt"] = nl_prompt

    max_age = _ask(t["max_age"], default=str(prefs.get("max_offer_age_days", 10)), hint="Les offres plus anciennes seront ignorées")
    prefs["max_offer_age_days"] = int(max_age) if max_age.isdigit() else 10
    config["preferences"] = prefs
    config.setdefault("matching", {})["min_score"] = 6  # Défaut, modifiable dans config
    print()

    # ── 4. APIs ────────────────────────────────────────────────
    print(f"  {_bold(t['apis'])}")
    api = config.get("api", {})

    # France Travail
    print(f"\n  {_cyan('France Travail API')} {_dim('(gratuit — emploi-store.fr)')}")
    setup_ft = _ask("Configurer France Travail ?", default="y", choices=["y", "n"])
    if setup_ft.lower() == "y":
        if not api.get("france_travail"):
            api["france_travail"] = {}
        print(f"\n  {_dim('Guide :')}")
        print(f"  1. Allez sur {_yellow('https://www.emploi-store.fr/portail/')}")
        print(f"  2. Créez un compte (gratuit)")
        print(f"  3. Dans 'Mes applications', créez une nouvelle application")
        print(f"  4. Choisissez l'API 'Offres d'emploi'")
        print(f"  5. Copiez le Client ID et Client Secret\n")
        api["france_travail"]["client_id"] = _ask("Client ID", default=api["france_travail"].get("client_id", ""))
        api["france_travail"]["client_secret"] = _ask("Client Secret", default=api["france_travail"].get("client_secret", ""))
        # Test les clés France Travail
        if api["france_travail"]["client_id"] and api["france_travail"]["client_secret"]:
            print(f"  {_dim('Test France Travail...')}", end=" ", flush=True)
            ok, msg = _test_ft_keys(api["france_travail"]["client_id"], api["france_travail"]["client_secret"])
            if ok:
                print(f"{_green('✅ ' + msg)}")
            else:
                print(f"{_red('❌ ' + msg)}")
                print(f"  {_dim('Vérifiez vos identifiants sur emploi-store.fr')}")
                retry = _ask("Réessayer ?", default="y", choices=["y", "n"])
                if retry.lower() == "y":
                    api["france_travail"]["client_id"] = _ask("Client ID", default="")
                    api["france_travail"]["client_secret"] = _ask("Client Secret", default="")
    print()

    # SerpApi
    print(f"  {_cyan('SerpApi (Google Jobs)')} {_dim('(100 req/mois gratuites)')}")
    setup_sa = _ask("Configurer SerpApi ?", default="y", choices=["y", "n"])
    if setup_sa.lower() == "y":
        if not api.get("serpapi"):
            api["serpapi"] = {}
        print(f"\n  {_dim('Guide :')}")
        print(f"  1. Allez sur {_yellow('https://serpapi.com/')}")
        print(f"  2. Créez un compte gratuit")
        print(f"  3. Copiez votre API key depuis le dashboard\n")
        api["serpapi"]["api_key"] = _ask("API Key", default=api["serpapi"].get("api_key", ""))
        # Test la clé SerpApi
        if api["serpapi"]["api_key"]:
            print(f"  {_dim('Test SerpApi...')}", end=" ", flush=True)
            ok, msg = _test_serpapi_key(api["serpapi"]["api_key"])
            if ok:
                print(f"{_green('✅ ' + msg)}")
            else:
                print(f"{_red('❌ ' + msg)}")
                retry = _ask("Réessayer ?", default="y", choices=["y", "n"])
                if retry.lower() == "y":
                    api["serpapi"]["api_key"] = _ask("API Key", default="")
    config["api"] = api
    print()

    # ── 5. LLM ─────────────────────────────────────────────────
    print(f"  {_bold(t['llm'])}")
    print(f"  {_dim('1 = Ollama (local, gratuit, privé)')}")
    print(f"  {_dim('2 = Mistral AI (français 🇫🇷, tier gratuit généreux)')}")
    print(f"  {_dim('3 = OpenAI (payant, meilleure qualité)')}")
    print(f"  {_dim('4 = DeepSeek (très bon marché, excellent en français)')}")
    print(f"  {_dim('5 = OpenRouter (agrège Claude, Gemini, GPT, etc.)')}")
    print(f"  {_dim('6 = Groq (ultra-rapide, gratuit limité)')}")
    print(f"  {_dim('7 = Custom (n importe quelle API OpenAI-compatible)')}")
    print(f"  {_dim('8 = Aucun (lettres avec template uniquement)')}")
    llm_choice = _ask("Choisissez", default="1", choices=["1","2","3","4","5","6","7","8"])

    llm = config.get("llm", {})

    def _setup_api_key(api, provider_name, guide_url, key_name=None):
        """Configure une clé API pour un provider. Retourne (api_dict, api_key)."""
        if key_name is None:
            key_name = provider_name
        if not api.get(key_name):
            api[key_name] = {}
        print(f"\n  {_dim('Guide ' + provider_name + ' :')}")
        print(f"  1. Allez sur {_yellow(guide_url)}")
        print(f"  2. Créez une API key")
        key = _ask(f"{provider_name} API Key", default=api.get(key_name, {}).get("api_key", ""))
        api[key_name]["api_key"] = key
        return api, key

    if llm_choice == "1":
        llm["provider"] = "ollama"
        model = _ask("Modèle Ollama", default=llm.get("model", "llama3.2"))
        llm["model"] = model
        print()
        print(f"  {_yellow('⚠️  AVERTISSEMENT OLLAMA')}")
        print(f"  {_yellow('─────────────────────')}")
        print(f"  {_dim('• Nécessite 4+ Go de VRAM (carte graphique) ou 16+ Go de RAM (sans GPU)')}")
        print(f"  {_dim('• Le 1er téléchargement du modèle pèse 2 à 8 Go (5-15 minutes)')}")
        print(f"  {_dim('• Génération de lettres : 30-90 secondes par lettre (selon votre machine)')}")
        print(f"  {_dim('• Ne convient PAS aux machines avec 4 Go RAM sans carte graphique')}")
        print(f"  {_dim('• Doit tourner en arrière-plan : ouvrez un terminal, tapez ollama serve')}")
        print()
        print(f"  {_cyan('💡 Comment installer Ollama :')}")
        print(f"  {_dim('1. Téléchargez :')} {_yellow('https://ollama.com/download')}")
        app_desktop = "2. Lancez Ollama (l'application desktop ou ollama serve)"
        print(f"  {_dim(app_desktop)}")
        print(f"  {_dim('3. Téléchargez un modèle léger :')}")
        print(f"  {_dim('   •')} {_cyan('ollama pull qwen3.5:9b')} {_dim('(4.5 Go — 🤖 meilleur rapport qualité/taille, multilingue)')}")
        print(f"  {_dim('   •')} {_cyan('ollama pull phi3:mini')} {_dim('(2.4 Go — recommandé, compatible CPU)')}")
        print(f"  {_dim('   •')} {_cyan('ollama pull llama3.2')} {_dim('(2.0 Go — bon équilibre)')}")
        print(f"  {_dim('   •')} {_cyan('ollama pull tinyllama')} {_dim('(637 Mo — ultra-léger, qualité correcte)')}")
        verif_ollama = '4. Vérifiez que ça marche :'
        ollama_cmd = "ollama run phi3:mini 'Bonjour'"
        print(f"  {_dim(verif_ollama)} {_cyan(ollama_cmd)}")
        print()
        print(f"  {_cyan('☁️  Alternative cloud (si Ollama ne marche pas) :')}")
        print(f"  {_dim('TOM détecte automatiquement si Ollama est injoignable')}")
        print(f"  {_dim('→ fallback automatique sur un provider cloud (si clé API configurée)')}")
        print(f"  {_dim('→ sinon fallback regex (pas de LLM requis, parsing basique)')}")
        print()
        ans = _ask("Continuer avec Ollama ?", default="y", choices=["y", "n"])
        if ans == "n":
            llm["provider"] = "none"
            llm["model"] = ""
            print(f"  {_yellow('OK — les lettres utiliseront uniquement le template.')}")
            print(f"  {_dim('Vous pourrez changer ce paramètre plus tard (option 8).')}\n")
        else:
            print(f"\n  {_dim('Installation Ollama :')}")
            print(f"  1. {_yellow('https://ollama.com/download')}")
            print(f"  2. {_cyan('ollama pull ' + model)}\n")

    elif llm_choice == "2":
        llm["provider"] = "mistral"
        model = _ask("Modèle Mistral", default=llm.get("model", "mistral-small-2506"))
        llm["model"] = model
        api, _ = _setup_api_key(api, "Mistral", "https://console.mistral.ai/")

    elif llm_choice == "3":
        llm["provider"] = "openai"
        model = _ask("Modèle OpenAI", default=llm.get("model", "gpt-5.4-mini"))
        llm["model"] = model
        api, _ = _setup_api_key(api, "OpenAI", "https://platform.openai.com/api-keys")

    elif llm_choice == "4":
        llm["provider"] = "deepseek"
        model = _ask("Modèle DeepSeek", default=llm.get("model", "deepseek-v4-flash"))
        llm["model"] = model
        api, _ = _setup_api_key(api, "DeepSeek", "https://platform.deepseek.com/api_keys")

    elif llm_choice == "5":
        llm["provider"] = "openrouter"
        model = _ask("Modèle OpenRouter", default=llm.get("model", "openai/gpt-5.4-mini"))
        llm["model"] = model
        print(f"\n  {_dim('Exemples de modèles OpenRouter :')}")
        print(f"  {_dim('  openai/gpt-5.4-mini, anthropic/claude-3.5-sonnet, google/gemini-2.0-flash')}")
        api, _ = _setup_api_key(api, "OpenRouter", "https://openrouter.ai/keys")

    elif llm_choice == "6":
        llm["provider"] = "groq"
        model = _ask("Modèle Groq", default=llm.get("model", "llama-3.3-70b-versatile"))
        llm["model"] = model
        api, _ = _setup_api_key(api, "Groq", "https://console.groq.com/keys")

    elif llm_choice == "7":
        llm["provider"] = "custom"
        model = _ask("Modèle", default=llm.get("model", "gpt-5.4-mini"))
        llm["model"] = model
        base_url = _ask("Base URL (endpoint OpenAI-compatible)", default=llm.get("base_url", ""))
        llm["base_url"] = base_url
        api, _ = _setup_api_key(api, "Custom", "votre fournisseur API")
        print(f"\n  {_dim('Le provider custom fonctionne avec n importe quelle API OpenAI-compatible :')}")
        print(f"  {_dim('  • Claude via OpenRouter, Gemini via OpenRouter')}")
        print(f"  {_dim('  • Together AI, Fireworks, xAI, Perplexity')}")
        print(f"  {_dim('  • N importe quel endpoint /v1/chat/completions')}")

    else:
        llm["provider"] = "none"
        llm["model"] = ""
        print(f"  {_yellow('OK — les lettres utiliseront uniquement le template.')}")

    config["llm"] = llm
    config["api"] = api

    # Résumé tests API + LLM
    api_ok = 0
    if api.get("france_travail", {}).get("client_id"):
        print(f"  {_green('✅ France Travail configuré')}")
        api_ok += 1
    else:
        print(f"  {_yellow('⚠️  France Travail non configuré — scan impossible')}")
    if api.get("serpapi", {}).get("api_key"):
        print(f"  {_green('✅ SerpApi configuré')}")
        api_ok += 1
    else:
        print(f"  {_dim('💡 SerpApi non configuré — scan limité')}")
    if llm.get("provider", "none") != "none":
        print(f"  {_green('✅ LLM configuré: ' + llm.get('provider', '') + ' (' + llm.get('model', '?') + ')')}")
    else:
        print(f"  {_yellow('⚠️  Aucun LLM — lettres avec template uniquement')}")
    if api_ok == 0:
        print(f"\n  {_red('⚠️  Aucune API configurée !')}")
        print(f"  {_dim('Vous pourrez en configurer une depuis le menu [8] Configuration.')}")
    print()

    # ── 6. CV (upload passif) ──────────────────────────────────
    print(f"  {_bold(t['cv'])}")
    print(f"  {_dim('TOM lit votre CV pour extraire vos compétences (lecture seule, aucune modification).')}")
    print(f"  {_dim('Formats acceptés : .docx uniquement.')}")
    # Tente un sélecteur de fichier natif si dispo
    cv_path = _pick_file("Sélectionnez votre CV .docx", [("Word documents", "*.docx")])
    if not cv_path:
        if sys.platform == "darwin":
            print(f"  {_dim('💡 Astuce Mac : faites glisser votre fichier .docx dans ce terminal et appuyez sur Entrée.')}")
        cv_path = _ask("Chemin vers votre CV .docx (Entrée = ignorer)",
                        default=config.get("_cv_path", ""),
                        hint="Pour obtenir le chemin : faites un clic droit sur le fichier → Copier en tant que chemin (Windows) ou faites glisser le fichier dans le terminal (Mac)")
    if cv_path:
        cv_p = Path(cv_path.strip('"').strip("'"))
        if cv_p.exists() and cv_p.suffix.lower() == ".docx":
            config["_cv_path"] = str(cv_p.resolve())
            print(f"  {_green('✅ CV trouvé et enregistré.')}")
        elif cv_path.strip():
            print(f"  {_red(f'Fichier introuvable ou pas .docx : {cv_path}')}")
    print()

    # ── 7. Template de lettre ──────────────────────────────────
    print(f"  {_bold(t['template'])}")
    no_template = "Optionnel — TOM fournit un template par défaut si vous n'en avez pas."
    print(f"  {_dim(no_template)}")
    ph_text = "Placeholders disponibles : {ENTREPRISE} {POSTE} {DATE} {CORPS} {DESTINATAIRE} {PRENOM} {EMAIL}"
    print(f"  {_dim(ph_text)}")
    tmpl_path = _pick_file("Sélectionnez votre template .docx", [("Word documents", "*.docx")])
    if not tmpl_path:
        if sys.platform == "darwin":
            print(f"  {_dim('💡 Astuce Mac : faites glisser votre template .docx dans ce terminal.')}")
        tmpl_path = _ask("Chemin vers votre template .docx (Entrée = template par défaut)",
                          default=config.get("_letter_template_path", ""),
                          hint="Pour obtenir le chemin : clic droit → Copier en tant que chemin (Windows) ou glisser-déposer dans le terminal (Mac)")
    if tmpl_path:
        tmpl_p = Path(tmpl_path.strip('"').strip("'"))
        if tmpl_p.exists() and tmpl_p.suffix.lower() == ".docx":
            config["_letter_template_path"] = str(tmpl_p.resolve())
            print("  " + _green("✅ Template trouvé et enregistré."))
        elif tmpl_path.strip():
            msg = f"Fichier introuvable ou pas .docx : {tmpl_path}"
            print("  " + _red(msg))
    print()

    # ── Sauvegarder ────────────────────────────────────────────
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print(f"{BAR}")
    cmd = _bold("python bot.py")
    run_hint = t["launch"]
    print(f"  {_green(t['saved'])} : {_dim(str(CONFIG_PATH))}")
    print(f"  {_dim(run_hint)}")
    print()
    print(f"  {_yellow('📁 Où tout sera sauvegardé :')}")
    print(f"  {_dim('Offres    →')} {_cyan(str(Path('data/offres.md')))}  {_dim('(vos annonces filtrées)')}")
    print(f"  {_dim('Lettres   →')} {_cyan(str(Path('lettres/')))}  {_dim('(.docx et .md)')}")
    print(f"  {_dim('Candidatures →')} {_cyan(str(Path('data/candidatures.md')))}  {_dim('(suivi)')}")
    print(f"{BAR}\n")

    return config
