FROM --platform=linux/amd64 python:3.9.1-buster

COPY Pipfile /tmp/
RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get -y update && \
    apt-get install -y ffmpeg git wkhtmltopdf wget && \
    wget https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_102.0.5005.61-1_amd64.deb && \
    apt-get install -y ./google-chrome-stable_102.0.5005.61-1_amd64.deb && \
    rm ./google-chrome-stable_102.0.5005.61-1_amd64.deb && \
    pip install pipenv pipfile-requirements && \
    cd /tmp &&  \
    pipfile2req Pipfile > requirements.txt && \
    pipfile2req -d Pipfile > requirements_dev.txt && \
    pip install -r /tmp/requirements.txt && \
    pip install -r /tmp/requirements_dev.txt

COPY ./sdk/ /app/sdk
COPY ./__init__.py /app
COPY ./extensions/ /app/extensions
COPY ./libs /app/libs
COPY ./apps/ /app/apps
COPY ./tools/ /app/tools

COPY ./.pytest.ini /app
COPY ./.coveragerc /app
COPY ./Makefile /app
COPY ./conftest.py /app

WORKDIR /app
CMD ["make", "SHELL=/bin/sh", "PYTHONPATH=/app", "ppserver/tests/run-full-test-suit-in-docker-compose"]
