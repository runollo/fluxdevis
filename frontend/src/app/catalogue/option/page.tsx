import { serverFetch, type Option } from "@/lib/api";
import { saveOption } from "@/lib/actions";
import Link from "next/link";

export const dynamic = "force-dynamic";

function Field({ label, name, type = "text", value, required, step }: {
  label: string; name: string; type?: string; value?: string | number | null; required?: boolean; step?: string;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <input name={name} type={type} defaultValue={value ?? ""} required={required} step={step}
        className="w-full border rounded px-3 py-2.5 text-sm" />
    </div>
  );
}

export default async function OptionEditPage({ searchParams }: { searchParams: Promise<{ id?: string }> }) {
  const params = await searchParams;
  const id = params.id;
  let option: Option | null = null;

  if (id) {
    try {
      option = await serverFetch<Option>(`/options/${id}`);
    } catch { /* nouvelle option */ }
  }

  const title = option ? `Modifier : ${option.nom}` : "Nouvelle option";

  return (
    <div className="max-w-2xl">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/catalogue?tab=options" className="text-gray-400 hover:text-gray-600 text-sm">&larr; Retour</Link>
        <h1 className="text-xl font-bold text-gray-900">{title}</h1>
      </div>

      <form action={saveOption} className="bg-white border rounded-lg p-4 sm:p-6 space-y-4">
        {option && <input type="hidden" name="id" value={option.id} />}

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Field label="Code" name="code" value={option?.code} required />
          <Field label="Nom" name="nom" value={option?.nom} required />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Field label="Categorie" name="categorie" value={option?.categorie} required />
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Type de ligne</label>
            <select name="type_ligne" defaultValue={option?.type_ligne || "OPTION_SETUP"}
              className="w-full border rounded px-3 py-2.5 text-sm">
              <option value="OPTION_SETUP">Setup (ponctuel)</option>
              <option value="OPTION_RECURRENT">Recurrent (mensuel)</option>
              <option value="PACK">Pack maintenance</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Regle de selection</label>
            <select name="selection_regle" defaultValue={option?.selection_regle || "OPTIONNEL"}
              className="w-full border rounded px-3 py-2.5 text-sm">
              <option value="OPTIONNEL">Optionnel</option>
              <option value="UNIQUE">Unique</option>
              <option value="MULTI">Multiple</option>
            </select>
          </div>
        </div>

        <div className="border-t pt-4">
          <h2 className="text-sm font-semibold text-gray-500 uppercase mb-3">Calcul du prix</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <Field label="Heures setup" name="heures_setup" type="number" step="0.01" value={option?.heures_setup} />
            <Field label="Heures mensuel" name="heures_mensuel" type="number" step="0.01" value={option?.heures_mensuel} />
            <Field label="Prix / heure" name="prix_heure" type="number" step="0.01" value={option?.prix_heure} />
            <Field label="Taux marge" name="taux_marge" type="number" step="0.01" value={option?.taux_marge} />
          </div>
          {option && (
            <div className="mt-3 bg-gray-50 rounded p-3 grid grid-cols-2 sm:grid-cols-4 gap-2 text-sm">
              <div><span className="text-gray-500">Setup achat:</span> {Number(option.setup_achat).toFixed(2)} &euro;</div>
              <div><span className="text-gray-500">Setup vente:</span> {Number(option.vente_setup).toFixed(2)} &euro;</div>
              <div><span className="text-gray-500">Mensuel achat:</span> {Number(option.mensuel_achat).toFixed(2)} &euro;</div>
              <div><span className="text-gray-500">Mensuel vente:</span> {Number(option.vente_mensuel).toFixed(2)} &euro;</div>
            </div>
          )}
        </div>

        <div className="border-t pt-4">
          <h2 className="text-sm font-semibold text-gray-500 uppercase mb-3">Parametres</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Field label="Prix hebergement" name="prix_hebergement" type="number" step="0.01" value={option?.prix_hebergement} />
            <Field label="Quantite par defaut" name="quantite_defaut" type="number" value={option?.quantite_defaut} />
            <Field label="Unite" name="unite" value={option?.unite} />
          </div>
          <div className="mt-3">
            <label className="block text-sm font-medium text-gray-700 mb-1">Commentaire</label>
            <textarea name="commentaire" defaultValue={option?.commentaire || ""} rows={2}
              className="w-full border rounded px-3 py-2.5 text-sm" />
          </div>
        </div>

        <div className="flex gap-3 pt-4">
          <button type="submit"
            className="flex-1 sm:flex-none px-6 py-3 bg-[#1A355E] text-white rounded-lg font-medium text-sm">
            {option ? "Enregistrer" : "Creer l'option"}
          </button>
          <Link href="/catalogue?tab=options"
            className="flex-1 sm:flex-none px-6 py-3 bg-gray-100 text-gray-700 rounded-lg font-medium text-sm text-center">
            Annuler
          </Link>
        </div>
      </form>
    </div>
  );
}
