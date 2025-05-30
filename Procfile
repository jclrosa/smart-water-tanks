release: python manage.py migrate && python manage.py populate_sample_data
web: gunicorn smart_water_tanks.wsgi:application --bind 0.0.0.0:$PORT 