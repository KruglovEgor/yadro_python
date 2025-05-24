#!/bin/bash

echo "Waiting for database..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "Database is ready!"

echo "Creating database if not exists..."
PGPASSWORD=password psql -h db -U user -d postgres -c "CREATE DATABASE random_users;" || true

echo "Applying migrations..."
alembic upgrade head

echo "Starting application..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
