"use client";

import { useSyncExternalStore } from "react";

import {
  getServerSnapshot,
  getSnapshot,
  type Script,
  setPreference,
  subscribe,
  type UiLang,
} from "@/lib/preferences";

import { T } from "./T";

function Toggle<V extends string>({
  label,
  options,
  value,
  onChange,
}: {
  label: React.ReactNode;
  options: { value: V; label: React.ReactNode; lang?: string }[];
  value: V;
  onChange: (value: V) => void;
}) {
  return (
    <fieldset className="flex items-center gap-2">
      <legend className="sr-only">{label}</legend>
      <span aria-hidden="true" className="text-xs text-muted">
        {label}
      </span>
      <div className="flex rounded-md border border-line p-0.5">
        {options.map((option) => (
          <button
            key={option.value}
            type="button"
            lang={option.lang}
            aria-pressed={value === option.value}
            onClick={() => onChange(option.value)}
            className="rounded px-2 py-1 text-sm aria-pressed:bg-accent aria-pressed:text-on-accent"
          >
            {option.label}
          </button>
        ))}
      </div>
    </fieldset>
  );
}

export function Preferences() {
  const prefs = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);

  return (
    <div className="flex flex-wrap items-center gap-4">
      <Toggle<UiLang>
        label={<T fr="Langue" en="Language" />}
        value={prefs.lang}
        onChange={(v) => setPreference("lang", v)}
        options={[
          { value: "fr", label: "FR", lang: "fr" },
          { value: "en", label: "EN", lang: "en" },
        ]}
      />
      <Toggle<Script>
        label={<T fr="Écriture tamasheq" en="Tamasheq script" />}
        value={prefs.script}
        onChange={(v) => setPreference("script", v)}
        options={[
          { value: "latn", label: <T fr="Latin" en="Latin" /> },
          { value: "tfng", label: <T fr="Tifinagh" en="Tifinagh" /> },
        ]}
      />
    </div>
  );
}
