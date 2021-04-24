<template>
  <div>
    <p>Job {{ jobid }}</p>
    <div>The job's status is {{ this.status }}</div>
    <div>The job's progress is {{ this.progress }}</div>
    <div v-if="this.result != ''">
      <table>
        <tr v-for="(value, name) in this.studentresult" :key="value">
          <th>{{ name }}</th>
          <th>{{ value }}</th>
        </tr>
      </table>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import {
  parsePreferences,
  getProjectMap,
  getStudentMap,
  allocationForStudent,
  getMaxCost,
  getAverageCost,
  getCostHistogram,
  getLecturerProjectMap,
  getLecturerNameMap,
  getLoadMap,
  getProjectMinPreferences,
} from "./common";
export default {
  name: "JobStatus",
  props: ["jobid"],
  mounted() {
    console.log("mounted");
    this.id = this.jobid;
    this.getInfo();
    console.log("state 2: ", this.$store.state.pref);
    this.studentMap = getStudentMap(this.$store.state.pref);
    this.projectMap = getProjectMap(this.$store.state.proj);
    this.preferences = parsePreferences(this.$store.state.pref);
    this.ProjectLecturer = getLecturerProjectMap(this.$store.state.proj);
    this.LecturerName = getLecturerNameMap(this.$store.state.proj);
    console.log("minPref: ", getProjectMinPreferences(this.preferences));
    console.log("prasedPreferences: ", this.preferences);
    this.timer = setInterval(this.getInfo, 5000);
  },
  data() {
    return {
      timer: "",
      id: "",
      status: "",
      result: "",
      studentMap: "",
      projectMap: "",
      studentresult: "",
      preferences: "",
      progress: "",
      ProjectLecturer: "",
      LecturerName: "",
    };
  },
  methods: {
    getInfo() {
      //params = URLSearchParams([["job_id", this.id]]);
      axios
        .get("http://localhost:5050/get_status/", {
          params: {
            job_id: this.id,
          },
        })
        .then((res) => this.getResult(res))
        .catch(
          (err) => (console.log("oh no " + err), clearInterval(this.timer))
        );
      axios
        .get("http://localhost:5050/get_progress/", {
          params: {
            job_id: this.id,
          },
        })
        .then((res) => (this.progress = res.data))
        .catch(
          (err) => (console.log("oh no " + err), clearInterval(this.timer))
        );
    },
    getResult(res) {
      this.status = res.data;
      if (res.data == "finished" || res.data == "FAILURE") {
        clearInterval(this.timer);
        axios
          .get("http://localhost:5050/get_result/", {
            params: {
              job_id: this.id,
            },
          })
          .then(
            (res) => (
              (this.result = res.data),
              console.log(this.result),
              console.log(
                "getMaxCost: ",
                getMaxCost(this.result, this.preferences),
                "getAverageCost:",
                getAverageCost(this.result, this.preferences),
                "getCostHistogram:",
                getCostHistogram(this.result, this.preferences),
                "getLoadMap:",
                getLoadMap(this.result, this.ProjectLecturer)
              ),
              (this.studentresult = allocationForStudent(
                this.result,
                this.studentMap,
                this.projectMap
              ))
            )
          )
          .catch(
            (err) => (console.log("oh no " + err), clearInterval(this.timer))
          );
      }
    },
  },
};
</script>