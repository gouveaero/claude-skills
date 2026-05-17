<script setup lang="ts">
import { computed } from 'vue'
import { useSlideContext } from '@slidev/client'

interface Step {
  lines: number[]
  note?: string
}

const props = defineProps<{
  code: string
  lang?: string
  steps: Step[]
}>()

const { $clicks } = useSlideContext()

const stepIdx = computed(() =>
  Math.min(Math.max($clicks.value - 1, 0), props.steps.length - 1)
)
const currentStep = computed(() => props.steps[stepIdx.value])

const lines = computed(() => props.code.split('\n'))
const isHighlighted = (idx: number) =>
  !!currentStep.value?.lines.includes(idx + 1)
</script>

<template>
  <div class="code-reveal">
    <pre class="code-block"><code><span
      v-for="(line, idx) in lines"
      :key="idx"
      class="code-line"
      :class="{ dim: !isHighlighted(idx), hl: isHighlighted(idx) }"
    ><span class="ln">{{ String(idx + 1).padStart(2, ' ') }}</span><span class="txt">{{ line || ' ' }}</span></span></code></pre>
    <transition name="note">
      <aside v-if="currentStep?.note" :key="stepIdx" class="note">
        <div class="note-idx">{{ stepIdx + 1 }} / {{ steps.length }}</div>
        <div class="note-text">{{ currentStep.note }}</div>
      </aside>
    </transition>
  </div>
</template>

<style scoped>
.code-reveal {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 300px;
  gap: 1.5rem;
  align-items: start;
  width: 100%;
}
.code-block {
  background: #0b1020;
  color: #e2e8f0;
  padding: 1.25rem 1rem 1.25rem 0.5rem;
  border-radius: 14px;
  font-size: 0.95rem;
  line-height: 1.65;
  overflow: auto;
  margin: 0;
  box-shadow: 0 10px 40px -10px rgba(0,0,0,0.4);
}
.code-block code { font-family: 'JetBrains Mono', ui-monospace, monospace; }
.code-line {
  display: flex;
  gap: 0.85rem;
  padding: 0 0.5rem;
  border-radius: 6px;
  transition: opacity 350ms ease, background 350ms ease, box-shadow 350ms ease;
}
.code-line.dim { opacity: 0.28; }
.code-line.hl {
  background: rgba(94, 234, 212, 0.1);
  box-shadow: inset 3px 0 0 #5eead4;
}
.ln {
  color: #475569;
  user-select: none;
  white-space: pre;
  font-variant-numeric: tabular-nums;
}
.hl .ln { color: #5eead4; }
.txt { white-space: pre; }
.note {
  position: sticky;
  top: 1rem;
  background: rgba(94, 234, 212, 0.08);
  border-left: 3px solid #5eead4;
  padding: 1rem 1.1rem;
  border-radius: 10px;
  font-size: 0.95rem;
  line-height: 1.55;
  color: #e2e8f0;
}
.note-idx {
  font-size: 0.75rem;
  color: #5eead4;
  text-transform: uppercase;
  letter-spacing: 0.15em;
  margin-bottom: 0.4rem;
}
.note-enter-active, .note-leave-active { transition: opacity 250ms, transform 250ms; }
.note-enter-from { opacity: 0; transform: translateY(8px); }
.note-leave-to { opacity: 0; transform: translateY(-8px); }
</style>
