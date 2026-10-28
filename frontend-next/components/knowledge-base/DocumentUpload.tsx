"use client";

import { useId, useState, type DragEvent } from "react";
import { UploadCloud } from "lucide-react";

import { cn } from "@/lib/utils";

interface DocumentUploadProps {
  onUpload: (file: File) => void;
  /** True while an upload is in flight — disables further uploads and
   * shows a busy state. */
  uploading: boolean;
}

/** Upload dropzone for the Knowledge Base page. */
export function DocumentUpload({ onUpload, uploading }: DocumentUploadProps) {
  const inputId = useId();
  const [isDragOver, setIsDragOver] = useState(false);

  function handleFiles(fileList: FileList | null) {
    const file = fileList?.[0];
    if (file && !uploading) {
      onUpload(file);
    }
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setIsDragOver(false);
    handleFiles(event.dataTransfer.files);
  }

  return (
    <div
      className={cn("kb-dropzone", isDragOver && "kb-dropzone--active")}
      data-state={uploading ? "uploading" : "idle"}
      onDragOver={(event) => {
        event.preventDefault();
        setIsDragOver(true);
      }}
      onDragLeave={() => setIsDragOver(false)}
      onDrop={handleDrop}
    >
      <UploadCloud aria-hidden="true" size={22} />

      <div className="kb-dropzone-copy">
        <p className="kb-dropzone-title">
          {uploading
            ? "Uploading and indexing…"
            : "Drop a document to add it to the knowledge base"}
        </p>
        <p className="kb-dropzone-hint">
          or{" "}
          <label htmlFor={inputId} className="kb-dropzone-browse">
            browse files
          </label>
        </p>
      </div>

      <input
        id={inputId}
        type="file"
        className="kb-dropzone-input"
        disabled={uploading}
        onChange={(event) => {
          handleFiles(event.target.files);
          event.target.value = "";
        }}
      />
    </div>
  );
}
