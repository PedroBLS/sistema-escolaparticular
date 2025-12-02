import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Configurações de Segurança Essenciais
    SECRET_KEY = os.environ.get('SECRET_KEY') or '@ImpetusSistema96'  # Melhor usar variável de ambiente
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.environ.get('CSRF_SECRET_KEY') or 'CSRFImpetus96'
    
    # Configuração do Banco de Dados
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'gestao_educacional.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configurações de Sessão Segura
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    SESSION_COOKIE_SECURE = True  # Envia cookie apenas sobre HTTPS
    SESSION_COOKIE_HTTPONLY = True  # Previne acesso via JavaScript
    SESSION_COOKIE_SAMESITE = 'Lax'  # Proteção contra CSRF
    
    # Configurações Adicionais Recomendadas
    DEBUG = False  # Sempre False em produção
    TESTING = False

# Criar diretório para contratos
CONTRATOS_DIR = os.path.join('static', 'contratos')
os.makedirs(CONTRATOS_DIR, exist_ok=True)