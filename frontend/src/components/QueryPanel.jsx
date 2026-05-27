import { useState } from "react";
import { MessageSquare, Search, Loader2, AlertTriangle, BookOpen } from "lucide-react";
import { queryDocuments, evaluateResponse } from "../api";

export default function QueryPanel({ collectionName, onEvalComplete }) {
  const [question, setQuestion] = useState("");
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [evaluating, setEvaluating] = useState(false);
  const [error, setError] = useState("");

  const handleQuery = async () => {
    if (!question.trim()) return;
    setLoading(true);
    setError("");
    setResponse(null);

    try {
      const result = await queryDocuments(question, collectionName);
      setResponse(result);
    } catch (err) {
      setError(err.response?.data?.detail || "Query failed. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  const handleEvaluate = async () => {
    if (!response) return;
    setEvaluating(true);

    try {
      const contexts = response.sources.map((s) => s.text);
      const evalResult = await evaluateResponse(
        question,
        response.answer,
        contexts
      );
      onEvalComplete?.(evalResult);
    } catch (err) {
      setError("Evaluation failed: " + (err.response?.data?.detail || err.message));
    } finally {
      setEvaluating(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && e.ctrlKey) {
      handleQuery();
    }
  };

  return (
    <div className="bg-[#161b22] rounded-xl p-6 border border-[#30363d]">
      <h2 className="text-xl font-bold text-white mb-2 flex items-center gap-2">
        <MessageSquare size={20} className="text-purple-400" />
        Ask a Question
      </h2>
      <p className="text-gray-400 text-sm mb-4">
        Collection: <span className="text-purple-400 font-mono">{collectionName}</span>
        {" "}• Press Ctrl+Enter to submit
      </p>

      {/* Question Input */}
      <textarea
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="What does section 4.2 say about liability? / What are the patient's risk factors? / Summarize the Q3 revenue..."
        rows={4}
        className="w-full bg-[#0d1117] border border-[#30363d] rounded-lg px-4 py-3
                   text-white text-sm focus:outline-none focus:border-purple-500
                   resize-none mb-3"
        disabled={loading}
      />

      <button
        onClick={handleQuery}
        disabled={loading || !question.trim()}
        className="w-full bg-purple-600 hover:bg-purple-500 disabled:opacity-50
                   disabled:cursor-not-allowed text-white font-semibold py-3 px-4
                   rounded-lg transition-colors flex items-center justify-center gap-2"
      >
        {loading ? (
          <>
            <Loader2 size={16} className="animate-spin" />
            Thinking... (LLM processing)
          </>
        ) : (
          <>
            <Search size={16} />
            Search & Answer
          </>
        )}
      </button>

      {/* Error */}
      {error && (
        <div className="mt-4 p-3 bg-red-900/30 border border-red-700 rounded-lg
                        flex items-start gap-2 text-red-300 text-sm">
          <AlertTriangle size={16} className="shrink-0 mt-0.5" />
          {error}
        </div>
      )}

      {/* Response */}
      {response && (
        <div className="mt-4 space-y-4">
          {/* Answer */}
          <div className="bg-[#0d1117] rounded-lg p-4 border border-[#30363d]">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold text-gray-300">Answer</h3>
              <span className={`text-xs px-2 py-1 rounded-full font-mono
                              ${response.retrieval_score > 0.5 
                                ? "bg-green-900/50 text-green-400" 
                                : "bg-yellow-900/50 text-yellow-400"}`}>
                Retrieval Score: {(response.retrieval_score * 100).toFixed(1)}%
              </span>
            </div>
            <p className="text-gray-200 text-sm leading-relaxed whitespace-pre-wrap">
              {response.answer}
            </p>
          </div>

          {/* Sources */}
          {response.sources.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-gray-400 mb-2 flex items-center gap-1">
                <BookOpen size={14} />
                Retrieved Sources ({response.sources.length})
              </h3>
              <div className="space-y-2">
                {response.sources.map((source, idx) => (
                  <div key={idx} className="bg-[#21262d] rounded-lg p-3 border border-[#30363d]">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-mono text-blue-400">{source.file_name}</span>
                      <span className="text-xs text-gray-500">
                        Score: {(source.score * 100).toFixed(1)}%
                      </span>
                    </div>
                    <p className="text-gray-400 text-xs leading-relaxed line-clamp-3">
                      {source.text}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Evaluate Button */}
          <button
            onClick={handleEvaluate}
            disabled={evaluating || response.sources.length === 0}
            className="w-full bg-[#21262d] hover:bg-[#30363d] disabled:opacity-50
                       disabled:cursor-not-allowed text-white font-semibold py-2 px-4
                       rounded-lg transition-colors flex items-center justify-center gap-2
                       border border-[#30363d] text-sm"
          >
            {evaluating ? (
              <>
                <Loader2 size={14} className="animate-spin" />
                Running RAGAS Evaluation...
              </>
            ) : (
              "🔬 Evaluate with RAGAS"
            )}
          </button>
        </div>
      )}
    </div>
  );
}