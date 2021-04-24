from collections import deque, defaultdict, namedtuple
from dataclasses import dataclass, field
from pprint import pprint
from typing import Dict, NewType, Tuple, List, Deque, Set, NamedTuple
import csv
import logging
import random
import sys

from dataclasses_json import dataclass_json
import numpy as np

StudentID = NewType("StudentID", int)
ProfID = NewType("ProfID", int)
ProjectID = NewType("ProjectID", int)
Move = Tuple[StudentID, ProjectID]


@dataclass_json
@dataclass
class Config:
    maxDepth: int = 20
    defaultLoad: int = 5
    specialLoading: Dict[ProfID, int] = field(default_factory=dict)
    forcedMatching: Dict[StudentID, ProjectID] = field(default_factory=dict)
    disallowedMatching: Dict[StudentID, ProjectID] = field(default_factory=dict)
    numRuns: int = 50


def local_run(studentPref, ProjectInfo, maxDepth=7):
    with open(studentPref, mode="r", encoding="utf-8-sig") as infile:
        inputDict = csv.DictReader(infile)
        studentPreferences = createStudentPrefMap(inputDict)
    with open(ProjectInfo, mode="r", encoding="utf-8-sig") as infile:
        inputDict = csv.DictReader(infile)
        ProfProjMap = createProjProfMap(inputDict)
    config = Config()
    costMap = getCostMap(studentPreferences)
    studentProjectList = {
        student: [proj for proj, _ in projList]
        for student, projList in studentPreferences.items()
    }
    alloc = allocate(studentProjectList, ProfProjMap, config, costMap)
    return alloc


def createProjProfMap(inputDict: List[Dict[str, str]]) -> Dict[ProjectID, ProfID]:
    ret: Dict[ProjectID, ProfID] = {}
    for row in inputDict:
        ret[ProjectID(int(row["PID"]))] = ProfID(int(row["SUP"]))
    return ret


def patchMap(
    studentPreferences: Dict[StudentID, List[ProjectID]],
    ProjProfMap: Dict[ProjectID, ProfID],
):
    allProjects = set(sum(studentPreferences.values(), []))
    existingProject = set(ProjProfMap.keys())
    for proj in allProjects.difference(existingProject):
        ProjProfMap[proj] = ProfID(0)

    return ProjProfMap


def allocate(
    studentPreferences: Dict[StudentID, List[ProjectID]],
    ProjProfMap: Dict[ProjectID, ProfID],
    config: Config,
    costMap: Dict[Move, int],
) -> Dict[StudentID, ProjectID]:

    ProjProfMap = patchMap(studentPreferences, ProjProfMap)
    SPalloc = preAssign(studentPreferences, ProjProfMap, config.defaultLoad)
    loadMap = getLoadMap(ProjProfMap, SPalloc)
    first = SPalloc.copy()
    PSalloc = {v: k for k, v in SPalloc.items()}
    cycleList = findAllShiftAndRotate(
        SPalloc,
        PSalloc,
        studentPreferences,
        ProjProfMap,
        loadMap,
        costMap,
        config.maxDepth,
        config.defaultLoad,
    )
    i = 0
    while len(cycleList) > 0:
        loadMap = ShiftLoadMap(SPalloc, loadMap, cycleList[0][0], ProjProfMap)
        SPalloc, PSalloc = applyShiftOrRotate(SPalloc, PSalloc, cycleList[0][0])
        cycleList = findAllShiftAndRotate(
            SPalloc,
            PSalloc,
            studentPreferences,
            ProjProfMap,
            loadMap,
            costMap,
            config.maxDepth,
            config.defaultLoad,
        )
        i += 1
    assert len(studentPreferences) == len(SPalloc)
    return SPalloc


def preAssign(
    studentPreferences: Dict[StudentID, List[ProjectID]],
    LecturerProjectMap: Dict[ProjectID, ProfID],
    maxLoad: int,
) -> Dict[StudentID, ProjectID]:
    students = list(studentPreferences.keys())
    random.shuffle(students)
    allocationMap: Dict[StudentID, ProjectID] = {}
    loadingMap: Dict[ProfID, int] = defaultdict(int)

    for s in students:
        allocationMap[s] = ProjectID(0)  # unallocated
        for choice in studentPreferences[s]:
            if (
                LecturerProjectMap[choice] != 0
                and loadingMap[LecturerProjectMap[choice]] >= maxLoad
            ):
                continue
            if choice not in allocationMap.values():
                allocationMap[s] = choice
                loadingMap[LecturerProjectMap[choice]] += 1
                break
    return allocationMap


# now costmap only track the preference order
def getCostMap(
    studentPreferencesCost: Dict[StudentID, List[Tuple[ProjectID, int]]]
) -> Dict[Tuple[StudentID, ProjectID], int]:
    costMap: Dict[Tuple[StudentID, ProjectID], int] = {}
    for s, projects in studentPreferencesCost.items():
        for project, cost in projects:
            if project != 0:
                costMap[(s, project)] = cost
        costMap[(s, ProjectID(0))] = 100
    return costMap


def findAllShiftAndRotate(
    SPalloc: Dict[StudentID, ProjectID],
    PSalloc: Dict[ProjectID, StudentID],
    studentPreferences: Dict[StudentID, List[ProjectID]],
    LecturerProjectMap: Dict[ProjectID, ProfID],
    loadMap: Dict[ProfID, int],
    costMap: Dict[Move, int],
    maxDepth: int,
    maxLoad: int,
) -> List[Tuple[List[Move], bool]]:
    possibleMoves = []
    for s in SPalloc.keys():
        possibleMoves.extend(
            BFS(
                s,
                SPalloc,
                PSalloc,
                studentPreferences,
                LecturerProjectMap,
                costMap,
                loadMap,
                maxDepth,
                maxLoad,
            )
        )
        if len(possibleMoves) > 0:
            return possibleMoves
    return possibleMoves


