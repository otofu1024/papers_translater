import { useEffect, useState } from "react";
import { JobPage } from "./pages/JobPage";
import { UploadPage } from "./pages/UploadPage";

function readJobIdFromUrl(): string | null {
  const params = new URLSearchParams(window.location.search);
  return params.get("job_id");
}

function writeJobIdToUrl(jobId: string | null): void {
  const nextUrl = new URL(window.location.href);
  if (jobId) {
    nextUrl.searchParams.set("job_id", jobId);
  } else {
    nextUrl.searchParams.delete("job_id");
  }
  window.history.pushState({}, "", nextUrl);
}

export default function App() {
  const [jobId, setJobId] = useState<string | null>(readJobIdFromUrl());

  useEffect(() => {
    const handler = () => setJobId(readJobIdFromUrl());
    window.addEventListener("popstate", handler);
    return () => window.removeEventListener("popstate", handler);
  }, []);

  const handleJobCreated = (nextJobId: string) => {
    writeJobIdToUrl(nextJobId);
    setJobId(nextJobId);
  };

  const handleReset = () => {
    writeJobIdToUrl(null);
    setJobId(null);
  };

  return (
    <main className="app-root">
      <div className="background-grid" />
      <section className="shell">
        <header className="app-header">
          <h1>PDF Translate Local</h1>
          <p>Scan PDF to OCR to Translation to Markdown</p>
        </header>
        {jobId ? (
          <JobPage jobId={jobId} onReset={handleReset} />
        ) : (
          <UploadPage onJobCreated={handleJobCreated} />
        )}
      </section>
    </main>
  );
}
