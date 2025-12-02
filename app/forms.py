from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, BooleanField, SelectField, 
    TextAreaField, DateField, FloatField, IntegerField,
    TimeField, FileField, SubmitField, SelectMultipleField
)
from wtforms.validators import (
    DataRequired, Email, Length, EqualTo, 
    ValidationError, Optional, NumberRange
)
from flask_wtf.file import FileAllowed
from datetime import datetime, date
import re
from wtforms import DateTimeField
from wtforms.widgets import CheckboxInput, ListWidget 

# ========= Formulário para Responsável =========
class ResponsavelForm(FlaskForm):
    nome = StringField('Nome Completo', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=8)])
    confirmar_senha = PasswordField('Confirmar Senha', 
                                  validators=[DataRequired(), EqualTo('password')])
    cpf = StringField('CPF', validators=[DataRequired(), Length(min=11, max=11)])
    rg = StringField('RG', validators=[DataRequired()])
    telefone = StringField('Telefone', validators=[DataRequired()])
    endereco = StringField('Endereço', validators=[DataRequired()])
    estado_civil = SelectField('Estado Civil', choices=[
        ('solteiro', 'Solteiro(a)'),
        ('casado', 'Casado(a)'),
        ('divorciado', 'Divorciado(a)'),
        ('viuvo', 'Viúvo(a)')
    ], validators=[DataRequired()])
    nacionalidade = StringField('Nacionalidade', default='Brasileira')
    submit = SubmitField('Cadastrar')

    def validate_cpf(self, cpf):
        from app.models import Responsavel
        responsavel = Responsavel.query.filter_by(cpf=cpf.data).first()
        if responsavel:
            raise ValidationError('Este CPF já está cadastrado.')

    def validate_email(self, email):
        from app.models import Responsavel
        responsavel = Responsavel.query.filter_by(email=email.data).first()
        if responsavel:
            raise ValidationError('Este email já está cadastrado.')

