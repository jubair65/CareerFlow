import { useEffect, useState, useRef } from 'react';

interface ScoreCounterProps {
  value: number;
  duration?: number; // in milliseconds
  delay?: number; // in milliseconds
  className?: string;
  suffix?: string;
}

export function ScoreCounter({
  value,
  duration = 1600,
  delay = 200,
  className = '',
  suffix = '',
}: ScoreCounterProps) {
  const [currentValue, setCurrentValue] = useState(0);
  const startTimeRef = useRef<number | null>(null);
  const frameRef = useRef<number | null>(null);

  useEffect(() => {
    let timeoutId: NodeJS.Timeout;

    const animate = (timestamp: number) => {
      if (!startTimeRef.current) startTimeRef.current = timestamp;
      const elapsed = timestamp - startTimeRef.current;
      const progress = Math.min(elapsed / duration, 1);

      // Ease out quint: 1 - Math.pow(1 - progress, 5)
      const easeProgress = 1 - Math.pow(1 - progress, 5);
      const nextVal = Math.round(easeProgress * value);

      setCurrentValue(nextVal);

      if (progress < 1) {
        frameRef.current = requestAnimationFrame(animate);
      }
    };

    timeoutId = setTimeout(() => {
      startTimeRef.current = null;
      frameRef.current = requestAnimationFrame(animate);
    }, delay);

    return () => {
      clearTimeout(timeoutId);
      if (frameRef.current) cancelAnimationFrame(frameRef.current);
    };
  }, [value, duration, delay]);

  return (
    <span className={className}>
      {currentValue}
      {suffix}
    </span>
  );
}

