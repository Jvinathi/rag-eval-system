import axios from "axios";

const BASE_URL = "http://127.0.0.1:8000/api";

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 120000, // 2 minutes (LLM can be slow)
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
  const response = await api.post("/evaluate", {
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