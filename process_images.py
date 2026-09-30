# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "pillow>=10.0.0",
# ]
# ///
"""
Movie Asset Processor
- Tải toàn bộ ảnh backdrop_path từ movies.json về thư mục backdrop-cleans.
- Tự động crop ảnh backdrop theo tỷ lệ 2:3 (lấy vùng center, cắt bỏ 2 bên) lưu vào poster-cleans.
- Tự động làm mờ (Gaussian Blur) và làm tối 60%, nén dung lượng xuống ~20% lưu vào backdrop-blur.
- Hỗ trợ tải & xử lý song song (multithreading) và xử lý hàng loạt theo thư mục.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Tuple

try:
    from PIL import Image, ImageEnhance, ImageFilter
except ImportError:
    print("[ERROR] Thư viện 'Pillow' chưa được cài đặt.")
    print("Vui lòng chạy bằng uv: uv run process_images.py")
    print("Hoặc cài đặt qua pip: pip install pillow")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("MovieAssetProcessor")

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


class MovieAssetProcessor:
    """Quản lý tải, crop và hiệu ứng assets ảnh phim."""

    def __init__(
        self,
        base_dir: Path,
        json_filename: str = "movies.json",
        backdrop_dirname: str = "backdrop-cleans",
        poster_dirname: str = "poster-cleans",
        blur_dirname: str = "backdrop-blur",
        ratio: Tuple[int, int] = (2, 3),
        blur_radius: float = 14.0,
        darken_ratio: float = 0.50,
        blur_quality: int = 85,
        max_workers: int = 6,
        force_overwrite: bool = False,
    ) -> None:
        self.base_dir = base_dir.resolve()
        self.json_file = self.base_dir / json_filename
        self.backdrop_dir = self.base_dir / backdrop_dirname
        self.poster_dir = self.base_dir / poster_dirname
        self.blur_dir = self.base_dir / blur_dirname
        self.ratio = ratio
        self.blur_radius = blur_radius
        self.darken_ratio = max(0.0, min(1.0, darken_ratio))
        self.brightness_factor = max(0.0, 1.0 - self.darken_ratio)
        self.blur_quality = blur_quality
        self.max_workers = max_workers
        self.force_overwrite = force_overwrite

        self.backdrop_dir.mkdir(parents=True, exist_ok=True)
        self.poster_dir.mkdir(parents=True, exist_ok=True)
        self.blur_dir.mkdir(parents=True, exist_ok=True)

    def extract_backdrop_urls(self) -> List[str]:
        """Đọc và trích xuất danh sách backdrop_path từ file json."""
        if not self.json_file.exists():
            logger.warning("Không tìm thấy file JSON: %s, bỏ qua bước tải mới.", self.json_file)
            return []

        with open(self.json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        items: List[Dict[str, Any]] = []
        if isinstance(data, dict):
            items = data.get("results", [])
            if not items and "backdrop_path" in data:
                items = [data]
        elif isinstance(data, list):
            items = data

        urls: List[str] = []
        for item in items:
            if isinstance(item, dict):
                path = item.get("backdrop_path")
                if not path and isinstance(item.get("images"), dict):
                    path = item["images"].get("backdropClean")
                if path and isinstance(path, str) and path.strip():
                    urls.append(path.strip())

        logger.info("Tìm thấy %d backdrop URL(s) từ %s", len(urls), self.json_file.name)
        return urls

    def download_image(self, url: str) -> Tuple[str, bool, str]:
        """Tải một ảnh từ URL về thư mục backdrop-cleans."""
        filename = os.path.basename(url.split("?")[0])
        if not filename:
            filename = f"backdrop_{abs(hash(url))}.jpg"

        destination = self.backdrop_dir / filename

        if destination.exists() and not self.force_overwrite and destination.stat().st_size > 0:
            return filename, True, "Đã tồn tại (bỏ qua)"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=20) as resp:
                if resp.status != 200:
                    return filename, False, f"HTTP status {resp.status}"
                data = resp.read()

            destination.write_bytes(data)
            return filename, True, f"Tải thành công ({len(data) / 1024:.1f} KB)"
        except Exception as e:
            return filename, False, str(e)

    def download_all_backdrops(self, urls: List[str]) -> List[str]:
        """Tải toàn bộ backdrop bằng ThreadPoolExecutor."""
        logger.info("--- BƯỚC 1: Tải Backdrop vào %s ---", self.backdrop_dir.name)
        downloaded_files: List[str] = []
        failed_count = 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_url = {executor.submit(self.download_image, url): url for url in urls}
            for future in as_completed(future_to_url):
                filename, success, msg = future.result()
                if success:
                    downloaded_files.append(filename)
                    logger.info("✓ %s: %s", filename, msg)
                else:
                    failed_count += 1
                    logger.error("✗ %s thất bại: %s", filename, msg)

        logger.info(
            "Hoàn tất tải: %d thành công, %d thất bại.",
            len(downloaded_files),
            failed_count,
        )
        return downloaded_files

    def crop_to_aspect_ratio(self, src_path: Path, dst_path: Path) -> bool:
        """Crop ảnh theo tỷ lệ target_ratio (w:h = 2:3) từ center, bỏ 2 bên."""
        try:
            with Image.open(src_path) as img:
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")

                orig_w, orig_h = img.size
                target_w_ratio, target_h_ratio = self.ratio

                target_aspect = target_w_ratio / target_h_ratio
                orig_aspect = orig_w / orig_h

                if orig_aspect > target_aspect:
                    crop_w = int(round(orig_h * target_aspect))
                    crop_h = orig_h
                    left = (orig_w - crop_w) // 2
                    top = 0
                    right = left + crop_w
                    bottom = crop_h
                else:
                    crop_w = orig_w
                    crop_h = int(round(orig_w / target_aspect))
                    left = 0
                    top = (orig_h - crop_h) // 2
                    right = crop_w
                    bottom = top + crop_h

                cropped = img.crop((left, top, right, bottom))
                cropped.save(dst_path, quality=95, optimize=True)
                return True
        except Exception as e:
            logger.error("Lỗi khi crop %s: %s", src_path.name, e)
            return False

    def process_all_posters(self) -> None:
        """Duyệt toàn bộ ảnh trong backdrop-cleans để crop sang poster-cleans."""
        logger.info("--- BƯỚC 2: Crop Poster 2:3 vào %s ---", self.poster_dir.name)

        valid_extensions = {".jpg", ".jpeg", ".png", ".webp"}
        image_files = [
            f for f in sorted(self.backdrop_dir.iterdir())
            if f.is_file() and f.suffix.lower() in valid_extensions
        ]

        if not image_files:
            logger.warning("Không tìm thấy ảnh hợp lệ nào trong %s", self.backdrop_dir)
            return

        success_count = 0
        skipped_count = 0

        for img_path in image_files:
            dst_path = self.poster_dir / img_path.name
            if dst_path.exists() and not self.force_overwrite and dst_path.stat().st_size > 0:
                skipped_count += 1
                continue

            if self.crop_to_aspect_ratio(img_path, dst_path):
                success_count += 1
                logger.info("✓ Cropped 2:3: %s -> %s", img_path.name, dst_path.name)

        logger.info(
            "Hoàn tất crop poster: %d mới/cập nhật, %d đã tồn tại bỏ qua.",
            success_count,
            skipped_count,
        )

    def blur_and_darken_single(self, src_file: Path) -> Tuple[str, bool, int, int, str]:
        """Làm mờ, làm tối 60% và nén ảnh lưu vào backdrop-blur."""
        dst_file = self.blur_dir / src_file.name
        orig_size = src_file.stat().st_size

        if dst_file.exists() and not self.force_overwrite and dst_file.stat().st_size > 0:
            return src_file.name, True, orig_size, dst_file.stat().st_size, "Đã tồn tại (bỏ qua)"

        try:
            with Image.open(src_file) as img:
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")

                # Blur
                blurred = img.filter(ImageFilter.GaussianBlur(radius=self.blur_radius))
                # Darken 60% (độ sáng còn 40%)
                darkened = ImageEnhance.Brightness(blurred).enhance(self.brightness_factor)
                # Save optimized
                darkened.save(dst_file, format="JPEG", quality=self.blur_quality, optimize=True)

            new_size = dst_file.stat().st_size
            pct = (new_size / orig_size) * 100 if orig_size > 0 else 0
            msg = f"{orig_size / 1024:.1f} KB -> {new_size / 1024:.1f} KB ({pct:.1f}% gốc)"
            return src_file.name, True, orig_size, new_size, msg
        except Exception as e:
            return src_file.name, False, orig_size, 0, str(e)

    def process_all_blurs(self) -> None:
        """Duyệt toàn bộ ảnh trong backdrop-cleans để làm mờ, làm tối và lưu vào backdrop-blur."""
        logger.info(f"--- BƯỚC 3: Blur & Darken 60% vào {self.blur_dir.name} ---")

        valid_extensions = {".jpg", ".jpeg", ".png", ".webp"}
        image_files = [
            f for f in sorted(self.backdrop_dir.iterdir())
            if f.is_file() and f.suffix.lower() in valid_extensions
        ]

        if not image_files:
            logger.warning("Không tìm thấy ảnh hợp lệ nào trong %s", self.backdrop_dir)
            return

        total_orig_size = 0
        total_new_size = 0
        success_count = 0
        skipped_count = 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {
                executor.submit(self.blur_and_darken_single, img_path): img_path
                for img_path in image_files
            }

            for future in as_completed(future_to_file):
                filename, success, orig_sz, new_sz, msg = future.result()
                total_orig_size += orig_sz
                total_new_size += new_sz
                if success:
                    if "bỏ qua" in msg:
                        skipped_count += 1
                    else:
                        success_count += 1
                        logger.info("✓ Blur & Darken: %s: %s", filename, msg)
                else:
                    logger.error("✗ %s lỗi: %s", filename, msg)

        overall_pct = (total_new_size / total_orig_size * 100) if total_orig_size > 0 else 0
        logger.info(
            "Hoàn tất backdrop blur: %d mới/cập nhật, %d đã tồn tại bỏ qua (tỷ lệ dung lượng: %.1f%% so với gốc).",
            success_count,
            skipped_count,
            overall_pct,
        )

    def run(self) -> None:
        """Quy trình pipeline toàn diện 3 bước."""
        urls = self.extract_backdrop_urls()
        if urls:
            self.download_all_backdrops(urls)
        self.process_all_posters()
        self.process_all_blurs()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pipeline tải ảnh backdrop, crop poster 2:3 và tạo backdrop blur/darken."
    )
    parser.add_argument(
        "--dir",
        type=Path,
        default=Path(__file__).parent,
        help="Thư mục làm việc chứa movies.json (mặc định: thư mục chứa script)",
    )
    parser.add_argument(
        "--json",
        type=str,
        default="movies.json",
        help="Tên file JSON chứa metadata (mặc định: movies.json)",
    )
    parser.add_argument(
        "--backdrop-dir",
        type=str,
        default="backdrop-cleans",
        help="Tên thư mục lưu ảnh backdrop (mặc định: backdrop-cleans)",
    )
    parser.add_argument(
        "--poster-dir",
        type=str,
        default="poster-cleans",
        help="Tên thư mục lưu ảnh poster (mặc định: poster-cleans)",
    )
    parser.add_argument(
        "--blur-dir",
        type=str,
        default="backdrop-blur",
        help="Tên thư mục lưu ảnh backdrop làm mờ/tối (mặc định: backdrop-blur)",
    )
    parser.add_argument(
        "--blur-radius",
        type=float,
        default=14.0,
        help="Bán kính làm mờ Gaussian (mặc định: 14.0 - rõ hơn 30% so với 20.0)",
    )
    parser.add_argument(
        "--darken",
        type=float,
        default=0.50,
        help="Tỷ lệ làm tối (mặc định: 0.50 tức 50%, sáng hơn 10% so với 60%)",
    )
    parser.add_argument(
        "--blur-quality",
        type=int,
        default=85,
        help="Chất lượng nén JPEG cho ảnh blur (mặc định: 85 để còn ~20% dung lượng)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=6,
        help="Số luồng xử lý song song (mặc định: 6)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Ghi đè và xử lý lại toàn bộ file",
    )

    args = parser.parse_args()

    processor = MovieAssetProcessor(
        base_dir=args.dir,
        json_filename=args.json,
        backdrop_dirname=args.backdrop_dir,
        poster_dirname=args.poster_dir,
        blur_dirname=args.blur_dir,
        blur_radius=args.blur_radius,
        darken_ratio=args.darken,
        blur_quality=args.blur_quality,
        max_workers=args.workers,
        force_overwrite=args.force,
    )
    processor.run()


if __name__ == "__main__":
    main()
