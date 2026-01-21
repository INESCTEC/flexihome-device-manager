FROM python:3.11-slim-bookworm

WORKDIR /app

COPY energy_manager_service/ /app/energy_manager_service
COPY requirements.txt /app

ARG GITLAB_DEPLOY_USERNAME=local
ENV GITLAB_DEPLOY_USERNAME ${GITLAB_DEPLOY_USERNAME}
ARG GITLAB_DEPLOY_TOKEN=local
ENV GITLAB_DEPLOY_TOKEN ${GITLAB_DEPLOY_TOKEN}
ARG GITLAB_SSA_MANAGER_DEPLOY_TOKEN=local
ENV GITLAB_SSA_MANAGER_DEPLOY_TOKEN ${GITLAB_SSA_MANAGER_DEPLOY_TOKEN}

# RUN apt-get update -y && apt-get upgrade -y
# RUN apt-get install -y python3-pip git libpq-dev

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      git libpq-dev gcc g++ libffi-dev cmake make zlib1g-dev  \
 && rm -rf /var/lib/apt/lists/*

COPY . /app/notify_users_flexibility_not_accepted_by_grid

WORKDIR /app/notify_users_flexibility_not_accepted_by_grid

RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir --force-reinstall -r requirements.txt

WORKDIR /app/energy_manager_service/jobs/notify_users_flexibility_not_accepted_by_grid

ENTRYPOINT ["python3"]

CMD ["notify_users_flexibility_not_accepted_by_grid.py"]
