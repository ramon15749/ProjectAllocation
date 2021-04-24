<template>
  <div class="home">
    <p>hello</p>
    <Uploadfile filename="student-pref" v-on:fileUploaded="handleFile" />
    <Uploadfile filename="project-info" v-on:fileUploaded="handleFile" />
    <ConfigShort configName="Default Staff Load" v-model.number="defaultLoad" />
    <ConfigShort configName="max Depth" v-model.number="maxDepth" />
    <ConfigShort configName="number of Run" v-model.number="numRuns" />
  </div>
  <button v-on:click="submitFiles()">Allocate!</button>
</template>

<script>
// @ is an alias to /src
import axios from "axios";
import Uploadfile from "../components/uploadfile.vue";
import ConfigShort from "../components/configShort";
import Papa from "papaparse";
export default {
  name: "Home",
  components: { Uploadfile, ConfigShort },
  data() {
    return {
      pref: "",
      proj: "",
      defaultLoad: "",
      maxDepth: "",
      numRuns: "",
      parsedPref: [],
      parsedProj: [],
    };
  },
  methods: {
    handleFile(file, type) {
      switch (type) {
        case "student-pref":
          console.log("pref home");
          this.pref = file;
          console.log(type, this.pref);
          break;
        case "project-info":
          this.proj = file;
          console.log(type, this.proj);
          break;
        default:
          console.log("unsupported type ", type);
      }
    },
    submitFiles() {
      let formData = new FormData();
      const config = {
        maxDepth: this.maxDepth,
        defaultLoad: this.defaultLoad,
        numRuns: this.numRuns,
      };
      var self = this;
      Papa.parse(this.pref, {
        header: true,
        complete: function (results) {
          self.parsedPref = results.data;
          self.$store.commit("assignPref", self.parsedPref);
        },
      });
      Papa.parse(this.proj, {
        header: true,
        complete: function (results) {
          console.log("Proj Finished:", results.data);
          self.parsedProj = results.data;
          self.$store.commit("assignProj", self.parsedProj);
        },
      });
      const json = JSON.stringify(config);
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
      console.log(id);
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
