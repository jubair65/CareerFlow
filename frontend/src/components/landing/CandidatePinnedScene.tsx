import { useEffect, useRef, useState } from 'react';
import { useLocation } from 'wouter';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { Check, Plus, ArrowRight, Sparkles, FileText, CheckCircle2 } from 'lucide-react';
import { BRAND } from './motionTokens';
import { Chip } from './shared/Chip';

gsap.registerPlugin(ScrollTrigger);

export function CandidatePinnedScene() {
  const [, setLocation] = useLocation();
  const sectionRef = useRef<HTMLElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const [activeStage, setActiveStage] = useState(0); // 0, 1, 2
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < 768 || window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      setIsMobile(mobile);
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  useEffect(() => {
    if (isMobile) return;

    const ctx = gsap.context(() => {
      ScrollTrigger.create({
        trigger: sectionRef.current,
        start: 'top top',
        end: '+=1200',
        pin: true,
        scrub: 0.5,
        onUpdate: (self) => {
          const progress = self.progress;
          if (progress < 0.35) {
            setActiveStage(0);
          } else if (progress < 0.7) {
            setActiveStage(1);
          } else {
            setActiveStage(2);
          }
        },
      });
    }, sectionRef);

    return () => ctx.revert();
  }, [isMobile]);

  // Dynamic states per stage
  const stageData = [
    {
      score: 58,
      statusLabel: 'Needs keyword match',
      statusColor: '#a33d35',
      matchedCount: 0,
      skills: [
        { label: 'Design Systems', state: 'missing' },
        { label: 'Figma Variables', state: 'missing' },
        { label: 'WCAG 2.1 A11y', state: 'missing' },
        { label: 'Cross-functional Collab', state: 'missing' },
      ],
      keywordsActive: false,
    },
    {
      score: 72,
      statusLabel: 'Keywords partially aligned',
      statusColor: '#9a7922',
      matchedCount: 2,
      skills: [
        { label: 'Design Systems', state: 'matched' },
        { label: 'Figma Variables', state: 'matched' },
        { label: 'WCAG 2.1 A11y', state: 'missing' },
        { label: 'Cross-functional Collab', state: 'missing' },
      ],
      keywordsActive: true,
    },
    {
      score: 87,
      statusLabel: 'Strong semantic match',
      statusColor: '#277254',
      matchedCount: 4,
      skills: [
        { label: 'Design Systems', state: 'matched' },
        { label: 'Figma Variables', state: 'matched' },
        { label: 'WCAG 2.1 A11y', state: 'matched' },
        { label: 'Cross-functional Collab', state: 'matched' },
      ],
      keywordsActive: true,
    },
  ];

  const current = stageData[activeStage];

  const steps = [
    {
      title: 'Raw CV ingestion and benchmark',
      description:
        'CareerFlow scans your resume against verified industry competency models, establishing a baseline score across four structured dimensions.',
    },
    {
      title: 'Semantic keyword alignment',
      description:
        'Contextual phrase matching detects evidence of technical depth and product impact, highlighting where keywords snap into place.',
    },
    {
      title: 'Verified candidate signal',
      description:
        'Missing skill requirements are turned into matched competencies with actionable feedback, increasing your readiness score to 87/100.',
    },
  ];

  return (
    <section
      ref={sectionRef}
      aria-labelledby="candidates-heading"
      className="relative w-full border-t border-[#ddd8ca] bg-[#f5f1e6] py-16 md:py-24"
      style={{ backgroundColor: 'var(--cf-landing-light, #f5f1e6)' }}
    >
      <div ref={containerRef} className={`${BRAND.layout.container}`}>
        {/* Section Header */}
        <div className="mb-10 max-w-2xl">
          <div className="mb-3 flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#7c5e14]">
            <Sparkles size={16} /> For candidates
          </div>
          <h2
            id="candidates-heading"
            className="cf-display text-3xl font-bold leading-tight text-[#253142] md:text-5xl"
            style={{ textWrap: 'balance' }}
          >
            Confidence is a skill you can train.
          </h2>
          <p
            className="mt-4 max-w-[60ch] text-base leading-relaxed text-[#4b5563]"
            style={{ textWrap: 'pretty' }}
          >
            Practice real interviews, receive actionable delivery feedback, and watch your CV match signals snap into place.
          </p>
        </div>

        {/* Interactive 2-Column Scene */}
        <div className="grid grid-cols-1 items-center gap-12 md:grid-cols-2 md:gap-16">
          {/* Left: CV Document & Live Skill Snap */}
          <div className="rounded-2xl border border-[#ddd8ca] bg-white p-6 shadow-xs">
            {/* CV Header */}
            <div className="flex items-center justify-between border-b border-[#ddd8ca]/70 pb-4">
              <div className="flex items-center gap-3">
                <div className="grid h-10 w-10 place-items-center rounded-xl bg-[#faf8f3] text-[#253142] border border-[#ddd8ca]">
                  <FileText size={20} />
                </div>
                <div>
                  <h4 className="font-bold text-[#253142]">Alex Morgan</h4>
                  <p className="text-xs text-[#4b5563]">Target Role: Senior Product Designer</p>
                </div>
              </div>
              <div className="text-right">
                <div className="text-xs text-[#4b5563]">Match Score</div>
                <div className="cf-display text-2xl font-bold text-[#253142] transition-all duration-300">
                  {current.score}
                  <span className="text-xs font-normal text-[#4b5563]">/100</span>
                </div>
              </div>
            </div>

            {/* CV Snippet with keyword highlighting */}
            <div className="mt-4 rounded-xl border border-[#ddd8ca]/60 bg-[#faf8f3] p-4 text-xs leading-relaxed text-[#4b5563]">
              <div className="mb-2 font-bold uppercase tracking-wider text-[10px] text-[#7c5e14]">
                Professional Experience Summary
              </div>
              <p>
                Lead designer overseeing the multi-platform UI refresh. Architected comprehensive{' '}
                <span
                  className={`rounded-sm px-1.5 py-0.5 transition-all duration-300 font-semibold ${
                    current.keywordsActive
                      ? 'bg-[#f5c84b]/40 text-[#253142] ring-1 ring-[#f5c84b]'
                      : 'bg-transparent text-[#4b5563]'
                  }`}
                >
                  Design Systems
                </span>{' '}
                leveraging nested{' '}
                <span
                  className={`rounded-sm px-1.5 py-0.5 transition-all duration-300 font-semibold ${
                    current.keywordsActive
                      ? 'bg-[#f5c84b]/40 text-[#253142] ring-1 ring-[#f5c84b]'
                      : 'bg-transparent text-[#4b5563]'
                  }`}
                >
                  Figma Variables
                </span>{' '}
                and audited workflows for strict{' '}
                <span
                  className={`rounded-sm px-1.5 py-0.5 transition-all duration-300 font-semibold ${
                    activeStage === 2
                      ? 'bg-[#e2f0e9] text-[#277254] ring-1 ring-[#277254]'
                      : 'bg-transparent text-[#4b5563]'
                  }`}
                >
                  WCAG 2.1 A11y
                </span>{' '}
                compliance across our candidate portal.
              </p>
            </div>

            {/* Skill Requirements State */}
            <div className="mt-5">
              <div className="flex items-center justify-between text-xs font-semibold text-[#253142] mb-2.5">
                <span>Role Competency Match</span>
                <span className="text-[#277254] font-bold">
                  {current.matchedCount} of 4 Matched
                </span>
              </div>
              <div className="flex flex-wrap gap-2">
                {current.skills.map((skill) => (
                  <Chip
                    key={skill.label}
                    label={skill.label}
                    variant={skill.state === 'matched' ? 'matched' : 'neutral'}
                    icon={
                      skill.state === 'matched' ? (
                        <Check size={13} className="text-[#277254]" />
                      ) : (
                        <Plus size={13} className="text-[#7c5e14]" />
                      )
                    }
                  />
                ))}
              </div>
            </div>

            {/* Bottom Status Callout */}
            <div className="mt-5 flex items-center justify-between border-t border-[#ddd8ca]/70 pt-4 text-xs">
              <span className="text-[#4b5563]">System Verification:</span>
              <span
                className="font-bold flex items-center gap-1.5 transition-colors duration-300"
                style={{ color: current.statusColor }}
              >
                <CheckCircle2 size={13} /> {current.statusLabel}
              </span>
            </div>
          </div>

          {/* Right: Narrative Steps changing per scroll stage */}
          <div className="space-y-4">
            {steps.map((step, idx) => {
              const isActive = activeStage === idx;
              return (
                <div
                  key={step.title}
                  onClick={() => setActiveStage(idx)}
                  className={`cursor-pointer rounded-2xl border p-5 transition-all duration-300 ${
                    isActive
                      ? 'border-[#253142] bg-white shadow-xs'
                      : 'border-[#ddd8ca]/70 bg-transparent opacity-65 hover:opacity-100 hover:bg-white/50'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span
                      className={`grid h-6 w-6 place-items-center rounded-full text-xs font-bold ${
                        isActive
                          ? 'bg-[#253142] text-[#faf7ef]'
                          : 'bg-[#ddd8ca] text-[#4b5563]'
                      }`}
                    >
                      {idx + 1}
                    </span>
                    <h3 className="font-bold text-[#253142]">{step.title}</h3>
                  </div>
                  <p className="mt-2 text-sm leading-relaxed text-[#4b5563]">
                    {step.description}
                  </p>
                </div>
              );
            })}

            <div className="pt-2">
              <button
                type="button"
                onClick={() => setLocation('/register')}
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#f5c84b] px-5 py-2.5 text-sm font-semibold text-[#253142] transition duration-200 hover:bg-[#e8b93c] active:bg-[#dbaa2b] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#253142]"
              >
                Build your candidate profile <ArrowRight size={16} />
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

