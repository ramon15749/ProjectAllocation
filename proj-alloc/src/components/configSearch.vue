<template>
  <div>
    <Button label="ConfigSearch" v-on:click="allocateConfigSearch()"
      >Allocate!</Button
    >
  </div>
</template>


<script>
import axios from "axios";
import md5 from "crypto-js/md5";
import { inject } from "vue";
export default {
  name: "ConfigSearch",
  components: {},
  setup() {
    const store = inject("store");
    return { store };
  },
  data() {
    return {
      pref: "",
      proj: "",
      parsedPref: [],
      parsedProj: [],
      hideUpload: false,
      LecturerNameMap: {},
      projectTitleMap: {},
      studentNameMap: {},
      selectedCity: null,
    };
  },
  computed: {},
  methods: {
    allocateConfigSearch() {
      let formData = new FormData();
      const config = {};
      const json = JSON.stringify(config);
      console.log("JSON:" + json);
      const blob = new Blob([json], {
        type: "application/json",
      });
      formData.append("pref", this.store.state.refpref);
      formData.append("proj", this.store.state.refproj);
      formData.append("config", blob);
      axios
        .post("http://localhost:5050/allocate_file/", formData, {
          header: {
            "Content-Type": "multipart/form-data",
          },
          params: {
            configSearch: true,
          },
        })
        .then((res) => this.redirect(res))
        .catch((err) => console.log(err));
    },
    reformatConfig(input) {
      var test = Object.entries(input.specialLoading).map(([k, v]) => {
        return {
          key: this.parsedPref[k],
          value: v,
        };
      });
      console.log(test);
    },
    redirect(res) {
      var id = res.data.id;
      const hashPref = md5(JSON.stringify(this.store.state.refparsedPref));
      const hashProj = md5(JSON.stringify(this.store.state.refparsedProj));
      localStorage.setItem(
        hashPref,
        JSON.stringify(this.store.state.refparsedPref)
      );
      localStorage.setItem(
        hashProj,
        JSON.stringify(this.store.state.refparsedProj)
      );
      localStorage.setItem("pref_" + id, hashPref);
      localStorage.setItem("proj_" + id, hashProj);
      var prevList = localStorage.getItem("AllJobs");
      console.log("prevList" + prevList);
      var currentList = [];
      if (prevList === null) {
        currentList = [id];
      } else {
        currentList = JSON.parse(prevList);
        console.log("currentList" + currentList);
        currentList.push(id);
      }
      localStorage.setItem("AllJobs", JSON.stringify(currentList));
      this.store.methods.writeNewCurrentJobID(id);
      console.log("emitting yeet");
      this.$emit("yeet");
      console.log("emitting yeet");
    },
  },
};
</script>