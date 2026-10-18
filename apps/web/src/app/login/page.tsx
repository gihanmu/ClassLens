"use client";

import * as React from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { BrandLogo } from "@/components/shared/brand-logo";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Alert } from "@/components/ui/alert";
import { api } from "@/lib/api";
import {
  Lock,
  Mail,
  Eye,
  EyeOff,
  GraduationCap,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

function sanitizeRedirectUrl(url: string | null): string {
  if (!url) return "/";
  const trimmed = url.trim();
  // Ensure relative path starting with / and not protocol-relative //
  if (trimmed.startsWith("/") && !trimmed.startsWith("//")) {
    return trimmed;
  }
  return "/";
}

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const redirectUrl = sanitizeRedirectUrl(searchParams.get("redirect"));
  const isSessionExpired = searchParams.get("session_expired") === "true";

  const [username, setUsername] = React.useState("teacher@classlens.demo");
  const [password, setPassword] = React.useState("");
  const [showPassword, setShowPassword] = React.useState(false);
  const [loading, setLoading] = React.useState(false);
  const [checkingAuth, setCheckingAuth] = React.useState(true);
  const [errorMessage, setErrorMessage] = React.useState<string | null>(null);

  // Check if teacher already has an active session on mount
  React.useEffect(() => {
    let isMounted = true;
    api
      .getCurrentUser()
      .then((user) => {
        if (isMounted && user) {
          router.replace(redirectUrl);
        }
      })
      .catch(() => {
        if (isMounted) setCheckingAuth(false);
      });

    return () => {
      isMounted = false;
    };
  }, [router, redirectUrl]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    const cleanUsername = username.trim();
    if (!cleanUsername) {
      setErrorMessage("Please enter your teacher username or email address.");
      return;
    }
    if (!password) {
      setErrorMessage("Please enter your password.");
      return;
    }

    try {
      setLoading(true);
      await api.login(cleanUsername, password);
      // Successful login -> redirect to destination
      router.push(redirectUrl);
    } catch (err: any) {
      console.warn("Login failed:", err);
      const msg =
        err.message ||
        "Invalid username or password. Please verify your credentials and try again.";
      setErrorMessage(msg);
    } finally {
      setLoading(false);
    }
  };

  if (checkingAuth) {
    return (
      <div className="flex flex-col items-center justify-center py-16 space-y-4">
        <div className="w-8 h-8 border-3 border-brand-primary/30 border-t-brand-primary rounded-full animate-spin" />
        <p className="text-xs text-ink-muted">Checking authentication session...</p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Session Expired Notice */}
      {isSessionExpired && !errorMessage && (
        <Alert variant="warning" title="Session Expired">
          Your session has expired. Please sign in with your teacher credentials to resume your work.
        </Alert>
      )}

      {/* Error Notice */}
      {errorMessage && (
        <Alert variant="error" title="Sign In Failed">
          {errorMessage}
        </Alert>
      )}

      {/* Username / Email Field */}
      <div>
        <label
          htmlFor="login-username"
          className="block text-xs font-semibold text-ink-primary mb-1.5"
        >
          Teacher Username / Email
        </label>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-ink-muted">
            <Mail className="w-4 h-4" />
          </div>
          <Input
            id="login-username"
            type="text"
            autoComplete="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="teacher@classlens.demo"
            className="pl-9 h-10 text-sm font-sans"
            disabled={loading}
            required
          />
        </div>
        <span className="text-[11px] text-ink-muted mt-1 block">
          Default persona: <span className="font-mono text-ink-secondary">teacher@classlens.demo</span>
        </span>
      </div>

      {/* Password Field with Visibility Toggle */}
      <div>
        <label
          htmlFor="login-password"
          className="block text-xs font-semibold text-ink-primary mb-1.5"
        >
          Password
        </label>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-ink-muted">
            <Lock className="w-4 h-4" />
          </div>
          <Input
            id="login-password"
            type={showPassword ? "text" : "password"}
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter your teacher password"
            className="pl-9 pr-10 h-10 text-sm font-sans"
            disabled={loading}
            required
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute inset-y-0 right-0 pr-3 flex items-center text-ink-muted hover:text-ink-primary transition-colors focus:outline-none"
            aria-label={showPassword ? "Hide password" : "Show password"}
          >
            {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </button>
        </div>
      </div>



      {/* Submit Button */}
      <Button
        type="submit"
        variant="primary"
        className="w-full h-11 text-sm font-semibold shadow-xs transition-transform active:scale-[0.99]"
        isLoading={loading}
      >
        <Sparkles className="w-4 h-4 mr-2" />
        Sign In to Teacher Portal
      </Button>

      {/* Security disclosures */}
      <div className="pt-2 text-center">
        <p className="text-[11px] text-ink-muted inline-flex items-center gap-1.5">
          <ShieldCheck className="w-3.5 h-3.5 text-semantic-success" />
          Protected by Argon2id password hashing and secure HTTP-only cookies
        </p>
      </div>
    </form>
  );
}

export default function LoginPage() {
  return (
    <div className="min-h-screen bg-surface-canvas flex flex-col justify-center items-center p-4 sm:p-6 lg:p-8 font-sans">
      <div className="max-w-md w-full">
        {/* School & Department Badge */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-brand-light/70 border border-brand-primary/20 text-brand-primary text-xs font-semibold shadow-2xs mb-4">
            <GraduationCap className="w-4 h-4" />
            <span>Cedar Secondary School • Mathematics</span>
          </div>

          <div className="flex justify-center mb-2">
            <BrandLogo size="lg" showSubtitle />
          </div>

          <p className="text-xs text-ink-muted mt-2 max-w-sm mx-auto">
            Teacher Diagnostic Workspace for Secondary 1 Mathematics
          </p>
        </div>

        {/* Login Card */}
        <div className="bg-surface-base rounded-2xl border border-border-default shadow-sm p-6 sm:p-8">
          <div className="mb-6 pb-4 border-b border-border-default">
            <h1 className="text-lg font-bold text-ink-primary">Teacher Portal Login</h1>
            <p className="text-xs text-ink-secondary mt-0.5">
              Sign in with your Singapore MOE / School credentials
            </p>
          </div>

          <React.Suspense
            fallback={
              <div className="flex flex-col items-center justify-center py-12 space-y-3">
                <div className="w-6 h-6 border-2 border-brand-primary/30 border-t-brand-primary rounded-full animate-spin" />
                <p className="text-xs text-ink-muted">Loading login portal...</p>
              </div>
            }
          >
            <LoginForm />
          </React.Suspense>
        </div>

        {/* Footer info */}
        <div className="mt-6 text-center text-xs text-ink-muted">
          <p>© 2026 ClassLens Singapore • AI Builder Cup Prototype</p>
        </div>
      </div>
    </div>
  );
}
