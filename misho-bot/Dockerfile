FROM python:3.12-slim

WORKDIR /root

ENV PYTHONPATH=src/
RUN pip install --no-cache-dir uv

COPY misho-api/ ./misho-api
COPY misho-client/ ./misho-client
COPY misho-bot ./misho-bot
COPY pyproject.toml .

RUN uv venv
WORKDIR ./misho-bot
RUN uv pip install -e .
WORKDIR ..


CMD ["uv", "run", "misho-bot"]