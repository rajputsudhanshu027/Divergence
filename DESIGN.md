---
name: Development Divergence Explorer
description: A sketchpad-like workspace for comparing country development paths.
colors:
  ink: "#141414"
  paper: "#ffffff"
  canvas: "#f5f5f5"
  mist: "#e9e9e9"
  hairline: "#d9d9d9"
  signal-green: "#30a81d"
  forest: "#21935b"
  highlight-yellow: "#fecc33"
  ember: "#ff8400"
  ink-hover: "#303030"
  control-wash: "rgba(255,255,255,.78)"
  chart-gap-wash: "rgba(48,168,29,.16)"
typography:
  display:
    fontFamily: "Schibsted Grotesk, Arial, sans-serif"
    fontSize: "clamp(4.5rem, 9vw, 7.8125rem)"
    fontWeight: 500
    lineHeight: 0.86
    letterSpacing: "-0.02em"
  heading:
    fontFamily: "Schibsted Grotesk, Arial, sans-serif"
    fontSize: "1.7rem"
    fontWeight: 500
    lineHeight: 1.1
  body:
    fontFamily: "Arial, Helvetica, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.4
  label:
    fontFamily: "IBM Plex Mono, ui-monospace, SFMono-Regular, Menlo, monospace"
    fontSize: "12px"
    fontWeight: 400
    lineHeight: 1.2
    letterSpacing: "0.06em"
rounded:
  button: "8px"
  card: "16px"
  pill: "160px"
  highlight: "25px"
components:
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
    typography: "{typography.label}"
    rounded: "{rounded.button}"
    padding: "0.65rem 1.15rem"
  filter-pill:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.pill}"
  chart-card:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.card}"
    padding: "0.5rem 0.55rem"
  control-surface:
    backgroundColor: "{colors.control-wash}"
    textColor: "{colors.ink}"
    rounded: "{rounded.card}"
    padding: "1.15rem 1.25rem 1rem"
---

# Design System: Development Divergence Explorer

## Overview

**Creative North Star: “Scattered Polaroids on a Sketchpad Grid.”**

The dashboard treats a country comparison as an object on a shared working surface. A quiet graph-paper canvas holds the controls, readouts, charts, and tables; the chart surfaces are rounded and hairline-bordered, like analysis cards placed on paper. Charts and data remain the main visual material, so the board supports exploration without decorative photography.

The interface carries the Flim reference into an analytical tool: near-black type, mono annotations, a large restrained display title, and small purposeful accents. It uses a continuous light canvas rather than alternating bands or a rigid dashboard tile grid. The comparison controls sit together, then the result moves from a wide trajectory to the relative gap and peer set. The explanatory caveats stay available beside the analysis.

**Key Characteristics:**
- A visible graph-paper canvas with a 36px grid.
- Large, mid-weight display type balanced by tracked mono labels.
- White chart and table surfaces with fine borders and rounded corners.
- Green, yellow, and ember accents reserved for data, highlights, and state.
- Flat construction; no drop shadows.

## Colors

The palette is almost entirely neutral; the accents mark selected series, a highlighted readout, or a sensitivity boundary.

### Primary
- **Signal Green:** The selected-country trajectory, relative-gap fill, and small status outlines.
- **Ember:** The candidate break marker in the relative-gap chart.
- **Marker Yellow:** The highlighted latest-gap readout and inline emphasis.

### Secondary
- **Forest:** A deeper green in the reference palette for quieter supporting accents; the current interface primarily uses Signal Green.

### Neutral
- **Ink:** Headings, labels, chart text, and the filled download action.
- **Paper:** Chart and table surfaces and the filled action's text.
- **Canvas:** Page ground and pill-shaped filter fields.
- **Mist:** Secondary background such as the sidebar.
- **Hairline:** Grid, card borders, and dividers.
- **Ink Hover:** The filled action's hover state.
- **Control Wash:** A translucent white filter surface.
- **Chart Gap Wash:** The translucent area under the relative-gap curve.

**The Signal Rule.** Green and ember identify information in the analysis; they do not become large decorative surfaces.

