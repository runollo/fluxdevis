import { serverFetch, type Offre } from "@/lib/api";
import { saveOffre } from "@/lib/actions";
import Link from "next/link";

export const dynamic = "force-dynamic";

function Field({ label, name, type = "text", value, required, step }: {
  label: string; name: string; type?: string; value?: string | number; required?: boolean; step?: string;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <input name={name} type={type} defaultValue={value ?? ""} required={required} step={step}
        className="w-full border rounded px-3 py-2.5 text-sm" />
    </div>
  );
}

export default async function OffreEditPage({ searchParams }: { searchParams: Promise<{ id?: string }> }) {
  const params = await searchParams;
  const id = params.id;
  let offre: Offre | null = null;

  if (id) {
    try {
      offre = await serverFetch<Offre>(`/offres/${id}`);
    } catch { /* nouvelle offre */ }
  }

  const title = offre ? `Modifier : ${offre.nom}` : "Nouvelle offre";

  return (
    <div className="max-w-2xl">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/catalogue" className="text-gray-400 hover:text-gray-600 text-sm">&larr; Retour</Link>
        <h1 className="text-xl font-bold text-gray-900">{title}</h1>
      </div>

      <form action={saveOffre} className="bg-white border rounded-lg p-4 sm:p-6 space-y-4">
        {offre && <input type="hidden" name="id" value={offre.id} />}

        <Field label="Nom de l'offre" name="nom" value={offre?.nom} required />

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Type de site</label>
            <select name="type_site" defaultValue={offre?.type_site || "Webflow"}
              className="w-full border rounded px-3 py-2.5 text-sm">
              <option>Webflow</option>
              <option>Shopify</option>
            </select>
          </div>
          <Field label="Type d'offre" name="type_offre" value={offre?.type_offre} required />
        </div>

        <div className="border-t pt-4">
          <h2 className="text-sm font-semibold text-gray-500 uppercase mb-3">Tarification</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Field label="Tarif achat HT" name="tarif_achat" type="number" step="0.01" value={offre?.tarif_achat} required />
            <Field label="Taux de marge" name="taux_marge" type="number" step="0.01" value={offre?.taux_marge} required />
            <Field label="Prix vente conseille" name="tarif_vente_conseille" type="number" step="0.01" value={offre?.tarif_vente_conseille} required />
          </div>
        </div>

        <div className="border-t pt-4">
          <h2 className="text-sm font-semibold text-gray-500 uppercase mb-3">Production</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Field label="Nombre de pages" name="pages" type="number" value={offre?.pages} required />
            <Field label="Heures de travail" name="heures" type="number" value={offre?.heures} required />
            <Field label="Commission apporteur" name="commission_apporteur" type="number" step="0.01" value={offre?.commission_apporteur} />
          </div>
        </div>

        <div className="flex gap-3 pt-4">
          <button type="submit"
            className="flex-1 sm:flex-none px-6 py-3 bg-[#1A355E] text-white rounded-lg font-medium text-sm">
            {offre ? "Enregistrer" : "Creer l'offre"}
          </button>
          <Link href="/catalogue"
            className="flex-1 sm:flex-none px-6 py-3 bg-gray-100 text-gray-700 rounded-lg font-medium text-sm text-center">
            Annuler
          </Link>
        </div>
      </form>
    </div>
  );
}
