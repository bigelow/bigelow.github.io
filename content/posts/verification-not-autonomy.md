+++
title = "The Next Wave Isn't Autonomy. It's Verification."
date = 2026-07-02
slug = "verification-not-autonomy"
+++

Every wave of operations tooling has followed the same pattern: take something humans did imperatively, make it declarative, and hand it to a control loop that reconciles reality to the declaration.

CI/CD did this for releases. Config management did it for server state. IaC did it for infrastructure. Kubernetes made the reconciliation loop itself a platform primitive: desired state, controller, observed state, diff, convergence.

That pattern worked because the declaration was reviewable. A Terraform plan can be inspected before apply. A Kubernetes manifest can be reviewed before a controller acts on it. A CI pipeline can show the commit, the tests, the artifact, and the deployment target. The system still had moving parts and still failed in familiar ways, but there was usually an object a human could inspect before the system changed reality.

That property matters more than the automation. It is also the property agents break.

## The differ became a planner

An intent like "keep p99 latency under 200ms" is not a desired state in the same sense as a Kubernetes manifest. It is a goal. A system trying to satisfy that goal may need to inspect traces, compare deploys, check saturation, read recent incidents, decide whether the last release is suspicious, adjust capacity, change traffic policy, open a pull request, roll something back, or do nothing. There may be more than one valid path. Some paths may be safe, some may be expensive, and some may be technically correct and still operationally wrong.

You no longer have a differ.

You have a planner.

That is the important break. The previous model gave us plan, diff, apply, and reconcile. Agentic systems add reasoning and tool use between the declaration and the action, and that middle section is where most of the risk moves.

This is why I do not find "autonomous ops" very useful as the pitch. It skips the part I would need before trusting the system: what the agent saw, what it ignored, what it assumed, which tools it used, which policies constrained it, what alternatives it considered, what evidence supported the proposed action, and what would make the action reversible. Without that, autonomy is just an opaque control loop with production credentials.

## AIOps already taught part of this lesson

None of this is entirely new. AIOps made similar promises years ago: detect incidents, identify causes, recommend remediations, and eventually close the loop. Some of that work was useful, and a lot of the autonomy story got ahead of the reliability story.

LLM agents are more capable than the older systems, and that matters. They can read more context, use more tools, and handle fuzzier tasks. But capability does not remove the trust problem. In some cases it makes the trust problem sharper, because the system can now produce plausible plans across more of the stack.

A weak system fails obviously. A capable system can be wrong in ways that look reasonable.

