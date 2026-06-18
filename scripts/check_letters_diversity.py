#!/usr/bin/env python3
"""
Test de diversité des lettres de motivation.
À exécuter après chaque génération de nouvelle lettre.
Vérifie que les lettres ne sont pas des clones les unes des autres.
"""

import os
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

LETTRES_DIR = Path(__file__).parent.parent / "lettres"

def load_letter(path):
    """Charge une lettre .md et extrait le corps (sans l'en-tête)."""
    with open(path) as f:
        text = f.read()
    # Retirer l'en-tête (tout ce qui suit --- après la première ligne)
    # Le format est: # Titre\n\n**Offre**: ...\n**Date**: ...\n**Score**: ...\n\n---\n\ncorps
    parts = text.split('---', 1)
    if len(parts) > 1:
        body = parts[1].strip()
    else:
        body = text.strip()
    return body

def first_sentence(body):
    """Extrait la première vraie phrase du corps."""
    # Ignorer les lignes vides et les lignes de meta
    lines = [l.strip() for l in body.split('\n') if l.strip() and not l.startswith('**')]
    if not lines:
        return ""
    # Prendre la première ligne qui contient une phrase
    for line in lines:
        # Split sur . ! ? pour avoir la première phrase
        match = re.match(r'^([^.!?]+[.!?])', line)
        if match:
            return match.group(1).strip()
        return line.strip()[:120]
    return ""

def similarity(a, b):
    """Ratio de similarité entre deux textes."""
    return SequenceMatcher(None, a, b).ratio()

def check_forbidden_words(body, letter_name):
    """Vérifie les mots interdits."""
    forbidden = [
        "dans le paysage actuel", "dans un monde en constante évolution",
        "à l'intersection de", "exploiter le potentiel de", "tirer parti de",
        "favoriser l'innovation", "impulser le changement", "accompagner la transformation",
        "c'est pourquoi", "de par mon expérience", "je suis convaincu que",
        "j'ai toujours été passionné par", "robuste", "holistique", "synergique", "disruptif",
        "embrasser"
    ]
    body_lower = body.lower()
    found = []
    for word in forbidden:
        if word in body_lower:
            found.append(word)
    if found:
        print(f"  ⚠️  {letter_name}: mots interdits trouvés: {found}")
        return False
    return True

def check_also_count(body, letter_name):
    """Vérifie que 'également' n'apparaît pas plus d'une fois."""
    count = len(re.findall(r'\bégalement\b', body, re.IGNORECASE))
    if count > 1:
        print(f"  ⚠️  {letter_name}: 'également' utilisé {count} fois (max 1)")
        return False
    return True

def check_long_sentences(body, letter_name):
    """Vérifie qu'aucune phrase ne dépasse 40 mots."""
    sentences = re.split(r'[.!?]+', body)
    too_long = []
    for s in sentences:
        words = s.strip().split()
        if len(words) > 40:
            too_long.append(len(words))
    if too_long:
        print(f"  ⚠️  {letter_name}: {len(too_long)} phrases de plus de 40 mots (longueurs: {too_long})")
        return False
    return True

