from collections import deque, defaultdict, namedtuple
from dataclasses import dataclass, field
from pprint import pprint
from typing import (
    Dict,
    NewType,
    Tuple,
    List,
    Deque,
    Set,
    NamedTuple,
    Optional,
    Callable,
    Generator,
)
import random
import sys
from statistics import pvariance, mean, variance
from functools import partial, reduce
import time
import math
import statistics as stat
from copy import deepcopy

from dataclasses_json import dataclass_json
import numpy as np

StudentID = NewType("StudentID", int)
StaffID = NewType("StaffID", int)
ProjectID = NewType("ProjectID", int)
Move = Tuple[StudentID, ProjectID]
PrefType = Dict[StudentID, List[Tuple[ProjectID, int]]]

globalPruneCount = 0
globaltotalCount = 0


@dataclass_json
@dataclass
class Config:
    maxDepth: int = 10
    defaultLoad: int = 5
    specialLoading: Dict[StaffID, int] = field(default_factory=dict)
    forcedMatching: Dict[StudentID, ProjectID] = field(default_factory=dict)
    disallowedMatching: Dict[StudentID, ProjectID] = field(default_factory=dict)
    preferredStudent: Dict[StudentID, ProjectID] = field(default_factory=dict)
    numRuns: int = 20
    maxRank: int = 8
    costUnalloc: int = 100
    costNoStaffPref: int = 10
    weightStaff: float = 10
    weightRank: int = 1
    weightUnfair: float = 0.1
    weightVarLoad: float = 0.01
    steepest: bool = False
    preAssignType: str = "RSD"
    # earlyStopping: float = 10


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


def applyPreallocConstraints(
    studentPreferences: PrefType,
    config: Config = Config(),
) -> PrefType:
    studentPreferences = setPreferredStudent(studentPreferences, config)
    studentPreferences = removeDisallowedMatching(studentPreferences, config)
    # remove matching and student then add the matching in the final allocation
    studentPreferences = removeForcedMatching(studentPreferences, config)
    # remove project outside maxRank
    studentPreferences = removeAboveMaxRank(studentPreferences, config)
    # remove less preferred student
    return studentPreferences


def bestAllocateAllResults(
    studentPreferences: PrefType,
    projStaffMap: Dict[ProjectID, StaffID],
    staffPreferences: Dict[ProjectID, List[Tuple[StudentID, int]]] = None,
    config: Config = Config(),
    callback: Generator[None, Optional[float], None] = None,
) -> Tuple[List[Dict[StudentID, ProjectID]], List[float]]:
    if callback:
        callback.send(None)
    costMap_original = getCostMap(studentPreferences, config)
    studentPreferences = applyPreallocConstraints(studentPreferences, config)
    staffCostMap = getStaffCostMap(staffPreferences, config)
    costMap = getCostMap(studentPreferences, config)
    # remove matching so it is not possible
    studentProjectList = {
        student: [proj for proj, _ in projList]
        for student, projList in studentPreferences.items()
    }
    counter = 0
    results = []
    cost = None
    costs = []
    i = 0
    for i in range(config.numRuns):
        # print(i)
        start_time = time.time()
        r = allocate(studentProjectList, projStaffMap, config, costMap, staffCostMap)
        # add back forced matching
        r = addForcedMatching(r, config)
        currentCost = getcurrentCost(
            config, r, costMap_original, staffCostMap, projStaffMap
        )
        costs += [currentCost / len(r)]
        if cost == None:
            result = r
            cost = currentCost
            continue
        results += [r]
        if callback:
            callback.send(((i + 1) / config.numRuns) * 100)

    return results, costs


def getcurrentCost(config, r, costMap, staffCostMap, projStaffMap):
    return (
        config.weightStaff * sumCost(r, staffCostMap)
        + config.weightRank * sumCost(r, costMap)
        + config.weightUnfair * costUnfair(r, costMap)
        + (
            config.weightVarLoad
            * absolute_deviation(getLoadMap(projStaffMap, r).values())
            / len(r)
        )
    )


