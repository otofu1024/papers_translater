import { useEffect, useMemo, useState } from "react";
import { getJob, getResultDownloadUrl, getResultMarkdown, type JobMeta } from "../api/client";
import { MarkdownViewer } from "../components/MarkdownViewer";
import { Progress } from "../components/Progress";

type JobPageProps = {
  jobId: string;
  onReset: () => void;
};

export function JobPage({ jobId, onReset }: JobPageProps) {
  const [job, setJob] = useState<JobMeta | null>(null);
  const [markdown, setMarkdown] = useState("");
  const [error, setError] = useState<string | null>(null);

  const terminal = job?.status === "succeeded" || job?.status === "failed";

  useEffect(() => {
    let active = true;
    let timer: number | null = null;

    const poll = async () => {
      try {
        const latest = await getJob(jobId);
        if (!active) {
          return;
        }
        setJob(latest);
        if (latest.status === "succeeded") {
          const md = await getResultMarkdown(jobId);
          if (!active) {
            return;
          }
          setMarkdown(md);
          return;
        }
        if (latest.status === "failed") {
          return;
        }
      } catch (err) {
        if (!active) {
          return;
        }
        setError(err instanceof Error ? err.message : "Failed to fetch job status.");
        return;
      }
      timer = window.setTimeout(poll, 2000);
    };

    poll();
    return () => {
      active = false;
      if (timer !== null) {
        window.clearTimeout(timer);
      }
    };
  }, [jobId]);

  const statusColor = useMemo(() => {
    if (!job) {
      return "status-pending";
    }
    if (job.status === "succeeded") {
      return "status-ok";
    }
    if (job.status === "failed") {
      return "status-failed";
    }
    return "status-pending";
  }, [job]);

  return (
    <section className="stack">
      <section className="card stack">
        <div className="row">
          <h2>Job {jobId}</h2>
          <button type="button" onClick={onReset}>
            New Upload
          </button>
        </div>
        <p className={`pill ${statusColor}`}>Status: {job?.status ?? "loading"}</p>
        <p className="muted">Stage: {job?.stage ?? "..."}</p>
        <Progress label="Progress" value={job?.progress ?? 0} />
        {job?.error ? <p className="error">{job.error}</p> : null}
        {error ? <p className="error">{error}</p> : null}
      </section>

      <section className="card stack">
        <div className="row">
          <h2>Result Markdown</h2>
          <a href={getResultDownloadUrl(jobId)} download={!terminal ? undefined : `${jobId}.md`}>
            Download
          </a>
        </div>
        {job?.status === "succeeded" ? (
          <MarkdownViewer markdown={markdown} />
        ) : (
          <p className="muted">Result will appear after job completion.</p>
        )}
      </section>
    </section>
  );
}

