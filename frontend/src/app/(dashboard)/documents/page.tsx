"use client";

import { useState, useCallback } from "react";
import {
  Upload,
  FileText,
  Trash2,
  Search,
  CheckCircle,
  Loader2,
  XCircle,
  File,
  Send,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface DocumentItem {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  status: "processing" | "ready" | "failed";
  chunk_count: number;
  created_at: string;
}

const mockDocuments: DocumentItem[] = [
  {
    id: "1",
    filename: "security_policy_2024.pdf",
    file_type: "application/pdf",
    file_size: 2456000,
    status: "ready",
    chunk_count: 42,
    created_at: "2024-01-15T10:30:00Z",
  },
  {
    id: "2",
    filename: "quarterly_report_Q4.pdf",
    file_type: "application/pdf",
    file_size: 5120000,
    status: "ready",
    chunk_count: 87,
    created_at: "2024-01-14T14:20:00Z",
  },
  {
    id: "3",
    filename: "ai_governance_framework.pdf",
    file_type: "application/pdf",
    file_size: 1834000,
    status: "processing",
    chunk_count: 0,
    created_at: "2024-01-16T09:15:00Z",
  },
  {
    id: "4",
    filename: "compliance_audit_notes.pdf",
    file_type: "application/pdf",
    file_size: 890000,
    status: "failed",
    chunk_count: 0,
    created_at: "2024-01-13T16:45:00Z",
  },
  {
    id: "5",
    filename: "incident_response_playbook.pdf",
    file_type: "application/pdf",
    file_size: 3200000,
    status: "ready",
    chunk_count: 56,
    created_at: "2024-01-12T11:00:00Z",
  },
];

function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>(mockDocuments);
  const [dragActive, setDragActive] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [ragQuery, setRagQuery] = useState("");
  const [ragAnswer, setRagAnswer] = useState("");
  const [ragLoading, setRagLoading] = useState(false);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const files = Array.from(e.dataTransfer.files);
    files.forEach((file) => {
      const newDoc: DocumentItem = {
        id: crypto.randomUUID(),
        filename: file.name,
        file_type: file.type,
        file_size: file.size,
        status: "processing",
        chunk_count: 0,
        created_at: new Date().toISOString(),
      };
      setDocuments((prev) => [newDoc, ...prev]);
    });
  }, []);

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    files.forEach((file) => {
      const newDoc: DocumentItem = {
        id: crypto.randomUUID(),
        filename: file.name,
        file_type: file.type,
        file_size: file.size,
        status: "processing",
        chunk_count: 0,
        created_at: new Date().toISOString(),
      };
      setDocuments((prev) => [newDoc, ...prev]);
    });
  };

  const handleDelete = (id: string) => {
    setDocuments((prev) => prev.filter((d) => d.id !== id));
    setDeleteConfirm(null);
  };

  const handleRagQuery = async () => {
    if (!ragQuery.trim()) return;
    setRagLoading(true);
    // Simulated RAG response
    await new Promise((resolve) => setTimeout(resolve, 1500));
    setRagAnswer(
      "Based on the security policy document (security_policy_2024.pdf, chunks 12-15): " +
      "The organization requires all AI model interactions to pass through the security gateway. " +
      "Prompt injection detection must achieve a minimum 95% accuracy rate before deployment. " +
      "All PII must be redacted from both inputs and outputs."
    );
    setRagLoading(false);
  };

  const statusConfig = {
    ready: { icon: CheckCircle, color: "text-green-500", badge: "success" as const, label: "Ready" },
    processing: { icon: Loader2, color: "text-yellow-500", badge: "warning" as const, label: "Processing" },
    failed: { icon: XCircle, color: "text-red-500", badge: "danger" as const, label: "Failed" },
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Documents</h1>
        <p className="mt-1 text-muted-foreground">
          Upload documents for secure RAG queries. Files are chunked, embedded, and stored with access controls.
        </p>
      </div>

      {/* Upload Zone */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={cn(
          "relative rounded-lg border-2 border-dashed p-8 text-center transition-colors",
          dragActive
            ? "border-primary bg-primary/5"
            : "border-border hover:border-muted-foreground/50"
        )}
      >
        <input
          type="file"
          multiple
          accept=".pdf,.txt,.md,.docx"
          onChange={handleFileInput}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        />
        <Upload className={cn("mx-auto h-10 w-10", dragActive ? "text-primary" : "text-muted-foreground")} />
        <p className="mt-3 text-sm font-medium">
          {dragActive ? "Drop files here" : "Drag & drop files here, or click to browse"}
        </p>
        <p className="mt-1 text-xs text-muted-foreground">
          Supports PDF, TXT, MD, DOCX (max 50MB per file)
        </p>
      </div>

      {/* Document List */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-semibold">
            Uploaded Documents ({documents.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {documents.map((doc) => {
              const config = statusConfig[doc.status];
              const StatusIcon = config.icon;
              return (
                <div
                  key={doc.id}
                  className="flex items-center gap-3 rounded-md border border-border p-3 hover:bg-accent/50 transition-colors"
                >
                  <div className="rounded-md bg-muted p-2">
                    <File className="h-5 w-5 text-muted-foreground" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{doc.filename}</p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-xs text-muted-foreground">
                        {formatFileSize(doc.file_size)}
                      </span>
                      {doc.chunk_count > 0 && (
                        <>
                          <span className="text-xs text-muted-foreground">·</span>
                          <span className="text-xs text-muted-foreground">
                            {doc.chunk_count} chunks
                          </span>
                        </>
                      )}
                      <span className="text-xs text-muted-foreground">·</span>
                      <span className="text-xs text-muted-foreground">
                        {new Date(doc.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                  <Badge variant={config.badge} className="text-[10px]">
                    <StatusIcon className={cn("mr-1 h-3 w-3", doc.status === "processing" && "animate-spin")} />
                    {config.label}
                  </Badge>
                  <div className="relative">
                    {deleteConfirm === doc.id ? (
                      <div className="flex items-center gap-1">
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => handleDelete(doc.id)}
                          className="h-7 text-xs"
                        >
                          Confirm
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setDeleteConfirm(null)}
                          className="h-7 text-xs"
                        >
                          Cancel
                        </Button>
                      </div>
                    ) : (
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => setDeleteConfirm(doc.id)}
                        className="h-8 w-8 text-muted-foreground hover:text-red-500"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* RAG Query Interface */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-semibold flex items-center gap-2">
            <Search className="h-4 w-4" />
            Ask Your Documents
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex gap-2">
              <input
                type="text"
                value={ragQuery}
                onChange={(e) => setRagQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleRagQuery()}
                placeholder="Ask a question about your uploaded documents..."
                className="flex-1 rounded-md border border-input bg-background px-4 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              />
              <Button onClick={handleRagQuery} disabled={ragLoading || !ragQuery.trim()}>
                {ragLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </Button>
            </div>
            {ragAnswer && (
              <div className="rounded-md border border-border bg-muted/50 p-4">
                <p className="text-sm leading-relaxed">{ragAnswer}</p>
                <p className="mt-2 text-xs text-muted-foreground">
                  Sources: security_policy_2024.pdf (chunks 12-15)
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
