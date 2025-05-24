#!/bin/bash

# Ждем, пока база данных будет готова
echo "Waiting for database..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "Database is ready!"

# Создаем базу данных, если она не существует
echo "Creating database if not exists..."
PGPASSWORD=password psql -h db -U user -d postgres -c "CREATE DATABASE random_users;" || true

# Применяем миграции
echo "Applying migrations..."
alembic upgrade head

# Запускаем приложение
echo "Starting application..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload 