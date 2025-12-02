from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, abort, jsonify, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from io import BytesIO
import os
from sqlalchemy import func, extract, and_, or_, distinct
import calendar
from weasyprint import HTML
from pytz import timezone
from functools import wraps
import tempfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from functools import wraps

from app.models import db, User, Aluno, Professor, Aula, Contrato, Notificacao, Documento, Responsavel
from app.forms import (
    ProfessorForm,
    RegistrationForm,
    AlunoForm, 
    AulaForm,
    LoginForm,
    ContratoForm,
    PerfilForm,
    ResponsavelForm
)
from app.utils import (
    allowed_file, validar_cpf, enviar_email_confirmacao,
    generate_confirmation_token, verificar_conflitos_horario
)

# Configuração de Blueprints
main_bp = Blueprint('main', __name__)
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
alunos_bp = Blueprint('alunos', __name__, url_prefix='/alunos')
professores_bp = Blueprint('professores', __name__, url_prefix='/professores')
agenda_bp = Blueprint('agenda', __name__, url_prefix='/agenda')
api_bp = Blueprint('api', __name__, url_prefix='/api')

# ========== FUNÇÕES AUXILIARES ==========
def criar_notificacao(usuario_id, titulo, mensagem, tipo='info'):
    """Cria uma nova notificação no sistema"""
    notificacao = Notificacao(
        usuario_id=usuario_id,
        titulo=titulo,
        mensagem=mensagem,
        tipo=tipo,
        lida=False,
        data_criacao=datetime.utcnow()
    )
    db.session.add(notificacao)
    db.session.commit()
    return notificacao

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'pdf', 'doc', 'docx', 'jpg', 'png'}

def admin_required(func):
    """Decorator para verificar se o usuário é admin"""
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        return func(*args, **kwargs)
    return decorated_view

# ========== ROTAS PÚBLICAS ==========
@main_bp.route('/')
def index():
    """Rota principal do sistema"""
    return render_template('index.html')

# ========== ROTAS DE AUTENTICAÇÃO ==========
@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Registro de novos usuários
    Permite cadastro de alunos e professores
    """
    form = RegistrationForm()
    
    if form.validate_on_submit():
        try:
            # Verifica se email ou CPF já existem
            if User.query.filter_by(email=form.email.data).first():
                flash('Este e-mail já está cadastrado', 'error')
                return redirect(url_for('auth.register'))
            
            # Validação de CPF baseada no tipo de usuário
            if form.user_type.data == 'aluno':
                cpf = form.aluno_cpf.data
                nome = form.aluno_nome.data
            elif form.user_type.data == 'professor':
                cpf = form.professor_cpf.data
                nome = form.professor_nome.data
            elif form.user_type.data == 'responsavel':
                cpf = form.responsavel_cpf.data
                nome = form.responsavel_nome.data
            
            if not validar_cpf(cpf):
                flash('CPF inválido', 'error')
                return redirect(url_for('main.register'))
            
            # Cria User
            user = User(
                email=form.email.data,
                nome=form.nome.data,
                role=form.user_type.data
            )
            user.set_password(form.password.data)
            db.session.add(user)

             # Cria entidade específica baseada no tipo
            if form.user_type.data == 'aluno':
                aluno = Aluno(
                    nome=form.aluno_nome.data,
                    cpf=cpf,
                    rg=form.aluno_rg.data,
                    telefone=form.aluno_telefone.data,
                    endereco=form.aluno_endereco.data,
                    serie=form.aluno_serie.data,
                    mora_plano_piloto=form.aluno_mora_plano_piloto.data,
                    estado_civil=form.aluno_estado_civil.data,
                    nacionalidade=form.aluno_nacionalidade.data,
                    plano_adquirido=form.aluno_plano_adquirido.data
                )
                db.session.add(aluno)
                db.session.flush()
                user.aluno_id = aluno.id
                
            elif form.user_type.data == 'professor':
                professor = Professor(
                    nome=form.professor_nome.data,
                    cpf=cpf,
                    rg=form.professor_rg.data,
                    disciplina=form.professor_disciplina.data,
                    telefone=form.professor_telefone.data,
                    endereco=form.professor_endereco.data,
                    nacionalidade=form.professor_nacionalidade.data,
                    estado_civil=form.professor_estado_civil.data,
                    banco=form.professor_banco.data,
                    agencia=form.professor_agencia.data,
                    conta=form.professor_conta.data,
                    pix=form.professor_pix.data,
                    disponibilidade=form.professor_disponibilidade.data,
                    valor_hora=form.professor_valor_hora.data,
                    tipo_atendimento=form.professor_tipo_atendimento.data
                )
                db.session.add(professor)
                db.session.flush()
                user.professor_id = professor.id
                
            elif form.user_type.data == 'responsavel':
                responsavel = Responsavel(
                    nome=form.responsavel_nome.data,
                    cpf=cpf,
                    rg=form.responsavel_rg.data,
                    telefone=form.responsavel_telefone.data,
                    email=form.email.data,
                    endereco=form.responsavel_endereco.data,
                    estado_civil=form.responsavel_estado_civil.data,
                    nacionalidade=form.responsavel_nacionalidade.data
                )
                db.session.add(responsavel)
                db.session.flush()
                user.responsavel_id = responsavel.id

            db.session.commit()

            # Envia e-mail de confirmação
            token = generate_confirmation_token(user.email)
            confirm_url = url_for('auth.confirm_email', token=token, _external=True)
            enviar_email_confirmacao(user.email, confirm_url)
            
            flash('Cadastro realizado com sucesso! Por favor, verifique seu e-mail para confirmar.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Erro no registro: {str(e)}', exc_info=True)
            flash(f'Erro no cadastro: {str(e)}', 'danger')

    return render_template('auth/register.html', form=form)

# ========== DASHBOARDS ==========
@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Redireciona para o dashboard apropriado baseado no tipo de usuário"""
    if current_user.role == 'aluno':
        return redirect(url_for('main.aluno_dashboard'))
    elif current_user.role == 'professor':
        return redirect(url_for('main.professor_dashboard'))
    elif current_user.role == 'responsavel':
        return redirect(url_for('main.responsavel_dashboard'))
    elif current_user.role == 'admin':
        return redirect(url_for('main.admin_dashboard'))
    abort(403)

@main_bp.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    """Dashboard administrativo com estatísticas do sistema"""
    total_alunos = Aluno.query.count()
    total_professores = Professor.query.count()
    total_responsaveis = Responsavel.query.count()
    total_contratos = Contrato.query.count()
    contratos_ativos = Contrato.query.filter(Contrato.validade >= date.today()).count()

    aulas_hoje = Aula.query.filter(
        func.date(Aula.data_hora) == datetime.today().date()
    ).count()

# Contratos vencendo nos próximos 30 dias
    data_limite = date.today() + timedelta(days=30)
    contratos_vencendo = Contrato.query.filter(
        and_(Contrato.validade <= data_limite, Contrato.validade >= date.today())
    ).count()

    return render_template('admin/dashboard.html',
                         total_alunos=total_alunos,
                         total_professores=total_professores,
                         total_responsaveis=total_responsaveis,
                         total_contratos=total_contratos,
                         contratos_ativos=contratos_ativos,
                         contratos_vencendo=contratos_vencendo,
                         aulas_hoje=aulas_hoje)

@main_bp.route('/aluno/dashboard')
@login_required
def aluno_dashboard():
    """Dashboard do aluno com próximas aulas e informações"""
    if current_user.role != 'aluno' or not current_user.aluno:
        abort(403)

    aluno = current_user.aluno
    proximas_aulas = Aula.query.filter(
        Aula.aluno_id == aluno.id,
        Aula.data_hora >= datetime.now()
    ).order_by(Aula.data_hora).limit(5).all()
    
    # Busca notificações não lidas
    notificacoes = Notificacao.query.filter_by(
        usuario_id=current_user.id,
        lida=False
    ).order_by(Notificacao.data_criacao.desc()).limit(5).all()

    # Busca contratos do aluno
    contratos = Contrato.query.join(Contrato.alunos).filter(Aluno.id == aluno.id).all()


    return render_template('aluno/dashboard.html',
                         aluno=aluno,
                         proximas_aulas=proximas_aulas,
                         notificacoes=notificacoes,
                         contratos=contratos)

@main_bp.route('/professor/dashboard')
@login_required
def professor_dashboard():
    """Dashboard do professor com próximas aulas e informações"""
    if current_user.role != 'professor' or not current_user.professor:
        abort(403)

    professor = current_user.professor
    proximas_aulas = Aula.query.filter(
        Aula.professor_id == professor.id,
        Aula.data_hora >= datetime.now()
    ).order_by(Aula.data_hora).limit(5).all()

    # Busca notificações não lidas
    notificacoes = Notificacao.query.filter_by(
        usuario_id=current_user.id,
        lida=False
    ).order_by(Notificacao.data_criacao.desc()).limit(5).all()

    return render_template('professor/dashboard.html',
                         professor=professor,
                         proximas_aulas=proximas_aulas,
                         notificacoes=notificacoes)

