/**
 * ClassLens Design System Token Constants & Type Definitions
 */

export const colors = {
  brand: {
    primary: "#5145F5",
    primaryHover: "#4035D5",
    primaryActive: "#3026B5",
    primarySoft: "#EEECFF",
    coral: "#F76543",
    coralHover: "#D94D2D",
    yellow: "#FFCF78",
    yellowSoft: "#FFF3D6",
    mint: "#D8F4E8",
    blue: "#3D91F5",
    purpleSoft: "#F1ECFF",
  },
  ink: {
    primary: "#10182B",
    secondary: "#475569",
    muted: "#64748B",
  },
  surface: {
    page: "#F7F9FC",
    card: "#FFFFFF",
    warm: "#FFF9ED",
    subtle: "#F1F5F9",
  },
  border: {
    default: "#DDE4ED",
    strong: "#B7C3D4",
  },
  semantic: {
    success: {
      text: "#087A53",
      bg: "#E7F8EF",
      border: "#A3E7C8",
    },
    error: {
      text: "#B42332",
      bg: "#FFF0F1",
      border: "#FECDCA",
    },
    warning: {
      text: "#925300",
      bg: "#FFF2D6",
      border: "#FEDF89",
    },
    info: {
      text: "#175CD3",
      bg: "#EAF3FF",
      border: "#B2DDFF",
    },
    neutral: {
      text: "#475569",
      bg: "#F1F5F9",
      border: "#DDE4ED",
    },
  },
} as const;

export const radii = {
  xs: "4px",
  sm: "6px",
  md: "10px",
  lg: "14px",
  xl: "20px",
  "2xl": "28px",
  full: "9999px",
} as const;

export const shadows = {
  sm: "0 1px 3px rgba(16, 24, 43, 0.05), 0 1px 2px rgba(16, 24, 43, 0.03)",
  md: "0 4px 6px -1px rgba(16, 24, 43, 0.08), 0 2px 4px -1px rgba(16, 24, 43, 0.04)",
  lg: "0 10px 15px -3px rgba(16, 24, 43, 0.1), 0 4px 6px -2px rgba(16, 24, 43, 0.05)",
  modal: "0 20px 25px -5px rgba(16, 24, 43, 0.12), 0 10px 10px -5px rgba(16, 24, 43, 0.04)",
} as const;
