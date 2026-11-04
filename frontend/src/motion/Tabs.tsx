import { motion, useReducedMotion } from 'framer-motion';
import { MOTION } from './tokens';

export interface TabItem {
  id: string;
  label: string;
  count?: number;
}

interface TabsProps {
  tabs: TabItem[];
  activeTab: string;
  onChange: (id: string) => void;
  variant?: 'underline' | 'pill';
  className?: string;
  layoutId?: string;
}

export function Tabs({
  tabs,
  activeTab,
  onChange,
  variant = 'underline',
  className = '',
  layoutId = 'tab-indicator',
}: TabsProps) {
  const prefersReduced = useReducedMotion();

  return (
    <div
      role="tablist"
      className={`flex items-center gap-1 ${
        variant === 'underline' ? 'border-b border-[#d9dbd1]' : 'p-1 bg-[#ede9dd] rounded-xl'
      } ${className}`}
    >
      {tabs.map((tab) => {
        const isActive = activeTab === tab.id;

        return (
          <button
            key={tab.id}
            role="tab"
            aria-selected={isActive}
            onClick={() => onChange(tab.id)}
            className={`relative flex items-center gap-2 px-3.5 py-2 text-xs font-semibold transition-colors duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#277254] rounded-lg ${
              isActive
                ? variant === 'underline'
                  ? 'text-[#253142]'
                  : 'text-[#253142]'
                : 'text-[#687382] hover:text-[#253142]'
            }`}
          >
            {/* Sliding Pill Background */}
            {variant === 'pill' && isActive && (
              <motion.div
                layoutId={prefersReduced ? undefined : layoutId}
                transition={{
                  duration: prefersReduced ? 0 : MOTION.duration.micro,
                  ease: MOTION.easeOutQuint,
                }}
                className="absolute inset-0 rounded-lg bg-[#ffffff] shadow-xs"
              />
            )}

            <span className="relative z-10">{tab.label}</span>

            {tab.count !== undefined && (
              <span
                className={`relative z-10 rounded-full px-1.5 py-0.5 text-[10px] font-bold ${
                  isActive
                    ? 'bg-[#253142] text-[#faf7ef]'
                    : 'bg-[#e5e3d8] text-[#556070]'
                }`}
              >
                {tab.count}
              </span>
            )}

            {/* Sliding Underline Bar */}
            {variant === 'underline' && isActive && (
              <motion.div
                layoutId={prefersReduced ? undefined : layoutId}
                transition={{
                  duration: prefersReduced ? 0 : MOTION.duration.component,
                  ease: MOTION.easeOutQuint,
                }}
                className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#253142]"
              />
            )}
          </button>
        );
      })}
    </div>
  );
}

