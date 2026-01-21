FROM python:3.11-slim-bookworm

WORKDIR /app
COPY jobs/calculate_available_flexibility/ /app
COPY energy_manager_service/ /app/energy_manager_service
COPY requirements.txt /app

ARG GITLAB_DEPLOY_USERNAME=local
ENV GITLAB_DEPLOY_USERNAME ${GITLAB_DEPLOY_USERNAME}
ARG GITLAB_DEPLOY_TOKEN=local
ENV GITLAB_DEPLOY_TOKEN ${GITLAB_DEPLOY_TOKEN}
ARG GITLAB_SSA_MANAGER_DEPLOY_TOKEN=local
ENV GITLAB_SSA_MANAGER_DEPLOY_TOKEN ${GITLAB_SSA_MANAGER_DEPLOY_TOKEN}

# RUN apt update -y && apt upgrade -y
# RUN apt install -y python3-pip git libpq-dev

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      git libpq-dev gcc g++ libffi-dev cmake make zlib1g-dev  \
 && rm -rf /var/lib/apt/lists/*

RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir --force-reinstall -r requirements.txt

ENTRYPOINT ["python3"]

CMD ["calculate_available_flexibility.py"]
# ENTRYPOINT [ "tail", "-f", "/dev/null" ]


# docker run -t --name avail_flex --network host calculate_available_flexibility:local