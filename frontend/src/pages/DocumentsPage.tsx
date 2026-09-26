import React, { useState, useEffect } from 'react';
import {
  Upload,
  FileText,
  Trash2,
  RefreshCw,
  Eye,
  CheckCircle,
  AlertTriangle,
  FileBox,
  Layers,
  HardDrive,
  Calendar,
  X
} from 'lucide-react';
import { api } from '../services/api';
import { DocumentInfo, DocumentChunk } from '../types';

export const DocumentsPage: React.FC = () => {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [isReindexing, setIsReindexing] = useState<boolean>(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadMessage, setUploadMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Chunk inspection state
  const [inspectingDoc, setInspectingDoc] = useState<{ id: string; name: string } | null>(null);
  const [chunks, setChunks] = useState<DocumentChunk[]>([]);
  const [isLoadingChunks, setIsLoadingChunks] = useState<boolean>(false);

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    setIsLoading(true);
    try {
      const data = await api.getDocuments();
      setDocuments(data);
    } catch (err: any) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setUploadMessage(null);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    setIsUploading(true);
    setUploadMessage(null);

    try {
      const newDoc = await api.uploadDocument(selectedFile);
      setDocuments((prev) => [newDoc, ...prev]);
      setUploadMessage({
        type: 'success',
        text: `Successfully uploaded and indexed "${newDoc.filename}" into ChromaDB with ${newDoc.chunk_count} chunks.`
      });
      setSelectedFile(null);
    } catch (err: any) {
      setUploadMessage({
        type: 'error',
        text: err.message || 'Failed to upload document.'
      });
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (docId: string, filename: string) => {
    if (!confirm(`Are you sure you want to remove "${filename}" from the RAG knowledgebase?`)) return;

    try {
      await api.deleteDocument(docId);
      setDocuments((prev) => prev.filter((d) => d.id !== docId));
    } catch (err: any) {
      alert(`Failed to delete document: ${err.message}`);
    }
  };

  const handleReindexAll = async () => {
    setIsReindexing(true);
    try {
      const res = await api.reindexDocuments();
      alert(`Re-indexed ${res.documents_reindexed} documents into ${res.total_chunks} chunks.`);
      loadDocuments();
    } catch (err: any) {
      alert(`Re-indexing failed: ${err.message}`);
    } finally {
      setIsReindexing(false);
    }
  };

  const handleInspectChunks = async (docId: string, name: string) => {
    setInspectingDoc({ id: docId, name });
    setIsLoadingChunks(true);
    try {
      const res = await api.getDocumentChunks(docId);
      setChunks(res.chunks || []);
    } catch (err: any) {
      alert(`Failed to load chunks: ${err.message}`);
    } finally {
      setIsLoadingChunks(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="space-y-6">
      {/* Top Description */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">
            Company Knowledge Base & RAG Index
          </h2>
          <p className="text-xs text-slate-500 mt-1 max-w-2xl">
            Upload policies, FAQs, and service agreements. The system extracts text, generates embeddings, and saves chunk vectors into ChromaDB for high-precision retrieval.
          </p>
        </div>
        <button
          onClick={handleReindexAll}
          disabled={isReindexing}
          className="inline-flex items-center space-x-2 px-4 py-2.5 rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 text-slate-700 text-xs font-semibold transition"
        >
          <RefreshCw className={`w-4 h-4 ${isReindexing ? 'animate-spin text-blue-600' : 'text-slate-500'}`} />
          <span>{isReindexing ? 'Re-indexing...' : 'Re-index All Documents'}</span>
        </button>
      </div>

      {/* Upload Box */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <h3 className="font-semibold text-sm text-slate-800 mb-3 flex items-center space-x-2">
          <Upload className="w-4 h-4 text-blue-600" />
          <span>Upload Document (.PDF, .TXT, .DOCX)</span>
        </h3>

        <form onSubmit={handleUpload} className="space-y-4">
          <div className="border-2 border-dashed border-slate-300 hover:border-blue-400 rounded-xl p-6 text-center bg-slate-50/50 transition">
            <input
              type="file"
              id="file-upload"
              accept=".pdf,.txt,.docx,.md"
              onChange={handleFileChange}
              className="hidden"
            />
            <label
              htmlFor="file-upload"
              className="cursor-pointer flex flex-col items-center justify-center space-y-2"
            >
              <FileBox className="w-10 h-10 text-slate-400" />
              <div className="text-xs font-medium text-slate-700">
                {selectedFile ? (
                  <span className="text-blue-600 font-semibold">{selectedFile.name} ({formatFileSize(selectedFile.size)})</span>
                ) : (
                  <span>Click to select or drag and drop company documents</span>
                )}
              </div>
              <p className="text-[11px] text-slate-400">PDF, TXT, DOCX up to 15MB</p>
            </label>
          </div>

          {uploadMessage && (
            <div
              className={`p-3 rounded-xl text-xs flex items-center space-x-2 ${
                uploadMessage.type === 'success'
                  ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                  : 'bg-rose-50 text-rose-800 border border-rose-200'
              }`}
            >
              {uploadMessage.type === 'success' ? (
                <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0" />
              ) : (
                <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
              )}
              <span>{uploadMessage.text}</span>
            </div>
          )}

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={!selectedFile || isUploading}
              className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium text-xs shadow-sm transition flex items-center space-x-2"
            >
              <Upload className="w-4 h-4" />
              <span>{isUploading ? 'Extracting & Indexing...' : 'Upload & Process'}</span>
            </button>
          </div>
        </form>
      </div>

      {/* Documents Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 bg-slate-50/50 flex items-center justify-between">
          <span className="font-semibold text-xs text-slate-700 uppercase tracking-wider">
            Indexed Documents ({documents.length})
          </span>
          <span className="text-xs text-slate-500">
            Total Chunks: {documents.reduce((acc, d) => acc + (d.chunk_count || 0), 0)}
          </span>
        </div>

        {isLoading ? (
          <div className="p-12 text-center text-xs text-slate-400">Loading documents...</div>
        ) : documents.length === 0 ? (
          <div className="p-12 text-center text-xs text-slate-400">No documents found. Upload one above.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50 text-slate-500 uppercase tracking-wider font-semibold text-[11px]">
                  <th className="py-3 px-6">Document</th>
                  <th className="py-3 px-4">Type</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Chunks</th>
                  <th className="py-3 px-4 text-right">Size</th>
                  <th className="py-3 px-4">Uploaded</th>
                  <th className="py-3 px-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-50/80 transition">
                    <td className="py-3 px-6 font-medium text-slate-800 flex items-center space-x-2">
                      <FileText className="w-4 h-4 text-blue-500 shrink-0" />
                      <span className="truncate max-w-xs">{doc.filename}</span>
                    </td>
                    <td className="py-3 px-4 font-mono text-[11px] text-slate-500">
                      {doc.file_type}
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold ${
                          doc.status === 'Ready'
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            : 'bg-amber-50 text-amber-700 border border-amber-200'
                        }`}
                      >
                        {doc.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right font-mono font-medium text-slate-700">
                      {doc.chunk_count}
                    </td>
                    <td className="py-3 px-4 text-right text-slate-500 font-mono">
                      {formatFileSize(doc.file_size)}
                    </td>
                    <td className="py-3 px-4 text-slate-500">
                      {new Date(doc.uploaded_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-6 text-right space-x-2">
                      <button
                        onClick={() => handleInspectChunks(doc.id, doc.filename)}
                        className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg border border-slate-200 text-slate-600 hover:text-blue-600 hover:bg-blue-50 transition text-[11px]"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Chunks</span>
                      </button>
                      <button
                        onClick={() => handleDelete(doc.id, doc.filename)}
                        className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg border border-slate-200 text-slate-600 hover:text-red-600 hover:bg-red-50 transition text-[11px]"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                        <span>Delete</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Chunk Viewer Modal */}
      {inspectingDoc && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fadeIn">
          <div className="bg-white rounded-2xl shadow-2xl max-w-3xl w-full border border-slate-200 overflow-hidden flex flex-col max-h-[90vh]">
            <div className="px-6 py-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-slate-800 text-sm">
                  Document Chunks: {inspectingDoc.name}
                </h3>
                <p className="text-xs text-slate-500">
                  Total Chunks: {chunks.length}
                </p>
              </div>
              <button
                onClick={() => setInspectingDoc(null)}
                className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-200 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 overflow-y-auto space-y-4 flex-1">
              {isLoadingChunks ? (
                <div className="text-center py-10 text-xs text-slate-400">Loading chunks...</div>
              ) : chunks.length === 0 ? (
                <div className="text-center py-10 text-xs text-slate-400">No chunks found.</div>
              ) : (
                chunks.map((c, idx) => (
                  <div key={idx} className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-2">
                    <div className="flex items-center justify-between text-[11px] font-mono text-slate-500 border-b border-slate-200/60 pb-1.5">
                      <span>Chunk #{idx + 1} (Page {c.page_number})</span>
                      <span className="text-slate-400">{c.chunk_id}</span>
                    </div>
                    <p className="text-xs text-slate-700 whitespace-pre-wrap leading-relaxed font-mono">
                      {c.text}
                    </p>
                  </div>
                ))
              )}
            </div>

            <div className="px-6 py-3 bg-slate-50 border-t border-slate-200 flex justify-end">
              <button
                onClick={() => setInspectingDoc(null)}
                className="px-4 py-1.5 rounded-lg bg-slate-800 text-white text-xs font-medium hover:bg-slate-900 transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
