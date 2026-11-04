import { useState, useEffect } from 'react';
import { useReducedMotion } from 'framer-motion';

/**
 * Counts up from 0 to target value over specified duration using easeOutQuint.
 * Respects prefers-reduced-motion.
 */
export function useCountUp(target: number | null | undefined, durationMs = 800): number {
  const prefersReduced = useReducedMotion();
  const [count, setCount] = useState<number>(() => (prefersReduced || target == null ? (target ?? 0) : 0));

  useEffect(() => {
    if (target == null) {
      setCount(0);
      return;
    }

    if (prefersReduced) {
      setCount(target);
      return;
    }

    let startTimestamp: number | null = null;
    let animId: number;

    const step = (timestamp: number) => {
      if (!startTimestamp) startTimestamp = timestamp;
      const progress = Math.min((timestamp - startTimestamp) / durationMs, 1);
      // easeOutQuint: 1 - Math.pow(1 - progress, 5)
      const ease = 1 - Math.pow(1 - progress, 5);
      setCount(Math.round(ease * target));

      if (progress < 1) {
        animId = requestAnimationFrame(step);
      }
    };

    animId = requestAnimationFrame(step);

    return () => cancelAnimationFrame(animId);
  }, [target, durationMs, prefersReduced]);

  return count;
}

