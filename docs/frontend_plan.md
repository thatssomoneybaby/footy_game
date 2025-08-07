# Front-end Plan (Next.js + Tailwind CSS)

## 0. Stack Choices
| Layer | Tech | Rationale |
|-------|------|-----------|
| Framework | **Next.js 14 (App Router)** | File-system routing, SSR for SEO, built-in API routes |
| Language | **TypeScript** | Type-safety, autocompletion |
| Styling | **Tailwind CSS** | Rapid utility-first styling, dark-mode toggle |
| State | **TanStack Query** | Caching & optimistic updates for REST calls |
| Icons | **Lucide** | MIT licence, SVGs |

## 1. Page Skeletons
- `/` – Landing & sign-in
- `/club-select` – grid of clubs
- `/dashboard` – calendar widget + quick stats
- `/roster` – sortable table, injury tooltips
- `/lineup` – drag-and-drop board (react-beautiful-dnd)
- `/match/[id]` – live sim view (virtualised log list)
- `/season-summary` – end-of-year screen

## 2. Global Layout
```tsx
<Sidebar>
  <NavLink href="/dashboard" />
  <NavLink href="/roster" />
  …
</Sidebar>
<MainArea>
  <TopBar clubLogo seasonRound finances />
  <Outlet /> {/* page content */}
</MainArea>
 
---

## 3. Component‑Level Breakdown

| Layer | Component | Purpose |
|-------|-----------|---------|
| **Atoms** | `Button`, `Badge`, `StatChip`, `ClubLogo`, `Avatar` | Re‑usable primitives with Tailwind utility classes only |
| **Molecules** | `PlayerRow`, `FixtureCard`, `SidebarNavLink` | Combine 2‑4 atoms; expose minimal props |
| **Organisms** | `RosterTable`, `Calendar`, `MatchFeed`, `DraftBoard` | Contain internal state & render lists/virtualised tables |
| **Templates** | `DashboardTemplate`, `MatchTemplate` | Lay out organisms into full pages |
| **Pages** | `dashboard/page.tsx`, `match/[id]/page.tsx` | Fetch data (via TanStack Query) and pass into templates |

> Follow Atomic Design; test organisms in isolation with Storybook snapshots.

---

## 4. Data‑Fetching & State Strategy

1. **React Query (TanStack)**  
   ```ts
   const { data, isLoading } = useQuery(['club', clubId], api.clubs.get);
   ```  
   - Global cache time: 10 min; stale time: 30 s during match view.  
   - Use **useMutation** for POST/PUT calls with optimistic updates.

2. **Global Context**  
   - `AuthProvider` stores JWT & refresh logic.  
   - `ClubProvider` caches selected club across pages.

3. **API client** (`src/lib/api.ts`)  
   ```ts
   export const api = {
     clubs: {
       get: (id) => fetchJSON(`/api/club/${id}`),
     },
     simulateRound: (sid, r) => fetchJSON(`/api/season/${sid}/round/${r}/simulate`, { method:'POST' }),
   };
   ```

---

## 5. Error, Loading & Empty States

| State | Pattern |
|-------|---------|
| **Loading** | Skeleton components + Tailwind `animate-pulse` |
| **404 / No Data** | Friendly illustration + “Go home” button |
| **Error (network/500)** | Toast via `sonner` + retry button; Sentry capture |

---

## 6. Accessibility & i18n

- Keyboard navigation order matches visual order; all `button` elements get `focus-visible:ring`.
- Colour palette passes WCAG AA (contrast ≥ 4.5:1).
- Use `aria-live="polite"` in **MatchFeed** so screen‑reader users hear play‑by‑play.
- Text content wrapped in `next-intl`; default locale `en-AU`.

---

## 7. Testing

| Level | Tool | Coverage Target |
|-------|------|-----------------|
| Unit | **Vitest + React Testing Library** | 80 % of atoms/molecules |
| Story snapshots | **Storybook** + **@storybook/testing-react** | All organisms render |
| E2E | **Playwright** | Happy‑path: login → simulate round |

CI step (GitHub Actions):
```yaml
- name: Test
  run: pnpm vitest run --coverage
- name: E2E
  run: pnpm playwright test
```

---

## 8. Performance & Deployment

- **Code‑splitting**: `match/[id]` page in its own chunk.
- Tailwind `@apply` for critical classes + purge CSS via `content` glob.
- Register PWA in `layout.tsx` (`next-pwa` plugin) – offline access for dashboard & roster.
- Deploy preview branches to **Vercel**; production auto‑prunes old functions.

---

## 9. Style Guide & Branding

- Tailwind config extends palette:  
  ```js
  theme: {
    colors: {
      club: {
        primary: 'var(--club-primary)',
        secondary: 'var(--club-secondary)',
      },
    },
  }
  ```
- CSS custom props (`--club-primary`) set at runtime via `<body style={…}>`.
- Breakpoints follow Tailwind defaults (`sm=640`, `md=768`, `lg=1024`, `xl=1280`).

---

## 10. Roadmap (Front‑end)

| Sprint | Goal |
|--------|------|
| 1 | Set up Next.js project, Tailwind config, AuthProvider |
| 2 | Implement Sidebar + Dashboard skeleton |
| 3 | Finish RosterTable & Calendar organisms |
| 4 | Live MatchFeed (virtualised list) + Optimistic update hooks |
| 5 | Responsive pass, accessibility audit, Storybook docs |