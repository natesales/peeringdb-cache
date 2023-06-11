# PeeringDB Cache

A drop-in caching API for PeeringDB.

Various network automation tools rely on PeeringDB for network information. `peeringdb-cache` creates a local mirror of PeeringDB and exposes a drop-in replacement query API, decreasing latency to PeeringDB resources and avoiding PeeringDB rate limits.

## Features

The cache supports the `org`, `fac`, `net`, `ix`, `campus`, `carrier`, `carrierfac`, `ixfac`, `ixlan`, `ixpfx`, `netfac`, `netixlan`, and `poc` resource types.

## Setup

See below to get started with Docker or [docker-compose](https://github.com/natesales/peeringdb-cache/raw/main/docker-compose.yml). The cache may take up to 15 minutes to sync with PeeringDB when it's first started up. You can preload it with a `peeringdb.sqlite3` file in the data directory from another system that already has the database to speed up the initial sync. Subsequent syncs only update the database with changes so will be much faster.

To get network contact information, set the `PEERINGDB_API_KEY` variable to your [PeeringDB API key](https://docs.peeringdb.com/howto/api_keys/).

Once your cache is running, you can point your tools to the cache instead of PeeringDB. It should be as easy as replacing the URL from `https://www.peeringdb.com/api` to `http://your-peeringdb-cache:8080/api`.

## Running a Sync

The cache will automatically sync with PeeringDB approximately every 6 hours. You can also manually sync the cache by making a `GET` request to `/sync`.

```bash
docker exec -it peeringdb-cache curl localhost:8080/sync
```

## Monitoring

A Prometheus metrics endpoint is available at `/metrics`.

## Docker

```bash
docker run \
    -d \
    --name peeringdb-cache \
    -v ./peeringdb-cache:/data \
    -p 8080:8080 \
    -e PEERINGDB_API_KEY=your-peeringdb-api-key \
    ghcr.io/natesales/peeringdb-cache:latest
```
