<template>
  {{ name }}
  <Chart type="bar" :data="basicData" :options="options" />
</template>

<script>
export default {
  name: "RankHist",
  props: ["name", "dict", "label", "names"],
  data(props) {
    return {
      basicData: {
        labels: Object.keys(props.dict),
        datasets: [
          {
            label: "No. of " + props.label,
            backgroundColor: "#42A5F5",
            data: Object.keys(props.dict).map(function (key) {
              return props.dict[key];
            }),
          },
        ],
      },
      options: {
        responsive: true,
        tooltips: {
          callbacks: {
            afterLabel: function (tooltips) {
              if (props.names) {
                return props.names[tooltips["label"]];
              }
            },
          },
        },
      },
    };
  },
};
</script>