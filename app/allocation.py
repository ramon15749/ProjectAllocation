from collections import deque, defaultdict, namedtuple
from dataclasses import dataclass, field
from pprint import pprint
from typing import Dict, NewType, Tuple, List, Deque, Set, NamedTuple, Optional
import csv
import logging
import random
import sys
from statistics import pvariance, mean, variance
from functools import partial, reduce

from dataclasses_json import dataclass_json
import numpy as np

StudentID = NewType("StudentID", int)
StaffID = NewType("StaffID", int)
ProjectID = NewType("ProjectID", int)
Move = Tuple[StudentID, ProjectID]


@dataclass_json
@dataclass
class Config:
    maxDepth: int = 5
    defaultLoad: int = 5
    specialLoading: Dict[StaffID, int] = field(default_factory=dict)
    forcedMatching: Dict[StudentID, ProjectID] = field(default_factory=dict)
    disallowedMatching: Dict[StudentID, ProjectID] = field(default_factory=dict)
    preferredStudent: Dict[StudentID, ProjectID] = field(default_factory=dict)
    numRuns: int = 5
    maxRank: int = 8
    costUnalloc: int = 100
    costNoStaffPref: int = 10
    weightStaff: float = 10
    weightRank: int = 1
    weightUnfair: float = 0.1
    weightVarLoad: float = 0.01
    steepest: bool = False
    # earlyStopping: float = 10


def local_run(studentPref, ProjectInfo, maxDepth=7):
    with open(studentPref, mode="r", encoding="utf-8-sig") as infile:
        inputDict = csv.DictReader(infile)
        studentPreferences = createStudentPrefMap(inputDict)
    with open(ProjectInfo, mode="r", encoding="utf-8-sig") as infile:
        inputDict = csv.DictReader(infile)
        StaffProjMap = createProjStaffMap(inputDict)
    config = Config()
    alloc = bestAllocate(studentPreferences, StaffProjMap, config)
    return alloc


def createProjStaffMap(inputDict: List[Dict[str, str]]) -> Dict[ProjectID, StaffID]:
    ret: Dict[ProjectID, StaffID] = {}
    for row in inputDict:
        ret[ProjectID(int(row["PID"]))] = StaffID(int(row["SUP"]))
    return ret


def patchMap(
    studentPreferences: Dict[StudentID, List[ProjectID]],
    ProjStaffMap: Dict[ProjectID, StaffID],
):
    allProjects = set(sum(studentPreferences.values(), []))
    existingProject = set(ProjStaffMap.keys())
    for proj in allProjects.difference(existingProject):
        ProjStaffMap[proj] = StaffID(0)

    return ProjStaffMap


def bestAllocate(
    studentPreferences: Dict[StudentID, List[Tuple[ProjectID, int]]],
    projStaffMap: Dict[ProjectID, StaffID],
    staffPreferences: Dict[ProjectID, List[Tuple[StudentID, int]]] = None,
    config: Config = Config(),
) -> Dict[StudentID, ProjectID]:
    cost = None
    result = None
    # remove matching so it is not possible
    costMap_original = getCostMap(studentPreferences, config)
    studentPreferences = removeDisallowedMatching(studentPreferences, config)
    # remove matching and student then add the matching in the final allocation
    studentPreferences = removeForcedMatching(studentPreferences, config)
    # remove project outside maxRank
    studentPreferences = removeAboveMaxRank(studentPreferences, config)
    # remove less preferred student
    studentPreferences = setPreferredStudent(studentPreferences, config)
    costMap = getCostMap(studentPreferences, config)
    staffCostMap = getStaffCostMap(staffPreferences, config)
    studentProjectList = {
        student: [proj for proj, _ in projList]
        for student, projList in studentPreferences.items()
    }
    counter = 0
    i = 0
    for i in range(config.numRuns):
        r = allocate(studentProjectList, projStaffMap, config, costMap, staffCostMap)
        # add back forced matching
        r = addForcedMatching(r, config)
        currentCost = (
            config.weightStaff * sumCost(r, staffCostMap)
            + config.weightRank * sumCost(r, costMap_original)
            + config.weightUnfair * costUnfair(r, costMap_original)
            + (
                config.weightVarLoad
                * absolute_deviation(getLoadMap(projStaffMap, r).values())
                / len(r)
            )
        )
        if cost == None:
            result = r
            cost = currentCost
            continue
        # if config.earlyStopping != 0:
        #     if currentCost >= cost:
        #         counter += 1
        # if counter > config.earlyStopping:
        #     break
        result = r if currentCost < cost else result
        cost = currentCost if currentCost < cost else cost
    # print(f"stopped at {i}")

    return result


