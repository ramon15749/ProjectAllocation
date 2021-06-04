export function getStudentMap(inputJson){
    var result = inputJson.reduce(function(map, object) {
        map[object.EEID] = object;
        return map;
    }, {})
    return result
}

export function getProjectMap(inputJson){
    var result = inputJson.reduce(function(map, object) {
        map[object.PID] = object.TITLE;
        return map;
    }, {})
    return result
}

export function getUnfairDict(SPalloc, costMap){
    var projectStudentPref = Object.entries(costMap).reduce(function (map, [,p]){
        Object.entries(p).forEach(function ([proj,pref]){
            if(!map[proj]) map[proj] = []
            map[proj].push(parseInt(pref))
        })
        return map
    },{})
    var costs = Object.entries(SPalloc).reduce(function (map, [s,p]){
        if (p != 0){
            var current = parseInt(costMap[s][p])
            var filtered = projectStudentPref[p].filter(x => x < current)
            map[p] = filtered.map(x => current-x)
        }
        return map
    }, {})
    costs = Object.entries(costs).reduce(function(r, [e, v]) {
        if (v.length > 0){r[e] = v;} 
        return r;
    }, {})
    return costs
}

export function getUnfairMag(dict){
    const res = Object.entries(dict).reduce(function(sum, [, prefs]){
       prefs.forEach(function(p){sum+=p})
       return sum
    }, 0)
    return res
}
export function allocationForStudent(allocation, studentMap, projectMap){
    var result = Object.entries(allocation).reduce(function(map, [k,v]) {
        map[studentMap[k]['Namei']] = projectMap[v];
        if (projectMap[v] == undefined){
            map[studentMap[k]['Namei']] = "undefined " + k +" : " + v
        }
        return map;
    }, {})
    return result
}

export function parsePreferences(inputJson){
    var result = inputJson.reduce(function(map, object){
        const range = [1,2,3,4,5,6,7,8,9,10]
        var studentPref = range.reduce(function(mapStudent, number){
            if (object["P"+number] != 0){
            mapStudent[object['P'+number]] = object['N'+number]
            }
            return mapStudent
        }, {})
        map[object.EEID] = studentPref
        return map
    }, {})
    return result
}

export function getMaxCost(allocation, pref){
    const result = Object.entries(allocation).reduce(function(prev, [k,v]){
        var cost = parseInt(pref[k][v])
        return cost > prev.cost ? {id: k, cost:cost} : prev
    }, {id: 0, cost: 0})
    return result
}

export function getAverageCost(allocation, pref){
    const result = Object.entries(allocation).reduce(function(sum, [k,v]){
        var cost = parseInt(pref[k][v])
        if (!isNaN(cost)) {
            return sum+cost
        }
        else {return sum}
    }, 0)
    return result/(Object.keys(allocation).length)
}

export function getCostHistogram(allocation, pref){
    const result = Object.entries(allocation).reduce(function(map, [k,v]){
        var cost = parseInt(pref[k][v])
        if (isNaN(cost)) {
            cost = 'Unallocated'
        }
        if (!(cost in map)){
            map[cost] = 0
        }
        map[cost]++
        return map
    }, {'Unallocated':0})
    return result 
}
export function getCostHistogramName(allocation, pref){
    const result = Object.entries(allocation).reduce(function(map, [k,v]){
        var cost = parseInt(pref[k][v])
        if (isNaN(cost)) {
            cost = 'Unallocated'
        }
        if (!(cost in map)){
            map[cost] = []
        }
        map[cost] += `${k}: ${v}\n`
        return map
    }, {'Unallocated':0})
    return result 
}


export function getLecturerProjectMap(inputJson){
    var result = inputJson.reduce(function(map, object) {
        map[object.PID] = object.SUP;
        return map;
    }, new Map())
    return result
}

export function getLecturerNameMap(inputJson){
    var result = inputJson.reduce(function(map, object) {
        map[object.SUP] = object.Email;
        return map;
    }, {})
    return result
}

export function getLoadMap(allocation, ProjectLecturerMap){
    const result = Object.entries(allocation).reduce(function(map, [,v]){
        var lecturer = ProjectLecturerMap[v]
        if (!(lecturer in map)){
            map[lecturer] = 0
        }
        map[lecturer]++
        return map
    }, {})
    return result 
}

export function getLoadHistogram(LoadMap){
    const result=Object.entries(LoadMap).reduce(function(map, [,v]){
        if (!map[v]) map[v] = 0;
        map[v]++
        return map}, {})
    
    return result
}
export function getLoadHistogramName(LoadMap){
    const result=Object.entries(LoadMap).reduce(function(map, [k,v]){
        if (!map[v]) map[v] = '';
        map[v]+= `${k}\n`
        return map}, {})
    
    return result
}
export function getProjectMinPreferences(pref){
    var ProjectList = Object.entries(pref).reduce(function(map, [,list]) {
        Object.entries(list).forEach(function([k,v]){
            if (!(k in map)){
                map[k] = v
            }
            else{
                map[k] = map[k] < v ? map[k] : v 
            }
        })
        return map
    }, {})
    return ProjectList
}

export function getStudentDetailedResult(pref, result, studentMap, projectMap, LecturerMap, LecturerNameMap){
    var out = Object.entries(result).map(function([cid, pid]){
        var row = {
            CID : cid, 
            StudentName : studentMap[cid]['Namei'], 
            PID : pid, 
            title : projectMap[pid], 
            SID : LecturerMap[pid], 
            StaffName: LecturerNameMap[LecturerMap[pid]],
            rank: pref[cid][pid],
            comments : studentMap[cid]['COMMENTS'], 
        }
        return row
    })
    return out
}

// export function getResultForLecturers(pref){

// }

// export function getResultForStudent(){

// }