def bestAllocate(
    studentPreferences: PrefType,
    projStaffMap: Dict[ProjectID, StaffID],
    staffPreferences: Dict[ProjectID, List[Tuple[StudentID, int]]] = None,
    config: Config = Config(),
    callback: Generator[None, Optional[float], None] = None,
) -> Dict[StudentID, ProjectID]:
    cost = None
    result = {}
    # remove matching so it is not possible
    if callback:
        callback.send(None)
    costMap_original = getCostMap(studentPreferences, config)
    studentPreferences = applyPreallocConstraints(studentPreferences, config)
    staffCostMap = getStaffCostMap(staffPreferences, config)
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
        currentCost = getcurrentCost(
            config, r, costMap_original, staffCostMap, projStaffMap
        )
        if cost == None:
            result = r
            cost = currentCost
            continue

        result = r if currentCost < cost else result
        cost = currentCost if currentCost < cost else cost
        if callback:
            callback.send(((i + 1) / config.numRuns) * 100)

    return result


def absolute_deviation(input):
    if len(input) == 0:
        return 0
    meanVal = mean(input)
    return sum([abs(meanVal - x) for x in input])


def setPreferredStudent(pref: PrefType, config: Config) -> PrefType:
    out = deepcopy(pref)
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


def removeAboveMaxRank(pref: PrefType, config: Config) -> PrefType:
    out = deepcopy(pref)
    for k, v in out.items():
        out[k] = [(p, c) for (p, c) in v if c <= config.maxRank]
    return out


def addForcedMatching(
    SPalloc: Dict[StudentID, ProjectID], config: Config
) -> Dict[StudentID, ProjectID]:
    out = deepcopy(SPalloc)
    for s, p in config.forcedMatching.items():
        out[s] = p
    return out


def removeDisallowedMatching(pref: PrefType, config: Config) -> PrefType:
    out = deepcopy(pref)
    for s, p in config.disallowedMatching.items():
        if p in [proj for proj, _ in out[s]]:
            out[s] = [(proj, c) for proj, c in out[s] if proj != p]
    return out


def removeForcedMatching(pref: PrefType, config: Config) -> PrefType:
    out = deepcopy(pref)
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
    if config.preAssignType == "Random":
        SPalloc = preAssignRandom(studentPreferences, ProjStaffMap, config)
    else:
        SPalloc = preAssignRSD(studentPreferences, ProjStaffMap, config)
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
        # print(i)
        if i > 1000:
            if movement in histories:
                print("infiniteLoop")
                break
            histories += [movement]
    assert len(studentPreferences) == len(SPalloc)
    global globalPruneCount
    global globaltotalCount
    print(
        f"{globalPruneCount} / {globaltotalCount} = {globalPruneCount/globaltotalCount}"
    )
    return SPalloc


def preAssignRandom(
    studentPreferences: Dict[StudentID, List[ProjectID]],
    StaffProjectMap: Dict[ProjectID, StaffID],
    config: Config,
) -> Dict[StudentID, ProjectID]:
    students = list(studentPreferences.keys())
    random.shuffle(students)
    allocationMap: Dict[StudentID, ProjectID] = {}
    loadingMap: Dict[StaffID, int] = defaultdict(int)

    for s in students:
        choices = deepcopy(studentPreferences[s]) + [ProjectID(0)]
        random.shuffle(choices)
        for choice in choices:
            if choice == ProjectID(0):
                allocationMap[s] = choice
                continue

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


def preAssignRSD(
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
    studentPreferencesCost: PrefType,
    config: Config = Config(),
) -> Dict[Tuple[StudentID, ProjectID], int]:
    costMap: Dict[Tuple[StudentID, ProjectID], int] = {}
    for s, projects in studentPreferencesCost.items():
        for project, cost in projects:
            if project != 0:
                costMap[(s, project)] = cost
        if config.costUnalloc == -1:
            costMap[(s, ProjectID(0))] = len(studentPreferencesCost[s]) + 1
        else:
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
    while q:
        x, depth, partialSum, path = q.popleft()
        if x == s and depth != 0:
            if partialSum < 1e-15 and partialSum != 0:
                # print(partialSum)
                cycle_or_shift.append((path, False, partialSum))
                if not config.steepest:
                    return cycle_or_shift
        if x not in [x for x, _ in path]:
            depth += 1
            if depth > config.maxDepth:
                continue
            moves = deepcopy(studentPreferences[x]) + [ProjectID(0)]
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
                        if (
                            checkload(localLoadMap, config)
                            and movePartialSum < 1e-15
                            and partialSum != 0
                        ):
                            # print(movePartialSum)
                            cycle_or_shift.append((movePath, True, movePartialSum))
                            if not config.steepest:
                                return cycle_or_shift
                        continue
                    q.append((PSallocation[project], depth, movePartialSum, movePath))
    return cycle_or_shift


