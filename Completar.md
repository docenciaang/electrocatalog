# Módulo de enriquecimiento de componentes con LLM

## Objetivo

Completar automáticamente los campos técnicos de un componente electrónico a partir de su nombre
y categoría, usando un modelo de lenguaje (LLM). El proceso se lanza desde la página de edición
del componente y propone valores que el usuario puede aceptar, modificar o rechazar antes de guardar.

---

## Arquitectura general

```
[Formulario de edición]
        |
        | click "Completar con IA"
        | AJAX POST /components/<id>/enrich
        v
[Flask Route — routes.py]
        |
        v
[LLMEnrichmentService]
        |
        |-----------------------------+
        v                            v
[PromptBuilder]              [LLMProvider (abstracto)]
        |                            |
        | prompt str                 |--- AnthropicProvider
        v                            |--- OpenAIProvider
[LLMProvider.generate()]             |--- OllamaProvider
        |
        v
[ResponseValidator — Pydantic]
        |
        v
[JSON con campos sugeridos]
        |
        v
[UI: rellena formulario, usuario decide]
```

**Flujo:** síncrono. La llamada AJAX espera la respuesta antes de actualizar la UI.

---

## Campos completados por tipo de componente

El LLM recibe el **nombre** del componente (y el tipo de categoría) como contexto
y devuelve los campos que están vacíos o sin informar.

| Tipo | Contexto enviado al LLM | Campos que completa el LLM |
|---|---|---|
| `resistencia` | nombre | `valor_ohm`, `encapsulado`, `tolerancia`, `potencia_w`, `voltaje_max_v`, `description` |
| `condensador` | nombre | `capacitancia_uf`, `encapsulado`, `tolerancia`, `voltaje_max_v`, `description` |
| `inductor` | nombre | `inductancia_uh`, `encapsulado`, `tolerancia`, `potencia_w`, `description` |
| `ic` | nombre | `familia_ic`, `encapsulado`, `voltaje_max_v`, `description`, `notes` |
| `microcontrolador` | nombre | `flash_kb`, `ram_kb`, `rom_kb`, `voltaje_op_v`, `frecuencia_mhz`, `wifi`, `bt`, `zigbee`, `lora`, `familia_ic`, `encapsulado`, `description` |
| genérico | nombre, categoría | `encapsulado`, `description` |

Solo se proponen campos que el usuario tiene vacíos. Los campos ya rellenos no se sobreescriben
salvo que el usuario lo indique explícitamente.

---

## Endpoint Flask

```
POST /components/<int:id>/enrich
Content-Type: application/json

Body (opcional):
{
  "provider": "anthropic"   // "anthropic" | "openai" | "ollama"
                            // Si se omite, usa LLM_PROVIDER del entorno
}

Respuesta 200 OK:
{
  "fields": {
    "valor_ohm": 10000.0,
    "encapsulado": "THT",
    "tolerancia": 5.0,
    "potencia_w": 0.25,
    "voltaje_max_v": null,
    "description": "<p>Resistencia de 10 kΩ para uso general...</p>"
  }
}

Respuesta 422 — validación fallida:
{ "error": "Campo 'valor_ohm' fuera de rango", "detail": {...} }

Respuesta 503 — proveedor no configurado:
{ "error": "API key no configurada para el proveedor 'anthropic'" }

Respuesta 504 — timeout:
{ "error": "El proveedor LLM no respondió en el tiempo máximo" }
```

---

## Integración en la UI

Se añade un botón en `templates/components/form.html`, visible **solo en modo edición**,
junto al encabezado del formulario:

```html
{% if component %}
<button type="button" id="btn-enrich"
        class="btn btn-outline-primary btn-sm">
  <i class="bi bi-stars"></i> Completar con IA
  <span id="enrich-spinner" class="spinner-border spinner-border-sm d-none"></span>
</button>
{% endif %}
```

**Comportamiento:**
1. Click → spinner visible, botón deshabilitado.
2. AJAX `POST /components/{{ component.id }}/enrich`.
3. Respuesta → cada campo sugerido se rellena en el formulario y se marca con fondo amarillo
   (`background: #fffbe6`) para distinguirlo de lo que ya existía.
4. Si el campo tiene editor Quill (descripción, notas), se usa `quill.root.innerHTML = valor`.
5. Error → toast de Bootstrap con el mensaje.

