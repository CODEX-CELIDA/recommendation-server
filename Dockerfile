FROM tiangolo/uvicorn-gunicorn-fastapi:latest

COPY ./ca_root /usr/local/share/ca-certificates/extra
RUN chmod -R 644 /usr/local/share/ca-certificates/extra && update-ca-certificates
RUN pip install truststore --trusted-host=pypi.org --trusted-host=files.pythonhosted.org
RUN pip install --upgrade pip pytest_runner --trusted-host=pypi.org --trusted-host=files.pythonhosted.org
ADD requirements.txt .
RUN pip install -r requirements.txt --trusted-host=pypi.org --trusted-host=files.pythonhosted.org

COPY ./app /app

ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

RUN mkdir -p /app/data
