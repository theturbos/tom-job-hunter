# 🔍 TOM V2.0 — Agent Personnel de Recherche d'Emploi

> Votre bot CLI qui scanne les offres, match votre profil, génère des lettres de motivation et suit vos candidatures — 100% local, 100% privé.

**Auteur** : [Matthias Dubois](https://www.linkedin.com/in/matthias-dubois/) — [@theturbos](https://github.com/theturbos)  
**Licence** : Propriétaire — Tous droits réservés. Usage personnel autorisé, redistribution interdite. Voir [LICENSE](LICENSE).

---

## 🚀 Installation en 1 ligne

### macOS / Linux
```bash
curl -sSL https://raw.githubusercontent.com/theturbos/tom-job-hunter/main/install.sh | bash
```

### Windows (PowerShell admin)
```powershell
iwr -useb https://raw.githubusercontent.com/theturbos/tom-job-hunter/main/install.bat -outfile "$env:TEMP\tom-install.bat" && cmd /c "%TEMP%\tom-install.bat"
```

Le script d'installation :
1. ✅ Vérifie Python 3 et Git
2. 📂 Clone le repo dans `~/.tom-job-hunter` (ou `%USERPROFILE%\.tom-job-hunter`)
3. 🐍 Crée un virtualenv et installe les dépendances
4. ⚙️ Lance le **wizard interactif** qui configure tout

---

## ⚙️ Setup Wizard (inclus dans l'install)

Le wizard vous guide étape par étape :

| Étape | Question |
|-------|----------|
| 👤 Profil | Nom, email, LinkedIn, dispo |
| 🎯 Priorités | Classez : IA Stratégie / Finance+IA / Scale-up... |
| 🛠️ Skills | Vos compétences (Python, LLM, FP&A...) |
| 🎓 Formation | Diplôme + école |
| 📍 Localisation | Ville + pays de recherche |
| 🎯 Critères | Décrivez en langage naturel ce que vous cherchez |
| 🔑 APIs | France Travail (gratuit) + SerpApi (gratuit) |
| 🤖 LLM | Ollama (local/gratuit) / Mistral (FR/gratuit) / OpenAI |
| 📄 CV | Upload passif (.docx) — extraction keywords |
| ✉️ Template | Template lettre (.docx) — clonage formatage |

---

## 📖 Utilisation

```bash
cd ~/.tom-job-hunter
source .venv/bin/activate   # Windows : .venv\Scripts\activate
python bot.py
```

**Menu principal :**

```
[1] 🔍 Scanner les offres
[2] 📊 Dashboard / Statistiques
[3] 📋 Voir les offres
[4] ✅ J'ai postulé
[5] ❌ Rejet reçu
[6] ✍️  Générer des lettres
[7] ⚙️  Changer la config
[8] 🎤 Prompt — Mettre à jour mes critères
[9] 📝 Voir candidatures
[0] 🚪 Quitter
```

**Exemple de workflow :**
1. `[1]` Scanner → trouve 12 offres pertinentes
2. `[3]` Voir les offres → scores 6-10/10
3. `[6]` Générer lettres → crée des .docx personnalisées
4. `[4]` J'ai postulé → met à jour le suivi
5. `[2]` Dashboard → récapitulatif pipeline

---

## 🏗️ Architecture

```
tom-job-hunter/
├── bot.py              ← Menu CLI principal
├── install.sh          ← Installateur macOS/Linux
├── install.bat         ← Installateur Windows
├── requirements.txt    ← Dépendances (4 libs)
├── config.example.yaml ← Template de config
├── src/
│   ├── scanner.py      ← France Travail + SerpApi + Web
│   ├── matcher.py      ← Scoring offres vs profil
│   ├── letter_engine.py ← Génération lettres LLM + .docx
│   ├── cv_parser.py    ← Extraction passive CV
│   ├── prompt_engine.py ← NLP → config structurée
│   └── setup.py        ← Wizard interactif
├── data/               ← Données utilisateur (non commité)
│   ├── config.yaml
│   ├── offres.md
│   ├── candidatures.md
│   └── doublons.md
└── lettres/            ← Lettres générées
```

---

## 🔑 APIs requises

| API | Prix | Usage |
|-----|------|-------|
| **France Travail** | Gratuit | Offres officielles France (500k+) |
| **SerpApi** | 100 req/mois gratuits | Google Jobs (LinkedIn, WTTJ, Indeed...) |

**Guide France Travail :**
1. https://www.emploi-store.fr/portail/ → créez un compte
2. Mes applications → nouvelle application → API "Offres d'emploi"
3. Copiez Client ID + Client Secret

**Guide SerpApi :**
1. https://serpapi.com/ → créez un compte gratuit
2. Dashboard → copiez l'API key

---

## 🤖 Fournisseurs IA pour les lettres

| Provider | Prix | Qualité |
|----------|------|---------|
| **Ollama** | Gratuit, 100% local | Bonne (llama3.2) |
| **Mistral AI** 🇫🇷 | Tier gratuit généreux | Très bonne |
| **OpenAI** | Payant (~$0.02/lettre) | Excellente |
| **Aucun** | — | Template seul |

---

## 🛡️ Vie privée

- **100% local** — Aucune donnée envoyée à un serveur
- Vos offres, lettres et config restent sur votre machine
- Seuls les appels API (France Travail, SerpApi, LLM) sortent

---

## 🐛 Troubleshooting

| Problème | Solution |
|----------|----------|
| `ModuleNotFoundError` | `source .venv/bin/activate && pip install -r requirements.txt` |
| Scan retourne 0 offres | Configurer France Travail API dans `[7] Changer la config` |
| Ollama ne répond pas | `ollama serve` puis réessayer |
| Lettres vides | Vérifier `_letter_template_path` dans `data/config.yaml` |
| Windows : accent cassés | `chcp 65001` dans cmd avant de lancer |

---

## 📝 Licence

**Propriétaire — Tous droits réservés.**

- ✅ Usage personnel autorisé
- ❌ Redistribution, modification, intégration commerciale interdites
- Voir [LICENSE](LICENSE) pour le texte complet.

---

## 🤝 Contribuer

Pull requests bienvenues. Ouvrez une issue avant les gros changements.

---

*Fait avec ❤️ par [Matthias Dubois](https://www.linkedin.com/in/matthias-dubois/) — [@theturbos](https://github.com/theturbos)*
