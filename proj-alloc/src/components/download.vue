<template>
  <button v-on:click="downloadTextFile(JSONObject, name, filetype)">
    Download {{ name }}
  </button>
</template>

<script>
export default {
  name: "Download",
  props: ["name", "JSONObject", "filetype"],
  data() {
    return {};
  },
  methods: {
    downloadTextFile(JSONObj, filename, filetype) {
      const text = JSON.stringify(JSONObj, null, 2);
      const a = document.createElement("a");
      const type = filename.split(".").pop();
      a.href = URL.createObjectURL(
        new Blob([text], { type: `text/${type === "txt" ? "plain" : type}` })
      );
      a.download = filename + "." + filetype;
      a.click();
    },
  },
};
</script>
