<script setup lang="ts">
import { computed } from 'vue'
import { useSlideContext } from '@slidev/client'

interface Metric {
  value: string | number
  label: string
  prefix?: string
  suffix?: string
  icon?: string
}

const props = withDefaults(defineProps<{
  items: Metric[]
  cols?: number
  revealOnClick?: boolean
}>(), {
  cols: 2,
  revealOnClick: true,
})

const { $clicks } = useSlideContext()
const isVisible = (i: number) => !props.revealOnClick || $clicks.value >= i

const gridStyle = computed(() => ({
  'grid-template-columns': `repeat(${props.cols}, minmax(0, 1fr))`,
}))
</script>

<template>
  <div class="metric-grid" :style="gridStyle">
    <div
      v-for="(item, i) in items"
      :key="i"
      class="metric-cell"
      :class="{ 'is-visible': isVisible(i) }"
    >
      <div v-if="item.icon" class="metric-icon" v-html="item.icon" />
      <div class="metric-value">
        <span v-if="item.prefix" class="metric-prefix">{{ item.prefix }}</span>
        <span class="metric-number">{{ item.value }}</span>
        <span v-if="item.suffix" class="metric-suffix">{{ item.suffix }}</span>
      </div>
      <div class="metric-label">{{ item.label }}</div>
    </div>
  </div>
</template>

<style scoped>
.metric-grid {
  display: grid;
  gap: 1.5rem;
  width: 100%;
  max-width: 64rem;
  margin: 0 auto;
}

.metric-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
  background: rgba(94, 234, 212, 0.06);
  border: 1px solid rgba(94, 234, 212, 0.18);
  border-radius: 14px;
  opacity: 0;
  transform: translateY(12px);
  transition: opacity 0.55s ease, transform 0.55s ease;
}

.metric-cell.is-visible {
  opacity: 1;
  transform: translateY(0);
}

.metric-cell:nth-child(2) { transition-delay: 0.05s; }
.metric-cell:nth-child(3) { transition-delay: 0.10s; }
.metric-cell:nth-child(4) { transition-delay: 0.15s; }
.metric-cell:nth-child(5) { transition-delay: 0.20s; }
.metric-cell:nth-child(6) { transition-delay: 0.25s; }

.metric-icon {
  width: 2.2rem;
  height: 2.2rem;
  color: var(--accent, #5eead4);
  margin-bottom: 0.6rem;
}

.metric-value {
  display: flex;
  align-items: baseline;
  gap: 0.15rem;
  line-height: 1;
  margin-bottom: 0.45rem;
}

.metric-number {
  font-size: clamp(2.4rem, 5vw, 3.6rem);
  font-weight: 700;
  letter-spacing: -0.02em;
  background: linear-gradient(135deg, #5eead4 0%, #818cf8 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  font-variant-numeric: tabular-nums;
}

.metric-prefix, .metric-suffix {
  font-size: 1.2rem;
  font-weight: 500;
  color: var(--muted, #94a3b8);
}

.metric-label {
  font-size: 0.85rem;
  text-align: center;
  color: var(--muted, #94a3b8);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-weight: 500;
}
</style>
