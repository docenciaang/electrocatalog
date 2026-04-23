# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows
pip install -r requirements.txt

# Initialize DB with predefined categories
python init_db.py

# Run database migrations (adds missing columns, idempotent)
python migrate_db.py

# Run the app (debug mode, port 5000)
python app.py
```

No test suite or linter is configured.

## Architecture

**Stack:** Flask 3 + Flask-SQLAlchemy + SQLite + Jinja2 templates + Bootstrap 5.3

The app follows a flat MVC layout — no blueprints subpackages:
- `app.py` — app factory (`create_app()`), wires DB and registers the single `main` blueprint
- `models.py` — two SQLAlchemy models: `Category` and `Component`
- `routes.py` — all 13 routes in a single blueprint; contains business logic inline
- `init_db.py` / `migrate_db.py` — one-shot scripts for DB setup and schema evolution
- `templates/` — Jinja2 templates split into `categories/` and `components/` subdirectories; `base.html` has navigation, Bootstrap, Quill.js, and a custom lightbox
- `static/img/` — server-stored component images (uploaded via `/images/upload`)

## Key Domain Concepts

**Category `tipo` field** drives dynamic behavior throughout the app. Valid values: `resistencia`, `condensador`, `inductor`, `ic`, `microcontrolador` (or `None`). This field controls:
- Which technical columns are populated on `Component` (enforced in `_apply_tech_fields()` and `_TIPO_CAMPOS` dict in `routes.py`)
- Which form fields are visible (JavaScript in `components/form.html`)
- How `Component.valor_display` property formats the value (e.g., "10 kΩ", "100 µF")

**Component technical fields** are split by type — only the fields relevant to the component's category type are stored/shown. Microcontroladores have the richest set (flash, ram, rom, wifi, bt, zigbee, lora, etc.).

**Stock control** (`/components/<id>/stock` POST) accepts `action=increment` or `action=decrement` and is callable from both the list and detail views without a page reload pattern — it POSTs and redirects.

**Image handling:** images can be either uploaded (stored in `static/img/`, served directly) or referenced by URL. The upload endpoint (`/images/upload`) returns JSON and is called via fetch from the form's JS.

**Shelf location** uses two fields: `estanteria` (shelf identifier) and `caja` (box). The component list supports searching both fields.

## Database Notes

- SQLite database lives in `instance/components.db` (gitignored)
- `db.create_all()` runs on every `create_app()` call — safe because SQLAlchemy won't recreate existing tables
- `migrate_db.py` uses raw `ALTER TABLE` SQL to add new columns; it must be updated manually when the schema evolves
