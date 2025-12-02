from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import db, User
from app.forms import LoginForm, RegistrationForm

auth_bp = Blueprint('auth', __name__)

login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.index'))
        flash('Login inválido. Verifique seu email e senha', 'danger')
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            email=form.email.data,
            role='user'  # Ou 'admin' se for um cadastro especial
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Conta criada com sucesso! Você já pode fazer login', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

# ========== GERENCIAMENTO DE USUÁRIOS (ADMIN) ==========
@auth_bp.route('/users')
@login_required
def list_users():
    if current_user.role != 'admin':  # Verifica se é admin
        abort(403)
    
    users = User.query.order_by(User.email).all()
    return render_template('auth/users.html', users=users)

# Adicione esta função para verificar se o usuário é admin
@auth_bp.before_request
def check_admin():
    if request.endpoint in ['auth.list_users'] and current_user.is_authenticated:
        if current_user.role != 'admin':
            abort(403)