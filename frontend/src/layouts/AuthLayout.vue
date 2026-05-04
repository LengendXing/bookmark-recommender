<template>
  <div class="min-h-screen flex items-center justify-center p-4 relative" style="background-color: hsl(var(--muted))">
    <!-- Dot pattern background -->
    <div class="absolute inset-0" style="background-image: radial-gradient(circle, hsl(var(--foreground) / 0.06) 1px, transparent 1px); background-size: 24px 24px" />
    <slot />
  </div>
</template>
