FROM python:3.12.3-bullseye

ARG BUILD_DATE
ARG COMMIT
ARG VERSION

ADD deploy/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt && rm -rf ~/.cache/pip
