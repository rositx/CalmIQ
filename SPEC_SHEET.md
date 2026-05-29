# AI Guardrail Middleware — Product Specification Sheet

## What Is This?

AI Guardrail Middleware is a smart monitoring layer that sits between your customers and your AI support bot. It watches every conversation in real time, detects when a customer is becoming frustrated or stuck, and automatically escalates the situation to a human agent before the customer gives up and leaves.

It is not a chatbot. It is not a replacement for your AI. It is a safety net that makes your existing AI deployment significantly more reliable.

---

## The Problem It Solves

When companies deploy AI customer support bots, a predictable failure pattern emerges:

- The bot gets stuck in a loop, giving the same unhelpful answer repeatedly
- The customer becomes frustrated but has no easy way to reach a human
- The customer either abandons the conversation or leaves a negative review
- The company loses that customer — often permanently — without ever knowing why

This failure is silent. No alert fires. No agent knows. The customer just disappears.

---

## What It Does

The middleware intercepts every message exchanged between the customer and the AI bot. For each message, it calculates a real-time **Irritation Score** from 0 to 100 based on three things:

1. **What the customer is saying** — detecting negative language, aggressive tone, keywords like "cancel", "manager", "this is useless"
2. **How the customer is behaving** — rapid repeated messages, copy-pasting the same question, erratic typing patterns
3. **How the conversation is going** — whether the AI is giving the same response over and over, how long the conversation has been going without resolution

The moment this score crosses a safety threshold, the system executes a **circuit-breaker**:

- The AI bot is gracefully paused for that session
- A human agent is immediately notified and handed the live conversation
- An automatic compensation message (apology + discount/voucher) is sent to the customer to reduce churn in the gap before the agent connects

If no threshold is crossed, the middleware is completely invisible — it adds no friction and the conversation continues normally.

---

## Key Features

**Real-Time Irritation Scoring**
A continuously updated score that reflects the customer's emotional state across the entire session, not just the last message.

**Adaptive Escalation Thresholds**
The trigger point adapts based on customer value, history, and context. A high-value customer or one who has complained before gets escalated earlier. A brand-new customer gets a bit more patience.

**AI Loop Detection**
The system detects when the AI bot is stuck — repeating itself across multiple turns — and flags it as a strong escalation signal, independent of what the customer is saying.

**Hysteresis-Based Alerting**
Alerts don't fire on a single bad message and don't flicker on and off. The system requires sustained elevated scores before triggering, and only resets after a genuine period of calm. This prevents alert fatigue for your human agents.

**Automatic Retention Action**
When escalation triggers, a pre-configured compensation message (store credit, discount code, apology) is automatically sent to the customer. This bridges the gap before a human agent connects and reduces the chance the customer leaves during the handover.

**Coupon Fraud Prevention**
The compensation system includes a built-in fraud gate. The same customer cannot trigger automatic compensation repeatedly. Suspicious patterns are flagged for human review instead of being auto-approved.

**Human Agent Queue**
Escalated sessions are pushed into a live agent dashboard with full conversation context. Agents see the history, the current score, and the reason for escalation — no need to ask the customer to repeat themselves.

**Session Analytics**
Every session is logged with its full score history, escalation events, and resolution outcomes. This data feeds a business analytics dashboard for tracking trends, identifying AI failure patterns, and measuring intervention success rates.

---

## Who It Is For

Any company running a customer-facing AI support bot that cares about:

- Reducing customer churn caused by bad AI interactions
- Protecting their human agent team from being overwhelmed while still keeping them in the loop
- Having visibility into how their AI is actually performing in production
- Building trust with customers that a human is always reachable

---

## Key Advantages Over Alternatives

**Versus doing nothing:** Silent failures become visible. Customers who would have churned get retained.

**Versus always-on human support:** Human agents only handle the conversations that actually need them. The AI handles everything else, keeping costs low.

**Versus a simple "talk to human" button:** Customers often won't press a button when frustrated — they just leave. This system intervenes proactively, before the customer decides to go.

**Versus building this into the AI bot itself:** The middleware is AI-agnostic. It works with any bot, any LLM, any front-end. You don't need to modify your existing AI to use it.

---

## What Success Looks Like

- Reduction in conversation abandonment rate
- Reduction in negative reviews citing "couldn't reach a human"
- Faster average time-to-human-handover for genuinely stuck sessions
- Human agents spending their time on real escalations, not routine queries
- Business analytics showing which AI failure patterns are most common, enabling targeted improvements to the bot itself

---

## Current Scope (V1)

This version focuses entirely on **text-based chat** — web chat widgets, in-app messaging, and transcribed interactions. Voice/audio analysis is out of scope for V1. Behavioral telemetry (click patterns, typing velocity) is an optional enhancement; the core scoring works on text alone if telemetry is not available.
