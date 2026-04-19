import { create } from 'zustand'

const useAppStore = create((set) => ({
  // State
  queryResults: null,
  isLoading: false,
  indexStatus: {
    is_indexed: false,
    num_chunks: 0,
    last_updated: null
  },
  ingestProgress: {
    status: 'idle', // idle, ingesting, completed, error
    step: '',
    progress: 0,
    error: null
  },
  darkMode: true,

  // Actions
  setQueryResults: (results) => set({ queryResults: results }),
  setLoading: (loading) => set({ isLoading: loading }),
  setIndexStatus: (status) => set({ indexStatus: status }),
  setIngestProgress: (progress) => set((state) => ({ 
    ingestProgress: { ...state.ingestProgress, ...progress } 
  })),
  toggleDarkMode: () => set((state) => {
    const newDarkMode = !state.darkMode;
    if (newDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    return { darkMode: newDarkMode };
  }),
  resetIngestProgress: () => set({
    ingestProgress: {
      status: 'idle',
      step: '',
      progress: 0,
      error: null
    }
  })
}))

export default useAppStore;
