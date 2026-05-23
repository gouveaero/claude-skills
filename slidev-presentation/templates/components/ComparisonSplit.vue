<script setup lang="ts">
import { computed } from 'vue'
import { useSlideContext } from '@slidev/client'

const props = withDefaults(defineProps<{
  beforeTitle?: string
  afterTitle?: string
  revealAfterOnClick?: boolean
}>(), {
  beforeTitle: 'Antes',
  afterTitle: 'Depois',
  revealAfterOnClick: true,
})

const { $clicks } = useSlideContext()
const showAfter = computed(() => !props.revealAfterOnClick || $clicks.value >= 1)
</script>

<template>
  <div class="comparison-split">
    <div class="comparison-side comparison-before">
      <div class="comparison-label">{{ beforeTitle }}</div>
      <div class="comparison-content">
        <slot name="before" />
      </div>
    </div>
    <div class="comparison-divider">
      <div class="comparison-arrow" :class="{ 'is-active': showAfter }">→</div>
    </div>
    <div class="comparison-side comparison-after" :class="{ 'is-visible': showAfter }">
      <div class="comparison-label comparison-label--accent">{{ afterTitle }}</div>
      <div class="comparison-content">
        <slot name="after" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.comparison-split {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 1rem;
  align-items: stretch;
  width: 100%;
  max-width: 64rem;
  margin: 0 auto;
}

.comparison-side {
  padding: 1.5rem;
  border-radius: 14px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: rgba(15, 23, 42, 0.4);
}

.comparison-after {
  border-color: rgba(94, 234, 212, 0.35);
  background: rgba(94, 234, 212, 0.06);
  opacity: 0;
  transform: translateX(12px);
  transition: opacity 0.5s ease, transform 0.5s ease;
}

.comparison-after.is-visible {
  opacity: 1;
  transform: translateX(0);
}

.comparison-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted, #94a3b8);
  margin-bottom: 0.8rem;
}

.comparison-label--accent {
  color: var(--accent, #5eead4);
}

.comparison-content {
  font-size: 1rem;
  line-height: 1.55;
}

.comparison-divider {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 0.5rem;
}

.comparison-arrow {
  font-size: 2rem;
  color: var(--muted, #94a3b8);
  transition: color 0.4s ease, transform 0.4s ease;
}

.comparison-arrow.is-active {
  color: var(--accent, #5eead4);
  transform: scale(1.12);
}
</style>
