FROM python:3.12-slim

WORKDIR /root

ENV PYTHONPATH=src/
RUN pip install --no-cache-dir uv

COPY sportbooking/ ./sportbooking
COPY misho-server/ ./misho-server
COPY pyproject.toml .

RUN uv venv
WORKDIR ./misho-server
RUN uv pip install -e .
WORKDIR ..


CMD ["uv", "run", "misho-server"]