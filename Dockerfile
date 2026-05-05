FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY sovits_wyoming_connector ./sovits_wyoming_connector

RUN pip install --no-cache-dir .

EXPOSE 10200

ENTRYPOINT ["sovits-wyoming-connector"]
