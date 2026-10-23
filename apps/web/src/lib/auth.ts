// Connexion par jeton (créé par l'administration). Le jeton est gardé dans le sessionStorage :
// il disparaît à la fermeture de l'onglet et n'est envoyé qu'à l'API, dans l'en-tête
// Authorization. Une vraie connexion (lien par e-mail ou mot de passe) viendra plus tard.
import { API_URL } from "./capabilities";

const KEY = "tamasheq.token";

export type Account = { pseudonym: string; role: "contributor" | "reviewer" | "admin" };
export type AuthState = { token: string; account: Account } | null;

let state: AuthState = null;
let loaded = false;
const listeners = new Set<() => void>();

function emit() {
  listeners.forEach((l) => l());
}

export function subscribeAuth(listener: () => void): () => void {
  listeners.add(listener);
  if (!loaded) {
    loaded = true;
    let token: string | null = null;
    try {
      token = sessionStorage.getItem(KEY);
    } catch {
      token = null;
    }
    if (token) void signIn(token).catch(() => signOut());
  }
  return () => listeners.delete(listener);
}

export function getAuth(): AuthState {
  return state;
}

export function getServerAuth(): AuthState {
  return null;
}

/** Vérifie le jeton auprès de l'API avant de le garder. */
export async function signIn(token: string): Promise<Account> {
  const response = await fetch(`${API_URL}/api/v1/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new Error(response.status === 401 ? "invalid" : "network");
  const account = (await response.json()) as Account;
  state = { token, account };
  try {
    sessionStorage.setItem(KEY, token);
  } catch {
    // stockage indisponible : la connexion vaut pour cette page seulement
  }
  emit();
  return account;
}

export function signOut(): void {
  state = null;
  try {
    sessionStorage.removeItem(KEY);
  } catch {
    // rien à effacer
  }
  emit();
}