# ========= Formulário para Professor =========
class ProfessorForm(FlaskForm):
    nome = StringField('Nome Completo', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=8)])
    confirmar_senha = PasswordField('Confirmar Senha', 
                                  validators=[DataRequired(), EqualTo('password')])
    cpf = StringField('CPF', validators=[DataRequired()])
    rg = StringField('RG', validators=[DataRequired()])
    disciplina = StringField('Disciplina', validators=[DataRequired()])
    telefone = StringField('Telefone', validators=[DataRequired()])
    endereco = StringField('Endereço', validators=[DataRequired()])
    nacionalidade = StringField('Nacionalidade')
    estado_civil = StringField('Estado Civil')
    banco = StringField('Banco')
    agencia = StringField('Agência')
    conta = StringField('Conta')
    pix = StringField('Chave PIX')
    disponibilidade = StringField('Disponibilidade')
    valor_hora = FloatField('Valor por Hora')
    tipo_atendimento = SelectField('Tipo de Atendimento', 
                                 choices=[('presencial', 'Presencial'), 
                                         ('online', 'Online'), 
                                         ('ambos', 'Ambos')
                                ],
                                default='presencial')
    submit = SubmitField('Cadastrar')

    def validate_email(self, email):
        from app.models import Professor  # Importação local aqui
        professor = Professor.query.filter_by(email=email.data).first()
        if professor is not None:
            raise ValidationError('Este email já está cadastrado. Use um email diferente.')

    def validate_cpf(self, cpf):
        from app.models import Professor  # Importação local aqui
        professor = Professor.query.filter_by(cpf=cpf.data).first()
        if professor is not None:
            raise ValidationError('Este CPF já está cadastrado.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired()])
    remember = BooleanField('Lembrar-me')

class RegistrationForm(FlaskForm):
    # ========= Dados Básicos (User) =========
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[
        DataRequired(),
        Length(min=6, message='A senha deve ter pelo menos 6 caracteres'),
        EqualTo('confirm_password', message='As senhas devem ser iguais')
    ])
    confirm_password = PasswordField('Confirmar Senha')
    user_type = SelectField('Tipo de Usuário', 
                          choices=[('', 'Selecione...'), ('aluno', 'Aluno'), ('professor', 'Professor'), ('responsavel', 'Responsável')],
                          validators=[DataRequired()])

    # ========= Dados de Aluno =========
    aluno_nome = StringField('Nome Completo', validators=[
        Length(min=2, max=100, message='O nome deve ter entre 2 e 100 caracteres')
    ])
    aluno_cpf = StringField('CPF (apenas números)', validators=[
        Length(min=11, max=11, message='CPF deve ter 11 dígitos')
    ])
    aluno_endereco = StringField('Endereço', validators=[
        Length(max=200, message='Máximo de 200 caracteres'), 
        Optional()
    ])
    aluno_mora_plano_piloto = BooleanField('Mora no Plano Piloto?')
    aluno_rg = StringField('RG', validators=[
        Length(max=20, message='Máximo de 20 caracteres'), 
        Optional()
    ])
    aluno_estado_civil = SelectField('Estado Civil', choices=[
        ('', 'Selecione...'), 
        ('solteiro', 'Solteiro(a)'), 
        ('casado', 'Casado(a)'), 
        ('divorciado', 'Divorciado(a)'),
        ('viuvo', 'Viúvo(a)')
    ], validators=[Optional()])
    aluno_nacionalidade = StringField('Nacionalidade', validators=[
        Length(max=50, message='Máximo de 50 caracteres'), 
        Optional()
    ])
    aluno_serie = SelectField('Série/Ano', choices=[
        ('', 'Selecione...'),
        ('1ano', '1º Ano'),
        ('2ano', '2º Ano'),
        ('3ano', '3º Ano'),
        ('4ano', '4º Ano'),
        ('5ano', '5º Ano'),
        ('6ano', '6º Ano'),
        ('7ano', '7º Ano'),
        ('8ano', '8º Ano'),
        ('9ano', '9º Ano'),
        ('1EM', '1º Ensino Médio'),
        ('2EM', '2º Ensino Médio'),
        ('3EM', '3º Ensino Médio'),
        # ... adicione outras séries conforme necessário
    ], validators=[Optional()])
    aluno_telefone = StringField('Telefone', validators=[
        Length(max=20, message='Máximo de 20 caracteres'), 
        Optional()
    ])
    aluno_plano_adquirido = SelectField('Plano Adquirido', choices=[
        ('', 'Selecione...'),
        ('basico', 'Básico'),
        ('intermediario', 'Intermediário'),
        ('avancado', 'Avançado')
    ], validators=[Optional()])

    # ========= Dados de Professor =========
    professor_nome = StringField('Nome Completo', validators=[
        Length(min=2, max=100, message='O nome deve ter entre 2 e 100 caracteres')
    ])
    professor_cpf = StringField('CPF (apenas números)', validators=[
        Length(min=11, max=11, message='CPF deve ter 11 dígitos')
    ])
    professor_disciplina = SelectField('Disciplina Principal', choices=[
        ('', 'Selecione...'),
        ('matematica', 'Matemática'),
        ('portugues', 'Português'),
        ('historia', 'História'),
        ('geografia', 'Geografia'),
        ('ciencias', 'Ciências'),
        ('historia', 'História'),
        ('quimica', 'Química'),
        ('fisica', 'Física'),
        ('biologia', 'Biologia'),
        ('filosofia', 'Filosofia'),
        ('sociologia', 'Sociologia'),
        ('ingles', 'Inglês'),
        ('artes', 'Artes'),
        ('literatura', 'Literatura'),
        ('espanhol', 'Espanhol'),
        # ... adicione outras disciplinas
    ], validators=[Optional()])
    professor_nacionalidade = StringField('Nacionalidade', validators=[
        Length(max=50, message='Máximo de 50 caracteres'), 
        Optional()
    ])
    professor_estado_civil = SelectField('Estado Civil', choices=[
        ('', 'Selecione...'), 
        ('solteiro', 'Solteiro(a)'), 
        ('casado', 'Casado(a)'), 
        ('divorciado', 'Divorciado(a)'),
        ('viuvo', 'Viúvo(a)')
    ], validators=[Optional()])
    professor_rg = StringField('RG', validators=[
        Length(max=20, message='Máximo de 20 caracteres'), 
        Optional()
    ])
    professor_endereco = StringField('Endereço', validators=[
        Length(max=200, message='Máximo de 200 caracteres'), 
        Optional()
    ])
    professor_banco = StringField('Banco', validators=[
        Length(max=50, message='Máximo de 50 caracteres'), 
        Optional()
    ])
    professor_agencia = StringField('Agência', validators=[
        Length(max=10, message='Máximo de 10 caracteres'), 
        Optional()
    ])
    professor_conta = StringField('Conta', validators=[
        Length(max=15, message='Máximo de 15 caracteres'), 
        Optional()
    ])
    professor_pix = StringField('Chave PIX', validators=[
        Length(max=100, message='Máximo de 100 caracteres'), 
        Optional()
    ])
    professor_telefone = StringField('Telefone', validators=[
        Length(max=20, message='Máximo de 20 caracteres'), 
        Optional()
    ])
    professor_disponibilidade = TextAreaField('Disponibilidade', validators=[
        Length(max=200, message='Máximo de 200 caracteres'), 
        Optional()
    ])
    professor_valor_hora = FloatField('Valor por Hora (R$)', validators=[
        NumberRange(min=0, message='O valor não pode ser negativo'), 
        Optional()
    ])
    professor_tipo_atendimento = SelectField('Tipo de Atendimento', choices=[
        ('', 'Selecione...'),
        ('presencial', 'Presencial'),
        ('online', 'Online'),
        ('domicílio', 'Domicílio'),
        ('ambos', 'Ambos')
    ], validators=[Optional()])

    # ========= Dados de Responsável =========
    responsavel_nome = StringField('Nome Completo', validators=[
        Length(min=2, max=100, message='O nome deve ter entre 2 e 100 caracteres')
    ])
    responsavel_cpf = StringField('CPF (apenas números)', validators=[
        Length(min=11, max=11, message='CPF deve ter 11 dígitos')
    ])
    responsavel_rg = StringField('RG', validators=[
        Length(max=20, message='Máximo de 20 caracteres'), 
        Optional()
    ])
    responsavel_telefone = StringField('Telefone', validators=[
        Length(max=20, message='Máximo de 20 caracteres'), 
        Optional()
    ])
    responsavel_endereco = StringField('Endereço', validators=[
        Length(max=200, message='Máximo de 200 caracteres'), 
        Optional()
    ])
    responsavel_estado_civil = SelectField('Estado Civil', choices=[
        ('', 'Selecione...'), 
        ('solteiro', 'Solteiro(a)'), 
        ('casado', 'Casado(a)'), 
        ('divorciado', 'Divorciado(a)'),
        ('viuvo', 'Viúvo(a)')
    ], validators=[Optional()])
    responsavel_nacionalidade = StringField('Nacionalidade', validators=[
        Length(max=50, message='Máximo de 50 caracteres'), 
        Optional()
    ])

    # ========= Validações Personalizadas =========
    def validate_email(self, email):
        from app.models import User
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email já cadastrado. Use outro email ou faça login.')

    def validate_aluno_cpf(self, field):
        if self.user_type.data == 'aluno':
            if not field.data.isdigit():
                raise ValidationError('CPF deve conter apenas números')
            if len(field.data) != 11:
                raise ValidationError('CPF deve ter 11 dígitos')

    def validate_professor_cpf(self, field):
        if self.user_type.data == 'professor':
            if not field.data.isdigit():
                raise ValidationError('CPF deve conter apenas números')
            if len(field.data) != 11:
                raise ValidationError('CPF deve ter 11 dígitos')

    def validate_aluno_telefone(self, field):
        if field.data and not re.match(r'^[\d\s\(\)\-]+$', field.data):
            raise ValidationError('Telefone contém caracteres inválidos')

    def validate_professor_telefone(self, field):
        if field.data and not re.match(r'^[\d\s\(\)\-]+$', field.data):
            raise ValidationError('Telefone contém caracteres inválidos')

