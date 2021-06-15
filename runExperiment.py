from app.allocation import *
import matplotlib.pyplot as plt
from app.alloc_metric import *
from pprint import pprint
from collections import defaultdict
import time
import json
import math
import numpy as np
import sys, getopt
import os
import csv


def main(path, result_path, config, load, csvInput):
    print(f"path {path}")
    print(f"config {config}")
    with open(result_path + "_config", "w") as config_file:
        json.dump(config.to_json(), config_file)
    fileEnding = ".csv" if csvInput else ".json"
    studentPref = path + "/prefs" + fileEnding
    ProjectInfo = path + "/proj" + fileEnding
    print(f"pref {studentPref}")

    if not csvInput:
        with open(studentPref) as pref_f:
            studentPreferencesJson = json.load(pref_f)
            studentPreferences = {int(k): v for k, v in studentPreferencesJson.items()}
        with open(ProjectInfo) as proj_f:
            StaffProjMapJson = json.load(proj_f)
            StaffProjMap = {int(k): v for k, v in StaffProjMapJson.items()}
    else:
        with open(studentPref, mode="r", encoding="utf-8-sig") as infile:
            inputDict = csv.DictReader(infile)
            studentPreferences = createStudentPrefMap(inputDict)
        with open(ProjectInfo, mode="r", encoding="utf-8-sig") as infile:
            inputDict = csv.DictReader(infile)
            StaffProjMap = createProjStaffMap(inputDict)
            print(StaffProjMap)

    stats, results = data_collection(
        studentPreferences, StaffProjMap, config, result_path, load
    )
    cleanStat = getMetricList(stats)
    plotAllMetric(cleanStat)


def plotAllMetric(new_stats):
    fig, axes = plt.subplots(len(new_stats), 1, figsize=(10, 20), sharey="row")
    for i, ((metric, l)) in enumerate(new_stats.items()):
        axes[i].plot(list(l.keys()), list(l.values()), label="Depth")
        axes[i].set_ylabel(metric)
    axes[0].set_title("Metrics")
    fig.tight_layout()
    plt.show()


def getMetricList(stats_maxRank):
    new_stats = defaultdict(dict)
    for load, stat in stats_maxRank.items():
        for metric, val in stat.items():
            new_stats[metric][load] = val

    for metric, val in new_stats.items():
        sort_dict = dict(sorted(val.items(), key=lambda item: int(item[0])))
        new_stats[metric] = {int(a): float(b) for a, b in sort_dict.items()}
    return new_stats


def data_collection(studentPreferences, StaffProjMap, config, location, load):
    results = {}
    maxVal = 10
    stats = {}
    startInterval = 1

    if load:
        with open(location + "_results", "r") as res_file:
            results = json.load(res_file)
        with open(location + "_stats", "r") as stat_file:
            stats = json.load(stat_file)
        startInterval = int(list(stats.keys())[-1])
    costMap = getCostMap(studentPreferences)
    start = time.time()
    scale = [j for j in range(startInterval, maxVal + 1, 1)]
    scale = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 50, 100]
    print(scale)
    for i in scale:
        config.costUnalloc = i
        metric = "AvgRank"
        print(config)
        result = bestAllocate(studentPreferences, StaffProjMap, config=config)
        stats[i] = getStat(result, costMap, StaffProjMap)
        print(
            f"Iteration {i} | Been running for {(time.time() - start):.2f}s | {metric}: {stats[i][metric]:.4f}"
        )
        stats[i]["Duration"] = time.time() - start
        start = time.time()
        results[i] = result
        with open(location + "_results", "w") as res_file:
            json.dump(results, res_file)
        with open(location + "_stats", "w") as stat_file:
            json.dump(stats, stat_file)
    return stats, results


if __name__ == "__main__":
    config = Config()
    previousRes = False
    csvInput = False
    try:
        loc = sys.argv[1]
        filename = sys.argv[2]
        argv = sys.argv[3:]
        opts, args = getopt.getopt(argv, "hfmd:l:r:s:c:u:v:p:n:", ["ifile=", "ofile="])
    except getopt.GetoptError:
        print("test.py <loc> -o")
        sys.exit(2)
    for opt, arg in opts:
        if opt == "-h":
            print(
                "test.py <loc> -d <maxDepth> -l <defautlload> -r <maxRank> -ws <weightStaff> -wr <weightRank> -wu <weightUnfair> -wl <weightVarLoad>"
            )
            sys.exit()
        elif opt == "-f":
            csvInput = True
        elif opt in ("--maxDepth", "-d"):
            config.maxDepth = int(arg)
        elif opt in ("--defaultLoad", "-l"):
            config.defaultLoad = int(arg)
        elif opt in ("-maxRank", "-r"):
            config.maxRank = int(arg)
        elif opt in ("-weightStaff", "-s"):
            config.weightStaff = float(arg)
        elif opt in ("-weightRank", "-c"):
            config.weightRank = int(arg)
        elif opt in ("-weightUnfair", "-u"):
            config.weightUnfair = float(arg)
        elif opt in ("-weightVarLoad", "-v"):
            config.weightVarLoad = float(arg)
        elif opt in ("-numRuns", "-n"):
            config.numRuns = int(arg)
        elif opt in ("--steep", "-p"):
            config.steepest = True
    print(csvInput)

    main(loc, filename, config, previousRes, csvInput)
