"""
Script de gate IA : lit les rapports Pytest, Bandit, Pylint,
demande a Gemini d'evaluer le risque, et bloque le pipeline si necessaire.
"""
import os
import sys
import json

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv n'est pas necessaire en CI (variables deja injectees)

from google import genai
from google.genai import types

BANDIT_ORDER = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
PYLINT_ORDER = {'fatal': 0, 'error': 1, 'warning': 2, 'refactor': 3, 'convention': 4}


def load_json_safe(path):
    """Charge un fichier JSON, retourne None s'il est absent ou illisible."""
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def summarize_pytest(data):
    if data is None:
        return "Resultats Pytest indisponibles."
    summary = data.get('summary', {})
    lines = [
        f"Tests: {summary.get('total', 0)} total, "
        f"{summary.get('passed', 0)} reussis, "
        f"{summary.get('failed', 0)} echoues, "
        f"{summary.get('error', 0)} en erreur."
    ]
    failed = [t.get('nodeid') for t in data.get('tests', []) if t.get('outcome') in ('failed', 'error')]
    for nodeid in failed[:10]:
        lines.append(f"- ECHEC : {nodeid}")
    return "\n".join(lines)


def summarize_bandit(data):
    if data is None:
        return "Resultats Bandit indisponibles."

    # On ignore le bruit habituel : les assert des fichiers de tests (B101)
    results = [
        issue for issue in data.get('results', [])
        if not (issue.get('test_id') == 'B101' or 'tests.py' in issue.get('filename', ''))
    ]
    if not results:
        return "Bandit : aucune vulnerabilite detectee (hors assertions des fichiers de tests)."

    results.sort(key=lambda i: BANDIT_ORDER.get(i.get('issue_severity', 'LOW'), 3))

    counts = {}
    for issue in results:
        sev = issue.get('issue_severity', 'LOW')
        counts[sev] = counts.get(sev, 0) + 1

    lines = [
        f"Bandit a detecte {len(results)} probleme(s) : "
        + ", ".join(f"{n} {sev}" for sev, n in counts.items()) + "."
    ]
    for issue in results[:15]:
        lines.append(
            f"- [{issue.get('issue_severity')}/{issue.get('issue_confidence')}] "
            f"{issue.get('test_id')} : {issue.get('issue_text')} "
            f"(fichier: {issue.get('filename')}, ligne: {issue.get('line_number')})"
        )
    return "\n".join(lines)


def summarize_pylint(data):
    if not data:
        return "Pylint : aucun avertissement significatif."
    data = sorted(data, key=lambda i: PYLINT_ORDER.get(i.get('type', 'convention'), 5))
    counts = {}
    for issue in data:
        t = issue.get('type', 'convention')
        counts[t] = counts.get(t, 0) + 1
    lines = [
        f"Pylint a releve {len(data)} message(s) : "
        + ", ".join(f"{n} {t}" for t, n in counts.items()) + "."
    ]
    for issue in data[:10]:
        lines.append(f"- [{issue.get('type')}] {issue.get('message')} (ligne {issue.get('line')})")
    return "\n".join(lines)


def build_prompt(pytest_summary, bandit_summary, pylint_summary):
    return f"""Tu es un expert en revue de code charge d'evaluer le risque
d'un changement avant son deploiement en production.

Voici les resultats d'analyse automatique :

## Tests automatises
{pytest_summary}

## Analyse de securite (Bandit)
{bandit_summary}

## Analyse de qualite (Pylint)
{pylint_summary}

Regles de decision, a appliquer strictement :
- Toute vulnerabilite Bandit de severite HIGH => risk_level "high" et recommendation "block".
- Toute vulnerabilite Bandit de severite MEDIUM liee a une injection (SQL, commande)
  ou a l'execution de code arbitraire => risk_level "high" et recommendation "block".
- Un ou plusieurs tests Pytest en echec ou en erreur => au minimum "medium" et recommendation "block".
- Uniquement des messages Pylint de style ou de convention, sans autre probleme => "low" et "continue".
- Aucun probleme detecte => "low" et "continue".

Reponds STRICTEMENT au format JSON suivant, sans aucun texte avant ou apres :

{{
  "risk_level": "low" | "medium" | "high",
  "justification": "une explication concise en francais, 2-3 phrases maximum",
  "recommendation": "continue" | "block"
}}
"""


def main():
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("ERREUR: GEMINI_API_KEY manquante.")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    pytest_summary = summarize_pytest(load_json_safe('pytest-report.json'))
    bandit_summary = summarize_bandit(load_json_safe('bandit-report.json'))
    pylint_summary = summarize_pylint(load_json_safe('pylint-report.json'))

    print("=== Donnees transmises a l'IA ===")
    print(pytest_summary)
    print(bandit_summary)
    print(pylint_summary)
    print()

    prompt = build_prompt(pytest_summary, bandit_summary, pylint_summary)

    response = client.models.generate_content(
        model='gemini-3.6-flash',
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0),
    )
    raw_text = response.text.strip()

    if raw_text.startswith('```'):
        raw_text = raw_text.strip('`').replace('json', '', 1).strip()

    try:
        result = json.loads(raw_text)
    except json.JSONDecodeError:
        print(f"ERREUR: reponse Gemini non parsable :\n{raw_text}")
        sys.exit(1)

    risk = result.get('risk_level', 'high')
    justification = result.get('justification', 'Aucune justification fournie.')
    recommendation = result.get('recommendation', 'block')

    print("=== Evaluation IA du risque ===")
    print(f"Niveau de risque : {risk}")
    print(f"Justification : {justification}")
    print(f"Recommandation : {recommendation}")

    with open('ai-risk-report.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    if recommendation == 'block':
        print("PIPELINE BLOQUE : risque juge trop eleve pour continuer.")
        sys.exit(1)

    print("Risque acceptable, le pipeline continue.")
    sys.exit(0)


if __name__ == '__main__':
    main()