import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Canonical Design Tokens linked to CSS Custom Properties
        brand: {
          primary: "var(--brand-primary)",
          "primary-hover": "var(--brand-primary-hover)",
          "primary-active": "var(--brand-primary-active)",
          "primary-soft": "var(--brand-primary-soft)",
          coral: "var(--brand-coral)",
          "coral-hover": "var(--brand-coral-hover)",
          yellow: "var(--brand-yellow)",
          "yellow-soft": "var(--brand-yellow-soft)",
          mint: "var(--brand-mint)",
          blue: "var(--brand-blue)",
          "purple-soft": "var(--brand-purple-soft)",
        },
        ink: {
          primary: "var(--ink-primary)",
          secondary: "var(--ink-secondary)",
          muted: "var(--ink-muted)",
        },
        surface: {
          page: "var(--surface-page)",
          card: "var(--surface-card)",
          base: "var(--surface-base)",
          canvas: "var(--surface-canvas)",
          warm: "var(--surface-warm)",
          subtle: "var(--surface-subtle)",
          muted: "var(--surface-muted)",
        },
        border: {
          default: "var(--border-default)",
          strong: "var(--border-strong)",
          subtle: "var(--border-subtle)",
        },
        semantic: {
          success: "var(--semantic-success)",
          "success-soft": "var(--semantic-success-soft)",
          "success-border": "var(--semantic-success-border)",
          error: "var(--semantic-error)",
          "error-soft": "var(--semantic-error-soft)",
          "error-border": "var(--semantic-error-border)",
          warning: "var(--semantic-warning)",
          "warning-soft": "var(--semantic-warning-soft)",
          "warning-border": "var(--semantic-warning-border)",
          info: "var(--semantic-info)",
          "info-soft": "var(--semantic-info-soft)",
          "info-border": "var(--semantic-info-border)",
          neutral: "var(--semantic-neutral)",
          "neutral-soft": "var(--semantic-neutral-soft)",
          "neutral-border": "var(--semantic-neutral-border)",
        },
      },
      borderRadius: {
        xs: "var(--radius-xs)",
        sm: "var(--radius-sm)",
        md: "var(--radius-md)",
        lg: "var(--radius-lg)",
        xl: "var(--radius-xl)",
        "2xl": "var(--radius-2xl)",
        full: "var(--radius-full)",
      },
      boxShadow: {
        sm: "var(--shadow-sm)",
        md: "var(--shadow-md)",
        lg: "var(--shadow-lg)",
        modal: "var(--shadow-modal)",
      },
      fontFamily: {
        sans: [
          "Plus Jakarta Sans",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
        mono: [
          "IBM Plex Mono",
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "Monaco",
          "Consolas",
          "Liberation Mono",
          "monospace",
        ],
      },
    },
  },
  plugins: [],
};

export default config;
