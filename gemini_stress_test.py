#!/usr/bin/env python3
"""
Gemini Flash Lite Stress Tester
Tests free tier limits with image processing
"""

import asyncio
import aiohttp
import base64
import csv
import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from collections import deque
import sys

# Configuration
API_KEY = ""  # Will be set from argument or input
MODEL_ID = "gemini-flash-lite-latest"
API_ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_ID}:generateContent"
IMAGE_FOLDER = Path("./images")

# Free tier limits for reference
FREE_TIER_LIMITS = {
    "rpm": 15,           # Requests per minute
    "tpm": 1_000_000,    # Tokens per minute
    "rpd": 1_500,        # Requests per day
}

class StressTester:
    def __init__(self, api_key, duration_minutes=10, max_concurrent=5, delay_seconds=2):
        self.api_key = api_key
        self.duration = timedelta(minutes=duration_minutes)
        self.max_concurrent = max_concurrent
        self.delay = delay_seconds

        self.results = []
        self.stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "rate_limited": 0,
            "total_tokens": 0,
            "start_time": None,
            "end_time": None
        }

        # Rate limiting tracking
        self.request_times = deque()  # Track request timestamps for RPM calculation
        self.tokens_used = deque()    # Track token usage timestamps

    def get_mime_type(self, filepath):
        """Determine MIME type from file extension"""
        ext = Path(filepath).suffix.lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.bmp': 'image/bmp'
        }
        return mime_types.get(ext, 'image/jpeg')

    def encode_image(self, filepath):
        """Convert image to base64"""
        with open(filepath, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')

    def calculate_current_rpm(self):
        """Calculate current requests per minute"""
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)

        # Remove old entries
        while self.request_times and self.request_times[0] < minute_ago:
            self.request_times.popleft()

        return len(self.request_times)

    async def send_request(self, session, image_path, request_id):
        """Send a single request to Gemini API"""
        start_time = time.time()
        file_size = os.path.getsize(image_path) / 1024  # KB

        try:
            # Prepare image
            image_data = self.encode_image(image_path)
            mime_type = self.get_mime_type(image_path)

            payload = {
                "contents": [{
                    "parts": [
                        {"text": "Extract all text and data from this image. Provide structured JSON output."},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": image_data
                            }
                        }
                    ]
                }],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 2048
                }
            }

            url = f"{API_ENDPOINT}?key={self.api_key}"

            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=120)) as response:
                elapsed = (time.time() - start_time) * 1000  # ms

                if response.status == 200:
                    data = await response.json()

                    # Extract token usage
                    tokens = data.get("usageMetadata", {}).get("totalTokenCount", 0)

                    # Get response text snippet
                    try:
                        text = data["candidates"][0]["content"]["parts"][0]["text"][:100]
                    except (KeyError, IndexError):
                        text = "No text extracted"

                    result = {
                        "request_id": request_id,
                        "timestamp": datetime.now().strftime("%H:%M:%S"),
                        "image": Path(image_path).name,
                        "size_kb": round(file_size, 2),
                        "status": "success",
                        "duration_ms": round(elapsed, 2),
                        "tokens": tokens,
                        "error": "",
                        "snippet": text.replace("\n", " ")
                    }

                    self.stats["success"] += 1
                    self.stats["total_tokens"] += tokens
                    self.tokens_used.append((datetime.now(), tokens))
                    color = "\033[92m"  # Green

                elif response.status == 429:
                    self.stats["rate_limited"] += 1
                    error_text = await response.text()
                    result = {
                        "request_id": request_id,
                        "timestamp": datetime.now().strftime("%H:%M:%S"),
                        "image": Path(image_path).name,
                        "size_kb": round(file_size, 2),
                        "status": "rate_limited",
                        "duration_ms": round(elapsed, 2),
                        "tokens": 0,
                        "error": f"HTTP 429: Rate limit exceeded",
                        "snippet": ""
                    }
                    color = "\033[93m"  # Yellow

                else:
                    error_text = await response.text()
                    result = {
                        "request_id": request_id,
                        "timestamp": datetime.now().strftime("%H:%M:%S"),
                        "image": Path(image_path).name,
                        "size_kb": round(file_size, 2),
                        "status": f"error_{response.status}",
                        "duration_ms": round(elapsed, 2),
                        "tokens": 0,
                        "error": f"HTTP {response.status}: {error_text[:100]}",
                        "snippet": ""
                    }
                    self.stats["failed"] += 1
                    color = "\033[91m"  # Red

        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            result = {
                "request_id": request_id,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "image": Path(image_path).name,
                "size_kb": round(file_size, 2),
                "status": "exception",
                "duration_ms": round(elapsed, 2),
                "tokens": 0,
                "error": str(e)[:100],
                "snippet": ""
            }
            self.stats["failed"] += 1
            color = "\033[91m"  # Red

        self.results.append(result)
        self.request_times.append(datetime.now())
        self.stats["total"] += 1

        # Print status
        reset = "\033[0m"
        rpm = self.calculate_current_rpm()
        print(f"{color}[{result['timestamp']}] REQ #{request_id:<4} | {result['status']:<15} | {result['duration_ms']:<6}ms | RPM:{rpm:<3} | {result['image']}{reset}")

        return result

    async def run_test(self):
        """Main test execution"""
        print("\n" + "="*70)
        print("GEMINI FLASH LITE STRESS TEST")
        print("="*70)
        print(f"Model: {MODEL_ID}")
        print(f"Duration: {self.duration.total_seconds()/60} minutes")
        print(f"Max Concurrent: {self.max_concurrent}")
        print(f"Delay between requests: {self.delay}s")
        print(f"Target RPM: {60/self.delay:.1f} (Free tier limit: {FREE_TIER_LIMITS['rpm']})")
        print("="*70 + "\n")

        # Validate images
        if not IMAGE_FOLDER.exists():
            print(f"ERROR: Folder {IMAGE_FOLDER} not found!")
            return

        images = list(IMAGE_FOLDER.glob("*.jpg")) + list(IMAGE_FOLDER.glob("*.png")) + \
                 list(IMAGE_FOLDER.glob("*.jpeg")) + list(IMAGE_FOLDER.glob("*.gif")) + \
                 list(IMAGE_FOLDER.glob("*.webp"))

        if not images:
            print(f"ERROR: No images found in {IMAGE_FOLDER}!")
            return

        print(f"Found {len(images)} images for testing")
        print("Starting test... Press Ctrl+C to stop\n")

        self.stats["start_time"] = datetime.now()
        end_time = self.stats["start_time"] + self.duration
        request_id = 0

        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async with aiohttp.ClientSession() as session:
            tasks = []

            try:
                while datetime.now() < end_time:
                    # Pick random image
                    img = images[request_id % len(images)]

                    # Control concurrency
                    async with semaphore:
                        task = asyncio.create_task(self.send_request(session, str(img), request_id))
                        tasks.append(task)

                        # Show stats every 5 requests
                        if request_id % 5 == 4:
                            await asyncio.sleep(0.1)  # Allow prints to flush
                            rpm = self.calculate_current_rpm()
                            success_rate = (self.stats["success"] / max(1, self.stats["total"])) * 100
                            print(f"\033[96m--- Stats: Total:{self.stats['total']} | Success:{self.stats['success']} | RateLimits:{self.stats['rate_limited']} | RPM:{rpm} ---\033[0m")

                        request_id += 1

                        # Delay to control rate
                        await asyncio.sleep(self.delay)

            except KeyboardInterrupt:
                print("\n\nTest interrupted by user...")

            # Wait for pending tasks
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

        self.stats["end_time"] = datetime.now()
        await self.generate_report()

    async def generate_report(self):
        """Generate CSV and summary report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_file = f"stress_test_{timestamp}.csv"
        txt_file = f"stress_test_{timestamp}.txt"

        # Write CSV
        if self.results:
            keys = self.results[0].keys()
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                writer.writerows(self.results)

        # Calculate statistics
        duration = self.stats["end_time"] - self.stats["start_time"]
        total_minutes = duration.total_seconds() / 60
        avg_rpm = self.stats["total"] / max(1, total_minutes)

        # Group by status
        status_counts = {}
        for r in self.results:
            status_counts[r["status"]] = status_counts.get(r["status"], 0) + 1

        # Size analysis
        size_groups = {"Small(<100KB)": [], "Medium(100-500KB)": [], "Large(>500KB)": []}
        for r in self.results:
            if r["status"] == "success":
                size = r["size_kb"]
                if size < 100:
                    size_groups["Small(<100KB)"].append(r["duration_ms"])
                elif size < 500:
                    size_groups["Medium(100-500KB)"].append(r["duration_ms"])
                else:
                    size_groups["Large(>500KB)"].append(r["duration_ms"])

        report = f"""
