FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 8000

# init_db ще се изпълни при старта (в app.py)
CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]
