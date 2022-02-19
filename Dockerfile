FROM python:3.8

SHELL ["/bin/bash", "-c"]

WORKDIR /app

EXPOSE 8000

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

CMD cd src && python manage.py migrate && python manage.py runserver 0.0.0.0:8000