GEMINI FLASH LITE STRESS TEST RESULTS
{'='*50}
Test Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Duration: {duration}
Model: {MODEL_ID}

SUMMARY
-------
Total Requests: {self.stats["total"]}
Successful: {self.stats["success"]} ({self.stats["success"]/max(1,self.stats["total"])*100:.1f}%)
Failed: {self.stats["failed"]} ({self.stats["failed"]/max(1,self.stats["total"])*100:.1f}%)
Rate Limited: {self.stats["rate_limited"]}

PERFORMANCE
-----------
Average RPM: {avg_rpm:.2f}
Target RPM: {60/self.delay:.2f}
Total Tokens: {self.stats["total_tokens"]:,}
Avg Tokens/Request: {self.stats["total_tokens"]/max(1,self.stats["success"]):.0f}

STATUS BREAKDOWN
----------------
"""
        for status, count in sorted(status_counts.items()):
            report += f"  {status}: {count}\n"

        report += f"""
RESPONSE TIME BY IMAGE SIZE
---------------------------
"""
        for group, times in size_groups.items():
            if times:
                avg_time = sum(times) / len(times)
                report += f"  {group}: {avg_time:.0f}ms avg ({len(times)} samples)\n"
            else:
                report += f"  {group}: No data\n"

        report += f"""
