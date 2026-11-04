import { useState, useEffect } from 'react';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import { Check, ChevronRight, Presentation, FileText, Briefcase } from 'lucide-react';
import { useLocation } from 'wouter';
import { DASHBOARD_MOTION } from './motionTokens';

export interface ChecklistItem {
  id: string;
  title: string;
  description: string;
  completed: boolean;
  path: string;
  icon: typeof Presentation;
}

interface InteractiveChecklistProps {
  initialItems: ChecklistItem[];
}

export function InteractiveChecklist({ initialItems }: InteractiveChecklistProps) {
  const [, setLocation] = useLocation();
  const prefersReduced = useReducedMotion();
  const [items, setItems] = useState<ChecklistItem[]>(initialItems);

  useEffect(() => {
    setItems(initialItems);
  }, [initialItems]);

  const completedCount = items.filter((i) => i.completed).length;
  const totalCount = items.length;
  const progressRatio = totalCount > 0 ? completedCount / totalCount : 0;

  // Circular progress ring metrics
  const radius = 18;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - progressRatio * circumference;

  const toggleItem = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setItems((prev) =>
      prev.map((item) => (item.id === id ? { ...item, completed: !item.completed } : item))
    );
  };

  return (
    <div className="w-full">
      {/* Header with Circular Progress Ring */}
      <div className="flex items-center justify-between border-b border-[#eef0e7] pb-4">
        <div>
          <span className="text-[11px] font-bold uppercase tracking-[.14em] text-[#7b8490]">
            Onboarding Progress
          </span>
          <h3 className="text-base font-bold text-[#253142] mt-0.5">
            {completedCount === totalCount ? 'All starter tasks complete!' : 'Getting started checklist'}
          </h3>
        </div>

        {/* Circular Progress Ring */}
        <div className="relative flex items-center justify-center">
          <svg className="h-12 w-12 -rotate-90 transform" viewBox="0 0 48 48">
            <circle
              cx="24"
              cy="24"
              r={radius}
              stroke="#e8e6dc"
              strokeWidth="3.5"
              fill="transparent"
            />
            {prefersReduced ? (
              <circle
                cx="24"
                cy="24"
                r={radius}
                stroke="#277254"
                strokeWidth="3.5"
                fill="transparent"
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
              />
            ) : (
              <motion.circle
                cx="24"
                cy="24"
                r={radius}
                stroke="#277254"
                strokeWidth="3.5"
                fill="transparent"
                strokeDasharray={circumference}
                strokeLinecap="round"
                initial={{ strokeDashoffset: circumference }}
                animate={{ strokeDashoffset }}
                transition={{ duration: 0.8, ease: DASHBOARD_MOTION.easeOutQuint }}
              />
            )}
          </svg>
          <span className="absolute text-[11px] font-bold text-[#253142]">
            {completedCount}/{totalCount}
          </span>
        </div>
      </div>

      {/* Checklist items with layout animation */}
      <div className="mt-3.5 space-y-2">
        <AnimatePresence initial={false}>
          {items.map((item) => {
            const Icon = item.icon;
            return (
              <motion.div
                key={item.id}
                layout
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, transition: { duration: 0.25 } }}
                transition={{
                  duration: DASHBOARD_MOTION.duration.component,
                  ease: DASHBOARD_MOTION.easeOutQuint,
                }}
                className={`group flex items-center gap-3 rounded-xl border p-3 transition-colors cursor-pointer ${
                  item.completed
                    ? 'border-[#e4ebe6] bg-[#fbfdfc]'
                    : 'border-[#eef0e7] bg-[#fbfaf5] hover:bg-[#fff7e2]'
                }`}
                onClick={() => setLocation(item.path)}
              >
                {/* Interactive Checkbox */}
                <button
                  type="button"
                  aria-label={item.completed ? `Mark ${item.title} as incomplete` : `Mark ${item.title} as complete`}
                  onClick={(e) => toggleItem(item.id, e)}
                  className={`grid h-6 w-6 shrink-0 place-items-center rounded-lg border transition-all ${
                    item.completed
                      ? 'border-[#277254] bg-[#277254] text-white shadow-xs'
                      : 'border-[#ccd0c6] bg-white text-transparent hover:border-[#277254]'
                  }`}
                >
                  {item.completed && (
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ duration: 0.15 }}
                    >
                      <Check size={14} strokeWidth={3} />
                    </motion.div>
                  )}
                </button>

                {/* Icon thumbnail */}
                <div
                  className={`grid h-8 w-8 shrink-0 place-items-center rounded-lg ${
                    item.completed
                      ? 'bg-[#e2f0e9] text-[#277254]'
                      : 'bg-[#fff1c9] text-[#8a6a16]'
                  }`}
                >
                  <Icon size={15} />
                </div>

                {/* Text */}
                <div className="min-w-0 flex-1">
                  <div
                    className={`text-xs font-bold transition-colors ${
                      item.completed ? 'text-[#7b8490] line-through' : 'text-[#253142]'
                    }`}
                  >
                    {item.title}
                  </div>
                  <div className="truncate text-[11px] text-[#7b8490]">{item.description}</div>
                </div>

                {/* Link Arrow */}
                <ChevronRight
                  size={15}
                  className="text-[#9da5ac] transition-transform group-hover:translate-x-1"
                />
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </div>
  );
}

