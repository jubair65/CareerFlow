import type { ReactNode } from 'react';
import { useLocation } from 'wouter';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import { Logo } from '../brand/Logo';
import { AuthShowcase } from './AuthShowcase';
import type { AuthShowcaseMode } from './authContent';

interface AuthLayoutProps {
  title: string;
  eyebrow: string;
  subtitle?: string;
  children: ReactNode;
  showcaseMode: AuthShowcaseMode;
  showcaseStep?: number;
  showcaseRole?: 'student' | 'hr' | 'agency';
  backLink?: {
    label: string;
    href: string;
    testId?: string;
  };
}

export function AuthLayout({
  title,
  eyebrow,
  subtitle,
  children,
  showcaseMode,
  showcaseStep = 1,
  showcaseRole = 'student',
  backLink,
}: AuthLayoutProps) {
  const [path, setLocation] = useLocation();
  const prefersReduced = useReducedMotion();

  const handleBack = () => {
    if (backLink) {
      setLocation(backLink.href);
    } else {
      setLocation('/');
    }
  };

  return (
    <div className="flex min-h-[100dvh] w-full flex-col lg:flex-row bg-[#f5f1e6] text-[#253142] m-0 p-0 border-none">
      {/* 
        LEFT PANEL (42% width on desktop >= 1024px)
        - Sticky top 0, height 100dvh on desktop
        - Persists across auth routes without jumping
        - Compact bar on mobile/tablet < 1024px
      */}
      <aside
        data-testid="auth-showcase-panel"
        className="w-full lg:w-[42%] lg:max-w-[580px] shrink-0 bg-[#253142] text-[#faf7ef] lg:sticky lg:top-0 lg:h-[100dvh] flex flex-col justify-between px-6 py-5 sm:px-10 sm:py-8 lg:p-12 z-10"
      >
        {/* Top: Brand Logo */}
        <div className="flex items-center justify-between">
          <button
            type="button"
            onClick={() => setLocation('/')}
            className="focus:outline-hidden focus:ring-2 focus:ring-[#f5c84b]/60 rounded-xl transition cursor-pointer"
          >
            <Logo tone="onDark" />
          </button>

          {/* Mobile Back button visible only < 1024px */}
          <button
            type="button"
            onClick={handleBack}
            data-testid="link-auth-home-mobile"
            className="lg:hidden text-xs font-bold text-[#b7c0cc] hover:text-[#faf7ef] transition focus:outline-hidden focus:ring-2 focus:ring-[#f5c84b]/60 rounded-lg px-2 py-1"
          >
            {backLink?.label || 'Back to home'}
          </button>
        </div>

        {/* Lower-Middle: Animated Message Panel (hidden on mobile < 1024px) */}
        <div className="hidden lg:block my-auto py-8">
          <AuthShowcase
            mode={showcaseMode}
            currentStep={showcaseStep}
            currentRole={showcaseRole}
          />
        </div>

        {/* Bottom: Footer Copyright */}
        <div className="hidden lg:block text-xs font-medium text-[#b7c0cc]">
          <span>&copy; 2026 CareerFlow</span>
        </div>
      </aside>

      {/* 
        RIGHT PANEL (58% width on desktop >= 1024px)
        - Independent scrolling with scrollbar-gutter: stable
        - Top-aligned form container with padding-top: clamp(96px, 16vh, 160px)
        - Identical layout geometry across all auth routes
      */}
      <main className="flex-1 min-h-[100dvh] relative flex flex-col bg-[#f5f1e6] overflow-y-auto [scrollbar-gutter:stable]">
        {/* Top Navigation Bar: Back to Home / Back to Login */}
        <div className="absolute top-0 right-0 left-0 h-16 sm:h-20 flex items-center justify-end px-6 sm:px-10 lg:px-14 z-10">
          <button
            type="button"
            onClick={handleBack}
            data-testid={backLink?.testId || 'link-auth-home'}
            className="hidden lg:inline-flex items-center gap-1.5 text-xs sm:text-sm font-bold text-[#33435a] hover:text-[#253142] transition focus:outline-hidden focus:ring-2 focus:ring-[#277254]/40 rounded-lg px-2.5 py-1.5 cursor-pointer"
          >
            {backLink?.label || 'Back to home'}
          </button>
        </div>

        {/* 
          Form Area Container
          - Top-aligned with identical padding-top clamp across all auth routes
          - Single <h1> on the right only
        */}
        <div
          data-testid="auth-content-container"
          className="w-full max-w-[440px] mx-auto px-5 sm:px-8 pb-10 pt-[clamp(80px,13vh,140px)] lg:pt-[clamp(96px,16vh,160px)]"
        >
          <AnimatePresence mode="wait">
            <motion.div
              key={path}
              initial={prefersReduced ? { opacity: 0 } : { opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={prefersReduced ? { opacity: 0 } : { opacity: 0, y: -8 }}
              transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
              className="w-full"
            >
              {/* Header block with single <h1> and right-side eyebrow */}
              <div className="mb-6 sm:mb-7">
                <div
                  data-testid="auth-eyebrow"
                  className="mb-2 text-[11px] font-bold uppercase tracking-[.18em] text-[#9a7922]"
                >
                  {eyebrow}
                </div>
                <h1
                  data-testid="auth-page-title"
                  className="cf-display text-3xl sm:text-4xl font-bold text-[#253142] tracking-tight"
                >
                  {title}
                </h1>
                {subtitle && (
                  <p className="mt-2 text-xs sm:text-sm text-[#657081] leading-relaxed">
                    {subtitle}
                  </p>
                )}
              </div>

              {/* Form Content */}
              {children}
            </motion.div>
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}

