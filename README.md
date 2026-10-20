# Agent Platform

Reusable control plane for distributed automation and AI agents. Applications such as PhD Scout are independent clients, not dependencies.

**Status:** Repository initialized. The foundation implementation is proposed via pull request; do not deploy `main` until the PR has been reviewed and merged.

Architecture: Acer Nitro (always-on control plane) + optional RTX 4070 and other workers. Small local models support optional tool routing; reliable scheduling, persistence and safety controls are deterministic.

Never commit credentials, user data, `.env`, or `slack.env`. Public repository: review every diff before merging.
