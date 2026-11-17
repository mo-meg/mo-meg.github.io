import type { Lane } from '../../data/architectures'

export const laneColor: Record<Lane, string> = {
  ingest: 'var(--accent)',
  query: 'var(--accent-2)',
  output: '#10b981',
}

export const laneLabel: Record<Lane, string> = {
  ingest: 'Ingestion / processing',
  query: 'Query / reasoning',
  output: 'Delivery',
}
