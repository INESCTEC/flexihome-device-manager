![flexihome-logo](docs/logo/flexihome-logo.png)

---

# FlexiHome: A Home Energy Management System 🔌<br><br>Energy Manager

## Description

This repository contains the Energy Manager Service, a core component of the Home Energy Management System (HEMS). The Energy Manager Service is responsible for optimizing the flexibility of distributed energy resources (DERs) according to inputs from the SO and user comfort preferences. It provides secure, scalable APIs for flexibility calculations, recommendations, and integration with other HEMS micro-services.

## Table of Contents

- [FlexiHome: A Home Energy Management System 🔌Energy Manager](#flexihome-a-home-energy-management-system-energy-manager)
  - [Description](#description)
  - [Table of Contents](#table-of-contents)
  - [HEMS Overview](#hems-overview)
    - [Visit all the FlexiHome micro-services:](#visit-all-the-flexihome-micro-services)
  - [Project details](#project-details)
    - [Repository Structure](#repository-structure)
    - [Project Status](#project-status)
    - [Technology Stack](#technology-stack)
    - [Dependencies](#dependencies)
  - [Installation](#installation)
  - [Usage](#usage)
  - [Known Issues](#known-issues)
  - [Open Source Licensing Info](#open-source-licensing-info)
    - [Contacts](#contacts)

## HEMS Overview

EMSs (Energy Management Systems) play a key role in the flexibility enablement of consumers, residential and tertiary, which is paramount to accessing the previously untapped flexibility potential of residential DERs (Distributed Energy Resources). These resources, under the form of energy assets, are usually household appliances like heat pumps, EV chargers, dishwashers, PV inverts, batteries, etc. This is where the FlexiHome (Home Energy Management System) comes in. 

The goal of this system is to facilitate the user’s participation in the flexibility value chain, while providing them with incentives in a clear, explainable way.

To fulfill this goal in an effective and scalable way, the FlexiHome is designed with a micro-services architecture (below), orchestrated in a Kubernetes environment, where each micro-service is modular and can be replaced or expanded, without breaking the remaining logic.

![FlexiHome Architecture](docs/diagrams/hems-architecture-diagram.svg)

FlexiHome utilizes an IoT interoperable gateway (FlexiHome Hub) to connect to the end users DERs via interoperable protocols like OCPP and Modbus, which connects with the cloud system (FlexiHome Cloud) via an MQTT message broker.

The cloud operations are done via micro-services, where the flexibility optimization algorithms run. To complement these micro-services, support applications like postgres (database), elasticsearch (log database), prometheus (performance metrics) and grafana (metrics dashboard) are used.

Lastly, the user can view the information regarding their devices and flexibility on a user interface provided by the mobile app, which accesses the FlexiHome microservices using a REST API Gateway for additional security measures and routing of requests.

### Visit all the FlexiHome micro-services:
- [FlexiHome Account Manager](https://github.com/INESCTEC/hems-account-manager) - Manages user accounts, authentication, and implements cybersecurity measures within the FlexiHome ecosystem
- [FlexiHome Statistics Manager](https://github.com/INESCTEC/hems-statistics-manager) - Collects and processes data gathered from IoT devices connected to the FlexiHome ecosystem
- [FlexiHome Device Manager](https://github.com/INESCTEC/hems-device-manager) - Responsible for the integration and management of IoT devices to the FlexiHome ecosystem
- [FlexiHome Energy Manager](https://github.com/INESCTEC/hems-energy-manager) - Receives grid needs inputs from system operators and user comfort inputs to optimized the flexibility bids taken to market 
- [FlexiHome Hub](https://github.com/INESCTEC/hems-hub) - IoT interoperable gateway that implements the communication, using MQTT protocol, between the DERs and the FlexiHome services on the cloud
- [FlexiHome Mobile App](https://github.com/INESCTEC/hems-app) - mobile application targetted for residential end consumers to manage their flexible DERs. Available in Android and iOS

## Project details

### Repository Structure

```bash
.                              # Root directory of the repository
├── energy_manager_service/    # Main source code for the Energy Manager Service
│   ├── controllers/           # API controllers for energy management
│   ├── models/                # Data models and schemas
│   ├── clients/               # Service clients and integrations
│   ├── events/                # Event handling modules
│   ├── jobs/                  # Scheduled jobs and tasks
│   └── ...                    # Other supporting modules
├── Dockerfile                 # Docker configuration for containerization
├── requirements.txt           # Main Python dependencies
├── service-specific-requirements.txt # Additional service dependencies
├── test-requirements.txt      # Testing dependencies
├── setup.py                   # Python package setup
├── Docker-compose/            # Docker Compose files and configs
├── docs/                      # Documentation and architecture diagrams
├── energy-manager-openapi.yaml# OpenAPI specification
├── README.md                  # Main documentation
├── scipoptsuite-8.0.3.tgz     # Optimization suite (SCIP)
├── ...                        # Other resources and scripts
```

### Project Status

- 🚧 **In Progress:** Actively developed; features, APIs, and structure may change. See the repository for recent commits and roadmap updates.

### Technology Stack

- **Programming Language:** Python 3.8+
- **Frameworks/Libraries:** Flask, SQLAlchemy, Alembic, pytest
- **Containerization:** Docker, Docker Compose
- **Orchestration:** Kubernetes (recommended for deployment)
- **Other Tools:** Alembic (migrations), pytest (testing), OpenAPI/Swagger

### Dependencies

- Main dependencies: see `requirements.txt`
- Testing dependencies: see `test-requirements.txt`
- System dependencies: Docker, Docker Compose, Python 3.8+, (optionally) PostgreSQL, Cassandra

## Installation

Follow these steps to install and set up the Energy Manager Service:

1. **Clone the repository:**

```bash
git clone https://github.com/INESCTEC/hems-energy-manager.git
cd hems-energy-manager
```

2. **Create and activate a virtual environment:**

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**

```bash
pip install -r requirements.txt
pip install -r service-specific-requirements.txt
```

4. **Set up environment variables (if required):**

```bash
cp .env.example .env
nano .env  # Edit with your configuration values
```

5. **(Optional) Build and run with Docker Compose:**

```bash
docker-compose up --build
```

**Troubleshooting:**

- Ensure Docker and Python 3.8+ are installed.
- For database setup, see `Docker-compose/postgresql_start.sh` and `Docker-compose/cassandra_start.cql`.

## Usage

To start the Energy Manager Service locally:

```bash
source venv/bin/activate
python -m energy_manager_service
```

Or, if using Docker Compose:

```bash
cd Docker-compose
docker-compose up --build
```

Access the API documentation and endpoints as defined in the OpenAPI spec (`energy-manager-openapi.yaml`).
You can view and test the API using [Swagger Editor](https://editor.swagger.io/) or similar tools.

## Known Issues

- No major issues reported. Please use GitHub Issues to report bugs or request features.
- See [Issues](https://github.com/INESCTEC/hems-energy-manager/issues) for current limitations and workarounds.

## Open Source Licensing Info

See [`LICENSE`](LICENSE) for details on usage rights and licensing. This project is released under the MIT License.

### Contacts

For questions or support, contact:

- Vasco Manuel Campos: vasco.m.campos@inesctec.pt
- Igor Rezende Castro: igor.c.abreu@inesctec.pt
