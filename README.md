# Tibia PT Manager

Sistema web para organizar monstros, charms, hunts e imbuements de uma party de Tibia.

## Tecnologias

- Python 3.13
- Flask 3.1
- Bootstrap 5.3
- SQLAlchemy 2
- PostgreSQL Neon em produção
- SQLite como fallback local
- Deploy preparado para Vercel

## Funcionalidades

- CRUD de monstros com EXP, life, imagem, fraquezas percentuais e ataques por elemento.
- CRUD de charms Major e Minor.
- CRUD de hunts com localização, proteções, fraquezas, monstros e charms.
- Visualização detalhada da hunt, exibindo imagem, EXP, life, fraquezas e ataques de cada monstro.
- CRUD de imbuements com níveis Basic, Intricate e Powerful.
- Quantidade automática de materiais: 1, 2 ou 3 conforme o nível.
- Interface responsiva inspirada na estética medieval do jogo.

## Rodando localmente

### Windows PowerShell

```powershell
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env
python main.py
```

### Linux ou WSL

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
flask --app main.py run --host=0.0.0.0 --port=5000 --debug --no-reload
python main.py
```

Abra `http://127.0.0.1:5000`.

Sem `DATABASE_URL`, o sistema cria automaticamente um banco SQLite local em `instance/tibia_pt.db`.

## Configurando o PostgreSQL Neon

1. Crie um projeto no Neon.
2. No painel do projeto, clique em **Connect**.
3. Copie a connection string do PostgreSQL.
4. Crie o arquivo `.env` e informe:

```env
SECRET_KEY=uma-chave-secreta-forte
DATABASE_URL=postgresql://usuario:senha@host.neon.tech/neondb?sslmode=require
```

As tabelas são criadas automaticamente na primeira execução.

## Publicando na Vercel

1. Envie o projeto para um repositório GitHub.
2. Importe o repositório na Vercel.
3. Em **Settings > Environment Variables**, adicione:
   - `DATABASE_URL`
   - `SECRET_KEY`
4. Faça o deploy.

Também é possível usar a CLI:

```bash
npm install -g vercel
vercel
vercel --prod
```

## Estrutura

```text
.
├── app.py
├── main.py
├── models.py
├── routes.py
├── requirements.txt
├── runtime.txt
├── vercel.json
├── static/
│   ├── css/style.css
│   └── js/app.js
└── templates/
    ├── base.html
    ├── dashboard.html
    ├── monsters/
    ├── charms/
    ├── hunts/
    └── imbuements/
```

## Observação

Este é um projeto de comunidade, não oficial, sem vínculo com a CipSoft GmbH.

## Área administrativa

O site possui dois níveis de acesso:

- **Membro:** pode visualizar e pesquisar monstros, charms, hunts e imbuements.
- **Administrador:** pode criar, editar e excluir todos os registros.

Acesse a tela administrativa em `/admin/login` ou pelo botão **Entrar** no menu.

Configure no arquivo `.env` local e nas variáveis de ambiente da Vercel:

```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=uma-senha-forte
SECRET_KEY=uma-chave-longa-e-aleatoria
```

Para não armazenar a senha em texto simples, você também pode configurar `ADMIN_PASSWORD_HASH`:

```bash
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('sua-senha'))"
```

Depois, salve o resultado em `ADMIN_PASSWORD_HASH` e remova `ADMIN_PASSWORD`.
