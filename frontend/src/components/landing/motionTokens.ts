/**
 * CareerFlow Motion & Design Tokens
 * 
 * Strict studio-grade animation system.
 * - Easing: ease-out-quint for entrances, ease-in-out-cubic for transitions.
 * - Durations: micro (150-200ms), component (300-450ms), section (600-900ms).
 * - Distances: small (8-24px), stagger (40-80ms).
 * - No bounce, no elastic, 60fps transform + opacity only.
 */

export const MOTION = {
  // Cubic bezier easing arrays for Framer Motion
  easeOutQuint: [0.22, 1, 0.36, 1] as const,
  easeInOutCubic: [0.65, 0, 0.35, 1] as const,

  // GSAP easing strings
  gsapEaseOutQuint: 'power4.out',
  gsapEaseInOutCubic: 'power2.inOut',

  // Durations in seconds
  duration: {
    micro: 0.18,
    component: 0.38,
    section: 0.75,
  },

  // Stagger intervals in seconds
  stagger: {
    fast: 0.04,
    normal: 0.06,
    word: 0.075,
  },

  // Distance offsets in pixels
  distance: {
    sm: 8,
    md: 16,
    lg: 24,
  },
} as const;

export const BRAND = {
  colors: {
    navy: '#253142',
    yellow: '#f5c84b',
    yellowHover: '#e8b93c',
    green: '#277254',
    greenLight: '#e2f0e9',
    cream: '#f5f1e6',
    border: '#ddd8ca',
    borderDark: '#3a4b60',
    cardDark: '#2d3b4e',
    textMain: '#253142',
    textMuted: '#4b5563',
    textDarkMain: '#faf7ef',
    textDarkMuted: '#c3ccd5',
    eyebrowLight: '#7c5e14',
    eyebrowDark: '#f5c84b',
  },
  layout: {
    container: 'max-w-[1150px] mx-auto px-6',
  },
} as const;