FREE TIER ANALYSIS
------------------
Limit: {FREE_TIER_LIMITS['rpm']} RPM | Achieved: {avg_rpm:.2f} RPM
Limit: {FREE_TIER_LIMITS['rpd']} RPD | Projection: {int(avg_rpm * 60 * 24):,} RPD

RECOMMENDATIONS
---------------
"""
        if avg_rpm > FREE_TIER_LIMITS["rpm"]:
            report += "⚠️  You exceeded the free tier RPM limit!\n"
            report += f"   To stay safe, increase delay to {60/FREE_TIER_LIMITS['rpm']:.1f}s or higher\n"
        else:
            report += "✅ Within free tier RPM limits\n"

        if self.stats["rate_limited"] > 0:
            report += f"⚠️  Hit rate limits {self.stats['rate_limited']} times\n"
            report += "   Recommendation: Add exponential backoff or reduce concurrency\n"

        report += f"""
FILES GENERATED
---------------
CSV: {csv_file}
Report: {txt_file}

RAW DATA SAMPLE (Last 3 requests)
---------------------------------
"""
        for r in self.results[-3:]:
            report += f"{r['request_id']}: {r['status']} - {r['image']}\n"

        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print("\n" + "="*70)
        print("TEST COMPLETE")
        print("="*70)
        print(f"Duration: {duration}")
        print(f"Total: {self.stats['total']} | Success: {self.stats['success']} | RateLimits: {self.stats['rate_limited']}")
        print(f"Avg RPM: {avg_rpm:.2f}")
        print(f"\nFiles saved:")
        print(f"  CSV: {csv_file}")
        print(f"  Report: {txt_file}")
        print("="*70)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Gemini Flash Lite Stress Tester")
    parser.add_argument("--api-key", required=True, help="Your Gemini API Key")
    parser.add_argument("--duration", type=int, default=10, help="Test duration in minutes (default: 10)")
    parser.add_argument("--concurrent", type=int, default=3, help="Max concurrent requests (default: 3)")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay between requests in seconds (default: 2)")
    parser.add_argument("--images", default="./images", help="Path to images folder (default: ./images)")

    args = parser.parse_args()

    global API_KEY, IMAGE_FOLDER
    API_KEY = args.api_key
    IMAGE_FOLDER = Path(args.images)

    # Check dependencies
    try:
        import aiohttp
    except ImportError:
        print("Installing required package: aiohttp...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "aiohttp"])
        import aiohttp

    # Run test
    tester = StressTester(
        api_key=args.api_key,
        duration_minutes=args.duration,
        max_concurrent=args.concurrent,
        delay_seconds=args.delay
    )

    asyncio.run(tester.run_test())


if __name__ == "__main__":
    main()
