import { serverFetch, type Offre, type Client } from "@/lib/api";
import SimulateurClient, { type OptS, type EditionInitial } from "../../simulateur/SimulateurClient";
import Link from "next/link";

export const dynamic = "force-dynamic";

// Reedition d'un devis existant : charge l'etat (GET /devis/{id}/edition),
// l'offre, ses options et les clients, puis rend le simulateur pre-rempli.
// La sauvegarde passe par /reviser (maj brouillon ou nouvelle version).
export default async function EditerDevisPage({ searchParams }: { searchParams: Promise<{ id?: string }> }) {
  const { id } = await searchParams;
  if (!id) {
    return <p className="text-red-600 p-4">Devis non specifie.</p>;
  }

  let initial: EditionInitial | null = null;
  try {
    initial = await serverFetch<EditionInitial>(`/devis/${id}/edition`);
  } catch {
    return (
      <div className="p-4">
        <p className="text-red-600">Devis introuvable.</p>
        <Link href="/devis" className="text-[#1A355E] underline text-sm">Retour aux devis</Link>
      </div>
    );
  }

  let offres: Offre[] = [];
  let clients: Client[] = [];
  let options: OptS[] = [];
  try { offres = await serverFetch<Offre[]>("/offres/"); } catch {}
  try { clients = await serverFetch<Client[]>("/clients/"); } catch {}

  const offre = offres.find(o => o.id === initial!.offre_id);
  if (!offre) {
    return <p className="text-red-600 p-4">Offre du devis introuvable.</p>;
  }
  try { options = await serverFetch<OptS[]>(`/offres/${offre.id}/options`); } catch {}

  return (
    <SimulateurClient
      offre={{
        id: offre.id, nom: offre.nom, type_site: offre.type_site,
        tarif_achat: offre.tarif_achat, tarif_vente_conseille: offre.tarif_vente_conseille,
        pages: offre.pages, heures: offre.heures,
      }}
      options={options}
      clients={clients}
      initial={initial}
    />
  );
}
