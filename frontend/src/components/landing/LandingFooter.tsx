import { useLocation } from 'wouter';
import { ArrowRight } from 'lucide-react';
import { Logo } from '../brand/Logo';
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
          <Logo tone="color" />

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

