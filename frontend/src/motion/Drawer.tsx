import { useEffect, useRef } from 'react';
import type { ReactNode } from 'react';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import { X } from 'lucide-react';
import { MOTION } from './tokens';

interface DrawerProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  description?: string;
  children: ReactNode;
  width?: string; // e.g. 'max-w-md' or 'max-w-xl'
  side?: 'right' | 'left';
}

export function Drawer({
  isOpen,
  onClose,
  title,
  description,
  children,
  width = 'max-w-lg',
  side = 'right',
}: DrawerProps) {
  const prefersReduced = useReducedMotion();
  const triggerRef = useRef<Element | null>(null);
  const drawerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (isOpen) {
      triggerRef.current = document.activeElement;
      // Focus drawer container on open
      setTimeout(() => {
        const firstFocusable = drawerRef.current?.querySelector<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        firstFocusable?.focus();
      }, 50);

      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === 'Escape') {
          e.preventDefault();
          onClose();
        }
      };
      window.addEventListener('keydown', handleKeyDown);
      return () => window.removeEventListener('keydown', handleKeyDown);
    } else {
      if (triggerRef.current instanceof HTMLElement) {
        triggerRef.current.focus();
      }
    }
  }, [isOpen, onClose]);

  const slideInitial = side === 'right' ? { x: '100%' } : { x: '-100%' };
  const slideExit = side === 'right' ? { x: '100%' } : { x: '-100%' };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 overflow-hidden" role="dialog" aria-modal="true">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: prefersReduced ? 0 : MOTION.duration.micro }}
            onClick={onClose}
            className="fixed inset-0 bg-[#253142]/40 backdrop-blur-[2px]"
          />

          {/* Drawer Content */}
          <div className={`fixed inset-y-0 ${side === 'right' ? 'right-0' : 'left-0'} flex max-w-full`}>
            <motion.div
              ref={drawerRef}
              initial={prefersReduced ? { opacity: 0 } : { ...slideInitial, opacity: 0.95 }}
              animate={prefersReduced ? { opacity: 1 } : { x: 0, opacity: 1 }}
              exit={prefersReduced ? { opacity: 0 } : slideExit}
              transition={{
                duration: prefersReduced ? 0 : MOTION.duration.component,
                ease: MOTION.easeOutQuint,
              }}
              className={`w-screen ${width} bg-[#faf7ef] border-l border-[#d9dbd1] shadow-2xl flex flex-col h-full overflow-hidden`}
            >
              {/* Header */}
              <div className="flex items-center justify-between border-b border-[#e5e3d8] px-6 py-4 bg-[#f5f1e6]">
                <div>
                  {title && <h3 className="cf-display text-lg font-bold text-[#253142]">{title}</h3>}
                  {description && <p className="text-xs text-[#687382] mt-0.5">{description}</p>}
                </div>
                <button
                  type="button"
                  onClick={onClose}
                  aria-label="Close drawer"
                  className="rounded-lg p-1.5 text-[#687382] hover:bg-[#eae6db] hover:text-[#253142] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#277254]"
                >
                  <X size={18} />
                </button>
              </div>

              {/* Body */}
              <div className="flex-1 overflow-y-auto p-6">{children}</div>
            </motion.div>
          </div>
        </div>
      )}
    </AnimatePresence>
  );
}

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  description?: string;
  children: ReactNode;
  maxWidth?: string; // e.g. 'max-w-md', 'max-w-lg'
}

export function Modal({
  isOpen,
  onClose,
  title,
  description,
  children,
  maxWidth = 'max-w-lg',
}: ModalProps) {
  const prefersReduced = useReducedMotion();
  const triggerRef = useRef<Element | null>(null);
  const modalRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (isOpen) {
      triggerRef.current = document.activeElement;
      setTimeout(() => {
        const firstFocusable = modalRef.current?.querySelector<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        firstFocusable?.focus();
      }, 50);

      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === 'Escape') {
          e.preventDefault();
          onClose();
        }
      };
      window.addEventListener('keydown', handleKeyDown);
      return () => window.removeEventListener('keydown', handleKeyDown);
    } else {
      if (triggerRef.current instanceof HTMLElement) {
        triggerRef.current.focus();
      }
    }
  }, [isOpen, onClose]);

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" role="dialog" aria-modal="true">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: prefersReduced ? 0 : MOTION.duration.micro }}
            onClick={onClose}
            className="fixed inset-0 bg-[#253142]/45 backdrop-blur-[2px]"
          />

          {/* Modal Card */}
          <motion.div
            ref={modalRef}
            initial={prefersReduced ? { opacity: 0 } : { opacity: 0, scale: 0.96, y: 8 }}
            animate={prefersReduced ? { opacity: 1 } : { opacity: 1, scale: 1, y: 0 }}
            exit={prefersReduced ? { opacity: 0 } : { opacity: 0, scale: 0.96, y: 8 }}
            transition={{
              duration: prefersReduced ? 0 : MOTION.duration.component,
              ease: MOTION.easeOutQuint,
            }}
            className={`relative z-10 w-full ${maxWidth} rounded-2xl bg-[#faf7ef] border border-[#d9dbd1] shadow-2xl overflow-hidden`}
          >
            {/* Header */}
            <div className="flex items-center justify-between border-b border-[#e5e3d8] px-6 py-4 bg-[#f5f1e6]">
              <div>
                {title && <h3 className="cf-display text-lg font-bold text-[#253142]">{title}</h3>}
                {description && <p className="text-xs text-[#687382] mt-0.5">{description}</p>}
              </div>
              <button
                type="button"
                onClick={onClose}
                aria-label="Close modal"
                className="rounded-lg p-1.5 text-[#687382] hover:bg-[#eae6db] hover:text-[#253142] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#277254]"
              >
                <X size={18} />
              </button>
            </div>

            {/* Content */}
            <div className="p-6">{children}</div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}

