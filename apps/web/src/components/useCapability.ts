"use client";

import { useEffect, useState } from "react";

import { type CapabilityName, type CapabilityStatus, fetchCapabilities } from "@/lib/capabilities";

export function useCapability(name: CapabilityName): CapabilityStatus | "loading" | "error" {
  const [status, setStatus] = useState<CapabilityStatus | "loading" | "error">("loading");
  useEffect(() => {
    fetchCapabilities()
      .then((all) => setStatus(all.find((c) => c.name === name)?.status ?? "not_available"))
      .catch(() => setStatus("error"));
  }, [name]);
  return status;
}
