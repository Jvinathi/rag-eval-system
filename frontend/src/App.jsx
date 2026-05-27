import { useState } from "react";
import UploadPanel from "./components/UploadPanel";
import QueryPanel from "./components/QueryPanel";
import MetricsDashboard from "./components/MetricsDashboard";
import { Database } from "lucide-react";

export default function App() {
  const [collectionName, setCollectionName] = useState("rag_documents");
  const [latestEval, setLatestEval] = useState(null);

  return (
    <div className="min-h-screen bg-[#0d1117]">
      {/* Header */}
      <header className="border-b border-[#30363d] bg-[#161b22] px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 
                            flex items-center justify-center">
              <Database size={16} className="text-white" />
            </div>
            <div>
              <h1 className="text-white font-bold text-lg leading-none">
                Production RAG System
              </h1>
              <p className="text-gray-400 text-xs">with Evaluation Pipeline</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500 font-mono bg-[#21262d] px-2 py-1 rounded">
              Ollama/Mistral · ChromaDB · RAGAS
            </span>
          </div>
        </div>
      </header>

      {/* Hero Banner */}
      <div className="bg-gradient-to-r from-blue-900/20 to-purple-900/20 border-b border-[#30363d]">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <blockquote className="text-gray-300 italic text-sm border-l-2 border-blue-500 pl-3">
            "Chatbots hallucinate — mine doesn't, and here's the proof."
          </blockquote>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-6">
        {/* Metric Tags */}
        <div className="flex flex-wrap gap-2 mb-6">
          {["LlamaIndex", "RAGAS", "ChromaDB", "Ollama/Mistral", "FastAPI", "Docker"].map(tag => (
            <span key={tag} className="text-xs font-mono bg-[#21262d] text-gray-300 
                                       px-3 py-1 rounded-full border border-[#30363d]">
              {tag}
            </span>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Column */}
          <div className="space-y-6">
            <UploadPanel onUploadSuccess={setCollectionName} />
            <QueryPanel
              collectionName={collectionName}
              onEvalComplete={setLatestEval}
            />
          </div>

          {/* Right Column — Dashboard */}
          <div>
            <MetricsDashboard latestEval={latestEval} />
          </div>
        </div>

        {/* Why It Stands Out Box */}
        <div className="mt-6 bg-[#161b22] rounded-xl p-5 border border-[#30363d]">
          <p className="text-xs font-mono text-gray-500 mb-2">WHY IT STANDS OUT</p>
          <p className="text-gray-300 text-sm">
            Evaluation is the #1 gap in most AI projects. Having RAGAS metrics + a live 
            dashboard signals production readiness, not just a hobby build.
            This system uses <span className="text-blue-400">100% free, local models</span> — 
            no API keys, no costs, works offline.
          </p>
        </div>
      </main>
    </div>
  );
}
