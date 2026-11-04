import { useReducedMotion } from 'framer-motion';

interface ProgressBarProps {
  value: number; // 0 to 100
  max?: number;
  height?: number; // px
  color?: string;
  bgColor?: string;
  className?: string;
}

export function ProgressBar({
  value,
  max = 100,
  height = 8,
  color = '#277254',
  bgColor = '#eceae2',
  className = '',
}: ProgressBarProps) {
  const prefersReduced = useReducedMotion();
  const clamped = Math.max(0, Math.min(max, value));
  const percent = max > 0 ? (clamped / max) * 100 : 0;

  return (
    <div
      role="progressbar"
      aria-valuenow={clamped}
      aria-valuemin={0}
      aria-valuemax={max}
      className={`w-full overflow-hidden rounded-full ${className}`}
      style={{
        height: `${height}px`,
        backgroundColor: bgColor,
      }}
    >
      <div
        className="h-full rounded-full"
        style={{
          width: `${percent}%`,
          backgroundColor: color,
          transition: prefersReduced
            ? 'none'
            : 'width 0.45s cubic-bezier(0.22, 1, 0.36, 1)',
        }}
      />
    </div>
  );
}

interface ProgressRingProps {
  value: number; // current value
  max?: number; // target value
  size?: number; // width & height in px
  strokeWidth?: number; // px
  color?: string;
  bgColor?: string;
  showLabel?: boolean;
  label?: React.ReactNode;
  className?: string;
}

export function ProgressRing({
  value,
  max = 100,
  size = 40,
  strokeWidth = 3.5,
  color = '#277254',
  bgColor = '#e5e3d8',
  showLabel = true,
  label,
  className = '',
}: ProgressRingProps) {
  const prefersReduced = useReducedMotion();
  const clamped = Math.max(0, Math.min(max, value));
  const ratio = max > 0 ? clamped / max : 0;

  const center = size / 2;
  const radius = center - strokeWidth;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference * (1 - ratio);

  return (
    <div
      role="progressbar"
      aria-valuenow={clamped}
      aria-valuemin={0}
      aria-valuemax={max}
      className={`relative inline-flex items-center justify-center shrink-0 ${className}`}
      style={{ width: size, height: size, minWidth: size, minHeight: size }}
    >
      <svg width={size} height={size} className="transform -rotate-90 shrink-0">
        <circle
          cx={center}
          cy={center}
          r={radius}
          stroke={bgColor}
          strokeWidth={strokeWidth}
          fill="transparent"
        />
        <circle
          cx={center}
          cy={center}
          r={radius}
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          fill="transparent"
          style={{
            transition: prefersReduced
              ? 'none'
              : 'stroke-dashoffset 0.6s cubic-bezier(0.22, 1, 0.36, 1)',
          }}
        />
      </svg>
      {showLabel && (
        <span
          className="absolute inset-0 flex items-center justify-center text-center leading-none select-none pointer-events-none"
        >
          {label ?? (
            <span className="flex items-baseline justify-center tracking-tight">
              <span className="text-[11px] font-bold text-[#253142]">{clamped}</span>
              <span className="text-[9px] font-medium text-[#7b8490] mx-0.5">/</span>
              <span className="text-[9px] font-medium text-[#7b8490]">{max}</span>
            </span>
          )}
        </span>
      )}
    </div>
  );
}

