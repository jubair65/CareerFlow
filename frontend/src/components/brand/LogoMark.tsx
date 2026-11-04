import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';

export interface LogoMarkProps {
  tone?: 'color' | 'onDark' | 'mono';
  size?: number | string;
  className?: string;
  title?: string;
  animated?: boolean;
}

/**
 * CareerFlow Stepped Flow Badge (Direction A)
 * Geometric 64x64 canvas, rx=18, stroke=6.0px (+8% small-canvas boost),
 * +1.0px rightward centroid optical balance shift.
 */
export function LogoMark({
  tone = 'color',
  size = 36,
  className = '',
  title = 'CareerFlow Logo Mark',
  animated = false,
}: LogoMarkProps) {
  const prefersReduced = useReducedMotion();

  // Tone color definitions matching CareerFlow design tokens
  let badgeBg = '#f5c84b';    // Warm Yellow primary
  let glyphStroke = '#253142'; // Deep Navy primary

  if (tone === 'mono') {
    badgeBg = 'currentColor';
    glyphStroke = '#ffffff';
  } else if (tone === 'onDark') {
    badgeBg = '#f5c84b';
    glyphStroke = '#253142';
  }

  const dimension = typeof size === 'number' ? `${size}px` : size;

  const mainPathD =
    'M 36.5 18 L 26.5 18 A 12 12 0 0 0 14.5 30 L 14.5 34 A 12 12 0 0 0 26.5 46 L 36.5 46 A 6 6 0 0 0 42.5 40 L 42.5 34 L 49.5 34';
  const arrowPathD = 'M 43.5 28 L 49.5 34 L 43.5 40';

  return (
    <div
      className={`grid place-items-center rounded-xl overflow-hidden shrink-0 shadow-xs select-none ${className}`}
      style={{
        width: dimension,
        height: dimension,
        minWidth: dimension,
        minHeight: dimension,
        backgroundColor: badgeBg,
      }}
      aria-hidden={title ? undefined : 'true'}
    >
      <svg
        viewBox="0 0 64 64"
        className="h-full w-full block"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        role={title ? 'img' : 'presentation'}
        aria-label={title}
      >
        {title && <title>{title}</title>}
        <rect width="64" height="64" rx="18" fill={badgeBg} />

        {animated ? (
          <>
            <motion.path
              d={mainPathD}
              stroke={glyphStroke}
              strokeWidth="6"
              strokeLinecap="round"
              strokeLinejoin="round"
              initial={prefersReduced ? false : { pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ duration: 1.2, ease: [0.22, 1, 0.36, 1] }}
            />
            <motion.path
              d={arrowPathD}
              stroke={glyphStroke}
              strokeWidth="6"
              strokeLinecap="round"
              strokeLinejoin="round"
              initial={prefersReduced ? false : { pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ duration: 0.4, delay: 0.8, ease: [0.22, 1, 0.36, 1] }}
            />
          </>
        ) : (
          <>
            <path
              d={mainPathD}
              stroke={glyphStroke}
              strokeWidth="6"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d={arrowPathD}
              stroke={glyphStroke}
              strokeWidth="6"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </>
        )}
      </svg>
    </div>
  );
}

