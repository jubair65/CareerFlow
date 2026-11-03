import { useLocation } from 'wouter';
import { ArrowRight } from 'lucide-react';
import { BRAND } from './motionTokens';
import { MagneticButton } from './shared/MagneticButton';

export function LandingFooter() {
  const [, setLocation] = useLocation();

  return (
    <footer
      className="w-full bg-[#f5f1e6]"
      style={{ backgroundColor: 'var(--cf-landing-light, #f5f1e6)' }}
    >
      {/* Closing CTA */}
      <div className={`py-20 ${BRAND.layout.container}`}>
        <div className="rounded-3xl border border-[#ddd8ca] bg-white p-8 md:p-14 text-center shadow-xs">
          <span className="text-xs font-bold uppercase tracking-wider text-[#7c5e14]">
            Start Without Friction
          </span>
          <h2
            className="cf-display mt-2 text-3xl font-bold leading-tight text-[#253142] md:text-5xl"
            style={{ textWrap: 'balance' }}
          >
            Build your flow today.
          </h2>
          <p
            className="mx-auto mt-4 max-w-[60ch] text-base leading-relaxed text-[#4b5563]"
            style={{ textWrap: 'pretty' }}
          >
            Whether you are practicing for your next interview, standardizing hiring rooms, or scaling an agency pipeline, CareerFlow delivers explainable signals.
          </p>

          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <MagneticButton
              variant="primary"
              onClick={() => setLocation('/register')}
            >
              Start your flow <ArrowRight size={16} />
            </MagneticButton>
            <button
              type="button"
              onClick={() => setLocation('/login')}
              className="inline-flex items-center justify-center gap-2 rounded-xl border border-[#ccd0c6] bg-transparent px-5 py-3 text-sm font-semibold text-[#253142] transition duration-200 hover:border-[#253142] hover:bg-[#ebe6d8] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#253142]"
            >
              Sign in to workspace
            </button>
          </div>
        </div>
      </div>

      {/* Real, Simple Footer */}
      <div className={`border-t border-[#ddd8ca] py-10 ${BRAND.layout.container}`}>
        <div className="flex flex-col items-center justify-between gap-6 md:flex-row">
          <div className="flex items-center gap-2.5" data-testid="brand-careerflow">
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

          <div className="flex items-center gap-6 text-sm text-[#4b5563]">
            <a
              href="#"
              className="transition hover:text-[#253142] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#253142]"
            >
              Privacy
            </a>
            <a
              href="#"
              className="transition hover:text-[#253142] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#253142]"
            >
              Terms
            </a>
            <a
              href="#"
              className="transition hover:text-[#253142] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#253142]"
            >
              Contact
            </a>
          </div>

          <span className="text-sm text-[#4b5563]">© 2026 CareerFlow</span>
        </div>
      </div>
    </footer>
  );
}

