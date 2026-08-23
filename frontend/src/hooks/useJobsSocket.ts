import { useEffect, useRef } from "react";
import type { JobUpdateMessage } from "../types";

export function useJobsSocket(onUpdate: (message: JobUpdateMessage) => void): void {
  const onUpdateRef = useRef(onUpdate);
  onUpdateRef.current = onUpdate;

  useEffect(() => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const socket = new WebSocket(`${protocol}//${window.location.host}/ws/jobs`);

    socket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as JobUpdateMessage;
        if (message.type === "job_update") {
          onUpdateRef.current(message);
        }
      } catch {
        // ignore malformed messages
      }
    };

    return () => socket.close();
  }, []);
}
