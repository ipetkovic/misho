FROM python:3.12-slim

WORKDIR /root
COPY ./requirements.txt .

RUN python -m venv .venv
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src

ENV PYTHONPATH=src/
ENV MISHO_MAIL_USERNAME=ivo.petkovic@gmail.com
ENV MISHO_MAIL_PASSWORD=your_password_here
ENV MISHO_ENVIRONMENT=PROD