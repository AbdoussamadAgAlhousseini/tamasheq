"use client";

import { useSyncExternalStore } from "react";

import { getServerSnapshot, getSnapshot, subscribe } from "./preferences";

/** Préférences courantes, pour les textes qui ne peuvent pas utiliser <T> (options, attributs). */
export function usePreferences() {
  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}
