import { useState } from "react";
import { clearJobs } from "../api";

interface ClearAllButtonProps {
  disabled: boolean;
  onCleared: () => void;
}

export function ClearAllButton({ disabled, onCleared }: ClearAllButtonProps) {
  const [clearing, setClearing] = useState(false);

  async function handleClick() {
    if (!window.confirm("Clear all jobs and contacts? This can't be undone.")) {
      return;
    }
    setClearing(true);
    try {
      await clearJobs();
      onCleared();
    } finally {
      setClearing(false);
    }
  }

  return (
    <button onClick={handleClick} disabled={disabled || clearing}>
      {clearing ? "Clearing…" : "Clear all"}
    </button>
  );
}
