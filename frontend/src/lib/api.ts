// Appels en relatif — Next.js proxifie /api/* vers le backend (port 8000)
const API = "/api";

async function fetchAPI<T>(path: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
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
  commentaire: string | null; selection_regle: string; actif: boolean; ordre: number;
}

export interface Client {
  id: number; raison_sociale: string; adresse: string | null;
  code_postal: string | null; ville: string | null;
  interlocuteur: string | null; telephone: string | null;
  email: string | null; siret: string | null; actif: boolean;
}

export const api = {
  offres: {
    list: () => fetchAPI<Offre[]>("/offres/"),
    create: (d: Partial<Offre>) => fetchAPI<Offre>("/offres/", { method: "POST", body: JSON.stringify(d) }),
    update: (id: number, d: Partial<Offre>) => fetchAPI<Offre>(`/offres/${id}`, { method: "PATCH", body: JSON.stringify(d) }),
    delete: (id: number) => fetch(`${API}/offres/${id}`, { method: "DELETE" }),
  },
  options: {
    list: (cat?: string) => fetchAPI<Option[]>(`/options/${cat ? "?categorie=" + cat : ""}`),
    create: (d: Partial<Option>) => fetchAPI<Option>("/options/", { method: "POST", body: JSON.stringify(d) }),
    update: (id: number, d: Partial<Option>) => fetchAPI<Option>(`/options/${id}`, { method: "PATCH", body: JSON.stringify(d) }),
  },
  clients: {
    list: (q?: string) => fetchAPI<Client[]>(`/clients/${q ? "?q=" + q : ""}`),
    create: (d: Partial<Client>) => fetchAPI<Client>("/clients/", { method: "POST", body: JSON.stringify(d) }),
    update: (id: number, d: Partial<Client>) => fetchAPI<Client>(`/clients/${id}`, { method: "PATCH", body: JSON.stringify(d) }),
  },
  simulation: {
    run: (d: Record<string, unknown>) => fetchAPI<Record<string, number>>("/simulation/", { method: "POST", body: JSON.stringify(d) }),
  },
  generation: {
    facture: async (d: Record<string, unknown>): Promise<Blob> => {
      const res = await fetch(`${API}/generation/facture`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(d) });
      if (!res.ok) throw new Error(`Generation ${res.status}`);
      return res.blob();
    },
  },
};
