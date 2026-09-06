import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface SidebarState {
  collapsed: boolean
  setCollapsed: (collapsed: boolean) => void
  /** Mobile drawer open state — NOT persisted (resets on reload). */
  mobileOpen: boolean
  setMobileOpen: (open: boolean) => void
}

export const useSidebarStore = create<SidebarState>()(
  persist(
    (set) => ({
      collapsed: false,
      setCollapsed: (collapsed) => set({ collapsed }),
      mobileOpen: false,
      setMobileOpen: (open) => set({ mobileOpen: open }),
    }),
    {
      name: 'viswall-sidebar',
      partialize: (state) => ({ collapsed: state.collapsed }),
    }
  )
)
