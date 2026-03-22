import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, \
                  current_app, jsonify
from werkzeug.utils import secure_filename
from models import db, Category, Component

_IMG_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'bmp'}
_IMG_SUBDIR     = 'img'   # subdirectorio dentro de static/

def _is_image(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in _IMG_EXTENSIONS

main = Blueprint('main', __name__)


def _float_or_none(value):
    """Convierte un string de formulario a float, o None si está vacío."""
    v = (value or '').strip()
    try:
        return float(v) if v else None
    except ValueError:
        return None


# Campos específicos permitidos por tipo de categoría
_TIPO_CAMPOS = {
    'resistencia':      ('valor_ohm',),
    'condensador':      ('capacitancia_uf',),
    'inductor':         ('inductancia_uh',),
    'ic':               ('familia_ic', 'pinout_url'),
    'microcontrolador': ('familia_ic', 'pinout_url', 'flash_kb', 'ram_kb', 'rom_kb',
                         'voltaje_op_v', 'wifi', 'bt', 'zigbee', 'lora', 'frecuencia_mhz'),
}
_ALL_SPECIFIC = frozenset({
    'valor_ohm', 'capacitancia_uf', 'inductancia_uh',
    'familia_ic', 'pinout_url',
    'flash_kb', 'ram_kb', 'rom_kb', 'voltaje_op_v',
    'wifi', 'bt', 'zigbee', 'lora', 'frecuencia_mhz',
})
_SPECIFIC_STR  = frozenset({'familia_ic', 'pinout_url'})
_SPECIFIC_BOOL = frozenset({'wifi', 'bt', 'zigbee', 'lora'})


def _apply_tech_fields(component, form, category_tipo=None):
    """Copia campos técnicos del formulario. Limpia los específicos irrelevantes según tipo."""
    # Campos comunes: siempre se guardan
    component.encapsulado   = form.get('encapsulado', '').strip() or None
    component.tolerancia    = _float_or_none(form.get('tolerancia'))
    component.potencia_w    = _float_or_none(form.get('potencia_w'))
    component.voltaje_max_v = _float_or_none(form.get('voltaje_max_v'))

    # Campos específicos: solo los del tipo activo; el resto se limpia a None/False
    allowed = frozenset(_TIPO_CAMPOS.get(category_tipo, ()))
    for field in _ALL_SPECIFIC:
        if field in allowed:
            if field in _SPECIFIC_BOOL:
                setattr(component, field, form.get(field) == 'on')
            elif field in _SPECIFIC_STR:
                setattr(component, field, form.get(field, '').strip() or None)
            else:
                setattr(component, field, _float_or_none(form.get(field)))
        else:
            setattr(component, field, False if field in _SPECIFIC_BOOL else None)


# ── Dashboard ────────────────────────────────────────────────────────────────

@main.route('/')
def index():
    total_categories = Category.query.count()
    total_components = Component.query.count()
    total_stock = db.session.query(db.func.sum(Component.quantity)).scalar() or 0
    latest = Component.query.order_by(Component.created_at.desc()).limit(5).all()
    return render_template('index.html',
                           total_categories=total_categories,
                           total_components=total_components,
                           total_stock=total_stock,
                           latest=latest)


# ── Components ────────────────────────────────────────────────────────────────

@main.route('/components/')
def components_list():
    q = request.args.get('q', '').strip()
    category_id = request.args.get('category_id', type=int)
    query = Component.query

    if q:
        query = query.filter(
            db.or_(
                Component.name.ilike(f'%{q}%'),
                Component.description.ilike(f'%{q}%'),
                Component.estanteria.ilike(f'%{q}%'),
                Component.caja.ilike(f'%{q}%'),
            )
        )
    if category_id:
        query = query.filter_by(category_id=category_id)

    components = query.order_by(Component.name).all()
    categories = Category.query.order_by(Category.name).all()
    return render_template('components/list.html',
                           components=components,
                           categories=categories,
                           q=q,
                           category_id=category_id)


@main.route('/components/new', methods=['GET', 'POST'])
def component_new():
    categories = Category.query.order_by(Category.name).all()
    if request.method == 'POST':
        name = request.form['name'].strip()
        if not name:
            flash('El nombre es obligatorio.', 'danger')
            return render_template('components/form.html', categories=categories,
                                   component=None, action=url_for('main.component_new'))
        component = Component(
            name=name,
            description=request.form.get('description', '').strip(),
            category_id=int(request.form['category_id']),
            quantity=int(request.form.get('quantity', 0) or 0),
            estanteria=request.form.get('estanteria', '').strip(),
            caja=request.form.get('caja', '').strip(),
            image_url=request.form.get('image_url', '').strip() or None,
            datasheet_url=request.form.get('datasheet_url', '').strip(),
            notes=request.form.get('notes', '').strip(),
        )
        category = db.get_or_404(Category, component.category_id)
        _apply_tech_fields(component, request.form, category_tipo=category.tipo)
        db.session.add(component)
        db.session.commit()
        flash(f'Componente «{component.name}» creado correctamente.', 'success')
        return redirect(url_for('main.components_list'))
    return render_template('components/form.html', categories=categories,
                           component=None, action=url_for('main.component_new'))


@main.route('/components/<int:id>')
def component_detail(id):
    component = db.get_or_404(Component, id)
    return render_template('components/detail.html', component=component)


@main.route('/components/<int:id>/edit', methods=['GET', 'POST'])
def component_edit(id):
    component = db.get_or_404(Component, id)
    categories = Category.query.order_by(Category.name).all()
    if request.method == 'POST':
        name = request.form['name'].strip()
        if not name:
            flash('El nombre es obligatorio.', 'danger')
            return render_template('components/form.html', categories=categories,
                                   component=component,
                                   action=url_for('main.component_edit', id=id))
        component.name = name
        component.description = request.form.get('description', '').strip()
        component.category_id = int(request.form['category_id'])
        component.quantity = int(request.form.get('quantity', 0) or 0)
        component.estanteria = request.form.get('estanteria', '').strip()
        component.caja   = request.form.get('caja', '').strip()
        component.image_url = request.form.get('image_url', '').strip() or None
        component.datasheet_url = request.form.get('datasheet_url', '').strip()
        component.notes = request.form.get('notes', '').strip()
        category = db.get_or_404(Category, component.category_id)
        _apply_tech_fields(component, request.form, category_tipo=category.tipo)
        db.session.commit()
        flash(f'Componente «{component.name}» actualizado.', 'success')
        return redirect(url_for('main.component_detail', id=component.id))
    return render_template('components/form.html', categories=categories,
                           component=component,
                           action=url_for('main.component_edit', id=id))


@main.route('/components/<int:id>/delete', methods=['GET', 'POST'])
def component_delete(id):
    component = db.get_or_404(Component, id)
    if request.method == 'POST':
        name = component.name
        db.session.delete(component)
        db.session.commit()
        flash(f'Componente «{name}» eliminado.', 'warning')
        return redirect(url_for('main.components_list'))
    return render_template('components/confirm_delete.html', component=component)


@main.route('/components/<int:id>/stock', methods=['POST'])
def component_stock(id):
    component = db.get_or_404(Component, id)
    action = request.form.get('action')
    if action == 'inc':
        component.quantity += 1
    elif action == 'dec' and component.quantity > 0:
        component.quantity -= 1
    db.session.commit()
    return redirect(url_for('main.components_list',
                            q=request.form.get('q', ''),
                            category_id=request.form.get('category_id', '')))


# ── Imágenes locales ──────────────────────────────────────────────────────────

@main.route('/images/upload', methods=['POST'])
def image_upload():
    f = request.files.get('file')
    if not f or not _is_image(f.filename):
        return jsonify(error='Tipo de archivo no permitido'), 400
    filename = secure_filename(f.filename)
    upload_dir = os.path.join(current_app.static_folder, _IMG_SUBDIR)
    os.makedirs(upload_dir, exist_ok=True)
    f.save(os.path.join(upload_dir, filename))
    return jsonify(url=url_for('static', filename=f'{_IMG_SUBDIR}/{filename}'))


@main.route('/images/')
def images_list():
    static = current_app.static_folder
    result = []
    for root, _dirs, files in os.walk(static):
        for fname in sorted(files):
            if _is_image(fname):
                rel = os.path.relpath(os.path.join(root, fname), static).replace('\\', '/')
                result.append({'name': fname, 'rel': rel,
                               'url': url_for('static', filename=rel)})
    return jsonify(result)


# ── Categories ────────────────────────────────────────────────────────────────

@main.route('/categories/')
def categories_list():
    categories = Category.query.order_by(Category.name).all()
    return render_template('categories/list.html', categories=categories)


@main.route('/categories/new', methods=['GET', 'POST'])
def category_new():
    if request.method == 'POST':
        name = request.form['name'].strip()
        if not name:
            flash('El nombre es obligatorio.', 'danger')
            return render_template('categories/form.html', category=None,
                                   action=url_for('main.category_new'))
        if Category.query.filter_by(name=name).first():
            flash('Ya existe una categoría con ese nombre.', 'danger')
            return render_template('categories/form.html', category=None,
                                   action=url_for('main.category_new'))
        category = Category(
            name=name,
            description=request.form.get('description', '').strip(),
            tipo=request.form.get('tipo', '').strip() or None,
        )
        db.session.add(category)
        db.session.commit()
        flash(f'Categoría «{category.name}» creada.', 'success')
        return redirect(url_for('main.categories_list'))
    return render_template('categories/form.html', category=None,
                           action=url_for('main.category_new'))


@main.route('/categories/<int:id>/edit', methods=['GET', 'POST'])
def category_edit(id):
    category = db.get_or_404(Category, id)
    if request.method == 'POST':
        name = request.form['name'].strip()
        if not name:
            flash('El nombre es obligatorio.', 'danger')
            return render_template('categories/form.html', category=category,
                                   action=url_for('main.category_edit', id=id))
        existing = Category.query.filter_by(name=name).first()
        if existing and existing.id != id:
            flash('Ya existe una categoría con ese nombre.', 'danger')
            return render_template('categories/form.html', category=category,
                                   action=url_for('main.category_edit', id=id))
        category.name = name
        category.description = request.form.get('description', '').strip()
        category.tipo = request.form.get('tipo', '').strip() or None
        db.session.commit()
        flash(f'Categoría «{category.name}» actualizada.', 'success')
        return redirect(url_for('main.categories_list'))
    return render_template('categories/form.html', category=category,
                           action=url_for('main.category_edit', id=id))


@main.route('/categories/<int:id>/delete', methods=['GET', 'POST'])
def category_delete(id):
    category = db.get_or_404(Category, id)
    if request.method == 'POST':
        if category.component_count() > 0:
            flash(f'No se puede eliminar: la categoría tiene {category.component_count()} componente(s) asociado(s).', 'danger')
            return redirect(url_for('main.categories_list'))
        name = category.name
        db.session.delete(category)
        db.session.commit()
        flash(f'Categoría «{name}» eliminada.', 'warning')
        return redirect(url_for('main.categories_list'))
    return render_template('categories/confirm_delete.html', category=category)
