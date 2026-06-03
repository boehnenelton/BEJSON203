# Perceptual Analysis Report: HTML3 CSS Standard Gap Audit

## 1. Atomic Observations
- **Standard Domain (BECSS)**: Defined in `docs/css/becss-core.css`. Attributes: `c-` prefixes for components, `u-` for utilities, `OKLCH` color space, `@layer` architecture (reset, base, layout, components).
- **Legacy Domain (Merged Libs)**: Found in `lib_html3_*.py`. Attributes: Flat class names (`.card`, `.top-bar`), hex/variable-based colors (`#DE2626`, `var(--primary)`), heavy reliance on inline `style` attributes within Python strings.
- **BEM Implementation**: Standard mandates `block__element--modifier` with `c-` block prefix. Merged libs use partial BEM (e.g., `.card__title`) but omit the mandatory component namespace prefix.

## 2. Local Patterns
- **Styling Drift**: The library generates components with ad-hoc margins, padding, and borders hardcoded in Python, bypassing the "Atomic Design" principles established in the standard.
- **Color Inconsistency**: `BRUTAL_COLOR` uses hex codes, while BECSS mandates OKLCH (e.g., `oklch(65% 0.2 25)`).

## 3. Structural Relationships
- **Hierarchy**: `lib_bejson_html3_skeletons.py` is the foundational root for layout, but it currently lacks the `@layer` structure and BECSS variable naming (e.g., uses `--font-base` vs `--font-sans`).
- **Signal Pathways**: Component logic in `lib_html3_body.py` is decoupled from the CSS standard, leading to "Shim" behavior where Python handles visual state that should be delegated to CSS Modifiers.

## 4. System-Level Behaviors
- **State**: The system is currently in a "Hybrid-Legacy" state. It has the correct filenames (HTML3) but the underlying behavioral engine is HTML2.
- **Control**: Control is currently Python-dominant (imperative styling) rather than CSS-dominant (declarative BEM classes).

## 5. Emergent Properties
- **Technical Debt Accumulation**: Continued use of inline styles makes theme swapping (e.g., Brutal vs standard) brittle and dependent on string manipulation rather than CSS class toggling.

## 6. Probable Intent
- The user's intent is a rigorous migration to a "Scalable, Maintainable, and Modular" architecture using BEM and modern CSS standards (OKLCH, Layers).

## 7. Confidence Estimates
- **Standards Match**: 95% confidence in identified gap (BEM prefix + OKLCH + Layers).
- **Legacy Persistence**: 100% confidence that merged components currently violate these standards.

## 8. Unresolved Ambiguities
- The exact role of the `b-` prefix (found in `lib_html3_body.py`) is unclear—it appears to be a half-baked shorthand for "Brutal" or "Block" that violates the `c-` standard.

## 9. Alternative Interpretations
- None viable; the user's corrective prompt explicitly confirms the requirement for HTML3 BEM standards.

## 10. Final Conceptual Awareness Model
The HTML3 library is currently a **Nominal Shell**. To achieve **Architectural Integrity**, Phase 4 must shift from "Fixing Bugs" to "Reconstructing the Component Engine". This requires:
1. **Namespace Normalization**: Prepend `c-` to all component blocks.
2. **Token Migration**: Replace hex values with OKLCH tokens.
3. **Architecture Shift**: Move all component styling from Python strings to `lib_bejson_html3_component_css.py` using `@layer components`.

---
*Relational ID: pd-html3-css-audit-001*
