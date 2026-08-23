import type { Company } from "../types";

const CSV_HEADERS = [
  "company_name",
  "website",
  "city",
  "state",
  "first_name",
  "last_name",
  "title",
  "linkedin_url",
  "email",
  "email_status",
  "phone",
];

function csvEscape(value: string): string {
  if (value.includes(",") || value.includes('"') || value.includes("\n")) {
    return `"${value.replace(/"/g, '""')}"`;
  }
  return value;
}

function buildCsv(companies: Company[]): string {
  const rows = [CSV_HEADERS.join(",")];

  for (const company of companies) {
    for (const contact of company.contacts) {
      rows.push(
        [
          company.name,
          company.website,
          company.city ?? "",
          company.state ?? "",
          contact.first_name,
          contact.last_name,
          contact.title,
          contact.linkedin_url,
          contact.email ?? "",
          contact.email_status ?? "",
          contact.phone ?? "",
        ]
          .map((value) => csvEscape(String(value)))
          .join(",")
      );
    }
  }

  return rows.join("\n");
}

export function CsvExportButton({ companies }: { companies: Company[] }) {
  function handleExport() {
    const csv = buildCsv(companies);
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "decision-maker-contacts.csv";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  const hasContacts = companies.some((c) => c.contacts.length > 0);

  return (
    <button onClick={handleExport} disabled={!hasContacts}>
      Export CSV
    </button>
  );
}
