<template>
  <div class="result">
    <Button type="button" label="New Alloc" @click="toggle" />

    <OverlayPanel ref="op">
      <div v-if="!store.state.refpref">
        <Tag severity="danger" value="Error"></Tag>
        Please upload files before allocation
      </div>
      <div v-else>
        <Config @yeet="test" id="" />
      </div>
    </OverlayPanel>

    <Splitter>
      <SplitterPanel :size="80">
        {{ store.state.currentJobID }}
        <div v-if="store.state.currentJobID">
          <JobStatus v-bind:jobid="store.state.currentJobID" />
        </div>
      </SplitterPanel>
      <SplitterPanel :size="20">
        <JobList :key="childKey" />
      </SplitterPanel>
    </Splitter>
  </div>
</template>

<script>
import JobStatus from "../components/jobstatus";
import JobList from "../components/joblist";
import Config from "../components/config";
import { inject } from "vue";
export default {
  name: "Result",
  components: { JobStatus, JobList, Config },
  setup() {
    const store = inject("store");
    return { store };
  },
  data() {
    return {
      ids: "",
      childKey: true,
    };
  },
  mounted() {
    this.ids = this.$route.query.job_id;
  },
  methods: {
    toggle(event) {
      this.$refs.op.toggle(event);
    },
    test() {
      this.childKey = !this.childKey;
      console.log(localStorage.getItem("AllJobs"));
    },
  },
};
</script>