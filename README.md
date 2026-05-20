# 🔍 TOM V2.0 — Agent Personnel de Recherche d'Emploi / Personal Job Search Agent

> 🇫🇷 Votre bot CLI qui scanne les offres, match votre profil, génère des lettres de motivation et suit vos candidatures.
> 🇬🇧 Your CLI bot that scans job listings, matches your profile, generates cover letters, and tracks applications.

**Auteur / Author** : [Matthias Dubois](https://www.linkedin.com/in/matthias-dubois/) — [@theturbos](https://github.com/theturbos)  
**Licence / License** : Propriétaire — Tous droits réservés. Usage personnel autorisé, redistribution interdite. Voir [LICENSE](LICENSE).  
**🇫🇷 Unique en France** — seul agent de recherche d'emploi couplant NLP et génération automatique de lettres.

---

## 🚀 Installation en 1 ligne / 1-line install

### macOS / Linux
```bash
curl -sSL https://raw.githubusercontent.com/theturbos/tom-job-hunter/main/install.sh | bash
```

### Windows (PowerShell)
```powershell
iwr -useb https://raw.githubusercontent.com/theturbos/tom-job-hunter/main/install.bat -outfile "$env:TEMP\tom-install.bat"; cmd /c "%TEMP%\tom-install.bat"
```

**L'installateur / The installer :**
1. ✅ Vérifie Python 3 et Git / Checks Python 3 & Git
2. 📂 Clone le repo dans `~/.tom-job-hunter` (ou `%USERPROFILE%\.tom-job-hunter`)
3. 🐍 Crée un virtualenv + dépendances / Creates venv + dependencies
4. 📌 Crée un raccourci Bureau avec icône / Creates Desktop shortcut with icon
5. ⚙️ Lance le wizard interactif / Launches setup wizard

---

## ⚙️ Setup Wizard

| Étape / Step | Question |
|-------|----------|
| 👤 Profil | Nom, email, LinkedIn, disponibilité / Name, email, availability |
| 🎯 Priorités | IA Stratégie / Finance+IA / Scale-up / Autre |
| 🛠️ Skills | Python, LLM, FP&A, Power BI, SQL... |
| 🎓 Formation | Diplôme + école / Degree + school |
| 📍 Localisation | Ville + département / City + region |
| 🎯 Critères | Prompt en langage naturel ("Head of AI en finance à Paris") |
| 🔑 APIs | France Travail (gratuit/free) + SerpApi (100 req/mois free) |
| 🤖 LLM | Ollama (local) / Mistral / OpenAI / DeepSeek / Groq / OpenRouter |
| 📄 CV | Upload .docx — extraction compétences / skills extraction |
| ✉️ Template | Template lettre .docx — garde votre formatage / preserves formatting |

---

## 📖 Utilisation / Usage

```bash
cd ~/.tom-job-hunter
source .venv/bin/activate   # Windows : .venv\Scripts\activate
python bot.py
```

**Menu principal / Main menu :**

```
[1] 🔍 Scanner les offres / Scan jobs
[2] 📊 Dashboard / Statistiques
[3] 📋 Voir les offres / Browse offers
[4] ✅ J'ai postulé / Mark applied
[5] 📞 Entretien obtenu / Got interview
[6] ❌ Rejet reçu / Got rejected
[7] ✍️  Générer des lettres / Generate cover letters
[8] ⚙️  Changer la config / Edit config
[9] 🎤 Prompt — Mettre à jour mes critères / Update search criteria
[10] 📝 Voir candidatures / View applications
[0] 🚪 Quitter / Quit
```

**Workflow type :**
1. `[1]` Scanner → trouve des offres / finds matching listings
2. `[3]` Voir les offres → scores 1-10/10
3. `[7]` Générer lettres → crée des .docx personnalisées / custom .docx
4. `[4]` J'ai postulé → met à jour le suivi / updates tracker
5. `[2]` Dashboard → pipeline complet

---

## 🏗️ Architecture

```
tom-job-hunter/
├── bot.py              ← Menu CLI principal / Main CLI
├── install.sh          ← Installateur macOS/Linux
├── install.bat         ← Installateur Windows
├── requirements.txt    ← 3 dépendances légères / lightweight deps
├── config.example.yaml ← Template de config anonymisé
├── assets/
│   ├── icon.png        ← Icône TOM 256×256
│   └── icon.ico        ← Icône Windows
├── src/
│   ├── scanner.py      ← France Travail + SerpApi + Web fallback
│   ├── matcher.py      ← Scoring offres vs profil / job scoring
│   ├── letter_engine.py ← Génération lettres LLM + anti-patterns IA
│   ├── cv_parser.py    ← Extraction passive CV (.docx)
│   ├── prompt_engine.py ← NLP → config structurée + regex fallback
│   ├── setup.py        ← Wizard interactif + guide débutant
│   └── updater.py      ← MàJ auto (git pull / zip) sans toucher data/
├── data/               ← ⚡ Données utilisateur (non commité)
│   ├── config.yaml
│   ├── offres.md
│   ├── candidatures.md
│   └── doublons.md
└── lettres/            ← ⚡ Lettres générées (non commité)
```

---

## 🔑 APIs

| API | Prix / Price | Usage |
|-----|------|-------|
| **France Travail** | Gratuit / Free | 🇫🇷 Offres officielles France (500k+) |
| **SerpApi** | 100 req/mois gratuites | Google Jobs (LinkedIn, WTTJ, Indeed, Apec...) |

**Guide France Travail :**
1. https://www.emploi-store.fr/portail/ → créez un compte / create account
2. Mes applications → nouvelle application → API "Offres d'emploi"
3. Copiez Client ID + Client Secret

**Guide SerpApi :**
1. https://serpapi.com/ → créez un compte gratuit / free account
2. Dashboard → copiez l'API key

---

## 🤖 Fournisseurs IA / AI Providers

| Provider | Prix / Price | Qualité | Localisation données |
|----------|------|---------|---------------------|
| **Ollama** | Gratuit / Free | Bonne / Good | 🟢 100% local |
| **Mistral AI** 🇫🇷 | Tier gratuit / Free tier | Très bonne / Very good | ☁️ Cloud (UE) |
| **OpenAI** | ~$0.02/lettre | Excellente / Excellent | ☁️ Cloud (US) |
| **DeepSeek** | Très bon marché / Cheap | Excellent FR | ☁️ Cloud (CN) |
| **Groq** | Gratuit (limité) / Free tier | Très rapide / Very fast | ☁️ Cloud (US) |
| **OpenRouter** | Pay-per-use | Claude, Gemini, GPT... | ☁️ Cloud (US) |
| **Aucun / None** | — | Template seul / Template only | 🟢 100% local |

---

## 🛡️ Vie privée / Privacy

### 🟢 Local (Ollama)
- **100% de vos données restent sur votre machine.**
- Aucune donnée personnelle, offre, lettre ou config ne sort.
- Seules les APIs de scan (France Travail, SerpApi) envoient vos mots-clés de recherche.
- **Recommandé si vous traitez des données sensibles.**

### ☁️ Cloud (Mistral, OpenAI, DeepSeek, Groq, OpenRouter)
- **Votre profil, CV et offres sont envoyés au fournisseur LLM** pour générer les lettres.
- Ces données transitent par les serveurs du fournisseur et sont soumises à leur politique de confidentialité.
- Vos fichiers `data/` et `lettres/` restent sur votre machine — seul le contenu nécessaire à la génération est transmis.
- Choisissez un fournisseur selon votre niveau de confiance (Mistral = 🇫🇷 UE, données sous RGPD).

### ⚪ Aucun LLM
- Aucune donnée ne sort. Lettres générées par template uniquement.
- Moins personnalisé mais 100% confidentiel.

---

## 🐛 Troubleshooting

| Problème / Problem | Solution |
|----------|----------|
| `ModuleNotFoundError` | `source .venv/bin/activate && pip install -r requirements.txt` |
| Scan retourne 0 offres / 0 results | Configurer France Travail API dans `[8] Changer la config` |
| Ollama ne répond pas / not responding | `ollama serve` puis réessayer. Ou passez à Mistral (cloud gratuit). |
| Lettres vides / empty letters | Vérifier `_letter_template_path` dans `data/config.yaml` |
| Windows : accents cassés / broken accents | `chcp 65001` dans cmd avant de lancer |
| Erreur "git non trouvé" | Git optionnel — l'installateur fonctionne sans via téléchargement zip |

---

## 📝 Licence / License

**Propriétaire — Tous droits réservés / Proprietary — All rights reserved.**

- ✅ Usage personnel autorisé / Personal use allowed
- ❌ Redistribution, modification, intégration commerciale interdites
- ❌ No redistribution, modification, or commercial integration
- Voir / See [LICENSE](LICENSE) pour le texte complet.

---

## 🤝 Contribuer / Contributing

Pull requests bienvenues. Ouvrez une issue avant les gros changements.
Pull requests welcome. Open an issue before major changes.

---

## ✨ Fonctionnalités / Features

- 🔍 **Scan multi-source** : France Travail, SerpApi (Google Jobs → LinkedIn, WTTJ, Indeed, Apec), pages careers
- 🎯 **Scoring dynamique** : vos mots-clés extraits de votre prompt, secteurs IA/secteur, pénalités intelligentes
- 🧠 **NLP intégré** : écrivez "Head of AI en finance à Paris" → TOM comprend et configure tout
- ✍️ **Lettres .docx personnalisées** : template cloné (votre formatage préservé), nettoyage anti-patterns IA
- 🤖 **7 providers LLM** : Ollama, Mistral, OpenAI, DeepSeek, Groq, OpenRouter, ou aucun
- 📊 **Dashboard** : pipeline de candidatures, stats, offres par catégorie
- 🔄 **Updater intégré** : `python bot.py update` — vos données intactes
- 🪟🍎🐧 **Cross-platform** : Windows, macOS, Linux
- 🔒 **Privacy-first** : vos données, votre machine, votre choix du provider

---

*Fait avec ❤️ par / Made with ❤️ by [Matthias Dubois](https://www.linkedin.com/in/matthias-dubois/) — [@theturbos](https://github.com/theturbos)*