def absolute_deviation(input):
    if len(input) == 0:
        return 0
    meanVal = mean(input)
    return sum([abs(meanVal - x) for x in input])


def setPreferredStudent(
    pref: Dict[StudentID, List[Tuple[ProjectID, int]]], config: Config
) -> Dict[StudentID, List[Tuple[ProjectID, int]]]:
    out = pref.copy()
    for p_student, p_project in config.preferredStudent.items():
        cost = dict(out[p_student]).get(p_project)
        for s, proj_list in out.items():
            if s == p_student:
                continue
            if p_project in [proj for proj, _ in out[s]]:
                out[s] = [
                    (p, c) for p, c in proj_list if not (c >= cost and p_project == p)
                ]
    return out


def removeAboveMaxRank(
    pref: Dict[StudentID, List[Tuple[ProjectID, int]]], config: Config
) -> Dict[StudentID, List[Tuple[ProjectID, int]]]:
    out = pref.copy()
    for k, v in out.items():
        out[k] = [(p, c) for (p, c) in v if c <= config.maxRank]
    return out


def addForcedMatching(
    SPalloc: Dict[StudentID, ProjectID], config: Config
) -> Dict[StudentID, ProjectID]:
    out = SPalloc.copy()
    for s, p in config.forcedMatching.items():
        out[s] = p
    return out


def removeDisallowedMatching(
    pref: Dict[StudentID, List[Tuple[ProjectID, int]]], config: Config
) -> Dict[StudentID, List[Tuple[ProjectID, int]]]:
    out = pref.copy()
    for s, p in config.disallowedMatching.items():
        if p in [proj for proj, _ in out[s]]:
            out[s] = [(proj, c) for proj, c in out[s] if proj != p]
    return out


def removeForcedMatching(
    pref: Dict[StudentID, List[Tuple[ProjectID, int]]], config: Config
) -> Dict[StudentID, List[Tuple[ProjectID, int]]]:
    out = pref.copy()
    for s, p in config.forcedMatching.items():
        if s in out.keys():
            out.pop(s)
        for s, prefList in out.items():
            if p in [pr for pr, _ in prefList]:
                out[s] = [(proj, cost) for proj, cost in prefList if proj != p]
    return out


def allocate(
    studentPreferences: Dict[StudentID, List[ProjectID]],
    ProjStaffMap: Dict[ProjectID, StaffID],
    config: Config,
    costMap: Dict[Move, int],
    staffCostMap: Dict[Move, int],
) -> Dict[StudentID, ProjectID]:
    histories: List[Optional[List[Move]]] = []
    ProjStaffMap = patchMap(studentPreferences, ProjStaffMap)
    SPalloc = preAssign(studentPreferences, ProjStaffMap, config)
    loadMap = getLoadMap(ProjStaffMap, SPalloc)
    projPref = getProjectPreferences(costMap)
    PSalloc = {v: k for k, v in SPalloc.items()}
    movement = getBestMovement(
        SPalloc,
        PSalloc,
        studentPreferences,
        ProjStaffMap,
        loadMap,
        costMap,
        staffCostMap,
        projPref,
        config,
    )
    i = 0
    while movement:
        loadMap, _ = ShiftLoadMap(SPalloc, loadMap, movement, ProjStaffMap)
        SPalloc, PSalloc = applyShiftOrRotate(SPalloc, PSalloc, movement)
        movement = getBestMovement(
            SPalloc,
            PSalloc,
            studentPreferences,
            ProjStaffMap,
            loadMap,
            costMap,
            staffCostMap,
            projPref,
            config,
        )
        i += 1
        if i > 1000:
            if movement in histories:
                print("infiniteLoop")
                break
            histories += [movement]
    assert len(studentPreferences) == len(SPalloc)
    return SPalloc