@main_bp.route('/responsavel/dashboard')
@login_required
def responsavel_dashboard():
    """Dashboard do responsável com informações dos filhos e contratos"""
    if current_user.role != 'responsavel' or not current_user.responsavel:
        abort(403)

    responsavel = current_user.responsavel
    alunos = responsavel.alunos
    contratos = responsavel.contratos
    
    # Próximas aulas de todos os filhos
    proximas_aulas = []
    for aluno in alunos:
        aulas_aluno = Aula.query.filter(
            Aula.aluno_id == aluno.id,
            Aula.data_hora >= datetime.now()
        ).order_by(Aula.data_hora).limit(3).all()
        proximas_aulas.extend(aulas_aluno)
    
    # Ordenar por data
    proximas_aulas.sort(key=lambda x: x.data_hora)
    proximas_aulas = proximas_aulas[:10]  # Limitar a 10 aulas
    
    # Contratos próximos ao vencimento
    data_limite = date.today() + timedelta(days=30)
    contratos_vencendo = [c for c in contratos if c.validade <= data_limite and c.validade >= date.today()]

    return render_template('responsavel/dashboard.html',
                         responsavel=responsavel,
                         alunos=alunos,
                         contratos=contratos,
                         contratos_vencendo=contratos_vencendo,
                         proximas_aulas=proximas_aulas)

# ========== ROTAS PARA RESPONSÁVEIS ==========
@main_bp.route('/responsaveis')
@login_required
def lista_responsaveis():
    """Lista todos os responsáveis cadastrados"""
    if current_user.role not in ['admin']:
        abort(403)
        
    responsaveis = Responsavel.query.all()
    return render_template('responsaveis/lista.html', responsaveis=responsaveis)

