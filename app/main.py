from flask import Flask, redirect, render_template, request, url_for
import jobs
import rq
from enum import Enum, auto
from typing import Dict, NewType, Tuple, List
from multiprocessing import Process, Manager
import csv
import io
import json
import logging
import os
import random
import time
import uuid
import dataclasses

from flask import request, jsonify, flash, redirect, send_from_directory, url_for, abort
from flask_cors import CORS, cross_origin
from redis import Redis
from werkzeug.utils import secure_filename
import flask
import rq


from allocation import *

ALLOWED_EXTENSIONS = ["csv"]
app = flask.Flask(__name__)
cors = CORS(app)

jobs.rq.init_app(app)

test = {}
# For sake of simplicty, we keep track of the jobs we've launched
# in memory. This will only work as long there is only one python
# process (web server context) and it must not get restarted.
# In advanced use cases you want to keep track of jobs by their ids
# and utilize sessions and redis.
joblist = []
jobdict = {}


@app.route("/")
def index():
    l = []
    # work on copy of joblist,
    for job in list(joblist):
        # task may be expired, refresh() will fail
        try:
            job.refresh()
        except rq.exceptions.NoSuchJobError:
            joblist.remove(job)
            continue

        l.append(
            {
                "id": job.get_id(),
                "state": job.get_status(),
                "progress": job.meta.get("progress"),
                "result": job.result,
            }
        )

    return render_template("index.html", joblist=l)


@app.route("/enqueuejob", methods=["GET", "POST"])
def enqueuejob():
    job = jobs.approximate_pi.queue(int(request.form["num_iterations"]))
    joblist.append(job)
    return redirect("/")


@app.route("/allocate_json/", methods=["POST"])
def allocate_json():
    print("hello")
    if request.method == "POST":
        configSearch = request.args.get("configSearch")
        studentPreferencesJson = request.get_json()["pref"]
        studentPreferences = {int(k): v for k, v in studentPreferencesJson.items()}
        StaffProjMapJson = request.get_json()["staff"]
        StaffProj = {int(k): v for k, v in StaffProjMapJson.items()}

        if "config" in request.get_json():
            configdict = request.get_json()["config"]
            config = Config.from_dict(configdict)
        else:
            config = Config()
        # there must be a cleaner way
        new_special = {}
        for k, v in config.specialLoading.items():
            new_special[int(k)] = v
        config.specialLoading = new_special
        new_special = {}
        for k, v in config.disallowedMatching.items():
            new_special[int(k)] = v
        config.disallowedMatching = new_special
        new_special = {}
        for k, v in config.forcedMatching.items():
            new_special[int(k)] = v
        config.forcedMatching = new_special
        if not configSearch:
            job = jobs.run_allocation.queue(studentPreferences, StaffProj, config)
        else:
            job = jobs.run_allocation_configSearch.queue(
                studentPreferences, StaffProj, config
            )
        joblist.append(job)
        job_id = job.get_id()
        jobdict[job_id] = job
        return jsonify({"id": job.id}), 202


@app.route("/allocate_file/", methods=["POST"])
def allocate():
    if request.method == "POST":
        configSearch = request.args.get("configSearch")
        if "pref" not in request.files or "proj" not in request.files:
            return flask.Response(status=400)
        pref = request.files["pref"]
        proj = request.files["proj"]
        if not allowed_file(pref.filename):
            return flask.Response(status=400)
        if not allowed_file(pref.filename):
            return flask.Response(status=400)
        stream = io.StringIO(pref.stream.read().decode("utf-8-sig"), newline=None)
        inputDict = csv.DictReader(stream)
        if not set(["name", "P1", "N1"]).issubset(set(inputDict.fieldnames)):
            return ("", 400)
        studentPreferences = createStudentPrefMap(inputDict)
        stream2 = io.StringIO(proj.stream.read().decode("utf-8-sig"), newline=None)
        inputDict2 = csv.DictReader(stream2)
        if not set(["name", "P1", "N1"]).issubset(set(inputDict.fieldnames)):
            return ("", 400)
        StaffProj = createProjStaffMap(inputDict2)
        if not set(["PID", "SUP"]).issubset(set(inputDict2.fieldnames)):
            return ("", 400)
        if "config" in request.files:
            configfile = request.files["config"]
            stream3 = io.StringIO(
                configfile.stream.read().decode("utf-8-sig"), newline=None
            )
            configdict = json.load(stream3)
            config = Config.from_dict(configdict)
        else:
            config = Config()
        # there must be a cleaner way
        new_special = {}
        for k, v in config.specialLoading.items():
            new_special[int(k)] = v
        config.specialLoading = new_special
        new_special = {}
        for k, v in config.disallowedMatching.items():
            new_special[int(k)] = v
        config.disallowedMatching = new_special
        new_special = {}
        for k, v in config.forcedMatching.items():
            new_special[int(k)] = v
        config.forcedMatching = new_special
        if not configSearch:
            job = jobs.run_allocation.queue(studentPreferences, StaffProj, config)
        else:
            job = jobs.run_allocation_configSearch.queue(
                studentPreferences, StaffProj, config
            )
        joblist.append(job)
        job_id = job.get_id()
        jobdict[job_id] = job
        return jsonify({"id": job.id}), 202


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/deletejob", methods=["GET", "POST"])
def deletejob():
    if request.args.get("jobid"):
        job = rq.job.Job.fetch(request.args.get("jobid"), connection=jobs.rq.connection)
        job.delete()
    return redirect("/")


@app.route("/get_result/", methods=["GET"])
def get_results():
    id = request.args.get("job_id")
    job = jobdict.get(id)
    if job:
        res = job.result
        if res:
            return jsonify(res), 200
    return ("", 204)


@app.route("/get_progress/", methods=["GET"])
def get_progress():
    id = request.args.get("job_id")
    job = jobdict.get(id)
    if job:
        job.refresh()
        logging.warning(f"jobs progress {job}")
        return jsonify(job.meta.get("progress"))
    return ("", 204)


@app.route("/get_status/", methods=["GET"])
def get_status():
    id = request.args.get("job_id")
    job = jobdict.get(id)
    if job:
        return job.get_status()
    return ("", 204)


@app.route("/get_config/", methods=["GET"])
def get_config():
    id = request.args.get("job_id")
    job = jobdict.get(id)
    if job:
        job.refresh()
        logging.warning(f"jobs progress {job}")
        return jsonify(dataclasses.asdict(job.meta.get("config"))), 200
    return ("", 204)


@app.route("/add", methods=["POST"])
def add():
    data = request.get_json()
    test["a"] = 4
    return jsonify({"sum": data["a"] + data["b"]})


@app.route("/vroom", methods=["GET"])
def vroom():
    return "vroom"