# ========= Formulários para Cadastro/Edição de alunos =========
class AlunoForm(FlaskForm):
    nome_aluno = StringField('Nome do Aluno', validators=[DataRequired()])
    serie = SelectField('Série/Ano', choices=[
        ('', 'Selecione...'),
        ('1ano', '1º Ano'),
        ('2ano', '2º Ano'),
        ('3ano', '3º Ano'),
        ('4ano', '4º Ano'),
        ('5ano', '5º Ano'),
        ('6ano', '6º Ano'),
        ('7ano', '7º Ano'),
        ('8ano', '8º Ano'),
        ('9ano', '9º Ano'),
        ('1EM', '1º Ensino Médio'),
        ('2EM', '2º Ensino Médio'),
        ('3EM', '3º Ensino Médio'),
        ('outro', 'Outro')
    ], validators=[DataRequired()])
    mora_plano_piloto = BooleanField('Mora no Plano Piloto?')

    # ========= Dados do Responsável =========
    nome_responsavel = StringField('Nome do Responsável', validators=[DataRequired()])
    email_responsavel = StringField('Email do Responsável', validators=[DataRequired(), Email()])
    telefone_responsavel = StringField('Telefone do Responsável', validators=[DataRequired()])
    endereco_responsavel = StringField('Endereço do Responsável', validators=[DataRequired()])
    cpf_responsavel = StringField('CPF do Responsável', validators=[DataRequired(), Length(min=11, max=11)])
    rg_responsavel = StringField('RG do Responsável', validators=[DataRequired()])
    estado_civil_responsavel = SelectField('Estado Civil do Responsável', choices=[
        ('', 'Selecione...'),
        ('solteiro', 'Solteiro(a)'),
        ('casado', 'Casado(a)'),
        ('divorciado', 'Divorciado(a)'),
        ('viuvo', 'Viúvo(a)')
    ], validators=[DataRequired()])
    nacionalidade_responsavel = StringField('Nacionalidade do Responsável', default='Brasileira')

    # ========= Plano =========
    plano_adquirido = SelectField('Plano Adquirido', choices=[
        ('', 'Selecione um plano'),
        # Aulas Particulares
        ('1h de aula', '1h de aula'),
        ('1h30 de aula', '1h30 de aula'),
        ('2h de aula', '2h de aula'),
        # Pacotes Pré-Pagos Flexíveis
        ('10 aulas (6 meses)', '10 aulas (válido por 6 meses)'),
        ('20 aulas (12 meses)', '20 aulas (válido por 12 meses)'),
        ('30 aulas (12 meses)', '30 aulas (válido por 12 meses)'),
        # Aulas para 2 Alunos (Compartilhada)
        ('1h compartilhada', '1h compartilhada'),
        ('1h30 compartilhada', '1h30 compartilhada'),
        ('2h compartilhada', '2h compartilhada'),
        # Aulas em Grupo (3 a 5 alunos)
        ('1h em grupo', '1h em grupo'),
        ('1h30 em grupo', '1h30 em grupo'),
        ('2h em grupo', '2h em grupo'),
        # Planos para Duplas (2 alunos - 6 meses)
        ('4 aulas/mês (1h/semana) - Dupla', '4 aulas/mês (1h/semana)'),
        ('4 aulas/mês (1h30/semana) - Dupla', '4 aulas/mês (1h30/semana)'),
        ('8 aulas/mês (2x/semana - 1h) - Dupla', '8 aulas/mês (2x/semana - 1h)'),
        ('8 aulas/mês (2x/semana - 1h30) - Dupla', '8 aulas/mês (2x/semana - 1h30)'),
        ('12 aulas/mês (3x/semana - 1h) - Dupla', '12 aulas/mês (3x/semana - 1h)'),
        ('12 aulas/mês (3x/semana - 1h30) - Dupla', '12 aulas/mês (3x/semana - 1h30)'),
        ('16 aulas/mês (4x/semana - 1h) - Dupla', '16 aulas/mês (4x/semana - 1h)'),
        ('16 aulas/mês (4x/semana - 1h30) - Dupla', '16 aulas/mês (4x/semana - 1h30)'),
        # Planos para Grupos (3 a 5 alunos - 6 meses)
        ('4 aulas/mês (1h/semana) - Grupo', '4 aulas/mês (1h/semana)'),
        ('4 aulas/mês (1h30/semana) - Grupo', '4 aulas/mês (1h30/semana)'),
        ('8 aulas/mês (2x/semana - 1h) - Grupo', '8 aulas/mês (2x/semana - 1h)'),
        ('8 aulas/mês (2x/semana - 1h30) - Grupo', '8 aulas/mês (2x/semana - 1h30)'),
        ('12 aulas/mês (3x/semana - 1h) - Grupo', '12 aulas/mês (3x/semana - 1h)'),
        ('12 aulas/mês (3x/semana - 1h30) - Grupo', '12 aulas/mês (3x/semana - 1h30)'),
        ('16 aulas/mês (4x/semana - 1h) - Grupo', '16 aulas/mês (4x/semana - 1h)'),
        ('16 aulas/mês (4x/semana - 1h30) - Grupo', '16 aulas/mês (4x/semana - 1h30)'),
        # Assinatura Gold
        ('Assinatura Gold', 'Assinatura Gold'),
        # Psicopedagogia
        ('Avaliação Psicopedagógica', 'Avaliação Psicopedagógica'),
        ('4 sessões/mês - Psicopedagogia', '4 sessões/mês'),
        ('8 sessões/mês - Psicopedagogia', '8 sessões/mês')
    ], validators=[DataRequired()])
    responsavel_id = SelectField('Responsável', coerce=int, validators=[Optional()])
    submit = SubmitField('Cadastrar Aluno')  # Mudei de 'Salvar' para 'Cadastrar Aluno'

    def __init__(self, *args, **kwargs):
        super(AlunoForm, self).__init__(*args, **kwargs)
        from app.models import Responsavel
        self.responsavel_id.choices = [(0, 'Selecione um responsável')] + [
            (r.id, r.nome) for r in Responsavel.query.all()
        ]

    def validate_cpf_responsavel(self, cpf_responsavel):
        from app.models import Responsavel
        responsavel = Responsavel.query.filter_by(cpf=cpf_responsavel.data).first()
        if responsavel:
            raise ValidationError('Este CPF já está cadastrado para outro responsável.')

    def validate_email_responsavel(self, email_responsavel):
        from app.models import Responsavel
        responsavel = Responsavel.query.filter_by(email=email_responsavel.data).first()
        if responsavel:
            raise ValidationError('Este email já está cadastrado para outro responsável.')
            