def BFS(
    s: StudentID,
    SPallocation: Dict[StudentID, ProjectID],
    PSallocation: Dict[ProjectID, StudentID],
    studentPreferences: Dict[StudentID, List[ProjectID]],
    LecturerProjectMap: Dict[ProjectID, ProfID],
    costMap: Dict[Move, int],
    loadMap: Dict[ProfID, int],
    maxDepth: int,
    maxLoad: int,
) -> List[Tuple[List[Move], bool]]:
    cycle_or_shift: List[Tuple[List[Move], bool]] = []
    q: Deque[Tuple[StudentID, int, int, List[Move]]] = deque()
    q.append((s, 0, 0, []))
    while q:
        x, depth, partialSum, path = q.popleft()
        if x == s and depth != 0:
            if partialSum < 0:
                cycle_or_shift.append((path, False))
                return cycle_or_shift
        if x not in [x for x, _ in path]:
            depth += 1
            if depth > maxDepth:
                continue
            moves = studentPreferences[x].copy()
            random.shuffle(moves)
            for project in moves:
                if project == SPallocation[x]:
                    continue
                movePath = path + [(x, project)]
                movePartialSum = (
                    partialSum + costMap[(x, project)] - costMap[(x, SPallocation[x])]
                )
                if isValid(x, project, SPallocation, movePartialSum):
                    if project not in PSallocation:
                        localLoadMap = ShiftLoadMap(
                            SPallocation, loadMap, movePath, LecturerProjectMap
                        )
                        if max(localLoadMap.values()) <= maxLoad:
                            cycle_or_shift.append((movePath, True))
                            return cycle_or_shift
                        continue
                    q.append((PSallocation[project], depth, movePartialSum, movePath))
    return cycle_or_shift


def BFS_steepest(
    s: StudentID,
    SPallocation: Dict[StudentID, ProjectID],
    PSallocation: Dict[ProjectID, StudentID],
    studentPreferences: Dict[StudentID, List[ProjectID]],
    costMap: Dict[Move, int],
    maxDepth: int,
) -> List[Tuple[List[Move], bool]]:
    cycle_or_shift: List[Tuple[List[Move], int, bool]] = []
    q: Deque[Tuple[StudentID, int, int, List[Move]]] = deque()
    q.append((s, 0, 0, []))
    while q:
        x, depth, partialSum, path = q.popleft()
        if x == s and depth != 0:
            cycle_or_shift.append((path, partialSum, False))
            continue
        if x not in [x for x, _ in path]:
            depth += 1
            if depth > maxDepth:
                continue
            moves = studentPreferences[x].copy()
            random.shuffle(moves)
            for project in moves:
                if project == SPallocation[x]:
                    continue
                movePath = path + [(x, project)]
                movePartialSum = (
                    partialSum + costMap[(x, project)] - costMap[(x, SPallocation[x])]
                )
                assert costMap[(x, project)] != costMap[(x, SPallocation[x])]
                if isValid(x, project, SPallocation, movePartialSum):
                    if project not in PSallocation:
                        cycle_or_shift.append((movePath, movePartialSum, True))
                        continue
                    q.append((PSallocation[project], depth, movePartialSum, movePath))
    if len(cycle_or_shift) == 0:
        return []
    index_min = np.argmin([partialSum for moves, partialSum, isShift in cycle_or_shift])
    m: List[Move]
    shift: bool
    m, p, shift = cycle_or_shift[index_min]
    return [(m, shift)]


def isValid(
    s: StudentID, move: ProjectID, SPalloc: Dict[StudentID, ProjectID], partialSum: int
) -> bool:
    if SPalloc[s] == move:
        return False
    if partialSum >= 0:
        return False
    return True


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


def sumCost(SPalloc: Dict[StudentID, ProjectID], costMap: Dict[Move, int]) -> int:
    sum = 0
    for k, v in SPalloc.items():
        sum += costMap[(k, v)]
    return sum


def maxRank(SPalloc: Dict[StudentID, ProjectID], costMap: Dict[Move, int]) -> int:
    max = 0
    for k, v in SPalloc.items():
        if costMap[(k, v)] > max:
            max = costMap[(k, v)]
    return max


def getLoadMap(
    LecturerProjectMap: Dict[ProjectID, ProfID], SPalloc: Dict[StudentID, ProjectID]
) -> Dict[ProfID, int]:
    ret: Dict[ProfID, int] = defaultdict(int)
    for proj in SPalloc.values():
        if proj == 0:
            continue
        if LecturerProjectMap[proj] != 0:
            ret[LecturerProjectMap[proj]] += 1
    return ret


def ShiftLoadMap(
    SPalloc: Dict[StudentID, ProjectID],
    loadMap: Dict[ProfID, int],
    moves: List[Move],
    LecturerProjectMap: Dict[ProjectID, ProfID],
) -> Dict[ProfID, int]:
    copiedLoadMap = loadMap.copy()
    projRemove = SPalloc[moves[0][0]]
    projAdd = moves[-1][1]
    if projAdd != 0:
        staffAdd = LecturerProjectMap[projAdd]
        if staffAdd != 0:
            copiedLoadMap[staffAdd] += 1
    if projRemove != 0:
        staffRemove = LecturerProjectMap[projRemove]
        if staffRemove != 0:
            copiedLoadMap[staffRemove] -= 1
    assert min(copiedLoadMap.values()) >= 0, "min is {}".format(
        min(copiedLoadMap.values())
    )
    return copiedLoadMap


if __name__ == "__main__":
    local_run(sys.argv[1], sys.argv[2])