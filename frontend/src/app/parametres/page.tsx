import { serverFetch } from "@/lib/api";
import { saveParametres, saveModelesEmail, envoyerEmailTest } from "@/lib/actions";

export const dynamic = "force-dynamic";

interface Parametres {
  smtp_host: string | null; smtp_port: number | null; smtp_starttls: boolean | null;
  smtp_user: string | null; smtp_from: string | null;
  smtp_password_defini: boolean; smtp_actif: boolean; envoi_client_actif: boolean;
  email_signature: string; email_objet_devis: string; email_corps_devis: string;
  email_objet_facture: string; email_corps_facture: string;
}

export default async function ParametresPage(
  { searchParams }: { searchParams: Promise<{ ok?: string; test?: string; msg?: string }> }
) {
  const params = await searchParams;
  let p: Parametres | null = null;
  try { p = await serverFetch<Parametres>("/parametres/"); } catch {}

  interface Apercu { objet: string; html: string }
  let apDevis: Apercu | null = null;
  let apFacture: Apercu | null = null;
  try { apDevis = await serverFetch<Apercu>("/parametres/apercu?type=devis"); } catch {}
  try { apFacture = await serverFetch<Apercu>("/parametres/apercu?type=facture"); } catch {}

  if (!p) {
    return (
      <div>
        <h1 className="text-xl sm:text-2xl font-bold text-gray-900 mb-4">Parametres</h1>
        <div className="bg-white border rounded-lg p-8 text-center text-gray-400">
          Backend injoignable.
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl">
      <h1 className="text-xl sm:text-2xl font-bold text-gray-900 mb-4">Parametres</h1>

      {params.ok === "1" && (
        <div className="mb-4 rounded border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
          Parametres enregistres.
        </div>
      )}
      {params.test === "1" && (
        <div className="mb-4 rounded border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
          Email de test envoye. Verifiez votre boite de reception.
        </div>
      )}
      {params.msg && (
        <div className="mb-4 rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {params.msg}
        </div>
      )}

      {/* Envoi d'emails (SMTP) */}
      <section className="bg-white border rounded-lg p-5 mb-6">
        <div className="flex items-center justify-between mb-1">
          <h2 className="text-sm font-semibold text-gray-700 uppercase">Envoi d&apos;emails (SMTP)</h2>
          <span className={`px-2 py-0.5 rounded text-xs font-medium ${p.smtp_actif ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"}`}>
            {p.smtp_actif ? "Actif" : "Non configure"}
          </span>
        </div>
        <p className="text-xs text-gray-400 mb-4">
          Envoi des devis et factures depuis ta propre messagerie pro. Defauts OVH ;
          pour Gmail/Microsoft, utilise un &laquo; mot de passe d&apos;application &raquo;.
        </p>

        <form action={saveParametres} className="space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-gray-400 mb-0.5">Serveur SMTP</label>
              <input name="smtp_host" defaultValue={p.smtp_host ?? "ssl0.ovh.net"}
                className="w-full border rounded px-3 py-2 text-sm" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-gray-400 mb-0.5">Port</label>
                <input name="smtp_port" type="number" defaultValue={p.smtp_port ?? 587}
                  className="w-full border rounded px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-0.5">Securite</label>
                <select name="smtp_starttls" defaultValue={String(p.smtp_starttls ?? true)}
                  className="w-full border rounded px-2 py-2 text-sm">
                  <option value="true">STARTTLS (587)</option>
                  <option value="false">SSL/TLS (465)</option>
                </select>
              </div>
            </div>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-0.5">Adresse (boite d&apos;envoi)</label>
            <input name="smtp_user" type="email" defaultValue={p.smtp_user ?? ""}
              placeholder="contact@fluxweb.fr" className="w-full border rounded px-3 py-2 text-sm" />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-0.5">Mot de passe</label>
            <input name="smtp_password" type="password"
              placeholder={p.smtp_password_defini ? "•••••• (laisser vide pour conserver)" : "mot de passe de la boite"}
              className="w-full border rounded px-3 py-2 text-sm" />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-0.5">Expediteur affiche (optionnel)</label>
            <input name="smtp_from" defaultValue={p.smtp_from ?? ""}
              placeholder="FluXweb <contact@fluxweb.fr>" className="w-full border rounded px-3 py-2 text-sm" />
            <p className="text-[11px] text-gray-400 mt-0.5">
              Doit correspondre a la boite d&apos;envoi (OVH refuse un expediteur different).
            </p>
          </div>
          <div className="rounded border border-amber-200 bg-amber-50 p-3">
            <label className="block text-xs font-semibold text-amber-800 mb-1">
              Envoi direct au client
            </label>
            <select name="envoi_client_actif" defaultValue={String(p.envoi_client_actif)}
              className="border rounded px-2 py-2 text-sm">
              <option value="false">Desactive (securite) — seul &laquo; M&apos;envoyer &raquo; est possible</option>
              <option value="true">Active — l&apos;envoi direct au client est autorise</option>
            </select>
            <p className="text-[11px] text-amber-700 mt-1">
              Tant que c&apos;est desactive, impossible d&apos;envoyer par erreur au client : tu peux
              seulement t&apos;envoyer le document pour le transferer toi-meme. Active-le quand tu es a l&apos;aise.
            </p>
          </div>
          <button type="submit" className="px-4 py-2 bg-[#1A355E] text-white rounded text-sm font-medium">
            Enregistrer
          </button>
        </form>
      </section>

      {/* Modeles d'emails */}
      <section className="bg-white border rounded-lg p-5 mb-6">
        <h2 className="text-sm font-semibold text-gray-700 uppercase mb-1">Modeles d&apos;emails</h2>
        <p className="text-xs text-gray-400 mb-2">
          Objet, corps et signature des emails envoyes avec le devis ou la facture.
        </p>
        <p className="text-[11px] text-gray-400 mb-4 leading-relaxed">
          Variables (remplacees automatiquement) — communes :{" "}
          <code>{"{client}"}</code> <code>{"{interlocuteur}"}</code> <code>{"{montant_ttc}"}</code> <code>{"{marque}"}</code>.
          {" "}Devis : <code>{"{reference}"}</code> <code>{"{date}"}</code> <code>{"{date_validite}"}</code> <code>{"{type_document}"}</code>.
          {" "}Facture : <code>{"{numero}"}</code> <code>{"{date}"}</code> <code>{"{date_echeance}"}</code> <code>{"{periode}"}</code>.
        </p>

        <form action={saveModelesEmail} className="space-y-4">
          <div>
            <label className="block text-xs text-gray-400 mb-0.5">Signature (commune)</label>
            <textarea name="email_signature" rows={2} defaultValue={p.email_signature}
              className="w-full border rounded px-3 py-2 text-sm font-mono" />
          </div>

          <div className="border-t pt-3">
            <p className="text-xs font-semibold text-gray-600 mb-2">Email accompagnant un devis</p>
            <label className="block text-xs text-gray-400 mb-0.5">Objet</label>
            <input name="email_objet_devis" defaultValue={p.email_objet_devis}
              className="w-full border rounded px-3 py-2 text-sm mb-2" />
            <label className="block text-xs text-gray-400 mb-0.5">Corps</label>
            <textarea name="email_corps_devis" rows={5} defaultValue={p.email_corps_devis}
              className="w-full border rounded px-3 py-2 text-sm font-mono" />
          </div>

          <div className="border-t pt-3">
            <p className="text-xs font-semibold text-gray-600 mb-2">Email accompagnant une facture</p>
            <label className="block text-xs text-gray-400 mb-0.5">Objet</label>
            <input name="email_objet_facture" defaultValue={p.email_objet_facture}
              className="w-full border rounded px-3 py-2 text-sm mb-2" />
            <label className="block text-xs text-gray-400 mb-0.5">Corps</label>
            <textarea name="email_corps_facture" rows={5} defaultValue={p.email_corps_facture}
              className="w-full border rounded px-3 py-2 text-sm font-mono" />
          </div>

          <button type="submit" className="px-4 py-2 bg-[#1A355E] text-white rounded text-sm font-medium">
            Enregistrer les modeles
          </button>
        </form>
      </section>

      {/* Apercu des emails (donnees d'exemple, reflete les modeles enregistres) */}
      <section className="bg-white border rounded-lg p-5 mb-6">
        <h2 className="text-sm font-semibold text-gray-700 uppercase mb-1">Apercu</h2>
        <p className="text-xs text-gray-400 mb-4">
          Rendu avec des donnees d&apos;exemple. Reflete les modeles enregistres (cliquez
          &laquo; Enregistrer les modeles &raquo; pour mettre a jour).
        </p>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {apDevis && (
            <div>
              <p className="text-xs font-semibold text-gray-600 mb-1">Email d&apos;un devis</p>
              <div className="border rounded">
                <div className="border-b bg-gray-50 px-3 py-2 text-xs text-gray-600">
                  <span className="text-gray-400">Objet :</span> {apDevis.objet}
                </div>
                <div className="px-3 py-3 text-sm" dangerouslySetInnerHTML={{ __html: apDevis.html }} />
              </div>
            </div>
          )}
          {apFacture && (
            <div>
              <p className="text-xs font-semibold text-gray-600 mb-1">Email d&apos;une facture</p>
              <div className="border rounded">
                <div className="border-b bg-gray-50 px-3 py-2 text-xs text-gray-600">
                  <span className="text-gray-400">Objet :</span> {apFacture.objet}
                </div>
                <div className="px-3 py-3 text-sm" dangerouslySetInnerHTML={{ __html: apFacture.html }} />
              </div>
            </div>
          )}
        </div>
      </section>

      {/* Test d'envoi */}
      <section className="bg-white border rounded-lg p-5">
        <h2 className="text-sm font-semibold text-gray-700 uppercase mb-1">Tester l&apos;envoi</h2>
        <p className="text-xs text-gray-400 mb-3">
          Envoie un email de test pour verifier la configuration (enregistre d&apos;abord).
        </p>
        <form action={envoyerEmailTest} className="flex flex-wrap items-end gap-2">
          <div className="grow min-w-[200px]">
            <label className="block text-xs text-gray-400 mb-0.5">Adresse de test</label>
            <input name="destinataire" type="email" defaultValue={p.smtp_user ?? ""}
              placeholder="ton-email@exemple.fr" className="w-full border rounded px-3 py-2 text-sm" />
          </div>
          <button type="submit" disabled={!p.smtp_actif}
            className={`px-4 py-2 rounded text-sm font-medium ${p.smtp_actif ? "border border-[#1A355E] text-[#1A355E]" : "border border-gray-200 text-gray-300 cursor-not-allowed"}`}>
            Envoyer un email de test
          </button>
        </form>
      </section>
    </div>
  );
}
