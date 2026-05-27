import axios from "axios";

const BASE_URL = "http://127.0.0.1:8000/api";

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 720000, // ✅ 12 minutes — RAGAS needs a long time
});

export const uploadPDF = async (file, collectionName = "rag_documents") => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("collection_name", collectionName);
  const response = await api.post("/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
};

export const queryDocuments = async (question, collectionName = "rag_documents") => {
  const response = await api.post("/query", {
    question,
    collection_name: collectionName,
  });
  return response.data;
};

export const evaluateResponse = async (question, answer, contexts, groundTruth = "") => {
  // ✅ Separate axios instance with longer timeout just for evaluation
  const evalApi = axios.create({
    baseURL: BASE_URL,
    timeout: 720000, // 12 minutes
  });
  const response = await evalApi.post("/evaluate", {
    question,
    answer,
    contexts,
    ground_truth: groundTruth,
  });
  return response.data;
};

export const getMetricsHistory = async () => {
  const response = await api.get("/metrics/history");
  return response.data;
};

export const getMetricsSummary = async () => {
  const response = await api.get("/metrics/summary");
  return response.data;
};