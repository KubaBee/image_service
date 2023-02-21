FROM python:3.9-slim-bullseye

ENV PYTHONUNBUFFERED 1

WORKDIR /image_sevice

RUN apt-get update && apt-get install -y curl unzip
RUN curl -L -o image_service.zip https://github.com/KubaBee/image_service/archive/master.zip
RUN unzip image_service.zip -d /image_service

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

EXPOSE 8080

CMD python manage.py makemigrations && python manage.py migrate

#CMD python manage.py runserver 0.0.0.0:8000