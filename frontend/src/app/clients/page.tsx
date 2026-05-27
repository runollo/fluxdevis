"use client";
import { useEffect, useState } from "react";
import { api, type Client } from "@/lib/api";

export default function ClientsPage() {
  const [clients, setClients] = useState<Client[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ raison_sociale: "", adresse: "", code_postal: "", ville: "", interlocuteur: "", telephone: "", email: "", siret: "" });

  const load = (q?: string) => {
    setLoading(true);
    api.clients.list(q).then(setClients).catch((e) => setError(e.message)).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleSearch = (e: React.FormEvent) => { e.preventDefault(); load(search); };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const c = await api.clients.create(form);
      setClients((prev) => [...prev, c]);
      setShowForm(false);
      setForm({ raison_sociale: "", adresse: "", code_postal: "", ville: "", interlocuteur: "", telephone: "", email: "", siret: "" });
    } catch (err) { setError(String(err)); }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">Clients</h1>
        <button onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 bg-[#1A355E] text-white rounded text-sm hover:bg-[#15294a]">
          {showForm ? "Annuler" : "+ Nouveau client"}
        </button>
      </div>

      <form onSubmit={handleSearch} className="flex gap-2 mb-4">
        <input value={search} onChange={(e) => setSearch(e.target.value)}
          placeholder="Rechercher par raison sociale..."
          className="flex-1 border rounded px-3 py-2 text-sm" />
        <button type="submit" className="px-4 py-2 bg-gray-200 rounded text-sm hover:bg-gray-300">Rechercher</button>
      </form>

      {showForm && (
        <form onSubmit={handleCreate} className="bg-white border rounded-lg p-4 mb-4 grid grid-cols-2 gap-3">
          {Object.entries(form).map(([key, val]) => (
            <div key={key}>
              <label className="block text-xs font-medium text-gray-500 mb-1">{key.replace("_", " ")}</label>
              <input value={val} onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                className="w-full border rounded px-3 py-1.5 text-sm"
                required={key === "raison_sociale"} />
            </div>
          ))}
          <div className="col-span-2">
            <button type="submit" className="px-4 py-2 bg-[#1A355E] text-white rounded text-sm">Enregistrer</button>
          </div>
        </form>
      )}

      {error && <p className="text-red-600 mb-3">{error}</p>}
      {loading ? <p className="text-gray-500">Chargement...</p> : (
        <div className="bg-white rounded-lg border overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left">
              <tr>
                <th className="px-4 py-3 font-medium">Raison sociale</th>
                <th className="px-4 py-3 font-medium">Ville</th>
                <th className="px-4 py-3 font-medium">Interlocuteur</th>
                <th className="px-4 py-3 font-medium">Telephone</th>
                <th className="px-4 py-3 font-medium">Email</th>
                <th className="px-4 py-3 font-medium">SIRET</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {clients.map((c) => (
                <tr key={c.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">{c.raison_sociale}</td>
                  <td className="px-4 py-3 text-gray-500">{c.ville || "-"}</td>
                  <td className="px-4 py-3">{c.interlocuteur || "-"}</td>
                  <td className="px-4 py-3">{c.telephone || "-"}</td>
                  <td className="px-4 py-3">{c.email || "-"}</td>
                  <td className="px-4 py-3 font-mono text-xs">{c.siret || "-"}</td>
                </tr>
              ))}
              {clients.length === 0 && (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400">Aucun client</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
