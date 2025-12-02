# Sistema de Aulas Particulares - Impetus
![Sistema Impetus](https://github.com/user-attachments/assets/cbe25afa-75db-467a-b366-35a2c6347d73)

## 📋 Descrição

Sistema de gestão para aulas particulares desenvolvido para a empresa **Impetus**. A plataforma facilita o gerenciamento de alunos, professores, aulas e atividades educacionais, proporcionando uma interface intuitiva para administradores.

**⚠️ ATENÇÃO:** Sistema em fase de desenvolvimento - novas funcionalidades sendo implementadas.

## ✨ Funcionalidades

### ✅ Implementadas
- **Autenticação de Usuários**: Login com roles (admin, professor, aluno)
- **CRUD de Alunos**: Cadastro, edição e visualização
- **CRUD de Professores**: Gerenciamento de docentes
- **Controle de Aulas**: Agendamento e registro
- **Dashboard Administrativo**: Visão geral do sistema
- **Geração de Relatórios**: Em PDF com ReportLab

### 🚧 Em Desenvolvimento
- Sistema de pagamentos e financeiro
- Notificações por e-mail
- Dashboard para professores e alunos
- Calendário interativo
- API REST para integrações

## 🛠️ Tecnologias Utilizadas

### Backend
- **Python 3.8+**
- **Flask 3.0.0** - Framework web
- **Flask-SQLAlchemy** - ORM para banco de dados
- **Flask-Migrate** - Migrações de banco de dados
- **Flask-Login** - Gerenciamento de sessões
- **Flask-WTF** - Formulários e validação

### Banco de Dados
- **SQLite** (desenvolvimento)
- **SQLAlchemy** (ORM)

### Frontend
- **HTML5, CSS3, JavaScript**
- **Flask-Bootstrap** - Interface responsiva
- **Jinja2** - Templates

### Relatórios
- **ReportLab** - Geração de PDFs
- **WeasyPrint** - Conversão HTML para PDF

### Outras
- **python-dotenv** - Variáveis de ambiente
- **email-validator** - Validação de e-mails

## 🚀 Instalação e Configuração

### Pré-requisitos
- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

### Passos para Instalação

**Clone o repositório**
```bash
git clone https://github.com/PedroBLS/sistema-escolaparticular.git
cd impetus-educacional

Crie um ambiente virtual (recomendado)
bash
# Linux/Mac
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
Instale as dependências

bash
pip install -r requirements.txt
Configure as variáveis de ambiente


bash
# Crie um arquivo .env na raiz do projeto
cp .env.example .env  # Se tiver exemplo
# Ou crie manualmente:
echo "FLASK_APP=run.py" > .env
echo "FLASK_ENV=development" >> .env
echo "SECRET_KEY=sua_chave_secreta_aqui" >> .env
Inicialize o banco de dados

bash
python initiative_db.py
Isso criará as tabelas e um usuário admin padrão:

Email: admin@escola.com

Senha: admin123

Execute a aplicação

bash
python run.py
# ou
flask run
Acesse no navegador

URL: http://localhost:5000

Admin: admin@escola.com / admin123

📁 Estrutura do Projeto
text
impetus-educacional/
├── app/
│   ├── __init__.py          # Factory do Flask
│   ├── models.py            # Modelos do banco de dados
│   ├── routes.py            # Rotas da aplicação
│   ├── forms.py             # Formulários WTForms
│   ├── templates/           # Templates HTML (Jinja2)
│   │   ├── base.html        # Template base
│   │   ├── auth/            # Templates de autenticação
│   │   ├── admin/           # Templates administrativos
│   │   └── ...
│   └── static/              # Arquivos estáticos
│       ├── css/
│       ├── js/
│       └── images/
├── migrations/              # Migrações do Flask-Migrate
├── .env                     # Variáveis de ambiente (NÃO COMMITAR)
├── .env.example             # Exemplo de variáveis
├── .gitignore              # Arquivos ignorados pelo Git
├── config.py               # Configuração do Flask
├── initiative_db.py        # Inicialização do banco
├── requirements.txt        # Dependências do Python
├── run.py                  # Ponto de entrada
└── README.md               # Este arquivo

🔐 Credenciais Padrão
Após executar initiative_db.py, um usuário admin é criado:

Email: admin@escola.com

Senha: admin123

⚠️ IMPORTANTE: Altere estas credenciais imediatamente após o primeiro login em produção!

🗄️ Comandos Úteis
Desenvolvimento
bash
# Executar aplicação
python run.py

# Modo desenvolvimento com auto-reload
flask run --debug

# Criar migrações (após alterar models.py)
flask db migrate -m "Descrição da migração"

# Aplicar migrações
flask db upgrade
Banco de Dados
bash
# Reiniciar banco (CUIDADO: apaga todos os dados)
python initiative_db.py

# Shell interativo do Flask
flask shell
