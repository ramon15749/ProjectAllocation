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

from flask import request, jsonify, flash, redirect, send_from_directory, url_for, abort
from flask_cors import CORS, cross_origin
from redis import Redis
from werkzeug.utils import secure_filename
import flask
import rq

from allocation import *
import consts

ALLOWED_EXTENSIONS = ["csv"]
app = flask.Flask(__name__)
cors = CORS(app)

jobs.rq.init_app(app)


# For sake of simplicty, we keep track of the jobs we've launched
# in memory. This will only work as long there is only one python
# process (web server context) and it must not get restarted.
# In advanced use cases you want to keep track of jobs by their ids
# and utilize sessions and redis.
joblist = []
jobdict = {}


@app.route('/')
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

        l.append({
            'id': job.get_id(),
            'state': job.get_status(),
            'progress': job.meta.get('progress'),
            'result': job.result
            })

    return render_template('index.html', joblist=l)


@app.route('/enqueuejob', methods=['GET', 'POST'])
def enqueuejob():
    job = jobs.approximate_pi.queue(int(request.form['num_iterations']))
    joblist.append(job)
    return redirect('/')

@app.route("/allocate/", methods=["POST"])
def allocation():
    if request.method == "POST":
        if "pref" not in request.files or "proj" not in request.files:
            return flask.Response(status=500)
        pref = request.files["pref"]
        proj = request.files["proj"]
        if not allowed_file(pref.filename):
            return flask.Response(status=500)
        if not allowed_file(pref.filename):
            return flask.Response(status=500)
        stream = io.StringIO(pref.stream.read().decode("utf-8-sig"), newline=None)
        inputDict = csv.DictReader(stream)
        studentPreferences = createStudentPrefMap(inputDict)
        stream2 = io.StringIO(proj.stream.read().decode("utf-8-sig"), newline=None)
        inputDict2 = csv.DictReader(stream2)
        ProfProj = createProjProfMap(inputDict2)
        if "config" in request.files:
            configfile = request.files["config"]
            stream3 = io.StringIO(
                configfile.stream.read().decode("utf-8-sig"), newline=None
            )
            configdict = json.load(stream3)
            app.logger.info(f"configdict {configdict}")
            config = Config.from_dict(configdict)
        else:
            config = Config()
        job = jobs.run_allocation.queue(
            studentPreferences, ProfProj, config
        )
        joblist.append(job)
        jobdict[job.get_id()] = job
        app.logger.info(f"config {job.id}")
        return jsonify({"id": job.id}), 202

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/deletejob', methods=['GET', 'POST'])
def deletejob():
    if request.args.get('jobid'):
        job = rq.job.Job.fetch(request.args.get('jobid'), connection=jobs.rq.connection)
        job.delete()
    return redirect('/')

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
        return jsonify(job.meta.get('progress'))
    return ("", 204)

@app.route("/get_status/", methods=["GET"])
def get_status():
    id = request.args.get("job_id")
    job = jobdict.get(id)
    if job:
        return job.get_status()
    return ("", 204)
