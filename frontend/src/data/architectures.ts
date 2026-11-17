export type Lane = 'ingest' | 'query' | 'output'

export interface ArchNode {
  id: string
  label: string
  sub?: string
  lane: Lane
  detail: string
  /** Grid position in the diagram: [column, row]. */
  pos: [number, number]
}

export interface Architecture {
  id: string
  name: string
  summary: string
  nodes: ArchNode[]
  edges: [string, string][]
  principles: string[]
}

export const architectures: Architecture[] = [
  {
    id: 'rag',
    name: 'RAG Architecture',
    summary:
      'Ingestion and query paths are separate services. Ingestion is offline and idempotent; the query path is latency-sensitive and only reads from the index.',
    nodes: [
      { id: 'docs', label: 'Documents', sub: 'PDF · MD · README', lane: 'ingest', pos: [0, 0], detail: 'Sources are versioned. Each document carries a stable ID, category, and a link back to the original.' },
      { id: 'proc', label: 'Processing', sub: 'extract · clean', lane: 'ingest', pos: [1, 0], detail: 'Text extraction and normalization. Content hashes detect unchanged documents so re-runs are cheap.' },
      { id: 'chunk', label: 'Chunking', sub: 'size · overlap', lane: 'ingest', pos: [2, 0], detail: 'Structure-aware splitting (headings first, then paragraphs and sentences) with configurable size and overlap. Heading paths are kept as chunk metadata.' },
      { id: 'embed', label: 'Embeddings', sub: 'document task type', lane: 'ingest', pos: [3, 0], detail: 'Chunks are embedded in batches with a document-retrieval task type. Model and dimensionality are configuration, not code.' },
      { id: 'vdb', label: 'Vector Database', sub: 'PostgreSQL + pgvector', lane: 'ingest', pos: [4, 0], detail: 'Vectors live next to metadata and full-text indexes in Postgres — one system for filtering, hybrid search, and transactions.' },
      { id: 'retr', label: 'Retrieval', sub: 'hybrid · top-k', lane: 'query', pos: [4, 1], detail: 'The question is embedded with a query task type. Vector and keyword results are fused, filtered by metadata, and cut at a relevance threshold.' },
      { id: 'llm', label: 'LLM', sub: 'grounded prompt', lane: 'query', pos: [3, 1], detail: 'Retrieved chunks are passed as numbered, untrusted evidence. The model must cite them and say when the evidence is insufficient.' },
      { id: 'ans', label: 'Grounded Answer', sub: 'with citations', lane: 'output', pos: [2, 1], detail: 'Only sources the model actually cited are shown to the user, each linking back to the original document.' },
    ],
    edges: [['docs', 'proc'], ['proc', 'chunk'], ['chunk', 'embed'], ['embed', 'vdb'], ['vdb', 'retr'], ['retr', 'llm'], ['llm', 'ans']],
    principles: [
      'Retrieval decides what the model may know; the LLM only phrases it.',
      'Every chunk keeps provenance metadata from ingestion to answer.',
      'Chunk size, overlap, and top-k are tuned by evaluation, not by guesswork.',
    ],
  },
  {
    id: 'mm-rag',
    name: 'Multimodal RAG',
    summary:
      'Each modality gets its own processing path, but they converge on a single text-searchable index so one query can retrieve evidence from slides, figures, and lectures alike.',
    nodes: [
      { id: 'pdf', label: 'PDF', sub: 'text layer', lane: 'ingest', pos: [0, 0], detail: 'Page text is extracted and chunked, keeping file and page references.' },
      { id: 'img', label: 'Images & Tables', sub: 'embedded in PDFs', lane: 'ingest', pos: [0, 1], detail: 'Figures are extracted with their surrounding page context so they can be found by what the page says about them.' },
      { id: 'vid', label: 'Videos', sub: 'lecture recordings', lane: 'ingest', pos: [0, 2], detail: 'Audio is transcribed (Whisper) in background workers; transcripts are indexed like documents.' },
      { id: 'mmp', label: 'Multimodal Processing', sub: 'async workers', lane: 'ingest', pos: [1, 1], detail: 'Heavy jobs run in Celery workers with Redis as broker, so the API and the LMS stay responsive.' },
      { id: 'uni', label: 'Unified Retrieval', sub: 'one vector index', lane: 'query', pos: [2, 1], detail: 'All modalities share one embedding space and index; metadata records the modality and origin file.' },
      { id: 'llm', label: 'LLM', sub: 'local inference', lane: 'query', pos: [3, 1], detail: 'Generation runs on locally hosted models (Ollama), keeping course material on own infrastructure.' },
      { id: 'ans', label: 'Answer with Sources', sub: 'file-level attribution', lane: 'output', pos: [4, 1], detail: 'Answers reference the PDFs, figures, or videos they were derived from.' },
    ],
    edges: [['pdf', 'mmp'], ['img', 'mmp'], ['vid', 'mmp'], ['mmp', 'uni'], ['uni', 'llm'], ['llm', 'ans']],
    principles: [
      'Normalize modalities into a shared representation, never lose the pointer to the original.',
      'Move slow media processing off the request path.',
      'Measure retrieval per modality — failures hide in the minority modalities.',
    ],
  },
  {
    id: 'meeting',
    name: 'AI Meeting Intelligence',
    summary:
      'A staged speech-to-insight pipeline. Each stage produces an inspectable artefact, which makes the system debuggable and lets stages be swapped independently.',
    nodes: [
      { id: 'audio', label: 'Audio', sub: 'meeting recording', lane: 'ingest', pos: [0, 0], detail: 'Recorded sales conversations enter the pipeline.' },
      { id: 'asr', label: 'ASR', sub: 'Whisper', lane: 'ingest', pos: [1, 0], detail: 'Speech is transcribed with timestamps.' },
      { id: 'dia', label: 'Speaker Diarization', sub: 'who spoke when', lane: 'ingest', pos: [2, 0], detail: 'Segments are attributed to speakers and aligned with the transcript.' },
      { id: 'tr', label: 'Transcript', sub: 'speaker-attributed', lane: 'ingest', pos: [3, 0], detail: 'A structured transcript is the contract between the speech layer and the language layer.' },
      { id: 'llm', label: 'LLM Analysis', sub: 'sentiment · themes', lane: 'query', pos: [3, 1], detail: 'NLP and LLM workflows detect sentiment and themes and extract key points.' },
      { id: 'ins', label: 'Business Insights', sub: 'follow-up actions', lane: 'query', pos: [2, 1], detail: 'Analysis is turned into sales insights and recommended follow-ups.' },
      { id: 'crm', label: 'CRM Integration', sub: 'AWS backend', lane: 'output', pos: [1, 1], detail: 'Results are written back into the CRM where sales teams already work.' },
    ],
    edges: [['audio', 'asr'], ['asr', 'dia'], ['dia', 'tr'], ['tr', 'llm'], ['llm', 'ins'], ['ins', 'crm']],
    principles: [
      'Clear contracts between stages (audio → transcript → analysis).',
      'Deliver results inside existing business tools.',
      'Each stage produces an artefact that can be inspected and evaluated on its own.',
    ],
  },
]
