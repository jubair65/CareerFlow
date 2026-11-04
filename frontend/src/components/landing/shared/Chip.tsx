import type { ReactNode } from 'react';
import { motion } from 'framer-motion';

interface ChipProps {
  label: string;
  variant?: 'neutral' | 'matched' | 'missing' | 'active' | 'stage';
  icon?: ReactNode;
  onClick?: () => void;
  className?: string;
  layoutId?: string;
}

export function Chip({
  label,
  variant = 'neutral',
  icon,
  onClick,
  className = '',
  layoutId,
}: ChipProps) {
  const styles = {
    neutral:
      'border-[#ddd8ca] bg-white text-[#4b5563] hover:border-[#253142]/40',
    matched:
      'border-[#277254]/30 bg-[#e2f0e9] text-[#277254] font-semibold',
    missing:
      'border-[#e26d5c]/30 bg-[#fdf2f0] text-[#a33d35] font-semibold',
    active:
      'border-[#253142] bg-[#253142] text-[#faf7ef] font-semibold shadow-xs',
    stage:
      'border-[#ddd8ca] bg-[#faf8f3] text-[#253142] hover:bg-[#ece8dc] font-medium',
  }[variant];

  return (
    <motion.button
      type="button"
      layoutId={layoutId}
      onClick={onClick}
      disabled={!onClick}
      className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#253142] disabled:cursor-default ${styles} ${className}`}
    >
      {icon}
      <span>{label}</span>
    </motion.button>
  );
}

