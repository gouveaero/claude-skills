<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref } from 'vue'
import { gsap } from 'gsap'

const props = withDefaults(defineProps<{
  value: number
  prefix?: string
  suffix?: string
  label?: string
  duration?: number
  decimals?: number
}>(), {
  duration: 1.6,
  decimals: 0,
  prefix: '',
  suffix: ''
})

const displayValue = ref(0)
let tween: gsap.core.Tween | null = null

onMounted(() => {
  const state = { n: 0 }
  tween = gsap.to(state, {
    n: props.value,
    duration: props.duration,
    ease: 'power3.out',
    onUpdate: () => {
      displayValue.value = state.n
    }
  })
})

onBeforeUnmount(() => {
  tween?.kill()
})

function formatted(n: number) {
  return n.toFixed(props.decimals)
}
</script>

<template>
  <div class="stat-number">
    <div class="value">
      <span v-if="prefix" class="prefix">{{ prefix }}</span>
      <span class="num">{{ formatted(displayValue) }}</span>
      <span v-if="suffix" class="suffix">{{ suffix }}</span>
    </div>
    <div v-if="label" class="label">{{ label }}</div>
  </div>
</template>

<style scoped>
.stat-number {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}
.value {
  font-size: clamp(3rem, 7vw, 5.5rem);
  font-weight: 800;
  line-height: 1;
  font-variant-numeric: tabular-nums;
  background: linear-gradient(135deg, #5eead4 0%, #818cf8 60%, #f472b6 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  letter-spacing: -0.02em;
}
.prefix, .suffix {
  font-size: 0.55em;
  vertical-align: top;
  opacity: 0.85;
  margin: 0 0.1em;
}
.label {
  font-size: 1rem;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.18em;
  font-weight: 500;
}
</style>
