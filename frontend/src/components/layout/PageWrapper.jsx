import Navbar from './Navbar'

/**
 * PageWrapper — Standard layout for all pages
 * @param {Object} props
 * @param {React.ReactNode} props.children
 */
export default function PageWrapper({ children }) {
  return (
    <div className="min-h-screen flex flex-col bg-navy-900 text-slate-100">
      <Navbar />
      <main className="flex-1 max-w-7xl mx-auto w-full p-6">
        {children}
      </main>
      <footer className="py-6 px-6 border-t border-navy-800 text-center text-slate-500 text-xs font-mono">
        ACADEMIC POLICY QA SYSTEM &copy; 2024 • NUST STUDENT GUIDE CHATBOT
      </footer>
    </div>
  )
}
