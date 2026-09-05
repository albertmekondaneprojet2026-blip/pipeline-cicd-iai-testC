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
    pass  # python-dotenv n'est pas necessaire en environnement CI (variables deja injectees)

from google import genai


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
    return (
        f"Tests: {summary.get('total', 0)} total, "
        f"{summary.get('passed', 0)} reussis, "
        f"{summary.get('failed', 0)} echoues."
    )


def summarize_bandit(data):
    if data is None:
        return "Resultats Bandit indisponibles."
    results = data.get('results', [])
    if not results:
        return "Bandit : aucune vulnerabilite detectee."
    lines = ["Bandit a detecte les problemes suivants :"]
    for issue in results[:10]:
        lines.append(
            f"- [{issue.get('issue_severity')}] {issue.get('issue_text')} "
            f"(fichier: {issue.get('filename')}, ligne: {issue.get('line_number')})"
        )
    return "\n".join(lines)


def summarize_pylint(data):
    if data is None or not data:
        return "Pylint : aucun avertissement significatif."
    lines = [f"Pylint a releve {len(data)} avertissement(s) :"]
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

Evalue le niveau de risque global de ce changement pour un deploiement en production.
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

    pytest_data = load_json_safe('pytest-report.json')
    bandit_data = load_json_safe('bandit-report.json')
    pylint_data = load_json_safe('pylint-report.json')

    prompt = build_prompt(
        summarize_pytest(pytest_data),
        summarize_bandit(bandit_data),
        summarize_pylint(pylint_data),
    )

    response = client.models.generate_content(
        model='gemini-3.6-flash',
        contents=prompt,
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