/**
 * CareerFlow Dashboard Motion System
 * 
 * Strict studio-grade animation system.
 * - Easing: ease-out-quint for entrances, ease-in-out-cubic for transitions.
 * - Durations: micro (150-200ms), component (300-450ms), section (600-900ms).
 * - Distances: 8-16px.
 * - Stagger: 40-70ms max.
 * - prefers-reduced-motion: instant states, no counters, no stagger.
 */

export const DASHBOARD_MOTION = {
  // Cubic bezier easing arrays for Framer Motion
  easeOutQuint: [0.22, 1, 0.36, 1] as const,
  easeInOutCubic: [0.65, 0, 0.35, 1] as const,

  // Durations in seconds
  duration: {
    micro: 0.18,
    component: 0.35,
    section: 0.65,
    countUp: 0.8,
    chartDraw: 0.9,
  },

  // Stagger in seconds
  stagger: {
    statCards: 0.05,
    items: 0.06,
  },

  // Distance offsets in pixels
  distance: {
    sm: 8,
    md: 12,
    lg: 16,
  },
} as const;

export const BRAND_COLORS = {
  navy: '#253142',
  yellow: '#f5c84b',
  yellowHover: '#e8b93c',
  green: '#277254',
  greenLight: '#e2f0e9',
  cream: '#f5f1e6',
  cardBg: '#ffffff',
  border: '#d9dbd1',
  borderDark: '#354255',
  textMain: '#253142',
  textMuted: '#687382',
  textSub: '#7b8490',
} as const;

