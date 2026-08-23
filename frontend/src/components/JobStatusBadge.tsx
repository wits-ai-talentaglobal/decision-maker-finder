import type { JobStatus } from "../types";

const STATUS_LABELS: Record<JobStatus, string> = {
  queued: "Queued",
  resolving_company: "Resolving company",
  scraping_employees: "Scraping employees",
  identifying_decision_makers: "Identifying decision-makers",
  enriching_contacts: "Enriching contacts",
  done: "Done",
  failed: "Failed",
};

const STATUS_COLORS: Record<JobStatus, string> = {
  queued: "#94a3b8",
  resolving_company: "#3b82f6",
  scraping_employees: "#3b82f6",
  identifying_decision_makers: "#3b82f6",
  enriching_contacts: "#3b82f6",
  done: "#22c55e",
  failed: "#ef4444",
};

export function JobStatusBadge({ status }: { status: JobStatus }) {
  return (
    <span
      style={{
        display: "inline-block",
        padding: "2px 10px",
        borderRadius: 999,
        fontSize: 12,
        fontWeight: 600,
        color: "white",
        backgroundColor: STATUS_COLORS[status],
        whiteSpace: "nowrap",
      }}
    >
      {STATUS_LABELS[status]}
    </span>
  );
}