def preAssign(
    studentPreferences: Dict[StudentID, List[ProjectID]],
    StaffProjectMap: Dict[ProjectID, StaffID],
    config: Config,
) -> Dict[StudentID, ProjectID]:
    students = list(studentPreferences.keys())
    random.shuffle(students)
    allocationMap: Dict[StudentID, ProjectID] = {}
    loadingMap: Dict[StaffID, int] = defaultdict(int)

    for s in students:
        allocationMap[s] = ProjectID(0)  # unallocated
        for choice in studentPreferences[s]:
            staff = StaffProjectMap[choice]
            if staff != 0 and loadingMap[staff] >= config.specialLoading.get(
                staff, config.defaultLoad
            ):
                continue
            if choice not in allocationMap.values():
                allocationMap[s] = choice
                loadingMap[StaffProjectMap[choice]] += 1
                break
    return allocationMap


# now costmap only track the preference order
def getCostMap(
    studentPreferencesCost: Dict[StudentID, List[Tuple[ProjectID, int]]],
    config: Config = Config(),
) -> Dict[Tuple[StudentID, ProjectID], int]:
    costMap: Dict[Tuple[StudentID, ProjectID], int] = {}
    for s, projects in studentPreferencesCost.items():
        for project, cost in projects:
            if project != 0:
                costMap[(s, project)] = cost
        costMap[(s, ProjectID(0))] = config.costUnalloc
    return costMap


def getStaffCostMap(
    staffPreferencesCost: Optional[Dict[ProjectID, List[Tuple[StudentID, int]]]],
    config: Config = Config(),
) -> Dict[Tuple[StudentID, ProjectID], int]:
    if not staffPreferencesCost:
        return defaultdict(int)
    costMap: Dict[Tuple[StudentID, ProjectID], int] = defaultdict(
        lambda: config.costNoStaffPref
    )
    for project, students in staffPreferencesCost.items():
        for s, cost in students:
            if project != 0:
                costMap[(s, project)] = cost
    return costMap


def getBestMovement(
    SPalloc: Dict[StudentID, ProjectID],
    PSalloc: Dict[ProjectID, StudentID],
    studentPreferences: Dict[StudentID, List[ProjectID]],
    StaffProjectMap: Dict[ProjectID, StaffID],
    loadMap: Dict[StaffID, int],
    costMap: Dict[Move, int],
    staffCostMap: Dict[Move, int],
    projPref: Dict[ProjectID, List[int]],
    config: Config,
) -> Optional[List[Move]]:
    possibleMoves = []
    for s in SPalloc.keys():
        possibleMoves.extend(
            BFS(
                s,
                SPalloc,
                PSalloc,
                studentPreferences,
                StaffProjectMap,
                costMap,
                staffCostMap,
                loadMap,
                projPref,
                config,
            )
        )
        if config.steepest:
            if len(possibleMoves) > 0:
                return possibleMoves[0][0]
    if len(possibleMoves) == 0:
        return None
    cycle, _, _ = min(possibleMoves, key=lambda t: t[2])
    return cycle


def BFS(
    s: StudentID,
    SPallocation: Dict[StudentID, ProjectID],
    PSallocation: Dict[ProjectID, StudentID],
    studentPreferences: Dict[StudentID, List[ProjectID]],
    projStaffMap: Dict[ProjectID, StaffID],
    costMap: Dict[Move, int],
    staffCostMap: Dict[Move, int],
    loadMap: Dict[StaffID, int],
    projPref: Dict[ProjectID, List[int]],
    config: Config,
) -> List[Tuple[List[Move], bool, float]]:
    cycle_or_shift: List[Tuple[List[Move], bool, float]] = []
    q: Deque[Tuple[StudentID, int, int, List[Move]]] = deque()
    q.append((s, 0, 0, []))
    meanLoad = mean(loadMap.values())
    while q:
        x, depth, partialSum, path = q.popleft()
        if x == s and depth != 0:
            if partialSum < 0:
                cycle_or_shift.append((path, False, partialSum))
                if not config.steepest:
                    return cycle_or_shift
        if x not in [x for x, _ in path]:
            depth += 1
            if depth > config.maxDepth:
                continue
            moves = studentPreferences[x].copy() + [ProjectID(0)]
            random.shuffle(moves)
            for project in moves:
                if project == SPallocation[x]:
                    continue
                movePath = path + [(x, project)]
                movePartialSum = partialSum + getMoveCost(
                    costMap, staffCostMap, SPallocation, (x, project), projPref, config
                )
                if isValid(x, project, SPallocation, movePartialSum):
                    # check if the project is a valid shift
                    if project not in PSallocation or project == 0:
                        localLoadMap, costShift = ShiftLoadMap(
                            SPallocation, loadMap, movePath, projStaffMap
                        )
                        movePartialSum += config.weightVarLoad * costShift
                        if checkload(localLoadMap, config) and movePartialSum < 0:
                            cycle_or_shift.append((movePath, True, movePartialSum))
                            if not config.steepest:
                                return cycle_or_shift
                        continue
                    q.append((PSallocation[project], depth, movePartialSum, movePath))
    return cycle_or_shift


