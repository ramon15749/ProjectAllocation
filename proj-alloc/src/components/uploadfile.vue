<template>
  <div class="container">
    <div class="large-12 medium-12 small-12 cell">
      <p>{{ filename }}</p>
    </div>
    <FileUpload
      name="demo"
      mode="basic"
      :customUpload="true"
      @uploader="onUpload"
      :auto="true"
      accept=".csv"
    >
      <template #empty>
        <p>Drag and drop files to here to upload.</p>
      </template>
    </FileUpload>
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
    onUpload(event) {
      this.file = event.files[0];
      this.$toast.add({
        severity: "info",
        summary: "Success",
        detail: "File Uploaded",
        life: 3000,
      });
      console.log(event.files);
      this.$emit("update:modelValue", this.file);
    },
  },
};
</script>