import {createStore} from 'vuex'

// Create store
const store = createStore({
    state() {
        return {
            name: "Vue",
            pref: "",
            proj: ""
        }
    },
    mutations: {
        assignPref (state, pref_in) {
            console.log("assignPref")
            state.pref = pref_in
        },
        assignProj(state, proj_in) {
            console.log("assignProj")
            state.proj = proj_in
        }
    }
})

export default store
    