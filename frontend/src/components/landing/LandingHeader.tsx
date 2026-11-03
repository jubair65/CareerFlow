import { useEffect, useState } from 'react';
import { useLocation } from 'wouter';
import { ArrowRight } from 'lucide-react';
import { BRAND } from './motionTokens';

interface LandingHeaderProps {
  onLogoClick?: () => void;
}

export function LandingHeader({ onLogoClick }: LandingHeaderProps) {
  const [, setLocation] = useLocation();
  const [condensed, setCondensed] = useState(false);

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
          <div
            onClick={onLogoClick}
            className="flex items-center gap-2.5 cursor-pointer"
            data-testid="brand-careerflow"
          >
            <div className="grid h-9 w-9 place-items-center rounded-xl bg-[#253142] text-[#f5c84b]">
              <svg viewBox="0 0 24 24" className="h-[21px] w-[21px]" fill="none" aria-hidden="true">
                <path
                  d="M4 6.5h5.25c1.52 0 2.75 1.23 2.75 2.75v5.5c0 1.52 1.23 2.75 2.75 2.75H20"
                  stroke="currentColor"
                  strokeWidth="1.8"
                  strokeLinecap="round"
                />
                <path
                  d="m17.2 14.75 2.8 2.75-2.8 2.75"
                  stroke="currentColor"
                  strokeWidth="1.8"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                <circle cx="4" cy="6.5" r="1.55" fill="currentColor" />
                <circle cx="12" cy="9.25" r="1.55" fill="currentColor" />
              </svg>
            </div>
            <span className="cf-display text-lg font-bold text-[#253142]">CareerFlow</span>
          </div>

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

