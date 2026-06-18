# MEMORY.md — Historique & Contexte du Projet

_Dernière mise à jour : 17/06/2026 — 13:05 PDT_
_Tenue par : Tom 🔍_

---

## 📌 Résumé du projet

**Mission** : Veille emploi automatisée pour Matthias Dubois — postes IA Strategy / Finance+IA à Paris, disponibilité septembre 2026.

**Date de création** : 15 mai 2026 (première activation de Tom)

---

## 🗓️ Chronologie des sessions

### 15 MAI 2026 — Session inaugurale

- **Première activation** de Tom
- **Base constituée de zéro** : scraping multi-sources (web_search, LinkedIn, WTTJ, Indeed, pages careers scale-ups)
- **20 offres initiales** collectées (15 Cat A + 5 Cat B)
- **8 lettres** générées pour les offres score ≥ 8
- Matthias a partagé sa **lettre de motivation type** (SPIE Industrie) comme modèle de format
- Le script de génération DOCX a été construit avec ce template

#### Bug SPIE — PROBLÈME RÉSOLU LE 15/05
- Les DOCX générés à partir du template SPIE ont eu plusieurs bugs :
  1. **Trace de SPIE** : le paragraphe de closing (P9) et certains paragraphes n'étaient pas remplacés → restait "SPIE Industrie" dans des lettres destinées à d'autres entreprises
  2. **Double espacement** : paragraphes vides non nettoyés → trous visuels
- **Corrigé en session** : script de remplacement amélioré, cleanup des paragraphes vides
- Les DOCX actuels (workspace et canvas) sont **propres** — zéro référence à SPIE

#### Dashboard LinkedIn
- Matthias a demandé un dashboard HTML pour screenshot LinkedIn
- Développement en cours, interrompu par un restart OpenClaw
- **À reprendre si Matthias le demande**

### 16 MAI 2026 — Scan quotidien

- Script `daily_scanner.py` exécuté
- **35 offres brutes** récupérées → 4 ajoutées par le script mais en **doublon** (DN8, EY, PIXMANIA, DINUM)
- **Bug identifié** : le script ne vérifie pas les doublons avant d'écrire dans offres.md
- **Nettoyage manuel** : retrait des 4 doublons
- **Résultat net : 0 nouvelle offre pertinente**
- Base stable à 11 offres actives

### 17 MAI 2026 — Scan quotidien

- Même pattern : 35 offres brutes, doublons systématiques
- **Bug du script confirmé** : réinsère DN8, EY, PIXMANIA, DINUM à chaque run
- Nettoyage répété
- **0 nouvelle offre** — marché stable sur notre niche
- Lettres pour DN8 (7/10), DINUM (7/10) et Skello (7/10) restent en attente

### 18 MAI 2026 — Scan + Nettoyage

- Scan SerpApi : 31 offres, aucune nouvelle avec date confirmée
- Nettoyage des doublons récurrents
- **Base stable** : pas de nouvelles offres pertinentes sur la période 13-18 mai

### 22 MAI 2026 — Scan SerpApi

- Recherche élargie (10 SerpApi + 2 requêtes web)
- Plusieurs offres intéressantes repérées mais SANS DATE (SerpApi limitation)
  - Powell Software — Senior PM AI Digital Workplace
  - Wivoo/Wavestone — Lead AI Product Manager Agentic & ML
  - Orus — Product Manager AI Features
- Aucune retenue (date non confirmable)

### 27 MAI 2026 — Scan SerpApi + Nettoyage

- Scan complet, tous les résultats sans date → non retenus
- Détection de doublons récurrents (Galadrim, Okuden, Mendo, Dynergie, IDEAL)
- 14 offres SerpApi sans date rejetées

### 29 MAI 2026 — Scan manuel (APIs down)

- ⚠️ France Travail API : INDISPONIBLE (FT_CLIENT_ID/FT_CLIENT_SECRET non configurées)
- ⚠️ SerpApi : INDISPONIBLE (SERPAPI_KEY non configurée)
- **Fallback web_search** : scan manuel multi-requêtes
- **4 nouvelles offres retenues** (dates ≤ 10 jours) :
  - Mistral AI — Senior AI Deployment Strategist (7/10)
  - Mistral AI — FP&A Manager (7/10)
  - Dust — Finance Manager FP&A & Controlling (8/10) ⭐
  - Time2Scale — FP&A Manager Strategic Finance & Automation (7/10)
- **Base atteint 15 offres**
- **Problème critique non résolu** : clés API non configurées

### 17 JUIN 2026 — Session

- Matthias signale un problème de template sur les lettres
- Vérification complète : tous les DOCX (workspace + canvas) sont **propres** côté SPIE
- Le bug SPIE a été corrigé le 15 mai — si Matthias voit SPIE, c'est probablement un cache navigateur ou d'anciens fichiers

### 18 JUIN 2026 — Refonte complète des lettres

