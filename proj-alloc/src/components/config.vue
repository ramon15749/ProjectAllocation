<template>
  <div>
    <Uploadjson filename="config" v-model="config" />
    <ConfigShort
      configName="Default Staff Load"
      v-model.number="config.defaultLoad"
    />
    <ConfigShort configName="max Depth" v-model.number="config.maxDepth" />
    <ConfigShort configName="number of Run" v-model.number="config.numRuns" />
    <ConfigShort configName="Max Rank" v-model.number="config.maxRank" />
    <Fieldset legend="Advance" :toggleable="true" :collapsed="true">
      <ConfigShort
        configName="Weight Of Unfair Loading"
        v-model.number="config.weightUnfair"
      />
      <ConfigShort
        configName="Weight of Variance of Loading"
        v-model.number="config.weightVariance"
      />
      <ConfigLong
        v-bind:configList="store.state.refLecturerNameMap"
        v-model="config.specialLoading"
        initValue="config.specialLoading"
      />
      <ConfigLongDropdowns
        configName="Forced Matching"
        v-bind:configList1="store.state.refstudentNameMap"
        v-bind:configList2="store.state.refProjectTitleMap"
        v-model="config.forcedMatching"
      />
      <ConfigLongDropdowns
        configName="Disallowed Matching"
        v-bind:configList1="store.state.refstudentNameMap"
        v-bind:configList2="store.state.refProjectTitleMap"
        v-model="config.disallowedMatching"
      />
    </Fieldset>

    <Button label="Submit" v-on:click="submitFiles()">Allocate!</Button>
  </div>
</template>


<script>
import axios from "axios";
import ConfigShort from "../components/configShort";
import ConfigLong from "../components/configLong";
import ConfigLongDropdowns from "../components/configLongDropdowns";
import Uploadjson from "../components/uploadjson.vue";
import md5 from "crypto-js/md5";
import { inject } from "vue";
export default {
  name: "Config",
  components: { ConfigShort, ConfigLong, ConfigLongDropdowns, Uploadjson },
  setup() {
    const store = inject("store");
    return { store };
  },
  mounted() {
    // var cachedConfig = localStorage.getItem(
    //   "config_" + this.store.state.currentJobID
    // );
    this.config = {
      defaultLoad: "",
      maxDepth: "",
      numRuns: "",
      weightUnfair: 0,
      weightVariance: 0,
      maxRank: 10,
      specialLoading: [
        {
          key: "",
          value: "",
        },
      ],
      disallowedMatching: [
        {
          key: "",
          value: "",
        },
      ],
      forcedMatching: {},
    };
    // if (cachedConfig !== null) {
    //   this.config = this.reformatConfig(JSON.parse(cachedConfig));
    //   console.log("hithere ", this.config);
    // }
  },
  data() {
    return {
      pref: "",
      proj: "",
      config: {
        defaultLoad: "",
        maxDepth: "",
        numRuns: "",
        weightUnfair: 0,
        weightVariance: 0,
        maxRank: 10,
        specialLoading: [
          {
            key: "4342",
            value: "423",
          },
        ],
        disallowedMatching: [
          {
            key: "",
            value: "",
          },
        ],
        forcedMatching: [
          {
            key: "432423",
            value: "fds",
          },
        ],
      },
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
        maxDepth: this.config.maxDepth,
        defaultLoad: this.config.defaultLoad,
        numRuns: this.config.numRuns,
        maxRank: this.config.maxRank,
        weightUnfair: this.config.weightUnfair,
        weightVariance: this.config.weightVariance,
        forcedMatching: this.config.forcedMatching,
      };
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