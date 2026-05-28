import { serverFetch, type Offre } from "@/lib/api";
import SimulateurForm from "./SimulateurForm";

export const dynamic = "force-dynamic";

interface OptS {
  id: number; code: string; nom: string; categorie: string; type_ligne: string;
  vente_setup: string; vente_mensuel: string; setup_achat: string; mensuel_achat: string;
  statut: string; commentaire: string | null; ordre: number;
}

export default async function SimulateurPage() {
  let offres: Offre[] = [];
  try { offres = await serverFetch<Offre[]>("/offres/"); } catch {}

  // Pre-charger les options pour toutes les offres (pour eviter un rechargement au changement d'offre)
  const optionsByOffre: Record<number, OptS[]> = {};
  for (const o of offres) {
    try {
      optionsByOffre[o.id] = await serverFetch<OptS[]>(`/offres/${o.id}/options`);
    } catch {}
  }

  return <SimulateurForm offres={offres} optionsByOffre={optionsByOffre} />;
}
