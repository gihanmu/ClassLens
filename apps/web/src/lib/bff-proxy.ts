import { NextRequest, NextResponse } from "next/server";

interface CachedOidcToken {
  token: string;
  expiresAtMs: number;
}

const oidcTokenCache = new Map<string, CachedOidcToken>();

/**
 * Fetches and caches a Google-signed OIDC Identity Token from the local
 * Cloud Run Metadata Server for authenticated service-to-service calls
 * to the private classlens-backend Cloud Run service.
 */
async function getCloudRunIdToken(audienceOrigin: string): Promise<string | null> {
  if (process.env.CLASSLENS_DISABLE_METADATA_AUTH === "true") {
    return null;
  }

  const now = Date.now();
  const cached = oidcTokenCache.get(audienceOrigin);
  if (cached && cached.expiresAtMs > now) {
    return cached.token;
  }

  const metadataUrl = `http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity?audience=${encodeURIComponent(
    audienceOrigin
  )}`;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 2000);

  try {
    const res = await fetch(metadataUrl, {
      method: "GET",
      headers: {
        "Metadata-Flavor": "Google",
      },
      signal: controller.signal,
      cache: "no-store",
    });

    if (!res.ok) {
      return null;
    }

    const token = (await res.text()).trim();
    if (!token) {
      return null;
    }

    // Cache for 50 minutes (Google OIDC tokens have a 60-minute lifetime)
    oidcTokenCache.set(audienceOrigin, {
      token,
      expiresAtMs: now + 50 * 60 * 1000,
    });
    return token;
  } catch {
    // Running outside Cloud Run (e.g., local development)
    return null;
  } finally {
    clearTimeout(timeoutId);
  }
}

const FORWARDED_REQUEST_HEADERS = [
  "accept",
  "content-type",
  "cookie",
  "idempotency-key",
  "user-agent",
  "x-correlation-id",
  "x-csrf-token",
  "x-forwarded-for",
  "x-forwarded-proto",
  "x-live-auth-key",
  "x-requested-with",
];

const FORWARDED_RESPONSE_HEADERS = [
  "cache-control",
  "content-disposition",
  "content-type",
  "referrer-policy",
  "strict-transport-security",
  "x-content-type-options",
  "x-correlation-id",
  "x-frame-options",
];

/**
 * Runtime Backend-for-Frontend (BFF) proxy handler.
 * Forwards /api/* and /health requests to INTERNAL_API_URL at runtime,
 * attaching a Cloud Run OIDC identity token when calling a private Cloud Run backend
 * while preserving cookies, CSRF headers, and binary multipart file uploads.
 */
export async function proxyToBackend(
  request: NextRequest,
  targetPath: string
): Promise<NextResponse> {
  const rawBaseUrl = (process.env.INTERNAL_API_URL || "http://127.0.0.1:8000").replace(/\/+$/, "");
  const search = request.nextUrl.search || "";
  const upstreamUrl = `${rawBaseUrl}${targetPath}${search}`;

  const upstreamHeaders = new Headers();
  for (const headerName of FORWARDED_REQUEST_HEADERS) {
    const value = request.headers.get(headerName);
    if (value) {
      upstreamHeaders.set(headerName, value);
    }
  }

  // Attach Cloud Run service-to-service OIDC Identity Token when targeting an HTTPS backend
  if (rawBaseUrl.startsWith("https://")) {
    try {
      const audienceOrigin = new URL(rawBaseUrl).origin;
      const idToken = await getCloudRunIdToken(audienceOrigin);
      if (idToken) {
        upstreamHeaders.set("authorization", `Bearer ${idToken}`);
      }
    } catch {
      // Proceed without OIDC token if URL parsing fails
    }
  } else {
    const existingAuth = request.headers.get("authorization");
    if (existingAuth) {
      upstreamHeaders.set("authorization", existingAuth);
    }
  }

  const method = request.method.toUpperCase();
  let bodyBuffer: ArrayBuffer | undefined = undefined;
  if (method !== "GET" && method !== "HEAD" && method !== "OPTIONS") {
    const buf = await request.arrayBuffer();
    if (buf.byteLength > 0) {
      bodyBuffer = buf;
    }
  }

  try {
    const upstreamRes = await fetch(upstreamUrl, {
      method,
      headers: upstreamHeaders,
      body: bodyBuffer,
      redirect: "manual",
      cache: "no-store",
    });

    const responseHeaders = new Headers();
    for (const headerName of FORWARDED_RESPONSE_HEADERS) {
      const value = upstreamRes.headers.get(headerName);
      if (value) {
        responseHeaders.set(headerName, value);
      }
    }

    // Preserve all Set-Cookie headers (e.g. HttpOnly __session and csrf_token cookies)
    if (typeof upstreamRes.headers.getSetCookie === "function") {
      const cookies = upstreamRes.headers.getSetCookie();
      for (const cookie of cookies) {
        responseHeaders.append("set-cookie", cookie);
      }
    } else {
      const singleCookie = upstreamRes.headers.get("set-cookie");
      if (singleCookie) {
        responseHeaders.set("set-cookie", singleCookie);
      }
    }

    const responseBody =
      method === "HEAD" || upstreamRes.status === 204 || upstreamRes.status === 304
        ? null
        : await upstreamRes.arrayBuffer();

    return new NextResponse(responseBody, {
      status: upstreamRes.status,
      headers: responseHeaders,
    });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Upstream backend unreachable";
    return NextResponse.json(
      {
        detail: "Backend service unavailable",
        error: message,
      },
      { status: 502 }
    );
  }
}
