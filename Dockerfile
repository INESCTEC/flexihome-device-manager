FROM python:3.11-slim-bookworm

WORKDIR /app
COPY . /app

ARG GITLAB_DEPLOY_USERNAME=local
ENV GITLAB_DEPLOY_USERNAME ${GITLAB_DEPLOY_USERNAME}
ARG GITLAB_DEPLOY_TOKEN=local
ENV GITLAB_DEPLOY_TOKEN ${GITLAB_DEPLOY_TOKEN}
ARG GITLAB_SSA_MANAGER_DEPLOY_TOKEN=local
ENV GITLAB_SSA_MANAGER_DEPLOY_TOKEN ${GITLAB_SSA_MANAGER_DEPLOY_TOKEN}

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      git libpq-dev gcc g++ libffi-dev cmake make zlib1g-dev  \
 && rm -rf /var/lib/apt/lists/*

RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir --force-reinstall -r requirements.txt

##############################
# COMPILE AND INSTALL SOPLEX #
##############################

RUN tar xvzf soplex-6.0.2.0.tgz

WORKDIR /app/soplex-6.0.2.0
RUN mkdir -p build

WORKDIR /app/soplex-6.0.2.0/build
RUN cmake /app/soplex-6.0.2.0
RUN make
RUN make test
RUN make install


#################################
# COMPILE AND INSTALL PYSCIPOPT #
#################################

WORKDIR /app
RUN tar xvzf scip-8.0.2.tgz

WORKDIR /app/scip-8.0.2
RUN mkdir -p build

WORKDIR /app/scip-8.0.2/build
RUN cmake .. -DCMAKE_INSTALL_PREFIX=make -DSOPLEX_DIR=/app/soplex-6.0.2.0/ -DAUTOBUILD=ON
RUN make
# RUN make test  # Takes upwards of 15 minutes to run the tests
RUN make install


#######################################
# INSTALL PYSCIPOPT AS PYTHON PACKAGE #
#######################################

WORKDIR /app

RUN pip3 install wheel

ENV SCIPOPTDIR=/app/scip-8.0.2/build/make
RUN python3 -m pip install "pyscipopt<5"

EXPOSE 8080

ENTRYPOINT ["python3"]

CMD ["-m", "energy_manager_service"]

# docker build --build-arg GITLAB_DEPLOY_USERNAME=XXX --build-arg GITLAB_DEPLOY_TOKEN=XXX --build-arg GITLAB_SSA_MANAGER_DEPLOY_TOKEN=XXX -t energy-manager-local:local .
