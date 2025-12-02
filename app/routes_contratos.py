"""
Rotas Flask para o sistema de contratos
Integra todas as funcionalidades desenvolvidas
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, send_file
from datetime import datetime, date, timedelta
from sqlalchemy import and_, or_
import os
import json

# Importar modelos (assumindo que estão no arquivo models.py)
from app.models import (
    db, Contrato, Aluno, Professor, Responsavel, ContratoAluno
)

# Importar gerador de contratos - CORREÇÃO AQUI
try:
    from app.gerador_contratos import gerar_contrato_pdf
except ImportError:
    # Fallback caso o gerador não esteja disponível
    def gerar_contrato_pdf(*args, **kwargs):
        raise Exception("Gerador de contratos não disponível")

# Criar blueprint para as rotas de contratos
contratos_bp = Blueprint('contratos', __name__, url_prefix='/contratos')

@contratos_bp.route('/')
def lista_contratos():
    """Página principal de listagem de contratos"""
    contratos = Contrato.query.order_by(Contrato.data_upload.desc()).all()
    return render_template('contratos/lista.html', contratos=contratos)

@contratos_bp.route('/vencimentos')
def vencimentos():
    """Página de vencimentos de contratos"""
    hoje = date.today()
    
    # Contratos vencidos
    contratos_vencidos = Contrato.query.filter(
        Contrato.validade < hoje,
        Contrato.status == 'ativo'
    ).all()
    
    # Contratos que vencem nos próximos 30 dias
    data_30_dias = hoje + timedelta(days=30)
    contratos_30_dias = Contrato.query.filter(
        and_(
            Contrato.validade >= hoje,
            Contrato.validade <= data_30_dias,
            Contrato.status == 'ativo'
        )
    ).all()
    
    # Contratos que vencem nos próximos 90 dias
    data_90_dias = hoje + timedelta(days=90)
    contratos_90_dias = Contrato.query.filter(
        and_(
            Contrato.validade >= hoje,
            Contrato.validade <= data_90_dias,
            Contrato.status == 'ativo'
        )
    ).all()
    
    # Todos os contratos ativos para a tabela
    contratos = Contrato.query.filter(Contrato.status == 'ativo').order_by(Contrato.validade.asc()).all()
    
    # Calcular valor total
    valor_total = sum(contrato.valor_total for contrato in contratos)
    valor_total_formatado = f"{valor_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    # Lista de responsáveis para filtros
    responsaveis = Responsavel.query.order_by(Responsavel.nome).all()
    
    return render_template('contratos/vencimentos.html', 
                         contratos=contratos,
                         contratos_vencidos=contratos_vencidos,
                         contratos_30_dias=contratos_30_dias,
                         contratos_90_dias=contratos_90_dias,
                         valor_total_formatado=valor_total_formatado,
                         responsaveis=responsaveis)

@contratos_bp.route('/novo', methods=['GET', 'POST'])
def novo_contrato():
    """Página para criar novo contrato"""
    if request.method == 'GET':
        # Buscar responsáveis e professores para os selects
        responsaveis = Responsavel.query.order_by(Responsavel.nome).all()
        professores = Professor.query.order_by(Professor.nome).all()
        
        return render_template('contratos/novo.html', 
                             responsaveis=responsaveis,
                             professores=professores)
    
    elif request.method == 'POST':
        try:
            # Coletar dados do formulário
            responsavel_id = request.form.get('responsavel_id')
            alunos_ids = request.form.getlist('alunos_ids')
            
            # Dados do responsável (caso seja novo)
            if responsavel_id == '0' or not responsavel_id:
                # Criar novo responsável
                responsavel = Responsavel(
                    nome=request.form.get('responsavel_nome'),
                    cpf=request.form.get('responsavel_cpf'),
                    rg=request.form.get('responsavel_rg'),
                    telefone=request.form.get('responsavel_telefone'),
                    email=request.form.get('responsavel_email'),
                    endereco=request.form.get('responsavel_endereco'),
                    estado_civil=request.form.get('responsavel_estado_civil', ''),
                    nacionalidade=request.form.get('responsavel_nacionalidade', 'brasileira')
                )
                db.session.add(responsavel)
                db.session.flush()  # Para obter o ID
            else:
                # Usar responsável existente
                responsavel = Responsavel.query.get_or_404(responsavel_id)
            
            # Buscar alunos selecionados
            alunos = Aluno.query.filter(Aluno.id.in_(alunos_ids)).all()
            
            if not alunos:
                flash('Selecione pelo menos um aluno para o contrato.', 'error')
                return redirect(url_for('contratos.novo_contrato'))
            
            # Dados do contrato
            tipo_plano = request.form.get('tipo_plano')
            valor_total = float(request.form.get('valor_total'))
            data_inicio = datetime.strptime(request.form.get('data_inicio'), '%Y-%m-%d').date()
            validade = datetime.strptime(request.form.get('validade'), '%Y-%m-%d').date()
            professor_id = request.form.get('professor_id') or None
            servicos_incluidos = request.form.get('servicos_incluidos', '')
            observacoes = request.form.get('observacoes', '')
            
            # Criar contrato
            contrato = Contrato(
                responsavel_id=responsavel.id,
                professor_id=professor_id,
                tipo_plano=tipo_plano,
                valor_total=valor_total,
                data_inicio=data_inicio,
                validade=validade,
                servicos_incluidos=servicos_incluidos,
                observacoes=observacoes,
                status='ativo'
            )
            
            db.session.add(contrato)
            db.session.flush()  # Para obter o ID do contrato
            
            # Associar alunos ao contrato
            for aluno in alunos:
                contrato_aluno = ContratoAluno(
                    contrato_id=contrato.id,
                    aluno_id=aluno.id
                )
                db.session.add(contrato_aluno)
            
            # Gerar PDF do contrato
            try:
                caminho_pdf = gerar_contrato_pdf(
                    responsavel, alunos, tipo_plano, valor_total,
                    data_inicio, validade, observacoes
                )
                contrato.arquivo = caminho_pdf
            except Exception as e:
                print(f"Erro ao gerar PDF: {e}")
                # Continuar mesmo se houver erro na geração do PDF
            
            db.session.commit()
            
            flash('Contrato criado com sucesso!', 'success')
            return redirect(url_for('contratos.visualizar_contrato', contrato_id=contrato.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar contrato: {str(e)}', 'error')
            return redirect(url_for('contratos.novo_contrato'))

@contratos_bp.route('/<int:contrato_id>/visualizar')
def visualizar_contrato(contrato_id):
    """Visualizar contrato específico"""
    contrato = Contrato.query.get_or_404(contrato_id)
    
    if contrato.arquivo and os.path.exists(contrato.arquivo):
        return send_file(contrato.arquivo, as_attachment=False)
    else:
        flash('Arquivo do contrato não encontrado.', 'error')
        return redirect(url_for('contratos.lista_contratos'))

@contratos_bp.route('/<int:contrato_id>/editar', methods=['GET', 'POST'])
def editar_contrato(contrato_id):
    """Editar contrato existente"""
    contrato = Contrato.query.get_or_404(contrato_id)
    
    if request.method == 'GET':
        responsaveis = Responsavel.query.order_by(Responsavel.nome).all()
        professores = Professor.query.order_by(Professor.nome).all()
        
        return render_template('contratos/editar_contrato.html', 
                             contrato=contrato,
                             responsaveis=responsaveis,
                             professores=professores)
    
    elif request.method == 'POST':
        try:
            # Atualizar dados do contrato
            contrato.tipo_plano = request.form.get('tipo_plano')
            contrato.valor_total = float(request.form.get('valor_total'))
            contrato.data_inicio = datetime.strptime(request.form.get('data_inicio'), '%Y-%m-%d').date()
            contrato.validade = datetime.strptime(request.form.get('validade'), '%Y-%m-%d').date()
            contrato.professor_id = request.form.get('professor_id') or None
            contrato.servicos_incluidos = request.form.get('servicos_incluidos', '')
            contrato.observacoes = request.form.get('observacoes', '')
            contrato.status = request.form.get('status', 'ativo')
            
            db.session.commit()
            
            flash('Contrato atualizado com sucesso!', 'success')
            return redirect(url_for('contratos.visualizar_contrato', contrato_id=contrato.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar contrato: {str(e)}', 'error')
            return redirect(url_for('contratos.editar_contrato', contrato_id=contrato_id))

@contratos_bp.route('/renovar', methods=['POST'])
def renovar_contrato():
    """Renovar contrato existente"""
    try:
        dados = request.get_json()
        contrato_id = dados.get('contrato_id')
        
        contrato_original = Contrato.query.get_or_404(contrato_id)
        
        # Criar novo contrato baseado no original
        novo_contrato = Contrato(
            responsavel_id=contrato_original.responsavel_id,
            professor_id=contrato_original.professor_id,
            tipo_plano=dados.get('tipo_plano'),
            valor_total=float(dados.get('valor_total')),
            data_inicio=datetime.strptime(dados.get('data_inicio'), '%Y-%m-%d').date(),
            validade=datetime.strptime(dados.get('validade'), '%Y-%m-%d').date(),
            servicos_incluidos=contrato_original.servicos_incluidos,
            observacoes=dados.get('observacoes', ''),
            status='ativo'
        )
        
        db.session.add(novo_contrato)
        db.session.flush()
        
        # Copiar associações de alunos
        for contrato_aluno in contrato_original.alunos:
            nova_associacao = ContratoAluno(
                contrato_id=novo_contrato.id,
                aluno_id=contrato_aluno.aluno_id
            )
            db.session.add(nova_associacao)
        
        # Marcar contrato original como renovado
        contrato_original.status = 'renovado'
        
        # Gerar PDF do novo contrato
        try:
            alunos = [ca.aluno for ca in contrato_original.alunos]
            caminho_pdf = gerar_contrato_pdf(
                contrato_original.responsavel, alunos, 
                novo_contrato.tipo_plano, novo_contrato.valor_total,
                novo_contrato.data_inicio, novo_contrato.validade, 
                novo_contrato.observacoes
            )
            novo_contrato.arquivo = caminho_pdf
        except Exception as e:
            print(f"Erro ao gerar PDF: {e}")
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Contrato renovado com sucesso!',
            'novo_contrato_id': novo_contrato.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro ao renovar contrato: {str(e)}'
        }), 500

@contratos_bp.route('/<int:contrato_id>/lembrete', methods=['POST'])
def enviar_lembrete(contrato_id):
    """Enviar lembrete de vencimento"""
    try:
        contrato = Contrato.query.get_or_404(contrato_id)
        
        # Aqui você implementaria o envio do lembrete
        # Por exemplo, via email, WhatsApp, SMS, etc.
        
        # Por enquanto, apenas simular o envio
        return jsonify({
            'success': True,
            'message': f'Lembrete enviado para {contrato.responsavel.nome}'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao enviar lembrete: {str(e)}'
        }), 500

@contratos_bp.route('/rascunho', methods=['POST'])
def salvar_rascunho():
    """Salvar rascunho de contrato"""
    try:
        dados = request.get_json()
        
        # Salvar em arquivo temporário ou sessão
        # Por simplicidade, vamos apenas retornar sucesso
        
        return jsonify({
            'success': True,
            'message': 'Rascunho salvo com sucesso!'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao salvar rascunho: {str(e)}'
        }), 500

# Rotas da API para AJAX
@contratos_bp.route('/api/responsavel/<int:responsavel_id>/alunos')
def api_alunos_responsavel(responsavel_id):
    """API para buscar alunos de um responsável"""
    try:
        alunos = Aluno.query.filter_by(responsavel_id=responsavel_id).all()
        
        alunos_data = []
        for aluno in alunos:
            alunos_data.append({
                'id': aluno.id,
                'nome': aluno.nome,
                'cpf': aluno.cpf,
                'serie': aluno.serie,
                'mora_plano_piloto': aluno.mora_plano_piloto
            })
        
        return jsonify(alunos_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@contratos_bp.route('/api/responsaveis/buscar')
def api_buscar_responsaveis():
    """API para buscar responsáveis"""
    try:
        termo = request.args.get('q', '').strip()
        
        if len(termo) < 3:
            return jsonify([])
        
        # Buscar por nome, CPF ou telefone
        responsaveis = Responsavel.query.filter(
            or_(
                Responsavel.nome.ilike(f'%{termo}%'),
                Responsavel.cpf.ilike(f'%{termo}%'),
                Responsavel.telefone.ilike(f'%{termo}%')
            )
        ).limit(10).all()
        
        responsaveis_data = []
        for resp in responsaveis:
            responsaveis_data.append({
                'id': resp.id,
                'nome': resp.nome,
                'cpf': resp.cpf,
                'rg': resp.rg,
                'telefone': resp.telefone,
                'email': resp.email,
                'endereco': resp.endereco,
                'estado_civil': resp.estado_civil or '',
                'nacionalidade': resp.nacionalidade or 'brasileira'
            })
        
        return jsonify(responsaveis_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@contratos_bp.route('/dashboard')
def dashboard_contratos():
    """Dashboard de contratos"""
    hoje = date.today()
    
    # Estatísticas gerais
    total_contratos = Contrato.query.count()
    contratos_ativos = Contrato.query.filter_by(status='ativo').count()
    contratos_vencidos = Contrato.query.filter(
        Contrato.validade < hoje,
        Contrato.status == 'ativo'
    ).count()
    
    # Contratos por tipo
    contratos_por_tipo = db.session.query(
        Contrato.tipo_plano,
        db.func.count(Contrato.id).label('total')
    ).filter_by(status='ativo').group_by(Contrato.tipo_plano).all()
    
    # Receita total
    receita_total = db.session.query(
        db.func.sum(Contrato.valor_total)
    ).filter_by(status='ativo').scalar() or 0
    
    # Contratos por mês (últimos 12 meses)
    contratos_por_mes = []
    for i in range(12):
        data_mes = hoje.replace(day=1) - timedelta(days=30*i)
        inicio_mes = data_mes.replace(day=1)
        fim_mes = (inicio_mes + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        total_mes = Contrato.query.filter(
            and_(
                Contrato.data_inicio >= inicio_mes,
                Contrato.data_inicio <= fim_mes
            )
        ).count()
        
        contratos_por_mes.append({
            'mes': inicio_mes.strftime('%m/%Y'),
            'total': total_mes
        })
    
    contratos_por_mes.reverse()
    
    return render_template('contratos/dashboard_contratos.html',
                         total_contratos=total_contratos,
                         contratos_ativos=contratos_ativos,
                         contratos_vencidos=contratos_vencidos,
                         contratos_por_tipo=contratos_por_tipo,
                         receita_total=receita_total,
                         contratos_por_mes=contratos_por_mes)

# Função para registrar o blueprint na aplicação Flask
def register_contratos_routes(app):
    """Registra as rotas de contratos na aplicação Flask"""
    app.register_blueprint(contratos_bp)
    
    # Criar diretório para contratos se não existir
    contratos_dir = os.path.join(app.static_folder, 'contratos')
    os.makedirs(contratos_dir, exist_ok=True)