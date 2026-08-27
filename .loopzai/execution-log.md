<!-- execution-log.md — checkpointed action entries for the current cycle; entry format per ARCHITECTURE.md §6. -->

### entry-0001
```yaml
timestamp: 2026-08-27T07:36:25Z
phase: execution
cycle: 2
status: committed
commitSha: "eb6f39c7bf79ae22d5af28c6a1676a8d330b740e"
filesTouched: [".loopzai/execution-log.md", "scraper/image_utils.py", "scraper/requirements.txt"]
```
Creating scraper/image_utils.py with normalize_image_url per spec.md C1-C4, and adding pytest>=8 to scraper/requirements.txt per C26.

### entry-0002
```yaml
timestamp: 2026-08-27T07:37:05Z
phase: execution
cycle: 2
status: committed
commitSha: "a10a5e066df1ba8a42356b216139f4d36bd9d362"
filesTouched: [".loopzai/execution-log.md", "scraper/yoshis_scraper.py"]
```
Adding the Yoshi's pure helpers extract_image_url and detail_url_from_item plus the bounded, cached detail-page fetch layer per spec.md C5-C14 (milestone M1).

### entry-0003
```yaml
timestamp: 2026-08-27T07:39:06Z
phase: execution
cycle: 2
status: in_progress
commitSha: null
filesTouched: []
```
Capturing the two Yoshi's detail-page HTML fixtures named in spec.md section 5 into tests/fixtures/scraper/ before the live page ages out, so Verification has deterministic input for T2.
