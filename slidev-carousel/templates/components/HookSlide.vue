<script setup lang="ts">
withDefaults(defineProps<{
  hook: string
  subhook?: string
  variant?: 'dark' | 'gradient' | 'accent'
}>(), {
  variant: 'dark',
})
</script>

<template>
  <div class="hook-slide" :class="`hook-slide--${variant}`">
    <div class="hook-text">
      <h1 class="hook-headline">{{ hook }}</h1>
      <p v-if="subhook" class="hook-sub">{{ subhook }}</p>
    </div>
    <div class="hook-swipe">
      <span class="hook-swipe-icon"><mdi-arrow-right /></span>
      <span class="hook-swipe-label">swipe</span>
    </div>
  </div>
</template>

<style scoped>
.hook-slide {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 4rem 3.5rem 5rem;
  background: var(--bg, #0a0e1a);
}

.hook-slide--dark { background: #0a0e1a; }

.hook-slide--gradient {
  background: linear-gradient(135deg, #0a0e1a 0%, #1e1b4b 50%, #0f172a 100%);
}

.hook-slide--accent {
  background: linear-gradient(135deg, #134e4a 0%, #0a0e1a 100%);
}

.hook-text {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.hook-headline {
  font-size: clamp(3.5rem, 9vw, 6rem);
  font-weight: 800;
  letter-spacing: -0.03em;
  line-height: 1.04;
  margin: 0 0 1.5rem;
  background: linear-gradient(135deg, #f8fafc 0%, #5eead4 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.hook-sub {
  font-size: clamp(1.4rem, 2.8vw, 2rem);
  color: rgba(248, 250, 252, 0.75);
  line-height: 1.4;
  font-weight: 500;
  margin: 0;
  max-width: 90%;
}

.hook-swipe {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-size: 1.1rem;
  color: rgba(94, 234, 212, 0.85);
  font-weight: 500;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  animation: nudge 1.8s ease-in-out infinite;
}

.hook-swipe-icon {
  display: inline-flex;
  font-size: 1.5rem;
}

@keyframes nudge {
  0%, 100% { transform: translateX(0); }
  50% { transform: translateX(8px); }
}
</style>
