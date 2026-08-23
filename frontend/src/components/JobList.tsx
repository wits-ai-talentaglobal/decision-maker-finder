import type { Job } from "../types";
import { JobStatusBadge } from "./JobStatusBadge";

export function JobList({ jobs }: { jobs: Job[] }) {
  if (jobs.length === 0) {
    return <p style={{ color: "#64748b" }}>No jobs submitted yet.</p>;
  }

  return (
    <table style={{ width: "100%", borderCollapse: "collapse" }}>
      <thead>
        <tr style={{ textAlign: "left", borderBottom: "1px solid #e2e8f0" }}>
          <th style={{ padding: 8 }}>Website</th>
          <th style={{ padding: 8 }}>Status</th>
          <th style={{ padding: 8 }}>Company</th>
          <th style={{ padding: 8 }}>Contacts</th>
          <th style={{ padding: 8 }}>Error</th>
        </tr>
      </thead>
      <tbody>
        {jobs.map((job) => (
          <tr key={job.id} style={{ borderBottom: "1px solid #f1f5f9" }}>
            <td style={{ padding: 8 }}>{job.normalized_domain}</td>
            <td style={{ padding: 8 }}>
              <JobStatusBadge status={job.status} />
            </td>
            <td style={{ padding: 8 }}>{job.company?.name ?? "—"}</td>
            <td style={{ padding: 8 }}>{job.company?.contacts.length ?? 0}</td>
            <td style={{ padding: 8, color: "#ef4444", fontSize: 12 }}>
              {job.error_message ?? ""}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
