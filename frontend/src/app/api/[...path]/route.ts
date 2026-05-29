import { NextRequest, NextResponse } from "next/server";

const BACKEND = "http://127.0.0.1:8000";

async function proxy(req: NextRequest) {
  const path = req.nextUrl.pathname;
  const search = req.nextUrl.search;
  const url = `${BACKEND}${path}${search}`;

  const headers: Record<string, string> = {};
  if (req.headers.get("content-type")) {
    headers["content-type"] = req.headers.get("content-type")!;
  }

  const res = await fetch(url, {
    method: req.method,
    headers,
    body: req.method !== "GET" && req.method !== "HEAD" ? await req.text() : undefined,
    redirect: "follow",
  });

  const data = await res.arrayBuffer();
  const outHeaders: Record<string, string> = {
    "content-type": res.headers.get("content-type") || "application/json",
  };
  // Preserver le nom de fichier pour les telechargements (devis/factures Word)
  const disposition = res.headers.get("content-disposition");
  if (disposition) outHeaders["content-disposition"] = disposition;

  return new NextResponse(data, {
    status: res.status,
    headers: outHeaders,
  });
}

export const GET = proxy;
export const POST = proxy;
export const PATCH = proxy;
export const PUT = proxy;
export const DELETE = proxy;
