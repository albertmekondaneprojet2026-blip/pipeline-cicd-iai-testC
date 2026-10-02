"""
Script de gate IA : lit les rapports Pytest, Bandit, Pylint,
demande a Gemini d'evaluer le risque, et bloque le pipeline si necessaire.

Fonctionnalites :
- Analyse Pytest / Bandit / Pylint
- Evaluation du risque par Gemini
- Desactivation explicite de l'Automatic Function Calling
- Retry avec backoff exponentiel pour les erreurs temporaires
- Fallback de securite si Gemini est indisponible
- Blocage automatique en cas de vulnerabilite HIGH ou de tests en echec
"""

import json
import os
import sys
import time

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv n'est pas necessaire en CI

from google import genai
from google.genai import types


BANDIT_ORDER = {
    'HIGH': 0,
    'MEDIUM': 1,
    'LOW': 2,
}

PYLINT_ORDER = {
    'fatal': 0,
    'error': 1,
    'warning': 2,
    'refactor': 3,
    'convention': 4,
}


# Nombre maximum de tentatives supplementaires
MAX_RETRIES = 3

# Delai initial entre les tentatives
BASE_DELAY = 2


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
    """Resume les resultats Pytest."""
    if data is None:
        return "Resultats Pytest indisponibles."

    summary = data.get('summary', {})

    lines = [
        f"Tests: {summary.get('total', 0)} total, "
        f"{summary.get('passed', 0)} reussis, "
        f"{summary.get('failed', 0)} echoues, "
        f"{summary.get('error', 0)} en erreur."
    ]

    failed = [
        t.get('nodeid')
        for t in data.get('tests', [])
        if t.get('outcome') in ('failed', 'error')
    ]

    for nodeid in failed[:10]:
        lines.append(f"- ECHEC : {nodeid}")

    return "\n".join(lines)


def summarize_bandit(data):
    """Resume les resultats Bandit."""
    if data is None:
        return "Resultats Bandit indisponibles."

    # On ignore les assertions B101 dans les fichiers de tests.
    results = [
        issue
        for issue in data.get('results', [])
        if not (
            issue.get('test_id') == 'B101'
            or 'tests.py' in issue.get('filename', '')
        )
    ]

    if not results:
        return (
            "Bandit : aucune vulnerabilite detectee "
            "(hors assertions des fichiers de tests)."
        )

    results.sort(
        key=lambda i: BANDIT_ORDER.get(
            i.get('issue_severity', 'LOW'),
            3
        )
    )

    counts = {}

    for issue in results:
        severity = issue.get('issue_severity', 'LOW')
        counts[severity] = counts.get(severity, 0) + 1

    lines = [
        f"Bandit a detecte {len(results)} probleme(s) : "
        + ", ".join(
            f"{n} {severity}"
            for severity, n in counts.items()
        )
        + "."
    ]

    for issue in results[:15]:
        lines.append(
            f"- [{issue.get('issue_severity')}/"
            f"{issue.get('issue_confidence')}] "
            f"{issue.get('test_id')} : "
            f"{issue.get('issue_text')} "
            f"(fichier: {issue.get('filename')}, "
            f"ligne: {issue.get('line_number')})"
        )

    return "\n".join(lines)


def summarize_pylint(data):
    """Resume les resultats Pylint."""
    if not data:
        return "Pylint : aucun avertissement significatif."

    data = sorted(
        data,
        key=lambda i: PYLINT_ORDER.get(
            i.get('type', 'convention'),
            5
        )
    )

    counts = {}

    for issue in data:
        issue_type = issue.get('type', 'convention')
        counts[issue_type] = counts.get(issue_type, 0) + 1

    lines = [
        f"Pylint a releve {len(data)} message(s) : "
        + ", ".join(
            f"{n} {issue_type}"
            for issue_type, n in counts.items()
        )
        + "."
    ]

    for issue in data[:10]:
        lines.append(
            f"- [{issue.get('type')}] "
            f"{issue.get('message')} "
            f"(ligne {issue.get('line')})"
        )

    return "\n".join(lines)


