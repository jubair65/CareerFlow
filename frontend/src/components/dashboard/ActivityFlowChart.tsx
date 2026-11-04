import { useState, useMemo, useEffect, useRef } from 'react';
import { useReducedMotion } from 'framer-motion';
import { BarChart3 } from 'lucide-react';

export interface ActivityDataPoint {
  label: string;
  count: number;
  dateStr?: string;
}

interface ActivityFlowChartProps {
  data: ActivityDataPoint[];
  color?: string;
  unit?: string;
  emptyMessage?: string;
}

export function ActivityFlowChart({
  data,
  color = '#277254',
  unit = 'applicants',
  emptyMessage = 'No applicant activity in the last 7 days.',
}: ActivityFlowChartProps) {
  const prefersReduced = useReducedMotion();
  const [mounted, setMounted] = useState(false);
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    // Mount trigger for smooth CSS entrance transitions
    const timer = setTimeout(() => setMounted(true), 60);
    return () => clearTimeout(timer);
  }, []);

  const viewBoxWidth = 560;
  const viewBoxHeight = 190;
  const paddingLeft = 36;
  const paddingRight = 20;
  const paddingTop = 22;
  const paddingBottom = 32;

  const chartWidth = viewBoxWidth - paddingLeft - paddingRight;
  const chartHeight = viewBoxHeight - paddingTop - paddingBottom;
  const baselineY = paddingTop + chartHeight;

  const maxCount = useMemo(() => {
    const highest = Math.max(...data.map((d) => d.count), 0);
    if (highest <= 4) return 4;
    if (highest <= 10) return 10;
    if (highest <= 20) return 20;
    return Math.ceil(highest / 10) * 10;
  }, [data]);

  const yTicks = useMemo(() => {
    return [maxCount, Math.round(maxCount / 2), 0];
  }, [maxCount]);

  const isAllZero = data.length === 0 || data.every((d) => d.count === 0);

  const barWidth = useMemo(() => {
    if (data.length === 0) return 32;
    const available = chartWidth / data.length;
    return Math.min(Math.max(available * 0.48, 18), 38);
  }, [chartWidth, data.length]);

  const bars = useMemo(() => {
    return data.map((d, i) => {
      const colWidth = chartWidth / data.length;
      const x = paddingLeft + i * colWidth + (colWidth - barWidth) / 2;
      const ratio = maxCount > 0 ? d.count / maxCount : 0;
      const targetHeight = Math.max(ratio * chartHeight, d.count > 0 ? 6 : 0);
      const targetY = baselineY - targetHeight;
      return {
        ...d,
        x,
        targetY,
        targetHeight,
        idx: i,
        centerX: x + barWidth / 2,
      };
    });
  }, [data, chartWidth, barWidth, paddingLeft, baselineY, chartHeight, maxCount]);

  if (isAllZero) {
    return (
      <div
        data-testid="flow-chart-empty"
        className="flex h-44 flex-col items-center justify-center rounded-xl border border-dashed border-[#d9dbd1] bg-[#faf8f2] p-6 text-center"
      >
        <div className="grid h-9 w-9 place-items-center rounded-xl bg-[#eef0e7] text-[#687382] mb-2">
          <BarChart3 size={18} />
        </div>
        <p className="text-xs font-bold text-[#253142]">{emptyMessage}</p>
        <p className="mt-1 text-[11px] text-[#7b8490] max-w-xs">
          New candidate evaluations and room submissions will plot here across your 7-day pipeline.
        </p>
      </div>
    );
  }

  const activeBar = hoveredIdx !== null ? bars[hoveredIdx] : null;

  return (
    <div
      ref={containerRef}
      data-testid="activity-flow-chart"
      className="relative w-full overflow-hidden"
      onMouseLeave={() => setHoveredIdx(null)}
    >
      <svg
        viewBox={`0 0 ${viewBoxWidth} ${viewBoxHeight}`}
        className="w-full h-44 select-none overflow-hidden"
      >
        {/* Horizontal Dashed Gridlines */}
        {yTicks.map((tick) => {
          const y = paddingTop + (1 - tick / maxCount) * chartHeight;
          return (
            <g key={`flow-grid-${tick}`}>
              <line
                x1={paddingLeft}
                y1={y}
                x2={viewBoxWidth - paddingRight}
                y2={y}
                stroke="#e8e6dc"
                strokeWidth="1"
                strokeDasharray="4 4"
              />
              <text
                x={paddingLeft - 8}
                y={y + 3.5}
                textAnchor="end"
                className="text-[10px] font-semibold fill-[#8d9aab]"
              >
                {tick}
              </text>
            </g>
          );
        })}

        {/* Bottom baseline axis */}
        <line
          x1={paddingLeft}
          y1={baselineY}
          x2={viewBoxWidth - paddingRight}
          y2={baselineY}
          stroke="#d9dbd1"
          strokeWidth="1"
        />

        {/* Bars and Hit Areas */}
        {bars.map((bar, i) => {
          const isHovered = hoveredIdx === i;
          const currentHeight = mounted || prefersReduced ? bar.targetHeight : 0;
          const currentY = mounted || prefersReduced ? bar.targetY : baselineY;

          return (
            <g key={`flow-bar-${bar.label}-${i}`}>
              {/* Invisible Hit Area for smooth hover */}
              <rect
                x={bar.x - 8}
                y={paddingTop}
                width={barWidth + 16}
                height={chartHeight + 10}
                fill="transparent"
                className="cursor-pointer"
                onMouseEnter={() => setHoveredIdx(i)}
                onMouseLeave={() => {
                  if (hoveredIdx === i) setHoveredIdx(null);
                }}
              />

              {/* Bar Column Background slot */}
              <rect
                x={bar.x}
                y={paddingTop}
                width={barWidth}
                height={chartHeight}
                rx={4}
                fill="#f3f1ea"
                opacity={0.5}
                className="pointer-events-none"
              />

              {/* Main SVG Bar (Pure native SVG attributes, strictly no CSS transform translateY) */}
              {bar.count > 0 && (
                <rect
                  x={bar.x}
                  y={currentY}
                  width={barWidth}
                  height={currentHeight}
                  rx={4}
                  fill={isHovered ? '#f5c84b' : color}
                  className="pointer-events-none"
                  style={{
                    transition: prefersReduced
                      ? 'none'
                      : `height 0.45s cubic-bezier(0.22, 1, 0.36, 1) ${i * 45}ms, y 0.45s cubic-bezier(0.22, 1, 0.36, 1) ${i * 45}ms, fill 0.15s ease`,
                  }}
                />
              )}

              {/* X Axis Day Label */}
              <text
                x={bar.centerX}
                y={viewBoxHeight - 8}
                textAnchor="middle"
                className={`text-[10px] font-semibold transition-colors duration-150 pointer-events-none ${
                  isHovered ? 'fill-[#253142] font-bold' : 'fill-[#7b8490]'
                }`}
              >
                {bar.label}
              </text>
            </g>
          );
        })}

        {/* Hover Tooltip (Only renders when active bar has count > 0) */}
        {activeBar && activeBar.count > 0 && (
          <g
            transform={`translate(${activeBar.centerX}, ${Math.max(activeBar.targetY - 14, paddingTop + 6)})`}
            className="pointer-events-none"
          >
            <rect
              x="-46"
              y="-20"
              width="92"
              height="22"
              rx="6"
              fill="#253142"
              className="drop-shadow-xs"
            />
            <text
              x="0"
              y="-5"
              textAnchor="middle"
              className="text-[10px] font-bold fill-[#faf7ef]"
            >
              {activeBar.count} {activeBar.count === 1 ? unit.replace(/s$/, '') : unit}
            </text>
          </g>
        )}
      </svg>
    </div>
  );
}