def isValid(
    s: StudentID, move: ProjectID, SPalloc: Dict[StudentID, ProjectID], partialSum: int
) -> bool:
    if SPalloc[s] == move:
        return False
    if partialSum >= 0:
        return False
    return True


def isValidShift(partialSum) -> bool:
    return partialSum < 0


def getVarLoad(loadMap: Dict[StaffID, int], staff: StaffID, mean: float) -> float:
    return abs(loadMap[staff] - mean)


def getMoveCost(costMap, staffCostMap, SPalloc, move, projPref, config):
    x, project = move
    deltaUnfair = 0
    deltaCost = costMap[(x, project)] - costMap[(x, SPalloc[x])]
    deltaStaffCost = staffCostMap[(x, project)] - staffCostMap[(x, SPalloc[x])]
    if config.weightUnfair != 0:
        deltaUnfair = getUnfair(x, project, projPref, costMap) - getUnfair(
            x, SPalloc[x], projPref, costMap
        )
    return (
        config.weightStaff * deltaStaffCost
        + config.weightRank * deltaCost
        + config.weightUnfair * deltaUnfair
    )


def getUnfair(
    student: StudentID,
    project: ProjectID,
    projPref: Dict[ProjectID, List[int]],
    costMap: Dict[Move, int],
) -> int:
    cost = costMap[(student, project)]
    if project == ProjectID(0):
        return 0
    return sum([x for x in projPref[project] if x < cost])


def checkload(localLoadMap, config) -> bool:
    for k, v in localLoadMap.items():
        maxLoad = config.specialLoading.get(k, config.defaultLoad)
        if v > maxLoad:
            return False
    return True


# def BFS_steepest(
#    s: StudentID,
#    SPallocation: Dict[StudentID, ProjectID],
#    PSallocation: Dict[ProjectID, StudentID],
#    studentPreferences: Dict[StudentID, List[ProjectID]],
#    costMap: Dict[Move, int],
#    staffCostMap: Dict[Move, int],
#    maxDepth: int,
# ) -> List[Tuple[List[Move], bool]]:
#    cycle_or_shift: List[Tuple[List[Move], int, bool]] = []
#    q: Deque[Tuple[StudentID, int, int, List[Move]]] = deque()
#    q.append((s, 0, 0, []))
#    while q:
#        x, depth, partialSum, path = q.popleft()
#        if x == s and depth != 0:
#            cycle_or_shift.append((path, partialSum, False))
#            continue
#        if x not in [x for x, _ in path]:
#            depth += 1
#            if depth > maxDepth:
#                continue
#            moves = studentPreferences[x].copy()
#            random.shuffle(moves)
#            for project in moves:
#                if project == SPallocation[x]:
#                    continue
#                movePath = path + [(x, project)]
#                movePartialSum = (
#                    partialSum + costMap[(x, project)] - costMap[(x, SPallocation[x])]
#                )
#                assert costMap[(x, project)] != costMap[(x, SPallocation[x])]
#                if isValid(x, project, SPallocation, movePartialSum):
#                    if project not in PSallocation:
#                        cycle_or_shift.append((movePath, movePartialSum, True))
#                        continue
#                    q.append((PSallocation[project], depth, movePartialSum, movePath))
#    if len(cycle_or_shift) == 0:
#        return []
#    index_min = np.argmin([partialSum for moves, partialSum, isShift in cycle_or_shift])
#    m: List[Move]
#    shift: bool
#    m, p, shift = cycle_or_shift[index_min]
#    return [(m, shift)]


