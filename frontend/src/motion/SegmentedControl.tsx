import type { ReactNode } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { Check } from 'lucide-react';
import { MOTION } from './tokens';

export interface SegmentOption<T extends string = string> {
  value: T;
  label: string;
  icon?: ReactNode;
}

interface SegmentedControlProps<T extends string = string> {
  options: SegmentOption<T>[];
  value: T;
  onChange: (value: T) => void;
  size?: 'sm' | 'md';
  className?: string;
  id?: string;
}

export function SegmentedControl<T extends string = string>({
  options,
  value,
  onChange,
  size = 'md',
  className = '',
  id = 'segmented-control',
}: SegmentedControlProps<T>) {
  const prefersReduced = useReducedMotion();

  return (
    <div
      role="radiogroup"
      className={`inline-flex items-center rounded-xl bg-[#ede9dd] p-1 ${className}`}
    >
      {options.map((option) => {
        const isSelected = value === option.value;

        return (
          <button
            key={option.value}
            role="radio"
            aria-checked={isSelected}
            type="button"
            onClick={() => onChange(option.value)}
            className={`relative flex items-center justify-center gap-1.5 rounded-lg font-semibold transition-colors duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#277254] ${
              size === 'sm' ? 'px-2.5 py-1 text-xs' : 'px-3 py-1.5 text-xs'
            } ${
              isSelected ? 'text-[#253142]' : 'text-[#687382] hover:text-[#253142]'
            }`}
          >
            {isSelected && (
              <motion.div
                layoutId={prefersReduced ? undefined : `${id}-indicator`}
                transition={{
                  duration: prefersReduced ? 0 : MOTION.duration.micro,
                  ease: MOTION.easeOutQuint,
                }}
                className="absolute inset-0 rounded-lg bg-[#ffffff] shadow-xs"
              />
            )}
            {option.icon && <span className="relative z-10">{option.icon}</span>}
            <span className="relative z-10">{option.label}</span>
          </button>
        );
      })}
    </div>
  );
}

interface ChipProps {
  label: string;
  selected?: boolean;
  onToggle?: () => void;
  variant?: 'status' | 'tag' | 'filter';
  tone?: 'default' | 'green' | 'yellow' | 'navy';
  className?: string;
}

export function Chip({
  label,
  selected = false,
  onToggle,
  variant = 'tag',
  tone = 'default',
  className = '',
}: ChipProps) {
  const prefersReduced = useReducedMotion();

  const toneClasses = {
    default: selected
      ? 'bg-[#253142] text-[#faf7ef] border-[#253142]'
      : 'bg-[#faf7ef] text-[#526072] border-[#d9dbd1] hover:border-[#8d9aab]',
    green: selected
      ? 'bg-[#277254] text-[#faf7ef] border-[#277254]'
      : 'bg-[#eef5f1] text-[#277254] border-[#c0dcd0] hover:border-[#277254]',
    yellow: selected
      ? 'bg-[#f5c84b] text-[#253142] border-[#e8b93c]'
      : 'bg-[#fdfaf1] text-[#785912] border-[#fae5a8] hover:border-[#f5c84b]',
    navy: selected
      ? 'bg-[#253142] text-[#faf7ef] border-[#253142]'
      : 'bg-[#edf0f5] text-[#253142] border-[#c8d1de] hover:border-[#253142]',
  }[tone];

  return (
    <motion.button
      type="button"
      onClick={onToggle}
      whileTap={prefersReduced ? undefined : { scale: 0.97 }}
      className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold transition-colors duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#277254] ${toneClasses} ${className}`}
    >
      {selected && variant === 'filter' && <Check size={12} strokeWidth={2.5} />}
      <span>{label}</span>
    </motion.button>
  );
}

