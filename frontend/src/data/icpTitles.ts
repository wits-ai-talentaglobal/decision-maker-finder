export const EXECUTIVE_TITLES = [
  "CEO",
  "Founder",
  "Owner",
  "President",
  "CRO",
  "CMO",
  "COO",
  "CFO",
  "CHRO",
  "CTO",
  "CCO",
] as const;

export const DEPARTMENT_TITLES: Record<string, readonly string[]> = {
  Sales: [
    "VP of Sales",
    "Director of Sales",
    "Regional Sales Manager",
    "Sales Manager",
    "Senior Account Executive",
    "Account Executive",
  ],
  Marketing: [
    "VP of Marketing",
    "Director of Marketing",
    "Marketing Manager",
    "Senior Marketing Specialist",
    "Marketing Specialist",
  ],
  Operations: [
    "VP of Operations",
    "Director of Operations",
    "Operations Manager",
    "Senior Operations Analyst",
    "Operations Analyst",
  ],
  Finance: [
    "VP of Finance",
    "Director of Finance",
    "Controller",
    "Finance Manager",
    "Senior Financial Analyst",
    "Financial Analyst",
  ],
  "Human Resources": [
    "VP of HR",
    "Director of HR",
    "HR Business Partner",
    "HR Manager",
    "Senior HR Generalist",
    "HR Generalist",
  ],
  "IT/Engineering": [
    "VP of Engineering",
    "Director of Engineering",
    "Engineering Manager",
    "Staff Engineer / Tech Lead",
    "Senior Engineer",
    "Engineer",
  ],
  "Customer Success": [
    "VP of Customer Success",
    "Director of Customer Success",
    "Customer Success Manager",
    "Senior CSM",
    "CSM",
  ],
};

export const DEPARTMENT_NAMES = Object.keys(DEPARTMENT_TITLES);

// The top-ranked title in a department's hierarchy (index 0) is the closest thing
// to a "department head" — there's no separate literal title for that concept, so
// any UI that needs to display it should derive it here rather than hardcoding one.
export function getDepartmentHead(department: string): string | undefined {
  return DEPARTMENT_TITLES[department]?.[0];
}
