<script setup lang="ts">
import { computed } from 'vue'
import { useNav } from '@slidev/client'

const { currentPage, total } = useNav()
const progress = computed(() => total.value > 0 ? (currentPage.value / total.value) * 100 : 0)
</script>

<template>
  <!-- Continuidade panorâmica: linha que cresce ao longo dos slides -->
  <div class="panoramic-bar">
    <div class="panoramic-fill" :style="{ width: progress + '%' }" />
  </div>
  <!-- Indicador discreto N/Total -->
  <div class="slide-indicator">{{ currentPage }} / {{ total }}</div>
</template>

<style scoped>
.panoramic-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 6px;
  background: rgba(148, 163, 184, 0.15);
  pointer-events: none;
  z-index: 100;
}

.panoramic-fill {
  height: 100%;
  background: linear-gradient(90deg, #5eead4 0%, #818cf8 50%, #f472b6 100%);
  transition: width 0.7s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 0 12px rgba(94, 234, 212, 0.5);
}

.slide-indicator {
  position: fixed;
  bottom: 1.2rem;
  right: 1.5rem;
  font-size: 0.85rem;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  color: rgba(248, 250, 252, 0.55);
  pointer-events: none;
  z-index: 100;
  letter-spacing: 0.06em;
}
</style>
