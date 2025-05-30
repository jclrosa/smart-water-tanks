web: gunicorn smart_water_tanks.wsgi --log-file -
release: python manage.py migrate && python manage.py populate_sample_data 