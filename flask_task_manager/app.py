from flask import Flask, render_template, redirect, url_for, request, flash, session, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required

# Configuración de la aplicación
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Modelos de datos
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    tasks = db.relationship('Task', backref='owner', lazy=True)
    categories = db.relationship('Category', backref='owner', lazy=True)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tasks = db.relationship('Task', backref='category', lazy=True)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    position = db.Column(db.Integer, nullable=False)

# Asegurarse de que las tablas de la base de datos se crean
with app.app_context():
    db.create_all()

# Cargar el usuario logueado
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Ruta de registro de usuarios
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user:
            flash('El nombre de usuario ya existe.')
            return redirect(url_for('register'))
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('dashboard'))
    return render_template('register.html', show_nav=False)

# Ruta de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Nombre de usuario o contraseña incorrectos.')
    return render_template('login.html', show_nav=False)

# Ruta de logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Ruta del dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', show_nav=True)

# Crear tarea
@app.route('/task/create', methods=['POST'])
@login_required
def create_task():
    title = request.form.get('title')
    category_id = request.form.get('category_id')
    position = len(current_user.tasks) + 1
    new_task = Task(title=title, owner=current_user, category_id=category_id, position=position)
    db.session.add(new_task)
    db.session.commit()
    return redirect(url_for('dashboard'))

# Editar tarea
@app.route('/task/edit/<int:task_id>', methods=['POST'])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.owner != current_user:
        abort(403)
    task.title = request.form.get('title')
    db.session.commit()
    return redirect(url_for('dashboard'))

# Eliminar tarea
@app.route('/task/delete/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.owner != current_user:
        abort(403)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('dashboard'))

# Marcar tarea como completada
@app.route('/task/complete/<int:task_id>', methods=['POST'])
@login_required
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.owner != current_user:
        abort(403)
    task.is_completed = True
    db.session.commit()
    return redirect(url_for('dashboard'))

# Crear categoría
@app.route('/category/create', methods=['POST'])
@login_required
def create_category():
    name = request.form.get('name')
    new_category = Category(name=name, owner=current_user)
    db.session.add(new_category)
    db.session.commit()
    return redirect(url_for('dashboard'))

# Editar categoría
@app.route('/category/edit/<int:category_id>', methods=['POST'])
@login_required
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)
    if category.owner != current_user:
        abort(403)
    category.name = request.form.get('name')
    db.session.commit()
    return redirect(url_for('dashboard'))

# Eliminar categoría
@app.route('/category/delete/<int:category_id>', methods=['POST'])
@login_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    if category.owner != current_user:
        abort(403)
    db.session.delete(category)
    db.session.commit()
    return redirect(url_for('dashboard'))

# Ver tareas dentro de una categoría
@app.route('/category/<int:category_id>')
@login_required
def view_category(category_id):
    category = Category.query.get_or_404(category_id)
    if category.owner != current_user:
        abort(403)
    tasks = Task.query.filter_by(owner=current_user, category_id=category_id).order_by(Task.position).all()
    return render_template('category.html', category=category, tasks=tasks)

# Cambiar la categoría de una tarea
@app.route('/task/change_category/<int:task_id>', methods=['POST'])
@login_required
def change_task_category(task_id):
    task = Task.query.get_or_404(task_id)
    if task.owner != current_user:
        abort(403)
    new_category_id = request.form.get('new_category_id')
    task.category_id = new_category_id if new_category_id != "" else None
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/category/<int:category_id>/tasks')
@login_required
def view_category_tasks(category_id):
    # Obtener la categoría especificada
    category = Category.query.get_or_404(category_id)
    
    # Verificar si la categoría pertenece al usuario actual
    if category.owner != current_user:
        abort(403)
    
    # Obtener las tareas asociadas a la categoría
    tasks = Task.query.filter_by(category_id=category.id).all()
    
    # Renderizar la plantilla con las tareas
    return render_template('view_category_tasks.html', category=category, tasks=tasks)

# Ejecutar la aplicación
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
