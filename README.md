# TaskFlow — Pipeline CI/CD Intelligent et AIOps

Application de gestion de projet (inspirée de Linear/Asana/Jira) servant de support de démonstration pour un pipeline CI/CD intelligent réutilisable, intégrant l'analyse par IA (Gemini) à deux niveaux : évaluation du risque avant déploiement, et détection d'anomalies en production.

## Contexte

Projet de fin d'études DTS Génie Logiciel — IAI Cameroun (Douala).

## Stack technique

- **Backend** : Python 3.14 / Django 6
- **Base de données** : PostgreSQL (Supabase, session pooler)
- **Frontend** : Templates Django, CSS custom, Lucide Icons
- **Conteneurisation** : Docker (à venir)
- **CI/CD** : GitHub Actions (à venir)
- **IA** : Gemini API (gate de risque + monitoring)
- **Déploiement** : Render (à venir)
- **Monitoring** : Prometheus + Grafana (à venir)

## Installation locale

```bash
git clone https://github.com/albertmekondaneprojet2026-blip/pipeline-cicd-iai-testC.git
cd pipeline-cicd-iai-testC
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
# Renseigner .env avec vos identifiants Supabase
python manage.py migrate
python manage.py runserver
```

## Statut du projet

🚧 En cours de développement — voir le planning détaillé dans le rapport de soutenance.

---

*Ce README sera complété avec l'architecture complète du pipeline, les schémas, et les instructions de déploiement à l'approche de la soutenance.*

# TaskFlow — Pipeline CI/CD Intelligent et AIOps

![CI Status](https://github.com/albertmekondaneprojet2026-blip/pipeline-cicd-iai-testC/actions/workflows/ci.yml/badge.svg)

Application de gestion de projet...