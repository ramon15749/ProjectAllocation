<template>
  <div class="result">
    <JobStatus v-bind:jobid="this.$route.query.job_id" />
  </div>
</template>

<script>
import JobStatus from "../components/jobstatus";
export default {
  name: "Result",
  components: { JobStatus },
};
</script>