#!/usr/bin/env python3
"""
TOM V2.0 — Agent personnel de recherche d'emploi
Menu CLI interactif : scan, offres, postuler, rejeter, lettres, config, stats
"""

import sys
import os
import yaml
import re
from pathlib import Path
from datetime import datetime, timedelta

_BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(_BASE))

from src.scanner import scan_all
from src.matcher import match_all, categorize, CAT_LABELS, get_cat_labels
from src.letter_engine import generate_all
from src.cv_parser import parse as parse_cv
from src.prompt_engine import run as interpret_prompt
from src.prompt_engine import get_token_usage as get_token_usage
from src.i18n import t as _t
from src.voir_lettres import open_letters_folder

BOT_NAME = "TOM V2.0"
CREATOR = "Matthias Dubois"
CREATOR_LINKEDIN = "https://www.linkedin.com/in/matthias-dubois/"
CREATOR_GITHUB = "https://github.com/theturbos"
LICENSE = "© Matthias Dubois — Tous droits réservés"
CONFIG_PATH = Path("data/config.yaml")
OFFERS_PATH = Path("data/offres.md")
DOUBLONS_PATH = Path("data/doublons.md")
CANDIDATURES_PATH = Path("data/candidatures.md")
LETTERS_DIR = Path("lettres")

# ── Couleurs : délégué à src.colors (cross-platform, colorama fallback) ─
from src.colors import green as _green, red as _red, yellow as _yellow
from src.colors import cyan as _cyan, bold as _bold, dim as _dim, italic as _italic
from src.colors import bar as _make_bar

BAR = _make_bar()

def _get_version():
    """Lit la version depuis le tag Git le plus récent, ou le fichier VERSION."""
    import subprocess
    try:
        r = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True, text=True,
            cwd=str(_BASE), timeout=5
        )
        tag = r.stdout.strip()
        if tag and r.returncode == 0:
            return tag.lstrip("v")  # v2.3 → 2.3
    except Exception:
        pass
    # Fallback: fichier VERSION
    ver_file = _BASE / "VERSION"
    if ver_file.exists():
        return ver_file.read_text(encoding="utf-8").strip()
    return "2.0"


def _header(title):
    b = BAR
    return f"\n{b}\n  {_bold(title)}\n{b}"

def _menu_item(n, label):
    num = f"[{n}]"
    return f"  {_green(f'{num:<4}')} {label}"


# ── Setup ─────────────────────────────────────────────────────

def run_setup():
    from src.setup import run_wizard
    print()
    lang = _ask_language()
    run_wizard({}, lang=lang)


def _ask_language():
    """Demande la langue au démarrage."""
    print(f"  {_bold('🌐 Langue / Language')}")
    print(f"  {_dim('[1]')} Français")
    print(f"  {_dim('[2]')} English")
    ans = input(f"  {_dim('Choix / Choice [1] : ')}").strip()
    if ans == "2":
        return "en"
    return "fr"


# ── Config ────────────────────────────────────────────────────

def load_config():
    if not CONFIG_PATH.exists():
        print()
        print(_yellow('⚠️  Aucune configuration trouvée.'))
        print(_dim('Lancement du wizard d\'installation...'))
        print()
        run_setup()
        if not CONFIG_PATH.exists():
            print(_red('Configuration annulée. Au revoir !'))
            sys.exit(0)
        print()
        print(_green('✅ Configuration créée avec succès !'))
        print(_dim('Redémarrage de TOM...'))
        print()
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not data:
        print(_red('Configuration vide.'))
        print(_dim('Lancement du wizard...'))
        run_setup({})
        if not CONFIG_PATH.exists():
            sys.exit(0)
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    if not data:
        print(_red('Configuration vide. Au revoir !'))
        sys.exit(1)
    return data

def save_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)


# ── Offres ────────────────────────────────────────────────────

def load_offers():
    """Parse offres.md → liste d'offres."""
    offers = []
    if not OFFERS_PATH.exists():
        return offers
    text = open(OFFERS_PATH, "r", encoding="utf-8").read()
    pattern = re.compile(
        r'🆔 ID OFFRE\s*:\s*([^\n]+)\n'
        r'📌 CATÉGORIE\s*:\s*([^\n]+)\n'
        r'🏢 ENTREPRISE\s*:\s*([^\n]+)\n'
        r'💼 TITRE POSTE\s*:\s*([^\n]+)\n'
        r'📍 LOCALISATION\s*:\s*([^\n]+)\n'
        r'📅 DATE PUBLIÉE\s*:\s*([^\n]+)\n'
        r'🔗 URL\s*:\s*([^\n]+)\n'
        r'⭐ SCORE MATCH\s*:\s*(\d+).*?\n'
        r'📝 DESCRIPTION\s*:\s*([^\n]*)\n'
        r'🚦 STATUT\s*:\s*([^\n]+)',
    )
    # Pattern v2 (avec description)
    pattern_v2 = re.compile(
        r'🆔 ID OFFRE\s*:\s*([^\n]+)\n'
        r'📌 CATÉGORIE\s*:\s*([^\n]+)\n'
        r'🏢 ENTREPRISE\s*:\s*([^\n]+)\n'
        r'💼 TITRE POSTE\s*:\s*([^\n]+)\n'
        r'📍 LOCALISATION\s*:\s*([^\n]+)\n'
        r'📅 DATE PUBLIÉE\s*:\s*([^\n]+)\n'
        r'🔗 URL\s*:\s*([^\n]+)\n'
        r'⭐ SCORE MATCH\s*:\s*(\d+).*?\n'
        r'📝 DESCRIPTION\s*:\s*([^\n]*)\n'
        r'🚦 STATUT\s*:\s*([^\n]+)',
    )
    # Pattern v1 (sans description — backward compat)
    pattern_v1 = re.compile(
        r'🆔 ID OFFRE\s*:\s*([^\n]+)\n'
        r'📌 CATÉGORIE\s*:\s*([^\n]+)\n'
        r'🏢 ENTREPRISE\s*:\s*([^\n]+)\n'
        r'💼 TITRE POSTE\s*:\s*([^\n]+)\n'
        r'📍 LOCALISATION\s*:\s*([^\n]+)\n'
        r'📅 DATE PUBLIÉE\s*:\s*([^\n]+)\n'
        r'🔗 URL\s*:\s*([^\n]+)\n'
        r'⭐ SCORE MATCH\s*:\s*(\d+).*?\n'
        r'🚦 STATUT\s*:\s*([^\n]+)',
    )
    for m in pattern_v2.finditer(text):
        id_, cat_raw, company, title, loc, date, url, score, desc, status = m.groups()
        has_letter = '✅' in status
        cat = 'A' if cat_raw.strip().startswith('A') else 'B'
        offers.append({
            'id': id_.strip(), 'company': company.strip(), 'title': title.strip(),
            'location': loc.strip(), 'date': date.strip(), 'url': url.strip(),
            'score': int(score.strip()), 'status': status.strip(),
            'has_letter': has_letter, 'category': cat,
            'description': (desc or '').strip()
        })
    # Fallback v1 si aucune offre trouvée en v2
    if not offers:
        for m in pattern_v1.finditer(text):
            id_, cat_raw, company, title, loc, date, url, score, status = m.groups()
            has_letter = '✅' in status
            cat = 'A' if cat_raw.strip().startswith('A') else 'B'
            offers.append({
                'id': id_.strip(), 'company': company.strip(), 'title': title.strip(),
                'location': loc.strip(), 'date': date.strip(), 'url': url.strip(),
                'score': int(score.strip()), 'status': status.strip(),
                'has_letter': has_letter, 'category': cat,
                'description': ''
            })
    offers.sort(key=lambda x: x['score'], reverse=True)
    return offers

