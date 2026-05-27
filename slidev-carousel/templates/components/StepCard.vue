<script setup lang="ts">
defineProps<{
  step: number
  title: string
  body?: string
  icon?: string
}>()
</script>

<template>
  <div class="step-card">
    <div class="step-badge" v-motion :initial="{ scale: 0, rotate: -20 }" :enter="{ scale: 1, rotate: 0 }">
      <span v-if="icon" class="step-icon" v-html="icon" />
      <span v-else class="step-num">{{ step }}</span>
    </div>
    <div class="step-content">
      <div class="step-tag">passo {{ step }}</div>
      <h2 class="step-title" v-motion :initial="{ y: 30, opacity: 0 }" :enter="{ y: 0, opacity: 1, transition: { delay: 150 } }">{{ title }}</h2>
      <p v-if="body" class="step-body" v-motion :initial="{ y: 30, opacity: 0 }" :enter="{ y: 0, opacity: 1, transition: { delay: 250 } }">{{ body }}</p>
    </div>
  </div>
</template>

<style scoped>
.step-card {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 4rem 3.5rem;
  gap: 2.5rem;
}

.step-badge {
  width: 7rem;
  height: 7rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #5eead4, #818cf8);
  box-shadow: 0 0 40px rgba(94, 234, 212, 0.35);
  font-weight: 800;
}

.step-num {
  font-size: 3.5rem;
  color: #0a0e1a;
  font-variant-numeric: tabular-nums;
}

.step-icon {
  width: 3.5rem;
  height: 3.5rem;
  color: #0a0e1a;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.step-content {
  display: flex;
  flex-direction: column;
  gap: 1.2rem;
}

.step-tag {
  font-size: 0.85rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: rgba(94, 234, 212, 0.8);
}

.step-title {
  font-size: clamp(2.4rem, 5.5vw, 3.8rem);
  font-weight: 800;
  line-height: 1.1;
  letter-spacing: -0.02em;
  margin: 0;
}

.step-body {
  font-size: clamp(1.3rem, 2.6vw, 1.7rem);
  line-height: 1.5;
  color: rgba(248, 250, 252, 0.75);
  margin: 0;
  max-width: 95%;
}
</style>