- Matthias signale que toutes les lettres ont le même contenu et ne sont pas dynamiques
- **Problème confirmé** : les 8 lettres principales partagent une ossature identique (intro copiée-collée, même enchaînement Seb Professional → SKU → LLM, conclusion générique)
- **Refonte complète** : les 10 lettres réécrites de zéro, chacune avec une accroche unique, un angle adapté à l'offre spécifique, et un ton différencié
- Suppression des vieux DOCX (contenu générique)
- Lettres conservées au format .md uniquement (plus authentiques, moins robotiques)

---

## 📊 État actuel de la base

| Métrique | Valeur |
|----------|--------|
| Total offres | 15 |
| Cat A (IA Stratégie) | 10 |
| Cat B (Finance+IA) | 5 |
| Score ≥ 8 | 9 |
| Candidatures envoyées | 0 |
| Lettres générées (.md) | 10 |
| Lettres générées (.docx) | 0 (supprimés — lettres .md refaites le 18/06) |
| Doublons détectés | 50+ entrées |

---

## 🏆 Top offres (score ≥ 8)

| Score | ID | Entreprise | Poste | Statut |
|-------|-----|-----------|-------|--------|
| 9 | iqo_manager-senior-manager-ia | iQo | Manager/Senior Manager IA | Non postulé |
| 9 | artefact_head-of-transformation | Artefact | Head of Transformation | Non postulé |
| 9 | h-company_spm-enterprise-ai-platform | H Company | Senior PM Enterprise AI Platform | Non postulé |
| 9 | mirakl_senior-ai-product-manager | Mirakl | Senior AI Product Manager | Non postulé |
| 8 | doctolib_ai-senior-product-manager | Doctolib | AI Senior Product Manager | Non postulé |
| 8 | galadrim_head-of-ai-education | Galadrim | Head of AI Education | Non postulé |
| 8 | theodo-data-ai_consultant-senior-ai-advisory | Theodo Data & AI | Consultant Senior AI Advisory | Non postulé |
| 8 | vo2-finance_consultant-acculturation-change-ai | VO2 Finance | Consultant Acculturation & Change AI | Non postulé |
| 8 | dust_finance-manager-fp&a-controlling | Dust | Finance Manager FP&A & Controlling | Non postulé |
| 8 | extia_head-of-ai-practice-leader-ia | Extia | Head of AI / Practice Leader IA | Non postulé |

---

## ⚠️ Problèmes connus

### Critique
1. **Clés API non configurées** : SERPAPI_KEY, FT_CLIENT_ID, FT_CLIENT_SECRET
   - Sans elles, le scan automatique est inopérant
   - Fallback web_search = fastidieux, moins fiable
   - Matthias doit les configurer pour que Tom soit pleinement autonome

### Technique
2. **Script daily_scanner.py** : réinsère des doublons à chaque run
   - Bug de déduplication : ne vérifie pas l'existant avant d'écrire
   - Les 4 mêmes offres (DN8, EY, PIXMANIA, DINUM) reviennent en boucle
   - Contournement actuel : nettoyage manuel post-scan

3. **SerpApi sans date** : ~80% des résultats SerpApi n'ont pas de date
   - Impossible de vérifier le critère ≤ 10 jours
   - Perte d'opportunités potentielles

4. **Memory search down** : pas de clé embedding OpenAI configurée
   - La recherche sémantique dans les conversations est indisponible
   - Contournement : fichiers plats (MEMORY.md, dream logs)

---

## 🔧 Leçons apprises

1. **Template SPIE** : ne JAMAIS réutiliser un template contenant des données d'une entreprise spécifique sans un remplacement à 100% de TOUS les paragraphes
2. **DOCX génération** : toujours vérifier le XML final (zipfile + grep) avant de livrer
3. **Déduplication** : le script doit lire offres.md ET doublons.md AVANT d'écrire
4. **SerpApi** : les résultats sans date sont inutilisables sans vérification manuelle — à considérer comme source secondaire
5. **Fallback** : le web_search manuel fonctionne mais ne scale pas — priorité aux API

---

## 📁 Fichiers clés

| Fichier | Rôle |
|---------|------|
| `SOUL.md` | Identité, règles, format |
| `USER.md` | Profil Matthias |
| `AGENTS.md` | Procédures de démarrage session |
| `TOOLS.md` | API, sources, stratégie scraping |
| `HEARTBEAT.md` | Tâches de fond automatiques |
| `MEMORY.md` | Ce fichier — historique complet |
| `data/offres.md` | Base d'offres |
| `data/candidatures.md` | Registre candidatures |
| `data/doublons.md` | Registre anti-doublons |
| `data/derniere_session.md` | Timestamp dernier scan |
| `lettres/` | Lettres de motivation (.md, .html, .docx) |
| `scripts/daily_scanner.py` | Script de scan automatique (buggé) |
