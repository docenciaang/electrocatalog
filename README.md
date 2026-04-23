# ElectroCatalog

Catálogo web de componentes electrónicos desarrollado con Flask. Permite gestionar un inventario de componentes organizados por categorías, con seguimiento de stock, parámetros técnicos específicos por tipo y ubicación física en el taller.

## Funcionalidades

### Dashboard
- Resumen general: total de categorías, componentes y unidades en stock.
- Listado de los 5 componentes añadidos más recientemente.

### Componentes
- **Listado** con búsqueda por nombre, descripción, estantería o caja, y filtro por categoría.
- **Ficha de detalle** con toda la información del componente, imagen con vista a tamaño completo (lightbox), stock actual y parámetros técnicos.
- **Creación y edición** mediante formulario con:
  - Editor de texto enriquecido (Quill.js) en descripción y notas (negrita, cursiva, enlaces, listas…).
  - Subida de imagen local o introducción de URL, con vista previa en tiempo real.
  - Explorador de imágenes ya subidas a `static/`.
  - Selector visual de estantería (mapa interactivo).
  - Campos técnicos dinámicos según el tipo de categoría.
- **Control de stock** con botones +/− directamente desde el listado o la ficha.
- **Eliminación** con confirmación previa.

### Categorías
- CRUD completo de categorías.
- Cada categoría tiene un **tipo** que activa campos técnicos específicos en el formulario de componentes:

  | Tipo | Campos específicos |
  |---|---|
  | `resistencia` | Valor (Ω / kΩ / MΩ), tolerancia |
  | `condensador` | Capacitancia (pF / nF / µF), tolerancia |
  | `inductor` | Inductancia (µH / mH) |
  | `ic` | Familia/Arquitectura, imagen de pinout |
  | `microcontrolador` | Flash, RAM, ROM/EEPROM, voltaje de operación, frecuencia, conectividad (WiFi, Bluetooth, Zigbee, LoRa), imagen de pinout |

- Protección: no se puede eliminar una categoría que tenga componentes asociados.

### Gestión de imágenes
- Endpoint `/images/upload` para subir imágenes (PNG, JPG, JPEG, GIF, WebP, SVG, BMP) a `static/img/`.
- Endpoint `/images/` que devuelve el listado de todas las imágenes disponibles en `static/`.

## Tecnologías

| Capa | Tecnología |
|---|---|
| Backend | Python 3 / Flask 3 |
| ORM / BD | Flask-SQLAlchemy 3 + SQLite |
| Frontend | Bootstrap 5.3 + Bootstrap Icons 1.11 |
| Editor rich text | Quill.js 2 (Snow theme) |

## Instalación

```bash
# 1. Clonar el repositorio
git clone <url-del-repo>
cd componentes

# 2. Crear y activar entorno virtual
python -m venv venv
# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Inicializar la base de datos
python init_db.py

# 5. Arrancar la aplicación
python app.py
```

La aplicación queda disponible en `http://localhost:5000`.

## Estructura del proyecto

```
componentes/
├── app.py               # Configuración y arranque de Flask
├── models.py            # Modelos SQLAlchemy (Category, Component)
├── routes.py            # Rutas y lógica de negocio
├── init_db.py           # Script de inicialización de la BD
├── migrate_db.py        # Script de migración de la BD
├── requirements.txt
├── static/
│   ├── estanteria.jpg   # Imagen del mapa de estantería
│   └── img/             # Imágenes subidas de componentes
└── templates/
    ├── base.html
    ├── index.html
    ├── categories/
    │   ├── list.html
    │   ├── form.html
    │   └── confirm_delete.html
    └── components/
        ├── list.html
        ├── detail.html
        ├── form.html
        └── confirm_delete.html
```

## Servidor MCP

`mcp_server.py` expone el inventario como servidor [MCP](https://modelcontextprotocol.io/) para clientes como Claude Desktop.

### Arranque

```bash
# Modo desarrollo — abre el inspector web en http://localhost:5173
mcp dev mcp_server.py

# Modo producción (stdio, para Claude Desktop)
python mcp_server.py
```

### Recursos

| URI | Descripción |
|---|---|
| `electrocatalog://categories` | Lista completa de categorías con conteo de componentes |
| `electrocatalog://components` | Lista completa de componentes con todos sus campos |
| `electrocatalog://component/{id}` | Detalle de un componente por ID |

### Herramientas

| Herramienta | Descripción |
|---|---|
| `list_categories` | Devuelve todas las categorías con su tipo y conteo |
| `search_components(q, category_id)` | Búsqueda por texto libre y/o categoría |
| `get_component(component_id)` | Detalle completo de un componente |
| `create_component(name, category_id, …)` | Crea un componente con todos sus campos técnicos |
| `update_stock(component_id, action)` | Incrementa (`inc`) o decrementa (`dec`) el stock en 1 |
| `enrich_component(component_id, provider)` | Sugiere valores para campos vacíos usando un LLM (no modifica la BD) |

### Prompts

| Prompt | Descripción |
|---|---|
| `encontrar_componente(descripcion)` | Guía al LLM para buscar un componente por características técnicas |
| `revisar_stock_bajo(umbral)` | Guía al LLM para identificar componentes con stock crítico |

### Integración con Claude Desktop

Añade esta entrada a tu `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "electrocatalog": {
      "command": "python",
      "args": ["C:/ruta/a/componentes/mcp_server.py"]
    }
  }
}
```

> Si usas entorno virtual, sustituye `python` por la ruta al ejecutable dentro de `.venv`
> (p. ej. `C:/ruta/a/componentes/.venv/Scripts/python.exe`).

## Notas

- La base de datos SQLite se crea en `instance/components.db` y está excluida del repositorio (`.gitignore`).
- Las imágenes subidas se almacenan en `static/img/` y sí se incluyen en el repositorio.
- Los campos de descripción y notas se almacenan como HTML generado por Quill y se renderizan con `| safe` en las plantillas (uso interno).
