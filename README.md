# Setlist Club API

API com FastAPI + MySQL + Redis para gestão de cifras e setlists.

---

## Pré-requisitos

- **Docker** e **Docker Compose** instalados
- **Python 3.11+** instalado localmente
- **pip** disponível no PATH

---

## 1. Subir MySQL e Redis com Docker

Execute a partir da **raiz do monorepo** (`/setlistclub`):

```bash
docker compose up -d mysql redis
```

Aguarde os serviços ficarem saudáveis (healthcheck automático):

```bash
docker compose ps
```

Serviços disponíveis:

| Serviço | Host            | Porta |
|---------|-----------------|-------|
| MySQL   | `localhost`     | 3306  |
| Redis   | `localhost`     | 6379  |

---

## 2. Configurar o ambiente da API

Entre na pasta da API:

```bash
cd setlistclub-api
```

Copie o arquivo de exemplo e ajuste as variáveis se necessário:

```bash
cp .env.example .env
```

> Para desenvolvimento local, o `.env.example` já aponta para `localhost:3306` e `localhost:6379`, então geralmente não precisa de alterações.

---

## 3. Configurar a versão do Python com pyenv

Se você usa **pyenv**, defina a versão correta dentro da pasta da API:

```bash
pyenv local 3.11.9
```

Confirme que está usando a versão certa:

```bash
python --version   # deve mostrar Python 3.11.x
```

---

## 4. Criar e ativar o ambiente virtual Python

```bash
python -m venv venv
source venv/bin/activate   # macOS / Linux
# ou
venv\Scripts\activate      # Windows
```

Após ativar, o prompt do terminal deve mostrar `(venv)`.

---

## 5. Instalar dependências

```bash
pip install -r requirements.txt
```

---

## 6. Iniciar a API

```bash
python -m uvicorn app.main:app --reload
```

> Use `python -m uvicorn` (em vez de apenas `uvicorn`) para garantir que o executável do venv ativo seja usado, evitando conflitos com pyenv.

A API estará disponível em: **http://localhost:8000**

> No primeiro start, a API cria automaticamente todas as tabelas no MySQL.

- Documentação Swagger: http://localhost:8000/docs
- Documentação Redoc: http://localhost:8000/redoc

---

## Comandos úteis do Docker

```bash
# Ver logs dos serviços
docker compose logs -f mysql redis

# Parar os serviços
docker compose down

# Parar e remover volumes (dados do banco)
docker compose down -v
```

---

## Endpoints principais

| Método | Endpoint                          | Auth |
|--------|-----------------------------------|------|
| POST   | `/api/v1/auth/register`           | Não  |
| POST   | `/api/v1/auth/login`              | Não  |
| GET    | `/api/v1/auth/google/url`         | Não  |
| POST   | `/api/v1/auth/google/callback`    | Não  |
| GET    | `/api/v1/chord-sheets`            | Não  |
| POST   | `/api/v1/chord-sheets`            | Sim  |
| GET    | `/api/v1/setlists`                | Não  |
| POST   | `/api/v1/setlists`                | Sim  |
| PUT    | `/api/v1/setlists/{id}/reorder`   | Sim  |

---

## Variáveis de ambiente (`.env`)

| Variável                      | Descrição                            | Padrão local          |
|-------------------------------|--------------------------------------|-----------------------|
| `MYSQL_HOST`                  | Host do MySQL                        | `localhost`           |
| `MYSQL_PORT`                  | Porta do MySQL                       | `3306`                |
| `MYSQL_DB`                    | Nome do banco                        | `setlistclub`         |
| `MYSQL_USER`                  | Usuário do banco                     | `setlistclub`         |
| `MYSQL_PASSWORD`              | Senha do banco                       | `setlistclub`         |
| `REDIS_HOST`                  | Host do Redis                        | `localhost`           |
| `REDIS_PORT`                  | Porta do Redis                       | `6379`                |
| `SECRET_KEY`                  | Chave JWT (altere em produção!)      | `change-me`           |
| `GOOGLE_CLIENT_ID`            | Client ID OAuth Google               | —                     |
| `GOOGLE_REDIRECT_URI`         | URI de callback do Google            | `http://localhost:3000/auth/google/callback` |
