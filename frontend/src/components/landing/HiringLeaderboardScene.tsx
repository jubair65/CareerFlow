import { useState, useMemo } from 'react';
import { useLocation } from 'wouter';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Building2, ArrowRight, SlidersHorizontal, ChevronRight, X, FileSpreadsheet, CheckCircle2
} from 'lucide-react';
import { BRAND, MOTION } from './motionTokens';
import { MagneticButton } from './shared/MagneticButton';

interface Candidate {
  id: string;
  name: string;
  role: string;
  cvScore: number;
  videoScore: number;
  stage: 'Shortlisted' | 'Round 1' | 'Offered';
  avatarInitials: string;
  cvDetails: { keywords: number; clarity: number; structure: number };
  videoDetails: { pace: string; eyeContact: number; posture: number };
  notes: string;
}

const INITIAL_CANDIDATES: Candidate[] = [
  {
    id: 'c1',
    name: 'Alex Rivera',
    role: 'Senior Frontend Engineer',
    cvScore: 94,
    videoScore: 76,
    stage: 'Shortlisted',
    avatarInitials: 'AR',
    cvDetails: { keywords: 96, clarity: 92, structure: 94 },
    videoDetails: { pace: '136 WPM (Ideal)', eyeContact: 88, posture: 92 },
    notes: 'Exceptional deep dive on state management and rendering bottlenecks.',
  },
  {
    id: 'c2',
    name: 'Maya Chen',
    role: 'Staff Product Designer',
    cvScore: 80,
    videoScore: 96,
    stage: 'Shortlisted',
    avatarInitials: 'MC',
    cvDetails: { keywords: 82, clarity: 80, structure: 78 },
    videoDetails: { pace: '142 WPM (Ideal)', eyeContact: 98, posture: 95 },
    notes: 'Outstanding articulation of cross-functional trade-offs and user testing.',
  },
  {
    id: 'c3',
    name: 'David Kim',
    role: 'Full Stack Engineer',
    cvScore: 86,
    videoScore: 82,
    stage: 'Round 1',
    avatarInitials: 'DK',
    cvDetails: { keywords: 88, clarity: 84, structure: 86 },
    videoDetails: { pace: '128 WPM (Fair)', eyeContact: 84, posture: 80 },
    notes: 'Solid full-stack architecture background with clean API designs.',
  },
  {
    id: 'c4',
    name: 'Sarah Jenkins',
    role: 'Lead System Engineer',
    cvScore: 90,
    videoScore: 72,
    stage: 'Offered',
    avatarInitials: 'SJ',
    cvDetails: { keywords: 92, clarity: 90, structure: 88 },
    videoDetails: { pace: '122 WPM (Fair)', eyeContact: 78, posture: 85 },
    notes: 'Strong distributed system expertise; offer pending candidate sign-off.',
  },
];

