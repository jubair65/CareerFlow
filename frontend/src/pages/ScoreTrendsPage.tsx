import { useLocation } from 'wouter';
import { ArrowLeft, TrendingUp, Video as VideoIcon } from 'lucide-react';
import { AppShell } from '../components/layout/AppShell';
import { ScoreTrendsDashboard } from '../components/presentation/ScoreTrendsDashboard';
import { type Notify } from '../components/dashboard/DashboardShared';

export function ScoreTrendsPage({ notify }: { notify: Notify }) {
  const [, setLocation] = useLocation();

  return (
    <AppShell activeTab="videos">
      <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
        {/* Navigation Breadcrumbs & Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setLocation('/student/videos')}
              className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg border border-[#d9dbd1] bg-[#f4f6ef] hover:bg-[#ecefe7] text-[#526072] hover:text-[#253142] transition-all text-sm font-medium shadow-xs cursor-pointer"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Video Takes
            </button>
            <span className="text-[#d9dbd1]">|</span>
            <span className="text-sm font-semibold text-[#253142] flex items-center gap-1.5">
              <TrendingUp className="w-4 h-4 text-[#277254]" />
              Historical Analytics
            </span>
          </div>

          <button
            onClick={() => setLocation('/student/videos')}
            className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg border border-[#b8d8c7] bg-[#e2f0e9] hover:bg-[#d0e8db] text-[#277254] transition-all text-xs font-semibold self-start sm:self-auto cursor-pointer"
          >
            <VideoIcon className="w-3.5 h-3.5" />
            View All Video Takes
          </button>
        </div>

        {/* Score Trends Analytics Dashboard */}
        <ScoreTrendsDashboard notify={notify} />
      </div>
    </AppShell>
  );
}

export default ScoreTrendsPage;
