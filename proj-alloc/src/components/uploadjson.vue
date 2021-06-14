<template>
  <div class="container">
    <div class="large-12 medium-12 small-12 cell">
      <p>{{ filename }}</p>
      <label
        >File
        <input
          type="file"
          id="file"
          ref="file"
          v-on:change="handleFileUpload()"
        />
      </label>
    </div>
  </div>
</template>


<script>
export default {
  name: "Uploadjson",
  data() {
    return {
      file: "",
      text: "",
    };
  },
  props: ["filename", "modelValue"],
  methods: {
    handleFileUpload() {
      this.file = this.$refs.file.files[0];
      var r = new FileReader();
      var self = this;
      r.onload = (function () {
        return function (e) {
          let json = JSON.parse(e.target.result);
          this.text = json;
          console.log(this.text);
          self.$emit("update:modelValue", this.text);
        };
      })(this.file);
      r.readAsText(this.file);
      this;
      console.log(this.text);
    },
  },
};
</script>