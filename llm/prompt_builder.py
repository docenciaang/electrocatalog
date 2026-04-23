_FIELD_UNITS = {
    "valor_ohm":       "número en Ohmios (Ω). Ej: 10000 para 10kΩ",
    "capacitancia_uf": "número en microfaradios (µF). Ej: 0.1 para 100nF",
    "inductancia_uh":  "número en microhenrios (µH). Ej: 100 para 100µH",
    "tolerancia":      "número entre 0 y 100 representando porcentaje. Ej: 5 para ±5%",
    "potencia_w":      "número en vatios (W). Ej: 0.25 para 1/4W",
    "voltaje_max_v":   "número en voltios (V)",
    "voltaje_op_v":    "número en voltios (V). Voltaje típico de operación",
    "frecuencia_mhz":  "número en megahercios (MHz)",
    "flash_kb":        "número en kilobytes (KB)",
    "ram_kb":          "número en kilobytes (KB)",
    "rom_kb":          "número en kilobytes (KB). 0 si no tiene",
    "familia_ic":      "string. Familia o arquitectura (Ej: TTL, CMOS, AVR, ARM Cortex-M0, RISC-V)",
    "procesador":      "string. Modelo o núcleo del procesador (Ej: ESP32, STM32F411, ATmega328P, RP2040)",
    "encapsulado":     "string con nomenclatura estándar (Ej: THT, SMD, DIP-8, QFP-32, QFN-40, 0603, 0805)",
    "wifi":            "true o false",
    "bt":              "true o false (Bluetooth)",
    "zigbee":          "true o false",
    "lora":            "true o false",
    "description":     "string HTML simple, un párrafo <p> en español, máximo 3 frases",
    "notes":           "string HTML simple con notas técnicas relevantes en español, o null",
    "datasheet_url":   "URL directa al datasheet oficial del fabricante (PDF). null si no la conoces con certeza",
    "image_url":       "URL directa a una imagen del componente (PNG/JPG). null si no la conoces con certeza",
    "pinout_url":      "URL directa a un diagrama de pinout del componente (imagen o PDF). null si no la conoces con certeza",
}


def build_prompt(name: str, tipo: str | None, empty_fields: list[str]) -> str:
    field_lines = "\n".join(
        f'  - "{f}": {_FIELD_UNITS.get(f, "valor apropiado")}'
        for f in empty_fields
    )
    return f"""Eres un experto en componentes electrónicos.

Componente: "{name}"
Tipo de categoría: "{tipo or 'genérico'}"

Devuelve ÚNICAMENTE un objeto JSON (sin texto adicional, sin markdown) con estos campos:
{field_lines}

Reglas:
- Usa null si no puedes deducir el valor con certeza razonable.
- Los valores numéricos deben estar en las unidades indicadas.
- No incluyas unidades dentro de los valores numéricos, solo el número.
- "description" y "notes" son HTML simple (solo etiquetas <p>, <b>, <ul>, <li>).
- Responde solo con el JSON, sin explicaciones ni texto adicional.
"""
