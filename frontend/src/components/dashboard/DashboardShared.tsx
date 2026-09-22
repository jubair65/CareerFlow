import type { ReactNode } from 'react';
import type { LucideIcon } from 'lucide-react';

export type Role = 'student' | 'hr' | 'agency';
export type Notify = (message: string, tone?: 'success' | 'info' | 'error') => void;

export type CandidateStatus = 'New' | 'Reviewing' | 'Shortlisted' | 'Rejected';

export type Candidate = {
  id: string;
  name: string;
  email: string;
  skills: string[];
  education: string;
  experience: string;
  cvScore: number;
  videoScore: number;
  overallScore: number;
  status: CandidateStatus;
  company: string;
  position: string;
  appliedAt: string;
};

export type Room = {
  id: string;
  title: string;
  company: string;
  description: string;
  requiredSkills: string[];
  education: string;
  experience: string;
  cvWeight: number;
  videoWeight: number;
  minimumScore: number;
  shortlistCount: number;
  status: 'Active' | 'Draft' | 'Closed';
  slug: string;
};

export type Application = {
  id: string;
  candidateId: string;
  roomId: string;
  job: string;
  company: string;
  cvScore: number;
  videoScore: number;
  overallScore: number;
  status: CandidateStatus;
  appliedAt: string;
};

export type Client = {
  id: string;
  companyName: string;
  industry: string;
  contactPerson: string;
  contactEmail: string;
  status: 'Active' | 'Onboarding';
};

export const candidatesSeed: Candidate[] = [
  { id: 'cand-1', name: 'Alex Rahman', email: 'alex.rahman@mail.com', skills: ['React', 'TypeScript', 'Design systems'], education: 'BSc Computer Science — BRAC University', experience: '2 years', cvScore: 92, videoScore: 86, overallScore: 89, status: 'Shortlisted', company: 'TechNova Ltd.', position: 'Frontend Developer', appliedAt: 'Today, 9:24 AM' },
  { id: 'cand-2', name: 'Sara Ahmed', email: 'sara.ahmed@mail.com', skills: ['Python', 'Django', 'PostgreSQL'], education: 'BSc Software Engineering — NSU', experience: '3 years', cvScore: 88, videoScore: 79, overallScore: 84, status: 'Reviewing', company: 'BrightStack Solutions', position: 'Backend Developer', appliedAt: 'Yesterday' },
  { id: 'cand-3', name: 'Tanvir Hasan', email: 'tanvir.hasan@mail.com', skills: ['Figma', 'UX research', 'Prototyping'], education: 'BFA Visual Communication — ULAB', experience: '4 years', cvScore: 84, videoScore: 91, overallScore: 88, status: 'New', company: 'Vertex Digital', position: 'UI/UX Designer', appliedAt: 'May 18, 2024' },
  { id: 'cand-4', name: 'Nusrat Jahan', email: 'nusrat.jahan@mail.com', skills: ['Excel', 'SQL', 'Tableau'], education: 'BSc Statistics — University of Dhaka', experience: '1 year', cvScore: 81, videoScore: 83, overallScore: 82, status: 'Shortlisted', company: 'NextGen Labs', position: 'Data Analyst', appliedAt: 'May 17, 2024' },
  { id: 'cand-5', name: 'Fahim Karim', email: 'fahim.karim@mail.com', skills: ['Node.js', 'AWS', 'MongoDB'], education: 'BSc CSE — AIUB', experience: '2 years', cvScore: 76, videoScore: 73, overallScore: 75, status: 'Rejected', company: 'BrightStack Solutions', position: 'Backend Developer', appliedAt: 'May 15, 2024' },
  { id: 'cand-6', name: 'Mehedi Hasan', email: 'mehedi.hasan@mail.com', skills: ['React', 'Next.js', 'Jest'], education: 'BSc CSE — Daffodil International University', experience: '1 year', cvScore: 79, videoScore: 88, overallScore: 84, status: 'Reviewing', company: 'TechNova Ltd.', position: 'Frontend Developer', appliedAt: 'May 14, 2024' },
];

