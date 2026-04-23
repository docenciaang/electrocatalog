from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False, unique=True)
    description = db.Column(db.String(256))
    tipo = db.Column(db.String(32))  # 'resistencia' | 'condensador' | 'inductor' | 'ic' | 'microcontrolador' | None
    components = db.relationship(
        'Component', backref='category', lazy='dynamic', cascade='all, delete-orphan'
    )

    def component_count(self):
        return self.components.count()

    def __repr__(self):
        return f'<Category {self.name}>'


class Component(db.Model):
    __tablename__ = 'components'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    estanteria = db.Column(db.String(64))   # ej: "Cajón A", "Estante 3"
    caja       = db.Column(db.String(64))   # ej: "Caja azul", "Compartimento B4"
    image_url     = db.Column(db.String(512))
    datasheet_url = db.Column(db.String(512))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ── Atributos técnicos comunes ──────────────────────────────────────────
    encapsulado  = db.Column(db.String(32))   # THT, SMD, 0603, QFN…
    tolerancia   = db.Column(db.Float)        # %
    potencia_w   = db.Column(db.Float)        # W
    voltaje_max_v = db.Column(db.Float)       # V
    # temp_op_min / temp_op_max eliminados de la UI (columnas conservadas en BD)

    # ── Atributos específicos por tipo ──────────────────────────────────────
    valor_ohm      = db.Column(db.Float)      # Resistencias (Ω)
    capacitancia_uf = db.Column(db.Float)     # Condensadores (µF)
    inductancia_uh  = db.Column(db.Float)     # Inductores (µH)
    familia_ic      = db.Column(db.String(64))  # ICs (TTL, CMOS, AVR…)
    pinout_url      = db.Column(db.String(512)) # ICs — imagen/URL pinout
    flash_kb        = db.Column(db.Float)       # Microcontroladores — Flash (KB)
    ram_kb          = db.Column(db.Float)       # Microcontroladores — RAM (KB)
    rom_kb          = db.Column(db.Float)       # Microcontroladores — ROM/EEPROM (KB)
    voltaje_op_v    = db.Column(db.Float)       # Microcontroladores — voltaje operación (V)
    wifi            = db.Column(db.Boolean, default=False)  # Conectividad
    bt              = db.Column(db.Boolean, default=False)
    zigbee          = db.Column(db.Boolean, default=False)
    lora            = db.Column(db.Boolean, default=False)
    frecuencia_mhz  = db.Column(db.Float)       # Frecuencia CPU (MHz)
    procesador      = db.Column(db.String(128))  # Microcontroladores — núcleo/procesador (ej: ESP32, STM32F4)

    @property
    def valor_display(self):
        """Devuelve el valor técnico principal formateado según el tipo de categoría."""
        tipo = (self.category.tipo if self.category else None)
        if tipo == 'resistencia' and self.valor_ohm is not None:
            v = self.valor_ohm
            if v >= 1_000_000:
                return f'{v/1_000_000:g} MΩ'
            if v >= 1_000:
                return f'{v/1_000:g} kΩ'
            return f'{v:g} Ω'
        if tipo == 'condensador' and self.capacitancia_uf is not None:
            v = self.capacitancia_uf
            if v < 0.001:
                return f'{v*1_000_000:g} pF'
            if v < 1:
                return f'{v*1_000:g} nF'
            return f'{v:g} µF'
        if tipo == 'inductor' and self.inductancia_uh is not None:
            v = self.inductancia_uh
            if v >= 1_000:
                return f'{v/1_000:g} mH'
            return f'{v:g} µH'
        return None

    def __repr__(self):
        return f'<Component {self.name}>'
