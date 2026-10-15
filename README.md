# targeting-service (Python)

Este é o serviço de regras de segmentação (targeting) do projeto ToggleMaster. Ele é responsável por gerenciar regras complexas (ex: "50% dos usuários", "usuários do país X") para uma feature flag específica.

**IMPORTANTE:** Este serviço também é protegido e depende que o `auth-service` esteja rodando (ex: em `http://localhost:8001`).

## 📦 Pré-requisitos (Local)

* [Python](https://www.python.org/) (versão 3.13 ou superior)
* [PostgreSQL](https://www.postgresql.org/download/)
* O `auth-service` deve estar rodando.

## 🚀 Rodando Localmente

1.  **Clone o repositório** e entre na pasta `targeting-service`.

2.  **Prepare o Banco de Dados:**
    * Crie um banco de dados no seu PostgreSQL (ex: `targeting_db`).
    * Execute o script `db/init.sql` para criar a tabela `targeting_rules`:
        ```bash
        psql -U seu_usuario -d targeting_db -f db/init.sql
        ```

3.  **Configure as Variáveis de Ambiente:**
    Crie um arquivo chamado `.env` na raiz desta pasta (`targeting-service/`) com o seguinte conteúdo:
    ```.env
    # String de conexão do seu banco de dados PostgreSQL
    DATABASE_URL="postgres://SEU_USUARIO:SUA_SENHA@localhost:5432/targeting_db"
    
    # Porta que este serviço (targeting-service) irá rodar
    PORT="8003"
    
    # URL do auth-service (que deve estar rodando na porta 8001)
    AUTH_SERVICE_URL="http://localhost:8001"
    ```

4.  **Instale as Dependências:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Inicie o Serviço:**
    ```bash
    gunicorn --bind 0.0.0.0:8003 app:app
    ```
    O servidor estará rodando em `http://localhost:8003`.

## 🧪 Testando os Endpoints

Lembre-se de obter sua `SUA_CHAVE_API` no `auth-service` (veja o README do `flag-service`).

**1. Verifique a Saúde (Health Check):**
```bash
curl http://localhost:8003/health
```
Saída esperada: `{"status":"ok"}`

**2. Crie uma nova Regra de Segmentação:** Vamos criar uma regra para a flag enable-new-dashboard (que você criou no flag-service). Esta regra fará a flag aparecer para 50% dos usuários.
```bash
curl -X POST http://localhost:8003/rules \
-H "Content-Type: application/json" \
-H "Authorization: Bearer SUA_CHAVE_API" \
-d '{
    "flag_name": "enable-new-dashboard",
    "is_enabled": true,
    "rules": {
        "type": "PERCENTAGE",
        "value": 50
    }
}'
```
Saída esperada: (Um JSON com os dados da regra criada).

**3. Busque a Regra que você criou:**
```bash
curl http://localhost:8003/rules/enable-new-dashboard \
-H "Authorization: Bearer SUA_CHAVE_API"
```
Saída esperada: (O JSON da regra que você acabou de criar).

**4. Atualize a Regra (mude para 75%):**
```bash
curl -X PUT http://localhost:8003/rules/enable-new-dashboard \
-H "Content-Type: application/json" \
-H "Authorization: Bearer SUA_CHAVE_API" \
-d '{
    "rules": {
        "type": "PERCENTAGE",
        "value": 75
    }
}'
```
Saída esperada: (O JSON da regra atualizada, com `"value": 75`).

## 🔁 CI/CD e DevSecOps (Fase 3)

O deploy não é mais feito com `kubectl`: a pipeline publica a imagem no ECR e atualiza a versão no repositório [toggle-master-gitops](https://github.com/FIAP-PosTech-DevOps/toggle-master-gitops), e o ArgoCD de cada ambiente sincroniza. A pipeline é compartilhada pelos 5 serviços e fica em [toggle-master-infra](https://github.com/FIAP-PosTech-DevOps/toggle-master-infra/blob/main/docs/ci-cd.md).

| Workflow | Quando roda | O que faz |
|---|---|---|
| `ci.yml` | PR para `release/*` ou `main` | build, testes, lint, SonarQube Cloud (SAST), Snyk ou Trivy (SCA) e scan da imagem com Trivy, sem publicar |
| `ci.yml` | botão (Actions → ci → Run workflow), com **qualquer branch** em "Use workflow from" | o mesmo + imagem `dev-<branch>-<sha>` no ECR + deploy em **develop** |
| `ci.yml` | push em `release/vX.Y.Z` (merge de um PR no pacote) | o mesmo + imagem `vX.Y.Z-<sha>` no ECR + deploy em **staging** |
| `promote.yml` | merge do PR `release/vX.Y.Z` → `main` | confere se a imagem é a de staging, re-scan com Trivy, aprovação e deploy em **production**, sem novo build; cria a tag `vX.Y.Z` na main |
| `release.yml` | botão (Actions → release → Run workflow) | `criar-release`: cria `release/vX.Y.Z` a partir da main (patch, minor ou major) |

Uma vulnerabilidade **crítica** (dependência ou imagem) ou o Quality Gate do Sonar reprovado interrompem a pipeline, e nada chega ao ECR.

Para rodar localmente as mesmas verificações da pipeline:

```bash
pip install -r requirements-dev.txt
pytest --cov=.                      # testes unitários (sem banco/AWS: tudo simulado)
flake8 .                            # lint (mesma configuração da CI: .flake8)
```