export const roomsSeed: Room[] = [
  { id: 'room-1', title: 'Frontend Developer', company: 'TechNova Ltd.', description: 'Build calm, useful tools for the next generation of teams.', requiredSkills: ['React', 'TypeScript', 'Accessibility'], education: 'Bachelor degree in Computer Science or equivalent', experience: '2+ years', cvWeight: 45, videoWeight: 55, minimumScore: 72, shortlistCount: 4, status: 'Active', slug: 'technova-frontend-2024' },
  { id: 'room-2', title: 'Backend Developer', company: 'BrightStack Solutions', description: 'Own reliable APIs that power high-trust products.', requiredSkills: ['Node.js', 'PostgreSQL', 'AWS'], education: 'Computer Science or engineering degree', experience: '3+ years', cvWeight: 60, videoWeight: 40, minimumScore: 75, shortlistCount: 2, status: 'Active', slug: 'brightstack-backend-2024' },
  { id: 'room-3', title: 'Product Designer', company: 'Vertex Digital', description: 'Shape simple experiences from complex problems.', requiredSkills: ['Figma', 'UX research', 'Prototyping'], education: 'Design or related degree', experience: '3+ years', cvWeight: 50, videoWeight: 50, minimumScore: 70, shortlistCount: 3, status: 'Draft', slug: 'vertex-product-design' },
];

export const applicationsSeed: Application[] = [
  { id: 'app-1', candidateId: 'cand-1', roomId: 'room-1', job: 'Frontend Developer', company: 'TechNova Ltd.', cvScore: 92, videoScore: 86, overallScore: 89, status: 'Shortlisted', appliedAt: 'Today, 9:24 AM' },
  { id: 'app-2', candidateId: 'cand-1', roomId: 'room-2', job: 'Backend Developer', company: 'BrightStack Solutions', cvScore: 78, videoScore: 82, overallScore: 80, status: 'Reviewing', appliedAt: 'May 14, 2024' },
  { id: 'app-3', candidateId: 'cand-1', roomId: 'room-3', job: 'Junior UI Engineer', company: 'Vertex Digital', cvScore: 88, videoScore: 90, overallScore: 89, status: 'New', appliedAt: 'May 10, 2024' },
];

export const clientsSeed: Client[] = [
  { id: 'client-1', companyName: 'TechNova Ltd.', industry: 'Enterprise SaaS', contactPerson: 'Arif Chowdhury', contactEmail: 'arif@technova.example', status: 'Active' },
  { id: 'client-2', companyName: 'BrightStack Solutions', industry: 'Fintech & Cloud', contactPerson: 'Sabrina Rahman', contactEmail: 'sabrina@brightstack.example', status: 'Active' },
  { id: 'client-3', companyName: 'Vertex Digital', industry: 'Design & Engineering', contactPerson: 'Kamal Hossain', contactEmail: 'kamal@vertex.example', status: 'Onboarding' },
];

export function PageHeading({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="mb-7 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        {eyebrow && (
          <div className="mb-2 text-[11px] font-bold uppercase tracking-[.18em] text-[#9a7922]">
            {eyebrow}
          </div>
        )}
        <h1 className="cf-display text-3xl font-bold text-[#253142] md:text-[2.6rem]" data-testid="page-title">
          {title}
        </h1>
        {description && (
          <p className="mt-2 max-w-2xl text-sm leading-6 text-[#687382]">
            {description}
          </p>
        )}
      </div>
      {action && <div>{action}</div>}
    </div>
  );
}

