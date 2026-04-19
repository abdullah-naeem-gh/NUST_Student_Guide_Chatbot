import { create } from 'zustand'

const useAppStore = create((set, get) => ({
  // ── Chat history ─────────────────────────────────────────────────
  // Each entry: { id, role: 'user'|'assistant', content, results, timestamp }
  messages: [],
  activeResultId: null,

  addMessage: (message) => set((state) => ({
    messages: [...state.messages, { ...message, id: message.id ?? Date.now() }],
    activeResultId: message.role === 'assistant' ? message.id : state.activeResultId,
  })),

  updateMessage: (id, patch) => set((state) => ({
    messages: state.messages.map((m) => m.id === id ? { ...m, ...patch } : m),
  })),

  setActiveResultId: (id) => set({ activeResultId: id }),

  /**
   * When set, EvidencePanel focuses a chunk (by id, else first match on page_start), then clears.
   * @type {{ chunkId: string, pageStart?: number } | null}
   */
  evidenceFocus: null,
  setEvidenceFocus: (focus) => set({ evidenceFocus: focus }),

  clearMessages: () => set({ messages: [], activeResultId: null }),

  // ── Loading ───────────────────────────────────────────────────────
  isLoading: false,
  setLoading: (loading) => set({ isLoading: loading }),

  // ── Index status ─────────────────────────────────────────────────
  indexStatus: { is_indexed: false, num_chunks: 0, last_updated: null },
  setIndexStatus: (status) => set({ indexStatus: status }),

  /** Indexed PDF filename for POST /query source_file and GET /pdf?file= */
  selectedHandbookFile: null,
  setSelectedHandbookFile: (name) => set({ selectedHandbookFile: name }),

  // ── Ingest progress ───────────────────────────────────────────────
  ingestProgress: { status: 'idle', step: '', progress: 0, error: null },
  setIngestProgress: (progress) => set((state) => ({
    ingestProgress: { ...state.ingestProgress, ...progress },
  })),
  resetIngestProgress: () => set({
    ingestProgress: { status: 'idle', step: '', progress: 0, error: null },
  }),

  // ── Theme (optional; main UI uses theme-guide / light scholarly palette) ──
  darkMode: false,
  toggleDarkMode: () => set((state) => {
    const next = !state.darkMode
    document.body.classList.toggle('light', !next)
    document.documentElement.classList.toggle('dark', next)
    return { darkMode: next }
  }),

  // ── Legacy compat (some API files use these) ──────────────────────
  queryResults: null,
  setQueryResults: (results) => set({ queryResults: results }),
}))

export default useAppStore
