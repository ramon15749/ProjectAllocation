<template>
  <div
    style="height: 200px; width: 300px; display: flex; flex-direction: column"
  >
    <p>{{ name }}</p>
    <vue3-chart-js
      :id="doughnutChart.id"
      ref="chartRef"
      :type="doughnutChart.type"
      :data="doughnutChart.data"
    ></vue3-chart-js>
  </div>
</template>

<script>
import Vue3ChartJs from "@j-t-mcc/vue3-chartjs";
import { ref } from "vue";

export default {
  name: "RankHist",
  components: {
    Vue3ChartJs,
  },
  props: ["name", "dict"],
  setup(props) {
    const chartRef = ref(null);
    const doughnutChart = {
      id: "doughnut",
      type: "bar",
      data: {
        labels: Object.keys(props.dict),
        datasets: [
          {
            label: "No. of Students",
            data: Object.keys(props.dict).map(function (key) {
              return props.dict[key];
            }),
          },
        ],
      },
    };

    return {
      doughnutChart,
      chartRef,
    };
  },
  watch: {},
};
</script>