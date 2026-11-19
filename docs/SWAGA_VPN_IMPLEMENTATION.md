# Swaga VPN implementation plan

## Product requirements

- VPN traffic is scoped to the SwagaBrowser Android package only.
- Supported provider choices: Windscribe and Proton VPN.
- Switching providers always requires an explicit confirmation.
- The browser must clearly show disconnected, connecting, connected, and error states.
- A tunnel failure must never be presented as protected browsing. No silent fallback is allowed.
- Keep GeckoView and the existing low-memory UI optimizations unchanged.

## Architecture

1. **SwagaVpnController**: owns the VPN state machine and serializes connect, disconnect, and provider-switch operations.
2. **Android VpnService adapter**: requests Android's VPN consent and creates a per-app VPN using an allow-list containing only `app.swaga.browser`.
3. **Tunnel engine interface**: provider-neutral boundary for establishing and closing a tunnel. It must not claim connectivity until the tunnel is actually established.
4. **Windscribe adapter** and **Proton adapter**: separate provider integrations. Each adapter may only use a documented SDK/API or provider-issued configuration and credentials.
5. **Status UI**: reports the actual tunnel state, selected provider, and last connection error.

## Provider integration gate

An Android `VpnService` can provide per-app routing, but it does not grant access to Windscribe or Proton accounts. Embedded official account sign-in is not assumed. Before implementing either provider adapter, confirm a supported integration method and applicable redistribution/licensing terms with that provider. Do not scrape private endpoints, reverse-engineer authentication, reuse app-private tokens, or embed provider credentials.

## Switch sequence

1. Ask the user to confirm the provider change.
2. Stop the current tunnel.
3. Start the selected provider through its approved integration.
4. Mark the connection as protected only after successful tunnel establishment.
5. If startup fails, show an error and remain disconnected. Never silently switch to ordinary networking while displaying a VPN-connected state.

## Acceptance checks

- Only the SwagaBrowser package is routed through the VPN.
- Other applications retain their normal network route.
- Android VPN consent is requested through the platform.
- Provider changes cannot occur without confirmation.
- Disconnect, process recreation, denied consent, and tunnel failure are represented accurately.
- GeckoView remains the browser engine.
- No provider-specific login or tunnel implementation is shipped until its supported integration path is verified.
