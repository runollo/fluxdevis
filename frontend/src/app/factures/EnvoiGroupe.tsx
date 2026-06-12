"use client";

// Envoi GROUPE de plusieurs factures en pieces jointes (PDF) dans un seul email.
// Cas d'usage : le comptable reclame les factures. On ouvre une popup, on coche
// les factures (emises uniquement), puis on choisit le destinataire :
// - toutes du MEME client -> a moi / au client / les deux ;
// - clients differents     -> a moi uniquement (jamais les factures d'un client
//   a un autre).
// L'appel passe par /api/factures/envoyer-lot (proxy -> backend).

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";

interface FactureLite {
  id: number; numero: string; type: string; statut: string;
  total_ttc: string; date_emission: string;
  client?: string | null; client_id?: number | null;
}

function eur(v: number | string) {
  return Number(v).toLocaleString("fr-FR", { style: "currency", currency: "EUR" });
}

export default function EnvoiGroupe(
  { factures, envoiClientActif }: { factures: FactureLite[]; envoiClientActif: boolean }
) {
  // Seules les factures EMISES (numero legal) sont envoyables ; pas les brouillons.
  const envoyables = useMemo(
    () => factures.filter(f => f.statut !== "brouillon"),
    [factures]
  );
  const [open, setOpen] = useState(false);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [mode, setMode] = useState<"moi" | "client" | "deux">("moi");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState<string | null>(null);
  const router = useRouter();

  const selFactures = envoyables.filter(f => selected.has(f.id));
  const clientIds = new Set(selFactures.map(f => f.client_id ?? -1));
  const monoClient = selFactures.length > 0 && clientIds.size === 1;
  const nomClient = monoClient ? (selFactures[0].client || "ce client") : "";
  // L'envoi au client n'est offert que si toutes les factures sont du meme client
  // ET que l'envoi direct au client est active dans Parametres.
  const peutClient = monoClient && envoiClientActif;
  const modeEffectif: "moi" | "client" | "deux" = peutClient ? mode : "moi";

  function toggle(id: number) {
    setSelected(prev => {
      const n = new Set(prev);
      if (n.has(id)) n.delete(id); else n.add(id);
      return n;
    });
  }
  function toggleAll() {
    setSelected(prev =>
      prev.size === envoyables.length ? new Set() : new Set(envoyables.map(f => f.id))
    );
  }
  function fermer() {
    if (sending) return;
    setOpen(false);
  }

  async function envoyer() {
    setSending(true); setError(null); setDone(null);
    const au_client = modeEffectif === "client" || modeEffectif === "deux";
    const a_moi = modeEffectif === "moi" || modeEffectif === "deux";
    try {
      const res = await fetch("/api/factures/envoyer-lot", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ facture_ids: [...selected], au_client, a_moi }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || `Erreur ${res.status}`);
      }
      setDone("Envoi effectue.");
      setSelected(new Set());
      router.refresh();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Echec de l'envoi.");
    } finally {
      setSending(false);
    }
  }

  if (envoyables.length === 0) return null;

  return (
    <>
      <button
        type="button"
        onClick={() => { setOpen(true); setError(null); setDone(null); }}
        className="px-4 py-2.5 border border-[#1A355E] text-[#1A355E] rounded text-sm font-medium text-center"
      >
        Envoyer plusieurs factures
      </button>

      {open && (
        <div
          className="fixed inset-0 z-50 flex items-start sm:items-center justify-center bg-black/40 p-4 overflow-y-auto"
          onClick={fermer}
        >
          <div
            className="bg-white rounded-lg shadow-xl w-full max-w-lg p-5 my-8"
            onClick={e => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-lg font-semibold text-gray-900">Envoyer des factures (PDF)</h2>
              <button type="button" onClick={fermer} className="text-gray-400 hover:text-gray-600 text-2xl leading-none">&times;</button>
            </div>

            <p className="text-xs text-gray-500 mb-2">
              Cochez les factures a joindre ({envoyables.length} facture(s) emise(s) disponible(s)).
            </p>

            <div className="border rounded max-h-64 overflow-y-auto divide-y mb-3">
              <label className="flex items-center gap-2 px-3 py-2 bg-gray-50 text-sm font-medium cursor-pointer">
                <input
                  type="checkbox"
                  checked={envoyables.length > 0 && selected.size === envoyables.length}
                  onChange={toggleAll}
                />
                Tout selectionner
              </label>
              {envoyables.map(f => (
                <label key={f.id} className="flex items-center gap-2 px-3 py-2 text-sm cursor-pointer hover:bg-gray-50">
                  <input type="checkbox" checked={selected.has(f.id)} onChange={() => toggle(f.id)} />
                  <span className="font-mono">{f.numero}</span>
                  <span className="text-gray-500 truncate flex-1">{f.client || ""}</span>
                  <span className="text-gray-600 whitespace-nowrap">{eur(f.total_ttc)}</span>
                </label>
              ))}
            </div>

            {selFactures.length > 0 && (
              <div className="mb-3 text-sm">
                {monoClient ? (
                  <>
                    <p className="text-gray-600 mb-1">
                      {selFactures.length} facture(s), client : <b>{nomClient}</b>. Envoyer :
                    </p>
                    <div className="flex flex-col gap-1">
                      <label className="flex items-center gap-2">
                        <input type="radio" name="dest" checked={modeEffectif === "moi"} onChange={() => setMode("moi")} />
                        A moi (pour transferer, ex. au comptable)
                      </label>
                      <label className={`flex items-center gap-2 ${peutClient ? "" : "text-gray-400"}`}>
                        <input type="radio" name="dest" disabled={!peutClient} checked={modeEffectif === "client"} onChange={() => setMode("client")} />
                        Au client ({nomClient})
                      </label>
                      <label className={`flex items-center gap-2 ${peutClient ? "" : "text-gray-400"}`}>
                        <input type="radio" name="dest" disabled={!peutClient} checked={modeEffectif === "deux"} onChange={() => setMode("deux")} />
                        Les deux
                      </label>
                    </div>
                    {!envoiClientActif && (
                      <p className="text-[11px] text-amber-700 mt-1">
                        Envoi direct au client desactive (Parametres) : seul l&apos;envoi a vous-meme est possible.
                      </p>
                    )}
                  </>
                ) : (
                  <p className="text-gray-600">
                    {selFactures.length} factures de <b>clients differents</b> : envoi <b>a vous-meme</b> uniquement.
                  </p>
                )}
              </div>
            )}

            {error && <p className="text-sm text-red-600 mb-2">{error}</p>}
            {done && <p className="text-sm text-green-700 mb-2">{done}</p>}

            <div className="flex justify-end gap-2">
              <button type="button" onClick={fermer} className="px-4 py-2 border border-gray-300 text-gray-600 rounded text-sm">Fermer</button>
              <button
                type="button"
                onClick={envoyer}
                disabled={sending || selFactures.length === 0}
                className="px-4 py-2 bg-[#1A355E] text-white rounded text-sm font-medium disabled:opacity-50"
              >
                {sending ? "Envoi..." : "Envoyer"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
