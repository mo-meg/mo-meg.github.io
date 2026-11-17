export interface TimelineEntry {
  role: string
  organization: string
  kind: 'Professional' | 'Research' | 'Academic'
  focus: string
  points: string[]
  period?: string
}

export const experience: TimelineEntry[] = [
  {
    role: 'AI Engineer',
    organization: 'Prolumios',
    kind: 'Professional',
    focus: 'Integrating Artificial Intelligence into CRM systems',
    points: [
      'Developing end-to-end AI solutions for enterprise CRM systems.',
      'Engineering speech recognition and speaker diarization pipelines.',
      'Building NLP and LLM-driven analysis workflows.',
      'Extracting actionable insights from sales conversations.',
      'Collaborating with business teams to identify AI use cases.',
    ],
  },
  {
    role: 'Research Internship',
    organization: 'FernUniversität in Hagen',
    kind: 'Research',
    focus: 'Cloud-based information extraction',
    points: [
      'Developing web-based annotation interfaces.',
      'Implementing spaCy-based NER solutions.',
      'Configuring and optimizing GCP resources.',
    ],
  },
  {
    role: 'M.Sc. Information Systems',
    organization: 'FernUniversität in Hagen',
    kind: 'Academic',
    period: '2025',
    focus: 'Business Informatics (Wirtschaftsinformatik)',
    points: [
      'Business Intelligence',
      'Digital Transformation',
      'Business/IT Alignment',
      'Information Retrieval',
    ],
  },
]

export const education = [
  { title: 'M.Sc. Information Systems', institution: 'FernUniversität in Hagen', note: 'Business Informatics · 2025' },
  { title: 'B.Sc. Economics', institution: 'Alexandria University' },
  { title: 'Diploma in Computerized Accounting' },
]

export const activities = [
  { title: 'Guest lecturer — NLP and Generative AI', note: 'Teaching NLP and generative AI concepts.' },
  { title: 'Smart City workshop facilitator', note: 'Facilitating workshops on Smart City topics.' },
]
