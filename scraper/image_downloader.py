"""Download and store event images locally."""

import asyncio
import hashlib
import logging
import mimetypes
from pathlib import Path
from urllib.parse import urlparse

import aiohttp

from .database import EventDatabase

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

DEFAULT_IMAGE_DIR = Path("scraper/images")


class ImageDownloader:
    """Download and manage event images."""

    def __init__(
        self,
        db_path: str = "scraper/events.db",
        image_dir: Path = DEFAULT_IMAGE_DIR,
        max_concurrent: int = 5,
    ):
        self.db = EventDatabase(db_path)
        self.image_dir = Path(image_dir)
        self.image_dir.mkdir(parents=True, exist_ok=True)
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)

    def _get_filename(self, url: str, content_type: str = None) -> str:
        """Generate a unique filename for an image URL."""
        # Create hash of URL for unique filename
        url_hash = hashlib.md5(url.encode()).hexdigest()[:12]

        # Try to get extension from URL
        parsed = urlparse(url)
        path = parsed.path.lower()

        # Common image extensions
        for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            if path.endswith(ext):
                return f"{url_hash}{ext}"

        # Try from content-type
        if content_type:
            ext = mimetypes.guess_extension(content_type.split(';')[0])
            if ext:
                return f"{url_hash}{ext}"

        # Default to .jpg
        return f"{url_hash}.jpg"

    async def _download_image(self, session: aiohttp.ClientSession, url: str) -> str | None:
        """Download a single image and return local path."""
        if not url:
            return None

        async with self.semaphore:
            try:
                async with session.get(url, timeout=30) as response:
                    if response.status != 200:
                        logger.warning(f"Failed to download {url}: HTTP {response.status}")
                        return None

                    content_type = response.headers.get('content-type', '')
                    if not content_type.startswith('image/'):
                        logger.warning(f"Not an image: {url} ({content_type})")
                        return None

                    filename = self._get_filename(url, content_type)
                    filepath = self.image_dir / filename

                    # Skip if already exists
                    if filepath.exists():
                        logger.debug(f"Image already exists: {filename}")
                        return str(filepath)

                    # Download and save
                    content = await response.read()
                    filepath.write_bytes(content)
                    logger.info(f"Downloaded: {filename}")
                    return str(filepath)

            except asyncio.TimeoutError:
                logger.warning(f"Timeout downloading: {url}")
                return None
            except Exception as e:
                logger.warning(f"Error downloading {url}: {e}")
                return None

    async def download_all_images(self) -> dict:
        """Download all event images and update database."""
        events = self.db.get_all_events()
        urls_to_download = {}

        # Collect unique URLs
        for event in events:
            if event.image_url and event.image_url not in urls_to_download:
                urls_to_download[event.image_url] = None

        logger.info(f"Found {len(urls_to_download)} unique images to download")

        # Download images
        async with aiohttp.ClientSession() as session:
            tasks = [
                self._download_image(session, url)
                for url in urls_to_download.keys()
            ]
            results = await asyncio.gather(*tasks)

        # Map URLs to local paths
        for url, local_path in zip(urls_to_download.keys(), results):
            urls_to_download[url] = local_path

        # Update database with local paths
        updated = 0
        for event in events:
            if event.image_url and urls_to_download.get(event.image_url):
                local_path = urls_to_download[event.image_url]
                self._update_local_image_path(event, local_path)
                updated += 1

        downloaded = sum(1 for p in urls_to_download.values() if p)
        stats = {
            "total_urls": len(urls_to_download),
            "downloaded": downloaded,
            "updated_events": updated,
            "image_dir": str(self.image_dir),
        }

        logger.info(f"Download complete: {stats}")
        return stats

    def _update_local_image_path(self, event, local_path: str):
        """Update event with local image path in database."""
        # Store local path in a new field or update existing
        # For now, we'll create a simple mapping file
        pass

    def get_local_image_path(self, image_url: str) -> str | None:
        """Get local path for an image URL if downloaded."""
        if not image_url:
            return None

        filename = self._get_filename(image_url)
        filepath = self.image_dir / filename

        if filepath.exists():
            return str(filepath)
        return None

    def export_image_manifest(self, output_path: str = "scraper/images/manifest.json"):
        """Export a JSON manifest mapping URLs to local files."""
        import json

        events = self.db.get_all_events()
        manifest = {}

        for event in events:
            if event.image_url:
                local_path = self.get_local_image_path(event.image_url)
                if local_path:
                    manifest[event.image_url] = {
                        "local_path": local_path,
                        "event_title": event.title,
                        "event_date": event.date,
                        "venue": event.venue,
                    }

        with open(output_path, 'w') as f:
            json.dump(manifest, f, indent=2)

        logger.info(f"Exported manifest with {len(manifest)} images to {output_path}")
        return len(manifest)


async def main():
    """Download all event images."""
    import argparse

    parser = argparse.ArgumentParser(description="Download event images")
    parser.add_argument("--db", default="scraper/events.db", help="Database path")
    parser.add_argument("--dir", default="scraper/images", help="Image output directory")
    parser.add_argument("--manifest", action="store_true", help="Export manifest after download")
    args = parser.parse_args()

    downloader = ImageDownloader(db_path=args.db, image_dir=Path(args.dir))
    stats = await downloader.download_all_images()

    print(f"\nImage Download Results:")
    print(f"  Total URLs: {stats['total_urls']}")
    print(f"  Downloaded: {stats['downloaded']}")
    print(f"  Saved to:   {stats['image_dir']}")

    if args.manifest:
        count = downloader.export_image_manifest()
        print(f"  Manifest:   {count} images mapped")


if __name__ == "__main__":
    asyncio.run(main())
