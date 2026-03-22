"""
Migraciones acumulativas para la BD de componentes.
Ejecutar: python migrate_db.py
Es idempotente — omite columnas que ya existen.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'components.db')

# ── Migración 1: campos técnicos en components ────────────────────────────────
COMPONENTS_COLUMNS = [
    ('encapsulado',    'TEXT'),
    ('tolerancia',     'REAL'),
    ('potencia_w',     'REAL'),
    ('voltaje_max_v',  'REAL'),
    ('temp_op_min',    'REAL'),
    ('temp_op_max',    'REAL'),
    ('valor_ohm',      'REAL'),
    ('capacitancia_uf','REAL'),
    ('inductancia_uh', 'REAL'),
    ('familia_ic',     'TEXT'),
    ('pinout_url',     'TEXT'),
    ('image_url',      'TEXT'),
    ('wifi',           'INTEGER'),
    ('bt',             'INTEGER'),
    ('zigbee',         'INTEGER'),
    ('lora',           'INTEGER'),
    ('frecuencia_mhz', 'REAL'),
    ('estanteria',     'TEXT'),
    ('caja',       'TEXT'),
    ('flash_kb',       'REAL'),
    ('ram_kb',         'REAL'),
    ('rom_kb',         'REAL'),
    ('voltaje_op_v',   'REAL'),
]

# ── Migración 2: campo tipo en categories + poblar valores ────────────────────
TIPO_MAP = {
    'Resistencias':         'resistencia',
    'Condensadores':        'condensador',
    'Inductores':           'inductor',
    'Circuitos Integrados': 'ic',
    'Microcontroladores':   'microcontrolador',
}


def col_names(cursor, table):
    cursor.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cursor.fetchall()}


if __name__ == '__main__':
    if not os.path.exists(DB_PATH):
        print(f'No se encontró la BD en {DB_PATH}')
        print('Ejecuta primero: python app.py')
        raise SystemExit(1)

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    # Migración 1
    existing = col_names(cur, 'components')
    added = 0
    for col_name, col_type in COMPONENTS_COLUMNS:
        if col_name not in existing:
            cur.execute(f'ALTER TABLE components ADD COLUMN {col_name} {col_type}')
            print(f'  components + {col_name} ({col_type})')
            added += 1
        else:
            print(f'  components · {col_name} ya existe')

    # Migración 2
    existing_cat = col_names(cur, 'categories')
    if 'tipo' not in existing_cat:
        cur.execute('ALTER TABLE categories ADD COLUMN tipo TEXT')
        print('  categories + tipo (TEXT)')
        added += 1
    else:
        print('  categories · tipo ya existe')

    for name, tipo in TIPO_MAP.items():
        cur.execute('UPDATE categories SET tipo=? WHERE name=?', (tipo, name))
        if cur.rowcount:
            print(f'  categories: "{name}" tipo="{tipo}"')

    con.commit()
    con.close()
    print(f'\nListo. {added} columna(s) añadida(s).')
