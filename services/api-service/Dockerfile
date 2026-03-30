FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc libpq-dev

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY gunicorn.conf.py .

CMD ["gunicorn", "-c", "gunicorn.conf.py", "app.main:app"]