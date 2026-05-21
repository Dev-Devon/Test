# Eleuther Browser

⚠️ **Note:** This project is not intended as a full-featured daily driver browser.  
It is a security-focused experimental wrapper around QtWebEngine.

GitHub: https://github.com/Dev-Devon/Eleuther

---

## Overview

Eleuther is a prototype browser security monitor built on top of QtWebEngine.

Instead of trusting all web content by default, it introduces a policy-based interception layer that evaluates network requests before they are executed.

The goal is to explore stricter control over web execution behavior, especially around third-party scripts and telemetry endpoints.

---

## Core Design

### 1. Request Interception Layer
Every outgoing request is processed through a `PolicyEngine` that returns a structured decision:

- `ALLOW`
- `BLOCK`

Each decision includes:
- Action
- Confidence score
- Reason for decision

This allows inspection and debugging of why specific requests are blocked.

---

### 2. Domain Filtering
The system maintains two primary domain categories:

- **Blocked domains:** commonly used ad and tracking networks
- **Telemetry-scoped domains:** domains where additional path-level filtering is applied

Requests are evaluated using both hostname and path-level matching.

---

### 3. Path-Level Filtering
Certain request patterns are blocked when detected on sensitive domains:

- tracking endpoints
- analytics beacons
- pixel-based telemetry routes

This is applied only to specific resource types (e.g., XHR, Script, Fetch).

---

### 4. DOM Sanitization Layer
A lightweight JavaScript injection runs after page load to remove known advertisement-related elements.

It uses:
- attribute-based selectors (`[is-promoted]`)
- class-based selectors (YouTube UI ad containers)
- iframe filtering for known ad sources

It is triggered on mutation events rather than polling intervals to reduce CPU overhead.

---

## Current Capabilities

- Request interception with policy-based evaluation
- Domain and path-level blocking
- Lightweight DOM cleanup injection
- Basic tabbed browsing via QtWebEngine
- Persistent profile storage (non-incognito mode)

---

## Limitations

- Performance overhead due to Python + QtWebEngine integration layer
- Aggressive filtering may break authentication flows or third-party widgets
- DOM sanitization depends on stability of external platform markup (e.g., YouTube structure)
- No adaptive learning or heuristic model currently implemented

---

## Potential Improvements

### Native Performance Layer
Porting the network filtering logic to a native extension (Rust or C++) would reduce latency and improve scalability under heavy request loads.

### Heuristic Filtering
Current filtering is rule-based. A future version could incorporate:
- anomaly detection for request patterns
- adaptive classification of telemetry endpoints

### DOM Resilience
The DOM cleaning system is brittle by design and depends on static selectors. A more robust approach would require:
- structure-aware heuristics
- mutation diff classification
- or integration with browser-level APIs

---

## Contribution Areas

Help is needed in the following areas:

- Rust/C++ developers for native network filtering module
- Web security researchers for improving heuristic accuracy
- Frontend engineers for improving DOM sanitization resilience
- Performance optimization of QtWebEngine integration layer

---

## Disclaimer

This project is experimental.

It is not a replacement for a production browser and may break websites due to its restrictive filtering behavior.

---
