import { serverFetch, type Client } from "@/lib/api";
import ClientsClient from "./ClientsClient";

export const dynamic = "force-dynamic";

export default async function ClientsPage() {
  let clients: Client[] = [];
  let error = "";

  try {
    clients = await serverFetch<Client[]>("/clients/");
  } catch (e) {
    error = String(e);
  }

  if (error) {
    return <p className="text-red-600 p-4">Erreur : {error}</p>;
  }

  return <ClientsClient initialClients={clients} />;
}
