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


def _ask(prompt, default="", required=False, choices=None):
    """Pose une question et retourne la réponse."""
    suffix = ""
    if default:
        suffix = f" {_dim(f'[{default}]')}"
    options_str = '/'.join(choices)
    if choices:
        suffix = f" {_dim('(' + options_str + ')')}"

    while True:
        try:
            ans = input(f"  {prompt}{suffix} : ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            sys.exit(0)

        if not ans and default:
            return default
        if not ans and required:
            print(f"    {_red('Réponse requise.')}")
            continue
        if choices and ans.lower() not in [c.lower() for c in choices]:
            opts_str = ', '.join(choices)
            print(f"    {_red(f'Choix invalide. Options : {opts_str}')}")
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

def run_wizard(existing_config=None):
    """Lance le wizard interactif."""
    config = existing_config or {}

    print(f"\n{BAR}")
    print(f"  {_bold('⚙️  TOM V2.0 — Configuration')}")
    print(f"{BAR}\n")

    # ── 1. Profil ──────────────────────────────────────────────
    print(f"  {_bold('👤 Profil')}")
    profile = config.get("profile", {})
    profile["name"] = _ask("Votre nom", default=profile.get("name", ""), required=True)
    profile["email"] = _ask("Email", default=profile.get("email", ""))
    profile["linkedin"] = _ask("LinkedIn URL", default=profile.get("linkedin", ""))
    profile["phone"] = _ask("Téléphone", default=profile.get("phone", ""))
    profile["available"] = _ask("Disponibilité", default=profile.get("available", "Septembre 2026"))
    config["profile"] = profile
    print()

    # ── 1b. Priorités de recherche ─────────────────────────────
    print(f"  {_bold('🎯 Priorités de recherche')}")
    print(f"  {_dim('Classez vos priorités (1 = le plus important)')}")
    print(f"  {_dim('Options : IA Stratégie / Finance+IA / Conseil / Scale-up / Autre')}")
    prio1 = _ask("Priorité 1", default="IA Stratégie")
    prio2 = _ask("Priorité 2", default="Finance+IA")
    prio3 = _ask("Priorité 3", default="Scale-up tech")
    prefs = config.get("preferences", {})
    prefs["priorities"] = [prio1, prio2, prio3]
    config["preferences"] = prefs
    print()

    # ── 1c. Skills ─────────────────────────────────────────────
    print(f"  {_bold('🛠️  Vos compétences clés')}")
    print(f"  {_dim('Séparez par des virgules. Ex: Python, LLM, RAG, FP&A, Power BI, SQL')}")
    skills_raw = _ask("Skills", default=", ".join(profile.get("skills", [])))
    profile["skills"] = [s.strip() for s in skills_raw.split(",") if s.strip()] if skills_raw else []
    print()

    # ── 1d. Éducation ──────────────────────────────────────────
    print(f"  {_bold('🎓 Formation')}")
    edu1 = _ask("Diplôme principal", default=profile.get("education_main", ""))
    edu2 = _ask("École / Université", default=profile.get("education_school", ""))
    profile["education_main"] = edu1
    profile["education_school"] = edu2
    config["profile"] = profile
    print()

    # ── 2. Localisation ────────────────────────────────────────
    print(f"  {_bold('📍 Localisation')}")
    location = config.get("preferences", {}).get("location", {})
    city = _ask("Ville de recherche", default=location.get("city", "Paris"), required=True)
    country = _ask("Pays", default=location.get("country", "France"))
    dept = _ask("Code département (75=Paris, 45=Orléans, 92=Hauts-de-Seine...)", default=location.get("department", "75"))
    location = {"city": city, "country": country, "department": dept}
    config.setdefault("preferences", {})["location"] = location
    print()

    # ── 3. Critères de recherche ───────────────────────────────
    print(f"  {_bold('🎯 Critères de recherche')}")
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
    nl_prompt = _ask("Recherche", default=prefs.get("natural_language_prompt", ""))
    prefs["natural_language_prompt"] = nl_prompt

    max_age = _ask("Âge max des offres (jours)", default=str(prefs.get("max_offer_age_days", 10)))
    prefs["max_offer_age_days"] = int(max_age) if max_age.isdigit() else 10
    config["preferences"] = prefs

    min_score = _ask("Score minimum pour retenir une offre (1-10)", default=str(config.get("matching", {}).get("min_score", 6)))
    config.setdefault("matching", {})["min_score"] = int(min_score) if min_score.isdigit() else 6
    print()

    # ── 4. APIs ────────────────────────────────────────────────
    print(f"  {_bold('🔑 Configuration API')}")
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
    config["api"] = api
    print()

    # ── 5. LLM ─────────────────────────────────────────────────
    print(f"  {_bold('🤖 Fournisseur IA (pour les lettres et le parsing)')}")
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
        print(f"  {_dim('• Nécessite 4+ Go de VRAM (GPU) ou 16+ Go de RAM (CPU)')}")
        print(f"  {_dim('• Le 1er téléchargement du modèle pèse 2-8 Go (5-15 min)')}")
        print(f"  {_dim('• Génération de lettres : 30-90 secondes par lettre')}")
        print(f"  {_dim('• Ne convient PAS aux machines avec 4 Go RAM sans GPU')}")
        print(f"  {_dim('• Si le scan semble bloqué → Ollama charge le modèle (patience)')}")
        print()
        print(f"  {_cyan('💡 Modèle léger recommandé :')}")
        print(f"  {_dim('phi3:mini (2.4 Go, compatible CPU, démarrage rapide)')}")
        print(f"  {_dim('tinyllama (637 Mo, ultra-léger, qualité correcte)')}")
        print(f"  {_dim('Installation one-liner :')} {_cyan('ollama pull phi3:mini')}")
        print()
        print(f"  {_cyan('☁️  Alternative cloud (si Ollama ne marche pas) :')}")
        print(f"  {_dim('TOMATO détecte automatiquement si Ollama est down')}")
        print(f"  {_dim('→ fallback sur le provider configuré (si clé API dispo)')}")
        print(f"  {_dim('→ sinon fallback regex (pas de LLM requis)')}")
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
        model = _ask("Modèle Mistral", default=llm.get("model", "mistral-small-latest"))
        llm["model"] = model
        api, _ = _setup_api_key(api, "Mistral", "https://console.mistral.ai/")

    elif llm_choice == "3":
        llm["provider"] = "openai"
        model = _ask("Modèle OpenAI", default=llm.get("model", "gpt-4o-mini"))
        llm["model"] = model
        api, _ = _setup_api_key(api, "OpenAI", "https://platform.openai.com/api-keys")

    elif llm_choice == "4":
        llm["provider"] = "deepseek"
        model = _ask("Modèle DeepSeek", default=llm.get("model", "deepseek-chat"))
        llm["model"] = model
        api, _ = _setup_api_key(api, "DeepSeek", "https://platform.deepseek.com/api_keys")

    elif llm_choice == "5":
        llm["provider"] = "openrouter"
        model = _ask("Modèle OpenRouter", default=llm.get("model", "openai/gpt-4o-mini"))
        llm["model"] = model
        print(f"\n  {_dim('Exemples de modèles OpenRouter :')}")
        print(f"  {_dim('  openai/gpt-4o-mini, anthropic/claude-3.5-sonnet, google/gemini-2.0-flash')}")
        api, _ = _setup_api_key(api, "OpenRouter", "https://openrouter.ai/keys")

    elif llm_choice == "6":
        llm["provider"] = "groq"
        model = _ask("Modèle Groq", default=llm.get("model", "llama-3.3-70b-versatile"))
        llm["model"] = model
        api, _ = _setup_api_key(api, "Groq", "https://console.groq.com/keys")

    elif llm_choice == "7":
        llm["provider"] = "custom"
        model = _ask("Modèle", default=llm.get("model", "gpt-4o-mini"))
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
    print()

    # ── 6. CV (upload passif) ──────────────────────────────────
    print(f"  {_bold('📄 CV (.docx)')}")
    cv_path = _ask("Chemin vers votre CV .docx (Entrée = ignorer)", default=config.get("_cv_path", ""))
    if cv_path:
        cv_p = Path(cv_path)
        if cv_p.exists() and cv_p.suffix.lower() == ".docx":
            config["_cv_path"] = str(cv_p.resolve())
            print(f"  {_green('✅ CV trouvé et enregistré.')}")
        elif cv_path:
            print(f"  {_red(f'Fichier introuvable ou pas .docx : {cv_path}')}")
    print()

    # ── 7. Template de lettre ──────────────────────────────────
    print(f"  {_bold('✉️  Template de lettre (.docx)')}")
    print(f"  {_dim('Placeholders disponibles : {{ENTREPRISE}} {{POSTE}} {{DATE}} {{CORPS}} {{DESTINATAIRE}}')}")
    tmpl_path = _ask("Chemin vers votre template .docx (Entrée = ignorer)", default=config.get("_letter_template_path", ""))
    if tmpl_path:
        tmpl_p = Path(tmpl_path)
        if tmpl_p.exists() and tmpl_p.suffix.lower() == ".docx":
            config["_letter_template_path"] = str(tmpl_p.resolve())
            print("  " + _green("\u2705 Template trouv\u00e9 et enregistr\u00e9."))
        elif tmpl_path:
            msg = f"Fichier introuvable ou pas .docx : {tmpl_path}"
            print("  " + _red(msg))
    print()

    # ── Sauvegarder ────────────────────────────────────────────
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print(f"{BAR}")
    cmd = _bold("python bot.py")
    run_hint = "Lancez " + cmd + " pour commencer."
    print(f"  {_green('✅ Configuration sauvegardée :')} {_dim(str(CONFIG_PATH))}")
    print(f"  {_dim(run_hint)}")
    print(f"{BAR}\n")

    return config
