FROM python:3.9-slim-buster

ENV PYTHONUNBUFFERED 1

RUN git clone mojgithub_tutaj /image_sevice

WORKDIR /image_sevice

RUN pip install -r requirements.txt

#VOLUME /drf_src

EXPOSE 8080

CMD python manage.py makemigrations && python manage.py migrate && python manage.py runserver 0.0.0.0:8000