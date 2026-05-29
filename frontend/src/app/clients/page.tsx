import { serverFetch, type Client } from "@/lib/api";
import Link from "next/link";

export const dynamic = "force-dynamic";

export default async function ClientsPage(
  { searchParams }: { searchParams: Promise<{ q?: string }> }
) {
  const params = await searchParams;
  const q = (params.q || "").trim();
  let clients: Client[] = [];
  let error = "";

  try {
    clients = await serverFetch<Client[]>(`/clients/${q ? `?q=${encodeURIComponent(q)}` : ""}`);
  } catch (e) {
    error = String(e);
  }

  if (error) return <p className="text-red-600 p-4">Erreur : {error}</p>;

  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Clients ({clients.length})</h1>
        <Link href="/clients/edit"
          className="px-4 py-2.5 bg-[#1A355E] text-white rounded text-sm font-medium text-center">
          + Nouveau client
        </Link>
      </div>

      {/* Recherche */}
      <form method="GET" className="mb-4 flex gap-2">
        <input
          type="search" name="q" defaultValue={q}
          placeholder="Rechercher (raison sociale, ville, email, interlocuteur)..."
          className="flex-1 border rounded px-3 py-2 text-sm"
        />
        <button type="submit" className="px-4 py-2 bg-[#1A355E] text-white rounded text-sm font-medium">Rechercher</button>
        {q && <Link href="/clients" className="px-4 py-2 border border-gray-300 text-gray-600 rounded text-sm font-medium">Effacer</Link>}
      </form>

      {/* Mobile : cards */}
      <div className="sm:hidden space-y-3">
        {clients.map((c) => (
          <Link key={c.id} href={`/clients/edit?id=${c.id}`} className="block bg-white border rounded-lg p-4">
            <h3 className="font-medium text-sm mb-2">{c.raison_sociale}</h3>
            <div className="space-y-1 text-sm text-gray-600">
              {c.ville && <p>{c.code_postal} {c.ville}</p>}
              {c.interlocuteur && <p>{c.interlocuteur}</p>}
              {c.telephone && <p>{c.telephone}</p>}
              {c.email && <p>{c.email}</p>}
              {c.siret && <p className="font-mono text-xs text-gray-400">SIRET {c.siret}</p>}
            </div>
          </Link>
        ))}
        {clients.length === 0 && <p className="text-center text-gray-400 py-8">Aucun client</p>}
      </div>

      {/* Desktop : tableau */}
      <div className="hidden sm:block bg-white rounded-lg border overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left">
            <tr>
              <th className="px-4 py-3 font-medium">Raison sociale</th>
              <th className="px-4 py-3 font-medium">Ville</th>
              <th className="px-4 py-3 font-medium">Interlocuteur</th>
              <th className="px-4 py-3 font-medium">Telephone</th>
              <th className="px-4 py-3 font-medium">Email</th>
              <th className="px-4 py-3 font-medium">SIRET</th>
              <th className="px-4 py-3"></th>
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
                <td className="px-4 py-3 text-right">
                  <Link href={`/clients/edit?id=${c.id}`} className="text-blue-600 hover:underline text-xs">Modifier</Link>
                </td>
              </tr>
            ))}
            {clients.length === 0 && (
              <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-400">Aucun client</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
