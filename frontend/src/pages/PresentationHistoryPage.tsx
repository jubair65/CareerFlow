import { VideoHistory } from './VideoHistory';
import { type Notify } from '../components/dashboard/DashboardShared';

export function PresentationHistoryPage({ notify }: { notify: Notify }) {
  return <VideoHistory notify={notify} />;
}

export default PresentationHistoryPage;