El usuario puede editar los valores propuestos y guardar el formulario de forma normal.

---

## Estructura de ficheros

```
componentes/
├── routes.py                       ← añadir ruta /enrich
├── llm/
│   ├── __init__.py
│   ├── provider_base.py            ← clase abstracta LLMProvider
│   ├── anthropic_provider.py
│   ├── openai_provider.py
│   ├── ollama_provider.py
│   ├── prompt_builder.py           ← build_prompt(component_data, tipo)
│   └── schemas.py                  ← modelos Pydantic por tipo
└── services/
    └── llm_enrichment_service.py   ← orquesta provider + prompt + validación
```

---

## Componentes software

### LLMProvider — interfaz abstracta (`llm/provider_base.py`)

```python
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    def generate_structured(self, prompt: str, max_tokens: int = 1024) -> dict:
        """Llama al modelo y devuelve un dict con el JSON parseado.
        Lanza ValueError si la respuesta no es JSON válido."""
        ...
```

### AnthropicProvider (`llm/anthropic_provider.py`)

```python
import os, json
import anthropic
from .provider_base import LLMProvider

class AnthropicProvider(LLMProvider):
    MODEL = "claude-haiku-4-5-20251001"   # rápido y económico para este uso

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    def generate_structured(self, prompt: str, max_tokens: int = 1024) -> dict:
        msg = self.client.messages.create(
            model=self.MODEL,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        text = msg.content[0].text.strip()
        # Extraer JSON si viene envuelto en ```json ... ```
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text)
```

### OpenAIProvider (`llm/openai_provider.py`)

```python
import os, json
from openai import OpenAI
from .provider_base import LLMProvider

class OpenAIProvider(LLMProvider):
    MODEL = "gpt-4o-mini"

    def __init__(self):
        self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    def generate_structured(self, prompt: str, max_tokens: int = 1024) -> dict:
        resp = self.client.chat.completions.create(
            model=self.MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            response_format={"type": "json_object"},  # fuerza JSON
        )
        return json.loads(resp.choices[0].message.content)
```

### OllamaProvider (`llm/ollama_provider.py`)

```python
import os, json, requests
from .provider_base import LLMProvider

class OllamaProvider(LLMProvider):
    def __init__(self):
        self.base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model    = os.environ.get("OLLAMA_MODEL", "llama3.2")

    def generate_structured(self, prompt: str, max_tokens: int = 1024) -> dict:
        resp = requests.post(
            f"{self.base_url}/api/generate",
            json={"model": self.model, "prompt": prompt, "stream": False},
            timeout=60,
        )
        resp.raise_for_status()
        text = resp.json()["response"].strip()
        if text.startswith("```"):
            text = text.split("```")[1].lstrip("json").strip()
        return json.loads(text)
```

---

### PromptBuilder (`llm/prompt_builder.py`)

```python
def build_prompt(name: str, tipo: str | None, empty_fields: list[str]) -> str:
    fields_str = ", ".join(empty_fields)
    base = f"""Eres un experto en componentes electrónicos.
Dado el nombre del componente: "{name}"
Categoría: "{tipo or 'genérico'}"

Devuelve ÚNICAMENTE un objeto JSON (sin texto adicional, sin markdown) con estos campos:
{fields_str}

Reglas estrictas:
- Usa null si no puedes deducir el valor con certeza.
- Valores numéricos en las unidades indicadas (Ω, µF, µH, KB, V, W, MHz, %).
- Los booleanos (wifi, bt, zigbee, lora) son true o false.
- "description" es HTML simple (párrafo <p>), máximo 3 frases, en español.
- "encapsulado": usa nomenclatura estándar (THT, SMD, 0402, 0603, 0805, DIP-8, QFP-32...).
- "familia_ic": arquitectura o familia lógica (TTL, CMOS, AVR, ARM Cortex-M0...).
"""
    return base
```

**Ejemplo de prompt generado para una resistencia `10k THT`:**

```
Eres un experto en componentes electrónicos.
Dado el nombre del componente: "Resistencia 10k THT"
Categoría: "resistencia"

Devuelve ÚNICAMENTE un objeto JSON con estos campos:
valor_ohm, encapsulado, tolerancia, potencia_w, voltaje_max_v, description