I ran into this directly while building a [Kubernetes reference architecture](https://github.com/bigelow/kubernetes-2026) with heavy AI assistance. The generated manifests looked right. They were well-structured, idiomatic, and consistent with the surrounding code. On the very first CI run, kubeconform flagged a DRA ResourceClaimTemplate using the wrong request shape for the GA `resource.k8s.io/v1` API — a mistake I would not have caught reading the diff, because the diff read as plausible. ([Here is the fix](https://github.com/bigelow/kubernetes-2026/commit/bbd2fb1708dae29adc1760f4e49c59aaa28bb875).) The machine-generated change was wrong in a way that looked reasonable, and a boring verification step caught it. That single catch crystallized everything below.

## The missing primitive is reviewability

When I say verification, I do not mean a single test result. I mean the ability to inspect and bound the work.

Can I see the agent's inputs?
Can I see which context was used?
Can I see which policy allowed the tool call?
Can I replay the decision path?
Can I compare the proposed action to known-good patterns?
Can I require approval when the blast radius crosses a threshold?
Can I attach evidence to the action so someone can understand it later?

That is closer to what made previous waves usable. CI/CD needed tests that people trusted. IaC needed drift detection and policy checks. Kubernetes needed observability because reconciliation without visibility is not enough. Agentic operations need verification for the same reason: the work needs an evidence trail.

Not because evidence makes the system perfect. It does not. Evidence makes the system inspectable. It gives humans and other systems something to challenge.

## Agentic delivery pipelines expose the gap

This shows up quickly in software delivery. A coding agent can read a ticket, inspect a repository, edit code, update Terraform, write tests, open a pull request, respond to comments, and prepare release notes. That is not just assisted coding anymore. It is a delivery pipeline.

Most teams are not treating it that way yet. They are adding prompts, skills, MCP servers, sandboxes, and tool permissions. Those are necessary pieces, but they are not the whole system. The missing object is the record of work: the intent that started the action, the context it drew on, the tools it called and the policies that allowed each call, what changed, what evidence says the change is safe, what still requires human review, and what rollback would mean.

Without that record, the organization has action without enough inspection. That may be fine for low-risk work. It is not enough for production systems, regulated environments, or infrastructure changes with real blast radius.

## Skills have the same problem

Skills have a quieter version of the same issue. A skill is often described like a prompt, but operationally it can behave more like code. It can change how an agent plans, what context it retrieves, which tools it chooses, when it escalates, and how it interprets a request.

That means skill changes deserve the same basic scrutiny we apply to other executable logic: what changed between versions, what behavior the skill permits, what tool access it assumes, what tests prove it still behaves as expected, how it interacts with other skills, and what the rollback path is. If I install a few thousand lines of agent instruction and cannot answer those questions, I have added operational logic I cannot review.

Calling it a skill does not make it safer.

## The triad I keep coming back to

I find it useful to split the work into three parts.

Context engineering is what the agent is allowed to know: prompts, memory, retrieval, documentation, tickets, incidents, traces, logs, policies, and prior decisions.

Harness engineering is what the agent is allowed to touch: tools, APIs, sandboxes, MCP servers, execution loops, approval gates, and runtime constraints.

Verification engineering is what the organization is allowed to trust: evals, tests, policies, dry runs, audit trails, replay, blast-radius checks, and evidence attached to each action.

The first two are getting most of the attention, and that makes sense — agents need context and tools before they can do useful work. But the third part decides where the system can be used safely. A local agent suggesting a refactor has one trust boundary. An agent changing infrastructure, modifying deployment policy, or remediating an incident has another. The verification layer is what should make that distinction explicit.

## Simplicity becomes a safety property

This is where the old engineering advice comes back with more force. Simple systems are easier for humans to understand. They are also easier for agents to model and easier for verification systems to check.

That does not mean small systems are automatically safe. It means legibility matters. An agent cannot safely operate a system it cannot model. A reviewer cannot approve a plan they cannot understand. A policy engine cannot enforce boundaries that were never made explicit.

For teams that already value simplicity, this is not aesthetic preference anymore. It changes the work. The valuable artifact is not just the glue code. The valuable artifacts are the specification, the contract, the policy, the eval, the test, the action record, and the rollback path. Glue code still exists. It just stops being the only thing that matters.

## What I would want before closing the loop

Before I let an agent take higher-risk action, I would want a record of the work — a structured object, not a log line.

It would carry the intent that started the run, in plain language. It would name the actor and enumerate the context actually used: the incident, the recent deploys, the trace queries, the SLO. It would state the proposed action and the specific tool call behind it, along with the policy decision that governed it — including, when appropriate, "requires human review." It would summarize the change in a sentence a reviewer can evaluate. And it would attach evidence: test results, a risk assessment, the blast radius, and what rollback would actually mean.

The exact shape matters less than the habit it enforces: agent work should leave behind evidence that can be inspected, challenged, replayed, and used to improve the next run.

That is the part I want more tooling around. Not more vague autonomy. Not more demos where the happy path works once. More boring records. More dry runs. More policy decisions attached to tool calls. More evidence connected to outcomes.

## Where I think this goes

I do not think the next useful step is a fully autonomous operations platform. That may come in narrow domains first — where the environment is constrained, the actions are reversible, the cost of error is low, and the verification loop is strong.

For most production engineering work, the next useful step is more modest and more important: make agent work reviewable. Make it clear what the agent knew, what it did, why it did it, what checked it, and what happened afterward. That is enough to change the shape of the work.

Autonomy can wait behind that.

Verification cannot.
