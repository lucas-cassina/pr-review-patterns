# PR Review Patterns

Analiza los comentarios de code review de la semana desde GitHub y/o GitLab, los agrupa por patrón y sugiere qué convertir en regla de linter, qué agregar a un agente de desarrollo, y qué dejar como criterio humano.

Para ejecutarlo, usá el skill `review-patterns` definido en `skills/review-patterns/SKILL.md`.

## Configuración

- Repos: `config.py` → `GITHUB_REPOS` y/o `GITLAB_REPOS`
- Tokens: `.env` → `GITHUB_TOKEN` y/o `GITLAB_TOKEN`
- Dependencias: `python3 -m pip install -r requirements.txt`
