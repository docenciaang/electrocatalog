"""
Servidor MCP para ElectroCatalog.

Expone herramientas, recursos y prompts para gestionar el inventario de
componentes electrónicos desde cualquier cliente MCP (Claude Desktop, etc.).

Uso:
    # Modo desarrollo (abre inspector web en http://localhost:5173)
    mcp dev mcp_server.py

    # Modo producción (stdio — para Claude Desktop)
    python mcp_server.py
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from app import create_app

flask_app = create_app()
mcp = FastMCP("ElectroCatalog")


# ── Helpers de serialización ──────────────────────────────────────────────────

def _category_dict(cat) -> dict:
    return {
        "id": cat.id,
        "name": cat.name,
        "description": cat.description,
        "tipo": cat.tipo,
        "component_count": cat.component_count(),
    }


def _component_dict(c) -> dict:
    return {
        "id": c.id,
        "name": c.name,
        "description": c.description,
        "category_id": c.category_id,
        "category_name": c.category.name if c.category else None,
        "quantity": c.quantity,
        "estanteria": c.estanteria,
        "caja": c.caja,
        "image_url": c.image_url,
        "datasheet_url": c.datasheet_url,
        "notes": c.notes,
        "valor_display": c.valor_display,
        # Técnicos comunes
        "encapsulado": c.encapsulado,
        "tolerancia": c.tolerancia,
        "potencia_w": c.potencia_w,
        "voltaje_max_v": c.voltaje_max_v,
        # Específicos por tipo
        "valor_ohm": c.valor_ohm,
        "capacitancia_uf": c.capacitancia_uf,
        "inductancia_uh": c.inductancia_uh,
        "familia_ic": c.familia_ic,
        "pinout_url": c.pinout_url,
        "flash_kb": c.flash_kb,
        "ram_kb": c.ram_kb,
        "rom_kb": c.rom_kb,
        "voltaje_op_v": c.voltaje_op_v,
        "wifi": c.wifi,
        "bt": c.bt,
        "zigbee": c.zigbee,
        "lora": c.lora,
        "frecuencia_mhz": c.frecuencia_mhz,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }


# ── Resources ─────────────────────────────────────────────────────────────────

@mcp.resource("electrocatalog://categories")
def resource_categories() -> str:
    """Lista completa de categorías con conteo de componentes."""
    import json
    with flask_app.app_context():
        from models import Category
        cats = Category.query.order_by(Category.name).all()
        return json.dumps([_category_dict(c) for c in cats], ensure_ascii=False)


@mcp.resource("electrocatalog://components")
def resource_components() -> str:
    """Lista completa de componentes con todos sus campos."""
    import json
    with flask_app.app_context():
        from models import Component
        components = Component.query.order_by(Component.name).all()
        return json.dumps([_component_dict(c) for c in components], ensure_ascii=False)


@mcp.resource("electrocatalog://component/{component_id}")
def resource_component(component_id: str) -> str:
    """Detalle de un componente por ID."""
    import json
    with flask_app.app_context():
        from models import Component
        c = Component.query.get(int(component_id))
        if c is None:
            return json.dumps({"error": f"Componente {component_id} no encontrado"})
        return json.dumps(_component_dict(c), ensure_ascii=False)


# ── Tools ─────────────────────────────────────────────────────────────────────

@mcp.tool()
def list_categories() -> list[dict]:
    """Devuelve todas las categorías disponibles con su tipo y conteo de componentes."""
    with flask_app.app_context():
        from models import Category
        cats = Category.query.order_by(Category.name).all()
        return [_category_dict(c) for c in cats]


@mcp.tool()
def search_components(q: str = "", category_id: int | None = None) -> list[dict]:
    """
    Busca componentes por texto libre o categoría.

    Args:
        q: Texto a buscar en nombre, descripción, estantería o caja.
        category_id: Filtra por ID de categoría (opcional).

    Returns:
        Lista de componentes que coinciden, ordenados por nombre.
    """
    with flask_app.app_context():
        from models import Component, db
        query = Component.query
        if q:
            query = query.filter(
                db.or_(
                    Component.name.ilike(f"%{q}%"),
                    Component.description.ilike(f"%{q}%"),
                    Component.estanteria.ilike(f"%{q}%"),
                    Component.caja.ilike(f"%{q}%"),
                )
            )
        if category_id is not None:
            query = query.filter_by(category_id=category_id)
        return [_component_dict(c) for c in query.order_by(Component.name).all()]


@mcp.tool()
def get_component(component_id: int) -> dict:
    """
    Devuelve el detalle completo de un componente por su ID.

    Args:
        component_id: ID numérico del componente.

    Returns:
        Diccionario con todos los campos del componente, o error si no existe.
    """
    with flask_app.app_context():
        from models import Component
        c = Component.query.get(component_id)
        if c is None:
            return {"error": f"Componente con id={component_id} no encontrado"}
        return _component_dict(c)


@mcp.tool()
def create_component(
    name: str,
    category_id: int,
    quantity: int = 0,
    description: str = "",
    estanteria: str = "",
    caja: str = "",
    image_url: str = "",
    datasheet_url: str = "",
    notes: str = "",
    # Técnicos comunes
    encapsulado: str | None = None,
    tolerancia: float | None = None,
    potencia_w: float | None = None,
    voltaje_max_v: float | None = None,
    # Resistencias
    valor_ohm: float | None = None,
    # Condensadores
    capacitancia_uf: float | None = None,
    # Inductores
    inductancia_uh: float | None = None,
    # ICs y microcontroladores
    familia_ic: str | None = None,
    pinout_url: str | None = None,
    # Microcontroladores
    flash_kb: float | None = None,
    ram_kb: float | None = None,
    rom_kb: float | None = None,
    voltaje_op_v: float | None = None,
    frecuencia_mhz: float | None = None,
    wifi: bool = False,
    bt: bool = False,
    zigbee: bool = False,
    lora: bool = False,
) -> dict:
    """
    Crea un nuevo componente en el inventario.

    Args:
        name: Nombre del componente (obligatorio).
        category_id: ID de la categoría a la que pertenece (obligatorio).
        quantity: Stock inicial (por defecto 0).
        description: Descripción libre.
        estanteria: Identificador de estantería donde está físicamente.
        caja: Identificador de caja dentro de la estantería.
        image_url: URL o ruta de imagen.
        datasheet_url: URL o ruta del datasheet (PDF).
        notes: Notas adicionales (soporta HTML/Markdown).
        encapsulado: Tipo de encapsulado (THT, SMD, 0603, QFN…).
        tolerancia: Tolerancia en %.
        potencia_w: Potencia máxima en vatios.
        voltaje_max_v: Voltaje máximo en voltios.
        valor_ohm: Resistencia en ohmios (solo resistencias).
        capacitancia_uf: Capacitancia en µF (solo condensadores).
        inductancia_uh: Inductancia en µH (solo inductores).
        familia_ic: Familia del IC (TTL, CMOS, AVR…).
        pinout_url: URL de imagen de pinout.
        flash_kb: Memoria Flash en KB (microcontroladores).
        ram_kb: RAM en KB (microcontroladores).
        rom_kb: ROM/EEPROM en KB (microcontroladores).
        voltaje_op_v: Voltaje de operación en V (microcontroladores).
        frecuencia_mhz: Frecuencia de CPU en MHz (microcontroladores).
        wifi: Tiene WiFi integrado.
        bt: Tiene Bluetooth integrado.
        zigbee: Tiene Zigbee integrado.
        lora: Tiene LoRa integrado.

    Returns:
        Diccionario con el componente creado, o error si la categoría no existe.
    """
    with flask_app.app_context():
        from models import Category, Component, db

        category = Category.query.get(category_id)
        if category is None:
            return {"error": f"Categoría con id={category_id} no encontrada"}

        c = Component(
            name=name.strip(),
            description=description.strip(),
            category_id=category_id,
            quantity=quantity,
            estanteria=estanteria.strip() or None,
            caja=caja.strip() or None,
            image_url=image_url.strip() or None,
            datasheet_url=datasheet_url.strip() or None,
            notes=notes.strip() or None,
            encapsulado=encapsulado,
            tolerancia=tolerancia,
            potencia_w=potencia_w,
            voltaje_max_v=voltaje_max_v,
        )

        # Aplicar campos específicos según tipo de categoría
        _BOOL_FIELDS = {"wifi", "bt", "zigbee", "lora"}
        _TIPO_CAMPOS = {
            "resistencia":      ("valor_ohm",),
            "condensador":      ("capacitancia_uf",),
            "inductor":         ("inductancia_uh",),
            "ic":               ("familia_ic", "pinout_url"),
            "microcontrolador": ("familia_ic", "pinout_url", "flash_kb", "ram_kb",
                                 "rom_kb", "voltaje_op_v", "wifi", "bt", "zigbee",
                                 "lora", "frecuencia_mhz"),
        }
        all_specific = {
            "valor_ohm": valor_ohm, "capacitancia_uf": capacitancia_uf,
            "inductancia_uh": inductancia_uh, "familia_ic": familia_ic,
            "pinout_url": pinout_url, "flash_kb": flash_kb, "ram_kb": ram_kb,
            "rom_kb": rom_kb, "voltaje_op_v": voltaje_op_v, "wifi": wifi,
            "bt": bt, "zigbee": zigbee, "lora": lora, "frecuencia_mhz": frecuencia_mhz,
        }
        allowed = frozenset(_TIPO_CAMPOS.get(category.tipo, ()))
        for field, value in all_specific.items():
            setattr(c, field, value if field in allowed else (False if field in _BOOL_FIELDS else None))

        db.session.add(c)
        db.session.commit()
        return _component_dict(c)


@mcp.tool()
def update_stock(component_id: int, action: str) -> dict:
    """
    Incrementa o decrementa el stock de un componente en 1 unidad.

    Args:
        component_id: ID del componente.
        action: "inc" para incrementar, "dec" para decrementar (no baja de 0).

    Returns:
        Estado actualizado del componente, o error si no existe / acción inválida.
    """
    if action not in ("inc", "dec"):
        return {"error": f"Acción inválida: {action!r}. Usa 'inc' o 'dec'."}

    with flask_app.app_context():
        from models import Component, db
        c = Component.query.get(component_id)
        if c is None:
            return {"error": f"Componente con id={component_id} no encontrado"}

        if action == "inc":
            c.quantity += 1
        elif c.quantity > 0:
            c.quantity -= 1

        db.session.commit()
        return {"id": c.id, "name": c.name, "quantity": c.quantity}


@mcp.tool()
def enrich_component(component_id: int, provider: str | None = None) -> dict:
    """
    Usa un LLM para sugerir valores para los campos vacíos del componente.
    No modifica la base de datos — solo devuelve las sugerencias.

    Args:
        component_id: ID del componente a enriquecer.
        provider: Proveedor LLM a usar ("anthropic", "openai", "ollama", "docker").
                  Si se omite, usa el valor de la variable de entorno LLM_PROVIDER.

    Returns:
        Diccionario con los campos sugeridos por el LLM, o error.
    """
    with flask_app.app_context():
        from models import Component
        from services.llm_enrichment_service import enrich_component as _enrich

        c = Component.query.get(component_id)
        if c is None:
            return {"error": f"Componente con id={component_id} no encontrado"}

        try:
            suggestions = _enrich(c, provider)
            return {"component_id": component_id, "suggestions": suggestions}
        except KeyError as e:
            return {"error": f"API key no configurada: {e}"}
        except ValueError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": f"Error al contactar el LLM: {e}"}


# ── Prompts ───────────────────────────────────────────────────────────────────

@mcp.prompt()
def encontrar_componente(descripcion: str) -> str:
    """
    Genera un prompt para buscar un componente por características técnicas.

    Args:
        descripcion: Descripción del componente que se busca
                     (ej: "resistencia 10k SMD", "microcontrolador con WiFi y BT").
    """
    return f"""Busca en el inventario de ElectroCatalog un componente que coincida con:

