/**
 * CareerFlow Shared Motion Tokens & Interaction Rules
 * 
 * Strict studio-grade animation system.
 * - Easing: ease-out-quint for entrances, ease-in-out-cubic for transitions.
 * - Durations: micro (150-200ms), component (300-450ms), section (600-900ms).
 * - Distances: 8-16px.
 * - Stagger: 40-70ms.
 * - Prefers-reduced-motion: instant states, no counters, no stagger.
 */

export const MOTION = {
  // Cubic bezier easing curves
  easeOutQuint: [0.22, 1, 0.36, 1] as const,
  easeInOutCubic: [0.65, 0, 0.35, 1] as const,
  easeOutQuad: [0.25, 0.46, 0.45, 0.94] as const,

  // Durations in seconds
  duration: {
    micro: 0.18,       // 180ms - hovers, tooltips, toggles
    component: 0.35,   // 350ms - drawers, cards, modals, tabs
    section: 0.65,     // 650ms - page sections, reveals
    countUp: 0.8,      // 800ms - number counter
    chartDraw: 0.9,    // 900ms - SVG path stroke draw
  },

  // Stagger in seconds
  stagger: {
    fast: 0.04,        // 40ms
    normal: 0.06,      // 60ms
    relaxed: 0.08,     // 80ms
  },

  // Distance offsets in pixels
  distance: {
    sm: 8,
    md: 12,
    lg: 16,
  },
} as const;

export const BRAND_TOKENS = {
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

/**
 * Standard interaction states (CSS classes & Framer Motion props)
 * 
 * - Hover: 150ms transform translateY(-2px), subtle shadow bump, never scale text.
 * - Active / Press: 80ms translateY(0px) scale(0.99).
 * - Disabled: opacity 0.45, cursor not-allowed, no hover transform.
 * - Focus: 2px solid ring (#f5c84b / #277254) with 2px offset, visible on keyboard nav only.
 */
export const INTERACTION_CLASSES = {
  cardHover: 'transition-all duration-150 ease-out hover:-translate-y-0.5 hover:shadow-md active:translate-y-0 active:scale-[0.99]',
  buttonHover: 'transition-all duration-150 ease-out active:scale-[0.98]',
  focusRing: 'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#277254] focus-visible:ring-offset-2',
  disabled: 'disabled:opacity-45 disabled:cursor-not-allowed disabled:hover:translate-y-0 disabled:hover:shadow-none',
} as const;

