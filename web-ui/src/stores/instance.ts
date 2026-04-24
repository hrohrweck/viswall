import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface InstanceState {
  selectedInstanceId: number | null
  setSelectedInstance: (id: number | null) => void
}

export const useInstanceStore = create<InstanceState>()(
  persist(
    (set) => ({
      selectedInstanceId: null,
      setSelectedInstance: (id) => set({ selectedInstanceId: id }),
    }),
    {
      name: 'viswall-instance',
    }
  )
)
