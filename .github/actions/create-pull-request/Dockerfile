FROM python:3.9.6-slim-buster

# Labels for GitHub to read your action
LABEL "com.github.actions.name"="Huma Pull Request"
LABEL "com.github.actions.description"="Huma Pull Request"
# Here are all of the available icons: https://feathericons.com/
LABEL "com.github.actions.icon"="chevron-up"


# Install dependencies
RUN apt-get update
RUN apt-get -y install git

COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your action's code
COPY script.py /script.py

# Run `python /script.py`
ENTRYPOINT ["python", "/script.py"]
