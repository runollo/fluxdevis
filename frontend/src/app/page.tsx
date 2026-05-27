export default function Dashboard() {
  return (
    <div>
      <h1 className="text-xl sm:text-2xl font-bold text-gray-900 mb-4 sm:mb-6">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          { label: "Offres actives", value: "10", bg: "bg-blue-50", border: "border-blue-300", text: "text-blue-900" },
          { label: "Options catalogue", value: "52", bg: "bg-green-50", border: "border-green-300", text: "text-green-900" },
          { label: "Clients", value: "-", bg: "bg-orange-50", border: "border-orange-300", text: "text-orange-900" },
        ].map((card) => (
          <div key={card.label} className={`rounded-lg border p-5 ${card.bg} ${card.border}`}>
            <p className="text-sm text-gray-700 font-medium">{card.label}</p>
            <p className={`text-3xl font-bold mt-1 ${card.text}`}>{card.value}</p>
          </div>
        ))}
      </div>
      <div className="mt-6 rounded-lg border border-gray-200 bg-white p-5 sm:p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-3">Bienvenue sur FluxDevis</h2>
        <p className="text-gray-700 text-sm leading-relaxed">
          Application de gestion des devis et factures pour FluXweb.
          Utilisez le menu hamburger en haut pour naviguer entre le catalogue,
          les clients et le simulateur de prix.
        </p>
      </div>
    </div>
  );
}
