import { useState } from 'react';
import { useLocation } from 'wouter';
import { motion, AnimatePresence } from 'framer-motion';
import { BriefcaseBusiness, ArrowRight, ArrowLeftRight, CheckCircle2 } from 'lucide-react';
import { BRAND, MOTION } from './motionTokens';
import { MagneticButton } from './shared/MagneticButton';

interface PipelineCard {
  id: string;
  name: string;
  role: string;
  client: string;
  matchScore: number;
  columnId: 'sourced' | 'screening' | 'clientReview' | 'interviewing' | 'placed';
}

const INITIAL_PIPELINE: PipelineCard[] = [
  {
    id: 'p1',
    name: 'Marcus Vance',
    role: 'Principal DevOps Architect',
    client: 'CloudScale Inc',
    matchScore: 91,
    columnId: 'sourced',
  },
  {
    id: 'p2',
    name: 'Elena Rostova',
    role: 'Senior Product Designer',
    client: 'TechNova Ltd',
    matchScore: 89,
    columnId: 'screening',
  },
  {
    id: 'p3',
    name: 'Devon Miles',
    role: 'Full Stack Engineer',
    client: 'Apex Systems',
    matchScore: 94,
    columnId: 'clientReview',
  },
  {
    id: 'p4',
    name: 'Aria Montgomery',
    role: 'AI Research Engineer',
    client: 'TechNova Ltd',
    matchScore: 96,
    columnId: 'interviewing',
  },
  {
    id: 'p5',
    name: 'Lucas Thorne',
    role: 'Engineering Manager',
    client: 'Apex Systems',
    matchScore: 93,
    columnId: 'placed',
  },
];

const COLUMNS = [
  { id: 'sourced', title: 'Sourced', count: '1 Candidate' },
  { id: 'screening', title: 'Screening', count: '1 Candidate' },
  { id: 'clientReview', title: 'Client Review', count: '1 Candidate' },
  { id: 'interviewing', title: 'Interviewing', count: '1 Candidate' },
  { id: 'placed', title: 'Placed', count: '1 Candidate' },
] as const;

export function AgencyPipelineScene() {
  const [, setLocation] = useLocation();
  const [pipeline, setPipeline] = useState<PipelineCard[]>(INITIAL_PIPELINE);
  const [hasAdvanced, setHasAdvanced] = useState(false);

  // Eased movement of cards across columns
  const advancePipeline = () => {
    setPipeline((prev) =>
      prev.map((card) => {
        if (!hasAdvanced) {
          // Advance each card one step forward
          if (card.columnId === 'sourced') return { ...card, columnId: 'screening' };
          if (card.columnId === 'screening') return { ...card, columnId: 'clientReview' };
          if (card.columnId === 'clientReview') return { ...card, columnId: 'interviewing' };
          if (card.columnId === 'interviewing') return { ...card, columnId: 'placed' };
        } else {
          // Reset to initial
          return INITIAL_PIPELINE.find((c) => c.id === card.id) || card;
        }
        return card;
      })
    );
    setHasAdvanced(!hasAdvanced);
  };

  return (
    <section
      aria-labelledby="agencies-heading"
      className="w-full border-t border-[#ddd8ca] bg-[#f5f1e6] py-20"
      style={{ backgroundColor: 'var(--cf-landing-light, #f5f1e6)' }}
    >
      <div className={`${BRAND.layout.container}`}>
        {/* Section Header */}
        <div className="mb-10 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div className="max-w-2xl">
            <div className="mb-3 flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#7c5e14]">
              <BriefcaseBusiness size={16} /> For recruitment agencies
            </div>
            <h2
              id="agencies-heading"
              className="cf-display text-3xl font-bold leading-tight text-[#253142] md:text-5xl"
              style={{ textWrap: 'balance' }}
            >
              Move the right people forward.
            </h2>
            <p
              className="mt-4 max-w-[60ch] text-base leading-relaxed text-[#4b5563]"
              style={{ textWrap: 'pretty' }}
            >
              Keep every client, recruitment room, and applicant in view. Manage the talent lifecycle with live cross-client candidate movement.
            </p>
          </div>

          <button
            type="button"
            onClick={advancePipeline}
            className="inline-flex items-center gap-2 self-start rounded-xl border border-[#253142] bg-white px-4 py-2.5 text-xs font-bold text-[#253142] transition-colors hover:bg-[#faf8f3] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#253142]"
          >
            <ArrowLeftRight size={14} className="text-[#277254]" />
            {hasAdvanced ? 'Reset Pipeline Stages' : 'Simulate Stage Advance'}
          </button>
        </div>

        {/* Horizontal Pipeline Board */}
        <div className="overflow-x-auto pb-4">
          <div className="grid min-w-[840px] grid-cols-5 gap-4">
            {COLUMNS.map((col) => {
              const cardsInCol = pipeline.filter((c) => c.columnId === col.id);
              return (
                <div
                  key={col.id}
                  className="flex flex-col rounded-2xl border border-[#ddd8ca] bg-white p-4 shadow-xs"
                >
                  <div className="border-b border-[#ddd8ca]/70 pb-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-[#253142]">{col.title}</span>
                      <span className="rounded-md bg-[#faf8f3] px-2 py-0.5 text-[10px] font-semibold text-[#4b5563] border border-[#ddd8ca]">
                        {cardsInCol.length}
                      </span>
                    </div>
                  </div>

                  <div className="mt-3 flex flex-1 flex-col gap-3 min-h-[140px]">
                    <AnimatePresence>
                      {cardsInCol.map((card) => (
                        <motion.div
                          key={card.id}
                          layout
                          initial={{ opacity: 0, scale: 0.95 }}
                          animate={{ opacity: 1, scale: 1 }}
                          exit={{ opacity: 0, scale: 0.95 }}
                          transition={{
                            type: 'spring',
                            stiffness: 300,
                            damping: 26,
                            mass: 0.6,
                          }}
                          className="rounded-xl border border-[#ddd8ca]/70 bg-[#faf8f3] p-3 text-xs shadow-xs"
                        >
                          <div className="flex items-center justify-between">
                            <span className="rounded-sm bg-[#e2f0e9] px-1.5 py-0.5 text-[9px] font-bold text-[#277254]">
                              {card.client}
                            </span>
                            <span className="font-bold text-[#253142]">
                              {card.matchScore}%
                            </span>
                          </div>
                          <div className="mt-2 font-bold text-[#253142]">{card.name}</div>
                          <div className="text-[11px] text-[#4b5563]">{card.role}</div>
                        </motion.div>
                      ))}
                    </AnimatePresence>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Agency Action Row */}
        <div className="mt-8 flex flex-wrap items-center justify-between gap-4 border-t border-[#ddd8ca] pt-6">
          <MagneticButton
            variant="primary"
            onClick={() => setLocation('/register')}
          >
            Join as an agency <ArrowRight size={16} />
          </MagneticButton>
          <span className="text-xs text-[#4b5563]">
            Cross-client talent pools and client-ready shortlists in one agency portal.
          </span>
        </div>
      </div>
    </section>
  );
}

