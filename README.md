# PR Review Patterns

Agente que procesa todos los comentarios de code review de la semana desde GitHub y/o GitLab, los agrupa por patrón y clasifica cada uno en:

- **linter** → propone la regla de ESLint/Stylelint a crear
- **agent-rule** → genera el texto exacto listo para pegar en el archivo de reglas del agente (`CLAUDE.md`, `AGENTS.md`, `.cursor/rules/`)
- **template** → sugiere agregarlo al PR template o checklist
- **human** → lo registra pero no es automatizable

El output es un reporte `output/YYYY-WW.md` con los patrones ordenados por frecuencia, ejemplos reales de comentarios, y las acciones concretas recomendadas.

## Qué analiza

Todos los comentarios (inline y top-level) de los **PRs/MRs mergeados** en el período configurado. La ventana se aplica sobre `merged_at` — no sobre cuándo se escribió el comentario. Un PR abierto durante un mes y mergeado esta semana tiene feedback igual de relevante.

Incluye auto-comentarios del autor del propio PR: en equipos chicos o con self-review, son señal válida de criterio de calidad.

## Requisitos

- Python 3.10+
- Token de GitHub con permisos `repo` (classic personal access token)
- Token de GitLab con scope `read_api` (classic personal access token — no fine-grained)

## Setup

```bash
# 1. Instalar dependencias
python3 -m pip install -r requirements.txt

# 2. Configurar credenciales
cp .env.example .env
# Editar .env con los tokens correspondientes

# 3. Configurar repositorios en config.py
```

### config.py

```python
# Repos de GitHub — formato "org/repo"
GITHUB_REPOS = [
    "mi-org/mi-repo",
]

# Proyectos de GitLab — ID numérico o "grupo/proyecto"
GITLAB_REPOS = [
    {"id": "123", "name": "mi-repo"},
    {"id": "mi-grupo/mi-proyecto", "name": "mi-proyecto"},
]

# Para GitLab self-hosted, cambiar la URL base
GITLAB_BASE_URL = "https://gitlab.com"

# Cuántos días atrás analizar (se aplica sobre merged_at)
DAYS_LOOKBACK = 7
```

Se puede usar solo GitHub, solo GitLab, o ambos a la vez.

## Uso

El agente se puede correr desde tres herramientas:

| Herramienta | Comando |
|-------------|---------|
| **Claude Code** | `/review-patterns` |
| **Codex CLI** | `usá el skill review-patterns` |
| **Cursor** | `@review-patterns` en el Composer |

En los tres casos el agente:
1. Corre `python3 fetch.py` para traer los comentarios del período configurado
2. Analiza `output/comments.json` y agrupa por patrón semánticamente
3. Escribe el reporte en `output/YYYY-WW.md`
4. Propone las reglas `agent-rule` y ofrece agregarlas al archivo de reglas de tu herramienta

### Correr el fetch manualmente

```bash
python3 fetch.py
```

Escribe dos archivos:
- `output/comments.json` — versión compacta para el agente (~35% menos tokens)
- `output/raw_comments.json` — datos completos para debug

## Estructura

```
pr-review-patterns/
├── AGENTS.md                                  # Codex: descripción del agente
├── skills/review-patterns/SKILL.md            # Codex: instrucciones del skill
├── .claude/commands/review-patterns.md        # Claude Code: /review-patterns
├── .cursor/commands/review-patterns.md        # Cursor: @review-patterns
├── fetch.py                                   # Entry point unificado
├── fetch_github.py                            # Fetcher de GitHub
├── fetch_gitlab.py                            # Fetcher de GitLab
├── config.py                                  # Repos y configuración
├── .env.example                               # Template de credenciales
├── requirements.txt
└── output/
    ├── comments.json                          # Input del agente (no commitear)
    ├── raw_comments.json                      # Datos completos (no commitear)
    └── YYYY-WW.md                             # Reporte semanal
```

## Qué filtra automáticamente

- Comentarios de bots (`[bot]` en el nombre, sufijo `-bot`, flag `bot` de la API de GitLab)
- Mensajes de sistema de GitLab (merge, approve, pipeline events)

## Qué PRs/MRs analiza

Solo los **mergeados** en el período de `DAYS_LOOKBACK` días. La ventana se mide por `merged_at`, no por `updated_at` ni por la fecha de los comentarios.

## Nota sobre tokens de GitLab

Usar **classic personal access token** con scope `read_api`. Los fine-grained tokens requieren permisos adicionales por proyecto (`Work Item: Read`) que no siempre están disponibles según el plan.

URL para crear un classic token: `https://gitlab.com/-/user_settings/personal_access_tokens`
