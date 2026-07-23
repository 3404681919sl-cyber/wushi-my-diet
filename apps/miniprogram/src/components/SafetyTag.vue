<template>
  <text class="wushi-tag" :style="{ background: color }">{{ label }}</text>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { safetyColor, safetyLabel } from "../utils/format";

const props = defineProps<{ level: string }>();

const color = computed(() => safetyColor(props.level));
const label = computed(() => safetyLabel(props.level));
</script>