@main_bp.route('/responsavel/cadastro', methods=['GET', 'POST'])
@login_required
def cadastro_responsavel():
    """Cadastra um novo responsável"""
    if current_user.role not in ['admin']:
        abort(403)
        
    form = ResponsavelForm()
    
    if form.validate_on_submit():
        try:
            # Criar o usuário para login
            user = User(
                nome=form.nome.data,
                email=form.email.data,
                role='responsavel'
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.flush()  # Para obter o ID do user
            
            # Criar o responsável
            responsavel = Responsavel(
                nome=form.nome.data,
                cpf=form.cpf.data,
                rg=form.rg.data,
                telefone=form.telefone.data,
                email=form.email.data,
                endereco=form.endereco.data,
                estado_civil=form.estado_civil.data,
                nacionalidade=form.nacionalidade.data
            )
            db.session.add(responsavel)
            db.session.flush()  # Para obter o ID do responsável
            
            # Associar user ao responsável
            user.responsavel_id = responsavel.id
            
            db.session.commit()
            flash('Responsável cadastrado com sucesso!', 'success')
            return redirect(url_for('main.lista_responsaveis'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar responsável: {str(e)}', 'error')
    
    return render_template('responsaveis/cadastro.html', form=form)

@main_bp.route('/responsavel/<int:id>')
@login_required
def visualizar_responsavel(id):
    """Visualiza detalhes de um responsável"""
    responsavel = Responsavel.query.get_or_404(id)
    
    # Verificação de permissão
    if current_user.role == 'responsavel' and current_user.responsavel.id != id:
        abort(403)
    elif current_user.role not in ['admin', 'responsavel']:
        abort(403)
        
    alunos = responsavel.alunos
    contratos = responsavel.contratos
    return render_template('responsaveis/visualizar.html', 
                         responsavel=responsavel, alunos=alunos, contratos=contratos)

@main_bp.route('/responsavel/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_responsavel(id):
    """Edita um responsável"""
    responsavel = Responsavel.query.get_or_404(id)
    
    # Verificação de permissão
    if current_user.role == 'responsavel' and current_user.responsavel.id != id:
        abort(403)
    elif current_user.role not in ['admin', 'responsavel']:
        abort(403)
        
    form = ResponsavelForm(obj=responsavel)
    
    if form.validate_on_submit():
        try:
            responsavel.nome = form.nome.data
            responsavel.cpf = form.cpf.data
            responsavel.rg = form.rg.data
            responsavel.telefone = form.telefone.data
            responsavel.email = form.email.data
            responsavel.endereco = form.endereco.data
            responsavel.estado_civil = form.estado_civil.data
            responsavel.nacionalidade = form.nacionalidade.data
            
            # Atualizar também o user associado
            if responsavel.user:
                responsavel.user.nome = form.nome.data
                responsavel.user.email = form.email.data
            
            db.session.commit()
            flash('Responsável atualizado com sucesso!', 'success')
            return redirect(url_for('main.visualizar_responsavel', id=id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar responsável: {str(e)}', 'error')
    
    return render_template('responsaveis/editar.html', form=form, responsavel=responsavel)

    # ========== ROTAS PARA CONTRATOS ==========
@main_bp.route('/contratos')
@login_required
def lista_contratos():
    """Lista todos os contratos"""
    if current_user.role == 'responsavel':
        contratos = current_user.responsavel.contratos
    elif current_user.role == 'aluno':
        contratos = Contrato.query.join(Contrato.alunos).filter(Aluno.id == current_user.aluno.id).all()
    else:
        contratos = Contrato.query.all()
    
    # Verificar contratos próximos ao vencimento (30 dias)
    data_limite = date.today() + timedelta(days=30)
    contratos_vencendo = [c for c in contratos if c.validade <= data_limite and c.validade >= date.today()]
    
    return render_template('contratos/lista.html', 
                         contratos=contratos, contratos_vencendo=contratos_vencendo)

@main_bp.route('/contrato/novo', methods=['GET', 'POST'])
@login_required
def novo_contrato():
    """Cria um novo contrato"""
    if current_user.role not in ['admin']:
        abort(403)
        
    form = ContratoForm()
    
    if form.validate_on_submit():
        try:
            # Criar o contrato
            contrato = Contrato(
                responsavel_id=form.responsavel_id.data,
                professor_id=form.professor_id.data if form.professor_id.data != 0 else None,
                validade=form.validade.data,
                tipo_plano=form.tipo_plano.data,
                data_inicio=form.data_inicio.data,
                valor_total=form.valor_total.data,
                servicos_incluidos=form.servicos_incluidos.data,
                observacoes=form.observacoes.data,
                assinatura=form.assinatura.data,
                arquivo='contrato_gerado.pdf'  # Será gerado automaticamente
            )
            
            db.session.add(contrato)
            db.session.flush()  # Para obter o ID do contrato
            
            # Associar alunos ao contrato
            alunos_selecionados = Aluno.query.filter(Aluno.id.in_(form.alunos_ids.data)).all()
            contrato.alunos = alunos_selecionados
            
            db.session.commit()
            
            # Gerar o contrato automaticamente preenchido
            arquivo_contrato = gerar_contrato_automatico(contrato.id)
            contrato.arquivo = arquivo_contrato
            db.session.commit()
            
            flash('Contrato criado com sucesso!', 'success')
            return redirect(url_for('main.visualizar_contrato', id=contrato.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar contrato: {str(e)}', 'error')
    
    return render_template('contratos/novo.html', form=form)

@main_bp.route('/contrato/<int:id>')
@login_required
def visualizar_contrato(id):
    """Visualiza detalhes de um contrato"""
    contrato = Contrato.query.get_or_404(id)
    
    # Verificação de permissão
    if current_user.role == 'responsavel' and contrato.responsavel_id != current_user.responsavel.id:
        abort(403)
    elif current_user.role == 'aluno' and current_user.aluno not in contrato.alunos:
        abort(403)
    elif current_user.role not in ['admin', 'responsavel', 'aluno']:
        abort(403)
        
    return render_template('contratos/visualizar.html', contrato=contrato)

@main_bp.route('/contrato/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_contrato(id):
    """Edita um contrato"""
    if current_user.role not in ['admin']:
        abort(403)
        
    contrato = Contrato.query.get_or_404(id)
    form = ContratoForm(obj=contrato)
    
    # Pré-selecionar alunos associados
    form.alunos_ids.data = [aluno.id for aluno in contrato.alunos]
    
    if form.validate_on_submit():
        try:
            contrato.responsavel_id = form.responsavel_id.data
            contrato.professor_id = form.professor_id.data if form.professor_id.data != 0 else None
            contrato.validade = form.validade.data
            contrato.tipo_plano = form.tipo_plano.data
            contrato.data_inicio = form.data_inicio.data
            contrato.valor_total = form.valor_total.data
            contrato.servicos_incluidos = form.servicos_incluidos.data
            contrato.observacoes = form.observacoes.data
            contrato.assinatura = form.assinatura.data
            
            # Atualizar alunos associados
            alunos_selecionados = Aluno.query.filter(Aluno.id.in_(form.alunos_ids.data)).all()
            contrato.alunos = alunos_selecionados
            
            db.session.commit()
            flash('Contrato atualizado com sucesso!', 'success')
            return redirect(url_for('main.visualizar_contrato', id=id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar contrato: {str(e)}', 'error')
    
    return render_template('contratos/editar.html', form=form, contrato=contrato)

@main_bp.route('/contrato/<int:id>/download')
@login_required
def download_contrato(id):
    """Faz download do arquivo do contrato"""
    contrato = Contrato.query.get_or_404(id)
    
    # Verificação de permissão
    if current_user.role == 'responsavel' and contrato.responsavel_id != current_user.responsavel.id:
        abort(403)
    elif current_user.role == 'aluno' and current_user.aluno not in contrato.alunos:
        abort(403)
    elif current_user.role not in ['admin', 'responsavel', 'aluno']:
        abort(403)
    
    if not contrato.arquivo or not os.path.exists(contrato.arquivo):
        # Gerar o contrato se não existir
        arquivo_contrato = gerar_contrato_automatico(id)
        contrato.arquivo = arquivo_contrato
        db.session.commit()
    
    return send_file(contrato.arquivo, as_attachment=True, 
                    download_name=f'contrato_{contrato.id}.pdf')

# ========== FUNÇÃO PARA GERAR CONTRATO AUTOMATICAMENTE ==========
def gerar_contrato_automatico(contrato_id):
    """Gera um contrato PDF automaticamente preenchido"""
    contrato = Contrato.query.get_or_404(contrato_id)
    responsavel = contrato.responsavel
    alunos = contrato.alunos
    
    # Criar arquivo temporário
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    temp_path = temp_file.name
    temp_file.close()
    
    # Criar o PDF
    doc = SimpleDocTemplate(temp_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Título
    title = Paragraph(f"<b>CONTRATO DE PRESTAÇÃO DE SERVIÇOS EDUCACIONAIS</b>", 
                     styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))
    
    # Dados do contratado (empresa)
    contratado_text = f"""
    <b>CONTRATADO:</b> IMPETUS INSTITUTO DE EDUCAÇÃO<br/>
    CNPJ: [36.207.755/0001-09]<br/>
    Endereço: [CLN 104 Bloco D Sala 121]<br/>
    Telefone: [(61)994302031]<br/>
    Email: [impetusinstituto@gmail.com]
    """
    story.append(Paragraph(contratado_text, styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Dados do contratante (responsável)
    contratante_text = f"""
    <b>CONTRATANTE:</b> {responsavel.nome}<br/>
    Estado Civil: {responsavel.estado_civil}<br/>
    RG: {responsavel.rg}<br/>
    CPF: {responsavel.cpf}<br/>
    Email: {responsavel.email}<br/>
    Telefone: {responsavel.telefone}<br/>
    Endereço: {responsavel.endereco}<br/>
    Nacionalidade: {responsavel.nacionalidade}
    """
    story.append(Paragraph(contratante_text, styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Dados dos alunos
    if len(alunos) == 1:
        alunos_text = f"<b>ALUNO:</b> {alunos[0].nome}"
    else:
        nomes_alunos = ", ".join([aluno.nome for aluno in alunos])
        alunos_text = f"<b>ALUNOS:</b> {nomes_alunos}"
    
    story.append(Paragraph(alunos_text, styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Dados do contrato
    contrato_text = f"""
    <b>DADOS DO CONTRATO:</b><br/>
    Tipo de Plano: {contrato.tipo_plano}<br/>
    Data de Início: {contrato.data_inicio.strftime('%d/%m/%Y')}<br/>
    Validade: {contrato.validade.strftime('%d/%m/%Y')}<br/>
    Valor Total: R$ {contrato.valor_total:.2f}<br/>
    Serviços Incluídos: {contrato.servicos_incluidos or 'Não especificado'}
    """
    story.append(Paragraph(contrato_text, styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Cláusulas do contrato baseadas no tipo de plano
    clausulas = obter_clausulas_contrato(contrato.tipo_plano)
    for clausula in clausulas:
        story.append(Paragraph(clausula, styles['Normal']))
        story.append(Spacer(1, 6))
    
    # Assinaturas
    story.append(Spacer(1, 24))
    assinaturas_text = f"""
    Data: {date.today().strftime('%d/%m/%Y')}<br/><br/>
    
    _________________________________<br/>
    IMPETUS INSTITUTO DE EDUCAÇÃO<br/>
    CONTRATADO<br/><br/>
    
    _________________________________<br/>
    {responsavel.nome}<br/>
    CONTRATANTE
    """
    story.append(Paragraph(assinaturas_text, styles['Normal']))
    
    # Gerar o PDF
    doc.build(story)
    
    # Mover para o diretório de contratos
    contratos_dir = os.path.join(current_app.root_path, 'static', 'contratos')
    os.makedirs(contratos_dir, exist_ok=True)
    
    final_path = os.path.join(contratos_dir, f'contrato_{contrato_id}.pdf')
    os.rename(temp_path, final_path)
    
    return final_path

def obter_clausulas_contrato(tipo_plano):
    """Retorna as cláusulas específicas para cada tipo de plano"""
    clausulas_base = [
        "<b>CLÁUSULA 1ª - DO OBJETO:</b> O presente contrato tem por objeto a prestação de serviços educacionais.",
        "<b>CLÁUSULA 2ª - DAS OBRIGAÇÕES DO CONTRATADO:</b> Prestar os serviços educacionais com qualidade e pontualidade.",
        "<b>CLÁUSULA 3ª - DAS OBRIGAÇÕES DO CONTRATANTE:</b> Efetuar o pagamento nas datas acordadas.",
    ]
    
    if tipo_plano == 'aula_particular_grupo':
        clausulas_base.append("<b>CLÁUSULA 4ª - MODALIDADE:</b> Aulas particulares em grupo.")
    elif '10_aulas' in tipo_plano:
        clausulas_base.append("<b>CLÁUSULA 4ª - MODALIDADE:</b> Pacote de 10 aulas particulares.")
    elif '20_aulas' in tipo_plano:
        clausulas_base.append("<b>CLÁUSULA 4ª - MODALIDADE:</b> Pacote de 20 aulas particulares.")
    elif '30_aulas' in tipo_plano:
        clausulas_base.append("<b>CLÁUSULA 4ª - MODALIDADE:</b> Pacote de 30 aulas particulares.")
    
    return clausulas_base

# ========== ROTAS PARA ALUNOS ==========
@alunos_bp.route('/', methods=['GET'])
@login_required
def listar_alunos():
    """
    Lista todos os alunos cadastrados
    Permissões: Admin ou Professor
    """
    if current_user.role not in ['admin', 'professor']:
        abort(403)

    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('q', '').strip()
        sort = request.args.get('sort', 'nome')
        order = request.args.get('order', 'asc')

        query = Aluno.query

        if search:
            query = query.filter(
                or_(
                    Aluno.nome.ilike(f'%{search}%'),
                    Aluno.cpf.ilike(f'%{search}%'),
                    Aluno.telefone.ilike(f'%{search}%')
                )
            )

        # Ordenação
        if sort == 'nome':
            query = query.order_by(Aluno.nome.asc() if order == 'asc' else Aluno.nome.desc())
        elif sort == 'data_cadastro':
            query = query.order_by(Aluno.data_cadastro.asc() if order == 'asc' else Aluno.data_cadastro.desc())

        alunos = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return render_template('alunos/lista.html', 
                            alunos=alunos,
                            search_query=search,
                            sort=sort,
                            order=order)
    
    except Exception as e:
        current_app.logger.error(f"Erro ao listar alunos: {str(e)}", exc_info=True)
        flash('Ocorreu um erro ao carregar a lista de alunos', 'danger')
        return redirect(url_for('main.dashboard'))
    
@alunos_bp.route('/alunos/cadastrar', methods=['GET', 'POST'])
@login_required
def cadastro_aluno():
    """Cadastra um novo aluno (atualizado para incluir responsável)"""
    if current_user.role not in ['admin']:
        abort(403)
        
    form = AlunoForm()
    
    if form.validate_on_submit():
        try:
            # Criar o usuário para login
            user = User(
                nome=form.nome.data,
                email=form.email.data,
                role='aluno'
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.flush()
            
            # Criar o aluno
            aluno = Aluno(
                nome=form.nome.data,
                cpf=form.cpf.data,
                rg=form.rg.data,
                telefone=form.telefone.data,
                endereco=form.endereco.data,
                serie=form.serie.data,
                mora_plano_piloto=form.mora_plano_piloto.data,
                estado_civil=form.estado_civil.data,
                nacionalidade=form.nacionalidade.data,
                plano_adquirido=form.plano_adquirido.data,
                responsavel_id=form.responsavel_id.data if form.responsavel_id.data != 0 else None
            )
            db.session.add(aluno)
            db.session.flush()

           # Associar user ao aluno
            user.aluno_id = aluno.id
            
            db.session.commit()
            
            # Se um plano foi selecionado, sugerir criação de contrato
            if form.plano_adquirido.data and form.responsavel_id.data != 0:
                flash(f'Aluno cadastrado com sucesso! Deseja criar um contrato para o plano {form.plano_adquirido.data}?', 'success')
                return redirect(url_for('main.sugerir_contrato', aluno_id=aluno.id))
            else:
                flash('Aluno cadastrado com sucesso!', 'success')
                return redirect(url_for('alunos.listar_alunos'))
                
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar aluno: {str(e)}', 'error')
    
    return render_template('alunos/cadastro.html', form=form)

@main_bp.route('/aluno/<int:aluno_id>/sugerir-contrato')
@login_required
def sugerir_contrato(aluno_id):
    """Sugere a criação de um contrato para um aluno recém-cadastrado"""
    if current_user.role not in ['admin']:
        abort(403)
        
    aluno = Aluno.query.get_or_404(aluno_id)
    
    if not aluno.responsavel:
        flash('Este aluno não possui um responsável associado. Não é possível criar um contrato.', 'warning')
        return redirect(url_for('alunos.listar_alunos'))
    
    # Pré-preencher dados para o contrato
    dados_sugeridos = {
        'responsavel_id': aluno.responsavel.id,
        'aluno_id': aluno.id,
        'tipo_plano': aluno.plano_adquirido,
        'data_inicio': date.today(),
        'validade': date.today() + timedelta(days=365)  # 1 ano por padrão
    }
    
    return render_template('contratos/sugerir.html', aluno=aluno, dados=dados_sugeridos)

@alunos_bp.route('/alunos/<int:id>')
@login_required
def visualizar_aluno(id):
    """Visualiza detalhes de um aluno específico"""
    aluno = Aluno.query.get_or_404(id)
    
    # Verificação de permissão
    if current_user.role == 'aluno' and current_user.aluno.id != id:
        abort(403)
    elif current_user.role == 'professor':
        # Professores só podem ver seus próprios alunos (se implementado)
        pass  # Adicione lógica específica se necessário
    
    documentos = Documento.query.filter_by(aluno_id=id).all()
    aulas = Aula.query.filter_by(aluno_id=id).order_by(Aula.data_hora.desc()).limit(10).all()
    contratos = Contrato.query.join(Contrato.alunos).filter(Aluno.id == id).all()
    
    return render_template('alunos/visualizar.html', 
                        aluno=aluno,
                        documentos=documentos,
                        aulas=aulas,
                        contratos=contratos)


@main_bp.route('/alunos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_aluno(id):
    """Edita informações de um aluno existente"""
    aluno = Aluno.query.get_or_404(id)
    
    # Verificação de permissão
    if current_user.role == 'aluno' and current_user.aluno.id != id:
        abort(403)
    elif current_user.role == 'professor':
        abort(403)  # Professores não podem editar alunos
    
    form = AlunoForm(obj=aluno)
    
    if request.method == 'GET' and aluno.user:
        form.email.data = aluno.user.email
    
    if form.validate_on_submit():
        try:
            aluno.nome = form.nome.data
            aluno.telefone = form.telefone.data
            aluno.endereco = form.endereco.data
            aluno.serie = form.serie.data
            aluno.rg = form.rg.data
            aluno.estado_civil = form.estado_civil.data
            aluno.nacionalidade = form.nacionalidade.data
            aluno.mora_plano_piloto = form.mora_plano_piloto.data
            aluno.plano_adquirido = form.plano_adquirido.data
            aluno.responsavel_id = form.responsavel_id.data if form.responsavel_id.data != 0 else None
            
            if aluno.user:
                aluno.user.nome = form.nome.data
                if form.email.data != aluno.user.email:
                    if User.query.filter(User.email == form.email.data, User.id != aluno.user.id).first():
                        flash('Este e-mail já está em uso por outro usuário', 'error')
                        return redirect(url_for('alunos.editar_aluno', id=id))
                    aluno.user.email = form.email.data
                
                if form.password.data:
                    aluno.user.set_password(form.password.data)
            
            db.session.commit()
            flash('Aluno atualizado com sucesso!', 'success')
            return redirect(url_for('alunos.visualizar_aluno', id=id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar aluno: {str(e)}', 'danger')
    
    return render_template('alunos/editar.html', form=form, aluno=aluno)

# ========== ROTAS PARA RELATÓRIOS ==========
@main_bp.route('/relatorios/contratos')
@login_required
def relatorio_contratos():
    """Gera relatório de contratos"""
    if current_user.role not in ['admin']:
        abort(403)
    
    # Filtros
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    status = request.args.get('status', 'todos')
    
    query = Contrato.query
    
    if data_inicio:
        query = query.filter(Contrato.data_inicio >= datetime.strptime(data_inicio, '%Y-%m-%d').date())
    
    if data_fim:
        query = query.filter(Contrato.data_inicio <= datetime.strptime(data_fim, '%Y-%m-%d').date())
    
    if status == 'ativos':
        query = query.filter(Contrato.validade >= date.today())
    elif status == 'vencidos':
        query = query.filter(Contrato.validade < date.today())
    elif status == 'vencendo':
        data_limite = date.today() + timedelta(days=30)
        query = query.filter(and_(Contrato.validade <= data_limite, Contrato.validade >= date.today()))
    
    contratos = query.order_by(Contrato.data_inicio.desc()).all()
    
    return render_template('relatorios/contratos.html', 
                         contratos=contratos,
                         filtros={
                             'data_inicio': data_inicio,
                             'data_fim': data_fim,
                             'status': status
                         })

@main_bp.route('/alunos/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_aluno(id):
    try:
        aluno = Aluno.query.get_or_404(id)
        user = User.query.filter_by(aluno_id=id).first()
        
        if user:
            db.session.delete(user)
        
        db.session.delete(aluno)
        db.session.commit()
        
        flash('Aluno excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Erro ao excluir aluno: {str(e)}', exc_info=True)
        flash('Erro ao excluir aluno', 'danger')
    
    return redirect(url_for('main.listar_alunos'))

@alunos_bp.route('/<int:id>/upload', methods=['POST'])
@login_required
def upload_documento(id):
    """Faz upload de documento para um aluno"""
    aluno = Aluno.query.get_or_404(id)
    
    # Verificação de permissão
    if current_user.role == 'aluno' and current_user.aluno.id != id:
        abort(403)
    
    if 'documento' not in request.files:
        flash('Nenhum arquivo enviado', 'error')
        return redirect(url_for('alunos.visualizar_aluno', id=id))
    
    file = request.files['documento']
    if file.filename == '':
        flash('Nenhum arquivo selecionado', 'error')
        return redirect(url_for('alunos.visualizar_aluno', id=id))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(f"doc_{aluno.id}_{datetime.now().timestamp()}_{file.filename}")
        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        
        # Salva a referência no banco de dados
        documento = Documento(
            aluno_id=aluno.id,
            nome=file.filename,
            caminho=filepath,
            tipo=file.content_type,
            tamanho=os.path.getsize(filepath),
            upload_por=current_user.id,
            data_upload=datetime.utcnow()
        )
        db.session.add(documento)
        db.session.commit()
        
        flash('Documento enviado com sucesso!', 'success')
    else:
        flash('Tipo de arquivo não permitido', 'error')
    
    return redirect(url_for('alunos.visualizar_aluno', id=id))

# ========== ROTAS PARA PROFESSORES ==========
@main_bp.route('/professores', methods=['GET'])
@login_required
def listar_professores():
    """Lista todos os professores cadastrados"""
    if current_user.role not in ['admin', 'aluno']:
        abort(403)

    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('q', '').strip()
        disciplina = request.args.get('disciplina', '').strip()

        query = Professor.query

        if search:
            query = query.filter(
                or_(
                    Professor.nome.ilike(f'%{search}%'),
                    Professor.cpf.ilike(f'%{search}%'),
                    Professor.disciplina.ilike(f'%{search}%')
                )
            )
        
        if disciplina:
            query = query.filter(Professor.disciplina.ilike(f'%{disciplina}%'))

        professores = query.order_by(Professor.nome).paginate(page=page, per_page=per_page, error_out=False)
        
        disciplinas = db.session.query(
            Professor.disciplina.distinct().label('disciplina')
        ).all()
        
        return render_template('professores/lista.html', 
                            professores=professores,
                            search_query=search,
                            disciplinas=[d.disciplina for d in disciplinas],
                            disciplina_selecionada=disciplina)
    
    except Exception as e:
        current_app.logger.error(f"Erro ao listar professores: {str(e)}", exc_info=True)
        flash('Ocorreu um erro ao carregar a lista de professores', 'danger')
        return redirect(url_for('main.dashboard'))
    
@main_bp.route('/professores/<int:id>')
@login_required
def visualizar_professor(id):
    professor = Professor.query.get_or_404(id)
    return render_template('professores/visualizar.html', professor=professor)

@main_bp.route('/professores/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_professor(id):
    professor = Professor.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            professor.nome = request.form['nome'].strip()
            professor.rg = request.form['rg'].strip()
            professor.cpf = request.form['cpf'].strip()
            professor.endereco = request.form['endereco'].strip()
            professor.telefone = request.form['telefone'].strip()
            professor.disciplina = request.form['disciplina'].strip()
            professor.nacionalidade = request.form.get('nacionalidade', '')
            professor.estado_civil = request.form.get('estado_civil', '')
            professor.banco = request.form.get('banco', '')
            professor.agencia = request.form.get('agencia', '')
            professor.conta = request.form.get('conta', '')
            professor.pix = request.form.get('pix', '')
            professor.disponibilidade = request.form.get('disponibilidade', '')
            professor.valor_hora = float(request.form.get('valor_hora', 0))
            professor.tipo_atendimento = ','.join(request.form.getlist('tipo_atendimento'))
            
            if professor.user:
                professor.user.email = request.form['email'].strip().lower()
                if request.form.get('password'):
                    professor.user.set_password(request.form['password'])
            
            db.session.commit()
            flash('Professor atualizado com sucesso!', 'success')
            return redirect(url_for('main.listar_professores'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar professor: {str(e)}', 'danger')
    
    return render_template('professores/editar.html', professor=professor)

@main_bp.route('/professores/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_professor(id):
    try:
        professor = Professor.query.get_or_404(id)
        user = User.query.filter_by(professor_id=id).first()
        
        if user:
            db.session.delete(user)
        
        db.session.delete(professor)
        db.session.commit()
        
        flash('Professor excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Erro ao excluir professor: {str(e)}', exc_info=True)
        flash('Erro ao excluir professor', 'danger')
    
    return redirect(url_for('main.listar_professores'))

@main_bp.route('/professores/cadastrar', methods=['GET', 'POST'])
@login_required
def cadastrar_professor():
    if request.method == 'POST':
        try:
            # Validação dos campos obrigatórios
            required_fields = {
                'nome': 'Nome completo é obrigatório',
                'email': 'E-mail é obrigatório',
                'password': 'Senha é obrigatória',
                'confirmar_senha': 'Confirmação de senha é obrigatória',
                'rg': 'RG é obrigatório',
                'cpf': 'CPF é obrigatório',
                'disciplina': 'Disciplina é obrigatória',
                'telefone': 'Telefone é obrigatório',
                'endereco': 'Endereço é obrigatório'
            }

            for field, message in required_fields.items():
                if not request.form.get(field):
                    flash(message, 'error')
                    return redirect(url_for('main.cadastrar_professor'))

            # Validação de senha
            if request.form['password'] != request.form['confirmar_senha']:
                flash('As senhas não coincidem', 'error')
                return redirect(url_for('main.cadastrar_professor'))

            if len(request.form['password']) < 8:
                flash('A senha deve ter no mínimo 8 caracteres', 'error')
                return redirect(url_for('main.cadastrar_professor'))

            # Verifica se email ou CPF já existem
            if User.query.filter_by(email=request.form['email']).first():
                flash('Este e-mail já está cadastrado', 'error')
                return redirect(url_for('main.cadastrar_professor'))

            if Professor.query.filter_by(cpf=request.form['cpf']).first():
                flash('Este CPF já está cadastrado', 'error')
                return redirect(url_for('main.cadastrar_professor'))

            # Cria primeiro o Professor
            novo_professor = Professor(
                nome=request.form['nome'].strip(),
                rg=request.form['rg'].strip(),
                cpf=request.form['cpf'].strip(),
                endereco=request.form['endereco'].strip(),
                telefone=request.form['telefone'].strip(),
                disciplina=request.form['disciplina'].strip(),
                # Campos opcionais com valores padrão
                nacionalidade=request.form.get('nacionalidade', ''),
                estado_civil=request.form.get('estado_civil', ''),
                banco=request.form.get('banco', ''),
                agencia=request.form.get('agencia', ''),
                conta=request.form.get('conta', ''),
                pix=request.form.get('pix', ''),
                disponibilidade=request.form.get('disponibilidade', ''),
                valor_hora=float(request.form.get('valor_hora', 0)),
                tipo_atendimento=','.join(request.form.getlist('tipo_atendimento')),
                data_cadastro=datetime.utcnow()
            )
            db.session.add(novo_professor)
            db.session.flush()  # Obtém o ID do professor

            # Cria o User associado
            novo_usuario = User(
                nome=request.form['nome'].strip(),
                email=request.form['email'].strip().lower(),
                password_hash=generate_password_hash(request.form['password']),
                role='professor',
                professor_id=novo_professor.id,
                is_active=True,
                data_cadastro=datetime.utcnow()
            )
            db.session.add(novo_usuario)

            db.session.commit()
            flash('Professor cadastrado com sucesso!', 'success')
            return redirect(url_for('main.listar_professores'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar professor: {str(e)}', 'danger')
            return redirect(url_for('main.cadastrar_professor'))

    return render_template('professores/cadastro.html')

# ========== ROTAS PARA AGENDA ==========
@main_bp.route('/agenda', methods=['GET'])
@login_required
def agenda():
    """Exibe a agenda com calendário de aulas"""
    tz = timezone('America/Sao_Paulo')
    now = datetime.now()
    year = request.args.get('year', type=int, default=now.year)
    month = request.args.get('month', type=int, default=now.month)
    
    current_date = datetime(year=year, month=month, day=1)
    prev_month = current_date - relativedelta(months=1)
    next_month = current_date + relativedelta(months=1)
    
    first_weekday = current_date.weekday()
    last_day = (next_month - timedelta(days=1)).day
    first_weekday = (first_weekday + 1) % 7
    
    prev_month_days = []
    if first_weekday > 0:
        last_day_prev_month = (current_date - timedelta(days=1)).day
        prev_month_days = [
            datetime(year=prev_month.year, month=prev_month.month, day=d) 
            for d in range(last_day_prev_month - first_weekday + 1, last_day_prev_month + 1)
        ]
    
    current_month_days = [
        datetime(year=year, month=month, day=d) 
        for d in range(1, last_day + 1)
    ]
    
    total_days = len(prev_month_days) + len(current_month_days)
    remaining_days = (6 * 7) - total_days
    next_month_days = [
        datetime(year=next_month.year, month=next_month.month, day=d) 
        for d in range(1, remaining_days + 1)
    ] if remaining_days > 0 else []
    
    all_days = prev_month_days + current_month_days + next_month_days
    month_days = [all_days[i:i+7] for i in range(0, len(all_days), 7)]
    
    if current_user.role == 'aluno':
        aulas_query = Aula.query.filter_by(aluno_id=current_user.aluno.id)
    elif current_user.role == 'professor':
        aulas_query = Aula.query.filter_by(professor_id=current_user.professor.id)
    else:
        aulas_query = Aula.query
    
    start_date = datetime(year, month, 1)
    end_date = datetime(year, month + 1, 1) if month < 12 else datetime(year + 1, 1, 1)
    
    aulas = aulas_query.filter(
        Aula.data_hora >= start_date,
        Aula.data_hora < end_date
    ).order_by(Aula.data_hora).all()
    
    proximas_aulas = aulas_query.filter(
        Aula.data_hora >= now
    ).order_by(Aula.data_hora).limit(5).all()
    
    return render_template('agenda/calendario.html',
                         aulas=aulas,
                         proximas_aulas=proximas_aulas,
                         current_month=current_date,
                         prev_month=prev_month,
                         next_month=next_month,
                         month_days=month_days,
                         now=now)

@main_bp.route('/agenda/novo', methods=['POST'])
@login_required
def novo_agendamento():
    try:
        # Obter dados básicos do formulário
        data_hora = request.form.get('dataHora')
        duracao = int(request.form.get('duracao', 60))  # Default 60 minutos
        professor_id = int(request.form.get('professor_id'))
        aluno_id = request.form.get('aluno_id')
        materia_id = int(request.form.get('materia_id'))
        local = request.form.get('local', 'presencial')
        tipo_aula = request.form.get('tipoAula', 'individual')
        observacoes = request.form.get('observacoes', '').strip()
        
        # Processar recorrências
        recorrencias = []
        if 'recorrenciaAtiva' in request.form:
            tipos = request.form.getlist('recorrenciaTipo[]')
            dias = request.form.getlist('recorrenciaDia[]')
            fins = request.form.getlist('recorrenciaFim[]')
            
            for tipo, dia, fim in zip(tipos, dias, fins):
                if tipo and dia and fim:  # Verifica se todos os campos estão preenchidos
                    recorrencias.append({
                        'tipo': tipo,
                        'dia_semana': int(dia),
                        'data_fim': datetime.strptime(fim, '%Y-%m-%d')
                    })
        
        # Verificar conflitos antes de criar
        data_base = datetime.strptime(data_hora, '%Y-%m-%dT%H:%M')
        data_fim = data_base + timedelta(minutes=duracao)
        
        conflitos = verificar_conflitos_horario(professor_id, aluno_id, data_base, data_fim)
        if conflitos:
            raise ValueError(f"Conflito de horário: {conflitos[0].data_hora.strftime('%d/%m/%Y %H:%M')}")
        
        # Tratar tipo de aula
        if tipo_aula == 'individual':
            aluno_id = int(aluno_id) if aluno_id else None
            grupo_id = None
        else:
            grupo_id = int(request.form.get('grupo_id')) if request.form.get('grupo_id') else None
            aluno_id = None
        
        # Tratar local
        link_aula = request.form.get('linkAula') if local == 'online' else None
        
        # Criar agendamentos
        if not recorrencias:
            # Cria apenas um agendamento se não houver recorrência
            aula = Aula(
                data_hora=data_base,
                duracao=duracao,
                professor_id=professor_id,
                aluno_id=aluno_id,
                grupo_id=grupo_id,
                materia_id=materia_id,
                local=local,
                link_aula=link_aula,
                observacoes=observacoes,
                criado_por=current_user.id
            )
            db.session.add(aula)
        else:
            for rec in recorrencias:
                data_atual = data_base
                while data_atual <= rec['data_fim']:
                    # Verifica se o dia da semana corresponde (para recorrência semanal)
                    if rec['tipo'] == 'semanal' and data_atual.weekday() != rec['dia_semana']:
                        data_atual += timedelta(days=1)
                        continue
                    
                    aula = Aula(
                        data_hora=data_atual,
                        duracao=duracao,
                        professor_id=professor_id,
                        aluno_id=aluno_id,
                        grupo_id=grupo_id,
                        materia_id=materia_id,
                        local=local,
                        link_aula=link_aula,
                        observacoes=observacoes,
                        criado_por=current_user.id,
                        recorrencia=rec
                    )
                    db.session.add(aula)
                    
                    # Avança para a próxima data
                    if rec['tipo'] == 'semanal':
                        data_atual += timedelta(weeks=1)
                    elif rec['tipo'] == 'mensal':
                        data_atual = data_atual + relativedelta(months=1)
        
        db.session.commit()
        
        # Enviar notificações
        enviar_notificacao_agendamento(aula)
        
        flash('Agendamento(s) criado(s) com sucesso!', 'success')
        return redirect(url_for('main.agenda'))
        
    except ValueError as e:
        db.session.rollback()
        flash(f'Erro de validação: {str(e)}', 'warning')
        return redirect(url_for('main.agenda'))
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Erro ao criar agendamento: {str(e)}', exc_info=True)
        flash(f'Erro ao criar agendamento: {str(e)}', 'danger')
        return redirect(url_for('main.agenda'))

def enviar_notificacao_agendamento(aula):
    """Envia notificações por e-mail para professor e aluno"""
    try:
        professor = Professor.query.get(aula.professor_id)
        if not professor:
            current_app.logger.error(f"Professor não encontrado: ID {aula.professor_id}")
            return

        destinatarios = [professor.email]
        
        if aula.aluno_id:
            aluno = Aluno.query.get(aula.aluno_id)
            if aluno and aluno.email:
                destinatarios.append(aluno.email)
        
        materia_nome = getattr(aula.materia, 'nome', 'Aula') if hasattr(aula, 'materia') else 'Aula'
        assunto = f"Novo Agendamento - {materia_nome}"
        mensagem = render_template('emails/novo_agendamento.html', aula=aula)
        
        # Implementação do envio de email aqui
        # ...
        
    except Exception as e:
        current_app.logger.error(f"Erro ao enviar notificação: {str(e)}", exc_info=True)

# ========== ROTAS API ==========
@api_bp.route('/aulas', methods=['GET'])
@login_required
def api_aulas():
    """API para buscar aulas no formato JSON"""
    start = request.args.get('start')
    end = request.args.get('end')
    
    try:
        start_date = datetime.strptime(start, '%Y-%m-%d')
        end_date = datetime.strptime(end, '%Y-%m-%d')
    except (ValueError, TypeError):
        return jsonify({'error': 'Datas inválidas'}), 400
    
    # Filtra aulas baseado no tipo de usuário
    if current_user.role == 'aluno':
        aulas = Aula.query.filter(
            Aula.aluno_id == current_user.aluno.id,
            Aula.data_hora >= start_date,
            Aula.data_hora <= end_date
        ).all()
    elif current_user.role == 'professor':
        aulas = Aula.query.filter(
            Aula.professor_id == current_user.professor.id,
            Aula.data_hora >= start_date,
            Aula.data_hora <= end_date
        ).all()
    else:
        aulas = Aula.query.filter(
            Aula.data_hora >= start_date,
            Aula.data_hora <= end_date
        ).all()
    
    eventos = []
    for aula in aulas:
        eventos.append({
            'id': aula.id,
            'title': f"{aula.materia} - {aula.aluno.nome if aula.aluno else 'Grupo'}",
            'start': aula.data_hora.isoformat(),
            'end': (aula.data_hora + timedelta(minutes=aula.duracao)).isoformat(),
            'color': '#3a87ad' if aula.aluno_id else '#f89406',
            'url': url_for('agenda.visualizar_aula', id=aula.id)
        })
    
    return jsonify(eventos)

# ========== ROTAS PARA RELATÓRIOS ==========
@main_bp.route('/relatorios/mensal', methods=['GET'])
@login_required
def relatorio_mensal():
    now = datetime.now()
    ano = request.args.get('ano', type=int, default=now.year)
    mes = request.args.get('mes', type=int, default=now.month)
    
    # Consulta básica para filtrar por mês/ano
    aulas_query = Aula.query.filter(
        extract('year', Aula.data_hora) == ano,
        extract('month', Aula.data_hora) == mes
    )
    
    # Totais gerais
    total_aulas = aulas_query.count()
    alunos_ativos = aulas_query.distinct(Aula.aluno_id).count()
    professores_ativos = aulas_query.distinct(Aula.professor_id).count()
    
    # Horas ministradas (soma da duração em minutos convertida para horas)
    horas_ministradas = aulas_query.with_entities(
        func.sum(Aula.duracao).label('total_minutos')
    ).first().total_minutos or 0
    horas_ministradas = round(horas_ministradas / 60, 1)
    
    # Cálculos financeiros
    faturamento_total = aulas_query.with_entities(
        func.sum(Aula.valor_aula).label('total_valor')
    ).first().total_valor or 0
    
    custo_professores = aulas_query.with_entities(
        func.sum(Aula.custo_aula).label('total_custo')
    ).first().total_custo or 0
    
    deslocamento_total = aulas_query.with_entities(
        func.sum(func.coalesce(Aula.deslocamento, 0)).label('total_deslocamento')
    ).first().total_deslocamento or 0
    
    lucro_liquido = faturamento_total - custo_professores - deslocamento_total
    custos_fixos = 1780.00
    
    # Aulas por professor
    aulas_por_professor = db.session.query(
        Professor.nome,
        func.count(Aula.id).label('total_aulas'),
        func.sum(Aula.duracao).label('total_minutos'),
        func.sum(Aula.valor_aula).label('valor_gerado'),
        func.count(distinct(Aula.aluno_id)).label('total_alunos')
    ).join(Aula, Aula.professor_id == Professor.id)\
     .filter(
        extract('year', Aula.data_hora) == ano,
        extract('month', Aula.data_hora) == mes
     ).group_by(Professor.nome).all()

    
    # Adicionando horas formatadas e alunos atendidos
    aulas_por_professor = [{
        'nome': prof.nome,
        'total_aulas': prof.total_aulas,
        'horas_ministradas': round(prof.total_minutos / 60, 1),
        'valor_gerado': prof.valor_gerado or 0,
        'valor_hora': prof.valor_hora or 0,
        'custo_total': (prof.total_minutos / 60) * (prof.valor_hora or 0),
        'alunos_atendidos': get_alunos_por_professor(prof.nome, mes, ano)
    } for prof in aulas_por_professor]
    
    # Aulas por aluno
    aulas_por_aluno = db.session.query(
        Aluno.nome,
        Aluno.plano_adquirido,
        func.count(Aula.id).label('total_aulas'),
        func.sum(Aula.duracao).label('total_minutos'),
        func.count(distinct(Aula.professor_id)).label('total_professores')
    ).join(Aula, Aula.aluno_id == Aluno.id)\
     .filter(
        extract('year', Aula.data_hora) == ano,
        extract('month', Aula.data_hora) == mes
     ).group_by(Aluno.nome, Aluno.plano_adquirido).all()
    
    # Adicionando horas formatadas e professores
    aulas_por_aluno = [{
        'nome': aluno.nome,
        'plano_adquirido': aluno.plano_adquirido,
        'total_aulas': aluno.total_aulas,
        'horas_recebidas': round(aluno.total_minutos / 60, 1),
        'professores': get_professores_por_aluno(aluno.nome, mes, ano)
    } for aluno in aulas_por_aluno]
    
    # Relação aluno-professor detalhada
    relacoes_aluno_professor = db.session.query(
        Aluno.nome.label('aluno_nome'),
        Professor.nome.label('professor_nome'),
        func.count(Aula.id).label('total_aulas'),
        func.sum(Aula.duracao).label('total_minutos'),
        func.sum(Aula.valor_aula).label('valor_total')
    ).join(Aula, Aula.aluno_id == Aluno.id)\
     .join(Professor, Aula.professor_id == Professor.id)\
     .filter(
        extract('year', Aula.data_hora) == ano,
        extract('month', Aula.data_hora) == mes
     ).group_by(Aluno.nome, Professor.nome).all()
    
    # Alunos por plano
    alunos_por_plano = db.session.query(
        Aluno.plano_adquirido,
        func.count(distinct(Aluno.id)).label('total'),
        (func.count(distinct(Aluno.id)) * 100.0 / alunos_ativos).label('percentual')
    ).join(Aula, Aula.aluno_id == Aluno.id)\
     .filter(
        extract('year', Aula.data_hora) == ano,
        extract('month', Aula.data_hora) == mes
     ).group_by(Aluno.plano_adquirido).all()
    
    # Aulas por local
    aulas_por_local = db.session.query(
        Aula.local,
        func.count(Aula.id).label('total'),
        (func.count(Aula.id) * 100.0 / total_aulas).label('percentual')
    ).filter(
        extract('year', Aula.data_hora) == ano,
        extract('month', Aula.data_hora) == mes
    ).group_by(Aula.local).all()
    
    # Aulas por tipo
    aulas_por_tipo = db.session.query(
        Aula.tipo_aula,
        func.count(Aula.id).label('total'),
        (func.count(Aula.id) * 100.0 / total_aulas).label('percentual')
    ).filter(
        extract('year', Aula.data_hora) == ano,
        extract('month', Aula.data_hora) == mes
    ).group_by(Aula.tipo_aula).all()
    
    # Lista de meses para o dropdown
    meses = [(i, calendar.month_name[i]) for i in range(1, 13)]

    
    return render_template('relatorios/mensal.html',
        mes=mes,
        ano=ano,
        meses=meses,
        ano_atual=now.year,
        total_aulas=total_aulas,
        alunos_ativos=alunos_ativos,
        professores_ativos=professores_ativos,
        horas_ministradas=horas_ministradas,
        faturamento_total=faturamento_total,
        custo_professores=custo_professores,
        custos_fixos=custos_fixos,
        aulas_por_professor=aulas_por_professor,
        aulas_por_aluno=aulas_por_aluno,
        relacoes_aluno_professor=relacoes_aluno_professor,
        alunos_por_plano=alunos_por_plano,
        aulas_por_local=aulas_por_local,
        aulas_por_tipo=aulas_por_tipo)

def get_alunos_por_professor(professor_nome, mes, ano):
    """Retorna lista de alunos atendidos por um professor específico"""
    alunos = db.session.query(
        Aluno.nome,
        func.count(Aula.id).label('total_aulas')
    ).join(Aula, Aula.aluno_id == Aluno.id)\
     .join(Professor, Aula.professor_id == Professor.id)\
     .filter(
        Professor.nome == professor_nome,
        extract('year', Aula.data_hora) == ano,
        extract('month', Aula.data_hora) == mes
     ).group_by(Aluno.nome).all()
    
    return [{'nome': a.nome, 'total_aulas': a.total_aulas} for a in alunos]

def get_professores_por_aluno(aluno_nome, mes, ano):
    """Retorna lista de professores que atenderam um aluno específico"""
    professores = db.session.query(
        Professor.nome,
        func.count(Aula.id).label('total_aulas')
    ).join(Aula, Aula.professor_id == Professor.id)\
     .join(Aluno, Aula.aluno_id == Aluno.id)\
     .filter(
        Aluno.nome == aluno_nome,
        extract('year', Aula.data_hora) == ano,
        extract('month', Aula.data_hora) == mes
     ).group_by(Professor.nome).all()
    
    return [{'nome': p.nome, 'total_aulas': p.total_aulas} for p in professores]

# ========== ROTAS PARA Relatório Personalizado ==========
@main_bp.route('/relatorios/aluno/<int:aluno_id>/pdf')
@login_required
def relatorio_aluno_pdf(aluno_id):
    aluno = Aluno.query.get_or_404(aluno_id)
    now = datetime.now()
    
    # Verificação de permissões
    if current_user.role == 'aluno' and current_user.aluno.id != aluno_id:
        abort(403)
    elif current_user.role == 'professor':
        # Verifica se o professor tem aulas com este aluno
        if not Aula.query.filter_by(professor_id=current_user.professor.id, aluno_id=aluno_id).first():
            abort(403)
    
    # Filtros
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    
    query = Aula.query.filter(
        Aula.aluno_id == aluno_id,
        Aula.realizada.is_(True)
    )
    
    if data_inicio:
        query = query.filter(Aula.data_hora >= datetime.strptime(data_inicio, '%Y-%m-%d'))
    if data_fim:
        # Adiciona 23:59:59 ao final do dia
        data_fim = datetime.strptime(data_fim, '%Y-%m-%d') + timedelta(days=1) - timedelta(seconds=1)
        query = query.filter(Aula.data_hora <= data_fim)
    
    aulas = query.order_by(Aula.data_hora).all()
    
    # Cálculos
    total_aulas = len(aulas)
    total_horas = sum(aula.duracao for aula in aulas) / 60
    total_devido = sum(aula.valor_aula for aula in aulas)
    
    # Caminho para o logo (ajuste conforme sua estrutura)
    logo_path = os.path.join(current_app.root_path, 'static', 'img', 'Logo_Impetus-preto.png')
    if not os.path.exists(logo_path):
        logo_path = None  # Ou use um logo padrão
    
    # Renderizar HTML
    html = render_template('relatorios/aluno_pdf.html',
        aluno=aluno,
        aulas=aulas,
        total_aulas=total_aulas,
        total_horas=total_horas,
        total_devido=total_devido,
        logo_path=logo_path,
        data_emissao=now.strftime('%d/%m/%Y'),
        current_user=current_user
    )
    
    # Gerar PDF
    pdf = HTML(string=html).write_pdf()
    
    # Criar resposta
    buffer = BytesIO(pdf)
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'relatorio_{aluno.nome}_{now.strftime("%Y%m%d")}.pdf'
    )

# --- FUNÇÕES AUXILIARES PARA RELATÓRIOS ---
def get_alunos_por_professor(professor_nome, mes, ano):
    """Retorna lista de alunos atendidos por um professor específico"""
    alunos = db.session.query(
        Aluno.nome,
        func.count(Aula.id).label('total_aulas')
    ).join(Aula, Aula.aluno_id == Aluno.id)\
     .join(Professor, Aula.professor_id == Professor.id)\
     .filter(
        Professor.nome == professor_nome,
        extract('year', Aula.data_hora) == ano,
        extract('month', Aula.data_hora) == mes
     ).group_by(Aluno.nome).all()
    
    return [{'nome': a.nome, 'total_aulas': a.total_aulas} for a in alunos]

def get_professores_por_aluno(aluno_nome, mes, ano):
    """Retorna lista de professores que atenderam um aluno específico"""
    professores = db.session.query(
        Professor.nome,
        func.count(Aula.id).label('total_aulas')
    ).join(Aula, Aula.professor_id == Professor.id)\
     .join(Aluno, Aula.aluno_id == Aluno.id)\
     .filter(
        Aluno.nome == aluno_nome,
        extract('year', Aula.data_hora) == ano,
        extract('month', Aula.data_hora) == mes
     ).group_by(Professor.nome).all()
    
    return [{'nome': p.nome, 'total_aulas': p.total_aulas} for p in professores]

# ========== ROTAS PARA CONTRATOS ==========
@main_bp.route('/contratos', methods=['GET'])
@login_required
def listar_contratos():
    contratos = Contrato.query.all()
    return render_template('contratos/lista.html', contratos=contratos)

# ========== ROTAS DE PERFIL ==========
@main_bp.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    if request.method == 'POST':
        try:
            current_user.email = request.form['email'].strip().lower()

            if current_user.role == 'aluno' and current_user.aluno:
                aluno = current_user.aluno
                aluno.telefone = request.form['telefone'].strip()
                aluno.endereco = request.form['endereco'].strip()

            elif current_user.role == 'professor' and current_user.professor:
                professor = current_user.professor
                professor.telefone = request.form['telefone'].strip()
                professor.endereco = request.form['endereco'].strip()

            db.session.commit()
            flash('Perfil atualizado com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar perfil: {str(e)}', 'danger')

    return render_template('perfil.html')

# ========== ROTAS PARA ALERTAS E RELATÓRIOS ==========
@main_bp.route('/contratos/vencimentos')
@login_required
def contratos_vencimentos():
    """Lista contratos próximos ao vencimento"""
    dias_alerta = request.args.get('dias', 30, type=int)
    data_limite = date.today() + timedelta(days=dias_alerta)
    
    if current_user.role == 'responsavel':
        contratos_vencendo = Contrato.query.filter(
            and_(
                Contrato.responsavel_id == current_user.responsavel.id,
                Contrato.validade <= data_limite, 
                Contrato.validade >= date.today()
            )
        ).order_by(Contrato.validade).all()
    else:
        contratos_vencendo = Contrato.query.filter(
            and_(Contrato.validade <= data_limite, Contrato.validade >= date.today())
        ).order_by(Contrato.validade).all()
    
    return render_template('contratos/vencimentos.html', 
                         contratos=contratos_vencendo, dias_alerta=dias_alerta)

@main_bp.route('/alunos/com-contratos')
@login_required
def alunos_com_contratos():
    """Lista todos os alunos que possuem contratos"""
    if current_user.role not in ['admin']:
        abort(403)
        
    # Buscar alunos que estão associados a pelo menos um contrato
    alunos_com_contrato = db.session.query(Aluno).join(
        Contrato.alunos
    ).distinct().all()
    
    return render_template('alunos/com_contratos.html', alunos=alunos_com_contrato)

@main_bp.route('/dashboard/contratos')
@login_required
def dashboard_contratos():
    """Dashboard com estatísticas de contratos"""
    if current_user.role not in ['admin']:
        abort(403)
        
    total_contratos = Contrato.query.count()
    contratos_ativos = Contrato.query.filter(Contrato.validade >= date.today()).count()
    contratos_vencidos = Contrato.query.filter(Contrato.validade < date.today()).count()
    
    # Contratos vencendo nos próximos 30 dias
    data_limite = date.today() + timedelta(days=30)
    contratos_vencendo = Contrato.query.filter(
        and_(Contrato.validade <= data_limite, Contrato.validade >= date.today())
    ).count()
    
    # Valor total dos contratos ativos
    valor_total_ativo = db.session.query(db.func.sum(Contrato.valor_total)).filter(
        Contrato.validade >= date.today()
    ).scalar() or 0
    
    estatisticas = {
        'total_contratos': total_contratos,
        'contratos_ativos': contratos_ativos,
        'contratos_vencidos': contratos_vencidos,
        'contratos_vencendo': contratos_vencendo,
        'valor_total_ativo': valor_total_ativo
    }
    
    # Contratos por tipo de plano
    contratos_por_plano = db.session.query(
        Contrato.tipo_plano, 
        db.func.count(Contrato.id)
    ).filter(
        Contrato.validade >= date.today()
    ).group_by(Contrato.tipo_plano).all()
    
    estatisticas = {
        'total_contratos': total_contratos,
        'contratos_ativos': contratos_ativos,
        'contratos_vencidos': contratos_vencidos,
        'contratos_vencendo': contratos_vencendo,
        'valor_total_ativo': valor_total_ativo,
        'contratos_por_plano': contratos_por_plano
    }
    
    return render_template('dashboard/contratos.html', estatisticas=estatisticas)

# ========== MANIPULADORES DE ERRO ==========
@main_bp.errorhandler(403)
def forbidden_error(error):
    return render_template('errors/403.html'), 403

@main_bp.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@main_bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    current_app.logger.error(f"Erro 500: {str(error)}", exc_info=True)
    return render_template('errors/500.html'), 500

# ========== API ENDPOINTS PARA AJAX ==========
@api_bp.route('/responsavel/<int:responsavel_id>/alunos')
@login_required
def api_alunos_responsavel(responsavel_id):
    """API para buscar alunos de um responsável específico"""
    responsavel = Responsavel.query.get_or_404(responsavel_id)
    alunos = [{'id': aluno.id, 'nome': aluno.nome} for aluno in responsavel.alunos]
    return jsonify(alunos)

@api_bp.route('/contrato/<int:contrato_id>/status')
@login_required
def api_status_contrato(contrato_id):
    """API para verificar status de um contrato"""
    contrato = Contrato.query.get_or_404(contrato_id)
    
    dias_para_vencimento = (contrato.validade - date.today()).days
    
    if dias_para_vencimento < 0:
        status = 'vencido'
    elif dias_para_vencimento <= 30:
        status = 'vencendo'
    else:
        status = 'ativo'
    
    return jsonify({
        'status': status,
        'dias_para_vencimento': dias_para_vencimento,
        'validade': contrato.validade.strftime('%d/%m/%Y')
    })

# ========== ROTAS PARA NOTIFICAÇÕES ==========
@main_bp.route('/notificacoes')
@login_required
def listar_notificacoes():
    """Lista todas as notificações do usuário"""
    notificacoes = Notificacao.query.filter_by(
        usuario_id=current_user.id
    ).order_by(Notificacao.data_criacao.desc()).all()
    
    return render_template('notificacoes/lista.html', notificacoes=notificacoes)

@main_bp.route('/notificacao/<int:id>/marcar-lida')
@login_required
def marcar_notificacao_lida(id):
    """Marca uma notificação como lida"""
    notificacao = Notificacao.query.get_or_404(id)
    
    if notificacao.usuario_id != current_user.id:
        abort(403)
    
    notificacao.lida = True
    db.session.commit()
    
    return jsonify({'success': True})

# ========== FUNÇÃO PARA CRIAR NOTIFICAÇÕES AUTOMÁTICAS ==========
def verificar_e_criar_notificacoes_vencimento():
    """Verifica contratos próximos ao vencimento e cria notificações"""
    data_limite = date.today() + timedelta(days=30)
    contratos_vencendo = Contrato.query.filter(
        and_(Contrato.validade <= data_limite, Contrato.validade >= date.today())
    ).all()
    
    for contrato in contratos_vencendo:
        dias_restantes = (contrato.validade - date.today()).days
        
        # Verificar se já existe notificação para este contrato
        notificacao_existente = Notificacao.query.filter_by(
            usuario_id=contrato.responsavel.user.id if contrato.responsavel.user else None,
            titulo=f'Contrato próximo ao vencimento - {contrato.tipo_plano}'
        ).first()
        
        if not notificacao_existente and contrato.responsavel.user:
            criar_notificacao(
                usuario_id=contrato.responsavel.user.id,
                titulo=f'Contrato próximo ao vencimento - {contrato.tipo_plano}',
                mensagem=f'Seu contrato {contrato.tipo_plano} vence em {dias_restantes} dias ({contrato.validade.strftime("%d/%m/%Y")}). Entre em contato para renovação.',
                tipo='warning'
            )

@main_bp.route('/admin/verificar-vencimentos')
@login_required
@admin_required
def verificar_vencimentos():
    """Executa verificação manual de vencimentos e cria notificações"""
    try:
        verificar_e_criar_notificacoes_vencimento()
        flash('Verificação de vencimentos executada com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao verificar vencimentos: {str(e)}', 'error')
    
    return redirect(url_for('main.admin_dashboard'))

# ========== ROTA PARA BUSCA AVANÇADA ==========
@main_bp.route('/buscar')
@login_required
def busca_avancada():
    """Busca avançada no sistema"""
    termo = request.args.get('q', '').strip()
    tipo = request.args.get('tipo', 'todos')
    
    resultados = {
        'alunos': [],
        'responsaveis': [],
        'contratos': [],
        'professores': []
    }
    
    if termo:
        if tipo in ['todos', 'alunos']:
            resultados['alunos'] = Aluno.query.filter(
                or_(
                    Aluno.nome.ilike(f'%{termo}%'),
                    Aluno.cpf.ilike(f'%{termo}%')
                )
            ).limit(10).all()
        
        if tipo in ['todos', 'responsaveis']:
            resultados['responsaveis'] = Responsavel.query.filter(
                or_(
                    Responsavel.nome.ilike(f'%{termo}%'),
                    Responsavel.cpf.ilike(f'%{termo}%')
                )
            ).limit(10).all()
        
        if tipo in ['todos', 'contratos']:
            resultados['contratos'] = Contrato.query.join(Responsavel).filter(
                or_(
                    Responsavel.nome.ilike(f'%{termo}%'),
                    Contrato.tipo_plano.ilike(f'%{termo}%')
                )
            ).limit(10).all()
        
        if tipo in ['todos', 'professores']:
            resultados['professores'] = Professor.query.filter(
                or_(
                    Professor.nome.ilike(f'%{termo}%'),
                    Professor.disciplina.ilike(f'%{termo}%')
                )
            ).limit(10).all()
    
    return render_template('busca/resultados.html', 
                         resultados=resultados, 
                         termo=termo, 
                         tipo=tipo)

# Registrar blueprints
def init_app(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(alunos_bp)
    app.register_blueprint(professores_bp)
    app.register_blueprint(agenda_bp)
    app.register_blueprint(api_bp)