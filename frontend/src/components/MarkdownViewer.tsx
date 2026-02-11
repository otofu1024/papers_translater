import ReactMarkdown from "react-markdown";

type MarkdownViewerProps = {
  markdown: string;
};

export function MarkdownViewer({ markdown }: MarkdownViewerProps) {
  return (
    <article className="markdown-panel">
      <ReactMarkdown>{markdown}</ReactMarkdown>
    </article>
  );
}

