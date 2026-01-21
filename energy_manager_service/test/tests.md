# Run Energy Manager Automated Integration Tests

## Setup

**Pre-requesite:** INESCTEC VPN must be connected. (to access the sentinel VM)

```bash
# Databases, kafka stack and SIF
docker compose up postgresql kafka zookeeper connect ke ga-local cassandra cassandra-load-keyspace

# Debezium connector
curl -i -X POST -H "Accept:application/json" -H "Content-Type:application/json" localhost:8083/connectors/ --data-binary "@connectors/account_manager.json"

# Startup HEMS services
docker compose up account-manager device-manager energy-prices forecast-rest-api notification-service
```

## Caveats

### 1. Device manager "idle in transaction"

When running the tests for the first time, sometimes the device manager gets a database transaction stuck in "idle in transaction". You can fix this with this command:

```bash
psql -h 127.0.0.1 -p 5432 -U postgres -d account_manager
```

```sql
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = 'devicemanager'
AND pid <> pg_backend_pid();
```

## Run tests

The tests can be run using the full test suite, or individually:

Full test suite:

```bash
# Run on service root directory (where tox.ini is)
tox
```

Specific test:

```bash
# tox -e py3 -- {{test file}}::{{test class}}::{{test function}}
tox -e py3 -- energy_manager_service/test/test_get_schedule_cycles.py::TestScheduler::test_no_cycles_happy_flow
```

## Remarks

1. When registerig a user, the registration of the dongle fails. This is normal, because we are not mocking an influx database on these tests.
2. The registration of an installation on the Account Manager service with the forecast API fails, because the NWP grid is not correctly ajusted.
   1. This is not important for the energy manager tests, so we just register an installation directly using the forecast service REST API.
3. We can only test a functioning delay call if we have a real physical appliance. So there are no tests for a scenarion where a delay call is correcly done.
