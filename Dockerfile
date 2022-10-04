FROM tiangolo/uvicorn-gunicorn-fastapi:latest

RUN pip install --upgrade pip
ADD requirements.txt .
RUN pip install -r requirements.txt

COPY ./app /app
