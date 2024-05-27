#Подготовка
FROM python:3.12-slim as builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && \
    apt-get install -y libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

RUN python -m pip install --upgrade pip
COPY requirements.txt .
RUN pip wheel --find-links=/wheels --wheel-dir=/wheels -r requirements.txt

# Финальный этап
FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .

COPY requirements.txt .

RUN pip install --no-cache /wheels/*

COPY app app

CMD ["python", "app/main.py"]
