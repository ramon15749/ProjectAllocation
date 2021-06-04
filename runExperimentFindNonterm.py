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


def main(path, result_path, config):
    print(f"path {path}")
    studentPref = path + "/prefs.csv"
    ProjectInfo = path + "/proj.csv"
    print(f"pref {studentPref}")

    with open(studentPref, mode="r", encoding="utf-8-sig") as infile:
        inputDict = csv.DictReader(infile)
        studentPreferences = createStudentPrefMap(inputDict)
    with open(ProjectInfo, mode="r", encoding="utf-8-sig") as infile:
        inputDict = csv.DictReader(infile)
        StaffProjMap = createProjStaffMap(inputDict)
    stats, results = data_collection(
        studentPreferences, StaffProjMap, config, result_path
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


def data_collection(studentPreferences, StaffProjMap, config, location):
    stats = {}
    results = {}
    maxVal = 300

    result = None
    costMap = getCostMap(studentPreferences)
    start = time.time()
    i = 10
    result = bestAllocate(studentPreferences, StaffProjMap, config=config)
    stats[i] = getStat(result, costMap, StaffProjMap)
    metric = "AvgRank"
    print(
        f"Iteration {i} | Been running for {(time.time() - start):.2f}s | {metric}: {stats[i][metric]:.4f}"
    )
    stats[i]["Duration"] = time.time() - start
    start = time.time()
    results[i] = result
    return stats, results


if __name__ == "__main__":
    config = Config()
    try:
        loc = sys.argv[1]
        filename = sys.argv[2]
        argv = sys.argv[3:]
        opts, args = getopt.getopt(argv, "hmd:l:r:s:c:u:v:", ["ifile=", "ofile="])
    except getopt.GetoptError:
        print("test.py <loc> -o")
        sys.exit(2)
    for opt, arg in opts:
        if opt == "-h":
            print(
                "test.py <loc> -d <maxDepth> -l <defautlload> -r <maxRank> -ws <weightStaff> -wr <weightRank> -wu <weightUnfair> -wl <weightVarLoad>"
            )
            sys.exit()
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
        elif opt in ("-weightVarLoad", "-l"):
            config.weightVarLoad = float(arg)

    main(loc, filename, config)