export function HiringLeaderboardScene() {
  const [, setLocation] = useLocation();
  const [cvWeight, setCvWeight] = useState(50); // 50 to 70%
  const [activeStageFilter, setActiveStageFilter] = useState<'All' | 'Shortlisted' | 'Round 1' | 'Offered'>('All');
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null);

  const videoWeight = 100 - cvWeight;

  // Compute composite score for each candidate and sort dynamically (FLIP)
  const rankedCandidates = useMemo(() => {
    return INITIAL_CANDIDATES.map((c) => {
      const composite = Math.round((c.cvScore * cvWeight + c.videoScore * videoWeight) / 100);
      return { ...c, composite };
    })
      .filter((c) => activeStageFilter === 'All' || c.stage === activeStageFilter)
      .sort((a, b) => b.composite - a.composite);
  }, [cvWeight, videoWeight, activeStageFilter]);

  return (
    <section
      aria-labelledby="hiring-teams-heading"
      className="relative w-full py-20 text-[#faf7ef]"
      style={{ backgroundColor: 'var(--cf-landing-dark, #253142)' }}
    >
      <div className={`${BRAND.layout.container}`}>
        {/* Section Header */}
        <div className="mb-12 max-w-2xl">
          <div className="mb-3 flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#f5c84b]">
            <Building2 size={16} /> For hiring teams
          </div>
          <h2
            id="hiring-teams-heading"
            className="cf-display text-3xl font-bold leading-tight text-[#faf7ef] md:text-5xl"
            style={{ textWrap: 'balance' }}
          >
            Make every hiring decision clearer.
          </h2>
          <p
            className="mt-4 max-w-[60ch] text-base leading-relaxed text-[#c3ccd5]"
            style={{ textWrap: 'pretty' }}
          >
            Create structured recruitment rooms, compare candidates on verified signals, and adjust evaluation weights with instant FLIP re-ranking.
          </p>
        </div>

        {/* Leaderboard Interactive Card */}
        <div className="rounded-2xl border border-[#3a4b60] bg-[#2d3b4e] p-6 text-[#faf7ef] shadow-xs">
          {/* Top Controls: Weight Slider & Stage Chips */}
          <div className="flex flex-col gap-6 border-b border-[#3a4b60] pb-6 lg:flex-row lg:items-center lg:justify-between">
            {/* Weight Slider */}
            <div className="flex flex-col gap-2">
              <div className="flex items-center gap-2 text-xs font-semibold text-[#c3ccd5]">
                <SlidersHorizontal size={14} className="text-[#f5c84b]" />
                <span>
                  Dynamic Rubric Weight:{' '}
                  <strong className="text-[#faf7ef]">
                    {cvWeight}% CV / {videoWeight}% Video
                  </strong>
                </span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-xs text-[#aab5c0]">50/50</span>
                <input
                  type="range"
                  min="50"
                  max="70"
                  step="5"
                  value={cvWeight}
                  onChange={(e) => setCvWeight(Number(e.target.value))}
                  aria-label="Evaluation rubric weight balance"
                  className="h-2 w-48 cursor-pointer accent-[#f5c84b]"
                />
                <span className="text-xs text-[#aab5c0]">70/30</span>
              </div>
            </div>

            {/* Stage Filter Chips */}
            <div className="flex flex-wrap items-center gap-2">
              {(['All', 'Shortlisted', 'Round 1', 'Offered'] as const).map((stage) => {
                const isActive = activeStageFilter === stage;
                return (
                  <button
                    key={stage}
                    type="button"
                    onClick={() => setActiveStageFilter(stage)}
                    className={`rounded-lg border px-3 py-1.5 text-xs font-semibold transition-all duration-150 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#faf7ef] ${
                      isActive
                        ? 'border-[#f5c84b] bg-[#f5c84b] text-[#253142]'
                        : 'border-[#3a4b60] bg-[#253142] text-[#c3ccd5] hover:border-[#aab5c0]'
                    }`}
                  >
                    {stage}
                  </button>
                );
              })}
            </div>
          </div>

          {/* FLIP Re-Ranking Leaderboard Rows */}
          <div className="mt-5 space-y-3">
            <AnimatePresence>
              {rankedCandidates.map((c, index) => (
                <motion.div
                  key={c.id}
                  layout
                  transition={{ type: 'spring', stiffness: 350, damping: 30 }}
                  onClick={() => setSelectedCandidate(c)}
                  className="flex cursor-pointer items-center justify-between rounded-xl border border-[#3a4b60] bg-[#253142] p-4 text-xs transition-colors hover:border-[#f5c84b]/60 hover:bg-[#283648]"
                >
                  <div className="flex items-center gap-3.5">
                    <span className="flex h-6 w-6 items-center justify-center rounded-md bg-[#394b5e] font-bold text-[#faf7ef]">
                      #{index + 1}
                    </span>
                    <div className="grid h-9 w-9 place-items-center rounded-lg bg-[#394b5e] font-bold text-[#f5c84b]">
                      {c.avatarInitials}
                    </div>
                    <div>
                      <div className="text-sm font-bold text-[#faf7ef]">{c.name}</div>
                      <div className="text-[11px] text-[#b5bfca]">{c.role}</div>
                    </div>
                  </div>

                  <div className="flex items-center gap-6">
                    <div className="hidden sm:block text-right">
                      <div className="text-[11px] text-[#b5bfca]">
                        CV: {c.cvScore}% · Video: {c.videoScore}%
                      </div>
                      <div className="font-semibold text-[#84c49f]">{c.stage}</div>
                    </div>

                    <div className="text-right">
                      <div className="cf-display text-xl font-bold text-[#f5c84b]">
                        {c.composite}
                        <span className="text-xs font-normal text-[#b5bfca]">/100</span>
                      </div>
                    </div>

                    <ChevronRight size={16} className="text-[#aab5c0]" />
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>

          {/* Bottom Action Row */}
          <div className="mt-8 flex flex-wrap items-center justify-between gap-4 border-t border-[#3a4b60] pt-6">
            <MagneticButton
              variant="darkPrimary"
              onClick={() => setLocation('/register')}
            >
              Join as hiring team <ArrowRight size={16} />
            </MagneticButton>
            <span className="text-xs text-[#aab5c0]">
              Click any candidate row to inspect sub-scores & verified interview signals.
            </span>
          </div>
        </div>

        {/* Slide-in Score Breakdown Drawer Modal */}
        <AnimatePresence>
          {selectedCandidate && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-xs"
            >
              <motion.div
                initial={{ y: 24, scale: 0.96 }}
                animate={{ y: 0, scale: 1 }}
                exit={{ y: 24, scale: 0.96 }}
                transition={{ duration: MOTION.duration.component, ease: MOTION.easeOutQuint }}
                className="w-full max-w-lg rounded-2xl border border-[#3a4b60] bg-[#253142] p-6 text-[#faf7ef] shadow-xl"
              >
                <div className="flex items-center justify-between border-b border-[#3a4b60] pb-4">
                  <div>
                    <span className="text-[11px] font-bold uppercase tracking-wider text-[#f5c84b]">
                      Applicant Breakdown · #{selectedCandidate.stage}
                    </span>
                    <h3 className="cf-display text-xl font-bold text-[#faf7ef]">
                      {selectedCandidate.name}
                    </h3>
                    <p className="text-xs text-[#b5bfca]">{selectedCandidate.role}</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => setSelectedCandidate(null)}
                    aria-label="Close modal"
                    className="rounded-lg p-1 text-[#b5bfca] hover:bg-[#394b5e] hover:text-[#faf7ef]"
                  >
                    <X size={18} />
                  </button>
                </div>

                <div className="mt-5 space-y-4 text-xs">
                  {/* Composite Callout */}
                  <div className="flex items-center justify-between rounded-xl bg-[#2d3b4e] p-4">
                    <div>
                      <div className="font-semibold text-[#b5bfca]">Current Weighted Score</div>
                      <div className="text-[11px] text-[#aab5c0]">
                        {cvWeight}% CV Weight + {videoWeight}% Video Weight
                      </div>
                    </div>
                    <div className="cf-display text-3xl font-bold text-[#f5c84b]">
                      {selectedCandidate.composite}
                      <span className="text-sm font-normal text-[#b5bfca]">/100</span>
                    </div>
                  </div>

                  {/* CV Signals */}
                  <div className="rounded-xl border border-[#3a4b60] p-4 space-y-2">
                    <div className="font-bold text-[#faf7ef] mb-1">CV Evaluation Signals</div>
                    <div className="flex justify-between text-[#c3ccd5]">
                      <span>Technical Keywords:</span>
                      <strong className="text-[#faf7ef]">{selectedCandidate.cvDetails.keywords}%</strong>
                    </div>
                    <div className="flex justify-between text-[#c3ccd5]">
                      <span>Clarity and Impact:</span>
                      <strong className="text-[#faf7ef]">{selectedCandidate.cvDetails.clarity}%</strong>
                    </div>
                    <div className="flex justify-between text-[#c3ccd5]">
                      <span>Structural Formatting:</span>
                      <strong className="text-[#faf7ef]">{selectedCandidate.cvDetails.structure}%</strong>
                    </div>
                  </div>

                  {/* Video Signals */}
                  <div className="rounded-xl border border-[#3a4b60] p-4 space-y-2">
                    <div className="font-bold text-[#faf7ef] mb-1">Interview Video Signals</div>
                    <div className="flex justify-between text-[#c3ccd5]">
                      <span>Speaking Pace:</span>
                      <strong className="text-[#84c49f]">{selectedCandidate.videoDetails.pace}</strong>
                    </div>
                    <div className="flex justify-between text-[#c3ccd5]">
                      <span>Eye Contact Ratio:</span>
                      <strong className="text-[#faf7ef]">{selectedCandidate.videoDetails.eyeContact}%</strong>
                    </div>
                    <div className="flex justify-between text-[#c3ccd5]">
                      <span>Posture & Engagement:</span>
                      <strong className="text-[#faf7ef]">{selectedCandidate.videoDetails.posture}%</strong>
                    </div>
                  </div>

                  {/* Interviewer Notes */}
                  <div className="rounded-xl bg-[#2d3b4e] p-3 text-[11px] text-[#c3ccd5]">
                    <strong className="text-[#faf7ef]">Interviewer Notes:</strong> {selectedCandidate.notes}
                  </div>
                </div>

                <div className="mt-6 flex items-center justify-between border-t border-[#3a4b60] pt-4">
                  <button
                    type="button"
                    onClick={() => setSelectedCandidate(null)}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-[#3a4b60] px-3 py-2 text-xs font-semibold text-[#faf7ef] hover:bg-[#394b5e]"
                  >
                    <FileSpreadsheet size={14} /> Export signals PDF
                  </button>
                  <button
                    type="button"
                    onClick={() => setSelectedCandidate(null)}
                    className="rounded-lg bg-[#f5c84b] px-4 py-2 text-xs font-bold text-[#253142] hover:bg-[#ffd969]"
                  >
                    Close
                  </button>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </section>
  );
}

