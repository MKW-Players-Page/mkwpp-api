web: gunicorn mkwpp.wsgi:application --bind 0.0.0.0:$PORT
worker: celery -A mkwpp worker --beat --scheduler django
