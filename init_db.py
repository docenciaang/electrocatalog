"""
Script de inicialización: carga las categorías predefinidas.
Ejecutar una vez tras el primer arranque: python init_db.py
Es idempotente — seguro ejecutar múltiples veces.
"""
from app import create_app
from models import db, Category

# (name, description, tipo)
CATEGORIES = [
    ('Resistencias',         'Resistencias de carbón, metal, SMD, arrays',            'resistencia'),
    ('Condensadores',        'Electrolíticos, cerámicos, tántalo, film',               'condensador'),
    ('Microcontroladores',   'Arduino, ESP32, STM32, PIC, ATmega',                     'microcontrolador'),
    ('Placas',               'Shields, módulos, breakout boards',                       None),
    ('Transistores',         'BJT, MOSFET, IGBT',                                       None),
    ('Diodos',               'Rectificadores, Zener, Schottky, LEDs',                   None),
    ('Circuitos Integrados', 'Amplificadores op., comparadores, reguladores, lógica',  'ic'),
    ('Sensores',             'Temperatura, humedad, presión, distancia, IMU',           None),
    ('Conectores',           'Pines, headers, JST, USB, barrel jack',                   None),
    ('Inductores',           'Bobinas, transformadores, ferrites',                      'inductor'),
    ('Displays',             'LCD, OLED, 7-segmentos, TFT',                             None),
    ('Herramientas',         'Cables, protoboards, puntas de soldador, accesorios',     None),
]

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        added = 0
        for name, desc, tipo in CATEGORIES:
            if not Category.query.filter_by(name=name).first():
                db.session.add(Category(name=name, description=desc, tipo=tipo))
                added += 1
        db.session.commit()
        print(f'Listo. {added} categorías añadidas ({len(CATEGORIES) - added} ya existían).')
