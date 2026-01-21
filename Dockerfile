FROM python:3.11-slim-bookworm

WORKDIR /app

ARG GITLAB_DEPLOY_TOKEN=local
ENV GITLAB_DEPLOY_TOKEN ${GITLAB_DEPLOY_TOKEN}
ARG GITLAB_DEPLOY_USERNAME=local
ENV GITLAB_DEPLOY_USERNAME ${GITLAB_DEPLOY_USERNAME}
ARG GITLAB_SSA_MANAGER_DEPLOY_TOKEN=local
ENV GITLAB_SSA_MANAGER_DEPLOY_TOKEN ${GITLAB_SSA_MANAGER_DEPLOY_TOKEN}
ARG GITLAB_SSA_DEPLOY_USERNAME=local
ENV GITLAB_SSA_DEPLOY_USERNAME ${GITLAB_SSA_DEPLOY_USERNAME}

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      git libpq-dev gcc g++ libffi-dev \
 && rm -rf /var/lib/apt/lists/*

COPY . /app

RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir --force-reinstall -r requirements.txt

EXPOSE 8080

ENTRYPOINT ["python3"]

CMD ["-m", "device_manager_service"]
