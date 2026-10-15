import React from 'react';
import {
  X,
  CheckCircle2,
  AlertCircle,
  FileText,
  Download,
  Calendar,
  Sparkles,
  TrendingUp,
  Award,
  Layers,
  Users2,
  ShieldCheck,
  Compass,
} from 'lucide-react';
import type { ApplicantCvScoreItem } from '../../api/recruitment';

interface CvSkillBreakdownModalProps {
  isOpen: boolean;
  onClose: () => void;
  applicant: ApplicantCvScoreItem | null;
  roomTitle?: string;
}

export function CvSkillBreakdownModal({
  isOpen,
  onClose,
  applicant,
  roomTitle,
}: CvSkillBreakdownModalProps) {
  if (!isOpen || !applicant) return null;

  const score = applicant.match_score ?? 0;
  const hasScore = applicant.has_score && applicant.match_score !== null;

  // Determine score color tier
  const getScoreTheme = (s: number) => {
    if (s >= 75) {
      return {
        text: 'text-[#1f5b43]',
        bg: 'bg-[#e2f0e9]',
        border: 'border-[#a7d7c1]',
        bar: 'bg-[#277254]',
        label: 'Strong Match',
      };
    }
    if (s >= 50) {
      return {
        text: 'text-[#b47d00]',
        bg: 'bg-[#fff5db]',
        border: 'border-[#f9e09d]',
        bar: 'bg-[#f5c84b]',
        label: 'Moderate Match',
      };
    }
    return {
      text: 'text-[#b34a40]',
      bg: 'bg-[#fbe9e7]',
      border: 'border-[#f3bbb5]',
      bar: 'bg-[#b34a40]',
      label: 'Low Match',
    };
  };

  const scoreTheme = getScoreTheme(score);

  const categories = [
    {
      key: 'domain_craft',
      label: 'Domain & Craft',
      icon: Layers,
      score: applicant.category_scores?.domain_craft ?? 75,
      description: 'Technical breadth, stack relevance & practical engineering depth',
    },
    {
      key: 'collaboration',
      label: 'Collaboration',
      icon: Users2,
      score: applicant.category_scores?.collaboration ?? 75,
      description: 'Cross-functional teamwork, agility & communication presence',
    },
    {
      key: 'leadership',
      label: 'Ownership & Scope',
      icon: Compass,
      score: applicant.category_scores?.leadership ?? 70,
      description: 'Project initiative, strategic decision-making & mentor impact',
    },
    {
      key: 'accessibility',
      label: 'Standards & Quality',
      icon: ShieldCheck,
      score: applicant.category_scores?.accessibility ?? 65,
      description: 'Security, testing discipline, documentation & accessibility',
    },
  ];

  return (
    <div
      role="dialog"
      aria-modal="true"
      data-testid="modal-cv-skill-breakdown"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 overflow-y-auto animate-in fade-in"
    >
      <div className="relative w-full max-w-2xl rounded-2xl bg-white border border-[#d9dbd1] shadow-2xl my-8 overflow-hidden">
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-[#eef0e7] px-6 py-4 bg-[#fbfaf5]">
          <div className="flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-xl bg-[#277254] text-white shadow-xs">
              <Sparkles size={20} />
            </div>
            <div>
              <div className="text-[11px] font-bold uppercase tracking-wider text-[#7b8490]">
                US-10 • CV Match Breakdown
              </div>
              <h2 className="text-base font-bold text-[#253142]" data-testid="text-breakdown-candidate-name">
                {applicant.candidate_name || applicant.candidate_email}
              </h2>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            data-testid="button-close-cv-breakdown"
            className="rounded-xl p-1.5 text-[#7b8490] hover:bg-[#eef0e7] hover:text-[#253142] transition"
          >
            <X size={18} />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-6 max-h-[80vh] overflow-y-auto">
          {/* Candidate & Role Sub-header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 rounded-xl bg-[#f8f9fa] border border-[#eef0e7] p-4 text-xs">
            <div className="space-y-1">
              <div className="text-[#7b8490]">Target Role:</div>
              <div className="font-bold text-[#253142] text-sm">
                {roomTitle || 'Recruitment Room Opening'}
              </div>
              <div className="text-[11px] text-[#7b8490] flex items-center gap-1.5">
                <Calendar size={12} />
                <span>Applied {new Date(applicant.applied_at).toLocaleDateString()}</span>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {applicant.cv_filename ? (
                <div className="flex items-center gap-2 rounded-lg bg-white border border-[#d9dbd1] px-3 py-1.5 shadow-2xs">
                  <FileText size={14} className="text-[#277254]" />
                  <span className="font-medium text-[#253142] truncate max-w-[150px]">
                    {applicant.cv_filename}
                  </span>
                  {applicant.cv_file_url && (
                    <a
                      href={applicant.cv_file_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      title="Download uploaded CV"
                      className="text-[#277254] hover:text-[#1f5b43]"
                    >
                      <Download size={13} />
                    </a>
                  )}
                </div>
              ) : (
                <span className="rounded-lg bg-[#f1f3f5] px-2.5 py-1 text-[11px] text-[#687382] italic">
                  No CV Uploaded
                </span>
              )}
            </div>
          </div>

          {/* Top Score Banner */}
          {hasScore ? (
            <div
              className={`rounded-2xl border p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${scoreTheme.bg} ${scoreTheme.border}`}
              data-testid="card-cv-overall-score"
            >
              <div className="flex items-center gap-4">
                <div
                  className="grid h-16 w-16 place-items-center rounded-2xl bg-white shadow-xs border border-black/5"
                  data-testid="badge-overall-match-score"
                >
                  <span className={`text-2xl font-black ${scoreTheme.text}`}>{score}%</span>
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-[#253142]">Overall CV Match Score</span>
                    <span
                      className={`rounded-md px-2 py-0.5 text-[10px] font-bold ${scoreTheme.bg} ${scoreTheme.text} border ${scoreTheme.border}`}
                    >
                      {scoreTheme.label}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-[#526072]">
                    Semantic fit based on skills, NLP content embeddings, and requirement taxonomy.
                  </p>
                </div>
              </div>

              {/* Keyword Coverage Pill */}
              <div className="rounded-xl bg-white/90 border border-black/5 p-3 sm:text-right shrink-0">
                <div className="text-[11px] text-[#7b8490] font-medium">Keyword Coverage</div>
                <div className="text-lg font-bold text-[#253142]">
                  {applicant.keyword_coverage}%
                </div>
                <div className="text-[10px] text-[#7b8490]">
                  {applicant.skills_matched.length} matched / {applicant.skills_matched.length + applicant.skills_missing.length} required
                </div>
              </div>
            </div>
          ) : (
            <div className="rounded-xl bg-[#fff5db] border border-[#f9e09d] p-4 text-xs text-[#8a6100] flex items-center gap-3">
              <AlertCircle size={20} className="shrink-0 text-[#b47d00]" />
              <div>
                <span className="font-bold">Evaluation Pending or Incomplete:</span> This applicant does not yet have a computed CV match score.
              </div>
            </div>
          )}

          {/* Sub-Signal Category Breakdown */}
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-[#7b8490] mb-3">
              Competency & Signal Breakdown
            </h3>
            <div className="grid gap-3 sm:grid-cols-2" data-testid="grid-signal-categories">
              {categories.map((cat) => {
                const CatIcon = cat.icon;
                return (
                  <div
                    key={cat.key}
                    className="rounded-xl border border-[#eef0e7] bg-[#fbfaf5] p-3.5 space-y-2"
                  >
                    <div className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2 font-bold text-[#253142]">
                        <CatIcon size={14} className="text-[#277254]" />
                        <span>{cat.label}</span>
                      </div>
                      <span className="font-bold text-[#277254]">{cat.score}%</span>
                    </div>
                    {/* Progress Bar */}
                    <div className="h-1.5 w-full rounded-full bg-[#eef0e7] overflow-hidden">
                      <div
                        className="h-full rounded-full bg-[#277254] transition-all duration-500"
                        style={{ width: `${Math.min(100, Math.max(0, cat.score))}%` }}
                      />
                    </div>
                    <p className="text-[10px] text-[#7b8490] leading-tight">{cat.description}</p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Matched & Missing Skills Grid */}
          <div className="grid gap-4 sm:grid-cols-2">
            {/* Matched Skills */}
            <div className="rounded-xl border border-[#c4e3d3] bg-[#f0f7f3] p-4 space-y-3" data-testid="card-matched-skills">
              <div className="flex items-center gap-2 text-xs font-bold text-[#1f5b43]">
                <CheckCircle2 size={15} />
                <span>Matched Skills ({applicant.skills_matched.length})</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {applicant.skills_matched.length > 0 ? (
                  applicant.skills_matched.map((sk, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-1 rounded-md bg-white border border-[#a7d7c1] px-2 py-1 text-xs font-semibold text-[#1f5b43] shadow-2xs"
                    >
                      <CheckCircle2 size={11} className="text-[#277254]" />
                      {sk}
                    </span>
                  ))
                ) : (
                  <span className="text-xs text-[#7b8490] italic">No directly matching skills found</span>
                )}
              </div>
            </div>

            {/* Missing Skills */}
            <div className="rounded-xl border border-[#f3bbb5] bg-[#fdf2f0] p-4 space-y-3" data-testid="card-missing-skills">
              <div className="flex items-center gap-2 text-xs font-bold text-[#b34a40]">
                <AlertCircle size={15} />
                <span>Missing Skills ({applicant.skills_missing.length})</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {applicant.skills_missing.length > 0 ? (
                  applicant.skills_missing.map((sk, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-1 rounded-md bg-white border border-[#f3bbb5] px-2 py-1 text-xs font-semibold text-[#b34a40] shadow-2xs"
                    >
                      <AlertCircle size={11} className="text-[#b34a40]" />
                      {sk}
                    </span>
                  ))
                ) : (
                  <span className="text-xs text-[#277254] font-medium">All required skills matched!</span>
                )}
              </div>
            </div>
          </div>

          {/* Strengths & Gaps Insights */}
          {(applicant.strengths.length > 0 || applicant.gaps.length > 0) && (
            <div className="rounded-xl border border-[#eef0e7] bg-white p-4 space-y-3">
              <div className="flex items-center gap-1.5 text-xs font-bold text-[#253142]">
                <TrendingUp size={14} className="text-[#277254]" />
                <span>AI Evaluation Insights</span>
              </div>
              <div className="space-y-2 text-xs">
                {applicant.strengths.map((str, idx) => (
                  <div key={idx} className="flex items-start gap-2 text-[#253142]">
                    <span className="text-[#277254] font-bold">•</span>
                    <span>{str}</span>
                  </div>
                ))}
                {applicant.gaps.map((gap, idx) => (
                  <div key={idx} className="flex items-start gap-2 text-[#7b8490]">
                    <span className="text-[#b47d00] font-bold">•</span>
                    <span>{gap}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="border-t border-[#eef0e7] px-6 py-3.5 bg-[#fbfaf5] flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl bg-[#253142] px-4 py-2 text-xs font-bold text-white hover:bg-[#344458] transition shadow-xs"
          >
            Close Breakdown
          </button>
        </div>
      </div>
    </div>
  );
}
