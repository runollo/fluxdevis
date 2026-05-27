export default function Dashboard() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          { label: "Offres actives", value: "10", color: "bg-blue-50 border-blue-200" },
          { label: "Options catalogue", value: "52", color: "bg-green-50 border-green-200" },
          { label: "Clients", value: "-", color: "bg-orange-50 border-orange-200" },
        ].map((card) => (
          <div key={card.label} className={`rounded-lg border p-5 ${card.color}`}>
            <p className="text-sm text-gray-500">{card.label}</p>
            <p className="text-3xl font-bold mt-1">{card.value}</p>
          </div>
        ))}
      </div>
      <div className="mt-8 rounded-lg border bg-white p-6">
        <h2 className="text-lg font-semibold mb-3">Bienvenue sur FluxDevis</h2>
        <p className="text-gray-600 text-sm leading-relaxed">
          Application de gestion des devis et factures pour FluXweb.
          Utilisez le menu de gauche pour naviguer entre le catalogue,
          les clients et le simulateur de prix.
        </p>
      </div>
    </div>
  );
}
