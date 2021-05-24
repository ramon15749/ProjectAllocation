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
  name: "Uploadfile",
  data() {
    return {
      file: "",
    };
  },
  props: ["filename", "modelValue"],
  methods: {
    handleFileUpload() {
      this.file = this.$refs.file.files[0];
      this.$emit("update:modelValue", this.file);
    },
  },
};
</script>