Reglas estrictas:
- Usa null si no puedes deducir el valor con certeza.
- Valores numéricos en las unidades indicadas (Ω, µF...).
- "description" es HTML simple, máximo 3 frases, en español.
...
```

**Respuesta esperada:**

```json
{
  "valor_ohm": 10000.0,
  "encapsulado": "THT",
  "tolerancia": 5.0,
  "potencia_w": 0.25,
  "voltaje_max_v": null,
  "description": "<p>Resistencia de 10 kΩ de montaje pasante (THT) para uso general en circuitos de baja potencia.</p>"
}
```

**Ejemplo de prompt para microcontrolador `ESP32-C6`:**

```
Nombre: "ESP32-C6"
Categoría: "microcontrolador"
Campos: flash_kb, ram_kb, rom_kb, voltaje_op_v, frecuencia_mhz, wifi, bt, zigbee, lora,
        familia_ic, encapsulado, description
```

**Respuesta esperada:**

```json
{
  "flash_kb": 4096,
  "ram_kb": 512,
  "rom_kb": 448,
  "voltaje_op_v": 3.3,
  "frecuencia_mhz": 160,
  "wifi": true,
  "bt": true,
  "zigbee": true,
  "lora": false,
  "familia_ic": "RISC-V",
  "encapsulado": "QFN-40",
  "description": "<p>Microcontrolador RISC-V de 32 bits con conectividad WiFi 6, Bluetooth 5 y Zigbee/Thread integrados.</p>"
}
```

---

### Schemas Pydantic (`llm/schemas.py`)

```python
from pydantic import BaseModel, Field
from typing import Optional

class ResistenciaEnrichment(BaseModel):
    valor_ohm:    Optional[float] = None
    encapsulado:  Optional[str]   = None
    tolerancia:   Optional[float] = Field(None, ge=0, le=100)
    potencia_w:   Optional[float] = Field(None, ge=0)
    voltaje_max_v: Optional[float] = Field(None, ge=0)
    description:  Optional[str]   = None

class CondensadorEnrichment(BaseModel):
    capacitancia_uf: Optional[float] = Field(None, ge=0)
    encapsulado:     Optional[str]   = None
    tolerancia:      Optional[float] = Field(None, ge=0, le=100)
    voltaje_max_v:   Optional[float] = Field(None, ge=0)
    description:     Optional[str]   = None

class InductorEnrichment(BaseModel):
    inductancia_uh: Optional[float] = Field(None, ge=0)
    encapsulado:    Optional[str]   = None
    tolerancia:     Optional[float] = Field(None, ge=0, le=100)
    potencia_w:     Optional[float] = Field(None, ge=0)
    description:    Optional[str]   = None

class ICEnrichment(BaseModel):
    familia_ic:   Optional[str]   = None
    encapsulado:  Optional[str]   = None
    voltaje_max_v: Optional[float] = Field(None, ge=0)
    description:  Optional[str]   = None
    notes:        Optional[str]   = None

class MicrocontroladorEnrichment(BaseModel):
    flash_kb:      Optional[float] = Field(None, ge=0)
    ram_kb:        Optional[float] = Field(None, ge=0)
    rom_kb:        Optional[float] = Field(None, ge=0)
    voltaje_op_v:  Optional[float] = Field(None, ge=0)
    frecuencia_mhz: Optional[float] = Field(None, ge=0)
    wifi:    Optional[bool] = None
    bt:      Optional[bool] = None
    zigbee:  Optional[bool] = None
    lora:    Optional[bool] = None
    familia_ic:  Optional[str] = None
    encapsulado: Optional[str] = None
    description: Optional[str] = None

class GenericoEnrichment(BaseModel):
    encapsulado: Optional[str] = None
    description: Optional[str] = None

SCHEMA_BY_TIPO = {
    "resistencia":    ResistenciaEnrichment,
    "condensador":    CondensadorEnrichment,
    "inductor":       InductorEnrichment,
    "ic":             ICEnrichment,
    "microcontrolador": MicrocontroladorEnrichment,
}

def get_schema(tipo: str | None):
    return SCHEMA_BY_TIPO.get(tipo or "", GenericoEnrichment)
```

---

### LLMEnrichmentService (`services/llm_enrichment_service.py`)

```python
import os
from llm.provider_base import LLMProvider
from llm.anthropic_provider import AnthropicProvider
from llm.openai_provider    import OpenAIProvider
from llm.ollama_provider    import OllamaProvider
from llm.prompt_builder     import build_prompt
from llm.schemas            import get_schema

