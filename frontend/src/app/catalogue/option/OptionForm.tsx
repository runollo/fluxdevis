"use client";

// Formulaire d'edition d'une option / pack avec CALCUL EN TEMPS REEL des prix
// derives et de la marge. Reproduit exactement la formule du catalogue Excel
// (cf. backend Option.recalculer_prix) :
//   setup_achat   = prix_heure * heures_setup
//   mensuel_achat = prix_heure * heures_mensuel + prix_hebergement
//   vente_setup   = setup_achat   * (1 + taux_marge)
//   vente_mensuel = mensuel_achat * (1 + taux_marge)
// La sauvegarde passe par la Server Action saveOption (le backend recalcule
// de toute facon : l'apercu ici est purement visuel, pour piloter la marge).

import { useState } from "react";
import Link from "next/link";
import { saveOption } from "@/lib/actions";
import type { Option } from "@/lib/api";

function eur(v: number) {
  return v.toLocaleString("fr-FR", { style: "currency", currency: "EUR" });
}
function N(v: string) { return Number(v || 0); }

export default function OptionForm({ option }: { option: Option | null }) {
  const [heuresSetup, setHeuresSetup] = useState(String(option?.heures_setup ?? "0"));
  const [heuresMensuel, setHeuresMensuel] = useState(String(option?.heures_mensuel ?? "0"));
  const [prixHeure, setPrixHeure] = useState(String(option?.prix_heure ?? "27"));
  const [tauxMarge, setTauxMarge] = useState(String(option?.taux_marge ?? "0.30"));
  const [prixHeberg, setPrixHeberg] = useState(String(option?.prix_hebergement ?? "0"));

  // Recalcul live (memes formules que le backend)
  const setupAchat = N(prixHeure) * N(heuresSetup);
  const mensuelAchat = N(prixHeure) * N(heuresMensuel) + N(prixHeberg);
  const venteSetup = setupAchat * (1 + N(tauxMarge));
  const venteMensuel = mensuelAchat * (1 + N(tauxMarge));
  const margeSetup = venteSetup - setupAchat;
  const margeMensuel = venteMensuel - mensuelAchat;
  const margePct = Math.round(N(tauxMarge) * 100);

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
          <Field label="Code" name="code" defaultValue={option?.code} required />
          <Field label="Nom" name="nom" defaultValue={option?.nom} required />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Field label="Categorie" name="categorie" defaultValue={option?.categorie} required />
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
            <Num label="Heures setup" name="heures_setup" value={heuresSetup} onChange={setHeuresSetup} />
            <Num label="Heures mensuel" name="heures_mensuel" value={heuresMensuel} onChange={setHeuresMensuel} />
            <Num label="Prix / heure" name="prix_heure" value={prixHeure} onChange={setPrixHeure} />
            <Num label="Taux marge" name="taux_marge" value={tauxMarge} onChange={setTauxMarge} />
          </div>
          <p className="text-xs text-gray-400 mt-1">
            Taux marge en decimal (0,30 = 30 %). Le mensuel inclut l&apos;hebergement.
          </p>

          {/* Apercu temps reel */}
          <div className="mt-3 rounded-lg border border-blue-200 bg-blue-50 p-3 space-y-3">
            <p className="text-xs font-semibold text-blue-800 uppercase">Apercu en temps reel (marge {margePct} %)</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Bloc titre="Setup (ponctuel)" achat={setupAchat} vente={venteSetup} marge={margeSetup} actif={N(heuresSetup) > 0} />
              <Bloc titre="Mensuel (recurrent)" achat={mensuelAchat} vente={venteMensuel} marge={margeMensuel} suffix="/mois"
                actif={N(heuresMensuel) > 0 || N(prixHeberg) > 0}
                note={N(prixHeberg) > 0 ? `dont hebergement ${eur(N(prixHeberg))}/mois` : undefined} />
            </div>
          </div>
        </div>

        <div className="border-t pt-4">
          <h2 className="text-sm font-semibold text-gray-500 uppercase mb-3">Parametres</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Num label="Prix hebergement /mois" name="prix_hebergement" value={prixHeberg} onChange={setPrixHeberg} />
            <Field label="Quantite par defaut" name="quantite_defaut" type="number" defaultValue={option?.quantite_defaut} />
            <Field label="Unite" name="unite" defaultValue={option?.unite} />
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

function Bloc({ titre, achat, vente, marge, suffix = "", note, actif }: {
  titre: string; achat: number; vente: number; marge: number; suffix?: string; note?: string; actif: boolean;
}) {
  const pct = achat > 0 ? Math.round((marge / achat) * 100) : 0;
  return (
    <div className={`rounded p-3 ${actif ? "bg-white border border-blue-200" : "bg-white/40 border border-gray-200"}`}>
      <p className="text-xs font-semibold text-gray-500 uppercase mb-1">{titre}</p>
      <div className="space-y-0.5 text-sm">
        <div className="flex justify-between"><span className="text-gray-500">Achat</span><span>{eur(achat)}{suffix}</span></div>
        <div className="flex justify-between"><span className="text-gray-500">Vente</span><span className="font-semibold">{eur(vente)}{suffix}</span></div>
        <div className="flex justify-between text-green-700"><span>Marge</span><span className="font-semibold">{eur(marge)}{suffix}{achat > 0 ? ` (${pct} %)` : ""}</span></div>
      </div>
      {note && <p className="text-[11px] text-gray-400 mt-1">{note}</p>}
    </div>
  );
}
