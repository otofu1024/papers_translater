type ProgressProps = {
  label: string;
  value: number;
};

export function Progress({ label, value }: ProgressProps) {
  const percent = Math.max(0, Math.min(100, Math.round(value * 100)));
  return (
    <section className="progress-card">
      <div className="progress-head">
        <span>{label}</span>
        <strong>{percent}%</strong>
      </div>
      <div className="progress-track">
        <div className="progress-fill" style={{ width: `${percent}%` }} />
      </div>
    </section>
  );
}

