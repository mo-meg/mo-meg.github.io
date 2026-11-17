/**
 * Courses and certifications shown in the "Continuous learning" block (Education section).
 *
 * To add a new one: append an entry below and push. Optional:
 *  - `url`: public verification link (e.g. the DataCamp "statement of accomplishment" page) — preferred
 *  - `pdf`: file name of a PDF placed in `frontend/public/certificates/` (build fails if the file is missing)
 *  - `featured: true`: show it in the highlighted list (keep that list short — ~10 entries)
 *  - `kind: 'certification'`: only for exam-based certifications (e.g. AWS, DataCamp Data Scientist cert);
 *    they are listed above the courses.
 * Then add the course to knowledge/education/training.md so the assistant knows about it.
 */

export type TrainingTopic =
  | 'LLMs & Generative AI'
  | 'AI Agents'
  | 'AI-assisted development'
  | 'Data engineering'
  | 'Python & software engineering'
  | 'DevOps, cloud & Git'
  | 'AI & ML foundations'

export const trainingTopics: TrainingTopic[] = [
  'LLMs & Generative AI',
  'AI Agents',
  'Data engineering',
  'AI-assisted development',
  'Python & software engineering',
  'DevOps, cloud & Git',
  'AI & ML foundations',
]

export interface TrainingEntry {
  title: string
  provider: string
  topic: TrainingTopic
  kind?: 'course' | 'certification'
  featured?: boolean
  year?: number
  url?: string
  pdf?: string
}

const dc = (title: string, topic: TrainingTopic, extra: Partial<TrainingEntry> = {}): TrainingEntry => ({
  title,
  provider: 'DataCamp',
  topic,
  kind: 'course',
  ...extra,
})

export const training: TrainingEntry[] = [
  // LLMs & Generative AI
  dc('Retrieval Augmented Generation (RAG) with LangChain', 'LLMs & Generative AI', { featured: true }),
  dc('Developing LLM Applications with LangChain', 'LLMs & Generative AI', { featured: true }),
  dc('Fine-Tuning with Llama 3', 'LLMs & Generative AI', { featured: true }),
  dc('Transformer Models with PyTorch', 'LLMs & Generative AI', { featured: true }),
  dc('Working with Hugging Face', 'LLMs & Generative AI', { featured: true }),
  dc('Prompt Engineering with the OpenAI API', 'LLMs & Generative AI', { featured: true }),
  dc('Working with the OpenAI API', 'LLMs & Generative AI'),
  dc('Large Language Models (LLMs) Concepts', 'LLMs & Generative AI'),
  dc('Generative AI Concepts', 'LLMs & Generative AI'),
  dc('Understanding ChatGPT', 'LLMs & Generative AI'),
  dc('Generative AI for Business', 'LLMs & Generative AI'),
  dc('AI Ethics', 'LLMs & Generative AI'),

  // AI Agents
  dc('Designing Agentic Systems with LangChain', 'AI Agents', { featured: true }),
  dc('Building Scalable Agentic Systems', 'AI Agents', { featured: true }),
  dc('Introduction to AI Agents', 'AI Agents'),

  // Data engineering
  dc('ETL and ELT in Python', 'Data engineering', { featured: true }),
  dc('Introduction to Apache Airflow in Python', 'Data engineering', { featured: true }),
  dc('Streamlined Data Ingestion with pandas', 'Data engineering'),
  dc('Reshaping Data with pandas', 'Data engineering'),
  dc('Cleaning Data in Python', 'Data engineering'),
  dc('Introduction to Importing Data in Python', 'Data engineering'),
  dc('Intermediate Importing Data in Python', 'Data engineering'),
  dc('Introduction to APIs in Python', 'Data engineering'),

  // AI-assisted development
  dc('AI-Assisted Coding for Developers', 'AI-assisted development'),
  dc('Software Development with GitHub Copilot', 'AI-assisted development'),
  dc('Software Development with Windsurf', 'AI-assisted development'),
  dc('Vibe Coding with Replit', 'AI-assisted development'),

  // Python & software engineering
  dc('Software Engineering Principles in Python', 'Python & software engineering'),
  dc('Writing Efficient Python Code', 'Python & software engineering'),
  dc('Introduction to Functions in Python', 'Python & software engineering'),
  dc('Introduction to Python for Developers', 'Python & software engineering'),
  dc('Intermediate Python for Developers', 'Python & software engineering'),

  // DevOps, cloud & Git
  dc('DevOps Concepts', 'DevOps, cloud & Git'),
  dc('Understanding Cloud Computing', 'DevOps, cloud & Git'),
  dc('Introduction to Git', 'DevOps, cloud & Git'),
  dc('Intermediate Git', 'DevOps, cloud & Git'),
  dc('Introduction to GitHub Concepts', 'DevOps, cloud & Git'),

  // AI & ML foundations
  dc('Understanding Artificial Intelligence', 'AI & ML foundations'),
  dc('Understanding Machine Learning', 'AI & ML foundations'),
]
