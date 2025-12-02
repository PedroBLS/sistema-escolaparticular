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

1. **Clone o repositório**
```bash
git clone https://github.com/PedroBLS/sistema-escolaparticular.git
cd impetus-educacional
