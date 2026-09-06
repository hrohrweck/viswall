import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { Header } from './Header'
import { ErrorBoundary } from './ui/ErrorBoundary'
import { Toaster } from './ui/Toaster'

export function Layout() {
  return (
    <div className="min-h-screen bg-surface flex flex-col">
      <Header />
      <div className="flex flex-1">
        <Sidebar />
        <main id="main-content" className="flex-1 p-6 max-w-[1440px] w-full">
          <ErrorBoundary>
            <Outlet />
          </ErrorBoundary>
        </main>
      </div>
      <Toaster />
    </div>
  )
}
