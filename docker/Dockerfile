FROM python:3.7-alpine3.11

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mv docker/docker_main.py main.py

CMD [ "python", "main.py" ]
