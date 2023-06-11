import json
import os
import threading
import time

from django.core import serializers
from flask import Flask, request, Response, jsonify
from peeringdb import resource, get_backend
from peeringdb.client import Client

app = Flask(__name__)
pdb = Client(cfg={
    "orm": {
        "backend": "django_peeringdb",
        "database": {
            "engine": "sqlite3",
            "host": "",
            "name": "/data/peeringdb.sqlite3",
            "password": "",
            "port": 0,
            "user": ""
        },
        "migrate": True,
        "secret_key": ""
    },
    "sync": {
        "api_key": os.environ.get("PEERINGDB_API_KEY", ""),
        "only": [],
        "password": "",
        "strip_tz": 1,
        "timeout": 0,
        "url": "https://www.peeringdb.com/api",
        "user": ""
    }
})


class SyncTask(threading.Thread):
    def run(self, *args, **kwargs):
        global last_sync
        pdb.update_all()
        last_sync = time.time()


class Scheduler(threading.Thread):
    def run(self, *args, **kwargs):
        global last_sync
        while True:
            if time.time() - last_sync > 60 * 60 * 6:  # 6 hours to seconds
                sync.run()
            time.sleep(60)


sync = SyncTask()
last_sync = 0
sched = Scheduler()
sched.start()


def model_to_jdict(model):
    d = json.loads(serializers.serialize("json", [model]))[0]
    resp = d["fields"]
    resp["created"] = resp["created"]+"Z"
    resp["updated"] = resp["updated"]+"Z"
    resp["id"] = d["pk"]
    return resp


def parse_args():
    args = {}
    for k, v in request.args.items():
        # Attempt int conversion
        try:
            args[k] = int(v)
        except ValueError:
            args[k] = v
    return args


def find_by_args(model):
    args = parse_args()
    if args == {}:
        return json.dumps({"data": [model_to_jdict(i) for i in pdb.all(model)]})

    out = None
    for k, v in args.items():
        if out is None:  # Lookup first arg directly
            b = get_backend()
            out = [model_to_jdict(i) for i in b.get_objects_by(b.get_concrete(model), k, v)]
            continue
        out = [i for i in out if i.get(k) == v]

    return jsonify({"data": out})


@app.route("/api/org", methods=["GET"])
def get_org():
    return find_by_args(resource.Organization)


@app.route("/api/fac", methods=["GET"])
def get_fac():
    return find_by_args(resource.Facility)


@app.route("/api/net", methods=["GET"])
def get_net():
    return find_by_args(resource.Network)


@app.route("/api/ix", methods=["GET"])
def get_ix():
    return find_by_args(resource.InternetExchange)


@app.route("/api/campus", methods=["GET"])
def get_campus():
    return find_by_args(resource.Campus)


@app.route("/api/carrier", methods=["GET"])
def get_carrier():
    return find_by_args(resource.Carrier)


@app.route("/api/carrierfac", methods=["GET"])
def get_carrierfac():
    return find_by_args(resource.CarrierFacility)


@app.route("/api/ixfac", methods=["GET"])
def get_ixfac():
    return find_by_args(resource.InternetExchangeFacility)


@app.route("/api/ixlan", methods=["GET"])
def get_ixlan():
    return find_by_args(resource.InternetExchangeLan)


@app.route("/api/ixpfx", methods=["GET"])
def get_ixpfx():
    return find_by_args(resource.InternetExchangeLanPrefix)


@app.route("/api/netfac", methods=["GET"])
def get_netfac():
    return find_by_args(resource.NetworkFacility)


@app.route("/api/netixlan", methods=["GET"])
def get_netixlan():
    return find_by_args(resource.NetworkIXLan)


@app.route("/api/poc", methods=["GET"])
def get_poc():
    return find_by_args(resource.NetworkContact)


@app.route("/metrics")
def metrics():
    total_orgs = len(pdb.all(resource.Organization))
    total_fac = len(pdb.all(resource.Facility))
    total_net = len(pdb.all(resource.Network))
    total_ix = len(pdb.all(resource.InternetExchange))
    total_campus = len(pdb.all(resource.Campus))
    total_carrier = len(pdb.all(resource.Carrier))
    total_carrierfac = len(pdb.all(resource.CarrierFacility))
    total_ixfac = len(pdb.all(resource.InternetExchangeFacility))
    total_ixlan = len(pdb.all(resource.InternetExchangeLan))
    total_ixpfx = len(pdb.all(resource.InternetExchangeLanPrefix))
    total_netfac = len(pdb.all(resource.NetworkFacility))
    total_netixlan = len(pdb.all(resource.NetworkIXLan))
    total_poc = len(pdb.all(resource.NetworkContact))

    metrics = f"""# HELP peeringdb_cache_entries Number of entries in the PeeringDB cache
# TYPE peeringdb_cache_entries counter
peeringdb_cache_entries{{model="orgs"}} {total_orgs}
peeringdb_cache_entries{{model="fac"}} {total_fac}
peeringdb_cache_entries{{model="net"}} {total_net}
peeringdb_cache_entries{{model="ix"}} {total_ix}
peeringdb_cache_entries{{model="campus"}} {total_campus}
peeringdb_cache_entries{{model="carrier"}} {total_carrier}
peeringdb_cache_entries{{model="carrierfac"}} {total_carrierfac}
peeringdb_cache_entries{{model="ixfac"}} {total_ixfac}
peeringdb_cache_entries{{model="ixlan"}} {total_ixlan}
peeringdb_cache_entries{{model="ixpfx"}} {total_ixpfx}
peeringdb_cache_entries{{model="netfac"}} {total_netfac}
peeringdb_cache_entries{{model="netixlan"}} {total_netixlan}
peeringdb_cache_entries{{model="poc"}} {total_poc}

# HELP peeringdb_sync_running Is a sync task running?
# TYPE peeringdb_sync_running gauge
peeringdb_sync_running {int(sync.is_alive())}

# HELP peeringdb_last_sync Epoch of last sync
# TYPE peeringdb_last_sync gauge
peeringdb_last_sync {int(last_sync)}
"""
    return Response(metrics, mimetype="text/plain")


@app.route("/sync")
def sync_start():
    if not sync.is_alive():
        sync.start()
        return jsonify({"started": True})
    return jsonify({"started": False}), 409


if __name__ == "__main__":
    app.run(debug=True)
