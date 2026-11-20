---
name: "CivicOps — Municipal Operations Design System"
description: "Structured, light-mode civic-tech operations console prioritizing operational clarity, role separation, and high-density scannability."
---

## Overview

CivicOps is a municipal infrastructure operations platform built for clarity under operational load. It serves two distinct experiences—an approachable public/citizen portal and a high-density, role-aware operations console for City Admins, Department Officers, Field Officers, and Supervisors.

The design style is a **modern civic-tech operations console**: clean white and soft neutral surfaces, crisp 1px borders, minimal elevation, strong typographic hierarchy, and restrained semantic color. Every screen is structured so its user immediately understands what is happening, what requires attention, and what action should happen next.

## Colors

The palette anchors on authoritative **Deep Navy (`#172B4D`)** for navigation, headings, and structural emphasis, paired with **Civic Blue (`#3D6FB6`)** for primary actions and active states over a **Soft Slate (`#F5F7FA`)** canvas and **Pure White (`#FFFFFF`)** surfaces.

- **Primary (`#172B4D`) & Primary Action (`#3D6FB6`):** Navy grounds the navigation shell and primary typography; Civic Blue drives primary buttons, active links, and selected states.
- **Surfaces (`#FFFFFF`, `#F5F7FA`):** Light mode is primary. Crisp white cards sit on a muted `#F5F7FA` application background with subtle `#E2E8F0` borders.
- **Semantic Status Colors:** Success (`#15803D`), Warning (`#D97706`), and Error/Critical (`#DC2626`) are reserved strictly for operational states (resolved, approaching SLA, breached/critical) and must always be paired with text labels and icons—never color alone.

```yaml
colors:
  primary: "#172B4D"
  on-primary: "#FFFFFF"
  primary-action: "#3D6FB6"
  on-primary-action: "#FFFFFF"
  primary-action-container: "#E8F0FB"
  on-primary-action-container: "#172B4D"
  app-background: "#F5F7FA"
  surface: "#FFFFFF"
  on-surface: "#0F172A"
  surface-container-low: "#F8FAFC"
  surface-container: "#F1F5F9"
  surface-container-high: "#E2E8F0"
  on-surface-variant: "#475569"
  secondary-text: "#475569"
  outline: "#CBD5E1"
  outline-variant: "#E2E8F0"
  success: "#15803D"
  on-success: "#FFFFFF"
  success-container: "#DCFCE7"
  on-success-container: "#14532D"
  warning: "#D97706"
  on-warning: "#0F172A"
  warning-container: "#FEF3C7"
  on-warning-container: "#78350F"
  error: "#DC2626"
  on-error: "#FFFFFF"
  error-container: "#FEE2E2"
  on-error-container: "#7F1D1D"
```

## Typography

**Inter** serves as the single primary UI typeface across headings, body copy, tables, and dense operational controls, paired with **JetBrains Mono** for complaint IDs, work order codes, and coordinates. All numeric metrics, dates, and table figures use `tabular-nums` for vertical alignment.

Icons: Lucide

```yaml
typography:
  display-sm:
    fontFamily: "Inter"
    fontSize: 28px
    fontWeight: 700
    lineHeight: 34px
    letterSpacing: -0.5px
  headline-lg:
    fontFamily: "Inter"
    fontSize: 26px
    fontWeight: 600
    lineHeight: 32px
    letterSpacing: -0.4px
  headline-md:
    fontFamily: "Inter"
    fontSize: 18px
    fontWeight: 600
    lineHeight: 24px
    letterSpacing: -0.2px
  title-md:
    fontFamily: "Inter"
    fontSize: 15px
    fontWeight: 600
    lineHeight: 22px
    letterSpacing: -0.1px
  body-md:
    fontFamily: "Inter"
    fontSize: 14px
    fontWeight: 400
    lineHeight: 20px
    letterSpacing: 0px
  body-sm:
    fontFamily: "Inter"
    fontSize: 13px
    fontWeight: 400
    lineHeight: 18px
    letterSpacing: 0px
  label-md:
    fontFamily: "Inter"
    fontSize: 12px
    fontWeight: 500
    lineHeight: 16px
    letterSpacing: 0.1px
  label-sm:
    fontFamily: "Inter"
    fontSize: 11px
    fontWeight: 600
    lineHeight: 16px
    letterSpacing: 0.2px
  mono-sm:
    fontFamily: "JetBrains Mono"
    fontSize: 12px
    fontWeight: 500
    lineHeight: 16px
    letterSpacing: 0px
```

