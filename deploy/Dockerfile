ARG BASE_IMAGE=647854334008.dkr.ecr.us-east-1.amazonaws.com/promptgpt-base:202404171654-c0a42f5
FROM $BASE_IMAGE

ARG BUILD_DATE
ARG COMMIT
ARG VERSION

ADD . /workspace
ADD deploy/entrypoint.sh /entrypoint.sh

WORKDIR /workspace

ENTRYPOINT ["/entrypoint.sh"]
CMD ["sleep"]
