# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Students and general readers learning about country development patterns are the primary audience, as confirmed by the user. `PROJECT_PLAN.md` also names researchers and policymakers as intended users.

## Product Purpose

Help users compare a selected country's development trajectory with two or three countries they choose, then inspect when and how the outcomes separate.

## Positioning

The explorer compares outcome trajectories for a focus country and two or three countries chosen directly by the user. It supports descriptive comparison, not causal explanation or prediction.

## Operating Context

Users select a focus country, two or three comparison countries, an indicator, outcome period, and data source. They inspect coverage, trajectories, relative gaps, and the annual comparison mean, then may export the comparison as CSV.

## Capabilities and Constraints

The Streamlit app defaults to a checksum-verified World Bank snapshot (or live API if no snapshot is available), with synthetic demo data available by explicit selection. It covers eight outcome indicators and a fixed 32-country selection universe. Data coverage varies. Comparisons are descriptive and do not establish causes or forecast outcomes.

## Brand Commitments

The product name is Development Divergence Explorer. The user supplied the Flim style reference as the visual direction for this interface: light graph-paper canvas, near-black type, tracked mono labels, loose polaroid-like surfaces, and restrained green, orange, and yellow accents.

## Evidence on Hand

Project capabilities, intended users, measures, data sources, limitations, and case-study prompts are documented in `PROJECT_PLAN.md`, `README.md`, and `CASE_STUDIES.md`. Demo values are synthetic; the app must label them as such. No customer endorsements or commercial claims are established.

## Product Principles

- Keep data source and coverage visible.
- Make the selected comparison group and its year-by-year coverage visible.
- Preserve the distinction between descriptive comparison and causal inference.
- Keep charts and controls easy to scan while retaining the full analysis workflow.
