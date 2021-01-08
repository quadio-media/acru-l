FROM python:3.8-slim-buster

ENV PYTHONUNBUFFERED 1
ENV AWS_CDK_VERSION 1.79.0

RUN apt-get update -y \
    && apt-get install -y --no-install-recommends \
        build-essential \
        git \
        nodejs \
        curl \
        docker

RUN curl https://www.npmjs.com/install.sh | sh
RUN npm install npm@latest -g && npm install -g aws-cdk@${AWS_CDK_VERSION}

COPY ./docker/requirements.txt /home/requirements.txt
RUN pip install --upgrade pip \
    && pip install --use-feature=2020-resolver --no-cache-dir -r /home/requirements.txt \
    && rm /home/requirements.txt

RUN mkdir -p /home/actions/bin
COPY ./docker/app.py /home/actions/app.py
COPY ./docker/entrypoint.sh /home/actions/bin/entrypoint.sh

ENV PYTHONPATH "${PYTHONPATH}:/home/actions"
ENV PATH "${PATH}:/home/actions/bin"

RUN mkdir -p /home/src
WORKDIR /home/src

# Clean up
RUN apt-get remove -y --purge build-essential curl \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

ENTRYPOINT ["entrypoint.sh"]
