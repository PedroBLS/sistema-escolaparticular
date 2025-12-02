from flask import Flask
from flask import Flask, render_template, send_from_directory, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
import os
from datetime import timedelta
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Inicializa as extensões
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()

# Adicionar a função user_loader
@login_manager.user_loader
def load_user(user_id):
    # Importação local para evitar circularidade no topo do arquivo
    from app.models import User
    return User.query.get(int(user_id))


def create_app():
    """Factory function que cria e configura a aplicação Flask"""
    app = Flask(__name__)

    # Configurações básicas
    app.config.from_object('config.Config')
    
    # Configurações de segurança
    app.config.update(
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )
    
    # Inicializa as extensões com o app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # Configurações do LoginManager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'warning'
    
    # Registrar blueprints
    register_blueprints(app)
    
    # Registrar filtros de template
    register_template_filters(app)
    
    # Registrar manipuladores de erro
    register_error_handlers(app)
    
    # Registrar context processors
    register_context_processors(app)
    
    # Registrar shell context
    register_shell_context(app)

    # Registrar as rotas de contratos (importação local para evitar circularidade)
    from app.routes_contratos import register_contratos_routes
    register_contratos_routes(app)
    
    # Rota para favicon
    @app.route('/favicon.ico')
    def favicon():
        try:
            return send_from_directory(
                os.path.join(app.root_path, 'static'),
                'favicon.ico',
                mimetype='image/vnd.microsoft.icon'
            )
        except FileNotFoundError:
            return '', 404
    
    return app

def register_blueprints(app):
    """Registra todos os blueprints da aplicação"""
    from app.routes import main_bp, alunos_bp, professores_bp, agenda_bp, api_bp
    from app.auth import auth_bp

    # Registrar todos os blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(alunos_bp)
    app.register_blueprint(professores_bp)
    app.register_blueprint(agenda_bp)
    app.register_blueprint(api_bp)

def register_template_filters(app):
    """Registra filtros personalizados para templates Jinja2"""
    
    @app.template_filter('format_cpf')
    def format_cpf(cpf):
        """Formata CPF no padrão 000.000.000-00"""
        if cpf and len(cpf) == 11 and cpf.isdigit():
            return f'{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}'
        return cpf

    @app.template_filter('format_telefone')
    def format_telefone(telefone):
        """Formata telefone no padrão (00) 00000-0000 ou (00) 0000-0000"""
        if telefone and telefone.isdigit():
            if len(telefone) == 11:  # Com DDD e 9º dígito
                return f'({telefone[:2]}) {telefone[2:7]}-{telefone[7:]}'
            elif len(telefone) == 10:  # Com DDD sem 9º dígito
                return f'({telefone[:2]}) {telefone[2:6]}-{telefone[6:]}'
        return telefone

    @app.template_filter('format_rg')
    def format_rg(rg):
        """Formata RG no padrão 00.000.000-0"""
        if rg and len(rg) >= 9 and rg.isdigit():
            return f'{rg[:2]}.{rg[2:5]}.{rg[5:8]}-{rg[8:]}'
        return rg

def register_error_handlers(app):
    """Registra manipuladores de erro"""
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(404)
    def page_not_found(error):
        try:
            return render_template('errors/404.html', user=current_user), 404
        except:
            return "<h1>Página não encontrada</h1><p>A página que você procura não existe.</p>", 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app = current_app._get_current_object()  # Acessa a instância atual do app
        app.logger.error(f"Erro 500: {str(error)}", exc_info=True)
        try:
            return render_template('errors/500.html', user=current_user), 500
        except:
            return "<h1>Erro no servidor</h1><p>Ocorreu um erro interno.</p>", 500

def register_context_processors(app):
    """Registra context processors"""
    
    @app.context_processor
    def inject_user():
        return dict(current_user=current_user)

def register_shell_context(app):
    """Registra contexto para o shell interativo"""
    
    @app.shell_context_processor
    def make_shell_context():
        from app.models import User, Aluno, Professor, Aula
        return {
            'db': db,
            'User': User,
            'Aluno': Aluno,
            'Professor': Professor,
            'Aula': Aula
        }