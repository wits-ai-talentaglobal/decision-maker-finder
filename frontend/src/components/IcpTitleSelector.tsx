import { useState } from "react";
import { DEPARTMENT_NAMES, DEPARTMENT_TITLES, EXECUTIVE_TITLES } from "../data/icpTitles";
import type { TargetTitles } from "../types";

interface IcpTitleSelectorProps {
  onChange: (value: TargetTitles) => void;
}

function slugify(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, "-");
}

const fieldsetStyle = {
  border: "1px solid #e2e8f0",
  borderRadius: 8,
  padding: 12,
  display: "flex",
  flexDirection: "column" as const,
  gap: 6,
};

const legendStyle = { fontWeight: 600, padding: "0 4px" };

const checkboxRowStyle = { display: "flex", alignItems: "center", gap: 6 };

export function IcpTitleSelector({ onChange }: IcpTitleSelectorProps) {
  const [executiveSelected, setExecutiveSelected] = useState<string[]>([]);
  const [departmentBlocks, setDepartmentBlocks] = useState<string[]>([]);
  const [departmentSelections, setDepartmentSelections] = useState<Record<string, string[]>>({});

  function emitChange(nextExecutive: string[], nextDepartments: Record<string, string[]>) {
    onChange({ executive: nextExecutive, departments: nextDepartments });
  }

  function toggleExecutive(title: string, checked: boolean) {
    const next = checked
      ? [...executiveSelected, title]
      : executiveSelected.filter((t) => t !== title);
    setExecutiveSelected(next);
    emitChange(next, departmentSelections);
  }

  function addDepartment(department: string) {
    if (!department || departmentBlocks.includes(department)) return;
    const nextBlocks = [...departmentBlocks, department];
    const nextSelections = { ...departmentSelections, [department]: [] };
    setDepartmentBlocks(nextBlocks);
    setDepartmentSelections(nextSelections);
    emitChange(executiveSelected, nextSelections);
  }

  function removeDepartment(department: string) {
    const nextBlocks = departmentBlocks.filter((d) => d !== department);
    const nextSelections = { ...departmentSelections };
    delete nextSelections[department];
    setDepartmentBlocks(nextBlocks);
    setDepartmentSelections(nextSelections);
    emitChange(executiveSelected, nextSelections);
  }

  function toggleDepartmentTitle(department: string, title: string, checked: boolean) {
    const current = departmentSelections[department] ?? [];
    const nextTitles = checked ? [...current, title] : current.filter((t) => t !== title);
    const nextSelections = { ...departmentSelections, [department]: nextTitles };
    setDepartmentSelections(nextSelections);
    emitChange(executiveSelected, nextSelections);
  }

  const availableDepartments = DEPARTMENT_NAMES.filter((d) => !departmentBlocks.includes(d));

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      <fieldset style={fieldsetStyle}>
        <legend style={legendStyle}>Executive Title</legend>
        {EXECUTIVE_TITLES.map((title) => {
          const id = `icp-exec-${slugify(title)}`;
          return (
            <div key={title} style={checkboxRowStyle}>
              <input
                id={id}
                type="checkbox"
                checked={executiveSelected.includes(title)}
                onChange={(e) => toggleExecutive(title, e.target.checked)}
              />
              <label htmlFor={id}>{title}</label>
            </div>
          );
        })}
      </fieldset>

      <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        <label htmlFor="icp-department-select" style={{ fontWeight: 600 }}>
          Department
        </label>
        <select
          id="icp-department-select"
          value=""
          onChange={(e) => addDepartment(e.target.value)}
          style={{ padding: 6, alignSelf: "flex-start" }}
        >
          <option value="">Add a department…</option>
          {availableDepartments.map((department) => (
            <option key={department} value={department}>
              {department}
            </option>
          ))}
        </select>
      </div>

      {departmentBlocks.map((department) => (
        <fieldset key={department} style={fieldsetStyle}>
          <legend style={legendStyle}>{department}</legend>
          <button
            type="button"
            aria-label={`Remove ${department}`}
            onClick={() => removeDepartment(department)}
            style={{ alignSelf: "flex-start", padding: "4px 10px" }}
          >
            Remove
          </button>
          {DEPARTMENT_TITLES[department].map((title) => {
            const id = `icp-dept-${slugify(department)}-${slugify(title)}`;
            return (
              <div key={title} style={checkboxRowStyle}>
                <input
                  id={id}
                  type="checkbox"
                  checked={(departmentSelections[department] ?? []).includes(title)}
                  onChange={(e) => toggleDepartmentTitle(department, title, e.target.checked)}
                />
                <label htmlFor={id}>{title}</label>
              </div>
            );
          })}
        </fieldset>
      ))}
    </div>
  );
}
