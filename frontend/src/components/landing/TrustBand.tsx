import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ShieldCheck, LockKeyhole, Info, CheckCircle2, ArrowRight } from 'lucide-react';
import { BRAND, MOTION } from './motionTokens';

export function TrustBand() {
  const [isInspecting, setIsInspecting] = useState(false);

  return (
    <section
      aria-labelledby="trust-heading"
      className="w-full border-t border-[#ddd8ca] bg-[#f5f1e6] py-20"
      style={{ backgroundColor: 'var(--cf-landing-light, #f5f1e6)' }}
    >
      <div className={`${BRAND.layout.container}`}>
        <div className="mb-10 max-w-2xl">
          <div className="mb-3 flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#7c5e14]">
            <ShieldCheck size={16} /> Architectural Principles
          </div>
          <h2
            id="trust-heading"
            className="cf-display text-3xl font-bold leading-tight text-[#253142] md:text-5xl"
            style={{ textWrap: 'balance' }}
          >
            Explainable scores. Private by default.
          </h2>
          <p
            className="mt-4 max-w-[60ch] text-base leading-relaxed text-[#4b5563]"
            style={{ textWrap: 'pretty' }}
          >
            We reject black-box hiring evaluations. Every score is fully traceable to concrete rubrics, and candidate data is strictly shielded.
          </p>
        </div>

        {/* 2 Interactive Cards */}
        <div className="grid grid-cols-1 gap-8 md:grid-cols-2 md:items-start">
          {/* Card 1: Interactive Explainable Score Explainer */}
          <div
            onMouseEnter={() => setIsInspecting(true)}
            onMouseLeave={() => setIsInspecting(false)}
            onClick={() => setIsInspecting(!isInspecting)}
            className="group cursor-pointer rounded-2xl border border-[#ddd8ca] bg-white p-6 shadow-xs transition-all duration-200 hover:border-[#253142]"
          >
            <div className="flex items-center justify-between border-b border-[#ddd8ca]/70 pb-4">
              <div className="flex items-center gap-2.5">
                <div className="grid h-8 w-8 place-items-center rounded-lg bg-[#e2f0e9] text-[#277254]">
                  <ShieldCheck size={18} />
                </div>
                <h3 className="font-bold text-[#253142]">Explainable Score Architecture</h3>
              </div>
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-[#7c5e14]">
                <Info size={13} /> {isInspecting ? 'Inspecting' : 'Hover to inspect'}
              </span>
            </div>

            <div className="mt-5 flex items-center justify-between">
              <div>
                <span className="text-xs text-[#4b5563]">Verified Composite Score</span>
                <div className="cf-display text-4xl font-bold text-[#253142]">
                  88<span className="text-xl font-normal text-[#4b5563]">/100</span>
                </div>
                <div className="text-xs font-semibold text-[#277254]">Senior Full Stack Engineer</div>
              </div>
              <div className="rounded-xl border border-[#ddd8ca] bg-[#faf8f3] px-3.5 py-2 text-right">
                <div className="text-[10px] uppercase font-bold text-[#4b5563]">Signal Confidence</div>
                <div className="text-sm font-bold text-[#253142]">99.4% Match</div>
              </div>
            </div>

            {/* Inspectable Formula Breakdown */}
            <AnimatePresence>
              {isInspecting ? (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: MOTION.duration.component, ease: MOTION.easeOutQuint }}
                  className="mt-5 space-y-3 border-t border-[#ddd8ca]/70 pt-4 overflow-hidden"
                >
                  <div className="rounded-lg bg-[#faf8f3] p-3 text-xs text-[#253142] font-mono leading-relaxed">
                    Score = (0.50 × CV Semantic) + (0.50 × Delivery Signals)
                    <br />
                    Score = (0.50 × 92) + (0.50 × 84) = <strong className="text-[#277254]">88.0</strong>
                  </div>

                  <div className="space-y-1.5 text-xs text-[#4b5563]">
                    <div className="flex justify-between">
                      <span>• CV Semantic Vector Match (Embeddings cosine):</span>
                      <strong className="text-[#253142]">92%</strong>
                    </div>
                    <div className="flex justify-between">
                      <span>• Technical Keyword Coverage (Verified skills):</span>
                      <strong className="text-[#253142]">95%</strong>
                    </div>
                    <div className="flex justify-between">
                      <span>• Delivery & Speech Metrics (Pace 138 WPM):</span>
                      <strong className="text-[#253142]">84%</strong>
                    </div>
                  </div>

                  <p className="text-[11px] text-[#277254] font-medium pt-1">
                    ✓ Full mathematical transparency. Zero arbitrary AI hallucinations.
                  </p>
                </motion.div>
              ) : (
                <div className="mt-5 border-t border-[#ddd8ca]/70 pt-4 text-xs text-[#4b5563] flex items-center justify-between">
                  <span>Hover or tap to reveal the transparent signal formula.</span>
                  <ArrowRight size={14} className="text-[#7c5e14] group-hover:translate-x-1 transition-transform" />
                </div>
              )}
            </AnimatePresence>
          </div>

          {/* Card 2: Private By Default Architecture */}
          <div className="rounded-2xl border border-[#ddd8ca] bg-white p-6 shadow-xs">
            <div className="flex items-center gap-2.5 border-b border-[#ddd8ca]/70 pb-4">
              <div className="grid h-8 w-8 place-items-center rounded-lg bg-[#faf8f3] text-[#253142] border border-[#ddd8ca]">
                <LockKeyhole size={18} />
              </div>
              <h3 className="font-bold text-[#253142]">Private by Default Protection</h3>
            </div>

            <div className="mt-5 space-y-4 text-xs text-[#4b5563] leading-relaxed">
              <div className="flex items-start gap-2.5">
                <CheckCircle2 size={16} className="text-[#277254] shrink-0 mt-0.5" />
                <div>
                  <strong className="text-[#253142]">Zero Foundation LLM Training:</strong> Your resumes, practice takes, and interview recordings are strictly isolated. We never license or pipe candidate data into external AI model training.
                </div>
              </div>

              <div className="flex items-start gap-2.5">
                <CheckCircle2 size={16} className="text-[#277254] shrink-0 mt-0.5" />
                <div>
                  <strong className="text-[#253142]">Role-Scoped Sandboxing:</strong> Hiring teams only view applicants within their designated recruitment room. Cross-tenant queries are blocked at the application boundary.
                </div>
              </div>

              <div className="flex items-start gap-2.5">
                <CheckCircle2 size={16} className="text-[#277254] shrink-0 mt-0.5" />
                <div>
                  <strong className="text-[#253142]">Encrypted Storage & Audit Trails:</strong> Sensitive artifacts are stored with cryptographic access policies and logged for enterprise compliance.
                </div>
              </div>
            </div>

            <div className="mt-6 border-t border-[#ddd8ca]/70 pt-4 flex items-center justify-between text-xs font-semibold text-[#277254]">
              <span>ISO & GDPR-aligned access controls</span>
              <span className="rounded-md bg-[#e2f0e9] px-2 py-0.5 text-[10px]">Active</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