## Layout & Spacing

Authenticated desktop workspaces use a persistent **248px left sidebar** (collapsible to 68px icon-only) and a **56px top utility bar** framing a fluid main content area (`#F5F7FA`). A 12-column responsive grid organizes KPI rows, analytics panels, and two-column detail views.

- **Desktop (`>= 1280px`):** Full sidebar, multi-column dashboards, full data tables, split map/list views (`65–75%` map, `25–35%` list).
- **Tablet (`768px–1279px`):** Collapsible sidebar, two-column grids, horizontal table overflow.
- **Mobile (`< 768px`):** Bottom navigation for Citizen and Field Officer apps, stacked single-column cards, touch targets `>= 44px`.

```yaml
spacing:
  xs: 4px
  sm: 8px
  md: 12px
  lg: 16px
  xl: 24px
  2xl: 32px
  3xl: 40px
  4xl: 48px
```

## Elevation & Depth

Hierarchy relies on **tonal contrast and crisp 1px borders (`outline-variant`)** rather than drop shadows. Cards sit flat on the `#F5F7FA` canvas with `1px solid #E2E8F0` borders. Subtle ambient shadows (`0 4px 12px rgba(23, 43, 77, 0.08)`) are reserved exclusively for floating layers such as modals, drawers, tooltips, and dropdown menus. No glassmorphism or backdrop blur.

## Shapes

Corner radii are restrained and functional—never overly rounded or pill-heavy outside of status badges and avatars.

```yaml
rounded:
  sm: 6px
  DEFAULT: 8px
  md: 10px
  lg: 12px
  full: 9999px
```

## Motion & Micro-interaction

Motion is crisp and strictly functional, reinforcing state changes without delaying operators. No continuous decorative animations, and all motion honors `prefers-reduced-motion`.

```yaml
motion:
  state-change:
    duration: 140ms
    delay: 0ms
    timingFunction: ease-out
  surface-enter:
    duration: 200ms
    delay: 0ms
    timingFunction: cubic-bezier(0.2, 0, 0, 1)
  surface-exit:
    duration: 150ms
    delay: 0ms
    timingFunction: cubic-bezier(0.3, 0, 1, 1)
```

## Voice & Content Strategy

- **Tone:** Direct, factual, and operational. Citizen-facing copy is approachable and plain-spoken; operations copy is concise and action-oriented.
- **Capitalization:** Sentence case for page titles, section headings, table headers, and button labels (`Assign department`, `Create work order`, `Report an issue`).
- **Action Labels:** Use specific verb-object phrases (`Assign officer`, `Export report`, `Verify resolution`) rather than generic `Submit` or `OK`.
- **Numbers & Dates:** Use `tabular-nums` for all metrics, SLA timers, and dates (`Nov 20, 2026 · 09:42`).
- **States:** Empty states state what is missing and offer a single clear recovery action (e.g., `Clear filters`).

## Components

Component implementations live as individual HTML sticker sheet files in
`components/`. Each file contains the canonical, styled HTML components with
`<!-- COMPONENT: name -->` comment markers. Read each file before use.

- **Badge** → `@components/badge.html`: `badge-numeric`, `badge-dot`
- **Button** → `@components/button.html`: `button-primary`, `button-icon`, `button-with-icon`
- **Card** → `@components/card.html`: `card-elevated`, `card-action`, `card-interactive`, `card-interactive-2`
- **Table** → `@components/table.html`: `table-standard`, `table-interactive`, `table-selectable`
