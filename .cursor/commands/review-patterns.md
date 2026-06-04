# PR Review Patterns — Análisis semanal

Analiza los comentarios de code review de la semana desde GitHub y/o GitLab, los agrupa por patrón y clasifica cada uno en linter / agent-rule / template / human.

## Paso 1 — Obtener los datos

Abrí una terminal en la raíz del proyecto y corré:

```
python3 fetch.py
```

Esto escribe `output/comments.json` con todos los comentarios de los últimos 7 días de los repos configurados en `config.py`.
Si falla, reportá el error y detené la ejecución.

## Paso 2 — Agrupar por patrón

Leé `output/comments.json` y analizá cada comentario. Para cada uno, inferí:

- **Categoría**: qué tipo de problema plantea (naming, error handling, performance, types, formatting, security, test coverage, architecture, writing style, UX copy, conventions)
- **Área del codebase**: qué directorio o módulo es (derivalo del campo `path`)
- **Tier de automatización** — clasificá en exactamente uno:
  - `linter` — se puede detectar estáticamente (ESLint, Stylelint, regla AST custom)
  - `agent-rule` — no puede ser linter, pero puede ser una instrucción en `.cursor/rules/` o un archivo de reglas del agente (convenciones de estilo, naming, copy de UI, elecciones de lenguaje/registro, preferencias de arquitectura)
  - `template` — pertenece a un PR template, issue template o checklist
  - `human` — requiere juicio; no es automatizable

Agrupá comentarios semánticamente similares. Dos comentarios sobre el mismo problema con distinta redacción cuentan como uno solo.

Cuando haya comentarios de múltiples plataformas (campo `platform`: github / gitlab), marcalo en el reporte — los patrones cross-platform son señales especialmente fuertes.

## Paso 3 — Generar el reporte

Escribí `output/YYYY-WW.md` (semana ISO de la fecha actual). Estructura:

```markdown
# PR Review Patterns — Semana YYYY-WW

**Período:** YYYY-MM-DD a YYYY-MM-DD  
**PRs/MRs analizados:** N  
**Comentarios totales:** N  
**Patrones únicos encontrados:** N

---

## Patrones principales

### 1. [Nombre del patrón] — N comentarios (X%)

**Categoría:** [categoría]  
**Áreas del codebase:** [lista de directorios/módulos]  
**Plataformas:** [github / gitlab / ambas]  
**Tier de automatización:** [linter / agent-rule / template / human]  
**Comentario de ejemplo:**
> "[cita textual de un comentario real]"

**Acción sugerida:** [una oración concreta]

---

[repetir para cada patrón con ≥2 ocurrencias, ordenado por frecuencia]

---

## Comentarios de una sola ocurrencia

[Lista breve en bullets — sin análisis profundo]

---

## Resumen de señales

| Patrón | Cant. | % | Plataforma | Tier |
|--------|-------|---|------------|------|
| ...    | ...   |...| ...        | ...  |

---

## Reglas propuestas para el agente (.cursor/rules/)

Para cada patrón con tier `agent-rule`, escribí el texto exacto listo para agregar a un archivo de reglas de Cursor.
Sé específico y accionable — escribí la regla como debe quedar, no una descripción de ella.

### [Nombre del patrón]

```
[Texto exacto de la regla para .cursor/rules/, escrito como instrucción directa.]
```

[repetir para cada patrón agent-rule]

---

## Próximas acciones recomendadas

1. [Regla de linter de mayor impacto a agregar]
2. [Regla de agente de mayor impacto a agregar]
3. [Cualquier cambio de template o proceso]
```

## Paso 4 — Ofrecer aplicar las reglas del agente

Después de escribir el reporte, preguntá:

> "Encontré N patrones que podrían convertirse en reglas de agente. ¿Querés que las agregue a algún archivo en `.cursor/rules/`? Si es así, decime cuáles y el nombre del archivo destino."

Si el usuario confirma, creá o actualizá el archivo `.cursor/rules/<nombre>.mdc` con las reglas aprobadas bajo una sección `## Patrones de code review`. No dupliques reglas que ya estén (verificá por similitud semántica, no por string exacto).

## Paso 5 — Imprimir resumen

Mostrá en el chat:

- Total de comentarios y PRs/MRs analizados
- Top 3 patrones con sus porcentajes y tier de automatización
- Cuántos son candidatos a linter vs. reglas de agente
- Path al reporte completo

Mantené el output del chat en menos de 20 líneas.
