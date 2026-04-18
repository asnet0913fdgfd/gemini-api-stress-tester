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

gemini-api-stress-tester/
├── gemini_stress_test.py     # Main stress tester script
├── config.json               # API key configuration
├── README.md                 # This file
└── images/                   # ← Put your test images here
    ├── image1.jpg
    ├── image2.png
    └── ...
```

---

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/asnet0913fdgfd/gemini-api-stress-tester.git
cd gemini-api-stress-tester
```

### 2. Install dependencies
```bash
pip install aiohttp
```

### 3. Add test images
Create an `images/` folder and place any JPG/PNG/JPEG/GIF/WEBP images inside. These will be used for OCR-style extraction testing.

### 4. Configure API key
Edit `config.json`:
```json
{
  "apiKey": "your_gemini_api_key_here"
}
```

> **Security note**: Never commit your real API key. Consider using environment variables in production.

---

## 📖 Usage

```bash
python gemini_stress_test.py
```

### Command-line options (planned / upcoming)
```bash
python gemini_stress_test.py --duration 15 --concurrent 8 --delay 1
```

**Default settings** (from script):
- Duration: 10 minutes
- Max concurrent requests: 5
- Delay between requests: 2 seconds
- Target model: `gemini-flash-lite-latest`

---

## 📊 What Gets Measured

| Metric              | Description                          |
|---------------------|--------------------------------------|
| **Total Requests**  | Total API calls made                 |
| **Success Rate**    | Successful responses                 |
| **Rate Limited**    | HTTP 429 responses                   |
| **Failures**        | Other errors / exceptions            |
| **Avg Latency**     | Average response time (ms)           |
| **Throughput**      | Requests per minute (live RPM)       |
| **Token Usage**     | Total tokens consumed                |
| **Image Size**      | KB size of each processed image      |

Results are saved to `stress_test_results_YYYYMMDD_HHMMSS.csv`

---

## 🛡️ Free Tier Limits (Gemini Flash Lite)

| Limit          | Value          |
|----------------|----------------|
| Requests/min   | 15 RPM         |
| Tokens/min     | 1,000,000 TPM  |
| Requests/day   | 1,500 RPD      |

The tester automatically tracks your current RPM and warns you when approaching limits.

---

## 🔧 Configuration (`config.json`)

| Key       | Description                  |
|-----------|------------------------------|
| `apiKey`  | Your Gemini API key (required) |

---

## 📝 Example Output

```
=======================================================================
GEMINI FLASH LITE STRESS TEST
=======================================================================
Model: gemini-flash-lite-latest
Duration: 10 minutes
Max Concurrent: 5
Delay between requests: 2s
Target RPM: 30.0 (Free tier limit: 15)

Found 12 images for testing
Starting test...

[14:22:05] REQ #0001 | success        | 2458ms | RPM:3  | receipt.jpg
[14:22:07] REQ #0002 | success        | 1892ms | RPM:5  | invoice.png
[14:22:09] REQ #0003 | rate_limited   | 312ms  | RPM:7  | menu.webp
...
```

---

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Add support for other Gemini models
- Implement `argparse` CLI options
- Add HTML/PDF report generation
- Improve error recovery and retry logic

1. Fork the repo
2. Create a feature branch
3. Submit a PR

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

**Made with ❤️ for the AI developer community**

