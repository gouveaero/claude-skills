<script setup lang="ts">
withDefaults(defineProps<{
  cta?: string
  handle?: string
  backArrow?: boolean
}>(), {
  cta: 'Salva esse post',
  handle: '@gouveaero',
  backArrow: true,
})
</script>

<template>
  <div class="cta-slide">
    <div class="cta-headline-block">
      <h1 class="cta-headline" v-motion :initial="{ y: 30, opacity: 0 }" :enter="{ y: 0, opacity: 1 }">
        {{ cta }}
      </h1>
      <p class="cta-instruction" v-motion :initial="{ opacity: 0 }" :enter="{ opacity: 1, transition: { delay: 200 } }">
        Pra não esquecer.
      </p>
    </div>

    <div class="cta-handle-block" v-motion :initial="{ scale: 0.9, opacity: 0 }" :enter="{ scale: 1, opacity: 1, transition: { delay: 300 } }">
      <div class="cta-handle-label">siga</div>
      <div class="cta-handle">{{ handle }}</div>
    </div>

    <div v-if="backArrow" class="cta-back" v-motion :initial="{ opacity: 0 }" :enter="{ opacity: 1, transition: { delay: 500 } }">
      <span class="cta-back-icon"><mdi-arrow-left /></span>
      <span>volta pro início pra rever</span>
    </div>
  </div>
</template>

<style scoped>
.cta-slide {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 4rem 3.5rem 5rem;
  background: linear-gradient(180deg, #0a0e1a 0%, #1e1b4b 100%);
}

.cta-headline-block { display: flex; flex-direction: column; gap: 0.8rem; }

.cta-headline {
  font-size: clamp(3rem, 8vw, 5rem);
  font-weight: 800;
  line-height: 1.05;
  letter-spacing: -0.025em;
  margin: 0;
  background: linear-gradient(135deg, #f8fafc, #5eead4);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.cta-instruction {
  font-size: 1.4rem;
  color: rgba(248, 250, 252, 0.65);
  margin: 0;
}

.cta-handle-block {
  text-align: center;
  padding: 2rem;
  background: rgba(94, 234, 212, 0.08);
  border: 2px solid rgba(94, 234, 212, 0.35);
  border-radius: 20px;
}

.cta-handle-label {
  font-size: 0.85rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.15em;
  color: rgba(94, 234, 212, 0.8);
  margin-bottom: 0.5rem;
}

.cta-handle {
  font-size: clamp(2rem, 5vw, 3rem);
  font-weight: 800;
  color: #5eead4;
  letter-spacing: -0.01em;
}

.cta-back {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-size: 1rem;
  color: rgba(248, 250, 252, 0.5);
  font-style: italic;
  animation: nudge-left 2s ease-in-out infinite;
}

.cta-back-icon {
  display: inline-flex;
  font-size: 1.2rem;
}

@keyframes nudge-left {
  0%, 100% { transform: translateX(0); }
  50% { transform: translateX(-6px); }
}
</style>
