import { useEffect, useState, useRef } from 'react';
import { useReducedMotion } from 'framer-motion';

interface UseInViewOnceOptions {
  threshold?: number;
  rootMargin?: string;
}

export function useInViewOnce<T extends HTMLElement = HTMLDivElement>(
  options: UseInViewOnceOptions = {}
) {
  const { threshold = 0.15, rootMargin = '0px 0px -40px 0px' } = options;
  const prefersReduced = useReducedMotion();
  const ref = useRef<T | null>(null);
  const [isInView, setIsInView] = useState(prefersReduced || false);

  useEffect(() => {
    if (prefersReduced) {
      setIsInView(true);
      return;
    }

    const node = ref.current;
    if (!node) return;

    if (!('IntersectionObserver' in window)) {
      setIsInView(true);
      return;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsInView(true);
          observer.unobserve(node);
        }
      },
      { threshold, rootMargin }
    );

    observer.observe(node);

    return () => {
      observer.disconnect();
    };
  }, [threshold, rootMargin, prefersReduced]);

  return { ref, isInView };
}