def isValid(
    s: StudentID, move: ProjectID, SPalloc: Dict[StudentID, ProjectID], partialSum: int
) -> bool:
    global globaltotalCount
    globaltotalCount += 1
    if SPalloc[s] == move:
        return False
    if partialSum >= 0:
        global globalPruneCount
        globalPruneCount += 1
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
        #    + config.weightUnfair * deltaUnfair
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


def createStudentPrefMap(inputDict: List[Dict[str, str]]) -> PrefType:
    ret: PrefType = {}
    for row in inputDict:
        ret[StudentID(int(row["name"]))] = getPrefTypeFromMap(row)
    return ret


def getPrefTypeFromMap(studentDict: Dict[str, str]) -> List[Tuple[ProjectID, int]]:
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
    SPalloc1 = deepcopy(SPalloc)
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
    copiedLoadMap = deepcopy(loadMap)
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


def findBestDepthandRuns(
    studentPreferences,
    StaffProjMap,
    staffPreferences=None,
    config=Config(),
    callback=None,
):
    progressGlobal = 0.0

    d = 1
    depth_histories = None
    bestNumRuns = -1
    if callback:
        callback.send(None)
    while True:
        print(f"running depth = {d}")
        if callback:
            progressGlobal = (d / 20) * 100
            callback.send(progressGlobal)
        print(f" progres {progressGlobal}")
        print(bestNumRuns)
        config.maxDepth = d
        d += 1
        results = []
        costs = []
        config.numRuns = 1
        startTime = time.time()
        r = bestAllocate(studentPreferences, StaffProjMap, config=config)
        duration = time.time() - startTime
        costMap_original = getCostMap(studentPreferences, config)
        staffCostMap = getStaffCostMap(staffPreferences, config)
        c = getcurrentCost(config, r, costMap_original, staffCostMap, StaffProjMap)
        results += [r]
        costs += [c]
        numRuns = max(min(math.floor(1200 / duration), 500), bestNumRuns)
        if numRuns < 3:
            if callback:
                callback.send(100)
            return rs[cs.index(min(cs))], (d, 500)
        config.numRuns = numRuns
        rs, cs = bestAllocateAllResults(studentPreferences, StaffProjMap, config=config)
        bestNumRuns = checkConverage(cs)
        if bestNumRuns == -1:
            depth_histories = None
            continue
        if min(cs) == depth_histories:
            if callback:
                callback.send(100)
            return rs[cs.index(min(cs))], (d - 1, bestNumRuns)
        if bestNumRuns != -1:
            depth_histories = min(cs)


def runWithoutConfig(
    studentPreferences, StaffProjMap, staffPreferences=None, config=Config()
):
    d = 1
    p_coverage = 0
    minPrev = None
    bestNumRuns = -1
    patient = 0
    while True:
        config.maxDepth = d
        results = []
        costs = []
        config.numRuns = 1
        startTime = time.time()
        r = bestAllocate(studentPreferences, StaffProjMap, config=config)
        duration = time.time() - startTime
        costMap_original = getCostMap(studentPreferences, config)
        staffCostMap = getStaffCostMap(staffPreferences, config)
        c = getcurrentCost(config, r, costMap_original, staffCostMap, StaffProjMap)
        results += [r]
        costs += [c]
        numRuns = min(math.floor(600 / duration), 300)
        if numRuns < 3:
            return None
        config.numRuns = numRuns
        rs, cs = bestAllocateAllResults(studentPreferences, StaffProjMap, config=config)
        if minPrev == min(cs):
            patient += 1
            if patient >= 3:
                return rs[cs.index(min(cs))], (d - 1, prev_numRuns)
            n = checkConverage(cs)
            if n == -1:
                n = numRuns
            prev_numRuns = n
        if minPrev == None or minPrev > min(cs):
            patient = 0
            minPrev = min(cs)

        d += 1


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def checkConverage(costs):
    toRuns = range(2, int(len(costs) / 3) + 1)
    for n in set(toRuns):
        list_costs = chunks(costs, n)
        mins = [min(l) for l in list_costs]
        if (mins.count(min(mins)) / len(mins)) > 0.80:
            return n
    return -1


