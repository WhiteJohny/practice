#!/bin/bash

# Функция для проверки доступности PostgreSQL
#wait_for_postgres() {
#    echo "Waiting for postgres..."
#    while ! nc -z db 5432; do
#        sleep 0.1
#    done
#    echo "PostgreSQL started"
#}

# Функция для применения миграций
apply_migrations() {
    echo "Applying database migrations..."
    python manage.py migrate
}

# Функция для сбора статических файлов
collect_static() {
    echo "Collecting static files..."
    python manage.py collectstatic --noinput
}

# Функция для создания суперпользователя, если его нет
create_superuser() {
    if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && \
       [ -n "$DJANGO_SUPERUSER_EMAIL" ] && \
       [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
        echo "Creating superuser..."
        python manage.py createsuperuser --noinput
    fi
}

# Основной процесс
#wait_for_postgres
apply_migrations
collect_static
create_superuser

# Запуск Gunicorn
echo "Starting Gunicorn..."
exec gunicorn sport_analytics.wsgi:application --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
