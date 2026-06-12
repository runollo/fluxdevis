import Link from "next/link";

// Page 404 globale : affichee pour une URL inexistante ou via notFound().

export default function NotFound() {
  return (
    <div className="max-w-lg mx-auto mt-8 rounded-lg border border-gray-200 bg-white p-6 text-center">
      <h1 className="text-lg font-semibold text-gray-900 mb-2">Page introuvable</h1>
      <p className="text-sm text-gray-500 mb-4">
        La page ou le document demande n&apos;existe pas (ou a ete deplace).
      </p>
      <Link href="/" className="px-4 py-2 bg-[#1A355E] text-white rounded text-sm font-medium inline-block">
        Retour a l&apos;accueil
      </Link>
    </div>
  );
}
