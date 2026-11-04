import type { ReactNode } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { MOTION } from './tokens';

interface PageTransitionProps {
  children: ReactNode;
  className?: string;
}

export function PageTransition({ children, className = '' }: PageTransitionProps) {
  const prefersReduced = useReducedMotion();

  if (prefersReduced) {
    return <div className={`w-full ${className}`}>{children}</div>;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -4 }}
      transition={{
        duration: 0.2, // 200ms cross-fade
        ease: MOTION.easeOutQuint,
      }}
      className={`w-full ${className}`}
    >
      {children}
    </motion.div>
  );
}

