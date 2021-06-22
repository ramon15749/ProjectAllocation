<template>
  <div>
    <h3>Special Loading</h3>
    <div v-for="(applicant, index) in applicants" v-bind:key="index">
      <div class="p-inputgroup">
        <span @click="deleteVisa(counter)">x</span>
        <Dropdown
          v-model="applicants[index].key"
          :options="this.configList"
          optionLabel="name"
          optionValue="id"
          placeholder="Select a Lecturer"
          :filter="true"
          filterPlaceholder="Find Lecturer"
          @input="updateData()"
        />
        <InputNumber v-model="applicants[index].value" @input="updateData()" />
      </div>
      <br />
    </div>
    <Button @click="addVisa">Another Lecturer</Button>
  </div>
</template>


<script>
export default {
  name: "ConfigLong",
  props: ["configName", "configList", "modelValue", "initValue"],
  data() {
    return {
      applicants: [
        {
          key: "",
          value: "",
        },
      ],
    };
  },
  methods: {
    updateData() {
      this.$emit("update:modelValue", this.applicants);
    },
    addVisa() {
      this.applicants.push({
        key: "",
        value: "",
      });
    },
    deleteVisa(counter) {
      this.applicants.splice(counter, 1);
    },
  },
};
</script>