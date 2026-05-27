import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, FileText, CheckCircle, AlertCircle, Loader2 } from "lucide-react";
import { uploadPDF } from "../api";

export default function UploadPanel({ onUploadSuccess }) {
  const [status, setStatus] = useState("idle"); // idle | uploading | success | error
  const [message, setMessage] = useState("");
  const [uploadedFile, setUploadedFile] = useState(null);
  const [collectionName, setCollectionName] = useState("rag_documents");

  const onDrop = useCallback(async (acceptedFiles) => {
    const file = acceptedFiles[0];
    if (!file) return;

    setStatus("uploading");
    setMessage(`Processing ${file.name}...`);
    setUploadedFile(file);

    try {
      const result = await uploadPDF(file, collectionName);
      setStatus("success");
      setMessage(
        `✓ ${result.file_name} indexed! ${result.chunks_created} chunks created in "${result.collection_name}"`
      );
      onUploadSuccess?.(result.collection_name);
    } catch (err) {
      setStatus("error");
      setMessage(err.response?.data?.detail || "Upload failed. Is the backend running?");
    }
  }, [collectionName, onUploadSuccess]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"] },
    maxFiles: 1,
    disabled: status === "uploading",
  });

  return (
    <div className="bg-[#161b22] rounded-xl p-6 border border-[#30363d]">
      <h2 className="text-xl font-bold text-white mb-2 flex items-center gap-2">
        <Upload size={20} className="text-blue-400" />
        Upload Document
      </h2>
      <p className="text-gray-400 text-sm mb-4">
        Upload legal, medical, or financial PDFs to build your knowledge base.
      </p>

      {/* Collection Name Input */}
      <div className="mb-4">
        <label className="block text-sm text-gray-400 mb-1">Collection Name</label>
        <input
          type="text"
          value={collectionName}
          onChange={(e) => setCollectionName(e.target.value)}
          className="w-full bg-[#0d1117] border border-[#30363d] rounded-lg px-3 py-2 
                     text-white text-sm focus:outline-none focus:border-blue-500"
          placeholder="rag_documents"
          disabled={status === "uploading"}
        />
      </div>

      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer
                    transition-all duration-200
                    ${isDragActive 
                      ? "border-blue-400 bg-blue-400/10" 
                      : "border-[#30363d] hover:border-blue-500 hover:bg-[#21262d]"
                    }
                    ${status === "uploading" ? "opacity-50 cursor-not-allowed" : ""}
                   `}
      >
        <input {...getInputProps()} />

        {status === "uploading" ? (
          <div className="flex flex-col items-center gap-3">
            <Loader2 size={40} className="text-blue-400 animate-spin" />
            <p className="text-gray-300">Indexing document... This may take a minute.</p>
            <p className="text-gray-500 text-sm">Chunking → Embedding → Storing in ChromaDB</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <FileText size={40} className="text-gray-500" />
            <p className="text-gray-300">
              {isDragActive ? "Drop your PDF here!" : "Drag & drop a PDF, or click to select"}
            </p>
            <p className="text-gray-500 text-sm">Max 50MB • PDF only</p>
          </div>
        )}
      </div>

      {/* Status Message */}
      {message && (
        <div className={`mt-4 p-3 rounded-lg flex items-start gap-2 text-sm
                        ${status === "success" 
                          ? "bg-green-900/30 border border-green-700 text-green-300"
                          : status === "error"
                          ? "bg-red-900/30 border border-red-700 text-red-300"
                          : "bg-blue-900/30 border border-blue-700 text-blue-300"
                        }`}>
          {status === "success" && <CheckCircle size={16} className="shrink-0 mt-0.5" />}
          {status === "error" && <AlertCircle size={16} className="shrink-0 mt-0.5" />}
          <span>{message}</span>
        </div>
      )}
    </div>
  );
}