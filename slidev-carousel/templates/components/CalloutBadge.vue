<script setup lang="ts">
withDefaults(defineProps<{
  text?: string
  variant?: 'new' | 'live' | 'alert' | 'highlight'
  pulse?: boolean
}>(), {
  text: 'novo',
  variant: 'highlight',
  pulse: true,
})
</script>

<template>
  <span class="callout-badge" :class="[`callout-badge--${variant}`, { 'is-pulsing': pulse }]">
    <span class="callout-badge-dot" />
    <span class="callout-badge-text"><slot>{{ text }}</slot></span>
  </span>
</template>

<style scoped>
.callout-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.3rem 0.7rem;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  border: 1px solid transparent;
  animation: scale-in 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.callout-badge--new {
  color: #5eead4;
  background: rgba(94, 234, 212, 0.12);
  border-color: rgba(94, 234, 212, 0.4);
}

.callout-badge--live {
  color: #f87171;
  background: rgba(248, 113, 113, 0.12);
  border-color: rgba(248, 113, 113, 0.4);
}

.callout-badge--alert {
  color: #fbbf24;
  background: rgba(251, 191, 36, 0.12);
  border-color: rgba(251, 191, 36, 0.4);
}

.callout-badge--highlight {
  color: #818cf8;
  background: rgba(129, 140, 248, 0.12);
  border-color: rgba(129, 140, 248, 0.4);
}

.callout-badge-dot {
  width: 0.4rem;
  height: 0.4rem;
  border-radius: 50%;
  background: currentColor;
}

.callout-badge.is-pulsing .callout-badge-dot {
  animation: pulse 1.6s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; box-shadow: 0 0 0 0 currentColor; }
  50% { opacity: 0.6; box-shadow: 0 0 0 6px transparent; }
}

@keyframes scale-in {
  from { opacity: 0; transform: scale(0.5); }
  to { opacity: 1; transform: scale(1); }
}
</style>
