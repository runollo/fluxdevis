"use client";

// Editeur du CONTENU d'un pack de maintenance (descriptif affiche dans le devis).
// Deux modeles selon la famille :
//  - Shopify : textes auto-portants (court = devis/PB, detaille = contrat/annexe) + delai.
//  - Webflow : modele CUMULATIF (prestations propres au niveau + herite en lecture seule).
// Defaut = fichier backend packs_maintenance ; edition persistee dans Option.contenu_pack.

import { useState } from "react";
import { saveContenuPack, resetContenuPack } from "@/lib/actions";
import type { ContenuPack, PrestationPack } from "@/lib/api";

export default function PackContenuEditor({ data }: { data: ContenuPack }) {
  const isShopify = data.famille === "Shopify";
  return (
    <div className="max-w-2xl mt-6 bg-white border rounded-lg p-4 sm:p-6">
      <div className="flex items-baseline justify-between gap-3 mb-1">
        <h2 className="text-sm font-semibold text-gray-500 uppercase">
          Contenu du pack ({data.niveau})
        </h2>
        {data.personnalise ? (
          <span className="text-[11px] px-2 py-0.5 rounded bg-violet-100 text-violet-700 font-medium">Personnalise</span>
        ) : (
          <span className="text-[11px] px-2 py-0.5 rounded bg-slate-100 text-slate-600 font-medium">Par defaut</span>
        )}
      </div>
      <p className="text-xs text-gray-400 mb-4">{data.famille_label}.</p>

      {isShopify
        ? <EditeurShopify data={data} />
        : <EditeurWebflow data={data} />}

      {data.personnalise && (
        <form action={resetContenuPack} className="mt-3">
          <input type="hidden" name="id" value={data.option_id} />
          <button type="submit"
            className="px-4 py-2 border border-gray-300 text-gray-600 rounded-lg font-medium text-sm">
            Reinitialiser au contenu par defaut
          </button>
        </form>
      )}
    </div>
  );
}

// --- Shopify : texte court (devis/PB) + texte detaille (contrat) + delai ---------
function EditeurShopify({ data }: { data: ContenuPack }) {
  const [court, setCourt] = useState(data.contenu.texte_court ?? "");
  const [detaille, setDetaille] = useState(data.contenu.texte_detaille ?? "");
  const [delai, setDelai] = useState(data.contenu.delai_reponse ?? "");

  return (
    <form action={saveContenuPack} className="space-y-4">
      <input type="hidden" name="id" value={data.option_id} />

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Texte court <span className="text-gray-400 font-normal">(devis simple / proposition budgetaire)</span>
        </label>
        <textarea value={court} onChange={(e) => setCourt(e.target.value)} name="texte_court" rows={3}
          className="w-full border rounded px-3 py-2.5 text-sm"
          placeholder="Resume affiche dans le bloc maintenance du devis." />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Texte detaille <span className="text-gray-400 font-normal">(contrat / annexe)</span>
        </label>
        <textarea value={detaille} onChange={(e) => setDetaille(e.target.value)} name="texte_detaille" rows={7}
          className="w-full border rounded px-3 py-2.5 text-sm"
          placeholder="Descriptif complet affiche en annexe du devis contractuel." />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Delai de reponse</label>
        <input value={delai} onChange={(e) => setDelai(e.target.value)} name="delai_reponse"
          className="w-full border rounded px-3 py-2.5 text-sm" placeholder="ex. 48 heures ouvrees" />
      </div>

      <p className="text-xs text-gray-400">
        Le temps inclus mensuel est calcule automatiquement a partir des heures du pack
        (champ Heures mensuel ci-dessus) : il n&apos;est pas a saisir ici.
      </p>

      <button type="submit" className="px-6 py-3 bg-[#1A355E] text-white rounded-lg font-medium text-sm">
        Enregistrer le contenu
      </button>
    </form>
  );
}