def build_prompt(pytest_summary, bandit_summary, pylint_summary):
    """Construit le prompt envoye a Gemini."""

    return f"""
Tu es un expert en revue de code charge d'evaluer le risque
d'un changement avant son deploiement en production.

Voici les resultats d'analyse automatique :

## Tests automatises
{pytest_summary}

## Analyse de securite (Bandit)
{bandit_summary}

## Analyse de qualite (Pylint)
{pylint_summary}

Regles de decision a appliquer strictement :

- Toute vulnerabilite Bandit de severite HIGH
  => risk_level "high" et recommendation "block".

- Toute vulnerabilite Bandit de severite MEDIUM liee a une injection
  (SQL, commande) ou a l'execution de code arbitraire
  => risk_level "high" et recommendation "block".

- Un ou plusieurs tests Pytest en echec ou en erreur
  => au minimum "medium" et recommendation "block".

- Uniquement des messages Pylint de style ou de convention,
  sans autre probleme
  => risk_level "low" et recommendation "continue".

- Aucun probleme detecte
  => risk_level "low" et recommendation "continue".

Reponds STRICTEMENT au format JSON suivant,
sans aucun texte avant ou apres :

{{
  "risk_level": "low" | "medium" | "high",
  "justification": "une explication concise en francais, 2-3 phrases maximum",
  "recommendation": "continue" | "block"
}}
"""


def is_transient_error(error):
    """
    Determine si une erreur Gemini est temporaire.

    Les erreurs 429 et 5xx peuvent etre retentees.
    """

    status_code = getattr(error, 'status_code', None)

    if status_code is None:
        status_code = getattr(error, 'code', None)

    if status_code is not None:
        try:
            status_code = int(status_code)
        except (TypeError, ValueError):
            pass

    if status_code == 429:
        return True

    if isinstance(status_code, int) and 500 <= status_code < 600:
        return True

    error_text = str(error).upper()

    temporary_markers = (
        '503',
        'UNAVAILABLE',
        '429',
        'RESOURCE_EXHAUSTED',
        'INTERNAL',
        'TIMEOUT',
        'DEADLINE',
    )

    return any(marker in error_text for marker in temporary_markers)


def call_gemini_with_retry(client, prompt):
    """
    Appelle Gemini avec plusieurs tentatives en cas d'erreur temporaire.
    """

    config = types.GenerateContentConfig(
        temperature=0,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(
            disable=True
        ),
    )

    for attempt in range(MAX_RETRIES + 1):

        try:
            print(
                f"Appel Gemini : tentative "
                f"{attempt + 1}/{MAX_RETRIES + 1}"
            )

            response = client.models.generate_content(
                model='gemini-3.6-flash',
                contents=prompt,
                config=config,
            )

            return response

        except Exception as error:

            if not is_transient_error(error):
                print(
                    "ERREUR Gemini non temporaire : "
                    f"{error}"
                )
                raise

            if attempt >= MAX_RETRIES:
                print(
                    "Gemini reste indisponible apres "
                    f"{MAX_RETRIES + 1} tentatives."
                )
                raise

            delay = BASE_DELAY * (2 ** attempt)

            print(
                f"Gemini temporairement indisponible. "
                f"Nouvelle tentative dans {delay} seconde(s)..."
            )

            time.sleep(delay)

    return None


def local_security_fallback(pytest_data, bandit_data):
    """
    Analyse locale minimale utilisee lorsque Gemini est indisponible.

    Cette fonction ne remplace pas l'IA :
    elle garantit simplement qu'un probleme critique
    ne puisse pas etre ignore a cause d'une indisponibilite
    du service Gemini.
    """

    # Analyse Pytest
    if pytest_data:
        summary = pytest_data.get('summary', {})

        failed = summary.get('failed', 0)
        errors = summary.get('error', 0)

        if failed > 0 or errors > 0:
            return {
                "risk_level": "medium",
                "justification": (
                    "Gemini est indisponible et des tests automatises "
                    "sont en echec ou en erreur."
                ),
                "recommendation": "block",
            }

    # Analyse Bandit
    if bandit_data:
        results = [
            issue
            for issue in bandit_data.get('results', [])
            if not (
                issue.get('test_id') == 'B101'
                or 'tests.py' in issue.get('filename', '')
            )
        ]

        high_issues = [
            issue
            for issue in results
            if issue.get('issue_severity') == 'HIGH'
        ]

        if high_issues:
            return {
                "risk_level": "high",
                "justification": (
                    f"{len(high_issues)} vulnerabilite(s) "
                    "Bandit de severite HIGH ont ete detectees. "
                    "Gemini etant indisponible, le pipeline est bloque "
                    "par mesure de securite."
                ),
                "recommendation": "block",
            }

    # Aucun signal critique detecte localement
    return {
        "risk_level": "low",
        "justification": (
            "Gemini est temporairement indisponible. "
            "Aucun test en echec ni vulnerabilite Bandit HIGH "
            "n'a ete detecte localement."
        ),
        "recommendation": "continue",
    }


