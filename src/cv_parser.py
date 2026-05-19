"""
cv_parser.py — Extraction passive des données CV (.docx uniquement)
Lit le CV, extrait nom, contact, skills, metrics, experience, education.
Le CV n'est JAMAIS modifié.
"""

import re
from pathlib import Path

try:
    from docx import Document
except ImportError:
    Document = None


# Patterns d'extraction
EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
PHONE_RE = re.compile(r'(?:\+?\d{1,3}[\s.-]?)?(?:\(?0?\)?[\s.-]?)?\d{2,4}[\s.-]?\d{2,4}[\s.-]?\d{2,4}')
LINKEDIN_RE = re.compile(r'linkedin\.com/in/([a-zA-Z0-9-]+)')
METRICS_RE = re.compile(r'(\d[\d,.]*)\s*(M€|M\\$|K€|K\\$|B€|%|ans|SKUs?|personnes?|employés?)', re.IGNORECASE)

SKILL_KW = [
    "python", "sql", "vba", "power bi", "tableau", "excel", "llm",
    "rag", "langchain", "llamaindex", "openai", "mistral", "hugging face",
    "machine learning", "deep learning", "nlp", "prompt engineering",
    "pnl", "opex", "bfr", "capex", "ocf", "forecast", "budget",
    "fp&a", "contrôle de gestion", "analyse financière", "kpi",
    "docker", "git", "api", "rest", "automation", "automatisation",
]


def parse(cv_path):
    """Parse un CV .docx et retourne un dict structuré."""
    cv_path = Path(cv_path)
    if not cv_path.exists():
        return {"error": f"CV introuvable : {cv_path}"}

    if Document is None:
        return {"error": "python-docx non installé. pip install python-docx"}

    if cv_path.suffix.lower() != ".docx":
        return {"error": "Seuls les CV .docx sont supportés."}

    try:
        doc = Document(str(cv_path))
    except Exception as e:
        return {"error": f"Erreur lecture CV : {e}"}

    # Concatène tout le texte
    text = "\n".join(p.text for p in doc.paragraphs)

    result = {
        "name": _extract_name(text),
        "email": _find_first(EMAIL_RE, text),
        "phone": _find_first(PHONE_RE, text),
        "linkedin": _find_linkedin(text),
        "skills": _extract_skills(text),
        "metrics": METRICS_RE.findall(text)[:10],
        "experience": _extract_sections(text, "experience"),
        "education": _extract_sections(text, "education"),
    }

    return result


def _extract_name(text):
    """Première ligne non-vide = probablement le nom."""
    for line in text.split("\n"):
        line = line.strip()
        if line and len(line) > 2 and not EMAIL_RE.search(line):
            return line
    return ""


def _find_first(pattern, text):
    m = pattern.search(text)
    return m.group(0) if m else ""


def _find_linkedin(text):
    m = LINKEDIN_RE.search(text)
    return f"linkedin.com/in/{m.group(1)}" if m else ""


def _extract_skills(text):
    """Trouve les skills connus mentionnés dans le CV."""
    lower = text.lower()
    found = []
    for kw in SKILL_KW:
        if kw.lower() in lower:
            found.append(kw)
    return found


def _extract_sections(text, section_type):
    """Extrait grossièrement les sections experience/education."""
    patterns = {
        "experience": [
            r"(?:expérience|experience|exp|historique|parcours)\s*(?:professionnelle|pro)?",
            r"(?:poste|position|role)[s]?\s*:",
        ],
        "education": [
            r"(?:formation|education|études|diplôme|diploma|master|bachelor|mba)",
        ],
    }

    results = []
    lower = text.lower()
    for pat in patterns.get(section_type, []):
        for m in re.finditer(pat, lower):
            start = m.start()
            end = min(start + 500, len(text))
            chunk = text[start:end].strip()
            if len(chunk) > 20:
                results.append(chunk[:300])
            break
    return results