def createStudentPrefMap(
    inputDict: List[Dict[str, str]]
) -> Dict[StudentID, List[Tuple[ProjectID, int]]]:
    ret: Dict[StudentID, List[Tuple[ProjectID, int]]] = {}
    for row in inputDict:
        ret[StudentID(int(row["name"]))] = getPrefListFromMap(row)
    return ret


def getPrefListFromMap(studentDict: Dict[str, str]) -> List[Tuple[ProjectID, int]]:
    projectList: List[Tuple[ProjectID, int]] = []
    for i in range(1, 11):
        projectList.append(
            (
                ProjectID(int(studentDict["P" + str(i)])),
                int(studentDict["N" + str(i)]),
            )
        )
    return projectList


def applyShiftOrRotate(
    SPalloc: Dict[StudentID, ProjectID],
    PSalloc: Dict[ProjectID, StudentID],
    moves: List[Move],
) -> Tuple[Dict[StudentID, ProjectID], Dict[ProjectID, StudentID]]:
    SPalloc1 = SPalloc.copy()
    for move in moves:
        SPalloc1[move[0]] = move[1]
    return SPalloc1, {v: k for k, v in SPalloc1.items()}


def getLoadMap(
    StaffProjectMap: Dict[ProjectID, StaffID], SPalloc: Dict[StudentID, ProjectID]
) -> Dict[StaffID, int]:
    ret: Dict[StaffID, int] = defaultdict(int)
    for proj in SPalloc.values():
        if proj == 0:
            continue
        if StaffProjectMap[proj] != 0:
            ret[StaffProjectMap[proj]] += 1
    return ret


def ShiftLoadMap(
    SPalloc: Dict[StudentID, ProjectID],
    loadMap: Dict[StaffID, int],
    moves: List[Move],
    StaffProjectMap: Dict[ProjectID, StaffID],
) -> Tuple[Dict[StaffID, int], float]:
    meanLoad = mean(loadMap.values())
    copiedLoadMap = loadMap.copy()
    projRemove = SPalloc[moves[0][0]]
    projAdd = moves[-1][1]
    costLoad = 0.0
    if projAdd != 0:
        staffAdd = StaffProjectMap[projAdd]
        if staffAdd != 0:
            costLoad -= abs(copiedLoadMap[staffAdd] - meanLoad)
            copiedLoadMap[staffAdd] += 1
            costLoad += abs(copiedLoadMap[staffAdd] - meanLoad)
    if projRemove != 0:
        staffRemove = StaffProjectMap[projRemove]
        if staffRemove != 0:
            costLoad -= abs(copiedLoadMap[staffRemove] - meanLoad)
            copiedLoadMap[staffRemove] -= 1
            costLoad += abs(copiedLoadMap[staffRemove] - meanLoad)
    assert min(copiedLoadMap.values()) >= 0, "min is {}".format(
        min(copiedLoadMap.values())
    )
    return copiedLoadMap, costLoad


def sumCost(
    SPalloc: Dict[StudentID, ProjectID],
    costMap: Dict[Move, int],
    skipUnassign: bool = False,
) -> int:
    sum: int = 0
    for k, v in SPalloc.items():
        if not skipUnassign or v != ProjectID(0):
            sum += costMap[(k, v)]
    return sum


def getProjectPreferences(costMap: Dict[Move, int]) -> Dict[ProjectID, List[int]]:
    projectStudentPref: Dict[ProjectID, List[int]] = defaultdict(list)
    for (_, proj), cost in costMap.items():
        projectStudentPref[proj] += [cost]
    return projectStudentPref


def getUnfairDict(
    SPalloc: Dict[StudentID, ProjectID], costMap: Dict[Move, int]
) -> Dict[ProjectID, List[int]]:
    projectStudentPref = getProjectPreferences(costMap)
    costs = {}
    for s, p in SPalloc.items():
        current = costMap[(s, p)]
        filtered = list(
            filter(lambda x: True if x < current else False, projectStudentPref[p])
        )
        costs[p] = [current - x for x in filtered]

    return costs


def costUnfair(SPalloc: Dict[StudentID, ProjectID], costMap: Dict[Move, int]):
    unfair = getUnfairDict(SPalloc, costMap)
    return reduce(lambda acc, x: acc + sum(x), unfair.values(), 0)


if __name__ == "__main__":
    local_run(sys.argv[1], sys.argv[2])