def main():
    letters = sorted(LETTRES_DIR.glob("*.md"))
    if not letters:
        print("❌ Aucune lettre trouvée dans", LETTRES_DIR)
        return 1

    bodies = {}
    first_sentences = {}

    for p in letters:
        body = load_letter(p)
        bodies[p.name] = body
        first_sentences[p.name] = first_sentence(body)

    print(f"📊 Analyse de {len(letters)} lettres\n")
    all_ok = True

    # 1. Vérifier les premières phrases — doivent être toutes distinctes
    print("🔍 TEST 1: Unicité des phrases d'accroche")
    sentences_seen = {}
    for name, sent in first_sentences.items():
        # Normaliser pour la comparaison
        norm = sent.lower()[:80]
        for seen_name, seen_sent in sentences_seen.items():
            if similarity(norm, seen_sent) > 0.60:
                print(f"  ⚠️  SIMILARITÉ D'ACCROCHE: {name} ↔ {seen_name} ({similarity(norm, seen_sent):.0%})")
                print(f"      \"{sent[:80]}...\"")
                print(f"      \"{seen_sent[:80]}...\"")
                all_ok = False
        sentences_seen[name] = norm
    print(f"  ✅ {len(letters)} accroches vérifiées\n")

    # 2. Vérifier la similarité globale entre paires
    print("🔍 TEST 2: Similarité globale entre lettres (seuil: 50%)")
    names = list(bodies.keys())
    high_sim_pairs = []
    for i in range(len(names)):
        for j in range(i+1, len(names)):
            sim = similarity(bodies[names[i]], bodies[names[j]])
            if sim > 0.50:
                high_sim_pairs.append((names[i], names[j], sim))

    if high_sim_pairs:
        for a, b, sim in sorted(high_sim_pairs, key=lambda x: -x[2]):
            print(f"  ⚠️  {a} ↔ {b}: {sim:.0%} de similarité")
        all_ok = False
    else:
        print(f"  ✅ Aucune paire au-dessus de 50%\n")

    # 3. Vérifier les mots interdits
    print("🔍 TEST 3: Mots interdits")
    forbidden_ok = True
    for name, body in bodies.items():
        if not check_forbidden_words(body, name):
            forbidden_ok = False
    if forbidden_ok:
        print(f"  ✅ Aucun mot interdit trouvé\n")

    # 4. Vérifier le compte de "également"
    print("🔍 TEST 4: Occurrences de 'également'")
    also_ok = True
    for name, body in bodies.items():
        if not check_also_count(body, name):
            also_ok = False
    if also_ok:
        print(f"  ✅ OK\n")

    # 5. Vérifier les phrases longues
    print("🔍 TEST 5: Phrases > 40 mots")
    long_ok = True
    for name, body in bodies.items():
        if not check_long_sentences(body, name):
            long_ok = False
    if long_ok:
        print(f"  ✅ OK\n")

    # 6. Vérifier la contamination d'entreprises (word-boundary)
    print("🔍 TEST 6: Contamination d'entreprises (chaque lettre mentionne-t-elle UNE AUTRE cible ?)")
    all_companies = [
        "iQo", "Artefact", "Mirakl", "Doctolib", "Galadrim",
        "Theodo", "VO2", "H Company", "Skello", "DN8",
        "Dust", "Mistral", "Time2Scale", "SPIE", "NetBooster",
        "Extia", "DINUM", "PIXMANIA"
    ]
    # Extraire l'entreprise cible de chaque lettre
    target_map = {}
    # Allowed co-mentions (e.g. Artefact mentioning NetBooster is intentional)
    allowed_co_mentions = {
        "artefact_head-of-transformation.md": ["NetBooster"],
    }
    for name, body in bodies.items():
        # Chercher le nom d'entreprise dans le header
        for comp in all_companies:
            pattern = r'\*\*Offre\*\*\s*:.*' + re.escape(comp)
            full_text = open(LETTRES_DIR / name).read()
            if re.search(pattern, full_text):
                target_map[name] = comp
                break
        if name not in target_map:
            # fallback: chercher dans le nom de fichier
            for comp in all_companies:
                if comp.lower().replace(' ', '-') in name.lower():
                    target_map[name] = comp
                    break
    
    contamination_ok = True
    for name, body in bodies.items():
        expected = target_map.get(name, "")
        allowed = allowed_co_mentions.get(name, [])
        for comp in all_companies:
            if comp == expected or comp in allowed:
                continue
            if re.search(r'\b' + re.escape(comp) + r'\b', body):
                print(f"  ⚠️  {name}: mentionne '{comp}' alors que la cible est '{expected}'")
                contamination_ok = False
    if contamination_ok:
        print(f"  ✅ Aucune contamination\n")

    # Résultat
    if all_ok and forbidden_ok and also_ok and long_ok and contamination_ok:
        print("✅ TOUS LES TESTS PASSÉS — Lettres diversifiées et propres.")
        return 0
    else:
        print("❌ ÉCHEC — Corriger les problèmes ci-dessus avant de livrer.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
