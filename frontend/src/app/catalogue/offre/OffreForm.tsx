"use client";

// Formulaire d'edition d'une offre du catalogue avec APERCU EN TEMPS REEL de la
// tarification et de la marge. Permet de piloter le prix de vente conseille selon
// le tarif d'achat, le taux de marge et la commission apporteur.
//
// Relation tarifaire (comme l'import du catalogue) :
//   tarif_vente_theorique = tarif_achat * (1 + taux_marge)
// Le tarif_vente_conseille reste saisissable (on peut s'ecarter du theorique) ;
// l'apercu montre alors la marge reelle obtenue sur le prix saisi.

import { useState } from "react";
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
  const [commission, setCommission] = useState(String(offre?.commission_apporteur ?? "0"));

  // Calculs live (formule du catalogue Excel) :
  //   tarif_vente_conseille = tarif_achat * (1 + taux_marge)
  // Le tarif conseille est CALCULE (pas saisi), comme dans la feuille Excel.
  const achat = N(tarifAchat);
  const vente = achat * (1 + N(tauxMarge));
  const margeBrute = vente - achat;
  const margePct = Math.round(N(tauxMarge) * 100);
  const margeNette = margeBrute - N(commission);

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
              <label className="block text-sm font-medium text-gray-700 mb-1">Tarif vente conseille HT</label>
              <input type="text" readOnly tabIndex={-1}
                value={eur(vente)}
                className="w-full border rounded px-3 py-2.5 text-sm bg-gray-50 font-semibold text-gray-800" />
              {/* Valeur calculee envoyee au backend */}
              <input type="hidden" name="tarif_vente_conseille" value={vente.toFixed(2)} />
            </div>
          </div>
          <p className="text-xs text-gray-400 mt-1">
            Taux marge en decimal (0,80 = 80 %). Le tarif de vente est calcule :
            achat x (1 + marge), comme dans le catalogue.
          </p>

          {/* Apercu temps reel */}
          <div className="mt-3 rounded-lg border border-blue-200 bg-blue-50 p-3">
            <p className="text-xs font-semibold text-blue-800 uppercase mb-2">Apercu en temps reel (marge {margePct} %)</p>
            <div className="rounded bg-white border border-blue-200 p-3 space-y-0.5 text-sm">
              <div className="flex justify-between"><span className="text-gray-500">Tarif achat HT</span><span>{eur(achat)}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Tarif vente conseille HT</span><span className="font-semibold">{eur(vente)}</span></div>
              <div className="flex justify-between text-green-700"><span>Marge brute</span><span className="font-semibold">{eur(margeBrute)}{achat > 0 ? ` (${margePct} %)` : ""}</span></div>
              {N(commission) > 0 && (
                <>
                  <div className="flex justify-between"><span className="text-gray-500">Commission apporteur</span><span>- {eur(N(commission))}</span></div>
                  <div className="flex justify-between text-green-700"><span>Marge nette</span><span className="font-semibold">{eur(margeNette)}</span></div>
                </>
              )}
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
