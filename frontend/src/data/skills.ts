import type { LucideIcon } from 'lucide-react'
import { BrainCircuit, Database, Server, Sparkles } from 'lucide-react'

export interface SkillGroup {
  title: string
  description: string
  icon: LucideIcon
  skills: string[]
}

export const skillGroups: SkillGroup[] = [
  {
    title: 'AI & Generative AI',
    description: 'Grounded LLM applications, retrieval, and evaluation.',
    icon: Sparkles,
    skills: [
      'Large Language Models (LLMs)',
      'Retrieval-Augmented Generation (RAG)',
      'Multimodal RAG',
      'AI Agents',
      'Prompt Engineering',
      'Semantic Search',
      'Embeddings',
      'LLM Evaluation',
    ],
  },
  {
    title: 'Machine Learning & NLP',
    description: 'Language and speech models from training to inference.',
    icon: BrainCircuit,
    skills: [
      'Machine Learning',
      'PyTorch',
      'spaCy',
      'Named Entity Recognition (NER)',
      'Natural Language Processing',
      'Automatic Speech Recognition (ASR)',
      'Speaker Diarization',
    ],
  },
  {
    title: 'AI & Backend Engineering',
    description: 'Services, APIs, and asynchronous processing around models.',
    icon: Server,
    skills: ['Python', 'FastAPI', 'LangChain', 'pandas', 'REST APIs', 'Celery', 'Redis', 'Microservices'],
  },
  {
    title: 'Data & Infrastructure',
    description: 'Storage, deployment, observability, and data pipelines.',
    icon: Database,
    skills: [
      'PostgreSQL',
      'pgvector',
      'MySQL',
      'Docker',
      'Docker Compose',
      'AWS',
      'Google Cloud Platform',
      'Git & GitHub',
      'Prometheus',
      'Grafana',
      'ETL/ELT Pipelines',
    ],
  },
]
