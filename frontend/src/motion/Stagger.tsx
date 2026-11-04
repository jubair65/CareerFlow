import type { ReactNode } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { MOTION } from './tokens';

interface StaggerProps {
  children: ReactNode;
  staggerDelay?: number;
  className?: string;
}

export function Stagger({
  children,
  staggerDelay = MOTION.stagger.normal,
  className = '',
}: StaggerProps) {
  const prefersReduced = useReducedMotion();

  if (prefersReduced) {
    return <div className={className}>{children}</div>;
  }

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={{
        hidden: { opacity: 0 },
        visible: {
          opacity: 1,
          transition: {
            staggerChildren: staggerDelay,
          },
        },
      }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

interface RevealProps {
  children: ReactNode;
  delay?: number;
  distance?: number;
  direction?: 'up' | 'down' | 'left' | 'right';
  className?: string;
}

export function Reveal({
  children,
  delay = 0,
  distance = MOTION.distance.md,
  direction = 'up',
  className = '',
}: RevealProps) {
  const prefersReduced = useReducedMotion();

  if (prefersReduced) {
    return <div className={className}>{children}</div>;
  }

  const offset = {
    up: { y: distance, x: 0 },
    down: { y: -distance, x: 0 },
    left: { x: distance, y: 0 },
    right: { x: -distance, y: 0 },
  }[direction];

  return (
    <motion.div
      initial={{ opacity: 0, ...offset }}
      animate={{ opacity: 1, x: 0, y: 0 }}
      transition={{
        duration: MOTION.duration.component,
        delay,
        ease: MOTION.easeOutQuint,
      }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

interface ListItemProps {
  children: ReactNode;
  layoutId?: string;
  className?: string;
  onClick?: () => void;
}

export function ListItem({
  children,
  layoutId,
  className = '',
  onClick,
}: ListItemProps) {
  const prefersReduced = useReducedMotion();

  if (prefersReduced) {
    return (
      <div className={className} onClick={onClick}>
        {children}
      </div>
    );
  }

  return (
    <motion.div
      layout={layoutId ? undefined : 'position'}
      layoutId={layoutId}
      variants={{
        hidden: { opacity: 0, y: MOTION.distance.sm },
        visible: {
          opacity: 1,
          y: 0,
          transition: {
            duration: MOTION.duration.component,
            ease: MOTION.easeOutQuint,
          },
        },
      }}
      transition={{
        duration: MOTION.duration.component,
        ease: MOTION.easeOutQuint,
      }}
      className={className}
      onClick={onClick}
    >
      {children}
    </motion.div>
  );
}

