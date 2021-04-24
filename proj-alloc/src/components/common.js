export function getStudentMap(inputJson){
    var result = inputJson.reduce(function(map, object) {
        map[object.EEID] = object.Namei;
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

export function allocationForStudent(allocation, studentMap, projectMap){
    var result = Object.entries(allocation).reduce(function(map, [k,v]) {
        map[studentMap[k]] = projectMap[v];
        if (projectMap[v] == undefined){
            map[studentMap[k]] = "undefined " + k +" : " + v
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
    console.log("allocation ",allocation)
    const result = Object.entries(allocation).reduce(function(sum, [k,v]){
        var cost = parseInt(pref[k][v])
        return sum+cost
    }, 0)
    return result/(Object.keys(allocation).length)
}

export function getCostHistogram(allocation, pref){
    const result = Object.entries(allocation).reduce(function(map, [k,v]){
        var cost = parseInt(pref[k][v])
        if (!(cost in map)){
            map[cost] = 0
        }
        map[cost]++
        return map
    }, {})
    return result 
}

export function getLecturerProjectMap(inputJson){
    var result = inputJson.reduce(function(map, object) {
        map[object.PID] = object.SUP;
        return map;
    }, {})
    return result
}

export function getLecturerNameMap(inputJson){
    var result = inputJson.reduce(function(map, object) {
        map[object.SUP] = object.Namei;
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

// export function getResultForLecturers(pref){

// }

// export function getResultForStudent(){

// }