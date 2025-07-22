FROM python:3.13

# Установка системных зависимостей
#RUN apt-get update && apt-get install -y netcat-traditional && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/

# Устанавливаем зависимости
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

# Настройки окружения
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=sport_analytics.settings

RUN mkdir -p /app/static /app/media

RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
