#!/usr/bin/python3

import numpy as np
import math
from collections import defaultdict
import argparse
import json

if __name__ == "main":
    parser = argparse.ArgumentParser()
    parser.add_argument("noStudent", help="The number student for the allocation")
    parser.add_argument(
        "tightness", help="The ratio between number of projects and students"
    )
    parser.add_argument("savePath", help="the location of the result file")
    parser.add_argument("-l", "--load", type=int, default=5, help="load per staff")
    parser.add_argument(
        "-c",
        "--numChoice",
        type=int,
        default=10,
        help="Number of choice student has make",
    )
    parser.add_argument(
        "-p",
        "--popularity",
        type=float,
        default=10,
        help="Student General Ratio (how much students pref depends on popularity",
    )
    parser.add_argument(
        "-s",
        "--specific",
        type=float,
        default=10,
        help="Project Staff Ratio (how much students pref depends on the project and the staff",
    )
    parser.add_argument(
        "-e",
        "--equalRank",
        type=float,
        default=10,
        help="How close the preferences has to be for the rank to be equal",
    )
    parser.add_argument(
        "--csv", help="to save file in .csv format", action="store_true"
    )

    args = parser.parse_args()
    print(args)


def main(
    noStudent,
    tightness,
    load,
    numChoices,
    ratioProjectStaff,
    ratioStudentGeneral,
    equalCloseness,
    savePath,
    csv,
):
    studentPref, staffProjMap = createMockData(
        noStudent,
        tightness,
        load,
        numChoices,
        ratioProjectStaff,
        ratioStudentGeneral,
        equalCloseness,
    )
    if csv:
        return

    with open(savePath + "/pref.json") as pref:
        json.dump(studentPref, pref)
    with open(savePath + "/proj.json") as proj:
        json.dump(staffProjMap, proj)


def createMockData(
    noStudent,
    tightness,
    load,
    num_choices,
    ratioProjectStaff,
    ratioStudentGeneral,
    equalCloseness,
):
    noStaff = math.ceil((noStudent * tightness) / load)
    projectPop = [np.random.normal(scale=1.0) for i in range(load * noStaff)]
    staffPop = [np.random.normal(scale=ratioProjectStaff) for i in range(noStaff)]
    staffProjMap = {
        i + 1: j for i, j in enumerate(np.repeat(np.arange(1, noStaff + 1), load))
    }
    studentPreferences = defaultdict(list)
    for i in range(noStudent):
        projectFit = [
            ratioStudentGeneral * np.random.normal(scale=1.0)
            for i in range(len(projectPop))
        ]
        staffFit = [
            ratioStudentGeneral * np.random.normal(scale=ratioProjectStaff)
            for i in range(len(staffPop))
        ]
        totalStaffPref = np.add(staffPop, staffFit)
        totalProjPref = np.add(projectPop, projectFit)
        finalPref = np.add(totalProjPref, np.repeat(totalStaffPref, load))
        finalPref = np.array([x / sum(finalPref) for x in finalPref])
        selectedProject = np.argsort(-finalPref)[:num_choices]
        studentPreferences[i] += [(selectedProject[0], 1)]
        rank = 1
        for j, (proj, prev_proj) in enumerate(
            zip(selectedProject[1:], selectedProject)
        ):
            rank = (
                rank
                if finalPref[prev_proj] - finalPref[proj] < equalCloseness
                else j + 2
            )
            studentPreferences[i] += [(proj + 1, rank)]
    return studentPreferences, staffProjMap