"{descripcion}"

Pasos:
1. Usa `list_categories` para ver las categorías disponibles y sus tipos.
2. Usa `search_components` con palabras clave extraídas de la descripción.
3. Si los resultados son muchos, filtra por `category_id`.
4. Muestra los resultados encontrados con: nombre, cantidad en stock, ubicación \
(estantería/caja) y valor técnico principal (valor_display).
5. Si no encuentras nada, sugiere términos de búsqueda alternativos."""


@mcp.prompt()
def revisar_stock_bajo(umbral: int = 5) -> str:
    """
    Genera un prompt para analizar componentes con stock crítico.

    Args:
        umbral: Cantidad mínima considerada "stock bajo" (por defecto 5).
    """
    return f"""Analiza el inventario de ElectroCatalog para identificar componentes \
con stock bajo o agotado.

Definición de stock bajo: menos de {umbral} unidades.

Pasos:
1. Usa el resource `electrocatalog://components` para obtener todos los componentes.
2. Filtra los que tienen `quantity` < {umbral}.
3. Agrupa los resultados por categoría.
4. Para cada componente crítico muestra: nombre, categoría, stock actual y ubicación.
5. Ordena de menor a mayor stock (agotados primero).
6. Incluye un resumen con el total de componentes en estado crítico."""


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run(transport="stdio")
