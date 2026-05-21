"""
i18n.py — Traductions FR/EN pour TOM V2.0
Utilise config._lang ("fr" ou "en").
"""

import yaml
from pathlib import Path

_CONFIG_PATH = Path("data/config.yaml")

TEXTS = {
    # ── Menu principal ──
    "menu_title": {
        "fr": "TOM V2.0 — Agent Personnel de Recherche d'Emploi",
        "en": "TOM V2.0 — Personal Job Search Agent",
    },
    "scan": {"fr": "🔍 Scanner les offres", "en": "🔍 Scan job offers"},
    "dashboard": {"fr": "📊 Dashboard & Statistiques", "en": "📊 Dashboard & Statistics"},
    "view_offers": {"fr": "📋 Voir les offres", "en": "📋 View offers"},
    "applied": {"fr": "✅ J'ai postulé", "en": "✅ I applied"},
    "interview": {"fr": "📞 Entretien obtenu", "en": "📞 Got an interview"},
    "rejected": {"fr": "❌ Rejet reçu", "en": "❌ Received rejection"},
    "letters": {"fr": "✍️  Générer des lettres", "en": "✍️  Generate cover letters"},
    "open_letters": {"fr": "📂 Voir mes lettres", "en": "📂 Open letters folder"},
    "config": {"fr": "⚙️  Changer la config", "en": "⚙️  Change config"},
    "prompt": {"fr": "🎤 Prompt — Changer mes critères", "en": "🎤 Prompt — Update my criteria"},
    "candidatures": {"fr": "📝 Voir candidatures", "en": "📝 View applications"},
    "update": {"fr": "🔄 Mettre à jour TOM", "en": "🔄 Update TOM"},
    "quit": {"fr": "🚪 Quitter", "en": "🚪 Quit"},
    "choice_prompt": {"fr": " Votre choix : ", "en": " Your choice : "},
    "invalid_choice": {"fr": "Choix invalide.", "en": "Invalid choice."},
    "goodbye": {"fr": "TOM V2.0 — À bientôt ! 👋👋", "en": "TOM V2.0 — See you soon! 👋👋"},
    "press_enter": {"fr": "Appuyez sur Entrée pour continuer...", "en": "Press Enter to continue..."},

    # ── Dashboard ──
    "dash_title": {"fr": "📊 Dashboard — Statistiques", "en": "📊 Dashboard — Statistics"},
    "dash_kpi_offers": {"fr": "📋 Offres actives", "en": "📋 Active offers"},
    "dash_kpi_score": {"fr": "⭐ Score moyen", "en": "⭐ Avg score"},
    "dash_kpi_letters": {"fr": "✍️  Lettres prêtes", "en": "✍️  Letters ready"},
    "dash_kpi_dupes": {"fr": "♻️  Doublons filtrés", "en": "♻️  Duplicates filtered"},
    "dash_categories": {"fr": "📂 Catégories", "en": "📂 Categories"},
    "dash_pipeline": {"fr": "📊 Pipeline", "en": "📊 Pipeline"},
    "dash_top": {"fr": "🏆 Top offres", "en": "🏆 Top offers"},
    "dash_col_score": {"fr": "Score", "en": "Score"},
    "dash_col_company": {"fr": "Entreprise", "en": "Company"},
    "dash_col_title": {"fr": "Poste", "en": "Position"},
    "dash_col_cat": {"fr": "Cat", "en": "Cat"},
    "dash_col_letter": {"fr": "Lettre", "en": "Letter"},
    "dash_total_offers": {"fr": "{} offres", "en": "{} offers"},
    "dash_letters": {"fr": "{} lettres", "en": "{} letters"},
    "dash_applied": {"fr": "{} postulées", "en": "{} applied"},
    "dash_interviews": {"fr": "{} entretiens", "en": "{} interviews"},
    "dash_rejected": {"fr": "{} rejets", "en": "{} rejected"},

    # ── Config ──
    "config_title": {"fr": "⚙️ Configuration", "en": "⚙️ Configuration"},
    "config_profile": {"fr": "PROFIL", "en": "PROFILE"},
    "config_name": {"fr": "Nom", "en": "Name"},
    "config_email": {"fr": "Email", "en": "Email"},
    "config_linkedin": {"fr": "LinkedIn", "en": "LinkedIn"},
    "config_dispo": {"fr": "Dispo", "en": "Available"},
    "config_skills": {"fr": "Skills", "en": "Skills"},
    "config_education": {"fr": "Formation", "en": "Education"},
    "config_search": {"fr": "RECHERCHE", "en": "SEARCH"},
    "config_city": {"fr": "Ville", "en": "City"},
    "config_dept": {"fr": "Département", "en": "Department"},
    "config_min_score": {"fr": "Min score", "en": "Min score"},
    "config_max_age": {"fr": "Max âge", "en": "Max age"},
    "config_tone": {"fr": "Ton lettres", "en": "Letter tone"},
    "config_apis": {"fr": "APIs", "en": "APIs"},
    "config_ft": {"fr": "France Travail", "en": "France Travail"},
    "config_serp": {"fr": "SerpApi", "en": "SerpApi"},
    "config_llm": {"fr": "LLM", "en": "LLM"},
    "config_provider": {"fr": "Provider", "en": "Provider"},
    "config_template": {"fr": "Template", "en": "Template"},
    "config_cv": {"fr": "CV", "en": "Resume"},
    "config_configured": {"fr": "CONFIGURÉ", "en": "CONFIGURED"},
    "config_not_configured": {"fr": "NON CONFIGURÉ", "en": "NOT CONFIGURED"},
    "config_none": {"fr": "NON", "en": "NO"},
    "config_unknown": {"fr": "—", "en": "—"},
    "config_lang": {"fr": "Langue", "en": "Language"},
    "config_lang_fr": {"fr": "🇫🇷 Français", "en": "🇫🇷 French"},
    "config_lang_en": {"fr": "🇬🇧 English", "en": "🇬🇧 English"},
    "config_uninstall": {"fr": "Désinstaller TOM", "en": "Uninstall TOM"},
    "config_modify": {"fr": "Modifier un paramètre", "en": "Modify a setting"},
    "config_resetup": {"fr": "Relancer le setup wizard", "en": "Restart setup wizard"},
    "config_help": {"fr": "Aide / Guide débutant", "en": "Help / Beginner's guide"},
    "config_update": {"fr": "Mettre à jour TOM", "en": "Update TOM"},
    "config_return": {"fr": "[Entrée] Retour", "en": "[Enter] Back"},
    "config_lang_changed_fr": {"fr": "✅ Langue changée : 🇫🇷 Français", "en": "✅ Language changed: 🇫🇷 French"},
    "config_lang_changed_en": {"fr": "✅ Langue changée : 🇬🇧 English", "en": "✅ Language changed: 🇬🇧 English"},
    "config_restart_lang": {"fr": "Redémarrage pour appliquer la nouvelle langue...", "en": "Restarting to apply the new language..."},

    # ── Scan ──
    "scan_title": {"fr": "🔍 Scan des offres", "en": "🔍 Job scan"},
    "scan_starting": {"fr": "Lancement du scan...", "en": "Starting scan..."},
    "scan_complete": {"fr": "Scan terminé.", "en": "Scan complete."},
    "scan_cancelled": {"fr": "Scan annulé. Aucune offre enregistrée.", "en": "Scan cancelled. No offers saved."},
    "no_offer_to_mark": {"fr": "Aucune offre à marquer. Scannez d'abord.", "en": "No offers to mark. Run a scan first."},
    "invalid_number": {"fr": "Numéro invalide.", "en": "Invalid number."},
    "scan_no_api": {"fr": "⚠️  Aucune API configurée. Configurez au moins France Travail dans [8] Configuration.", "en": "⚠️  No API configured. Configure at least France Travail in [8] Configuration."},

    # ── Offres ──
    "offers_title": {"fr": "📋 Offres Trouvées", "en": "📋 Found Offers"},
    "offers_empty": {"fr": "Aucune offre trouvée. Lancez un scan [1].", "en": "No offers found. Run a scan [1]."},

    # ── Lettres ──
    "letters_gen": {"fr": "✍️  Génération de lettres", "en": "✍️  Generating cover letters"},
    "letters_confirm": {"fr": "Générer des lettres pour les offres sans lettre?", "en": "Generate letters for offers without one?"},
    "letters_cancelled": {"fr": "Annulé.", "en": "Cancelled."},

    # ── Postuler / Entretien / Rejet ──
    "apply_which": {"fr": "Quelle offre (numéro) ?", "en": "Which offer (number)?"},
    "interview_which": {"fr": "Quelle offre (numéro) ?", "en": "Which offer (number)?"},
    "reject_which": {"fr": "Quelle offre (numéro) ?", "en": "Which offer (number)?"},
    "apply_ok": {"fr": "Offre marquée comme postulée.", "en": "Offer marked as applied."},
    "interview_ok": {"fr": "Statut mis à jour : Entretien.", "en": "Status updated: Interview."},
    "reject_ok": {"fr": "Statut mis à jour : Refus.", "en": "Status updated: Rejected."},

    # ── Prompt ──
    "prompt_title": {"fr": "🎤 Prompt — Modifier vos critères", "en": "🎤 Prompt — Update your criteria"},
    "prompt_help": {"fr": "Décrivez ce que vous cherchez en langage naturel :", "en": "Describe what you're looking for in natural language:"},
    "prompt_saved": {"fr": "✅ Prompt enregistré.", "en": "✅ Prompt saved."},

    # ── Update ──
    "update_confirm": {"fr": "Mettre à jour TOM ? Vos données resteront intactes. Redémarrage automatique après. [y/n] : ", "en": "Update TOM? Your data will stay safe. Auto-restart after. [y/n] : "},
    "update_ok": {"fr": "✅ Mise à jour terminée. Redémarrage...", "en": "✅ Update complete. Restarting..."},
    "update_cancelled": {"fr": "Annulé.", "en": "Cancelled."},

    # ── Uninstall ──
    "uninstall_title": {"fr": "⚠️  DÉSINSTALLATION DE TOM", "en": "⚠️  UNINSTALL TOM"},
    "uninstall_irrev": {"fr": "Cette action est IRRÉVERSIBLE.", "en": "This action is IRREVERSIBLE."},
    "uninstall_data": {"fr": "Vos données (offres, candidatures, config) seront PERDUES.", "en": "Your data (offers, applications, config) will be LOST."},
    "uninstall_step1": {"fr": "Tapez \"desinstaller\" pour confirmer : ", "en": "Type \"desinstaller\" to confirm: "},
    "uninstall_step2": {"fr": "Tapez \"oui\" pour confirmer une seconde fois : ", "en": "Type \"oui\" to confirm a second time: "},
    "uninstall_step3": {"fr": "Dernière chance — tapez \"SUPPRIMER\" pour tout effacer : ", "en": "Last chance — type \"SUPPRIMER\" to erase everything: "},
    "uninstall_deleting": {"fr": "Suppression en cours...", "en": "Deleting..."},
    "uninstall_shortcut_removed": {"fr": "Raccourci bureau supprimé : ", "en": "Desktop shortcut removed: "},
    "uninstall_done": {"fr": "✅ TOM a été désinstallé.", "en": "✅ TOM has been uninstalled."},
    "uninstall_bye": {"fr": "Au revoir !", "en": "Goodbye!"},

    # ── Setup / Wizard ──
    "setup_no_config": {"fr": "⚠️  Aucune configuration trouvée.", "en": "⚠️  No configuration found."},
    "setup_launching": {"fr": "Lancement du wizard d'installation...", "en": "Launching setup wizard..."},
    "setup_done": {"fr": "✅ Configuration créée avec succès !", "en": "✅ Configuration created successfully!"},
    "setup_restart": {"fr": "Redémarrage de TOM...", "en": "Restarting TOM..."},
    "setup_empty": {"fr": "Configuration vide.", "en": "Empty configuration."},
    "setup_exit": {"fr": "Configuration annulée. Au revoir !", "en": "Configuration cancelled. Goodbye!"},

    # ── Candidatures ──
    "cand_title": {"fr": "📝 Suivi des Candidatures", "en": "📝 Application Tracker"},
    "cand_empty": {"fr": "Aucune candidature enregistrée.", "en": "No applications tracked yet."},

    # ── Update notification ──
    "update_available": {"fr": "🔔 Mise à jour disponible :", "en": "🔔 Update available:"},
    "update_how": {"fr": "Lancez [U] pour mettre à jour (vos données sont protégées).", "en": "Run [U] to update (your data is protected)."},

    # ── Letter tone ──
    "ton_professionnel_direct": {"fr": "professionnel direct", "en": "direct professional"},
}


def _current_lang():
    """Lit la langue depuis config.yaml, défaut 'fr'."""
    try:
        if _CONFIG_PATH.exists():
            with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return (data or {}).get("_lang", "fr")
    except Exception:
        pass
    return "fr"


def t(key, *args, lang=None):
    """Traduit une clé. args = format arguments."""
    if lang is None:
        lang = _current_lang()
    text = TEXTS.get(key, {}).get(lang)
    if text is None:
        # Fallback FR
        text = TEXTS.get(key, {}).get("fr", f"??{key}??")
    if args:
        return text.format(*args)
    return text
