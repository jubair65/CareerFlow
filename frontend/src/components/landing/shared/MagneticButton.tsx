import { useRef, useState, useEffect } from 'react';
import type { ReactNode, MouseEvent } from 'react';
import { motion } from 'framer-motion';

interface MagneticButtonProps {
  children: ReactNode;
  onClick?: () => void;
  className?: string;
  testId?: string;
  variant?: 'primary' | 'secondary' | 'darkPrimary';
  disabled?: boolean;
}

export function MagneticButton({
  children,
  onClick,
  className = '',
  testId,
  variant = 'primary',
  disabled = false,
}: MagneticButtonProps) {
  const ref = useRef<HTMLButtonElement>(null);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isTouchOrReduced, setIsTouchOrReduced] = useState(false);

  useEffect(() => {
    const isTouch = window.matchMedia('(pointer: coarse)').matches;
    const isReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    setIsTouchOrReduced(isTouch || isReduced);
  }, []);

  const handleMouseMove = (e: MouseEvent<HTMLButtonElement>) => {
    if (isTouchOrReduced || disabled || !ref.current) return;
    const { clientX, clientY } = e;
    const { left, top, width, height } = ref.current.getBoundingClientRect();
    const centerX = left + width / 2;
    const centerY = top + height / 2;
    // Max 5px subtle magnetic pull
    const pullFactor = 0.12;
    const x = Math.max(-5, Math.min(5, (clientX - centerX) * pullFactor));
    const y = Math.max(-5, Math.min(5, (clientY - centerY) * pullFactor));
    setPosition({ x, y });
  };

  const handleMouseLeave = () => {
    setPosition({ x: 0, y: 0 });
  };

  const variantStyles = {
    primary:
      'bg-[#f5c84b] text-[#253142] hover:bg-[#e8b93c] active:bg-[#dbaa2b] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#253142]',
    secondary:
      'border border-[#ccd0c6] bg-transparent text-[#253142] hover:border-[#253142] hover:bg-[#ebe6d8] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#253142]',
    darkPrimary:
      'bg-[#f5c84b] text-[#253142] hover:bg-[#ffd969] active:bg-[#e8b93c] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#faf7ef]',
  }[variant];

  return (
    <motion.button
      ref={ref}
      type="button"
      onClick={onClick}
      disabled={disabled}
      data-testid={testId}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      animate={{ x: position.x, y: position.y }}
      transition={{ type: 'spring', stiffness: 350, damping: 25, mass: 0.5 }}
      className={`inline-flex items-center justify-center gap-2 rounded-xl px-5 py-3 text-sm font-semibold transition-colors duration-200 disabled:cursor-not-allowed disabled:opacity-50 ${variantStyles} ${className}`}
    >
      {children}
    </motion.button>
  );
}

