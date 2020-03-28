FROM python:3.7-alpine3.11

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mv docker/main.py main.py

RUN addgroup -g 1000 -S app_user && \
    adduser -u 1000 -S app_user -G app_user

EXPOSE 8000

CMD ["gunicorn", "-b", "0.0.0.0:8000", "-u", "app_user", "-g", "app_user", "main"]
