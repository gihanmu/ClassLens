# Public Assets

Files placed in this directory (`apps/web/public`) are served statically by Next.js from the root URL path (`/`).

## Directories

- **`logos/`**: Store organization, school, app, or sponsor logos (e.g. `apps/web/public/logos/classlens-logo.svg`).
  - Access in components: `<Image src="/logos/classlens-logo.svg" alt="Logo" width={40} height={40} />` or `<img src="/logos/classlens-logo.svg" alt="Logo" />`
- **`images/`**: Store general static images, icons, or banners.
  - Access in components: `<Image src="/images/banner.png" alt="Banner" width={800} height={200} />`

> **Note:** Next.js serves files in `public/` directly from `/`. Do not include `public` in the file path when referencing assets in code.
