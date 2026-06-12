// Bandeau affiche quand le chargement des donnees depuis le backend a echoue
// (serveur injoignable, 500...). Distingue "service indisponible" d'une vraie
// liste vide, pour ne plus laisser l'utilisateur devant une page vide muette.

export default function ErreurChargement({ quoi = "les donnees" }: { quoi?: string }) {
  return (
    <div role="alert" className="mb-4 rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
      Service momentanement indisponible : impossible de charger {quoi}. Verifiez que le
      serveur repond, puis actualisez la page.
    </div>
  );
}
