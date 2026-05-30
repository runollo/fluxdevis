"use client";

// Formulaire d'edition d'une offre du catalogue avec APERCU EN TEMPS REEL de la
// tarification et de la marge. Permet de piloter le prix de vente conseille selon
// le tarif d'achat, le taux de marge et la commission apporteur.
//
// Relation tarifaire (comme l'import du catalogue) :
//   tarif_vente_theorique = tarif_achat * (1 + taux_marge)
// Le tarif_vente_conseille reste saisissable (on peut s'ecarter du theorique) ;
// l'apercu montre alors la marge reelle obtenue sur le prix saisi.

import { useEffect, useState } from "react";
import Link from "next/link";
import { saveOffre } from "@/lib/actions";
import type { Offre } from "@/lib/api";

function eur(v: number) {
  return v.toLocaleString("fr-FR", { style: "currency", currency: "EUR" });
}
function N(v: string) { return Number(v || 0); }

export default function OffreForm({ offre }: { offre: Offre | null }) {
  const [tarifAchat, setTarifAchat] = useState(String(offre?.tarif_achat ?? "0"));
  const [tauxMarge, setTauxMarge] = useState(String(offre?.taux_marge ?? "0.30"));
  const [venteConseille, setVenteConseille] = useState(String(offre?.tarif_vente_conseille ?? "0"));
  const [commission, setCommission] = useState(String(offre?.commission_apporteur ?? "0"));

  // Tarif conseille = achat x (1 + marge) AUTO, mais surchargeable : des que
  // l'utilisateur saisit un prix a la main (prix rond), sa valeur est respectee
  // et n'est plus ecrasee par le recalcul. Si l'offre chargee a deja un prix
  // qui s'ecarte du theorique, on demarre en mode "force" pour ne pas l'ecraser.
  const achatInit = N(String(offre?.tarif_achat ?? "0"));
  const theoriqueInit = achatInit * (1 + N(String(offre?.taux_marge ?? "0.30")));
  const [manuel, setManuel] = useState(
    !!offre && Math.abs(N(String(offre.tarif_vente_conseille ?? "0")) - theoriqueInit) > 0.01
  );
  const achat = N(tarifAchat);
  const venteTheorique = achat * (1 + N(tauxMarge));

  // Recalcul auto du conseille tant que l'utilisateur ne l'a pas force.
  useEffect(() => {
    if (!manuel) setVenteConseille(venteTheorique.toFixed(2));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tarifAchat, tauxMarge, manuel]);

  const vente = N(venteConseille);
  const margeBrute = vente - achat;
  const margePct = achat > 0 ? Math.round((margeBrute / achat) * 100) : 0;
  const margePctTheorique = Math.round(N(tauxMarge) * 100);
  const margeNette = margeBrute - N(commission);
  const ecartTheorique = vente - venteTheorique;

  const title = offre ? `Modifier : ${offre.nom}` : "Nouvelle offre";

  return (
    <div className="max-w-2xl">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/catalogue" className="text-gray-400 hover:text-gray-600 text-sm">&larr; Retour</Link>
        <h1 className="text-xl font-bold text-gray-900">{title}</h1>
      </div>

      <form action={saveOffre} className="bg-white border rounded-lg p-4 sm:p-6 space-y-4">
        {offre && <input type="hidden" name="id" value={offre.id} />}

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Field label="Nom" name="nom" defaultValue={offre?.nom} required />
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Type de site</label>
            <select name="type_site" defaultValue={offre?.type_site || "Webflow"}
              className="w-full border rounded px-3 py-2.5 text-sm">
              <option value="Webflow">Webflow</option>
              <option value="Shopify">Shopify</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Field label="Type d'offre" name="type_offre" defaultValue={offre?.type_offre} />
          <Field label="Pages" name="pages" type="number" defaultValue={offre?.pages} />
        </div>

        <div className="border-t pt-4">
          <h2 className="text-sm font-semibold text-gray-500 uppercase mb-3">Tarification</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
            <Num label="Tarif achat HT" name="tarif_achat" value={tarifAchat} onChange={setTarifAchat} />
            <Num label="Taux marge" name="taux_marge" value={tauxMarge} onChange={setTauxMarge} />
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tarif vente conseille HT
                {manuel
                  ? <span className="ml-1 text-[11px] text-amber-600">(force)</span>
                  : <span className="ml-1 text-[11px] text-gray-400">(auto)</span>}
              </label>
              <input name="tarif_vente_conseille" type="number" step="0.01" inputMode="decimal"
                value={venteConseille}
                onChange={(e) => { setManuel(true); setVenteConseille(e.target.value); }}
                className={`w-full border rounded px-3 py-2.5 text-sm ${manuel ? "border-amber-300 bg-amber-50 font-semibold" : ""}`} />
            </div>
          </div>
          <p className="text-xs text-gray-400 mt-1">
            Taux marge en decimal (0,80 = 80 %). Le tarif conseille se calcule tout
            seul (achat x (1 + marge)) ; tu peux le forcer a un prix rond.
            {manuel && (
              <button type="button" onClick={() => setManuel(false)}
                className="ml-1 text-blue-700 underline">
                Revenir au calcul automatique
              </button>
            )}
          </p>

          {/* Apercu temps reel */}
          <div className="mt-3 rounded-lg border border-blue-200 bg-blue-50 p-3 space-y-3">
            <p className="text-xs font-semibold text-blue-800 uppercase">Apercu en temps reel</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="rounded bg-white border border-blue-200 p-3 space-y-0.5 text-sm">
                <p className="text-xs font-semibold text-gray-500 uppercase mb-1">Sur le tarif conseille</p>
                <div className="flex justify-between"><span className="text-gray-500">Achat</span><span>{eur(achat)}</span></div>
                <div className="flex justify-between"><span className="text-gray-500">Vente conseillee</span><span className="font-semibold">{eur(vente)}</span></div>
                <div className="flex justify-between text-green-700"><span>Marge brute</span><span className="font-semibold">{eur(margeBrute)}{achat > 0 ? ` (${margePct} %)` : ""}</span></div>
              </div>
              <div className="rounded bg-white border border-blue-200 p-3 space-y-0.5 text-sm">
                <p className="text-xs font-semibold text-gray-500 uppercase mb-1">Reperes</p>
                <div className="flex justify-between"><span className="text-gray-500">Vente theorique</span><span>{eur(venteTheorique)} <span className="text-gray-400">({margePctTheorique} %)</span></span></div>
                {manuel && <div className="flex justify-between"><span className="text-gray-500">Ecart vs theorique</span><span className={ecartTheorique < 0 ? "text-red-600" : "text-gray-700"}>{eur(ecartTheorique)}</span></div>}
                {N(commission) > 0 && <div className="flex justify-between"><span className="text-gray-500">Commission apporteur</span><span>- {eur(N(commission))}</span></div>}
                <div className="flex justify-between text-green-700"><span>Marge nette</span><span className="font-semibold">{eur(margeNette)}</span></div>
              </div>
            </div>
          </div>
        </div>

        <div className="border-t pt-4">
          <h2 className="text-sm font-semibold text-gray-500 uppercase mb-3">Details</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
            <Field label="Heures" name="heures" type="number" defaultValue={offre?.heures} />
            <Num label="Commission apporteur" name="commission_apporteur" value={commission} onChange={setCommission} />
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

function Field({ label, name, type = "text", defaultValue, required }: {
  label: string; name: string; type?: string; defaultValue?: string | number | null; required?: boolean;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <input name={name} type={type} defaultValue={defaultValue ?? ""} required={required}
        className="w-full border rounded px-3 py-2.5 text-sm" />
    </div>
  );
}

function Num({ label, name, value, onChange }: {
  label: string; name: string; value: string; onChange: (v: string) => void;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <input name={name} type="number" step="0.01" inputMode="decimal" value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full border rounded px-3 py-2.5 text-sm" />
    </div>
  );
}
