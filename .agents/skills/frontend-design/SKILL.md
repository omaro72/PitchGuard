---
name: frontend-design
description: Design or refine PitchGuard frontend pages and React components with a distinctive, professional visual direction. Use for UI layout, styling, responsive behavior, accessibility, and frontend interaction work in this repository.
---

# PitchGuard frontend design

Create polished, working interfaces that suit a professional PR quality-review tool. Preserve the user's requirements and the existing product behavior.

## Project context

- Use the existing Next.js 16 App Router, React 19, TypeScript, and Tailwind CSS 4 setup.
- Follow the root `AGENTS.md` and `frontend/AGENTS.md` instructions.
- Read the relevant bundled Next.js documentation under `frontend/node_modules/next/dist/docs/` before relying on framework behavior.
- Reuse the existing application structure, components, styles, and API types.
- Do not add a UI, animation, icon, font, or state-management dependency unless the user explicitly requests it and the dependency is justified.
- Keep server and client component boundaries intentional. Add `"use client"` only when browser state, effects, or event handlers require it.
- Keep product decisions and final review outcomes in the backend. The frontend presents API results and must not calculate `PASS`, `REVISE`, or `BLOCK`.

## Design approach

Before editing, identify:

- The user's task and the workflow it supports.
- The intended audience and the information they need first.
- The existing visual language that should be preserved.
- One clear visual direction appropriate for a credible PR review product.

Prefer deliberate hierarchy and recognizable product character over decorative novelty. A memorable detail may come from typography, composition, color, or information presentation, but it must not reduce clarity or trust.

## Interface standards

- Use semantic HTML and visible, associated labels.
- Make all controls keyboard accessible and provide clear focus states.
- Maintain readable contrast and do not communicate status through color alone.
- Design responsive layouts from small screens through desktop widths.
- Include useful loading, empty, validation, partial-result, error, and disabled states when relevant.
- Keep user-entered content visible when results or errors appear unless the task requires otherwise.
- Use the existing Tailwind CSS 4 conventions and CSS custom properties for shared design tokens.
- Prefer CSS transitions and restrained micro-interactions. Respect reduced-motion preferences.
- Use typography that supports long-form reading and dense review findings. Avoid changing fonts merely to appear distinctive.
- Keep effects, backgrounds, borders, shadows, and spacing consistent with the chosen direction.
- Avoid generic dashboard decoration, purple-on-white gradients, excessive cards, unnecessary glass effects, and animation without a workflow purpose.

## Implementation workflow

1. Inspect the affected components, styles, tests, and API types.
2. Confirm the relevant Next.js 16 convention in the bundled documentation when framework behavior matters.
3. Implement the smallest cohesive design change that satisfies the request.
4. Preserve accessibility, responsive behavior, and all existing functional states.
5. Add or update focused Vitest and React Testing Library tests for changed behavior.
6. Run the relevant frontend checks: `npm run lint`, `npm run typecheck`, `npm test`, and `npm run build` when the task affects production output.

Do not redesign unrelated screens, introduce speculative product features, or replace working project conventions solely for aesthetic preference.
