FROM python:3.7-alpine3.11

WORKDIR /usr/src/app

COPY sizematch-urls-publisher-py/requirements.txt ./urls_publisher_requirements.txt
RUN pip install --no-cache-dir -r urls_publisher_requirements.txt

COPY . .
RUN mv docker/docker_main.py main.py

CMD [ "python", "main.py" ]
