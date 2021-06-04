from app.allocation import *
import statistics as stat
from collections import defaultdict
from functools import reduce


def maxRank(SPalloc: Dict[StudentID, ProjectID], costMap: Dict[Move, int]) -> int:
    relevant = [costMap[(k, v)] for k, v in SPalloc.items() if v != 0]
    print([f"{k} {v} {costMap[(k, v)]}" for k, v in SPalloc.items() if v != 0])
    return max(relevant) if len(relevant) != 0 else 0


def medianRank(SPalloc: Dict[StudentID, ProjectID], costMap: Dict[Move, int]) -> float:
    relevant = [costMap[(k, v)] for k, v in SPalloc.items() if v != 0]
    return stat.median(relevant) if len(relevant) != 0 else 0


def avgRank(
    SPalloc: Dict[StudentID, ProjectID],
    costMap: Dict[Move, int],
    skipUnassign: bool = True,
) -> float:
    return sumCost(SPalloc, costMap, skipUnassign) / len(SPalloc)


def varRank(SPalloc: Dict[StudentID, ProjectID], costMap: Dict[Move, int]):
    ranks = [costMap[(k, v)] for k, v in SPalloc.items() if v != 0]

    return stat.pvariance(ranks) if len(ranks) != 0 else 0


def varLoad(
    SPalloc: Dict[StudentID, ProjectID], ProjStaffMap: Dict[ProjectID, StaffID]
) -> float:
    loadings = getLoadMap(ProjStaffMap, SPalloc)
    return stat.pvariance(loadings.values()) if len(loadings) != 0 else 0


def maxLoad(
    SPalloc: Dict[StudentID, ProjectID], ProjStaffMap: Dict[ProjectID, StaffID]
):
    loadings = getLoadMap(ProjStaffMap, SPalloc)
    return max(loadings.values()) if len(loadings) != 0 else 0


def medianLoad(
    SPalloc: Dict[StudentID, ProjectID], ProjStaffMap: Dict[ProjectID, StaffID]
):
    loadings = getLoadMap(ProjStaffMap, SPalloc)
    return stat.median(loadings.values()) if len(loadings) != 0 else 0


def unallocatedProject(SPalloc: Dict[StudentID, ProjectID]) -> int:
    return reduce(lambda acc, x: acc + 1 if x == 0 else acc, SPalloc.values(), 0)


def noUnfair(SPalloc: Dict[StudentID, ProjectID], costMap: Dict[Move, int]):
    unfair = getUnfairDict(SPalloc, costMap)
    return reduce(lambda acc, x: acc + len(x), unfair.values(), 0)


def getStudentRankMap(alloc, studentPreferences):
    studentPrefRankMap = {
        student: {proj: rank for proj, rank in projList}
        for student, projList in studentPreferences.items()
    }
    res = {}
    for student, project in alloc.items():
        if project == 0:
            res[student] = 0
        else:
            res[student] = studentPrefRankMap[student][project]
    return res


def getStat(
    SPalloc: Dict[StudentID, ProjectID],
    costMap: Dict[Move, int],
    ProjStaffMap: Dict[ProjectID, StaffID],
):
    result: Dict[str, float] = {}
    result["MaxRank"] = maxRank(SPalloc, costMap)
    result["MedianRank"] = medianRank(SPalloc, costMap)
    result["AvgRank"] = avgRank(SPalloc, costMap, False)
    result["VarianceRank"] = varRank(SPalloc, costMap)
    result["MaxLoad"] = maxLoad(SPalloc, ProjStaffMap)
    result["MedianLoad"] = medianLoad(SPalloc, ProjStaffMap)
    result["VarLoad"] = varLoad(SPalloc, ProjStaffMap)
    result["NoUnfair"] = noUnfair(SPalloc, costMap)
    result["MagUnfair"] = costUnfair(SPalloc, costMap)
    result["AveUnfair"] = (
        costUnfair(SPalloc, costMap) / len(SPalloc)
        if noUnfair(SPalloc, costMap) != 0
        else 0
    )
    result["NoUnalloc"] = unallocatedProject(SPalloc)
    return result
