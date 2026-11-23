# AI Smart City design system

The live site uses the existing CivicOps reference palette: evergreen structure, terracotta actions, warm stone canvas, porcelain surfaces, and restrained semantic status colors. Tokens live together in `static/css/site.css` under `:root`; component rules consume the existing semantic aliases so a palette change stays centralized.

## Tokens

| Group | Tokens | Use |
| --- | --- | --- |
| Color | `--color-evergreen`, `--color-terracotta`, `--color-terracotta-soft`, `--color-ink`, `--color-muted`, `--color-canvas`, `--color-surface`, `--color-surface-low`, `--color-surface-mid`, `--color-line`, `--color-line-strong` | Brand, text, surfaces and boundaries |
| State | `--color-success`, `--color-success-soft`, `--color-warning`, `--color-warning-soft`, `--color-error`, `--color-error-soft` | Status badges and feedback; status text remains explicit |
| Type | `--type-body`, `--type-small`, `--type-label` | Body, secondary text and compact labels |
| Space | `--space-1`, `--space-2`, `--space-3`, `--space-4`, `--space-6`, `--space-8` | Quarter-rem spacing scale |
| Radius | `--radius-control`, `--radius-card`, `--radius-panel` | Inputs, cards and larger panels |

Typography uses the operating system stack (`system-ui`, `-apple-system`, `Segoe UI`) so there are no remote font requests or font licensing dependencies. Complaint identifiers use a local monospace stack. Icons are text or CSS marks; no icon runtime is loaded.

Bootstrap was not used by the live templates: their controls and layout use the project's own component classes. Its stylesheet was removed from `templates/base.html`; the repository's historical vendor files are retained but not loaded. Bootstrap-specific selectors were checked in the templates before removal.

Visual verification at 360, 768, and 1280 pixels is pending because Django and the container runtime are unavailable in the current workspace. The CSS source file is 14,782 bytes; there is no Bootstrap stylesheet transfer from the live base template.
