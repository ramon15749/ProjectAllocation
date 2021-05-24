<template>
  <div>
    <p>Job {{ this.id }}</p>
    <div>The job's status is {{ this.status }}</div>
    <div>The config is</div>
    <table style="margin: auto">
      <tr v-for="(c, v) in this.config" :key="c.v">
        <td>{{ v }}</td>
        <td>
          {{ c }}
        </td>
      </tr>
    </table>
    <div v-show="this.status == 'finished'">
      <Download
        name="Student Allocation"
        v-bind:JSONObject="this.studentresult"
      />
      <div class="p-grid">
        <div class="p-col-12 p-sm-12 p-lg-6">
          <RankHist
            name="Rank Histogram"
            v-bind:dict="this.histogram"
            v-bind:names="this.histogramName"
            label="Students"
            :key="childKey"
          />
        </div>

        <div class="p-col-12 p-sm-12 p-lg-6">
          <RankHist
            name="Load Histogram"
            v-bind:dict="this.loadHistogram"
            v-bind:names="this.loadHistogramName"
            label="Lecturers"
            :key="childKey"
          />
        </div>
      </div>
      <div class="p-d-flex">
        <div class="p-mr-4">
          <h5>
            No. of Student Unallocate: <br />
            {{ this.histogram["Unallocated"] }}
          </h5>
        </div>
        <div class="p-mr-4">
          <h5>Average Rank: <br />{{ this.avgCost }}</h5>
        </div>
        <div class="p-mr-4">
          <h5>Unfair Magnitude: <br />{{ this.unfairMag }}</h5>
        </div>
        <div class="p-mr-4">
          <h5>Unfair Dict: <br />{{ this.unfairDict }}</h5>
        </div>
      </div>
      <DataTable :value="detailedRes" responsiveLayout="scroll">
        <Column field="CID" header="CID" :sortable="true"></Column>
        <Column field="StudentName" header="Student Name" :sortable="true">
          <template #filter="{ filterModel, filterCallback }">
            <InputText
              type="text"
              v-model="filterModel.value"
              @input="filterCallback()"
              class="p-column-filter"
            /> </template
        ></Column>
        <Column field="PID" header="PID" :sortable="true"></Column>
        <Column field="title" header="Title" :sortable="true"></Column>
        <Column field="SID" header="SID" :sortable="true"></Column>
        <Column field="StaffName" header="Staff Name" :sortable="true"></Column>
        <Column field="rank" header="Rank" :sortable="true"></Column>
        <Column field="comments" header="Comments" :sortable="true"></Column>
      </DataTable>
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
  getCostHistogram,
  getCostHistogramName,
  getLecturerProjectMap,
  getLecturerNameMap,
  getLoadMap,
  getAverageCost,
  getLoadHistogram,
  getLoadHistogramName,
  getUnfairDict,
  getUnfairMag,
  getStudentDetailedResult,
} from "./common";
import Download from "../components/download";
import RankHist from "../components/rankHist";
import { FilterMatchMode } from "primevue/api";
export default {
  name: "JobStatus",
  components: { Download, RankHist },
  props: ["jobid"],
  mounted() {
    if (this.jobid) {
      this.id = this.jobid;
    } else {
      const alljobs = JSON.parse(localStorage.getItem("AllJobs"));
      this.id = alljobs[alljobs.length - 1];
    }
    this.getInfoNetwork();
    this.getInfoLocal(this.id);
    this.filters2 = {
      StudentName: { value: null, matchMode: FilterMatchMode.CONTAINS },
    };
  },
  watch: {
    jobid: function () {
      this.clearResult();
      if (this.jobid) {
        this.id = this.jobid;
      } else {
        const alljobs = JSON.parse(localStorage.getItem("AllJobs"));
        this.id = alljobs[alljobs.length - 1];
      }
      this.getInfoLocal(this.id);
      this.getInfoNetwork();
    },
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
      loadMap: "",
      config: "",
      histogram: { hello: 43 },
      avgCost: "",
      loadHistogram: {},
      loadHistogramName: {},
      unfairDict: {},
      unfairMag: 0,
      childKey: false,
      detailedRes: false,
    };
  },
  methods: {
    clearResult() {
      this.status = "";
      this.result = "";
      this.studentresult = "";
      this.preferences = "";
      this.loadMap = "";
      this.config = "";
      this.histogram = {};
      this.avgCost = "";
    },
    getInfoNetwork() {
      console.log("status", status);
      if (this.status == "finished" || this.status == "FAILURE") {
        return;
      }
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
      this.config = JSON.parse(localStorage.getItem("config_" + this.id));
      if (!this.config) {
        console.log("getting config");
        axios
          .get("http://localhost:5050/get_config/", {
            params: {
              job_id: this.id,
            },
          })
          .then(
            (res) => (
              (this.config = {}),
              (this.config = res.data),
              localStorage.setItem(
                "config_" + this.id,
                JSON.stringify(res.data)
              )
            )
          )
          .catch(
            (err) => (
              console.log("cannot get config:  " + err),
              clearInterval(this.timer)
            )
          );
      }
    },
    getInfoLocal(id) {
      const hashPref = localStorage.getItem("pref_" + id);
      const hashProj = localStorage.getItem("proj_" + id);
      var pref = JSON.parse(localStorage.getItem(hashPref));
      var proj = JSON.parse(localStorage.getItem(hashProj));
      this.studentMap = getStudentMap(pref);
      this.projectMap = getProjectMap(proj);
      this.preferences = parsePreferences(pref);
      this.ProjectLecturer = getLecturerProjectMap(proj);
      this.LecturerName = getLecturerNameMap(proj);
    },
    getResult(res) {
      console.log("called!", res.data);
      if (res.status != 200) return;
      this.status = res.data;
      console.log("status != 200", res.data);
      if (res.data == "finished" || res.data == "FAILURE") {
        console.log("clear");
        clearInterval(this.timer);
        this.timer = "";
        axios
          .get("http://localhost:5050/get_result/", {
            params: {
              job_id: this.id,
            },
          })
          .then((res) => this.getSupportingData(res));
        //.catch(
        //  (err) => (console.log("oh no " + err), clearInterval(this.timer))
        //);
      } else {
        console.log("set");
        if (!this.timer) {
          this.timer = setInterval(this.getInfoNetwork, 5000);
        }
      }
    },
    getSupportingData(res) {
      this.result = res.data;
      this.loadMap = getLoadMap(this.result, this.ProjectLecturer);
      this.histogram = getCostHistogram(this.result, this.preferences);
      this.histogramName = getCostHistogramName(this.result, this.preferences);
      this.studentresult = allocationForStudent(
        this.result,
        this.studentMap,
        this.projectMap
      );
      this.avgCost = getAverageCost(this.result, this.preferences);
      this.loadHistogram = getLoadHistogram(this.loadMap);
      this.loadHistogramName = getLoadHistogramName(this.loadMap);
      this.unfairDict = getUnfairDict(this.result, this.preferences);
      this.unfairMag = getUnfairMag(this.unfairDict);
      this.detailedRes = getStudentDetailedResult(
        this.preferences,
        this.result,
        this.studentMap,
        this.projectMap,
        this.ProjectLecturer,
        this.LecturerName
      );
      console.log(this.detailedRes);
      this.childKey = !this.childKey;
    },
  },
};
</script>