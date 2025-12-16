set -e

cd /app/backend

echo "==> Launching alembic migrations..."
alembic upgrade head

echo "==> Starting application..."
python main.py
