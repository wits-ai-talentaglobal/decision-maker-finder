export const EXECUTIVE_TITLES = ["CEO", "Founder", "Owner", "President"] as const;

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
    "Finance Manager",
    "Senior Financial Analyst",
    "Financial Analyst",
  ],
  "Human Resources": [
    "VP of HR",
    "Director of HR",
    "HR Manager",
    "Senior HR Generalist",
    "HR Generalist",
  ],
  "IT/Engineering": [
    "VP of Engineering",
    "Director of Engineering",
    "Engineering Manager",
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