def save_candidate_status(offer_id, new_status):
    date_str = datetime.now().strftime("%d/%m/%Y")
    if OFFERS_PATH.exists():
        text = open(OFFERS_PATH, "r", encoding="utf-8").read()
        idx = text.find(f"🆔 ID OFFRE : {offer_id}")
        if idx >= 0:
            chunk = text[idx:idx + 500]
            spos = chunk.find("🚦 STATUT :")
            if spos >= 0:
                eol = chunk.find("\n", spos)
                old = chunk[spos:eol] if eol > 0 else chunk[spos:]
                letters_folder = str(LETTERS_DIR)
                new_line = f"🚦 STATUT : {new_status} | 📅 Date : {date_str} | 📝 Lettre : ✅ {letters_folder}/{offer_id.replace('-', '_')}.md"
                text = text[:idx + spos] + new_line + text[idx + spos + len(old):]
                open(OFFERS_PATH, "w", encoding="utf-8").write(text)
    CANDIDATURES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CANDIDATURES_PATH, "a", encoding="utf-8") as f:
        f.write(f"| {offer_id} | {date_str} | {new_status} |\n")
    print(f"  {_green('Statut mis à jour :')} {offer_id} {_dim('→')} {new_status} ({date_str})")


# ── Header / menu ─────────────────────────────────────────────

def show_header():
    print()
    print(_header(_t("menu_title")))
    if CONFIG_PATH.exists():
        config = load_config()
        profile = config.get("profile", {})
        prefs = config.get("preferences", {})
        loc = prefs.get("location", {})
        city = loc.get("city", "Paris")
        name = profile.get("name", "Utilisateur")
        min_score = config.get("matching", {}).get("min_score", 6)
        tone = config.get("letter_tone", "professionnel direct")
        ver = _get_version()
        print(f"  {_bold(name)} {_dim('·')} {_bold(city)} {_dim('· min')} {_bold(str(min_score))} {_dim('· ton')} {_italic(tone)} {_dim('·')} v{ver}")
        # Alertes config
        api = config.get("api", {})
        ft_ok = bool(api.get("france_travail", {}).get("client_id"))
        sa_ok = bool(api.get("serpapi", {}).get("api_key"))
        llm_ok = config.get("llm", {}).get("provider", "none") != "none"
        if not ft_ok:
            print(f"  {_red('⚠️  Aucune API configurée — scan impossible. Menu [8]')}")
        if not llm_ok:
            print(f"  {_yellow('💡 Aucun LLM configuré — lettres template uniquement. Menu [8]')}")
        print()
    print(f"  {_dim(LICENSE)}")
    print(f"  {_dim('🔗')} {_cyan(CREATOR_LINKEDIN)}")
    print(f"  {_dim('🐙')} {_cyan(CREATOR_GITHUB)}")
    print()

def menu_main():
    print()
    print(_menu_item(1, _t("scan")))
    print(_menu_item(2, _t("dashboard")))
    print(_menu_item(3, _t("view_offers")))
    print(_menu_item(4, _t("applied")))
    print(_menu_item(5, _t("interview")))
    print(_menu_item(6, _t("rejected")))
    print(_menu_item(7, _t("letters")))
    print(_menu_item(8, _t("config")))
    print(_menu_item(9, _t("prompt")))
    print(_menu_item(10, _t("candidatures")))
    print(_menu_item(11, _t("open_letters")))
    print()
    print(_menu_item('U', _t("update")))
    print(_menu_item(0, _t("quit")))
    print()
    choice = input(_dim(_t("choice_prompt"))).strip()
    return choice


# ── Menus ─────────────────────────────────────────────────────

def menu_scan():
    config = load_config()
    profile = config.get("profile", {})

    # Warning Ollama avant scan
    llm = config.get("llm", {})
    if llm.get("provider") == "ollama":
        fb = llm.get("fallback_provider", "")
        print()
        print(f"  {_yellow('⚠️  Provider configuré : Ollama (local)')}")
        print(f"  {_dim('Le scan peut etre lent si le modele n est pas deja charge.')}")
        print(f"  {_dim('Si le scan semble bloqué, Ollama télécharge peut-être le modèle.')}")
        print(f"  {_dim('Modèle léger recommandé :')} {_cyan('phi3:mini')} {_dim('ou')} {_cyan('tinyllama')}")
        print(f"  {_dim('Installation one-liner :')} {_cyan('ollama pull phi3:mini')}")
        fallback_msg = "Patience — ou passez au cloud avec l\'option [8]. Fallback configuré: " + fb if fb else "Patience — ou passez au cloud avec l\'option [8]."
        print(f"  {_dim(fallback_msg)}")
        print()

    print(_header(_t("scan_title")))
    print(f"  {_dim('Appuyez sur Ctrl+C pour annuler le scan.')}")
    print()

    try:
        raw = scan_all(config)
    except KeyboardInterrupt:
        print(f"\n  {_yellow(_t('scan_cancelled'))}")
        return

    if not raw:
        # Diagnostic : vérifie si les APIs sont configurées
        api = config.get("api", {})
        ft_ok = bool(api.get("france_travail", {}).get("client_id"))
        sa_ok = bool(api.get("serpapi", {}).get("api_key"))
        if not ft_ok and not sa_ok:
            print()
            print(f"  {_yellow(_t('scan_no_api'))}")
            besoin_api = "TOM a besoin d'au moins une source d'offres pour fonctionner."
            print(f"  {_dim(besoin_api)}")
            print()
            print(f"  {_cyan('➜ France Travail API')} {_dim('(gratuit, 500k+ offres)')}")
            print(f"    {_dim('1. Créez un compte sur')} {_yellow('https://www.emploi-store.fr/portail/')}")
            choisir_api = "2. Choisissez l'API \"Offres d'emploi\""
            print(f"    {_dim(choisir_api)}")
            print(f"    {_dim('3. Lancez')} {_cyan('[8] Changer la config')} {_dim('→ API → France Travail')}")
            print()
            print(f"  {_cyan('➜ SerpApi Google Jobs')} {_dim('(100 req/mois gratuites)')}")
            print(f"    {_dim('1. Créez un compte sur')} {_yellow('https://serpapi.com/')}")
            print(f"    {_dim('2. Lancez')} {_cyan('[8] Changer la config')} {_dim('→ API → SerpApi')}")
            print()
            print(f"  {_dim('Une fois configuré, relancez le scan avec [1].')}")
        elif not ft_ok:
            print(f"  {_yellow('⚠️  France Travail API non configurée.')}")
            print(f"  {_dim('Configurez-la dans [8] Changer la config → API.')}")
        elif not sa_ok:
            print(f"  {_dim('💡 SerpApi non configuré. Seule France Travail est utilisée.')}")
        else:
            print(f"  {_yellow(_t('offers_empty'))}")
            print(f"  {_dim('Vérifiez vos critères de recherche dans [9] Prompt.')}")
        return
    offers = match_all(raw, config, profile)
    for o in offers:
        o["category"] = categorize(o, config)
    _save_offers(offers)
    _update_doublons(raw, offers)
    print(f"\n  {_green('✅ Scan terminé :')} {_bold(str(len(offers)))} offres pertinentes trouvées.")
    print(f"  {_dim('Tapez [3] pour les voir.')}")
    actual_letters = Path(config.get("_letters_dir", LETTERS_DIR))
    print(f"\n  {_yellow('📁 Où sont mes fichiers ?')}")
    print(f"  {_dim('Ctrl+Click (ou Cmd+Click sur Mac) pour ouvrir :')}")
    offres_uri = OFFERS_PATH.resolve().as_uri()
    lettres_uri = actual_letters.resolve().as_uri()
    config_uri = CONFIG_PATH.resolve().as_uri()
    stats_uri = CANDIDATURES_PATH.resolve().as_uri()
    print(f"  {_dim('Offres    →')} {_cyan(offres_uri)}")
    print(f"  {_dim('Lettres   →')} {_cyan(lettres_uri)}")
    print(f"  {_dim('Config    →')} {_cyan(config_uri)}")
    print(f"  {_dim('Stats     →')} {_cyan(stats_uri)}")
    _show_token_usage()

