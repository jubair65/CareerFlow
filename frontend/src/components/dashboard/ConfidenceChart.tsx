import { useState, useMemo, useRef } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { Presentation, ArrowRight } from 'lucide-react';
import { DASHBOARD_MOTION } from './motionTokens';

export interface ChartDataPoint {
  attempt: number;
  score: number;
  date: string;
  fullDate?: string;
  grade?: string;
}

interface ConfidenceChartProps {
  points: ChartDataPoint[];
  onStartPractice?: () => void;
}

export function ConfidenceChart({ points, onStartPractice }: ConfidenceChartProps) {
  const prefersReducedMotion = useReducedMotion();
  const svgRef = useRef<SVGSVGElement | null>(null);
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  // SVG Coordinate metrics
  const viewBoxWidth = 600;
  const viewBoxHeight = 210;
  const paddingLeft = 45;
  const paddingRight = 25;
  const paddingTop = 20;
  const paddingBottom = 35;

  const chartWidth = viewBoxWidth - paddingLeft - paddingRight;
  const chartHeight = viewBoxHeight - paddingTop - paddingBottom;

  const yTicks = [100, 75, 50, 25, 0];

  const coords = useMemo(() => {
    if (points.length === 0) return [];
    if (points.length === 1) {
      const p = points[0];
      const cx = paddingLeft + chartWidth / 2;
      const cy = paddingTop + (1 - Math.max(0, Math.min(100, p.score)) / 100) * chartHeight;
      return [{ ...p, cx, cy, idx: 0 }];
    }
    return points.map((p, i) => {
      const cx = paddingLeft + (i / (points.length - 1)) * chartWidth;
      const cy = paddingTop + (1 - Math.max(0, Math.min(100, p.score)) / 100) * chartHeight;
      return { ...p, cx, cy, idx: i };
    });
  }, [points, chartWidth, chartHeight, paddingLeft, paddingTop]);

  const pathD = useMemo(() => {
    if (coords.length < 2) return '';
    return coords.reduce((acc, curr, idx) => {
      if (idx === 0) return `M ${curr.cx.toFixed(1)} ${curr.cy.toFixed(1)}`;
      return `${acc} L ${curr.cx.toFixed(1)} ${curr.cy.toFixed(1)}`;
    }, '');
  }, [coords]);

  const areaD = useMemo(() => {
    if (coords.length < 2) return '';
    const first = coords[0];
    const last = coords[coords.length - 1];
    const bottomY = paddingTop + chartHeight;
    return `${pathD} L ${last.cx.toFixed(1)} ${bottomY} L ${first.cx.toFixed(1)} ${bottomY} Z`;
  }, [coords, pathD, paddingTop, chartHeight]);

  // Handle hover tracking
  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    if (coords.length < 2 || !svgRef.current) return;
    const rect = svgRef.current.getBoundingClientRect();
    const mouseX = ((e.clientX - rect.left) / rect.width) * viewBoxWidth;

    let closestIdx = 0;
    let closestDist = Infinity;
    coords.forEach((c, idx) => {
      const dist = Math.abs(c.cx - mouseX);
      if (dist < closestDist) {
        closestDist = dist;
        closestIdx = idx;
      }
    });

    setHoveredIdx(closestIdx);
  };

  const handleMouseLeave = () => {
    setHoveredIdx(null);
  };

  // 0 Points: Empty state
  if (points.length === 0) {
    return (
      <div
        data-testid="confidence-chart-empty"
        className="flex h-52 flex-col items-center justify-center rounded-xl border border-dashed border-[#d9dbd1] bg-[#faf8f2] p-6 text-center"
      >
        <div className="grid h-10 w-10 place-items-center rounded-xl bg-[#fff1c9] text-[#8a6a16] mb-2">
          <Presentation size={20} />
        </div>
        <p className="text-sm font-bold text-[#253142]">No practice sessions recorded yet</p>
        <p className="mt-1 text-xs text-[#7b8490] max-w-sm">
          Record your first presentation take to establish your baseline and start tracking confidence trends over time.
        </p>
        {onStartPractice && (
          <button
            type="button"
            onClick={onStartPractice}
            className="mt-3.5 inline-flex items-center gap-1.5 rounded-xl bg-[#f5c84b] px-4 py-2 text-xs font-bold text-[#253142] hover:bg-[#e8b93c] transition shadow-xs cursor-pointer focus-visible:outline-2 focus-visible:outline-[#253142]"
          >
            Start practice take <ArrowRight size={14} />
          </button>
        )}
      </div>
    );
  }

  // 1 Point: Single dot state with helpful message
  if (points.length === 1) {
    const single = coords[0];
    return (
      <div data-testid="confidence-chart-single" className="relative flex flex-col items-center w-full">
        <svg
          ref={svgRef}
          viewBox={`0 0 ${viewBoxWidth} ${viewBoxHeight}`}
          className="w-full h-48 select-none overflow-visible"
        >
          {/* Gridlines & Y-Axis */}
          {yTicks.map((tick) => {
            const y = paddingTop + (1 - tick / 100) * chartHeight;
            return (
              <g key={`single-grid-${tick}`}>
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
                  x={paddingLeft - 10}
                  y={y + 3.5}
                  textAnchor="end"
                  className="text-[10px] font-semibold fill-[#8d9aab]"
                >
                  {tick}
                </text>
              </g>
            );
          })}

          {/* Baseline axis */}
          <line
            x1={paddingLeft}
            y1={paddingTop + chartHeight}
            x2={viewBoxWidth - paddingRight}
            y2={paddingTop + chartHeight}
            stroke="#d9dbd1"
            strokeWidth="1"
          />

          {/* Pulsing ring for single dot */}
          {!prefersReducedMotion && (
            <circle
              cx={single.cx}
              cy={single.cy}
              r={12}
              fill="none"
              stroke="#f5c84b"
              strokeWidth="2.5"
              className="chart-single-pulse"
            />
          )}

          {/* Single Data Dot */}
          <circle
            cx={single.cx}
            cy={single.cy}
            r={6}
            fill="#f5c84b"
            stroke="#253142"
            strokeWidth={2.5}
          />

          {/* Single Point Label */}
          <g transform={`translate(${single.cx}, ${single.cy - 16})`}>
            <rect
              x="-48"
              y="-18"
              width="96"
              height="22"
              rx="6"
              fill="#253142"
              className="drop-shadow-xs"
            />
            <text
              x="0"
              y="-4"
              textAnchor="middle"
              className="text-[11px] font-bold fill-[#faf7ef]"
            >
              Take 1 • {single.score}/100
            </text>
          </g>

          {/* X Date Label */}
          <text
            x={single.cx}
            y={viewBoxHeight - 8}
            textAnchor="middle"
            className="text-[11px] font-semibold fill-[#687382]"
          >
            {single.fullDate || single.date}
          </text>
        </svg>

        {/* Informative Trend Guidance banner */}
        <div className="mt-2 flex items-center justify-between gap-3 w-full rounded-xl bg-[#faf8f2] border border-[#e8e6dc] px-4 py-2.5">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-[#f5c84b]" />
            <span className="text-xs font-semibold text-[#526072]">
              Add a second take to see your trend.
            </span>
          </div>
          {onStartPractice && (
            <button
              type="button"
              onClick={onStartPractice}
              className="text-xs font-bold text-[#277254] hover:underline inline-flex items-center gap-1 cursor-pointer"
            >
              Record take #2 →
            </button>
          )}
        </div>
      </div>
    );
  }

  // 2+ Points: Interactive SVG Line Chart
  const activeCoord = hoveredIdx !== null ? coords[hoveredIdx] : null;

  return (
    <div
      data-testid="confidence-chart-multi"
      className="relative w-full"
      onMouseLeave={handleMouseLeave}
    >
      <svg
        ref={svgRef}
        viewBox={`0 0 ${viewBoxWidth} ${viewBoxHeight}`}
        onMouseMove={handleMouseMove}
        className="w-full h-48 select-none overflow-visible cursor-crosshair"
      >
        <defs>
          <linearGradient id="chartAreaGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#277254" stopOpacity="0.12" />
            <stop offset="100%" stopColor="#277254" stopOpacity="0.00" />
          </linearGradient>
        </defs>

        {/* Gridlines & Y-Axis */}
        {yTicks.map((tick) => {
          const y = paddingTop + (1 - tick / 100) * chartHeight;
          return (
            <g key={`multi-grid-${tick}`}>
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
                x={paddingLeft - 10}
                y={y + 3.5}
                textAnchor="end"
                className="text-[10px] font-semibold fill-[#8d9aab]"
              >
                {tick}
              </text>
            </g>
          );
        })}

        {/* Baseline axis */}
        <line
          x1={paddingLeft}
          y1={paddingTop + chartHeight}
          x2={viewBoxWidth - paddingRight}
          y2={paddingTop + chartHeight}
          stroke="#d9dbd1"
          strokeWidth="1"
        />

        {/* Subtle Area Fill */}
        {areaD && (
          <path
            d={areaD}
            fill="url(#chartAreaGradient)"
            className="transition-opacity duration-300 pointer-events-none"
          />
        )}

        {/* Animated Line Draw */}
        {prefersReducedMotion ? (
          <path
            d={pathD}
            fill="none"
            stroke="#277254"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        ) : (
          <motion.path
            d={pathD}
            fill="none"
            stroke="#277254"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{
              duration: DASHBOARD_MOTION.duration.chartDraw,
              ease: DASHBOARD_MOTION.easeOutQuint,
            }}
          />
        )}

        {/* Crosshair on hover */}
        {activeCoord && (
          <g className="pointer-events-none">
            <line
              x1={activeCoord.cx}
              y1={paddingTop}
              x2={activeCoord.cx}
              y2={paddingTop + chartHeight}
              stroke="#253142"
              strokeWidth="1.2"
              strokeDasharray="3 3"
              strokeOpacity="0.6"
            />
          </g>
        )}

        {/* Interactive Data Dots */}
        {coords.map((coord, i) => {
          const isHovered = hoveredIdx === i;
          return (
            <g key={`chart-dot-${coord.attempt}-${i}`}>
              {/* Invisible larger hover hit area */}
              <circle
                cx={coord.cx}
                cy={coord.cy}
                r={16}
                fill="transparent"
                className="cursor-pointer"
                onMouseEnter={() => setHoveredIdx(i)}
              />

              {/* Visible dot */}
              {prefersReducedMotion ? (
                <circle
                  cx={coord.cx}
                  cy={coord.cy}
                  r={isHovered ? 6 : 4.5}
                  fill={isHovered ? '#253142' : '#f5c84b'}
                  stroke={isHovered ? '#f5c84b' : '#253142'}
                  strokeWidth={2}
                  className="transition-all duration-150"
                />
              ) : (
                <motion.circle
                  cx={coord.cx}
                  cy={coord.cy}
                  r={isHovered ? 6 : 4.5}
                  fill={isHovered ? '#253142' : '#f5c84b'}
                  stroke={isHovered ? '#f5c84b' : '#253142'}
                  strokeWidth={2}
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{
                    delay: 0.35 + i * DASHBOARD_MOTION.stagger.statCards,
                    duration: DASHBOARD_MOTION.duration.component,
                    ease: DASHBOARD_MOTION.easeOutQuint,
                  }}
                  className="transition-colors duration-150"
                />
              )}

              {/* X Date Label */}
              <text
                x={coord.cx}
                y={viewBoxHeight - 8}
                textAnchor="middle"
                className={`text-[10px] font-semibold transition-colors duration-150 ${
                  isHovered ? 'fill-[#253142] font-bold' : 'fill-[#7b8490]'
                }`}
              >
                {coord.date}
              </text>
            </g>
          );
        })}

        {/* Active Tooltip */}
        {activeCoord && (
          <g
            transform={`translate(${
              // Keep tooltip within bounds
              Math.min(
                Math.max(activeCoord.cx, paddingLeft + 55),
                viewBoxWidth - paddingRight - 55
              )
            }, ${Math.max(activeCoord.cy - 22, paddingTop + 10)})`}
            className="pointer-events-none drop-shadow-sm transition-transform duration-100 ease-out"
          >
            <rect
              x="-55"
              y="-28"
              width="110"
              height="36"
              rx="8"
              fill="#253142"
            />
            <text
              x="0"
              y="-13"
              textAnchor="middle"
              className="text-[11px] font-bold fill-[#faf7ef]"
            >
              Take #{activeCoord.attempt}: {activeCoord.score}/100
            </text>
            <text
              x="0"
              y="-2"
              textAnchor="middle"
              className="text-[9px] font-medium fill-[#b7c0cc]"
            >
              {activeCoord.fullDate || activeCoord.date}
            </text>
          </g>
        )}
      </svg>
    </div>
  );
}

