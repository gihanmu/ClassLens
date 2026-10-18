import { NextRequest } from "next/server";
import { proxyToBackend } from "@/lib/bff-proxy";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";
export const maxDuration = 300;

type RouteContext = {
  params: {
    path?: string[];
  };
};

async function handleApiProxy(request: NextRequest, context: RouteContext) {
  const segments = context.params?.path || [];
  const targetPath = `/api/${segments.join("/")}`;
  return proxyToBackend(request, targetPath);
}

export async function GET(request: NextRequest, context: RouteContext) {
  return handleApiProxy(request, context);
}

export async function HEAD(request: NextRequest, context: RouteContext) {
  return handleApiProxy(request, context);
}

export async function POST(request: NextRequest, context: RouteContext) {
  return handleApiProxy(request, context);
}

export async function PUT(request: NextRequest, context: RouteContext) {
  return handleApiProxy(request, context);
}

export async function PATCH(request: NextRequest, context: RouteContext) {
  return handleApiProxy(request, context);
}

export async function DELETE(request: NextRequest, context: RouteContext) {
  return handleApiProxy(request, context);
}

export async function OPTIONS(request: NextRequest, context: RouteContext) {
  return handleApiProxy(request, context);
}
