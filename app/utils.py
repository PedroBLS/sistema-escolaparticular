import os
from datetime import datetime
from werkzeug.security import generate_password_hash
from itsdangerous import URLSafeTimedSerializer
from flask import current_app, url_for, render_template
from werkzeug.utils import secure_filename

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validar_cpf(cpf):
    """Validação simples de CPF (implementação básica)"""
    # Implemente a validação real do CPF aqui
    return len(cpf) == 11 and cpf.isdigit()

def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=current_app.config['SECURITY_PASSWORD_SALT'])

def enviar_email_confirmacao(email, confirm_url):
    """Função simulada de envio de email"""
    # Implementação real dependerá do seu serviço de email
    print(f"Email de confirmação enviado para {email}. Link: {confirm_url}")
    # Exemplo com Flask-Mail:
    # msg = Message('Confirme seu Email',
    #               sender='no-reply@seusite.com',
    #               recipients=[email])
    # msg.body = render_template('email/confirmacao.txt', confirm_url=confirm_url)
    # mail.send(msg)

def verificar_conflitos_horario(professor_id, aluno_id, data_inicio, data_fim):
    """Verifica conflitos de horário para agendamento"""
    from app.models import Aula, db
    
    query = Aula.query.filter(
        Aula.data_hora < data_fim,
        Aula.data_hora + db.cast(Aula.duracao * 60, db.Interval) > data_inicio
    )
    
    if professor_id:
        query = query.filter(Aula.professor_id == professor_id)
    if aluno_id:
        query = query.filter(Aula.aluno_id == aluno_id)
    
    return query.all()