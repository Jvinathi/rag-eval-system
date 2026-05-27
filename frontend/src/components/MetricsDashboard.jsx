import { useState, useEffect } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, RadarChart, Radar, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis, Legend,
} from "recharts";
import { BarChart2, RefreshCw, TrendingUp } from "lucide-react";
import { getMetricsHistory } from "../api";

const MetricCard = ({ label, value, color, description }) => (
  <div className="bg-[#0d1117] rounded-lg p-4 border border-[#30363d]">
    <p className="text-gray-400 text-xs mb-1">{label}</p>
    <p className={`text-2xl font-bold ${color}`}>
      {typeof value === "number" ? (value * 100).toFixed(1) + "%" : "—"}
    </p>
    <p className="text-gray-500 text-xs mt-1">{description}</p>
  </div>
);

export default function MetricsDashboard({ latestEval }) {
  const [history, setHistory] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const data = await getMetricsHistory();
      setHistory(data.history || []);
      setSummary(data.summary || null);
    } catch (err) {
      console.error("Failed to fetch metrics:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  // Refresh when new evaluation comes in
  useEffect(() => {
    if (latestEval) {
      fetchHistory();
    }
  }, [latestEval]);

  // Format history for chart
  const chartData = history.map((item, idx) => ({
    name: `Q${idx + 1}`,
    Faithfulness: parseFloat((item.faithfulness * 100).toFixed(1)),
    "Answer Relevancy": parseFloat((item.answer_relevancy * 100).toFixed(1)),
    "Context Precision": parseFloat((item.context_precision * 100).toFixed(1)),
    Overall: parseFloat((item.overall_score * 100).toFixed(1)),
  }));

  // Radar chart data for latest evaluation
  const radarData = latestEval ? [
    { metric: "Faithfulness", value: latestEval.metrics.faithfulness * 100 },
    { metric: "Relevancy", value: latestEval.metrics.answer_relevancy * 100 },
    { metric: "Precision", value: latestEval.metrics.context_precision * 100 },
  ] : [];

  return (
    <div className="bg-[#161b22] rounded-xl p-6 border border-[#30363d]">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <BarChart2 size={20} className="text-green-400" />
          RAGAS Metrics Dashboard
        </h2>
        <button
          onClick={fetchHistory}
          disabled={loading}
          className="flex items-center gap-1 text-xs text-gray-400 hover:text-white
                     bg-[#21262d] px-3 py-1.5 rounded-lg border border-[#30363d]
                     transition-colors"
        >
          <RefreshCw size={12} className={loading ? "animate-spin" : ""} />
          Refresh
        </button>
      </div>

      {/* Summary Cards */}
      {summary && summary.total_evaluations > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
          <MetricCard
            label="Faithfulness"
            value={summary.avg_faithfulness}
            color="text-blue-400"
            description="Answer grounded in docs"
          />
          <MetricCard
            label="Answer Relevancy"
            value={summary.avg_answer_relevancy}
            color="text-purple-400"
            description="Addresses the question"
          />
          <MetricCard
            label="Context Precision"
            value={summary.avg_context_precision}
            color="text-yellow-400"
            description="Retrieval quality"
          />
          <MetricCard
            label="Overall Score"
            value={summary.avg_overall}
            color="text-green-400"
            description={`Avg over ${summary.total_evaluations} evals`}
          />
        </div>
      )}

      {/* Latest Evaluation Radar Chart */}
      {latestEval && radarData.length > 0 && (
        <div className="mb-6">
          <h3 className="text-sm font-semibold text-gray-400 mb-3 flex items-center gap-1">
            <TrendingUp size={14} />
            Latest Evaluation Breakdown
          </h3>
          <div className="bg-[#0d1117] rounded-lg p-4 border border-[#30363d]">
            <p className="text-xs text-gray-500 mb-2 italic">
              "{latestEval.question}"
            </p>
            <ResponsiveContainer width="100%" height={220}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="#30363d" />
                <PolarAngleAxis dataKey="metric" tick={{ fill: "#9ca3af", fontSize: 12 }} />
                <PolarRadiusAxis 
                  angle={30} 
                  domain={[0, 100]} 
                  tick={{ fill: "#6b7280", fontSize: 10 }}
                />
                <Radar
                  name="Score"
                  dataKey="value"
                  stroke="#10b981"
                  fill="#10b981"
                  fillOpacity={0.3}
                />
                <Tooltip
                  contentStyle={{ backgroundColor: "#21262d", border: "1px solid #30363d" }}
                  formatter={(val) => [`${val.toFixed(1)}%`, "Score"]}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* History Line Chart */}
      {chartData.length > 1 && (
        <div>
          <h3 className="text-sm font-semibold text-gray-400 mb-3">
            Metrics Over Time
          </h3>
          <div className="bg-[#0d1117] rounded-lg p-4 border border-[#30363d]">
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#30363d" />
                <XAxis dataKey="name" tick={{ fill: "#9ca3af", fontSize: 12 }} />
                <YAxis domain={[0, 100]} tick={{ fill: "#9ca3af", fontSize: 12 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#21262d", border: "1px solid #30363d" }}
                  formatter={(val) => [`${val}%`]}
                />
                <Legend />
                <Line type="monotone" dataKey="Faithfulness" stroke="#60a5fa" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="Answer Relevancy" stroke="#a78bfa" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="Context Precision" stroke="#fbbf24" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="Overall" stroke="#10b981" strokeWidth={2} strokeDasharray="5 5" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Empty State */}
      {history.length === 0 && !latestEval && (
        <div className="text-center py-12 text-gray-500">
          <BarChart2 size={48} className="mx-auto mb-3 opacity-30" />
          <p className="text-sm">No evaluations yet.</p>
          <p className="text-xs mt-1">Upload a PDF, ask a question, then click "Evaluate with RAGAS"</p>
        </div>
      )}
    </div>
  );
}