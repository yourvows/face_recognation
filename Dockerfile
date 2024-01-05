# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.9.13
FROM python:${PYTHON_VERSION} as base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1



# Сначала копируем файл requirements.txt
COPY requirements.txt ./

# Теперь устанавливаем зависимости
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# После установки зависимостей копируем остальные файлы
COPY . .

EXPOSE 5000

CMD ["python", "test.py"]
