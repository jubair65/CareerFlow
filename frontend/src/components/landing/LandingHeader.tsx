import { useEffect, useState } from 'react';
import { useLocation } from 'wouter';
import { useReducedMotion } from 'framer-motion';
import { ArrowRight } from 'lucide-react';
import { Logo } from '../brand/Logo';
import { BRAND } from './motionTokens';

interface LandingHeaderProps {
  onLogoClick?: () => void;
}

export function LandingHeader({ onLogoClick }: LandingHeaderProps) {
  const [, setLocation] = useLocation();
  const [condensed, setCondensed] = useState(false);
  const prefersReduced = useReducedMotion();

  useEffect(() => {
    const handleScroll = () => {
      setCondensed(window.scrollY > 40);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <>
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-50 focus:rounded-xl focus:bg-[#253142] focus:px-4 focus:py-2.5 focus:text-sm focus:font-semibold focus:text-[#faf7ef] focus:shadow-md focus:outline-none"
      >
        Skip to content
      </a>

      <header
        className={`sticky top-0 z-40 w-full transition-all duration-300 ${
          condensed
            ? 'border-b border-[#ddd8ca]/80 bg-[#f5f1e6]/95 backdrop-blur-md py-3 shadow-xs'
            : 'bg-[#f5f1e6] py-5 border-b border-transparent'
        }`}
      >
        <div className={`flex items-center justify-between ${BRAND.layout.container}`}>
          <Logo animated tone="color" onClick={onLogoClick} className="group" />

          <div className="flex items-center gap-3">
            <button
              onClick={() => setLocation('/login')}
              data-testid="link-login"
              className="rounded-xl px-4 py-2 text-sm font-semibold text-[#4b5563] transition hover:bg-[#e6e1d3] hover:text-[#253142] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#253142]"
            >
              Log in
            </button>
            <button
              onClick={() => setLocation('/register')}
              data-testid="link-register"
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#f5c84b] px-4 py-2.5 text-sm font-semibold text-[#253142] transition duration-200 hover:bg-[#e8b93c] active:bg-[#dbaa2b] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#253142]"
            >
              Create account <ArrowRight size={16} />
            </button>
          </div>
        </div>
      </header>
    </>
  );
}

