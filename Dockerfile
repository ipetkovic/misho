FROM python:3.12-slim

WORKDIR /root
COPY ./requirements.txt .

RUN python -m venv .venv
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src
COPY alembic.ini .
COPY alembic/ alembic/
COPY run run

ENV PYTHONPATH=src/
CMD ["python", "src/misho"]