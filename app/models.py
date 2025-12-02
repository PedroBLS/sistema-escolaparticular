from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from sqlalchemy import func, Date

# Tabela de associação para Contrato e Aluno (muitos-para-muitos)
contrato_aluno_associacao = db.Table(
    'contrato_aluno_associacao',
    db.Column('contrato_id', db.Integer, db.ForeignKey('contrato.id'), primary_key=True),
    db.Column('aluno_id', db.Integer, db.ForeignKey('aluno.id'), primary_key=True)
)

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    # Dados de autenticação
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)  # Mantido sem default para obrigar preenchimento
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'aluno', 'professor', 'admin', 'responsavel'
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relacionamentos (1:1 com Aluno/Professor/Responsavel)
    aluno_id = db.Column(db.Integer, db.ForeignKey('aluno.id', ondelete='CASCADE'), nullable=True)
    professor_id = db.Column(db.Integer, db.ForeignKey('professor.id', ondelete='CASCADE'), nullable=True)
    responsavel_id = db.Column(db.Integer, db.ForeignKey('responsavel.id', ondelete='CASCADE'), nullable=True)

    # Relacionamentos com validação de integridade
    aluno = db.relationship('Aluno', back_populates='user', uselist=False, 
                          foreign_keys=[aluno_id])
    professor = db.relationship('Professor', back_populates='user', uselist=False,
                              foreign_keys=[professor_id])
    responsavel = db.relationship('Responsavel', back_populates='user', uselist=False,
                                foreign_keys=[responsavel_id])

    def __init__(self, **kwargs):
        # Validação durante a criação do objeto
        if 'nome' not in kwargs or not kwargs['nome']:
            raise ValueError("O campo 'nome' é obrigatório")
        if 'email' not in kwargs:
            raise ValueError("O campo 'email' é obrigatório")
        
        super().__init__(**kwargs)

    def set_password(self, password):
        """Método seguro para definir senha com validações"""
        if not password:
            raise ValueError('A senha não pode ser vazia')
        if len(password) < 8:
            raise ValueError('A senha deve ter pelo menos 8 caracteres')
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifica a senha com tratamento seguro"""
        if not password or not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    @property
    def password(self):
        raise AttributeError('A senha não é um atributo legível')

    @password.setter
    def password(self, password):
        """Setter que usa o método set_password validado"""
        self.set_password(password)

    def __repr__(self):
        return f'<User {self.id}: {self.email}>'

    @staticmethod
    def validate_email(email):
        """Validação robusta de email"""
        if not email or '@' not in email:
            return False
        return not db.session.query(
    db.exists().where(func.lower(User.email) == func.lower(email))
).scalar()


    @classmethod
    def create(cls, **kwargs):
        """Método factory para criação segura de usuários"""
        try:
            user = cls(**kwargs)
            db.session.add(user)
            db.session.commit()
            return user
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Erro ao criar usuário: {str(e)}")

    def update_last_login(self):
        """Atualiza o último login com tratamento de timezone"""
        self.last_login = datetime.utcnow()
        db.session.commit()

class Responsavel(db.Model):
    __tablename__ = 'responsavel'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    rg = db.Column(db.String(20), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    endereco = db.Column(db.String(200), nullable=False)
    estado_civil = db.Column(db.String(20), default='')
    nacionalidade = db.Column(db.String(50), default='')
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='responsavel', uselist=False)
    alunos = db.relationship('Aluno', back_populates='responsavel', lazy='dynamic')
    contratos = db.relationship('Contrato', back_populates='responsavel', lazy='dynamic')

    def __repr__(self):
        return f'<Responsavel {self.nome}>'

    @staticmethod
    def validate_cpf(cpf):
        return not db.session.query(db.exists().where(Responsavel.cpf == cpf)).scalar()

class Aluno(db.Model):
    __tablename__ = 'aluno'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    responsavel_id = db.Column(db.Integer, db.ForeignKey('responsavel.id'), nullable=True)
    endereco = db.Column(db.String(200), nullable=False)
    mora_plano_piloto = db.Column(db.Boolean, default=False)
    rg = db.Column(db.String(20), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    estado_civil = db.Column(db.String(20), default='')
    nacionalidade = db.Column(db.String(50), default='')
    serie = db.Column(db.String(30), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    plano_adquirido = db.Column(db.String(50), default='')
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='aluno', uselist=False)
    responsavel = db.relationship('Responsavel', back_populates='alunos')
    aulas = db.relationship('Aula', backref='aluno_rel', lazy=True)
    contratos = db.relationship('ContratoAluno', back_populates='aluno')

    def __repr__(self):
        return f'<Aluno {self.nome}>'

    @staticmethod
    def validate_cpf(cpf):
        return not db.session.query(db.exists().where(Aluno.cpf == cpf)).scalar()


class Professor(db.Model):
    __tablename__ = 'professor'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    nacionalidade = db.Column(db.String(50), default='')
    estado_civil = db.Column(db.String(20), default='')
    rg = db.Column(db.String(20), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    endereco = db.Column(db.String(200), nullable=False)
    banco = db.Column(db.String(50), default='')
    agencia = db.Column(db.String(10), default='')
    conta = db.Column(db.String(15), default='')
    pix = db.Column(db.String(100), default='')
    telefone = db.Column(db.String(20), nullable=False)
    disciplina = db.Column(db.String(50), nullable=False)
    disponibilidade = db.Column(db.String(200), default='')
    valor_hora = db.Column(db.Float, default=0.0)
    tipo_atendimento = db.Column(db.String(50), default='presencial')
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='professor', uselist=False)
    aulas = db.relationship('Aula', backref='professor_rel', lazy=True)
    contratos = db.relationship('Contrato', back_populates='professor', lazy='dynamic')
    materias = db.relationship('ProfessorMateria', back_populates='professor')

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __repr__(self):
        return f'<Professor {self.nome}>'

    @staticmethod
    def validate_cpf(cpf):
        return not db.session.query(db.exists().where(Professor.cpf == cpf)).scalar()


class Aula(db.Model):
    __tablename__ = 'aula'

    id = db.Column(db.Integer, primary_key=True)
    aluno_id = db.Column(db.Integer, db.ForeignKey('aluno.id'), nullable=False)
    professor_id = db.Column(db.Integer, db.ForeignKey('professor.id'), nullable=False)
    data_hora = db.Column(db.DateTime, nullable=False)
    duracao = db.Column(db.Integer, nullable=False)  # em minutos
    local = db.Column(db.String(50), nullable=False)
    tipo_aula = db.Column(db.String(20), nullable=False)
    realizada = db.Column(db.Boolean, default=False, nullable=False)
    materia_id = db.Column(db.Integer, db.ForeignKey('materia.id'), nullable=True)

    valor_aula = db.Column(db.Float, nullable=False, default=0.0)  # Valor cobrado ao aluno
    custo_aula = db.Column(db.Float, nullable=False, default=0.0)  # Custo com o professor
    deslocamento = db.Column(db.Float, default=0.0)  # Custo de deslocamento se houver
    observacoes = db.Column(db.Text)  # Para anotações adicionais

    recorrente = db.Column(db.Boolean, default=False)
    frequencia = db.Column(db.Integer)  # 1 = semanal, 2 = quinzenal
    dias_semana = db.Column(db.String(50))  # Ex: "2,4" (terça e quinta)
    data_fim = db.Column(db.DateTime)
    aula_principal_id = db.Column(db.Integer, db.ForeignKey('aula.id'))

    aulas_relacionadas = db.relationship('Aula', backref=db.backref('aula_principal', remote_side=[id]))
    materia = db.relationship('Materia', back_populates='aulas')

    def __repr__(self):
        return f'<Aula {self.id} - {self.data_hora}>'


class Materia(db.Model):
    __tablename__ = 'materia'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    codigo = db.Column(db.String(20), unique=True)  # Ex: "MAT-101"
    descricao = db.Column(db.Text)
    carga_horaria = db.Column(db.Integer)  # Em horas
    ativa = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    aulas = db.relationship('Aula', back_populates='materia', lazy='dynamic')
    professores = db.relationship('ProfessorMateria', back_populates='materia')
    
    def __init__(self, **kwargs):
        super(Materia, self).__init__(**kwargs)
        if not self.codigo:
            self.codigo = self.gerar_codigo()
    
    def gerar_codigo(self):
        """Gera um código automático baseado no nome"""
        prefixo = ''.join([p[0].upper() for p in self.nome.split()[:3]])
        return f"{prefixo}-{self.id:03d}" if self.id else prefixo
    
    def to_dict(self):
        """Converte o objeto para dicionário (útil para APIs)"""
        return {
            'id': self.id,
            'nome': self.nome,
            'codigo': self.codigo,
            'descricao': self.descricao,
            'carga_horaria': self.carga_horaria,
            'ativa': self.ativa,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None
        }
    
    def __repr__(self):
        return f'<Materia {self.codigo}: {self.nome}>'


# Tabela de associação para relacionamento muitos-para-muitos entre Professor e Materia
class ProfessorMateria(db.Model):
    __tablename__ = 'professor_materia'
    
    professor_id = db.Column(db.Integer, db.ForeignKey('professor.id'), primary_key=True)
    materia_id = db.Column(db.Integer, db.ForeignKey('materia.id'), primary_key=True)
    data_associacao = db.Column(db.DateTime, default=datetime.utcnow)
    principal = db.Column(db.Boolean, default=False)
    
    # Relacionamentos
    professor = db.relationship('Professor', back_populates='materias')
    materia = db.relationship('Materia', back_populates='professores')
    
    def __repr__(self):
        return f'<ProfessorMateria {self.professor_id}-{self.materia_id}>'

# Tabela de associação para relacionamento muitos-para-muitos entre Contrato e Aluno
class ContratoAluno(db.Model):
    __tablename__ = 'contrato_aluno'
    
    contrato_id = db.Column(db.Integer, db.ForeignKey('contrato.id'), primary_key=True)
    aluno_id = db.Column(db.Integer, db.ForeignKey('aluno.id'), primary_key=True)
    data_associacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    contrato = db.relationship('Contrato', back_populates='alunos')
    aluno = db.relationship('Aluno', back_populates='contratos')
    
    def __repr__(self):
        return f'<ContratoAluno {self.contrato_id}-{self.aluno_id}>'

class Contrato(db.Model):
    __tablename__ = 'contrato'

    id = db.Column(db.Integer, primary_key=True)
    responsavel_id = db.Column(db.Integer, db.ForeignKey('responsavel.id'), nullable=False)
    professor_id = db.Column(db.Integer, db.ForeignKey('professor.id'), nullable=True)
    arquivo = db.Column(db.String(200), nullable=True)
    validade = db.Column(db.Date, nullable=False)
    tipo_plano = db.Column(db.String(50), nullable=False)
    data_inicio = db.Column(db.Date, nullable=False)
    valor_total = db.Column(db.Float, nullable=False)
    servicos_incluidos = db.Column(db.Text, nullable=True)
    assinatura = db.Column(db.Boolean, default=False)
    observacoes = db.Column(db.Text)
    data_upload = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='ativo')  # ativo, vencido, cancelado

# Relacionamentos
    responsavel = db.relationship('Responsavel', back_populates='contratos')
    professor = db.relationship('Professor', back_populates='contratos')
    alunos = db.relationship('ContratoAluno', back_populates='contrato')
    @property
    def dias_para_vencimento(self):
        """Calcula quantos dias faltam para o vencimento"""
        from datetime import date
        if self.validade:
            delta = self.validade - date.today()
            return delta.days
        return None
    
    @property
    def esta_vencido(self):
        """Verifica se o contrato está vencido"""
        from datetime import date
        return self.validade < date.today() if self.validade else False
    
    @property
    def vence_em_30_dias(self):
        """Verifica se o contrato vence nos próximos 30 dias"""
        dias = self.dias_para_vencimento
        return dias is not None and 0 <= dias <= 30

    def __repr__(self):
        return f'<Contrato {self.id}>'

class Notificacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    titulo = db.Column(db.String(100), nullable=False)
    mensagem = db.Column(db.Text, nullable=False)
    tipo = db.Column(db.String(20), default='info')
    lida = db.Column(db.Boolean, default=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamento
    usuario = db.relationship('User', backref='notificacoes')

    def __repr__(self):
        return f'<Notificacao {self.titulo}>'

class Documento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    aluno_id = db.Column(db.Integer, db.ForeignKey('aluno.id'), nullable=False)
    nome = db.Column(db.String(255), nullable=False)
    caminho = db.Column(db.String(512), nullable=False)
    tipo = db.Column(db.String(50)) 
    tamanho = db.Column(db.Integer) 
    upload_por = db.Column(db.Integer, db.ForeignKey('users.id'))
    data_upload = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    aluno = db.relationship('Aluno', backref='documentos')
    usuario = db.relationship('User', foreign_keys=[upload_por])

    def __repr__(self):
        return f'<Documento {self.nome}>'