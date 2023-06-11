FROM python:3.11.4-slim-bullseye
ENV PYTHONUNBUFFERED=1
WORKDIR /app

RUN pip install peeringdb django-peeringdb django flask

COPY app.py /app/app.py

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0", "--port", "8080"]
