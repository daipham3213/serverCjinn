python manage.py rqworker &
python manage.py makemigrations &&
python manage.py migrate &&
python manage.py runserver 0.0.0.0:8000
#gunicorn serverCjinn.asgi:application -c gunicorn.conf
#gunicorn --bind 0.0.0.0:8000 serverCjinn.asgi -w 4 -k uvicorn.workers.UvicornWorker -t 30 -n "server_cjinn"