<template>
  <div class="home">
    <h1>Upload Files</h1>
    <Uploadfile
      filename="Student Preferences"
      v-model="refpref"
      style="padding=5px"
    />

    <Uploadfile filename="Project-Staff Map" v-model="refproj" />
    <Uploadfile filename="Staff Preferences" v-model="refproj" />
    <br />
    <br />
    <Button v-on:click="parseFile2()">Parse File!</Button>
    <br />
    <br />
    <ConfigSearch />
  </div>
</template>

<script>
import axios from "axios";
import Uploadfile from "../components/uploadfile.vue";
import md5 from "crypto-js/md5";
import Papa from "papaparse";
import {
  getLecturerNameMap,
  getStudentMap,
  getProjectMap,
} from "../components/common";
import ConfigSearch from "../components/configSearch.vue";
import { ref, inject } from "vue";
export default {
  name: "Home",
  components: { Uploadfile, ConfigSearch },
  data() {
    return {
      pref: "",
      proj: "",
      parsedPref: [],
      parsedProj: [],
      hideUpload: false,
    };
  },
  setup() {
    const store = inject("store");
    let refpref = ref();
    let refproj = ref();

    const parseFile2 = function () {
      store.state.refpref = refpref.value;
      store.state.refproj = refproj.value;
      Papa.parse(refpref.value, {
        header: true,
        complete: function (results) {
          store.state.refparsedPref = results.data;
          var studentDict = getStudentMap(store.state.refparsedPref);
          store.state.refstudentNameMap = Object.entries(studentDict).map(
            function (
              key,
              // eslint-disable-next-line no-unused-vars
              $
            ) {
              return { id: parseInt(key[0]), name: key[0] + " " + key[1] };
            }
          );
        },
      });
      Papa.parse(refproj.value, {
        header: true,
        complete: function (results) {
          store.state.refparsedProj = results.data;

          var nameDict = getLecturerNameMap(store.state.refparsedProj);
          store.state.refLecturerNameMap = Object.entries(nameDict).map(
            function (
              key,
              // eslint-disable-next-line no-unused-vars
              $
            ) {
              return { id: key[0], name: key[0] + " " + key[1] };
            }
          );
          var projDict = getProjectMap(store.state.refparsedProj);
          store.state.refProjectTitleMap = Object.entries(projDict).map(
            function (
              key,
              // eslint-disable-next-line no-unused-vars
              $
            ) {
              return { id: key[0], name: key[0] + " " + key[1] };
            }
          );
        },
      });
    };

    return {
      store,
      refpref,
      refproj,
      parseFile2,
    };
  },
  methods: {
    handleFile(file, type) {
      switch (type) {
        case "student-pref":
          this.pref = file;
          break;
        case "project-info":
          this.proj = file;
          break;
        default:
          console.log("unsupported type ", type);
      }
    },
    parseFile() {
      var self = this;
      Papa.parse(this.pref, {
        header: true,
        complete: function (results) {
          self.parsedPref = results.data;
          var studentDict = getStudentMap(self.parsedPref);
          var studentNameMap = Object.entries(studentDict).map(function (
            key,
            // eslint-disable-next-line no-unused-vars
            $
          ) {
            return { id: parseInt(key[0]), name: key[0] + " " + key[1] };
          });
          console.log(studentNameMap);
          // self.$store.commit("studentNameMap", studentNameMap);
          // self.$store.commit("assignPref", self.parsedPref);
        },
      });
      Papa.parse(this.proj, {
        header: true,
        complete: function (results) {
          self.parsedProj = results.data;

          var nameDict = getLecturerNameMap(self.parsedProj);
          var LecturerNameMap = Object.entries(nameDict).map(function (
            key,
            // eslint-disable-next-line no-unused-vars
            $
          ) {
            return { id: key[0], name: key[0] + " " + key[1] };
          });
          var projDict = getProjectMap(self.parsedProj);
          var projectTitleMap = Object.entries(projDict).map(function (
            key,
            // eslint-disable-next-line no-unused-vars
            $
          ) {
            return { id: key[0], name: key[0] + " " + key[1] };
          });
          //self.$store.commit("LecturerNameMap", LecturerNameMap);
          //self.$store.commit("projectTitleMap", projectTitleMap);
          console.log(LecturerNameMap, projectTitleMap);
        },
      });
    },
    arrayToMap(input) {
      return input.reduce((obj, item) => {
        if (!item.key) {
          return obj;
        } else {
          return {
            ...obj,
            [parseInt(item.key)]: item.value,
          };
        }
      }, {});
    },
    submitFiles() {
      let formData = new FormData();
      const config = {
        maxDepth: this.maxDepth,
        defaultLoad: this.defaultLoad,
        numRuns: this.numRuns,
        weightUnfair: this.weightUnfair,
        weightVariance: this.weightVariance,
        specialLoading: this.arrayToMap(this.specialLoading),
        forcedMatching: this.arrayToMap(this.forcedMatching),
        disallowedMatching: this.arrayToMap(this.disallowedMatching),
      };
      const json = JSON.stringify(config);
      console.log("JSON:" + json);
      const blob = new Blob([json], {
        type: "application/json",
      });
      formData.append("pref", this.pref);
      formData.append("proj", this.proj);
      formData.append("config", blob);
      axios
        .post("http://localhost:5050/allocate/", formData, {
          header: {
            "Content-Type": "multipart/form-data",
          },
        })
        .then((res) => this.redirect(res))
        .catch((err) => console.log(err));
    },
    redirect(res) {
      var id = res.data.id;
      const hashPref = md5(JSON.stringify(this.parsedPref));
      const hashProj = md5(JSON.stringify(this.parsedProj));
      localStorage.setItem(hashPref, JSON.stringify(this.parsedPref));
      localStorage.setItem(hashProj, JSON.stringify(this.parsedProj));
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
      window.location = "/#/allocation_result?job_id=" + id;
    },

    //downloadRes() {
    //  const data = JSON.stringify(this.result);
    //  const blob = new Blob([data], { type: "text/plain" });
    //  const e = document.createEvent("MouseEvent");
    //  var a = document.createElement("a");
    //  a.download = "test.json";
    //  a.href = window.URL.createObjectURL(blob);
    //  a.dataset.downloadurl = ["text/json", a.download, a.href].join(":");
    //  e.initEvent(
    //    "click",
    //    true,
    //    false,
    //    0,
    //    0,
    //    0,
    //    0,
    //    0,
    //    false,
    //    false,
    //    false,
    //    false,
    //    0,
    //    null
    //  );
    //  a.dispatchEvent(e);
    //},
  },
};
</script>

<style scoped>
.p-dropdown {
  width: 14rem;
}
</style>