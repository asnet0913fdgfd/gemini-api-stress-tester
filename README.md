# Gemini API Stress Tester

**Tools and scripts for stress testing Gemini APIs, measuring throughput, response quality, and failure behavior at scale.**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 📋 Overview

`gemini-api-stress-tester` is a high-performance asynchronous stress-testing tool specifically designed for **Google Gemini Flash Lite** (free tier). It floods the API with concurrent image-processing requests to:

- Measure real-world **throughput** (RPM, tokens/min)
- Track **latency** and **response quality**
- Identify **rate-limit behavior** and failure patterns
- Simulate heavy production load on the free tier

Perfect for developers, researchers, and teams who want to understand the practical limits of Gemini's free tier before building scalable applications.

---

## ✨ Features

- **Fully asynchronous** (asyncio + aiohttp) for maximum concurrency
- **Image-to-JSON extraction** workload (realistic multimodal test)
- Real-time colored console output with live RPM counter
- Automatic rate-limit detection (HTTP 429 handling)
- Detailed CSV logging of every request
- Built-in free-tier limit reference (15 RPM / 1M TPM / 1,500 RPD)
- Configurable duration, concurrency level, and delay
- Zero external dependencies beyond Python standard library + aiohttp

---

## 📁 Project Structure
