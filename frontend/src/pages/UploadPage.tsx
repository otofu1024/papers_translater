import { useState } from "react";
import { createJob } from "../api/client";
import { Dropzone } from "../components/Dropzone";

type UploadPageProps = {
  onJobCreated: (jobId: string) => void;
};

export function UploadPage({ onJobCreated }: UploadPageProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!selectedFile) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const created = await createJob(selectedFile);
      onJobCreated(created.job_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create job.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="card stack">
      <h2>Upload PDF</h2>
      <Dropzone disabled={loading} onFileSelected={setSelectedFile} />
      <div className="row">
        <span className="filename">{selectedFile?.name ?? "No file selected"}</span>
        <button type="button" onClick={handleSubmit} disabled={!selectedFile || loading}>
          {loading ? "Creating..." : "Start Job"}
        </button>
      </div>
      {error ? <p className="error">{error}</p> : null}
    </section>
  );
}

