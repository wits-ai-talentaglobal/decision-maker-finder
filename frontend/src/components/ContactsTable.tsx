import { useState } from "react";
import type { Company } from "../types";

function CompanyRow({ company }: { company: Company }) {
  const [expanded, setExpanded] = useState(true);

  return (
    <>
      <tr
        onClick={() => setExpanded((e) => !e)}
        style={{ cursor: "pointer", backgroundColor: "#f8fafc", borderTop: "1px solid #e2e8f0" }}
      >
        <td colSpan={6} style={{ padding: 8, fontWeight: 600 }}>
          {expanded ? "▾" : "▸"} {company.name} ({company.contacts.length} contact
          {company.contacts.length === 1 ? "" : "s"}) — {company.website}
          {company.city && company.state ? ` · ${company.city}, ${company.state}` : ""}
        </td>
      </tr>
      {expanded &&
        company.contacts.map((contact) => (
          <tr key={contact.id} style={{ borderBottom: "1px solid #f1f5f9" }}>
            <td style={{ padding: "6px 8px 6px 24px" }}>
              {contact.first_name} {contact.last_name}
            </td>
            <td style={{ padding: 8 }}>{contact.title}</td>
            <td style={{ padding: 8 }}>
              {contact.linkedin_url ? (
                <a href={contact.linkedin_url} target="_blank" rel="noreferrer">
                  LinkedIn
                </a>
              ) : (
                "—"
              )}
            </td>
            <td style={{ padding: 8 }}>{contact.email ?? "—"}</td>
            <td style={{ padding: 8 }}>{contact.phone ?? "—"}</td>
            <td style={{ padding: 8, fontSize: 12, color: "#64748b" }}>
              {contact.email_status ?? ""}
            </td>
          </tr>
        ))}
    </>
  );
}

export function ContactsTable({ companies }: { companies: Company[] }) {
  const companiesWithContacts = companies.filter((c) => c.contacts.length > 0);

  if (companiesWithContacts.length === 0) {
    return <p style={{ color: "#64748b" }}>No verified contacts yet.</p>;
  }

  return (
    <table style={{ width: "100%", borderCollapse: "collapse" }}>
      <thead>
        <tr style={{ textAlign: "left", borderBottom: "1px solid #e2e8f0" }}>
          <th style={{ padding: 8 }}>Name</th>
          <th style={{ padding: 8 }}>Title</th>
          <th style={{ padding: 8 }}>LinkedIn</th>
          <th style={{ padding: 8 }}>Email</th>
          <th style={{ padding: 8 }}>Phone</th>
          <th style={{ padding: 8 }}>Email status</th>
        </tr>
      </thead>
      <tbody>
        {companiesWithContacts.map((company) => (
          <CompanyRow key={company.id} company={company} />
        ))}
      </tbody>
    </table>
  );
}
