<script setup lang="ts">
import { ref, computed } from 'vue'

interface Input {
  id: string
  label: string
  min: number
  max: number
  step?: number
  default: number
  suffix?: string
  prefix?: string
}

const props = withDefaults(defineProps<{
  inputs: Input[]
  formula: (vals: Record<string, number>) => number
  resultLabel?: string
  resultPrefix?: string
  resultSuffix?: string
  resultDecimals?: number
}>(), {
  resultLabel: 'Resultado',
  resultPrefix: '',
  resultSuffix: '',
  resultDecimals: 0,
})

const values = ref<Record<string, number>>(
  Object.fromEntries(props.inputs.map(i => [i.id, i.default]))
)

const result = computed(() => {
  const r = props.formula(values.value)
  return r.toFixed(props.resultDecimals)
})
</script>

<template>
  <div class="roi-calculator">
    <div class="roi-inputs">
      <div v-for="input in inputs" :key="input.id" class="roi-input">
        <div class="roi-input-header">
          <label :for="`roi-${input.id}`" class="roi-input-label">{{ input.label }}</label>
          <span class="roi-input-value">
            <span v-if="input.prefix" class="roi-aff">{{ input.prefix }}</span>
            {{ values[input.id] }}
            <span v-if="input.suffix" class="roi-aff">{{ input.suffix }}</span>
          </span>
        </div>
        <input
          :id="`roi-${input.id}`"
          type="range"
          v-model.number="values[input.id]"
          :min="input.min"
          :max="input.max"
          :step="input.step ?? 1"
          class="roi-slider"
        />
      </div>
    </div>
    <div class="roi-result">
      <div class="roi-result-label">{{ resultLabel }}</div>
      <div class="roi-result-value">
        <span v-if="resultPrefix" class="roi-aff">{{ resultPrefix }}</span>
        <span class="roi-result-number">{{ result }}</span>
        <span v-if="resultSuffix" class="roi-aff">{{ resultSuffix }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.roi-calculator {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 2rem;
  align-items: center;
  width: 100%;
  max-width: 56rem;
  margin: 0 auto;
}

.roi-inputs {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.roi-input-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 0.35rem;
}

.roi-input-label {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--muted, #94a3b8);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.roi-input-value {
  font-size: 1rem;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  color: var(--accent, #5eead4);
}

.roi-aff {
  font-size: 0.75em;
  color: var(--muted, #94a3b8);
  margin: 0 0.1rem;
}

.roi-slider {
  -webkit-appearance: none;
  appearance: none;
  width: 100%;
  height: 4px;
  background: rgba(148, 163, 184, 0.2);
  border-radius: 2px;
  outline: none;
}

.roi-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--accent, #5eead4);
  cursor: pointer;
  box-shadow: 0 0 0 4px rgba(94, 234, 212, 0.18);
}

.roi-slider::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--accent, #5eead4);
  cursor: pointer;
  border: 0;
  box-shadow: 0 0 0 4px rgba(94, 234, 212, 0.18);
}

.roi-result {
  text-align: center;
  padding: 1.5rem;
  background: linear-gradient(135deg, rgba(94, 234, 212, 0.08), rgba(129, 140, 248, 0.06));
  border: 1px solid rgba(94, 234, 212, 0.25);
  border-radius: 14px;
}

.roi-result-label {
  font-size: 0.78rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted, #94a3b8);
  margin-bottom: 0.5rem;
}

.roi-result-value {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 0.1rem;
}

.roi-result-number {
  font-size: clamp(2rem, 5vw, 3.2rem);
  font-weight: 700;
  letter-spacing: -0.02em;
  background: linear-gradient(135deg, #5eead4 0%, #818cf8 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  font-variant-numeric: tabular-nums;
}
</style>