def clean_json_response(raw_text):
    """Nettoie une reponse JSON eventuellement entouree de Markdown."""

    raw_text = raw_text.strip()

    if raw_text.startswith("```"):
        raw_text = raw_text.replace("```json", "", 1)
        raw_text = raw_text.replace("```JSON", "", 1)
        raw_text = raw_text.replace("```", "", 1)
        raw_text = raw_text.strip()

    return raw_text


def main():

    # ---------------------------------------------------------
    # 1. Verification de la cle API
    # ---------------------------------------------------------

    api_key = os.environ.get('GEMINI_API_KEY')

    if not api_key:
        print("ERREUR : GEMINI_API_KEY manquante.")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    # ---------------------------------------------------------
    # 2. Chargement des rapports
    # ---------------------------------------------------------

    pytest_data = load_json_safe('pytest-report.json')
    bandit_data = load_json_safe('bandit-report.json')
    pylint_data = load_json_safe('pylint-report.json')

    pytest_summary = summarize_pytest(pytest_data)
    bandit_summary = summarize_bandit(bandit_data)
    pylint_summary = summarize_pylint(pylint_data)

    # ---------------------------------------------------------
    # 3. Affichage des donnees transmises a l'IA
    # ---------------------------------------------------------

    print("=== Donnees transmises a l'IA ===")
    print(pytest_summary)
    print()
    print(bandit_summary)
    print()
    print(pylint_summary)
    print()

    # ---------------------------------------------------------
    # 4. Construction du prompt
    # ---------------------------------------------------------

    prompt = build_prompt(
        pytest_summary,
        bandit_summary,
        pylint_summary
    )

    # ---------------------------------------------------------
    # 5. Appel Gemini avec retry
    # ---------------------------------------------------------

    try:
        response = call_gemini_with_retry(
            client,
            prompt
        )

        raw_text = response.text.strip()

        if not raw_text:
            raise ValueError(
                "Gemini a retourne une reponse vide."
            )

        raw_text = clean_json_response(raw_text)

        result = json.loads(raw_text)

    except Exception as error:

        print()
        print("=== FALLBACK DE SECURITE ===")
        print(
            "Impossible d'obtenir une evaluation Gemini : "
            f"{error}"
        )

        result = local_security_fallback(
            pytest_data,
            bandit_data
        )

    # ---------------------------------------------------------
    # 6. Normalisation de la decision
    # ---------------------------------------------------------

    risk = result.get('risk_level', 'high')
    justification = result.get(
        'justification',
        'Aucune justification fournie.'
    )
    recommendation = result.get(
        'recommendation',
        'block'
    )

    # Protection contre une reponse IA incoherente
    if risk not in ('low', 'medium', 'high'):
        risk = 'high'
        recommendation = 'block'

    if recommendation not in ('continue', 'block'):
        recommendation = 'block'

    # ---------------------------------------------------------
    # 7. Affichage de la decision
    # ---------------------------------------------------------

    print()
    print("=== Evaluation IA du risque ===")
    print(f"Niveau de risque : {risk}")
    print(f"Justification : {justification}")
    print(f"Recommandation : {recommendation}")

    # ---------------------------------------------------------
    # 8. Sauvegarde du rapport
    # ---------------------------------------------------------

    final_result = {
        "risk_level": risk,
        "justification": justification,
        "recommendation": recommendation,
    }

    with open(
        'ai-risk-report.json',
        'w',
        encoding='utf-8'
    ) as f:
        json.dump(
            final_result,
            f,
            ensure_ascii=False,
            indent=2
        )

    # ---------------------------------------------------------
    # 9. Decision finale du pipeline
    # ---------------------------------------------------------

    if recommendation == 'block':
        print()
        print(
            "PIPELINE BLOQUE : risque juge trop eleve "
            "pour continuer."
        )
        sys.exit(1)

    print()
    print(
        "Risque acceptable, le pipeline continue."
    )

    sys.exit(0)


if __name__ == '__main__':
    main()