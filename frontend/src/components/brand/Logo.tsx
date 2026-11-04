import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { LogoMark } from './LogoMark';

export type LogoVariant = 'mark' | 'horizontal' | 'stacked';
export type LogoTone = 'color' | 'onDark' | 'mono';
export type LogoSize = 'sm' | 'md' | 'lg' | 'xl' | number;

export interface LogoProps {
  variant?: LogoVariant;
  tone?: LogoTone;
  size?: LogoSize;
  className?: string;
  title?: string;
  subtitle?: string;
  animated?: boolean;
  onClick?: () => void;
  'data-testid'?: string;
}

const SIZE_MAP = {
  sm: { markSize: 28, textClass: 'text-base', gapClass: 'gap-2', subTextClass: 'text-[9px]' },
  md: { markSize: 36, textClass: 'text-lg', gapClass: 'gap-2.5', subTextClass: 'text-[10px]' },
  lg: { markSize: 44, textClass: 'text-xl', gapClass: 'gap-3', subTextClass: 'text-xs' },
  xl: { markSize: 56, textClass: 'text-2xl', gapClass: 'gap-3.5', subTextClass: 'text-sm' },
};

/**
 * CareerFlow Single Source of Truth Brand Logo Component
 *
 * Implements Direction A: Stepped Flow Badge with outlined Space Grotesk styling.
 * Renders data-brand-logo="v2" for automated verification and regression prevention.
 */
export function Logo({
  variant = 'horizontal',
  tone = 'color',
  size = 'md',
  className = '',
  title = 'CareerFlow',
  subtitle,
  animated = false,
  onClick,
  'data-testid': testId = 'brand-careerflow',
}: LogoProps) {
  const prefersReduced = useReducedMotion();

  // Resolve dimensions
  let markSize = 36;
  let textClass = 'text-lg';
  let gapClass = 'gap-2.5';
  let subTextClass = 'text-[10px]';

  if (typeof size === 'number') {
    markSize = size;
    if (size <= 28) {
      textClass = 'text-base';
      gapClass = 'gap-2';
      subTextClass = 'text-[9px]';
    } else if (size >= 56) {
      textClass = 'text-2xl';
      gapClass = 'gap-3.5';
      subTextClass = 'text-sm';
    } else if (size >= 44) {
      textClass = 'text-xl';
      gapClass = 'gap-3';
      subTextClass = 'text-xs';
    }
  } else if (SIZE_MAP[size]) {
    const config = SIZE_MAP[size];
    markSize = config.markSize;
    textClass = config.textClass;
    gapClass = config.gapClass;
    subTextClass = config.subTextClass;
  }

  // Resolve typography color
  let textToneClass = 'text-[#253142]';
  let subToneClass = 'text-[#7b8490]';

  if (tone === 'onDark') {
    textToneClass = 'text-[#f8f4e9]';
    subToneClass = 'text-[#9daaba]';
  } else if (tone === 'mono') {
    textToneClass = 'text-current';
    subToneClass = 'text-current opacity-70';
  }

  // Variant: Mark only
  if (variant === 'mark') {
    return (
      <div
        data-brand-logo="v2"
        data-testid={testId}
        className={`inline-flex shrink-0 ${onClick ? 'cursor-pointer' : ''} ${className}`}
        onClick={onClick}
      >
        <LogoMark
          tone={tone}
          size={markSize}
          title={title}
          animated={animated}
        />
      </div>
    );
  }

  // Variant: Stacked
  if (variant === 'stacked') {
    return (
      <div
        data-brand-logo="v2"
        data-testid={testId}
        className={`inline-flex flex-col items-center text-center gap-2 ${onClick ? 'cursor-pointer' : ''} ${className}`}
        onClick={onClick}
      >
        <LogoMark
          tone={tone}
          size={markSize}
          title={title}
          animated={animated}
        />
        <div className="flex flex-col items-center">
          <span className={`cf-display font-bold tracking-tight leading-none ${textClass} ${textToneClass}`}>
            CareerFlow
          </span>
          {subtitle && (
            <span className={`font-semibold tracking-wider uppercase mt-1 leading-none ${subTextClass} ${subToneClass}`}>
              {subtitle}
            </span>
          )}
        </div>
      </div>
    );
  }

  // Variant: Horizontal (Default)
  return (
    <div
      data-brand-logo="v2"
      data-testid={testId}
      className={`inline-flex items-center ${gapClass} ${onClick ? 'cursor-pointer' : ''} ${className}`}
      onClick={onClick}
    >
      <LogoMark
        tone={tone}
        size={markSize}
        title={title}
        animated={animated}
      />

      <div className="flex flex-col justify-center">
        {animated ? (
          <motion.span
            initial={prefersReduced ? false : { opacity: 0, x: -6 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.4, ease: [0.22, 1, 0.36, 1] }}
            className={`cf-display font-bold tracking-tight leading-none ${textClass} ${textToneClass}`}
          >
            CareerFlow
          </motion.span>
        ) : (
          <span className={`cf-display font-bold tracking-tight leading-none ${textClass} ${textToneClass}`}>
            CareerFlow
          </span>
        )}

        {subtitle && (
          <span className={`font-medium tracking-normal mt-0.5 leading-none ${subTextClass} ${subToneClass}`}>
            {subtitle}
          </span>
        )}
      </div>
    </div>
  );
}

