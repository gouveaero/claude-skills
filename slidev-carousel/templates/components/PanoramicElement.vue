<script setup lang="ts">
withDefaults(defineProps<{
  progress?: number
  color?: string
  position?: 'top' | 'bottom' | 'left' | 'right'
}>(), {
  progress: 0,
  color: 'var(--accent, #5eead4)',
  position: 'bottom',
})
</script>

<template>
  <div class="panoramic" :class="`panoramic--${position}`">
    <div class="panoramic-track">
      <div
        class="panoramic-fill"
        :style="{
          width: position === 'top' || position === 'bottom' ? progress + '%' : '100%',
          height: position === 'left' || position === 'right' ? progress + '%' : '100%',
          background: color,
        }"
      />
    </div>
  </div>
</template>

<style scoped>
.panoramic {
  position: fixed;
  pointer-events: none;
  z-index: 50;
}

.panoramic--bottom {
  bottom: 0;
  left: 0;
  right: 0;
  height: 6px;
}

.panoramic--top {
  top: 0;
  left: 0;
  right: 0;
  height: 6px;
}

.panoramic--left {
  left: 0;
  top: 0;
  bottom: 0;
  width: 6px;
}

.panoramic--right {
  right: 0;
  top: 0;
  bottom: 0;
  width: 6px;
}

.panoramic-track {
  position: relative;
  width: 100%;
  height: 100%;
  background: rgba(148, 163, 184, 0.15);
}

.panoramic-fill {
  position: absolute;
  top: 0;
  left: 0;
  transition: width 0.7s cubic-bezier(0.4, 0, 0.2, 1), height 0.7s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 0 12px currentColor;
}
</style>
