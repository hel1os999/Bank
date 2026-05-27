FROM python:3.12.6-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VERSION=1.8.3 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

WORKDIR /app

RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"

COPY pyproject.toml poetry.lock ./

RUN poetry install --no-root

COPY fastapi-application .

RUN chmod +x prestart.sh

ENTRYPOINT ["./prestart.sh"]

CMD ["uvicorn", "main:main_app", "--host", "0.0.0.0", "--port", "8000"]

# with alembic all good, maybe you must check the main.py