// --- Webflow : modele cumulatif (prestations propres + herite lecture seule) -----
function EditeurWebflow({ data }: { data: ContenuPack }) {
  const [accroche, setAccroche] = useState(data.contenu.accroche ?? "");
  const [intro, setIntro] = useState(data.contenu.intro ?? "");
  const [delai, setDelai] = useState(data.contenu.delai_reponse ?? "");
  const [prestations, setPrestations] = useState<PrestationPack[]>(
    (data.contenu.prestations ?? []).map((p) => ({ titre: p.titre, detail: p.detail }))
  );

  const setPresta = (i: number, patch: Partial<PrestationPack>) =>
    setPrestations((arr) => arr.map((p, j) => (j === i ? { ...p, ...patch } : p)));
  const addPresta = () => setPrestations((arr) => [...arr, { titre: "", detail: "" }]);
  const removePresta = (i: number) => setPrestations((arr) => arr.filter((_, j) => j !== i));

  return (
    <>
      <p className="text-xs text-gray-400 mb-4 -mt-3">
        Modifiez ce que ce niveau ajoute ; les prestations heritees du niveau inferieur
        sont reprises automatiquement.
      </p>

      {data.herite.length > 0 && (
        <div className="mb-4 rounded-lg border border-gray-200 bg-gray-50 p-3">
          <p className="text-xs font-semibold text-gray-500 mb-2">
            Herite du niveau inferieur (lecture seule)
          </p>
          <ul className="space-y-1">
            {data.herite.map((p, i) => (
              <li key={i} className="text-xs text-gray-500">
                <span className="font-medium text-gray-600">{p.titre}</span>
                {p.detail ? ` : ${p.detail}` : ""}
              </li>
            ))}
          </ul>
        </div>
      )}

      <form action={saveContenuPack} className="space-y-4">
        <input type="hidden" name="id" value={data.option_id} />
        <input type="hidden" name="prestations_json" value={JSON.stringify(prestations)} />

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Accroche</label>
          <input value={accroche} onChange={(e) => setAccroche(e.target.value)} name="accroche"
            className="w-full border rounded px-3 py-2.5 text-sm"
            placeholder="Phrase courte affichee en tete du bloc maintenance." />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Intro (facultatif)</label>
          <textarea value={intro} onChange={(e) => setIntro(e.target.value)} name="intro" rows={2}
            className="w-full border rounded px-3 py-2.5 text-sm"
            placeholder="Texte de presentation affiche sous l'accroche (souvent vide hors socle)." />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Delai de reponse</label>
          <input value={delai} onChange={(e) => setDelai(e.target.value)} name="delai_reponse"
            className="w-full border rounded px-3 py-2.5 text-sm" placeholder="ex. 24 heures ouvrees" />
        </div>

        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="block text-sm font-medium text-gray-700">
              Prestations ajoutees par ce niveau
            </label>
            <button type="button" onClick={addPresta}
              className="text-xs px-2 py-1 border border-[#1A355E] text-[#1A355E] rounded font-medium">
              + Ajouter
            </button>
          </div>
          {prestations.length === 0 && (
            <p className="text-xs text-gray-400 mb-2">
              Aucune prestation propre a ce niveau (il reprend seulement l&apos;herite).
            </p>
          )}
          <div className="space-y-3">
            {prestations.map((p, i) => (
              <div key={i} className="rounded-lg border border-gray-200 p-3 space-y-2">
                <div className="flex items-center gap-2">
                  <input value={p.titre} onChange={(e) => setPresta(i, { titre: e.target.value })}
                    className="flex-1 border rounded px-3 py-2 text-sm font-medium" placeholder="Titre de la prestation" />
                  <button type="button" onClick={() => removePresta(i)}
                    className="px-2 py-2 text-red-600 hover:bg-red-50 rounded text-sm" title="Supprimer">
                    Supprimer
                  </button>
                </div>
                <textarea value={p.detail} onChange={(e) => setPresta(i, { detail: e.target.value })} rows={2}
                  className="w-full border rounded px-3 py-2 text-sm" placeholder="Description detaillee" />
              </div>
            ))}
          </div>
        </div>

        <button type="submit" className="px-6 py-3 bg-[#1A355E] text-white rounded-lg font-medium text-sm">
          Enregistrer le contenu
        </button>
      </form>
    </>
  );
}
