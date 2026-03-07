import MoleculeViewer from '@/components/MoleculeViewer'
import SimilarityChecker from '@/components/SimilarityChecker'

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-50 p-8 space-y-8">
      <h1 className="text-center text-3xl font-bold">RDKit 全栈科研终端</h1>
      <MoleculeViewer />
      <SimilarityChecker />
    </main>
  )
}