def configSearch(
    studentPreferences, StaffProjMap, staffPref=None, config=Config(), callback=None
):
    costMap = getCostMap(studentPreferences, config)  # search for best rank
    max_rank = max([c for v in studentPreferences.values() for _, c in v])
    max_load = max(getStaffLoading(StaffProjMap).values())
    config.maxRank = max_rank + 1
    config.defaultLoad = max_load + 1
    alloc, (depth, numRuns) = findBestDepthandRuns(
        studentPreferences, StaffProjMap, staffPref, config, callback
    )
    bottleneckRank = maxRank(alloc, costMap)
    bottleneckLoad = maxLoad(alloc, StaffProjMap)

    # run allocation with time limit
    config.defaultLoad = max(bottleneckLoad + 1, 2)
    config.maxRank = max(int(bottleneckRank * 2 / 3), 2)
    config.maxDepth = depth
    config.numRuns = numRuns
    alloc = bestAllocate(studentPreferences, StaffProjMap, staffPref, config=config)

    return config, alloc


def getStaffLoading(projStaff):
    out = defaultdict(int)
    for p, s in projStaff.items():
        out[s] += 1
    return out


def maxRank(SPalloc: Dict[StudentID, ProjectID], costMap: Dict[Move, int]) -> int:
    relevant = [costMap[(k, v)] for k, v in SPalloc.items() if v != 0]
    return max(relevant) if len(relevant) != 0 else 0


def maxLoad(
    SPalloc: Dict[StudentID, ProjectID], ProjStaffMap: Dict[ProjectID, StaffID]
):
    loadings = getLoadMap(ProjStaffMap, SPalloc)
    return max(loadings.values()) if len(loadings) != 0 else 0


def splitProject(
    splitProjects: List[ProjectID],
    studentPreferences: PrefType,
    projStaffMap: Dict[ProjectID, StaffID],
    staffPreferences: Optional[Dict[ProjectID, List[Tuple[StudentID, int]]]] = None,
) -> Tuple[
    PrefType,
    Dict[ProjectID, StaffID],
    Optional[Dict[ProjectID, List[Tuple[StudentID, int]]]],
]:
    outPref = deepcopy(studentPreferences)
    outStaffProjMap = deepcopy(projStaffMap)
    outStaffPref = None
    if staffPreferences:
        outStaffPref = deepcopy(staffPreferences)

    for s in splitProjects:
        projectNewID = ProjectID(max(outStaffProjMap.keys()) + 1)
        print(f"adding {projectNewID}")
        for _, lc_proj in outPref.items():
            for p, c in lc_proj:
                if p == s:
                    lc_proj += [(projectNewID, c)]
        if staffPreferences:
            outStaffPref[projectNewID] = outStaffPref.get(s)
        outStaffProjMap[projectNewID] = outStaffProjMap[s]
    return outPref, outStaffProjMap, outStaffPref


def configHeuristic(
    studentPreferences: PrefType,
    staffProjMap: Dict[ProjectID, StaffID],
    config: Optional[Config] = None,
) -> Config:
    if not config:
        config = Config()
    noStudents = len(studentPreferences)
    depth = min(12, math.exp(int(0.308 * math.log(noStudents) + 0.433)))
    numRuns = 30
    if noStudents > 500:
        numRuns = int(0.05 * (noStudents - 500) + 30)
    config.maxDepth - depth
    config.numRuns = numRuns
    loading = getStaffLoading(staffProjMap)
    config.defaultLoad = stat.median(list(loading.values())) + 1
    maxRank = max([r for _, l in studentPreferences.items() for (_, r) in l])
    config.maxRank = math.ceil(maxRank * 0.4)
    return config


def getStaffLoading(projStaff):
    out = defaultdict(int)
    for p, s in projStaff.items():
        out[s] += 1
    return out