def _save_offers(new_offers):
    """Merge les nouvelles offres avec les existantes. Garde les statuts.
    Déduplication inter-sessions : vérifie similarité titre même après merge."""
    try:
        import fcntl
        _has_fcntl = True
    except (ImportError, ModuleNotFoundError):
        _has_fcntl = False
    from src.scanner import _normalize_title, _similarity
    existing = load_offers()
    existing_map = {o['id']: o for o in existing}

    # Merge : nouvelle offre écrase l'ancienne SEULEMENT si elle est plus récente ou nouveau score
    merged_map = dict(existing_map)
    for o in new_offers:
        oid = o.get('id', '')
        if oid in existing_map:
            # Garde le statut et la lettre de l'ancienne
            old = existing_map[oid]
            o['status'] = old.get('status', '[ ] Non postulé')
            o['has_letter'] = old.get('has_letter', False)
        else:
            o['status'] = '[ ] Non postulé'
            o['has_letter'] = False
        merged_map[oid] = o

    all_offers = sorted(merged_map.values(), key=lambda x: x.get('score', 0), reverse=True)

    # Passe anti-doublons inter-sessions : détecte titres quasi-identiques même entreprise
    # Seuil 80% (inter-sessions = plus permissif que le 85% intra-scan)
    deduped = []
    seen_companies = {}  # {company: [(title, desc)]}
    dupes_removed = 0
    for o in all_offers:
        company = o.get('company', '').lower().strip()
        title = o.get('title', '')
        desc = (o.get('description', '') or '')[:200]
        if company and company in seen_companies:
            is_dupe = False
            for existing_title, existing_desc in seen_companies[company]:
                title_sim = _similarity(_normalize_title(title), _normalize_title(existing_title))
                if title_sim >= 0.80:
                    is_dupe = True
                    break
                # Même si titre < 80%, vérifie description similaire (repost même offre)
                if title_sim >= 0.60 and desc and existing_desc:
                    desc_sim = _similarity(
                        _normalize_title(desc),
                        _normalize_title(existing_desc)
                    )
                    if desc_sim >= 0.70:
                        is_dupe = True
                        break
            if is_dupe:
                dupes_removed += 1
                continue
        if company not in seen_companies:
            seen_companies[company] = []
        seen_companies[company].append((title, desc))
        deduped.append(o)
    if dupes_removed:
        print(f"  {_dim(f'♻️  {dupes_removed} doublons inter-sessions filtrés')}")
    all_offers = deduped

    # Nettoyage : archiver les offres de plus de 45 jours sans statut actif
    cutoff_date = datetime.now() - timedelta(days=45)
    active_statuses = ('✅ Postulé', '📞 Entretien')
    expired_count = 0
    for o in all_offers:
        status = o.get('status', '')
        if any(s in status for s in active_statuses):
            continue
        date_str = o.get('date', '')
        if date_str:
            try:
                offer_date = datetime.strptime(date_str, '%d/%m/%Y')
                if offer_date < cutoff_date:
                    o['status'] = '🗄️ Expirée'
                    expired_count += 1
            except (ValueError, TypeError):
                pass

    lines = [
        "# 📊 Offres d'emploi — TOM V2.0\n",
        f"_Dernière mise à jour : {datetime.now().strftime('%d/%m/%Y %H:%M')}_\n",
        "---\n",
    ]
    cfg = load_config() if CONFIG_PATH.exists() else None
    labels = get_cat_labels(cfg)
    for o in all_offers:
        cat_label = labels.get(o.get('category'), 'Secteur')
        status_line = o.get('status', '[ ] Non postulé')
        letter_line = '✅' if o.get('has_letter') else '[ ]'
        lines += [
            "━" * 40,
            f"🆔 ID OFFRE : {o.get('id', 'N/A')}",
            f"📌 CATÉGORIE : {o.get('category', '?')} — {cat_label}",
            f"🏢 ENTREPRISE : {o.get('company', 'N/A')}",
            f"💼 TITRE POSTE : {o.get('title', '')}",
            f"📍 LOCALISATION : {o.get('location', '')}",
            f"📅 DATE PUBLIÉE : {o.get('date', 'N/A')}",
            f"🔗 URL : {o.get('url', '#')}",
            f"⭐ SCORE MATCH : {o.get('score', 0)}/10",
            f"📝 DESCRIPTION : {o.get('description', '')[:300]}",
            f"🚦 STATUT : {status_line}",
            "",
        ]
    OFFERS_PATH.parent.mkdir(parents=True, exist_ok=True)
    # File lock pour éviter corruption si 2 instances simultanées
    try:
        if _has_fcntl:
            with open(OFFERS_PATH, "w", encoding="utf-8") as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                f.write("\n".join(lines))
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        else:
            raise ImportError("fcntl not available")
    except (ImportError, ModuleNotFoundError, NameError):
        # Windows ou env sans fcntl — fallback sans lock
        with open(OFFERS_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    new_count = sum(1 for o in new_offers if o['id'] not in existing_map)
    updated_count = sum(1 for o in new_offers if o['id'] in existing_map)
    if new_count or updated_count:
        print(f"  {_dim(f'{new_count} nouvelles, {updated_count} mises à jour, {len(all_offers)} total')}")

def _update_doublons(raw, kept):
    kept_ids = {o.get("id") for o in kept}
    dupes = [o for o in raw if o.get("id") not in kept_ids]
    lines = ["# 📋 Doublons détectés\n", "---\n"]
    for d in dupes:
        lines.append(f"- {d.get('company', 'N/A')} — {d.get('title', '')} ({d.get('date', 'N/A')})")
    DOUBLONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DOUBLONS_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

def menu_dashboard():
    config = load_config()
    offers = load_offers()
    total = len(offers)
    avg = round(sum(o["score"] for o in offers) / total, 1) if total else 0
    letters = sum(1 for o in offers if o["has_letter"])
    cat_a = sum(1 for o in offers if o["category"] == "A")
    cat_b = total - cat_a
    doublons = 0
    if DOUBLONS_PATH.exists():
        dt = open(DOUBLONS_PATH, "r", encoding="utf-8").read()
        doublons = len(re.findall(r'^- ', dt, re.MULTILINE))
    postulees = 0
    entretiens = 0
    rejets = 0
    if CANDIDATURES_PATH.exists():
        ct = open(CANDIDATURES_PATH, "r", encoding="utf-8").read()
        postulees = ct.count("✅ Postulé")
        entretiens = ct.count("📞 Entretien")
        rejets = ct.count("❌ Refus")

    print(_header(_t("dash_title")))
    labels = get_cat_labels(config)
    print()

    # ── KPIs principaux (sans padding forcé, naturel + tabulation) ──
    kpi_labels = f"  {_bold(_t('dash_kpi_offers'))}    {_bold(_t('dash_kpi_score'))}    {_bold(_t('dash_kpi_letters'))}    {_bold(_t('dash_kpi_dupes'))}"
    kpi_values = f"  {_green(str(total))}              {_cyan(str(avg)+'/10')}           {_green(str(letters))}              {_dim(str(doublons))}"
    print(kpi_labels)
    print(kpi_values)
    print()

    # ── Catégories ──
    label_a = labels["A"]
    label_b = labels["B"]
    print(f"  {_bold(_t('dash_categories'))}")
    print(f"    {_green('Cat A — '+label_a)}  →  {_cyan(str(cat_a)+' offres')}")
    print(f"    {_yellow('Cat B — '+label_b)}  →  {_yellow(str(cat_b)+' offres')}")
    print()

    # ── Pipeline ──
    print(f"  {_bold(_t('dash_pipeline'))}")
    pipe_parts = [
        _dim(_t('dash_total_offers', total)),
        _green(_t('dash_letters', letters)),
        _cyan(_t('dash_applied', postulees)),
        _yellow(_t('dash_interviews', entretiens)),
        _dim(_t('dash_rejected', rejets)),
    ]
    pipe = f"  {'  →  '.join(pipe_parts)}"
    print(pipe)
    print()

    # ── Top offres (tableau compact) ──
    def _pad(s, w):
        """Pad une chaîne à largeur w, en gérant les séquences ANSI."""
        plain = re.sub(r'\x1b\[[0-9;]*m', '', s)
        return s + ' ' * max(0, w - len(plain))

    if offers[:7]:
        print(f"  {_bold(_t('dash_top'))}")
        W_SC, W_CO, W_TI, W_CA, W_LE = 10, 26, 34, 6, 8
        sep = f"  {'─'*W_SC}─{'─'*W_CO}─{'─'*W_TI}─{'─'*W_CA}─{'─'*W_LE}"
        hdr = f"  {_pad(_t('dash_col_score'), W_SC)} {_pad(_t('dash_col_company'), W_CO)} {_pad(_t('dash_col_title'), W_TI)} {_pad(_t('dash_col_cat'), W_CA)} {_pad(_t('dash_col_letter'), W_LE)}"
        print(sep)
        print(hdr)
        print(sep)
        for o in offers[:7]:
            if o['score'] >= 8:
                sc = _green(f"⭐ {o['score']}/10")
            elif o['score'] >= 6:
                sc = _cyan(f"  {o['score']}/10")
            else:
                sc = _dim(f"  {o['score']}/10")
            co = o["company"][:25]
            ti = o["title"][:33]
            ca = _green("A ") if o["category"] == "A" else _yellow("B ")
            le = _green(" ✓") if o["has_letter"] else _dim(" —")
            print(f"  {_pad(sc, W_SC)} {_pad(co, W_CO)} {_pad(ti, W_TI)} {_pad(ca, W_CA)} {_pad(le, W_LE)}")
        print(sep)
    print()

def menu_offers():
    config = load_config() if CONFIG_PATH.exists() else {}
    labels = get_cat_labels(config)
    offers = load_offers()
    if not offers:
        print("  " + _yellow(_t("offers_empty")))
        return
    print(_header(_t("offers_title")))
    print()
    for i, o in enumerate(offers, 1):
        sc = _green(f"{o['score']}/10") if o['score'] >= 9 else _cyan(f"{o['score']}/10") if o['score'] >= 7 else _dim(f"{o['score']}/10")
        ca = _green(labels['A']) if o['category'] == 'A' else _yellow(labels['B'])
        st = o.get('status', '[ ] Non postulé')
        le = _green("✓ Lettre") if o['has_letter'] else _dim("— Lettre")
        print(f"  {_bold(f'[{i}]')} {o['company'][:40]}")
        print(f"      {o['title'][:50]}")
        print(f"      Score: {sc}  {ca}  {le}  {st}")
        print(f"      📍 {o['location'][:40]}")
        print()

def menu_postuler():
    offers = load_offers()
    if not offers:
        print("  " + _yellow("Aucune offre à marquer. Scannez d'abord."))
        return
    menu_offers()
    raw = input(_dim("\n  Numéro de l'offre postulée (0 pour annuler) : ")).strip()
    if not raw.isdigit() or raw == "0":
        return
    idx = int(raw)
    if idx > len(offers):
        print(f"  {_red('Numéro invalide.')}")
        return
    offer = offers[idx - 1]
    save_candidate_status(offer["id"], "✅ Postulé")
    print()

def menu_entretien():
    """Marquer un entretien."""
    offers = load_offers()
    if not offers:
        print("  " + _yellow("Aucune offre à marquer."))
        return
    menu_offers()
    raw = input(_dim("\n  Numéro de l'offre avec entretien (0 pour annuler) : ")).strip()
    if not raw.isdigit() or raw == "0":
        return
    idx = int(raw)
    if idx > len(offers):
        print("  " + _red("Numéro invalide."))
        return
    offer = offers[idx - 1]
    save_candidate_status(offer["id"], "📞 Entretien")
    print()

def menu_rejet():
    offers = load_offers()
    if not offers:
        print("  " + _yellow("Aucune offre à marquer."))
        return
    menu_offers()
    raw = input(_dim("\n  Numéro de l'offre rejetée (0 pour annuler) : ")).strip()
    if not raw.isdigit() or raw == "0":
        return
    idx = int(raw)
    if idx > len(offers):
        print("  " + _red("Numéro invalide."))
        return
    offer = offers[idx - 1]
    save_candidate_status(offer["id"], "❌ Refus")
    print()

def menu_lettres():
    config = load_config()
    profile = config.get("profile", {})
    offers = load_offers()
    no_letter = [o for o in offers if not o["has_letter"] and o["score"] >= 7]
    if not no_letter:
        print(f"  {_dim('Toutes vos offres (score ≥ 7) ont déjà une lettre.')}")
        return
    print(f"  {_dim(f'{len(no_letter)} offres sans lettre trouvées (score ≥ 7)')}")
    for i, o in enumerate(no_letter, 1):
        print(f"    [{i}] {o['company']} — {o['title'][:50]}  (Score: {o['score']}/10)")
    ans = input(_dim("\n  Générer les lettres ? [y/n] : ")).strip().lower()
    if ans not in ("y", "yes", "oui"):
        return
    template_path = config.get("_letter_template_path", "")
    if template_path and not Path(template_path).exists():
        template_path = ""
    generated = generate_all(no_letter, config, profile, template_path)
    print(f"  {_bold(str(len(generated)))} lettre(s) générée(s)")
    _show_token_usage()

def menu_voir_lettres():
    """Ouvre le dossier des lettres."""
    config = load_config()
    open_letters_folder(config, LETTERS_DIR)


def menu_config():
    """Affiche et PERMET de modifier chaque paramètre de la config."""
    config = load_config()
    print(_header("⚙️  Configuration"))
    print()

    profile = config.get("profile", {})
    prefs = config.get("preferences", {})
    loc = prefs.get("location", {})
    matching = config.get("matching", {})
    api = config.get("api", {})
    llm = config.get("llm", {})

    print(f"  {_bold('👤 PROFIL')}")
    print(f"  {_dim('├─')} {_bold('Nom:')}          {profile.get('name', '?')}")
    print(f"  {_dim('├─')} {_bold('Email:')}        {profile.get('email', '?')}")
    print(f"  {_dim('├─')} {_bold('LinkedIn:')}     {profile.get('linkedin', '?')}")
    print(f"  {_dim('├─')} {_bold('Disponible:')}   {profile.get('available', '?')}")
    skills = ', '.join(profile.get('skills', []))
    educ = f"{profile.get('education_main', '—')}  {_dim('@')}  {profile.get('education_school', '—')}"
    print(f"  {_dim('└─')} {_bold('Formation:')}    {educ}")
    if skills:
        print(f"     {_dim('Compétences:')}  {skills[:80]}")
    print()
    print(f"  {_bold('🔍 RECHERCHE')}")
    print(f"  {_dim('├─')} {_bold('Localisation:')} {loc.get('city', '?')}, {loc.get('country', '?')}  {_dim('(dép. ' + loc.get('department', '?') + ')')}")
    priorities = prefs.get('priorities', [])
    if not isinstance(priorities, list) or len(priorities) < 2:
        priorities = (priorities if isinstance(priorities, list) else [priorities]) + ['?']
        priorities = priorities[:2]
    p1 = priorities[0] if priorities[0] else '?'
    p2 = priorities[1] if priorities[1] else '?'
    print(f"  {_dim('├─')} {_bold('Catégories:')}   {_cyan(p1)}  {_dim('|')}  {_cyan(p2)}")
    prompt_text = prefs.get('natural_language_prompt', '')
    if not prompt_text:
        sq = prefs.get('search_queries', [])
        prompt_text = ', '.join(sq[:3]) if sq else ''
    print(f"  {_dim('├─')} {_bold('Prompt:')}       {_italic(str(prompt_text)[:55])}")
    print(f"  {_dim('├─')} {_bold('Score min:')}    {matching.get('min_score', 6)}/10")
    print(f"  {_dim('├─')} {_bold('Âge max:')}      {prefs.get('max_offer_age_days', 10)} jours")
    tone = config.get('letter_tone', 'professionnel direct')
    print(f"  {_dim('└─')} {_bold('Ton lettres:')}  {_italic(tone)}")
    print()
    print(f"  {_bold('📡 API')}")
    ft = api.get('france_travail', {})
    sa = api.get('serpapi', {})
    ft_cfg = _green('✅ OK') if ft.get('client_id') else _red('✗ Non')
    sa_cfg = _green('✅ OK') if sa.get('api_key') else _red('✗ Non')
    print(f"  {_dim('├─')} {_bold('France Travail:')} {ft_cfg}")
    print(f"  {_dim('└─')} {_bold('SerpApi:')}        {sa_cfg}")
    print()
    print(f"  {_bold('🤖 LLM')}")
    prov = llm.get('provider', 'none')
    mod = llm.get('model', '?')
    tp = config.get('_letter_template_path', '')
    cv = config.get('_cv_path', '')
    ld = config.get('_letters_dir', str(LETTERS_DIR))
    print(f"  {_dim('├─')} {_bold('Provider:')}     {_cyan(prov)}  {_dim('(' + mod + ')')}")
    print(f"  {_dim('├─')} {_bold('Template:')}     {_green('✅ ' + str(Path(tp).name)) if tp else _dim('Aucun')}")
    print(f"  {_dim('├─')} {_bold('CV:')}           {_green('✅ ' + str(Path(cv).name)) if cv else _dim('Aucun')}")
    print(f"  {_dim('└─')} {_bold('Lettres →')}     {_cyan(ld)}")
    print()
    # Menu de modification
    print(f"  {_dim('─── Actions ──────────────────────')}")
    current_lang = config.get("_lang", "fr")
    lang_label = "🇫🇷 Français" if current_lang == "fr" else "🇬🇧 English"
    print(f"  {_green('[L]')}  Langue : {lang_label}")
    print(f"  {_green('[M]')}  Modifier un paramètre")
    print(f"  {_green('[S]')}  Relancer le setup wizard")
    print(f"  {_green('[?]')}  Aide / Guide débutant")
    print(f"  {_green('[U]')}  Mettre à jour TOM")
    print(f"  {_dim('[Entrée]')}  Retour")
    print(f"  {_red('[D]')}  Désinstaller TOM")
    choice = input(_dim("  Votre choix : ")).strip().upper()

    if choice == 'L':
        new_lang = "en" if current_lang == "fr" else "fr"
        config["_lang"] = new_lang
        save_config(config)
        label = "🇬🇧 English" if new_lang == "en" else "🇫🇷 Français"
        print(f"  {_green('✅ Langue changée : ' + label)}")
        # Relance le bot pour appliquer la nouvelle langue partout
        import subprocess
        print(f"  {_dim('Redémarrage pour appliquer la nouvelle langue...')}")
        subprocess.run([sys.executable, str(_BASE / 'bot.py')])
        sys.exit(0)
    elif choice == 'D':
        _uninstall()
    elif choice == 'M':
        _edit_config_interactive(config)
    elif choice == 'S':
        from src.setup import run_wizard
        run_wizard(config)
    elif choice == '?':
        from src.setup import show_guide
        show_guide()
    elif choice == 'U':
        run_update_cmd()
    print()

def _edit_config_interactive(config):
    """Modifie un paramètre spécifique de la config."""
    print(_header("✏️  Modifier un paramètre"))
    print()
    print(_menu_item(1, "👤 Nom"))
    print(_menu_item(2, "📧 Email"))
    print(_menu_item(3, "💼 LinkedIn"))
    print(_menu_item(4, "📅 Disponibilité"))
    print(_menu_item(5, "🛠️  Skills (virgules)"))
    print(_menu_item(6, "🎓 Formation"))
    print(_menu_item(7, "📍 Ville de recherche"))
    print(_menu_item(8, "🏷️  Code département"))
    print(_menu_item(9, "🎯 Score minimum"))
    print(_menu_item(10, "📆 Âge max offres (jours)"))
    print(_menu_item(11, "🎨 Ton des lettres"))
    print(_menu_item(12, "🔑 France Travail API"))
    print(_menu_item(13, "🔑 SerpApi key"))
    print(_menu_item(14, "🤖 LLM provider (OpenAI, DeepSeek, Claude...)"))
    print(_menu_item(15, "🎯 Catégories de recherche"))  
    print(_menu_item(16, "📄 Template lettre .docx"))
    print(_menu_item(17, "📄 CV .docx"))
    print(_menu_item(18, "📂 Dossier lettres"))
    print(_dim("  [0] Retour"))
    print(_dim("  [0] Retour"))

    choice = input(_dim("  Votre choix : ")).strip()
    profile = config.get("profile", {})
    prefs = config.get("preferences", {})
    loc = prefs.get("location", {})
    matching = config.get("matching", {})
    api = config.get("api", {})
    llm = config.get("llm", {})

    changed = True
    print()

    if choice == '1':
        val = input(f"  Nom [{profile.get('name', '')}] : ").strip()
        if val: profile['name'] = val
    elif choice == '2':
        val = input(f"  Email [{profile.get('email', '')}] : ").strip()
        if val: profile['email'] = val
    elif choice == '3':
        val = input(f"  LinkedIn [{profile.get('linkedin', '')}] : ").strip()
        if val: profile['linkedin'] = val
    elif choice == '4':
        val = input(f"  Disponibilité [{profile.get('available', '')}] : ").strip()
        if val: profile['available'] = val
    elif choice == '5':
        current = ', '.join(profile.get('skills', []))
        val = input(f"  Skills (séparés par virgules) [{current}] : ").strip()
        if val: profile['skills'] = [s.strip() for s in val.split(',') if s.strip()]
    elif choice == '6':
        val1 = input(f"  Diplôme [{profile.get('education_main', '')}] : ").strip()
        val2 = input(f"  École [{profile.get('education_school', '')}] : ").strip()
        if val1: profile['education_main'] = val1
        if val2: profile['education_school'] = val2
    elif choice == '7':
        val1 = input(f"  Ville [{loc.get('city', '')}] : ").strip()
        val2 = input(f"  Pays [{loc.get('country', '')}] : ").strip()
        if val1: loc['city'] = val1
        if val2: loc['country'] = val2
        prefs['location'] = loc
    elif choice == '8':
        val = input(f"  Département [{loc.get('department', '')}] : ").strip()
        if val: loc['department'] = val; prefs['location'] = loc
    elif choice == '9':
        val = input(f"  Score min (1-10) [{matching.get('min_score', 6)}] : ").strip()
        if val and val.isdigit(): matching['min_score'] = int(val)
    elif choice == '10':
        val = input(f"  Âge max (jours) [{prefs.get('max_offer_age_days', 10)}] : ").strip()
        if val and val.isdigit(): prefs['max_offer_age_days'] = int(val)
    elif choice == '11':
        current_tone = config.get('letter_tone', 'professionnel direct')
        print(f"  Ton actuel: {_italic(current_tone)}")
        print(f"  {_dim('Options: professionnel direct / formel classique / décontracté / motivant / autre')}")
        val = input(f"  Nouveau ton [{current_tone}] : ").strip()
        if val: config['letter_tone'] = val
    elif choice == '12':
        ft = api.setdefault('france_travail', {})
        val1 = input(f"  Client ID [{ft.get('client_id', '')}] : ").strip()
        val2 = input(f"  Client Secret [{ft.get('client_secret', '')[:4]}...] : ").strip()
        if val1: ft['client_id'] = val1
        if val2: ft['client_secret'] = val2
    elif choice == '13':
        sa = api.setdefault('serpapi', {})
        val = input(f"  SerpApi Key [{sa.get('api_key', '')[:4]}...] : ").strip()
        if val: sa['api_key'] = val
    elif choice == '14':
        current = llm.get('provider', 'none')
        print(f"  Provider actuel: {_bold(current)}")
        print(f"  {_dim('1=Ollama (local/gratuit)')}")
        print(f"  {_dim('2=Mistral (FR 🇫🇷, tier gratuit)')}")
        print(f"  {_dim('3=OpenAI (payant, meilleure qualité)')}")
        print(f"  {_dim('4=DeepSeek (très bon marché, bon français)')}")
        print(f"  {_dim('5=OpenRouter (Claude, Gemini, GPT...)')}")
        print(f"  {_dim('6=Groq (ultra-rapide, gratuit limité)')}")
        print(f"  {_dim('7=Custom (API OpenAI-compatible)')}")
        print(f"  {_dim('8=Aucun (template seul)')}")
        val = input(f"  Choix [{current}] : ").strip()
        if val == '1': llm['provider'] = 'ollama'; llm['model'] = 'llama3.2'
        elif val == '2':
            llm['provider'] = 'mistral'; llm['model'] = 'mistral-small-2506'
            mk = input(f"  Mistral API Key : ").strip()
            if mk: api.setdefault('mistral', {})['api_key'] = mk
        elif val == '3':
            llm['provider'] = 'openai'; llm['model'] = 'gpt-5.4-mini'
            ok = input(f"  OpenAI API Key : ").strip()
            if ok: api.setdefault('openai', {})['api_key'] = ok
        elif val == '4':
            llm['provider'] = 'deepseek'; llm['model'] = 'deepseek-v4-flash'
            dk = input(f"  DeepSeek API Key : ").strip()
            if dk: api.setdefault('deepseek', {})['api_key'] = dk
        elif val == '5':
            llm['provider'] = 'openrouter'; llm['model'] = 'openai/gpt-5.4-mini'
            rk = input(f"  OpenRouter API Key : ").strip()
            if rk: api.setdefault('openrouter', {})['api_key'] = rk
        elif val == '6':
            llm['provider'] = 'groq'; llm['model'] = 'llama-3.3-70b-versatile'
            gk = input(f"  Groq API Key : ").strip()
            if gk: api.setdefault('groq', {})['api_key'] = gk
        elif val == '7':
            llm['provider'] = 'custom'; llm['model'] = 'gpt-5.4-mini'
            ck = input(f"  Custom API Key : ").strip()
            if ck: api.setdefault('custom', {})['api_key'] = ck
            bu = input(f"  Base URL (endpoint /v1) [{llm.get('base_url', '')}] : ").strip()
            if bu: llm['base_url'] = bu
        elif val == '8': llm['provider'] = 'none'; llm['model'] = ''
    elif choice == '15':
        current = prefs.get('priorities', ['IA & Stratégie', 'Secteur'])
        if not isinstance(current, list) or len(current) < 2:
            current = (current if isinstance(current, list) else [current]) + ['Secteur']
            current = current[:2]
        print(f"  Catégorie A (Tech/IA):  {_cyan(current[0])}")
        print(f"  Catégorie B (Métier):   {_cyan(current[1])}")
        print(f"  {_dim('Ex: IA & Stratégie / Finance & Contrôle de gestion')}")
        val1 = input(f"  Catégorie A [{current[0]}] : ").strip()
        val2 = input(f"  Catégorie B [{current[1]}] : ").strip()
        if val1 or val2:
            prefs['priorities'] = [
                val1 if val1 else current[0],
                val2 if val2 else current[1]
            ]
            # Dérive automatiquement les secteurs depuis les catégories
            derived = []
            for cat in prefs['priorities']:
                cat_low = cat.lower()
                for sector in ['ia', 'ai', 'tech', 'data', 'finance', 'fintech', 'banque', 'saas', 'conseil',
                               'santé', 'automobile', 'luxe', 'marketing', 'rh', 'supply chain', 'logistique']:
                    if sector in cat_low and sector not in derived:
                        derived.append(sector)
            prefs['sectors'] = derived if derived else [prefs['priorities'][1].lower()]
            print(f"  {_green('✅ Catégories:')} {_cyan(prefs['priorities'][0])}  {_dim('|')}  {_cyan(prefs['priorities'][1])}")
        else:
            changed = False
    elif choice == '16':
        print(f"  {_dim('Ouverture du sélecteur de fichier...')}")
        from src.setup import _pick_file
        picked = _pick_file("Sélectionnez votre template .docx", [("Word documents", "*.docx")])
        if picked:
            config['_letter_template_path'] = str(Path(picked).resolve())
            print(f"  {_green('✅ Template enregistré:')} {_cyan(str(Path(picked).resolve()))}")
        else:
            val = input(f"  Ou collez le chemin [{config.get('_letter_template_path', '')}] : ").strip()
            if val and Path(val).exists():
                config['_letter_template_path'] = str(Path(val).resolve())
                print(f"  {_green('✅ Template enregistré.')}")
            elif val:
                print(f"  {_red(f'Fichier introuvable: {val}')}")
                changed = False
    elif choice == '17':
        print(f"  {_dim('Ouverture du sélecteur de fichier...')}")
        from src.setup import _pick_file
        picked = _pick_file("Sélectionnez votre CV .docx", [("Word documents", "*.docx")])
        if picked:
            config['_cv_path'] = str(Path(picked).resolve())
            print(f"  {_green('✅ CV enregistré:')} {_cyan(str(Path(picked).resolve()))}")
        else:
            val = input(f"  Ou collez le chemin [{config.get('_cv_path', '')}] : ").strip()
            if val and Path(val).exists():
                config['_cv_path'] = str(Path(val).resolve())
                print(f"  {_green('✅ CV enregistré.')}")
            elif val:
                print(f"  {_red(f'Fichier introuvable: {val}')}")
                changed = False
    elif choice == '18':
        current = config.get('_letters_dir', str(LETTERS_DIR))
        val = input(f"  Dossier lettres [{current}] : ").strip()
        if val:
            p = Path(val.strip('"').strip("'"))
            p.mkdir(parents=True, exist_ok=True)
            config['_letters_dir'] = str(p.resolve())
            print(f"  {_green('✅ Dossier lettres:')} {_cyan(str(p.resolve()))}")
        else:
            changed = False
    elif choice == '19':
        # Supprimé — les secteurs sont maintenant dérivés automatiquement des catégories
        print(f"  {_dim('Les secteurs sont dérivés de vos catégories de recherche.')}")
        print(f"  {_dim('Modifiez-les via le choix 15 — Catégories de recherche.')}")
        changed = False
    elif choice == '0':
        changed = False
    else:
        print(f"  {_red('Choix invalide.')}"); return

    # Réaffecter
    config['profile'] = profile
    config['preferences'] = prefs
    config['matching'] = matching
    config['api'] = api
    config['llm'] = llm

    if changed:
        save_config(config)
        print(f"\n  {_green('✅ Configuration mise à jour.')}")
        print(f"  {_dim('↳ Modifications actives immédiatement — pas besoin de redémarrer.')}")
    print()

def menu_prompt():
    print(_header("🎤 Mise à jour des critères"))
    print(f"  {_dim('Décrivez ce que vous cherchez en une ou plusieurs phrases :')}")
    example = 'Ex: "Je cherche un poste de Head of AI dans la finance, Paris uniquement"'
    print(f"  {_dim(example)}")
    print(f"  {_bold('👉 Appuyez sur ENTREE deux fois pour valider (une fois pour finir la saisie, la seconde pour confirmer)')}")
    print()
    lines = []
    while True:
        try:
            line = input("  > ")
        except EOFError:
            break
        if line.strip() == "":
            if lines:
                break  # Première ligne vide : fin de saisie
            else:
                continue  # Ignore les lignes vides au début
        lines.append(line)
    prompt_text = "\n".join(lines)
    if not prompt_text.strip():
        print(f"  {_yellow('Aucune saisie. Annulé.')}")
        return
    config = load_config()
    config = interpret_prompt(config, prompt_text)
    save_config(config)
    print(f"\n  {_green('✅ Critères mis à jour.')}")
    print(f"  {_dim('↳ Tapez [1] pour lancer un scan avec vos nouveaux critères.')}")

def menu_candidatures():
    if not CANDIDATURES_PATH.exists():
        print("  " + _yellow("Aucune candidature enregistrée."))
        return
    text = open(CANDIDATURES_PATH, "r", encoding="utf-8").read()
    print(_header("📝 Suivi des Candidatures"))
    print()
    for line in text.split("\n"):
        if line.strip().startswith("|"):
            if "✅ Postulé" in line:
                print(f"  {_cyan(line)}")
            elif "📞 Entretien" in line:
                print(f"  {_green(line)}")
            elif "❌ Refus" in line:
                print(f"  {_red(line)}")
            else:
                print(f"  {line}")
        else:
            print(f"  {_dim(line)}")
    print()


def run_update_cmd():
    """Lance la mise à jour depuis le menu."""
    from src.updater import run_update
    print()
    ans = input(f"  {_dim('Mettre à jour TOM ? Vos données resteront intactes [y/n] : ')}").strip().lower()
    if ans in ('y', 'yes', 'oui'):
        run_update()
    else:
        print(f"  {_dim('Annulé.')}")


def _uninstall():
    """Désinstalle TOM avec triple confirmation."""
    print()
    print(f"  {_red('⚠️  DÉSINSTALLATION DE TOM')}")
    print(f"  {_dim('Cette action est IRRÉVERSIBLE.')}")
    print(f"  {_dim('Vos données (offres, candidatures, config) seront PERDUES.')}")
    print()
    
    # Confirmation 1
    msg1 = 'Tapez "desinstaller" pour confirmer : '
    ans1 = input(f"  {_red(msg1)}").strip()
    if ans1 != "desinstaller":
        print(f"  {_dim('Annulé.')}")
        return
    
    # Confirmation 2
    msg2 = 'Tapez "oui" pour confirmer une seconde fois : '
    ans2 = input(f"  {_red(msg2)}").strip()
    if ans2.lower() != "oui":
        print(f"  {_dim('Annulé.')}")
        return
    
    # Confirmation 3
    msg3 = 'Dernière chance — tapez "SUPPRIMER" pour tout effacer : '
    ans3 = input(f"  {_red(msg3)}").strip()
    if ans3 != "SUPPRIMER":
        print(f"  {_dim('Annulé.')}")
        return
    
    print(f"  {_red('Suppression en cours...')}")
    import shutil
    base = _BASE
    desktop = Path.home() / "Desktop"
    
    # Supprime les raccourcis bureau
    for shortcut in ["TOM Job Hunter.lnk", "TOM Job Hunter.bat", "TOM Job Hunter.command"]:
        sp = desktop / shortcut
        if sp.exists():
            sp.unlink(missing_ok=True)
            print(f"  {_dim('Raccourci bureau supprimé : ' + shortcut)}")
    
    # Supprime le dossier d'installation
    try:
        shutil.rmtree(base, ignore_errors=False)
    except Exception:
        shutil.rmtree(base, ignore_errors=True)  # Force brute si échec (fichiers verrouillés)
    print(f"  {_green('✅ TOM a été désinstallé.')}")
    print(f"  {_dim('Au revoir !')}")
    sys.exit(0)


def _check_update_on_start():
    """Vérifie discrètement si une mise à jour est disponible."""
    try:
        from src.updater import check_for_updates
        update_avail, remote_ver = check_for_updates()
        if update_avail:
            ver_str = f"v{remote_ver}" if remote_ver else ""
            print(f"\n  {_yellow('🔔 Mise à jour disponible')} {_cyan(ver_str)}")
            print(f"  {_dim('Lancez')} {_cyan('python bot.py update')} {_dim('pour mettre à jour (vos données sont protégées).')}")
            print()
    except Exception as e:
        # Silencieux — ne pas bloquer le démarrage
        if os.environ.get("TOM_DEBUG"):
            print(f"  {_dim('[DEBUG] check_update: {e}')}")


def _show_token_usage():
    """Affiche la consommation de tokens LLM depuis le début de la session."""
    usage = get_token_usage()
    if usage["calls"] == 0:
        return
    inp = usage["input"]
    out = usage["output"]
    total = inp + out
    calls = usage["calls"]
    print(f"\n  {_dim('📊 Tokens LLM — ')}", end="")
    print(f"{_dim(f'{inp:,} in + {out:,} out = {total:,} total')}", end="")
    print(f"{_dim(f' ({calls} appel(s))')}")
    if usage.get("last_error"):
        print(f"  {_yellow('⚠️  Dernière erreur: ' + usage['last_error'])}")
    if usage.get("last_error"):
        print(f"  {_yellow('⚠️  Dernière erreur: ' + usage['last_error'])}")


# ── Setup ─────────────────────────────────────────────────────

def run_guide():
    from src.setup import show_guide
    print()
    show_guide()


# ── Boucle principale ─────────────────────────────────────────

def main_loop():
    # Vérification de mise à jour au démarrage (discret)
    _check_update_on_start()
    while True:
        show_header()
        choice = menu_main()

        if choice == "0":
            print(f"\n  {_green('TOM V2.0 — À bientôt ! 👋👋')}")
            print(f"  {_dim(LICENSE)} | {_dim('🔗')} {_cyan(CREATOR_LINKEDIN)} | {_dim('🐙')} {_cyan(CREATOR_GITHUB)}")
            print()
            break
        elif choice == "1":
            menu_scan()
        elif choice == "2":
            menu_dashboard()
        elif choice == "3":
            menu_offers()
        elif choice == "4":
            menu_postuler()
        elif choice == "5":
            menu_entretien()
        elif choice == "6":
            menu_rejet()
        elif choice == "7":
            menu_lettres()
        elif choice == "8":
            menu_config()
        elif choice == "9":
            menu_prompt()
        elif choice == "10":
            menu_candidatures()
        elif choice == "11":
            menu_voir_lettres()
        elif choice.upper() == "U":
            from src.updater import run_update
            print()
            ans = input(f"  {_dim('Mettre à jour TOM ? Vos données resteront intactes. Redémarrage automatique après. [y/n] : ')}").strip().lower()
            if ans in ('y', 'yes', 'oui'):
                run_update()
                print(f"  {_green('✅ Mise à jour terminée. Redémarrage...')}")
                # Relancer bot.py
                import subprocess
                subprocess.run([sys.executable, str(_BASE / 'bot.py')])
                sys.exit(0)
            else:
                print(f"  {_dim('Annulé.')}")
        else:
            if choice.lower() == "setup":
                run_setup()
            elif choice.lower() == "guide":
                run_guide()
            elif choice.lower() in ("update", "u"):
                run_update_cmd()
            else:
                print(f"  {_red('Choix invalide.')}")

        input(_dim("\n  Appuyez sur Entrée pour continuer..."))


if __name__ == "__main__":
    main_loop()
