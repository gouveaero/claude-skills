<script setup lang="ts">
import { ref, computed } from 'vue'

interface PollOption {
  id: string
  label: string
  initialVotes?: number
}

const props = withDefaults(defineProps<{
  question: string
  options: PollOption[]
}>(), {})

const votes = ref<Record<string, number>>(
  Object.fromEntries(props.options.map(o => [o.id, o.initialVotes ?? 0]))
)
const userPick = ref<string | null>(null)

const total = computed(() => Object.values(votes.value).reduce((a, b) => a + b, 0))
const pct = (id: string) => total.value > 0 ? Math.round((votes.value[id] / total.value) * 100) : 0

function vote(id: string) {
  if (userPick.value === id) return
  if (userPick.value) votes.value[userPick.value]--
  votes.value[id]++
  userPick.value = id
}

function reset() {
  Object.keys(votes.value).forEach(k => { votes.value[k] = props.options.find(o => o.id === k)?.initialVotes ?? 0 })
  userPick.value = null
}
</script>

<template>
  <div class="interactive-poll">
    <h3 class="poll-question">{{ question }}</h3>
    <div class="poll-options">
      <button
        v-for="opt in options"
        :key="opt.id"
        class="poll-option"
        :class="{ 'is-picked': userPick === opt.id }"
        @click="vote(opt.id)"
      >
        <div class="poll-bar" :style="{ width: `${pct(opt.id)}%` }" />
        <div class="poll-content">
          <span class="poll-label">{{ opt.label }}</span>
          <span class="poll-pct">{{ pct(opt.id) }}%</span>
        </div>
      </button>
    </div>
    <div class="poll-footer">
      <span class="poll-total">{{ total }} {{ total === 1 ? 'voto' : 'votos' }}</span>
      <button class="poll-reset" @click="reset">reset</button>
    </div>
  </div>
</template>

<style scoped>
.interactive-poll {
  max-width: 36rem;
  width: 100%;
  margin: 0 auto;
}

.poll-question {
  font-size: 1.5rem;
  font-weight: 600;
  text-align: center;
  margin-bottom: 1.5rem;
  letter-spacing: -0.01em;
}

.poll-options {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.poll-option {
  position: relative;
  display: block;
  width: 100%;
  padding: 0.85rem 1.1rem;
  background: rgba(15, 23, 42, 0.5);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 10px;
  text-align: left;
  cursor: pointer;
  overflow: hidden;
  transition: border-color 0.25s ease, background 0.25s ease;
  font: inherit;
  color: inherit;
}

.poll-option:hover {
  border-color: rgba(94, 234, 212, 0.4);
}

.poll-option.is-picked {
  border-color: var(--accent, #5eead4);
  background: rgba(94, 234, 212, 0.08);
}

.poll-bar {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, rgba(94, 234, 212, 0.25), rgba(129, 140, 248, 0.18));
  transition: width 0.55s cubic-bezier(0.4, 0, 0.2, 1);
}

.poll-content {
  position: relative;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.poll-label {
  font-weight: 500;
  font-size: 1rem;
}

.poll-pct {
  font-size: 0.95rem;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  color: var(--accent, #5eead4);
}

.poll-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1rem;
  font-size: 0.8rem;
  color: var(--muted, #94a3b8);
}

.poll-reset {
  background: none;
  border: 1px solid rgba(148, 163, 184, 0.25);
  color: inherit;
  padding: 0.25rem 0.7rem;
  border-radius: 6px;
  font-size: 0.75rem;
  cursor: pointer;
  font: inherit;
}
.poll-reset:hover { background: rgba(148, 163, 184, 0.1); }
</style>
