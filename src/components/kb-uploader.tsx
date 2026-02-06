"use client";

import * as React from "react";
import { Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { getSupabaseBrowserClient } from "@/lib/supabase/client";

export function KbUploader() {
  const [file, setFile] = React.useState<File | null>(null);
  const [status, setStatus] = React.useState<string | null>(null);
  const [isUploading, setIsUploading] = React.useState(false);

  const handleUpload = async () => {
    if (!file) return;
    setIsUploading(true);
    setStatus(null);
    const supabase = getSupabaseBrowserClient();
    if (!supabase) {
      setStatus("Supabase not configured.");
      setIsUploading(false);
      return;
    }

    const path = `kb/${Date.now()}-${file.name}`;
    const { error: uploadError } = await supabase.storage
      .from("kb-documents")
      .upload(path, file);

    if (uploadError) {
      setStatus(uploadError.message);
      setIsUploading(false);
      return;
    }

    const content = await file.text();
    const { error: ingestError } = await supabase.functions.invoke("kb-ingest", {
      body: {
        title: file.name,
        storage_path: path,
        content,
        mime_type: file.type || "text/plain",
      },
    });

    if (ingestError) {
      setStatus(ingestError.message);
    } else {
      setStatus("Uploaded and indexed.");
    }
    setIsUploading(false);
  };

  return (
    <Card className="glass-card p-5">
      <div className="text-sm font-semibold">Upload Document</div>
      <div className="mt-3 text-xs text-muted-foreground">
        Documents are chunked and indexed with citations.
      </div>
      <div className="mt-4 flex flex-col gap-3">
        <Input
          type="file"
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
        />
        <Button onClick={handleUpload} disabled={!file || isUploading} className="rounded-full">
          <Upload className="mr-2 h-4 w-4" />
          {isUploading ? "Uploading..." : "Upload & Index"}
        </Button>
        {status && <div className="text-xs text-muted-foreground">{status}</div>}
      </div>
    </Card>
  );
}
