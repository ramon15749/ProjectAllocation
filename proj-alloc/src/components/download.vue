<template>
  <button v-on:click="downloadTextFile(JSONObject, name)">{{ name }}</button>
</template>

<script>
export default {
  name: "Download",
  props: ["name", "JSONObject"],
  data() {
    return {};
  },
  methods: {
    downloadTextFile(JSONObj, filename) {
      const text = JSON.stringify(JSONObj, null, 2);
      const a = document.createElement("a");
      const type = filename.split(".").pop();
      a.href = URL.createObjectURL(
        new Blob([text], { type: `text/${type === "txt" ? "plain" : type}` })
      );
      a.download = filename + ".txt";
      a.click();
    },
  },
};
</script>
