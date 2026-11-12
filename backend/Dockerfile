FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
RUN groupadd --gid 10001 crm && useradd --uid 10001 --gid crm --no-create-home crm
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY app ./app
COPY alembic.ini ./
COPY migrations ./migrations

USER crm
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
