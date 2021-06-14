<template>
  <div>
    Jobs:

    <div v-for="(c, id) in this.id_config" :key="id">
      <a @click="ToNewJob(id)"> {{ id }} </a>
      <p style="font-size: 10px; color: grey">{{ c }}</p>
    </div>
  </div>
</template>

<script>
import { inject } from "vue";
import axios from "axios";
export default {
  name: "JobList",
  data() {
    return {
      ids: "",
      id_config: {},
    };
  },
  setup() {
    const store = inject("store");
    return { store };
  },
  mounted() {
    this.ids = JSON.parse(localStorage.getItem("AllJobs"));
    if (!this.ids) return;
    const self = this;
    this.id_config = this.ids.reduce(function (map, id) {
      console.log(id);
      map[id] = self.getConfig(id);
      console.log(map);
      return map;
    }, {});
  },
  methods: {
    ToNewJob(id) {
      this.store.methods.writeNewCurrentJobID(id);
      console.log(this.store.state.currentJobID);
    },
    getConfig(id) {
      var config = JSON.parse(localStorage.getItem("config_" + id));
      if (!config) {
        axios
          .get("http://localhost:5050/get_config/", {
            params: {
              job_id: id,
            },
          })
          .then(
            (res) => (
              (config = {}),
              (config = res.data),
              localStorage.setItem("config_" + id, JSON.stringify(res.data))
            )
          )
          .catch((err) => console.log("cannot get config:  " + err));
      }
      return config;
    },
  },
  watch: {
    localStorage: function () {
      this.ids = JSON.parse(localStorage.getItem("AllJobs"));
    },
  },
};
</script>