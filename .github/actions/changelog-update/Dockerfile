FROM python:3.9-slim

# Labels for GitHub to read your action
LABEL "com.github.actions.name"="Huma Changelog Update"
LABEL "com.github.actions.description"="Huma Changelog Update"
# Here are all of the available icons: https://feathericons.com/
LABEL "com.github.actions.icon"="chevron-up"


# Install dependencies
RUN apt-get update
RUN apt-get -y install git


# Copy the rest of your action's code
COPY script.py /script.py

ENTRYPOINT ["python", "/script.py"]