## Typography

**Display Font:** Schibsted Grotesk (with Arial fallback)
**Body Font:** Arial (with Helvetica fallback)
**Label/Mono Font:** IBM Plex Mono (with system monospace fallback)

**Character:** A shaped display voice gives the title its scale. Arial keeps longer explanations direct, while the mono face turns labels and metadata into compact annotations.

### Hierarchy
- **Display** (500, responsive 4.5rem–7.8125rem, 0.86 line-height, -0.02em tracking): The single-word hero title.
- **Headline** (500, 1.7rem): Section headings and comparison titles.
- **Title** (500, 1.3rem): Compact headings and control-group labels.
- **Body** (400, 15px, 1.4 line-height): Explanations and supporting notes.
- **Label** (400, 12px, 0.06em tracking, uppercase): Navigation context, field labels, and data annotations.

**The Three-Voice Rule.** Reserve the display face for hierarchy, Arial for reading, and mono for annotations.

## Layout

The canvas spans the available viewport. On desktop, the hero places the large title on the left and right-aligned explanatory copy on the right. The comparison settings form one grouped working strip below it. A four-part readout leads into a wide trajectory chart, followed by an asymmetric gap-chart and peer-table pairing. Content uses generous outer padding rather than a narrow centered page.

The grid repeats every 36px and stays faint under the content. At 900px, horizontal page padding tightens and the hero gap shrinks. At 700px, the hero stacks, its explanation becomes left-aligned, and the readout becomes two columns. Controls and analysis continue in document order.

## Elevation & Depth

The interface is flat. It uses no shadows. Separation comes from the canvas-to-paper shift, one-pixel hairlines, and the rounded chart surfaces. Keep controls, chart cards, and expanders on the same restrained depth system.

**The Paper Rule.** Never add a drop shadow; borders and surface contrast carry depth.

## Shapes

Three corner scales define the system: almost-square action buttons, rounded chart surfaces, and fully rounded filter fields. The yellow inline highlight uses a softer marker-like curve. Borders stay thin and neutral; green outlines are reserved for small status details.

## Components

### Navigation Context
- A slim two-sided row of uppercase mono labels, with a single hairline beneath it. It identifies the product and comparison source without presenting nonfunctional links.

### Filter Controls
- **Surface:** A translucent paper-white group with a hairline outline and rounded corners.
- **Fields:** Canvas-filled select and numeric fields use pill corners and a fine border. Widget labels use the tracked mono style.
- **Focus:** A visible green focus outline supports keyboard navigation.

### Primary Button
- **Shape:** Slightly rounded (8px).
- **Primary:** Ink fill, white text, tracked uppercase mono label.
- **Hover / Focus:** Darker ink on hover; green outline on keyboard focus.
- Used for the CSV download action.

### Chart and Table Surfaces
- **Corner Style:** Rounded (16px).
- **Background:** Paper white with a hairline border; no shadow.
- The selected-country line and gap fill use Signal Green. The peer mean uses Ink and a dashed line. Ember marks the candidate break date. Gridlines remain pale and subordinate.

### Result Readout
- Four label-and-value cells sit in one row, each introduced by a thin top rule. On narrow screens they form two columns. The latest relative gap receives the yellow marker treatment.

### Support Tag
- Outcome-only overlap and resampled stability use compact mono labels with a small green outline around each value.

### Alerts and Expanders
- White or translucent-white surfaces, fine borders, and rounded corners keep coverage notes, warnings, and statistical context in the same visual language as the main analysis.

## Do's and Don'ts

### Do:
- Keep the light grid visible as the dashboard's working surface.
- Use chart color consistently so selected-country and peer series remain distinguishable.
- Keep data provenance, coverage, and interpretation caveats easy to find.
- Let chart and table content serve as the dashboard's primary imagery.
- Preserve responsive reading order and keyboard-visible focus.

### Don't:
- Add drop shadows or gradients.
- Turn every section into a repeated, equal-size tile.
- Use accent colors as large background fills.
- Use decorative photography behind charts or controls.
- Hide the synthetic-data label or the descriptive-only caveat.
