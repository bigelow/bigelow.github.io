+++
title = "Test the Agent Like You Test the Code"
date = 2026-07-02
slug = "evals-as-ci"
+++

We would never merge code without tests. We merge agent behavior changes without them constantly.

A new skill, a reworked prompt, a different model version — each of these changes what an agent will do in production, and most teams ship them the way we shipped code in 1999: someone tried it, it seemed fine, it went out.

I want to make the case that evals belong in CI, and that this is not a research practice borrowed from ML teams. It is the same discipline we already apply to code, applied to the newest thing that behaves like code.

## The bug that made this concrete for me

While building a [Kubernetes reference architecture](https://github.com/bigelow/kubernetes-2026) with heavy AI assistance, I built a cross-checking workflow: split the repo into a JSON manifest of chunks, feed each chunk to a second and third model, and compare their claims against the actual source. It was tedious to set up and it caught real bugs — issues I had read past because the generated code looked idiomatic. The fixes landed squashed into the repo's [baseline commit](https://github.com/bigelow/kubernetes-2026/commit/1f51044da75b9f5d3a4199f9bc9811187f687f44), which is the honest limit of what I can show you: evidence the review happened, not an itemized list of what it caught. An earlier version of this post put a number on it; I couldn't evidence the count, so the count is gone.

The plainer checks earned their keep too. On the repo's first CI run, kubeconform flagged a DRA ResourceClaimTemplate with the wrong request shape — [here is the fix](https://github.com/bigelow/kubernetes-2026/commit/bbd2fb1708dae29adc1760f4e49c59aaa28bb875), if you want the receipt. Two different verifiers, same lesson: the generated output looked right, and a check that doesn't care how it looks caught it.

The pattern has repeated with each verification layer added since. Testing the admission policies against a real v1.36 API server surfaced a required `spec.reinvocationPolicy` field missing from both MutatingAdmissionPolicies — [static review could not have caught it](https://github.com/bigelow/kubernetes-2026/commit/b7a091354e2616ce7d96d433f02874b9b111e7a5), because the field only fails server-side. Static IaC scanning found a DRA inference-worker Pod with [no securityContext at all](https://github.com/bigelow/kubernetes-2026/commit/6e8c96ea897e6e8a7afaff0f0963ac7283079afb) — a workload prior sessions had missed, and I had too.

That workflow is an eval. It has inputs, expected properties, and a pass/fail signal. Once I saw it that way, the next step was obvious: it should not be something I run by hand when I remember to. It should run when the thing it checks changes.

## What an eval in CI actually looks like

In the triad I've written about before — context, harness, verification — this is verification engineering doing its most mechanical job. ([See: The Next Wave Isn't Autonomy. It's Verification.](https://bigelow.github.io/posts/verification-not-autonomy/))

Nothing exotic. A fixture of representative tasks. A defined set of properties the agent's output must hold — schema-valid manifests, no invented APIs, claims traceable to source. A runner that executes on every change to the prompt, skill, or model pin. A failure that blocks the merge, same as any other red build.

The hard part is not the pipeline. It is deciding what "correct" means for non-deterministic output, and being honest that some properties can only be checked statistically. That is uncomfortable for people who came up on deterministic tests. It was uncomfortable for me. But "we can only verify this to 95% confidence" is still infinitely better than "someone tried it and it seemed fine."

## Why this pays for itself

The ROI argument is the same one we made for CI twenty years ago, and it lands the same way: the cost of a behavior regression found in production is some multiple of the cost of finding it at merge time. If your team already tracks DORA metrics, agent-behavior regressions show up as change failure rate — you are likely already paying for the absence of evals; you are just booking it under a different line item.

## Where governance enters without a committee

There is a quieter benefit. An eval suite is a governance boundary you can read. "The agent is allowed to do X" stops being a policy document nobody checks and becomes a test that fails when violated. When someone asks how much the AI should really be in charge of, the eval suite is a concrete answer: this much — here is the fence, and here is the build that proves the fence holds.

## And when something gets through anyway

Something will get through anyway. When it does, the eval fixture is where the postmortem lands. Every incident caused by agent behavior should produce a new case in the suite, exactly the way a production bug produces a regression test. Teams that do this build an immune system. Teams that don't relive the same incident with different symptoms.

## Start smaller than feels serious

You do not need an eval platform. You need one fixture file, one property check, and one CI job that runs it. Mine started as a JSON manifest and a comparison script. It was finding real bugs before it had a name. If you want the runnable version, it lives at [bigelow/evals-in-ci](https://github.com/bigelow/evals-in-ci) — one fixture directory, two check files, one CI job, sixteen green checks.

Test the agent like you test the code. The rest follows.

---

*Updated July 10, 2026: the original version of this post claimed a specific bug count I couldn't trace to public evidence. I removed it; the examples that remain each link to their commit.*

