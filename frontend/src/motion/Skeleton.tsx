import { useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { MOTION } from './tokens';

interface SkeletonProps {
  delayMs?: number; // Only show skeleton if loading exceeds this time (default 300ms)
  className?: string;
  count?: number;
  height?: string | number;
  width?: string | number;
  rounded?: string;
}

export function Skeleton({
  delayMs = 300,
  className = '',
  count = 1,
  height = '1rem',
  width = '100%',
  rounded = 'rounded-lg',
}: SkeletonProps) {
  const [shouldRender, setShouldRender] = useState(delayMs === 0);
  const prefersReduced = useReducedMotion();

  useEffect(() => {
    if (delayMs === 0) return;
    const timer = setTimeout(() => setShouldRender(true), delayMs);
    return () => clearTimeout(timer);
  }, [delayMs]);

  if (!shouldRender) {
    return null;
  }

  const items = Array.from({ length: count });

  return (
    <div className="flex flex-col gap-2.5 w-full">
      {items.map((_, i) => (
        <div
          key={`skel-${i}`}
          style={{
            height: typeof height === 'number' ? `${height}px` : height,
            width: typeof width === 'number' ? `${width}px` : width,
          }}
          className={`bg-[#e8e6dc] ${rounded} ${
            prefersReduced ? '' : 'animate-pulse'
          } ${className}`}
        />
      ))}
    </div>
  );
}

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
    icon?: ReactNode;
  };
  className?: string;
}

export function EmptyState({
  icon,
  title,
  description,
  action,
  className = '',
}: EmptyStateProps) {
  const prefersReduced = useReducedMotion();

  return (
    <motion.div
      initial={prefersReduced ? { opacity: 0 } : { opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        duration: prefersReduced ? 0 : MOTION.duration.component,
        ease: MOTION.easeOutQuint,
      }}
      className={`flex flex-col items-center justify-center rounded-2xl border border-dashed border-[#d9dbd1] bg-[#faf8f2] p-8 text-center ${className}`}
    >
      {icon && (
        <div className="mb-3 grid h-12 w-12 place-items-center rounded-xl bg-[#eeebe2] text-[#556070]">
          {icon}
        </div>
      )}
      <h4 className="cf-display text-sm font-bold text-[#253142]">{title}</h4>
      <p className="mt-1 max-w-sm text-xs text-[#687382] leading-relaxed">
        {description}
      </p>
      {action && (
        <button
          type="button"
          onClick={action.onClick}
          className="mt-4 inline-flex items-center gap-2 rounded-xl bg-[#253142] px-4 py-2 text-xs font-semibold text-[#faf7ef] hover:bg-[#33435a] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#277254]"
        >
          {action.icon}
          <span>{action.label}</span>
        </button>
      )}
    </motion.div>
  );
}

