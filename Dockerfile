FROM python:3.7-alpine3.11

WORKDIR /app

ARG GITHUB_TOKEN
ENV GITHUB_TOKEN=$GITHUB_TOKEN

COPY requirements.txt ./

RUN apk --no-cache add git \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

RUN addgroup -g 1000 -S app_user && \
    adduser -u 1000 -S app_user -G app_user

EXPOSE 8000

CMD ["gunicorn", "-b", "0.0.0.0:8000", "-u", "app_user", "-g", "app_user", "main"]
