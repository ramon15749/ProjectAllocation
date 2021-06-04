import { reactive } from 'vue'

const state = reactive({
      refpref: "",
      refproj: "",
      refparsedPref: "",
      refparsedProj: "",
      refLecturerNameMap: "",
      refProjectTitleMap: "",
      refstudentNameMap: "",
      currentJobID: ""

})

const methods = {
    writeNewCurrentJobID(newID){
        state.currentJobID = newID;
    }
}


export default {
    state,
    methods
}