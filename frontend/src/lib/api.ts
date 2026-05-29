// URL absolue vers le backend — utilisee cote serveur (Server Components + Server Actions)
const BACKEND = "http://127.0.0.1:8000/api";

// URL relative — utilisee cote client (navigateur) via le proxy Next.js
const CLIENT_API = "/api";

export async function serverFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${BACKEND}${path}`, {
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`API ${res.status}`);
  return res.json();
}

export async function serverPost<T>(path: string, body: Record<string, unknown>): Promise<T> {
  const res = await fetch(`${BACKEND}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
  return res.json();
}

export async function serverPatch<T>(path: string, body: Record<string, unknown>): Promise<T> {
  const res = await fetch(`${BACKEND}${path}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
  return res.json();
}

export async function serverDelete(path: string): Promise<void> {
  const res = await fetch(`${BACKEND}${path}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
}

export async function clientFetch<T>(path: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(`${CLIENT_API}${path}`, {
    headers: { "Content-Type": "application/json", ...opts?.headers },
    ...opts,
  });
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
  return res.json();
}

export interface Offre {
  id: number; nom: string; type_site: string; type_offre: string;
  tarif_achat: number; taux_marge: number; tarif_vente_conseille: number;
  pages: number; heures: number; commission_apporteur: number;
  actif: boolean; ordre: number;
}

export interface Option {
  id: number; code: string; nom: string; categorie: string; type_ligne: string;
  vente_setup: number; vente_mensuel: number; setup_achat: number; mensuel_achat: number;
  taux_marge: number; prix_heure: number; heures_setup: number; heures_mensuel: number;
  prix_hebergement: number; commentaire: string | null; selection_regle: string;
  quantite_defaut: number; unite: string; actif: boolean; ordre: number;
}

export interface Client {
  id: number; raison_sociale: string; adresse: string | null;
  code_postal: string | null; ville: string | null;
  interlocuteur: string | null; telephone: string | null;
  email: string | null; siret: string | null; actif: boolean;
}
