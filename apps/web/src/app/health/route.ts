import { NextRequest } from "next/server";
import { proxyToBackend } from "@/lib/bff-proxy";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET(request: NextRequest) {
  return proxyToBackend(request, "/health");
}

export async function HEAD(request: NextRequest) {
  return proxyToBackend(request, "/health");
}
