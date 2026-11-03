import { useState, useEffect } from 'react';
import { useLocation } from 'wouter';
import { ArrowRight, CheckCircle2 } from 'lucide-react';
import { motion } from 'framer-motion';
import { BRAND, MOTION } from './motionTokens';
import { MaskWordReveal } from './shared/Reveal';
import { ScoreCounter } from './shared/ScoreCounter';
import { MagneticButton } from './shared/MagneticButton';

export function LandingHero() {
  const [, setLocation] = useLocation();
  const [showSubScores, setShowSubScores] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setShowSubScores(true);
    }, 400);
    return () => clearTimeout(timer);
  }, []);

  const subScores = [
    { label: 'Keywords', score: 80, color: '#277254', delay: 0.1 },
    { label: 'Clarity and Metrics', score: 72, color: '#f5c84b', delay: 0.25 },
    { label: 'Structure', score: 78, color: '#253142', delay: 0.4 },
    { label: 'Work and Education', score: 68, color: '#4b5563', delay: 0.55 },
  ];

  return (
    <section aria-labelledby="hero-heading" className="w-full py-24 md:py-28">
      <div className={`grid grid-cols-1 items-center gap-16 md:grid-cols-2 ${BRAND.layout.container}`}>
        <div>
          <h1
            id="hero-heading"
            className="cf-display text-5xl font-bold leading-[1.05] text-[#253142] md:text-6xl lg:text-7xl"
            style={{ textWrap: 'balance' }}
          >
            <MaskWordReveal text="Prepare better." delay={0.05} />
            <br />
            <MaskWordReveal text="Apply smarter." delay={0.25} />
            <br />
            <MaskWordReveal text="Hire faster." delay={0.45} />
          </h1>

          <p
            className="mt-6 max-w-[60ch] text-lg leading-relaxed text-[#4b5563]"
            style={{ textWrap: 'pretty' }}
          >
            CareerFlow brings candidates, hiring teams, and recruitment agencies into one focused workspace. Practice interviews, get CV feedback you can act on, and track your progress.
          </p>

          <div className="mt-8 flex flex-wrap items-center gap-3">
            <MagneticButton
              variant="primary"
              onClick={() => setLocation('/register')}
              testId="button-landing-start"
            >
              Start your flow <ArrowRight size={16} />
            </MagneticButton>
            <button
              type="button"
              onClick={() => setLocation('/login')}
              data-testid="button-landing-demo"
              className="inline-flex items-center justify-center gap-2 rounded-xl border border-[#ccd0c6] bg-transparent px-5 py-3 text-sm font-semibold text-[#253142] transition duration-200 hover:border-[#253142] hover:bg-[#ebe6d8] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#253142]"
            >
              Explore the demo
            </button>
          </div>

          <p className="mt-8 text-sm text-[#4b5563]">
            Explainable scoring algorithms and private by default data protection.
          </p>
        </div>

        {/* Real Product Card: CV Score 0 to 74 with 4 Sequenced Sub-Scores */}
        <div>
          <div className="rounded-2xl border border-[#ddd8ca] bg-white p-7 shadow-xs transition-shadow">
            <div className="flex items-center justify-between border-b border-[#ddd8ca]/70 pb-4">
              <div>
                <span className="text-[11px] font-bold uppercase tracking-wider text-[#7c5e14]">
                  CV Studio Evaluation
                </span>
                <h3 className="cf-display text-lg font-bold text-[#253142]">
                  Composite CV Score
                </h3>
              </div>
              <span className="inline-flex items-center gap-1.5 rounded-lg bg-[#e2f0e9] px-2.5 py-1 text-xs font-semibold text-[#277254]">
                <CheckCircle2 size={13} /> Active profile
              </span>
            </div>

            <div className="mt-6 flex items-center justify-between gap-6">
              <div>
                <div className="text-xs font-medium text-[#4b5563]">Readiness Score</div>
                <div className="cf-display mt-0.5 text-5xl font-bold text-[#253142]">
                  <ScoreCounter value={74} duration={1400} delay={150} />
                  <span className="text-2xl font-normal text-[#4b5563]">/100</span>
                </div>
                <div className="mt-1 text-xs font-medium text-[#277254]">
                  Solid baseline across 4 evaluation categories
                </div>
              </div>

              {/* Progress ring driven by 74% */}
              <div className="relative flex h-24 w-24 flex-shrink-0 items-center justify-center">
                <svg className="h-full w-full -rotate-90" viewBox="0 0 80 80" aria-hidden="true">
                  <circle cx="40" cy="40" r="32" stroke="#e9e6dc" strokeWidth="8" fill="none" />
                  <motion.circle
                    cx="40"
                    cy="40"
                    r="32"
                    stroke="#f5c84b"
                    strokeWidth="8"
                    fill="none"
                    strokeDasharray={201.06}
                    initial={{ strokeDashoffset: 201.06 }}
                    animate={{ strokeDashoffset: 201.06 * (1 - 0.74) }}
                    transition={{ duration: 1.4, ease: MOTION.easeOutQuint, delay: 0.15 }}
                    strokeLinecap="round"
                  />
                </svg>
                <div className="absolute text-center">
                  <span className="text-sm font-bold text-[#253142]">
                    <ScoreCounter value={74} duration={1400} delay={150} suffix="%" />
                  </span>
                </div>
              </div>
            </div>

            {/* 4 Sequenced Sub-Scores */}
            <div className="mt-6 space-y-3.5 border-t border-[#ddd8ca]/70 pt-5">
              {subScores.map((sub) => (
                <div key={sub.label}>
                  <div className="flex justify-between text-xs font-medium">
                    <span className="text-[#253142]">{sub.label}</span>
                    <span className="font-bold text-[#253142]">{sub.score}%</span>
                  </div>
                  <div className="mt-1.5 h-2 w-full overflow-hidden rounded-full bg-[#e9e6dc]">
                    <motion.div
                      className="h-full rounded-full"
                      style={{ backgroundColor: sub.color }}
                      initial={{ width: 0 }}
                      animate={showSubScores ? { width: `${sub.score}%` } : { width: 0 }}
                      transition={{
                        duration: MOTION.duration.section,
                        ease: MOTION.easeOutQuint,
                        delay: sub.delay,
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

