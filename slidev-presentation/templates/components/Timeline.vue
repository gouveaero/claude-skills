<script setup lang="ts">
import { useSlideContext } from '@slidev/client'

interface TimelineItem {
  date?: string
  title: string
  body?: string
  icon?: string
}

const props = withDefaults(defineProps<{
  items: TimelineItem[]
  orientation?: 'horizontal' | 'vertical'
  revealOnClick?: boolean
}>(), {
  orientation: 'horizontal',
  revealOnClick: true,
})

const { $clicks } = useSlideContext()
const isVisible = (i: number) => !props.revealOnClick || $clicks.value >= i
</script>

<template>
  <div class="timeline" :class="`timeline--${orientation}`">
    <div class="timeline-track">
      <div
        v-for="(_, i) in items"
        :key="`dot-${i}`"
        class="timeline-dot"
        :class="{ 'is-visible': isVisible(i) }"
      />
    </div>
    <div class="timeline-items">
      <div
        v-for="(item, i) in items"
        :key="`item-${i}`"
        class="timeline-item"
        :class="{ 'is-visible': isVisible(i) }"
      >
        <div v-if="item.date" class="timeline-date">{{ item.date }}</div>
        <div class="timeline-title">
          <span v-if="item.icon" class="timeline-icon" v-html="item.icon" />
          {{ item.title }}
        </div>
        <div v-if="item.body" class="timeline-body">{{ item.body }}</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.timeline { position: relative; padding: 1rem 0; }

.timeline--horizontal {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.timeline--horizontal .timeline-track {
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  margin: 0 0.5rem;
}
.timeline--horizontal .timeline-track::before {
  content: '';
  position: absolute;
  left: 0.6rem; right: 0.6rem;
  top: 50%;
  height: 2px;
  background: linear-gradient(90deg, var(--accent, #5eead4) 0%, var(--accent-2, #818cf8) 100%);
  transform: translateY(-50%);
  opacity: 0.3;
}
.timeline--horizontal .timeline-items {
  display: grid;
  grid-template-columns: repeat(v-bind('items.length'), 1fr);
  gap: 1rem;
  text-align: center;
}

.timeline--vertical { display: grid; grid-template-columns: auto 1fr; gap: 0 1.5rem; }
.timeline--vertical .timeline-track {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-items: center;
  position: relative;
}
.timeline--vertical .timeline-track::before {
  content: '';
  position: absolute;
  top: 0.4rem; bottom: 0.4rem;
  left: 50%;
  width: 2px;
  background: linear-gradient(180deg, var(--accent, #5eead4) 0%, var(--accent-2, #818cf8) 100%);
  transform: translateX(-50%);
  opacity: 0.3;
}
.timeline--vertical .timeline-items {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.timeline-dot {
  width: 1rem;
  height: 1rem;
  border-radius: 50%;
  background: var(--accent, #5eead4);
  box-shadow: 0 0 0 4px rgba(94, 234, 212, 0.18);
  opacity: 0;
  transform: scale(0.3);
  transition: opacity 0.4s ease, transform 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
  z-index: 1;
}
.timeline-dot.is-visible { opacity: 1; transform: scale(1); }

.timeline-item {
  opacity: 0;
  transform: translateY(10px);
  transition: opacity 0.55s ease, transform 0.55s ease;
}
.timeline-item.is-visible { opacity: 1; transform: translateY(0); }

.timeline-date {
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--muted, #94a3b8);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 0.3rem;
}

.timeline-title {
  font-size: 1.05rem;
  font-weight: 600;
  margin-bottom: 0.25rem;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
}

.timeline-icon {
  display: inline-flex;
  width: 1.2rem; height: 1.2rem;
  color: var(--accent, #5eead4);
}

.timeline-body {
  font-size: 0.85rem;
  color: var(--muted, #94a3b8);
  line-height: 1.4;
}
</style>
