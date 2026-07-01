+++
title = "Kubernetes in 2026: What a Decade of Decisions Looks Like When You Verify Them"
date = 2026-07-01
slug = "kubernetes-2026"
+++

In 2016, The New Stack published an eBook called *Use Cases for Kubernetes*. I reread it recently. The core architecture it describes — API server, scheduler, controllers, etcd, pods reconciled toward desired state — is still accurate a decade later — an unusually long run for infrastructure software. Almost everything *around* that core has been replaced. The container runtime it assumed is gone. Most of the vendors in its solutions directory no longer exist. The limitations it warned about — no stateful workloads, no Windows support, no multi-tenancy — have been resolved, partially resolved, or quietly redefined.

That gap between a stable core and a churning ecosystem is the interesting part. So I built a reference architecture for running Kubernetes as it actually stands in mid-2026 (v1.36), documented every major decision as an ADR with its rationale, and — this is the part I want to talk about — verified the claims instead of just writing them down.

The repo is at [github.com/bigelow/kubernetes-2026](https://github.com/bigelow/kubernetes-2026). This post covers the decisions and what verifying them taught me.

## The decisions

Nine ADRs cover the choices that teams actually argue about in 2026. The short version:

**Container runtime: containerd.** This stopped being a decision years ago — dockershim was removed in v1.24 (April 2022) — but it's worth recording because the 2016 framing ("Docker or rkt") is how a decade of drift looks from the inside. Neither answer survived.

**Networking: Cilium, kept pluggable.** eBPF-based networking won on observability and policy expressiveness. The ADR keeps the CNI choice pluggable because this layer has churned once already and there's no reason to believe it's done.

**Ingress: Gateway API, and plan your migration.** Ingress NGINX was retired in March 2026 — no further releases, no security fixes. If you're still running it, the deprecation clock isn't ticking anymore; it rang. Gateway API is the replacement for new work, and the repo's traffic-management examples are Gateway API end to end, including the cross-namespace `allowedRoutes` wiring that's easy to get silently wrong (a route that doesn't attach produces no error — it just doesn't route).

**Admission policy: CEL, not webhooks.** This is the decision I'd call the biggest quality-of-life change in the platform. ValidatingAdmissionPolicy went GA in v1.30; MutatingAdmissionPolicy went GA in v1.36 (April 2026). Together they eliminate the webhook server for a large class of policy: no Deployment to run, no TLS certificates to rotate, no availability SPOF sitting in your admission path. The repo implements an image-registry allowlist and resource-defaults injection entirely in CEL, in-process in the API server.

**Stateful workloads: StatefulSets plus operators.** The 2016 eBook said running databases on Kubernetes was not recommended. In 2026 it's routine. The repo shows the StatefulSet shape an operator would manage, with the headless Service and security context that make it actually apply-able — and is honest that the operator itself is out of scope.

**Multi-tenancy: namespace-per-tenant by default, vCluster for the hard tier.** Still no first-class tenant concept in core Kubernetes, a limitation the 2016 book flagged that remains true a decade later. The namespace tier — ResourceQuota, NetworkPolicy covering both ingress and egress, RBAC — is implemented; the hard-isolation tier is documented as a decision, not pretended into existence.

**AI/GPU scheduling: Dynamic Resource Allocation.** DRA went GA in v1.34 and replaces the device plugin's integer-counting model with attribute-based, declarative device claims. This is the clearest example of Kubernetes growing a capability nobody in 2016 imagined needing: the platform is now the default substrate for AI workloads, and the scheduler grew up to match.

**Managed control planes by default; cost discipline as policy.** EKS/GKE/AKS unless compliance says otherwise, and requests/limits enforced at admission time rather than by wiki page.

## The part that mattered: verification

Every 2026-trends post makes claims like the ones above. What I tried to do differently is make the repo's claims either verified or honestly scoped — and the verification process turned out to be more instructive than the decisions themselves. Three findings stand out.

**Static review missed a required field that only a real API server could catch.** The MutatingAdmissionPolicy manifests looked correct to me, and to every review pass I ran over them — correct apiVersion, plausible CEL, valid YAML. Then I stood up a kind cluster on `kindest/node:v1.36.1` and ran `kubectl apply --dry-run=server`. Both policies failed: `spec.reinvocationPolicy: Required value`. The field became mandatory when the API graduated to v1, and no amount of reading catches a schema requirement that didn't exist in the beta everyone's mental model was trained on. Beyond dry-run, live behavioral tests confirmed the policies actually work: defaults injected on containers *and* initContainers that omit resources, pre-set values preserved, the cost-center label merged via server-side apply without clobbering existing labels, the registry allowlist denying and admitting correctly.

**A gate that has never run has caught nothing.** The repo's CI includes kubeconform for schema validation. I had configured it but never actually run it — every local check used the lighter Python validator I'd written instead. The first time kubeconform actually ran, on the first GitHub Actions run after the repo went public, it immediately failed the build: the DRA ResourceClaimTemplate used a pre-GA request shape (`deviceClassName` directly on the request) instead of the GA `exactly` block. I had run five review passes, a documentation-verification pass, and a live cluster session, and all of them missed it — including the cluster session, which exercised the admission policies but never this file. None of my checks ran that particular gate against that particular manifest. Each gate catches its own class of bug. A green pipeline you've never run is a rumor.

**Scanners are a second opinion, not a formality.** After hardening the Terraform (KMS envelope encryption for Secrets, IMDSv2 enforcement, IRSA foundation, endpoint access controls), I wired tflint and trivy into CI. Trivy promptly found a workload I had walked past in every prior hardening pass — an example Pod with no securityContext at all. The triage rule that keeps scanners honest: every finding is either fixed or suppressed with a written rationale in the repo. No blanket rule-disables. A suppression with a reason is a decision; a disabled rule is a blind spot with a green checkmark on it.

There's a small honesty discipline threaded through the repo: claims say what the files actually do. "Intended to inject" became "injects (verified against v1.36)" only after the live test. The image-registry policy's docs state plainly that ephemeral containers are injected via a subresource the policy doesn't match, so they are *not* gated at admission — CI catches them instead. The local observability stack (a runnable Grafana Alloy → Tempo/Loki/Prometheus pipeline with PII redaction, up with one `docker compose up`) documents that redaction covers traces and logs, because that's what the config does. Precision about scope is what makes the rest of a reference believable.

## What the decade actually changed

Rereading the 2016 eBook next to this repo, the pattern is clear: Kubernetes' core model was right, and everything replaceable got replaced. The runtime, the CNI, the ingress layer, the policy mechanism, the vendor ecosystem — all turned over, some of it twice. The limitations list became a changelog. And the scope quietly expanded from "container orchestrator" to the default substrate for AI infrastructure.

Which suggests the real skill in 2026 isn't knowing the current answers — those will churn again. It's keeping decisions documented with their rationale so they can be revisited honestly, and keeping claims verified so the reference stays a reference instead of drifting into fiction. That's what the repo tries to model, ADRs and CI gates included.

The whole thing is at [github.com/bigelow/kubernetes-2026](https://github.com/bigelow/kubernetes-2026) — MIT licensed, every suppression annotated, every "verified" claim traceable to the run that verified it. If you spot a claim the files don't support, that's a bug; file an issue.

---

*Shannon Bigelow is an automation and platform engineer with 26 years in build/release, CI/CD, and developer productivity — Cisco/WebEx, Apple, and beyond.*
