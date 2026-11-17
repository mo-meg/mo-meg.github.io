import type { Project } from '../../data/projects'

export const contextStyle: Record<Project['context'], string> = {
  'Professional work': 'text-emerald-600 dark:text-emerald-400 border-emerald-500/30 bg-emerald-500/10',
  'Academic research': 'text-accent-3 border-accent-3/30 bg-accent-3/10',
  'Personal project': 'text-accent-2 border-accent-2/30 bg-accent-2/10',
}