export function StatCard({
  label,
  value,
  detail,
  icon: Icon,
  accent = 'yellow',
}: {
  label: string;
  value: string;
  detail: string;
  icon: LucideIcon;
  accent?: 'yellow' | 'green' | 'blue' | 'coral';
}) {
  const colors = {
    yellow: 'bg-[#fff1c9] text-[#8a6a16]',
    green: 'bg-[#e2f0e9] text-[#277254]',
    blue: 'bg-[#e4edf5] text-[#3a6384]',
    coral: 'bg-[#f7e5e1] text-[#a33d35]',
  };
  return (
    <div
      className="cf-card rounded-2xl p-5"
      data-testid={`stat-${label.toLowerCase().replaceAll(' ', '-')}`}
    >
      <div className="flex items-start justify-between">
        <span className="text-xs font-bold uppercase tracking-[.13em] text-[#7b8490]">
          {label}
        </span>
        <span className={`grid h-9 w-9 place-items-center rounded-xl ${colors[accent]}`}>
          <Icon size={17} />
        </span>
      </div>
      <div className="mt-4 text-3xl font-bold text-[#253142]">{value}</div>
      <div className="mt-1 text-xs font-semibold text-[#78818d]">{detail}</div>
    </div>
  );
}

export function Chart({
  values,
  labels,
  color = '#f5c84b',
}: {
  values: number[];
  labels: string[];
  color?: string;
}) {
  return (
    <div className="flex h-44 items-end gap-2 border-b border-l border-[#d9dbd1] px-3 pb-0 pt-5">
      {values.map((v, i) => (
        <div key={labels[i] || i} className="flex h-full flex-1 flex-col justify-end gap-2">
          <div
            className="cf-bar"
            style={{ height: `${v}%`, background: color }}
            title={`${v} points`}
          />
          <span className="text-center text-[10px] font-semibold text-[#8b929a]">
            {labels[i]}
          </span>
        </div>
      ))}
    </div>
  );
}

export function Badge({
  children,
  tone = 'neutral',
}: {
  children: ReactNode;
  tone?: 'neutral' | 'good' | 'warn' | 'bad' | 'accent';
}) {
  const colors = {
    neutral: 'bg-[#eef0e7] text-[#526072]',
    good: 'bg-[#e2f0e9] text-[#277254]',
    warn: 'bg-[#fff1c9] text-[#795f19]',
    bad: 'bg-[#f7e5e1] text-[#a33d35]',
    accent: 'bg-[#f5c84b]/25 text-[#685313]',
  };
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-bold ${colors[tone]}`}
    >
      {children}
    </span>
  );
}

export function DataAccessCard() {
  return (
    <div className="cf-card mt-6 rounded-2xl border border-[#d9dbd1] bg-[#fbfaf5] p-5 md:p-6 shadow-sm">
      <div className="flex items-center justify-between border-b border-[#eef0e7] pb-3">
        <div className="flex items-center gap-2">
          <div className="grid h-6 w-6 place-items-center rounded-lg bg-[#e2f0e9] text-[#277254]">
            <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              <path d="m9 12 2 2 4-4" />
            </svg>
          </div>
          <h3 className="font-bold text-sm text-[#253142]">
            Data Access Control & Security Auditing (US-36)
          </h3>
        </div>
        <span className="rounded-full bg-[#e2f0e9] px-2.5 py-0.5 text-[11px] font-bold text-[#277254]">
          Active
        </span>
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-3 text-xs">
        <div className="rounded-xl bg-white p-3 border border-[#eef0e7]">
          <span className="text-[#7b8490] block">Resource Access</span>
          <strong className="text-[#253142] mt-1 block">Role-Scoped Files</strong>
        </div>
        <div className="rounded-xl bg-white p-3 border border-[#eef0e7]">
          <span className="text-[#7b8490] block">Audit Logging</span>
          <strong className="text-[#253142] mt-1 block">careerflow_data_access_logs</strong>
        </div>
        <div className="rounded-xl bg-white p-3 border border-[#eef0e7]">
          <span className="text-[#7b8490] block">Access Status</span>
          <strong className="text-[#277254] mt-1 block">GRANTED / DENIED Tracked</strong>
        </div>
      </div>
    </div>
  );
}

