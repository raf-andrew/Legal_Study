# Dashboard Wireframes

This folder contains wireframes and resources for the Dashboard domain of the Legal Study System. All designs are browser-loadable HTML and structured for easy migration to and from Figma.

## Purpose
The dashboard is the central monitoring and control interface, providing real-time system status, metrics, quick actions, and recent activity.

## Key Features
- Real-time status overview
- Performance metrics visualization
- Quick action buttons
- System health indicators
- Recent activity log
- Notifications and alerts
- Responsive layout (desktop, tablet, mobile)

## Relevant Components
### Vue Components
- `StatusCard.vue` — System/service status display
- `ActivityFeed.vue` — Recent activity log
- `QuickActions.vue` — Frequently used actions
- `SystemMetrics.vue` — Performance and resource metrics
- `NotificationCenter.vue` — Alerts and notifications
- `DashboardLayout.vue` — Main dashboard layout

### Blade Views
- (Add any found in future profiling)

## Research & References
- `.planning/ui-ux/01-user-interface-specification.md`
- `.planning/ui-ux/02-component-wireframes.md`
- `.planning/ui-ux/03-feature-analysis.md`
- `.controls/ui/ui_ux_checklist.md`
- `.planning/ui-ux/design-patterns.md`

## Design Inspirations
- Laravel Horizon (real-time queue monitoring)
- Kubernetes Dashboard (resource/health visualization)
- PM2 (process monitoring)
- Best-in-class SaaS dashboards (e.g., Datadog, Grafana)

## Figma & HTML Workflow
- All wireframes are built in HTML/CSS for browser preview
- Variations for each component/screen are provided
- Shared resources (styles, icons, images) are in `.wireframe/resources/`
- To migrate to Figma: Export HTML/CSS assets or use Figma plugins for import
- To migrate from Figma: Place exported assets in `.wireframe/figma/dashboard/`

## Contents
- `index.html` — Main dashboard wireframe (with links to variations)
- `components/` — Standalone HTML/CSS for each dashboard component
- `README.md` — This file (domain summary and usage)

---

**Next steps:**
- Build out `index.html` and key component wireframes
- Document each variation and its intended use
- Update this README as new components/variations are added
