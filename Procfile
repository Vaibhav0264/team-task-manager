web: gunicorn taskmanager.wsgi:application --bind 0.0.0.0:$PORT --log-file -
release: python manage.py migrate --no-input && python manage.py collectstatic --no-input