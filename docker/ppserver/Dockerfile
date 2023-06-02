FROM --platform=linux/amd64 python:3.9.6-slim-buster

ARG GIT_COMMIT=""
ARG GIT_BRANCH="master"

LABEL branch=${GIT_BRANCH}
LABEL commit=${GIT_COMMIT}

COPY Pipfile /tmp/
RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get -y update && \
    apt-get install -y ffmpeg git wkhtmltopdf wget && \
    wget https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_102.0.5005.61-1_amd64.deb && \
    apt-get install -y ./google-chrome-stable_102.0.5005.61-1_amd64.deb && \
    rm ./google-chrome-stable_102.0.5005.61-1_amd64.deb && \
    pip install pipenv pipfile-requirements && \
    cd /tmp && pipfile2req Pipfile > requirements.txt && \
    pip install -r /tmp/requirements.txt


COPY ./sdk/ /app/sdk
COPY ./libs /app/libs
COPY ./__init__.py /app
COPY ./extensions/ /app/extensions
COPY ./apps/ /app/apps
COPY ./tools/ /app/tools

WORKDIR /app/apps/ppserver

ENV GIT_COMMIT ${GIT_COMMIT}
ENV GIT_BRANCH ${GIT_BRANCH}
CMD ["python", "ppserver.py", "--prod", "true"]