_PROVIDERS = {
    "anthropic": AnthropicProvider,
    "openai":    OpenAIProvider,
    "ollama":    OllamaProvider,
}

def get_provider(name: str | None = None) -> LLMProvider:
    name = name or os.environ.get("LLM_PROVIDER", "anthropic")
    cls  = _PROVIDERS.get(name)
    if cls is None:
        raise ValueError(f"Proveedor desconocido: {name!r}")
    return cls()

def enrich_component(component, provider_name: str | None = None) -> dict:
    """
    Devuelve un dict con los campos sugeridos por el LLM.
    Solo incluye campos que el componente tiene vacíos.
    """
    tipo   = component.category.tipo if component.category else None
    schema = get_schema(tipo)
    # Campos vacíos en el componente
    empty  = [f for f in schema.model_fields if getattr(component, f, None) in (None, False, "")]
    if not empty:
        return {}

    provider = get_provider(provider_name)
    prompt   = build_prompt(component.name, tipo, empty)
    raw      = provider.generate_structured(prompt)

    # Validar con Pydantic (descarta campos no esperados, valida rangos)
    validated = schema(**raw)
    return {k: v for k, v in validated.model_dump().items() if v is not None}
```

---

### Ruta Flask (`routes.py` — añadir)

```python
@main.route('/components/<int:id>/enrich', methods=['POST'])
def component_enrich(id):
    import traceback
    from services.llm_enrichment_service import enrich_component, get_provider
    from pydantic import ValidationError

    component = db.get_or_404(Component, id)
    data      = request.get_json(silent=True) or {}
    provider_name = data.get('provider')

    try:
        fields = enrich_component(component, provider_name)
        return jsonify(fields=fields)
    except KeyError as e:
        return jsonify(error=f"API key no configurada: {e}"), 503
    except ValidationError as e:
        return jsonify(error="Respuesta del LLM inválida", detail=e.errors()), 422
    except TimeoutError:
        return jsonify(error="El proveedor LLM no respondió en el tiempo máximo"), 504
    except Exception:
        traceback.print_exc()
        return jsonify(error="Error interno al contactar el LLM"), 500
```

---

## Configuración

Variables de entorno (fichero `.env`, excluido del repositorio):

```ini
# Proveedor activo: anthropic | openai | ollama
LLM_PROVIDER=anthropic

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# OpenAI
OPENAI_API_KEY=sk-...

# Ollama (servidor local)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

Cargar en `app.py`:

```python
from dotenv import load_dotenv
load_dotenv()
```

---

## Dependencias (`requirements.txt`)

```
Flask>=3.0
Flask-SQLAlchemy>=3.1
anthropic>=0.25
openai>=1.0
pydantic>=2.0
python-dotenv>=1.0
# requests ya está disponible como dependencia transitiva
```

> Ollama no requiere SDK propio: se comunica vía HTTP con `requests`.

---

## Manejo de errores

| Situación | Comportamiento |
|---|---|
| API key ausente | `KeyError` → HTTP 503 |
| LLM devuelve texto no JSON | `json.JSONDecodeError` → HTTP 500 (loggear) |
| JSON no cumple el schema | `pydantic.ValidationError` → HTTP 422 con detalle |
| Timeout de red | `requests.Timeout` / `TimeoutError` → HTTP 504 |
| Todos los campos ya rellenos | Devuelve `{ "fields": {} }` sin llamar al LLM |
| Proveedor desconocido | `ValueError` → HTTP 400 |

---

## Diagrama de secuencia

```
Usuario          form.html         Flask /enrich      LLMEnrichment      LLMProvider
   |                 |                   |                  |                  |
   |--click btn----->|                   |                  |                  |
   |                 |--POST /enrich---->|                  |                  |
   |                 |                   |--enrich_comp()-->|                  |
   |                 |                   |                  |--build_prompt()  |
   |                 |                   |                  |--generate()----->|
   |                 |                   |                  |                  |--API call-->
   |                 |                   |                  |                  |<--JSON------
   |                 |                   |                  |<-validate Pydantic|
   |                 |                   |<----fields dict--|                  |
   |                 |<--200 { fields }--|                  |                  |
   |<-rellena form---|                   |                  |                  |
   |  (fondo amarillo|                   |                  |                  |
   |   en campos)    |                   |                  |                  |
   |--guarda form--->|                   |                  |                  |
```
