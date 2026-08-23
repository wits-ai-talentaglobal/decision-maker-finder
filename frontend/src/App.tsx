import { useCallback, useEffect, useState } from "react";
import { fetchCompanies, fetchJobs, isBatchEstimate, submitJobs } from "./api";
import { ClearAllButton } from "./components/ClearAllButton";
import { ContactsTable } from "./components/ContactsTable";
import { CsvExportButton } from "./components/CsvExportButton";
import { JobList } from "./components/JobList";
import { UrlInputPanel } from "./components/UrlInputPanel";
import { useJobsSocket } from "./hooks/useJobsSocket";
import type { BatchEstimate, Company, Job } from "./types";

async function refreshAll(setJobs: (jobs: Job[]) => void, setCompanies: (c: Company[]) => void) {
  const [jobs, companies] = await Promise.all([fetchJobs(), fetchCompanies()]);
  setJobs(jobs);
  setCompanies(companies);
}

export default function App() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [companies, setCompanies] = useState<Company[]>([]);

  useEffect(() => {
    refreshAll(setJobs, setCompanies);
  }, []);

  // Live per-stage status arrives over the WebSocket; on any update we simply
  // re-fetch — the dataset is small enough that this stays snappy, and it keeps
  // the client free of hand-rolled partial-state merge logic.
  const handleWsUpdate = useCallback(() => {
    refreshAll(setJobs, setCompanies);
  }, []);
  useJobsSocket(handleWsUpdate);

  async function handleSubmit(urlsText: string, confirmed: boolean): Promise<BatchEstimate | null> {
    const result = await submitJobs(urlsText, confirmed);
    if (isBatchEstimate(result)) {
      return result;
    }
    await refreshAll(setJobs, setCompanies);
    return null;
  }

  return (
    <div style={{ maxWidth: 1000, margin: "0 auto", padding: 24, fontFamily: "system-ui, sans-serif" }}>
      <h1>Decision-Maker Finder</h1>
      <p style={{ color: "#64748b" }}>
        Paste one or more company website URLs to find verified sales, ownership, and
        general-management contacts.
      </p>

      <section style={{ marginBottom: 32 }}>
        <UrlInputPanel onSubmit={handleSubmit} />
      </section>

      <section style={{ marginBottom: 32 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h2>Jobs</h2>
          <ClearAllButton
            disabled={jobs.length === 0 && companies.length === 0}
            onCleared={() => refreshAll(setJobs, setCompanies)}
          />
        </div>
        <JobList jobs={jobs} />
      </section>

      <section>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h2>Contacts</h2>
          <CsvExportButton companies={companies} />
        </div>
        <ContactsTable companies={companies} />
      </section>
    </div>
  );
}
