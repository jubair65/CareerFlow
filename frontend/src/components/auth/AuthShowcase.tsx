import { useState, useEffect, useRef, useMemo } from 'react';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import {
  LOGIN_MESSAGES,
  REGISTER_ROLE_MESSAGES,
  FORGOT_STEP_MESSAGES,
  type AuthShowcaseMode,
  type ShowcaseMessage,
} from './authContent';

interface AuthShowcaseProps {
  mode: AuthShowcaseMode;
  currentStep?: number; // 1, 2, or 3 for 'stepped' mode
  currentRole?: 'student' | 'hr' | 'agency'; // for 'role' mode
}

const DURATION_MS = 6000;

export function AuthShowcase({
  mode,
  currentStep = 1,
  currentRole = 'student',
}: AuthShowcaseProps) {
  const prefersReduced = useReducedMotion();
  const isFirstMount = useRef(true);

  // Messages array based on mode
  const messages: ShowcaseMessage[] = useMemo(() => {
    if (mode === 'timed') {
      return LOGIN_MESSAGES;
    }
    if (mode === 'role') {
      return REGISTER_ROLE_MESSAGES[currentRole] || REGISTER_ROLE_MESSAGES.student;
    }
    if (mode === 'stepped') {
      return [
        FORGOT_STEP_MESSAGES[1],
        FORGOT_STEP_MESSAGES[2],
        FORGOT_STEP_MESSAGES[3],
      ];
    }
    return LOGIN_MESSAGES;
  }, [mode, currentRole]);

  // Current active index
  const [currentIndex, setCurrentIndex] = useState(() => {
    if (mode === 'stepped') {
      return Math.max(0, Math.min(2, currentStep - 1));
    }
    return 0;
  });

  // Track progress (0 to 1) for the active bar
  const [progress, setProgress] = useState(0);

  // Hover and focus pause state
  const [isHovered, setIsHovered] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  const [isTabHidden, setIsTabHidden] = useState(false);

  // Sync stepped mode directly
  useEffect(() => {
    if (mode === 'stepped') {
      const idx = Math.max(0, Math.min(messages.length - 1, currentStep - 1));
      setCurrentIndex(idx);
      setProgress(1);
    }
  }, [mode, currentStep, messages.length]);

  // Reset to first slide when role changes in 'role' mode
  const prevRoleRef = useRef(currentRole);
  useEffect(() => {
    if (mode === 'role' && prevRoleRef.current !== currentRole) {
      prevRoleRef.current = currentRole;
      setCurrentIndex(0);
      setProgress(0);
    }
  }, [mode, currentRole]);

  // Track visibility change (tab hidden)
  useEffect(() => {
    const handleVisibilityChange = () => {
      setIsTabHidden(document.visibilityState === 'hidden');
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, []);

  // Whether the carousel is actively paused
  const isPaused =
    mode === 'stepped' ||
    prefersReduced ||
    isHovered ||
    isFocused ||
    isTabHidden;

  // Timer loop for auto-rotation
  useEffect(() => {
    if (mode === 'stepped' || prefersReduced) return;

    let animFrame: number;
    let lastTime = performance.now();

    const tick = (now: number) => {
      const delta = now - lastTime;
      lastTime = now;

      if (!isPaused) {
        setProgress((prev) => {
          const next = prev + delta / DURATION_MS;
          if (next >= 1) {
            setCurrentIndex((curr) => (curr + 1) % messages.length);
            return 0;
          }
          return next;
        });
      }

      animFrame = requestAnimationFrame(tick);
    };

    animFrame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(animFrame);
  }, [mode, prefersReduced, isPaused, messages.length]);

  // Clear first mount flag after initial render
  useEffect(() => {
    const timer = setTimeout(() => {
      isFirstMount.current = false;
    }, 100);
    return () => clearTimeout(timer);
  }, []);

  const handleSelectSlide = (index: number) => {
    if (mode === 'stepped') return;
    setCurrentIndex(index);
    setProgress(0);
  };

  const currentMessage = messages[currentIndex] || messages[0];

  return (
    <div
      role="region"
      aria-roledescription="carousel"
      aria-label="Product highlights"
      aria-live={isPaused ? 'polite' : 'off'}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onFocus={() => setIsFocused(true)}
      onBlur={() => setIsFocused(false)}
      className="w-full max-w-md select-none"
    >
      {/* Messages stack in single CSS Grid cell for ZERO layout shift (CLS = 0) */}
      <div className="grid grid-cols-1 grid-rows-1 relative min-w-0">
        {/* Invisible sizer stack holding layout height to the tallest item */}
        {messages.map((msg, i) => (
          <div
            key={`sizer-${i}`}
            aria-hidden="true"
            className="col-start-1 row-start-1 invisible pointer-events-none select-none pb-2"
          >
            <p className="cf-display text-2xl sm:text-3xl lg:text-[2rem] font-bold leading-tight text-transparent">
              {msg.headline}
            </p>
            <p className="mt-3 text-sm leading-relaxed text-transparent">
              {msg.support}
            </p>
          </div>
        ))}

        {/* Active message cross-fade / slide */}
        <div className="col-start-1 row-start-1">
          <AnimatePresence mode="wait">
            <motion.div
              key={`${mode}-${currentRole}-${currentIndex}`}
              initial={
                isFirstMount.current || prefersReduced
                  ? { opacity: 1, y: 0 }
                  : { opacity: 0, y: 16 }
              }
              animate={{ opacity: 1, y: 0 }}
              exit={
                prefersReduced
                  ? { opacity: 0 }
                  : { opacity: 0, y: -12 }
              }
              transition={
                prefersReduced
                  ? { duration: 0.2 }
                  : {
                      opacity: { duration: 0.6, ease: [0.22, 1, 0.36, 1] },
                      y: { duration: 0.6, ease: [0.22, 1, 0.36, 1] },
                    }
              }
              className="min-w-0"
            >
              <p
                data-testid="showcase-headline"
                className="cf-display text-2xl sm:text-3xl lg:text-[2rem] font-bold leading-tight text-[#faf7ef]"
              >
                {currentMessage.headline}
              </p>
              <motion.p
                data-testid="showcase-support"
                initial={
                  isFirstMount.current || prefersReduced
                    ? { opacity: 1, y: 0 }
                    : { opacity: 0, y: 16 }
                }
                animate={{ opacity: 1, y: 0 }}
                transition={
                  prefersReduced
                    ? { duration: 0.2 }
                    : {
                        duration: 0.6,
                        delay: isFirstMount.current ? 0 : 0.08,
                        ease: [0.22, 1, 0.36, 1],
                      }
                }
                className="mt-3 text-sm leading-relaxed text-[#b7c0cc]"
              >
                {currentMessage.support}
              </motion.p>
            </motion.div>
          </AnimatePresence>
        </div>
      </div>

      {/* Indicators and Pause / Play Button */}
      <div className="mt-7 flex items-center gap-3">
        <div className="flex items-center gap-2">
          {messages.map((_, idx) => {
            const isActive = idx === currentIndex;
            const isCompleted = idx < currentIndex;

            return (
              <button
                key={`indicator-${idx}`}
                type="button"
                onClick={() => handleSelectSlide(idx)}
                aria-label={`Show message ${idx + 1} of ${messages.length}`}
                aria-current={isActive ? 'true' : undefined}
                data-testid={`showcase-indicator-${idx}`}
                className="group relative h-1.5 rounded-full bg-[#354255] transition-all overflow-hidden focus:outline-hidden focus:ring-2 focus:ring-[#f5c84b]/60 cursor-pointer"
                style={{
                  width: isActive ? '36px' : '16px',
                }}
              >
                {/* Active bar fill */}
                {isActive && (
                  <span
                    className="absolute inset-0 bg-[#f5c84b] origin-left rounded-full transition-transform"
                    style={{
                      transform:
                        mode === 'stepped' || prefersReduced
                          ? 'scaleX(1)'
                          : `scaleX(${progress})`,
                    }}
                  />
                )}
                {/* Completed bar */}
                {isCompleted && (
                  <span className="absolute inset-0 bg-[#f5c84b]/50 rounded-full" />
                )}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

