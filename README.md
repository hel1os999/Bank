<<<<<<< HEAD
# FastAPI Example App

Resources:

- `.gitignore` for Python https://github.com/github/gitignore/blob/main/Python.gitignore
- FastAPI events https://fastapi.tiangolo.com/advanced/events/
- FastAPI lifespan events https://fastapi.tiangolo.com/advanced/events/#lifespan-function
- SQLAlchemy create engine https://docs.sqlalchemy.org/en/20/core/engines.html#sqlalchemy.create_engine
- Python typing https://docs.python.org/3/library/typing.html
- pydantic settings dotenv https://docs.pydantic.dev/latest/concepts/pydantic_settings/#dotenv-env-support
- pydantic settings env variables https://docs.pydantic.dev/latest/concepts/pydantic_settings/#parsing-environment-variable-values
- case converter https://github.com/mahenzon/ri-sdk-python-wrapper/blob/master/ri_sdk_codegen/utils/case_converter.py
- SQLAlchemy constraint naming conventions https://docs.sqlalchemy.org/en/20/core/constraints.html#constraint-naming-conventions
- Alembic cookbook https://alembic.sqlalchemy.org/en/latest/cookbook.html
- Alembic naming conventions https://alembic.sqlalchemy.org/en/latest/naming.html#integration-of-naming-conventions-into-operations-autogenerate
- Alembic + asyncio recipe https://alembic.sqlalchemy.org/en/latest/cookbook.html#using-asyncio-with-alembic
- orjson https://github.com/ijl/orjson
- FastAPI ORJSONResponse https://fastapi.tiangolo.com/advanced/custom-response/#use-orjsonresponse


```shell
python -c 'import secrets; print(secrets.token_hex())'
```
=======
# Bank
  ## About the Project
This is a neobank (like Revolut). You can create users, set up bank accounts, issue cards, process transactions etc. The project itself is built on FastAPI. User management is implemented using FastAPI Users. Caching and a message broker have also been implemented.

  ## Techology
- FastAPI
- fastapi-users
- Pydantic
- Alembic
- SQLAlchemy
- Docker & Docker compose
- Redis
- RabbitMQ
- pytest

  ## Run
1. poetry install
2. For APP_CONFIG__ACCESS_TOKEN__RESET_PASSWORD_TOKEN_SECRET= and APP_CONFIG__ACCESS_TOKEN__VERIFICATION_TOKEN_SECRET= run two times: 
```shell
python -c 'import secrets; print(secrets.token_hex())'
```
3. For APP_CONFIG__CRYPTOGRAPHY__DB_ENCRYPTION_KEY= run:
```shell
python -c "import secrets, base64; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())"
```
4. APP_CONFIG__CRYPTOGRAPHY__PASSPORT__HASH_SALT and APP_CONFIG__CRYPTOGRAPHY__CARD_HASH_SALT= you will have to come up with this yourself.
5. Run: 
```shell
docker compose up -d --build       
```