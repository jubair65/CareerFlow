export interface ShowcaseMessage {
  headline: string;
  support: string;
}

export type AuthShowcaseMode = 'timed' | 'stepped' | 'role';

export const LOGIN_MESSAGES: ShowcaseMessage[] = [
  {
    headline: 'A little more ready than yesterday.',
    support: 'Pick up your practice where you left it.',
  },
  {
    headline: 'See why a score is what it is.',
    support: 'Every CV and practice score comes with its reasons.',
  },
  {
    headline: 'Compare candidates on the same signals.',
    support: 'Shortlists and notes stay together in the room.',
  },
  {
    headline: 'Keep every client and candidate in view.',
    support: 'One pipeline for the whole agency.',
  },
];

export const REGISTER_ROLE_MESSAGES: Record<'student' | 'hr' | 'agency', ShowcaseMessage[]> = {
  student: [
    {
      headline: 'Your best work deserves a clearer runway.',
      support: 'Upload your CV and see how it reads to a recruiter.',
    },
    {
      headline: 'Practice the answers that matter.',
      support: 'Record a take, get feedback, then record another and compare.',
    },
    {
      headline: 'Watch your progress add up.',
      support: 'Scores, takes and applications in one place.',
    },
  ],
  hr: [
    {
      headline: 'Make every hiring decision clearer.',
      support: 'Create a room, rank applicants and keep notes with the shortlist.',
    },
    {
      headline: 'Same signals for every applicant.',
      support: 'CV and video scores, side by side, with the reasons shown.',
    },
  ],
  agency: [
    {
      headline: 'Move the right people forward.',
      support: 'Manage clients, rooms and candidates in one pipeline.',
    },
    {
      headline: 'Keep every client up to date.',
      support: "See each candidate's stage without asking around.",
    },
  ],
};

export const FORGOT_STEP_MESSAGES: Record<number, ShowcaseMessage> = {
  1: {
    headline: 'Regain access securely.',
    support: "Enter your email and we'll send you a code.",
  },
  2: {
    headline: 'Check your inbox.',
    support: 'Enter the code we sent. It expires in 15 minutes, so use it right away.',
  },
  3: {
    headline: 'Choose a new password.',
    support: 'Use at least 8 characters. Then log in as usual.',
  },
};

