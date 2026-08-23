import { useMemo, useState } from "react";
import { parseUrlList } from "../normalize";
import type { BatchEstimate } from "../types";

interface UrlInputPanelProps {
  onSubmit: (urlsText: string, confirmed: boolean) => Promise<BatchEstimate | null>;
}

export function UrlInputPanel({ onSubmit }: UrlInputPanelProps) {
  const [urlsText, setUrlsText] = useState("");
  const [pendingEstimate, setPendingEstimate] = useState<BatchEstimate | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const parsed = useMemo(() => parseUrlList(urlsText), [urlsText]);

  async function handleSubmit(confirmed: boolean) {
    setSubmitting(true);
    setError(null);
    try {
      const estimate = await onSubmit(urlsText, confirmed);
      if (estimate) {
        setPendingEstimate(estimate);
      } else {
        setPendingEstimate(null);
        setUrlsText("");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      <label htmlFor="urls-input" style={{ fontWeight: 600 }}>
        Website URLs (one per line, or comma/space separated)
      </label>
      <textarea
        id="urls-input"
        value={urlsText}
        onChange={(e) => setUrlsText(e.target.value)}
        rows={6}
        placeholder={"acme-motors.com\nhttps://example-dealership.com\nfoo.com, bar.com"}
        style={{ fontFamily: "monospace", fontSize: 14, padding: 8 }}
      />

      <div style={{ fontSize: 13, color: "#64748b" }}>
        {parsed.valid.length} valid URL{parsed.valid.length === 1 ? "" : "s"}
        {parsed.invalid.length > 0 && (
          <span style={{ color: "#ef4444" }}>
            {" "}
            — {parsed.invalid.length} malformed: {parsed.invalid.join(", ")}
          </span>
        )}
      </div>

      {error && <div style={{ color: "#ef4444" }}>{error}</div>}

      <button
        onClick={() => handleSubmit(false)}
        disabled={submitting || parsed.valid.length === 0}
        style={{ alignSelf: "flex-start", padding: "8px 16px" }}
      >
        {submitting ? "Submitting…" : "Find decision-makers"}
      </button>

      {pendingEstimate && (
        <div
          role="dialog"
          aria-label="Confirm batch run"
          style={{
            border: "1px solid #e2e8f0",
            borderRadius: 8,
            padding: 16,
            marginTop: 8,
            backgroundColor: "#f8fafc",
          }}
        >
          <p style={{ marginTop: 0, fontWeight: 600 }}>
            This batch of {pendingEstimate.url_count} websites will make an estimated:
          </p>
          <ul>
            <li>{pendingEstimate.estimated_apify_calls} Apify calls</li>
            <li>{pendingEstimate.estimated_llm_calls} LLM calls (OpenRouter + Claude)</li>
            <li>{pendingEstimate.estimated_apollo_calls} Apollo.io calls</li>
            <li>{pendingEstimate.estimated_hunter_calls} Hunter.io calls</li>
          </ul>
          <div style={{ display: "flex", gap: 8 }}>
            <button onClick={() => handleSubmit(true)} disabled={submitting}>
              Confirm and run
            </button>
            <button onClick={() => setPendingEstimate(null)} disabled={submitting}>
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
