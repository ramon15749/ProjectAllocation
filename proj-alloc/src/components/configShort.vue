<template>
  <div>
    <p>
      {{ configName }}
      <InputText
        type="number"
        v-bind:placeholder="configName"
        :value="modelValue"
        @input="$emit('update:modelValue', $event.target.value)"
      />
    </p>
  </div>
</template>

<script>
export default {
  name: "ConfigShort",
  props: ["configName", "modelValue"],
  data() {
    return {
      value: "",
    };
  },
  methods: {
    submitConfig(e) {
      console.log("called");
      console.log(e);
    },
  },
};
</script>