import { type ReactNode, type FC } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { TrendingUp, TrendingDown, ArrowRight, type LucideIcon } from 'lucide-react';
import { DASHBOARD_MOTION } from './motionTokens';
import { useCountUp } from './useCountUp';

interface InteractiveStatCardProps {
  label: string;
  numericValue?: number | null;
  displayOverride?: string;
  detail: ReactNode;
  icon: LucideIcon;
  accent?: 'yellow' | 'green' | 'blue' | 'coral';
  onClick: () => void;
  testId: string;
  trendDelta?: string | null;
  showTrend?: boolean;
  isGoal?: boolean;
  goalCurrent?: number;
  goalTotal?: number;
  delayIndex?: number;
  isHighlighted?: boolean;
}

export const InteractiveStatCard: FC<InteractiveStatCardProps> = ({
  label,
  numericValue,
  displayOverride,
  detail,
  icon: Icon,
  accent = 'yellow',
  onClick,
  testId,
  trendDelta,
  showTrend = false,
  isGoal = false,
  goalCurrent = 0,
  goalTotal = 3,
  delayIndex = 0,
  isHighlighted = false,
}) => {
  const prefersReduced = useReducedMotion();
  const animatedNumber = useCountUp(numericValue != null ? numericValue : null, 800);

  const colors = {
    yellow: 'bg-[#fff1c9] text-[#8a6a16]',
    green: 'bg-[#e2f0e9] text-[#277254]',
    blue: 'bg-[#e4edf5] text-[#3a6384]',
    coral: 'bg-[#f7e5e1] text-[#a33d35]',
  };

  const isPositive = trendDelta ? !trendDelta.startsWith('-') : true;

  const displayString =
    displayOverride != null
      ? displayOverride
      : numericValue != null
      ? String(animatedNumber)
      : '--';

  return (
    <motion.div
      initial={prefersReduced ? false : { opacity: 0, y: 12 }}
      animate={prefersReduced ? false : { opacity: 1, y: 0 }}
      transition={{
        duration: DASHBOARD_MOTION.duration.component,
        delay: delayIndex * DASHBOARD_MOTION.stagger.statCards,
        ease: DASHBOARD_MOTION.easeOutQuint,
      }}
      tabIndex={0}
      role="button"
      onClick={onClick}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick();
        }
      }}
      data-testid={testId}
      className={`group relative flex flex-col justify-between rounded-2xl bg-white p-5 border text-left cursor-pointer transition-all duration-200 hover:-translate-y-0.5 active:scale-[0.98] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#253142] focus-visible:ring-offset-2 shadow-xs hover:shadow-md ${
        isHighlighted
          ? 'border-[#f5c84b] ring-2 ring-[#f5c84b]/50'
          : 'border-[#d9dbd1] hover:border-[#253142]/40'
      }`}
    >
      {/* Top Header */}
      <div className="flex items-start justify-between">
        <span className="text-[11px] font-bold uppercase tracking-[.14em] text-[#7b8490]">
          {label}
        </span>
        <span
          className={`grid h-9 w-9 place-items-center rounded-xl transition-transform duration-200 group-hover:scale-105 ${colors[accent]}`}
        >
          <Icon size={17} />
        </span>
      </div>

      {/* Metric Display */}
      <div className="mt-3">
        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-extrabold text-[#253142] tracking-tight">
            {displayString}
          </span>
          {showTrend && trendDelta && (
            <span
              className={`inline-flex items-center gap-0.5 text-xs font-bold ${
                isPositive ? 'text-[#277254]' : 'text-[#a33d35]'
              }`}
            >
              {isPositive ? <TrendingUp size={13} /> : <TrendingDown size={13} />}
              {trendDelta}
            </span>
          )}
        </div>

        {/* Goal Progress Bar if applicable */}
        {isGoal && (
          <div className="mt-2.5 flex items-center gap-1.5">
            {Array.from({ length: goalTotal }).map((_, idx) => (
              <div
                key={`goal-segment-${idx}`}
                className={`h-1.5 flex-1 rounded-full transition-colors duration-300 ${
                  idx < goalCurrent ? 'bg-[#253142]' : 'bg-[#e8e6dc]'
                }`}
              />
            ))}
          </div>
        )}

        {/* Subtitle / Detail */}
        <div className="mt-1 text-xs font-semibold text-[#78818d]">{detail}</div>
      </div>

      {/* Bottom sliding view indicator */}
      <div className="mt-3 flex items-center justify-between border-t border-[#f0eee6] pt-2.5 text-[11px] font-bold text-[#8d9aab] group-hover:text-[#253142] transition-colors">
        <span>View details</span>
        <ArrowRight size={13} className="transition-transform duration-200 group-hover:translate-x-1" />
      </div>
    </motion.div>
  );
};

