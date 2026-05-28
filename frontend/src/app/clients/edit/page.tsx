import { serverFetch } from "@/lib/api";
import { saveClient } from "@/lib/actions";
import Link from "next/link";

export const dynamic = "force-dynamic";

interface ClientFull {
  id: number; raison_sociale: string; forme_juridique: string | null;
  siret: string | null; code_ape: string | null; rcs: string | null; tva_intracom: string | null;
  adresse: string | null; complement_adresse: string | null;
  code_postal: string | null; ville: string | null; pays: string | null;
  civilite: string | null; interlocuteur: string | null; fonction: string | null;
  telephone: string | null; mobile: string | null; email: string | null;
  notes: string | null;
}

function Field({ label, name, value, required, type = "text", placeholder }: {
  label: string; name: string; value?: string | null; required?: boolean; type?: string; placeholder?: string;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <input name={name} type={type} defaultValue={value ?? ""} required={required} placeholder={placeholder}
        className="w-full border rounded px-3 py-2.5 text-sm" />
    </div>
  );
}

export default async function ClientEditPage({ searchParams }: { searchParams: Promise<{ id?: string }> }) {
  const params = await searchParams;
  const id = params.id;
  let client: ClientFull | null = null;

  if (id) {
    try {
      client = await serverFetch<ClientFull>(`/clients/${id}`);
    } catch { /* nouveau client */ }
  }

  const title = client ? `Fiche : ${client.raison_sociale}` : "Nouveau client";

  return (
    <div className="max-w-2xl">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/clients" className="text-gray-400 hover:text-gray-600 text-sm">&larr; Retour</Link>
        <h1 className="text-xl font-bold text-gray-900">{title}</h1>
      </div>

      <form action={saveClient} className="bg-white border rounded-lg p-4 sm:p-6 space-y-5">
        {client && <input type="hidden" name="id" value={client.id} />}

        {/* Identification */}
        <div>
          <h2 className="text-sm font-semibold text-gray-500 uppercase mb-3">Identification</h2>
          <div className="space-y-3">
            <Field label="Raison sociale *" name="raison_sociale" value={client?.raison_sociale} required />
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Forme juridique</label>
                <select name="forme_juridique" defaultValue={client?.forme_juridique || ""}
                  className="w-full border rounded px-3 py-2.5 text-sm">
                  <option value="">-</option>
                  <option>SARL</option>
                  <option>SAS</option>
                  <option>SASU</option>
                  <option>EURL</option>
                  <option>SA</option>
                  <option>SCI</option>
                  <option>Auto-entrepreneur</option>
                  <option>Association</option>
                  <option>Autre</option>
                </select>
              </div>
              <Field label="SIRET" name="siret" value={client?.siret} placeholder="XXX XXX XXX XXXXX" />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <Field label="Code APE / NAF" name="code_ape" value={client?.code_ape} placeholder="6201Z" />
              <Field label="RCS" name="rcs" value={client?.rcs} placeholder="RCS Montpellier" />
              <Field label="TVA intracommunautaire" name="tva_intracom" value={client?.tva_intracom} placeholder="FRXX XXXXXXXXX" />
            </div>
          </div>
        </div>

        {/* Adresse */}
        <div className="border-t pt-5">
          <h2 className="text-sm font-semibold text-gray-500 uppercase mb-3">Adresse</h2>
          <div className="space-y-3">
            <Field label="Adresse" name="adresse" value={client?.adresse} />
            <Field label="Complement d'adresse" name="complement_adresse" value={client?.complement_adresse} />
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              <Field label="Code postal" name="code_postal" value={client?.code_postal} />
              <Field label="Ville" name="ville" value={client?.ville} />
              <Field label="Pays" name="pays" value={client?.pays || "France"} />
            </div>
          </div>
        </div>

        {/* Contact */}
        <div className="border-t pt-5">
          <h2 className="text-sm font-semibold text-gray-500 uppercase mb-3">Contact principal</h2>
          <div className="space-y-3">
            <div className="grid grid-cols-3 sm:grid-cols-4 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Civilite</label>
                <select name="civilite" defaultValue={client?.civilite || ""}
                  className="w-full border rounded px-3 py-2.5 text-sm">
                  <option value="">-</option>
                  <option>M.</option>
                  <option>Mme</option>
                </select>
              </div>
              <div className="col-span-2 sm:col-span-3">
                <Field label="Nom et prenom" name="interlocuteur" value={client?.interlocuteur} />
              </div>
            </div>
            <Field label="Fonction" name="fonction" value={client?.fonction} placeholder="Gerant, Directeur..." />
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <Field label="Telephone fixe" name="telephone" type="tel" value={client?.telephone} />
              <Field label="Mobile" name="mobile" type="tel" value={client?.mobile} />
              <Field label="Email" name="email" type="email" value={client?.email} />
            </div>
          </div>
        </div>

        {/* Notes */}
        <div className="border-t pt-5">
          <h2 className="text-sm font-semibold text-gray-500 uppercase mb-3">Notes</h2>
          <textarea name="notes" defaultValue={client?.notes || ""} rows={3}
            className="w-full border rounded px-3 py-2.5 text-sm" placeholder="Notes internes..." />
        </div>

        {/* Actions */}
        <div className="flex gap-3 pt-2">
          <button type="submit"
            className="flex-1 sm:flex-none px-6 py-3 bg-[#1A355E] text-white rounded-lg font-medium text-sm">
            {client ? "Enregistrer" : "Creer le client"}
          </button>
          <Link href="/clients"
            className="flex-1 sm:flex-none px-6 py-3 bg-gray-100 text-gray-700 rounded-lg font-medium text-sm text-center">
            Annuler
          </Link>
        </div>
      </form>
    </div>
  );
}
