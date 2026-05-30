import { serverFetch, type Offre, type Client } from "@/lib/api";
import SimulateurClient, { type OptS } from "./SimulateurClient";
import Link from "next/link";

export const dynamic = "force-dynamic";

function eur(v: number | string) {
  return Number(v).toLocaleString("fr-FR", { style: "currency", currency: "EUR" });
}

// La page reste un Server Component pour le chargement des donnees (offres, clients,
// options de l'offre choisie) ; toute l'interactivite (selection + recalcul temps reel)
// est deleguee a SimulateurClient une fois l'offre selectionnee.
export default async function SimulateurPage({ searchParams }: { searchParams: Promise<Record<string, string>> }) {
  const p = await searchParams;

  let offres: Offre[] = [];
  let clients: Client[] = [];
  let options: OptS[] = [];
  let error = "";

  try { offres = await serverFetch<Offre[]>("/offres/"); } catch (e) { error = String(e); }
  try { clients = await serverFetch<Client[]>("/clients/"); } catch {}

  const offreId = p.offre_id || "";
  const offre = offreId ? offres.find(o => String(o.id) === offreId) : null;

  if (offre) {
    try { options = await serverFetch<OptS[]>(`/offres/${offre.id}/options`); } catch (e) { error = String(e); }
  }

  if (error && !offres.length) return <p className="text-red-600 p-4">Erreur : {error}</p>;

  // Pas d'offre selectionnee : formulaire de selection (server, navigation simple)
  if (!offre) {
    return (
      <div>
        <h1 className="text-xl sm:text-2xl font-bold text-gray-900 mb-4">Simulateur de prix</h1>
        <form method="GET" action="/simulateur" className="bg-white border rounded-lg p-4 sm:p-6 max-w-lg space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Choisissez une offre</label>
            <select name="offre_id" required className="w-full border rounded px-3 py-2.5 text-sm">
              <option value="">-- Selectionnez --</option>
              {offres.map(o => (
                <option key={o.id} value={o.id}>{o.nom} ({o.type_site}) - {eur(o.tarif_vente_conseille)}</option>
              ))}
            </select>
          </div>
          <button type="submit" className="w-full py-3 bg-[#1A355E] text-white rounded-lg font-medium text-sm">
            Charger les options
          </button>
        </form>
        {!offres.length && (
          <p className="text-gray-400 text-sm mt-4">
            Aucune offre disponible. <Link href="/catalogue" className="underline">Aller au catalogue</Link>
          </p>
        )}
      </div>
    );
  }

  return (
    <SimulateurClient
      offre={{
        id: offre.id, nom: offre.nom, type_site: offre.type_site,
        tarif_achat: offre.tarif_achat, tarif_vente_conseille: offre.tarif_vente_conseille,
        pages: offre.pages, heures: offre.heures,
      }}
      options={options}
      clients={clients}
    />
  );
}
