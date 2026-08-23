export type JobStatus =
  | "queued"
  | "resolving_company"
  | "scraping_employees"
  | "identifying_decision_makers"
  | "enriching_contacts"
  | "done"
  | "failed";

export interface Contact {
  id: number;
  first_name: string;
  last_name: string;
  title: string;
  linkedin_url: string | null;
  apollo_id: string | null;
  email: string | null;
  email_status: string | null;
  phone: string | null;
  source_stage: string;
  created_at: string;
}

export interface Company {
  id: number;
  name: string;
  website: string;
  linkedin_url: string | null;
  city: string | null;
  state: string | null;
  resolved_confidence: number | null;
  contacts: Contact[];
}

export interface Job {
  id: number;
  input_url: string;
  normalized_domain: string;
  status: JobStatus;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  company: Company | null;
}

export interface BatchEstimate {
  url_count: number;
  invalid_entries: string[];
  estimated_apify_calls: number;
  estimated_llm_calls: number;
  estimated_apollo_calls: number;
  estimated_hunter_calls: number;
  requires_confirmation: boolean;
}

export interface ClearJobsResult {
  deleted_jobs: number;
  deleted_companies: number;
  deleted_contacts: number;
}

export interface JobUpdateMessage {
  type: "job_update";
  job_id: number;
  status: JobStatus;
  error?: string;
  contact_count?: number;
}
