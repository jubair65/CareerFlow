import { useState, useRef } from 'react';
import type { ReactNode } from 'react';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import { MOTION } from './tokens';

interface TooltipProps {
  content: ReactNode;
  children: ReactNode;
  side?: 'top' | 'bottom';
  className?: string;
}

export function Tooltip({
  content,
  children,
  side = 'top',
  className = '',
}: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false);
  const prefersReduced = useReducedMotion();
  const timeoutRef = useRef<number | null>(null);

  const handleMouseEnter = () => {
    timeoutRef.current = window.setTimeout(() => setIsVisible(true), 120);
  };

  const handleMouseLeave = () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    setIsVisible(false);
  };

  return (
    <div
      className="relative inline-flex"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onFocus={() => setIsVisible(true)}
      onBlur={() => setIsVisible(false)}
    >
      {children}
      <AnimatePresence>
        {isVisible && (
          <motion.div
            role="tooltip"
            initial={prefersReduced ? { opacity: 0 } : { opacity: 0, scale: 0.96, y: side === 'top' ? 3 : -3 }}
            animate={prefersReduced ? { opacity: 1 } : { opacity: 1, scale: 1, y: 0 }}
            exit={prefersReduced ? { opacity: 0 } : { opacity: 0, scale: 0.96, y: side === 'top' ? 2 : -2 }}
            transition={{
              duration: prefersReduced ? 0 : MOTION.duration.micro,
              ease: MOTION.easeOutQuint,
            }}
            className={`absolute left-1/2 -translate-x-1/2 z-40 pointer-events-none whitespace-nowrap rounded-lg bg-[#253142] px-2.5 py-1 text-[11px] font-semibold text-[#faf7ef] shadow-md ${
              side === 'top' ? 'bottom-full mb-1.5' : 'top-full mt-1.5'
            } ${className}`}
          >
            {content}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

interface PopoverProps {
  trigger: ReactNode;
  content: ReactNode;
  isOpen: boolean;
  onClose: () => void;
  className?: string;
}

export function Popover({
  trigger,
  content,
  isOpen,
  onClose,
  className = '',
}: PopoverProps) {
  const prefersReduced = useReducedMotion();

  return (
    <div className="relative inline-block">
      {trigger}
      <AnimatePresence>
        {isOpen && (
          <>
            <div className="fixed inset-0 z-30" onClick={onClose} />
            <motion.div
              initial={prefersReduced ? { opacity: 0 } : { opacity: 0, scale: 0.95, y: -4 }}
              animate={prefersReduced ? { opacity: 1 } : { opacity: 1, scale: 1, y: 0 }}
              exit={prefersReduced ? { opacity: 0 } : { opacity: 0, scale: 0.95, y: -4 }}
              transition={{
                duration: prefersReduced ? 0 : MOTION.duration.micro,
                ease: MOTION.easeOutQuint,
              }}
              className={`absolute right-0 top-full mt-2 z-40 rounded-xl bg-[#faf7ef] border border-[#d9dbd1] p-3 shadow-xl ${className}`}
            >
              {content}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}

