+++
title = "The Policy That Passed Every Review and Failed on Reinvocation"
date = 2026-10-10
slug = "kubernetes-2026-reinvocation"
draft = false
+++

In July I wrote that the admission policies in [kubernetes-2026](https://github.com/bigelow/kubernetes-2026) were "verified against v1.36." That sentence was true and it was also too big. This is the follow-up it owes.

## What was claimed

The resource-defaults MutatingAdmissionPolicy injects CPU and memory requests and limits into containers that omit them. It went through five review passes, a documentation check, and a live session on `kindest/node:v1.36.1`: server-side dry-run, then real pods. Defaults landed on containers and initContainers; pre-set values were left alone. I wrote "verified" and pointed at the run.

## What the files did

The CEL expression mapped over `spec.containers` and, for a container that already had requests and limits, returned the container object itself. For one that didn't, it built a new object with just a name and resources. Both branches looked harmless. The second one was. The first one handed the API server an ApplyConfiguration containing whatever else the container carried, and an ApplyConfiguration may not touch atomic fields: `command`, `args`, `securityContext.capabilities.drop`. The test pods had none of those. The repo's own otel-collector and the DRA example pod had both.

Then there was `reinvocationPolicy: IfNeeded`, which I had set deliberately so a sidecar added by a later mutator would also get defaults. On the second pass the policy saw the container it had just defaulted, took the "already satisfied" branch, and returned it whole. So a container with no resources and a `command` was denied too. The failure surface wasn't "containers with atomic fields and resources." It was "any container with an atomic field, full stop," and the only pods that passed were the shaped-for-the-test ones.

## What the test caught, and when

The first half surfaced on July 3, two days after the post went up, bringing the stack up on local k3s v1.36.2: the collector pod was denied on restart. I fixed it with a kustomize patch in `local/` and left the reference manifest alone, with a comment that it was "worth upstreaming." That was a mistake with a note attached to it.

The second half surfaced on 2026-10-09, re-running the same live suite against `kindest/node:v1.37.0` for the version bump. A pod with `command` and no resources was rejected with `may not mutate atomic arrays, maps or structs: .spec.containers[0].command`. Switching the policy to `Never` made it pass, which named the cause without being the fix.

The fix, now on `main`, is the one the API was asking for all along: emit only the keys that are missing, guard every field with `has()`, and let a satisfied container produce nothing but its list-map key. `IfNeeded` stays. Thirteen focused cases and the full suite, now thirty-one, pass on v1.37.0, including the collector, the DRA example pod, and a container injected by a second policy. The local overlay patch is gone; the overlay applies the reference policy unmodified. The k3d stack itself has not been re-run on v1.37, and the repo says so.

## What I'd change in the sentence

"Verified against v1.36" named a version when it should have named a run. The run was real; its inputs were narrower than the claim. The CHANGELOG now records what each verification exercised, and the published post points at that instead of a version number. If a claim there still outruns the files, that's a bug; file an issue.

---

*Shannon Bigelow is an automation and platform engineer with 26 years in build/release, CI/CD, and developer productivity — Cisco/WebEx, Apple, and beyond.*
