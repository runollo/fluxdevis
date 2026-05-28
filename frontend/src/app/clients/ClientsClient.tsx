"use client";
import { useState } from "react";
import type { Client } from "@/lib/api";

export default function ClientsClient({ initialClients }: { initialClients: Client[] }) {
  const [clients] = useState<Client[]>(initialClients);

  return (
    <div>
      <h1 className="text-xl sm:text-2xl font-bold text-gray-900 mb-4">Clients ({clients.length})</h1>

      {/* Mobile : cards */}
      <div className="sm:hidden space-y-3">
        {clients.map((c) => (
          <div key={c.id} className="bg-white border rounded-lg p-4">
            <h3 className="font-medium text-sm mb-2">{c.raison_sociale}</h3>
            <div className="space-y-1 text-sm text-gray-600">
              {c.ville && <p>{c.code_postal} {c.ville}</p>}
              {c.interlocuteur && <p>{c.interlocuteur}</p>}
              {c.telephone && <p><a href={`tel:${c.telephone}`} className="text-blue-600 underline">{c.telephone}</a></p>}
              {c.email && <p><a href={`mailto:${c.email}`} className="text-blue-600 underline">{c.email}</a></p>}
              {c.siret && <p className="font-mono text-xs text-gray-400">SIRET {c.siret}</p>}
            </div>
          </div>
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
    </div>
  );
}