# ========= Formulários para Aulas =========
class AulaForm(FlaskForm):
    from app.models import Aluno, Professor
    aluno_id = SelectField('Aluno', coerce=int, validators=[DataRequired()])
    professor_id = SelectField('Professor', coerce=int, validators=[DataRequired()])
    data_hora = DateTimeField('Data e Hora', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    duracao = IntegerField('Duração (minutos)', validators=[
        DataRequired(),
        NumberRange(min=30, max=240, message='Duração deve ser entre 30 e 240 minutos')
    ])
    local = StringField('Local', validators=[
        DataRequired(),
        Length(max=50, message='Máximo de 50 caracteres')
    ])
    tipo_aula = SelectField('Tipo de Aula', choices=[
        ('regular', 'Regular'),
        ('reforco', 'Reforço'),
        ('avaliacao', 'Avaliação')
    ], validators=[DataRequired()])

# Widget personalizado para múltipla seleção com checkboxes
class MultiCheckboxField(SelectMultipleField):
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()

# ========= Formulários para Contratos =========
class ContratoForm(FlaskForm):
    responsavel_id = SelectField('Responsável', coerce=int, validators=[DataRequired()])
    alunos_ids = MultiCheckboxField('Alunos', coerce=int, validators=[DataRequired()])
    professor_id = SelectField('Professor (opcional)', coerce=int, validators=[Optional()])
    arquivo = FileField('Arquivo do Contrato', validators=[
        FileAllowed(['pdf', 'doc', 'docx'], 'Apenas arquivos PDF ou Word')
    ])
    validade = DateField('Validade', format='%Y-%m-%d', validators=[DataRequired()])
    tipo_plano = SelectField('Tipo de Plano', choices=[
        ('aula_avulsa', 'Aula Avulsa'),
        ('aula_particular_grupo', 'Aula Particular em Grupo'),
        ('10_aulas', '10 Aulas Particulares'),
        ('20_aulas', '20 Aulas Particulares'),
        ('30_aulas', '30 Aulas Particulares'),
        ('assinatura_gold', 'Assinatura Gold'),
        ('prestacao_servico_professor', 'Prestação de Serviço - Professor')
    ], validators=[DataRequired()])
    data_inicio = DateField('Data de Início', format='%Y-%m-%d', validators=[DataRequired()], default=date.today)
    valor_total = FloatField('Valor Total (R$)', validators=[DataRequired(), NumberRange(min=0)])
    servicos_incluidos = TextAreaField('Serviços Incluídos')
    observacoes = TextAreaField('Observações', validators=[Optional()])
    assinatura = BooleanField('Contrato Assinado')
    submit = SubmitField('Salvar Contrato')

    def __init__(self, *args, **kwargs):
        super(ContratoForm, self).__init__(*args, **kwargs)
        from app.models import Responsavel, Aluno, Professor
        
        # Carrega responsáveis
        self.responsavel_id.choices = [(0, 'Selecione um responsável')] + [
            (r.id, r.nome) for r in Responsavel.query.all()
        ]
        
        # Carrega alunos
        self.alunos_ids.choices = [
            (a.id, a.nome) for a in Aluno.query.all()
        ]
        
        # Carrega professores
        self.professor_id.choices = [(0, 'Nenhum')] + [
            (p.id, p.nome) for p in Professor.query.all()
        ]

# ========= Formulário de Perfil =========
class PerfilForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    telefone = StringField('Telefone', validators=[DataRequired()])
    endereco = StringField('Endereço', validators=[DataRequired()])
    foto = FileField('Foto de Perfil', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'Apenas imagens JPG ou PNG')
    ])