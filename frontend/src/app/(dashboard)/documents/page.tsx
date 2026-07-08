"use client";

export default function DocumentsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Documents</h1>
        <button className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition">
          Upload Document
        </button>
      </div>
      <p className="text-muted-foreground">
        Upload PDF documents for secure RAG queries. Documents are chunked,
        embedded, and stored with access controls.
      </p>
      <div className="rounded-lg border border-border p-12 text-center">
        <p className="text-muted-foreground">No documents uploaded yet.</p>
      </div>
    </div>
  );
}
