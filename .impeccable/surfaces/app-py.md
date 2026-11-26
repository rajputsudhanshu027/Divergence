# Development Divergence Explorer — Full Dashboard

## Scope and mode

Full Streamlit dashboard redesign. Operate surface for students and general readers learning country development patterns.

## Task and constraints

Choose an outcome, country, period, and peer-matching settings; read the trajectory, peer-relative gap, coverage, and sensitivity; optionally export the data. Preserve all calculations, controls, sources, synthetic-data labeling, coverage details, limitations, and descriptive-only interpretation. Keep dense charts and tables readable at desktop and mobile widths.

## Direction contract

THESIS: Treat the dashboard as an open sketchpad where readers pin and compare development trajectories. Keep the whole analysis usable without turning it into a rigid tile grid.

OWN-WORLD: User-pinned Flim reference: #f5f5f5 graph-paper canvas, #141414 ink, white chart surfaces with 16px corners and #d9d9d9 hairlines, tracked mono labels, Arial body, oversized restrained display type, and tiny green, ember, and marker-yellow accents. No shadows.

STORY: The reader chooses an outcome and comparison frame, then moves from the country trajectory to relative gap, peers, coverage, and statistical caveats.

FIRST VIEWPORT: Full-width grid canvas. A ghost-label top rail sits over a split hero: “Divergence” at display scale on the left and the India comparison explanation right-aligned on the right. The comparison controls follow as one calm, pill-led working strip; the compact result readout precedes a large chart surface.

FORM: Flim’s analog creative-tool workspace, translated to real charts and data tables rather than decorative photography. The user supplied this direction and confirmed it should cover the full dashboard. Concept seed dd1015b2; the pinned direction governs the build.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Unresolved decisions

Use the named Google Fonts substitutes when available; retain the specified system fallbacks when offline.
