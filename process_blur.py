# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "pillow>=10.0.0",
# ]
# ///
"""
Backdrop Blur & Darken Processor
- Làm mờ (Gaussian Blur) và làm tối 60% từ ảnh backdrop-cleans.
- Tối ưu dung lượng file xuất ra đạt khoảng ~20% so với ảnh gốc (tiết kiệm ~80% băng thông).
- Xuất ra thư mục backdrop-blur.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Tuple

try:
    from PIL import Image, ImageEnhance, ImageFilter
except ImportError:
    print("[ERROR] Thư viện 'Pillow' chưa được cài đặt.")
    print("Vui lòng chạy bằng uv: uv run process_blur.py")
    print("Hoặc cài đặt qua pip: pip install pillow")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("BackdropBlurProcessor")


class BackdropBlurProcessor:
    """Xử lý làm mờ, làm tối và nén dung lượng backdrop."""

    def __init__(
        self,
        base_dir: Path,
        src_dirname: str = "backdrop-cleans",
        dst_dirname: str = "backdrop-blur",
        blur_radius: float = 14.0,
        darken_ratio: float = 0.50,
        quality: int = 85,
        max_workers: int = 6,
        force_overwrite: bool = False,
    ) -> None:
        self.base_dir = base_dir.resolve()
        self.src_dir = self.base_dir / src_dirname
        self.dst_dir = self.base_dir / dst_dirname
        self.blur_radius = blur_radius
        self.darken_ratio = max(0.0, min(1.0, darken_ratio))
        # Làm tối 60% -> Hệ số độ sáng còn lại = 1.0 - 0.60 = 0.40
        self.brightness_factor = max(0.0, 1.0 - self.darken_ratio)
        self.quality = quality
        self.max_workers = max_workers
        self.force_overwrite = force_overwrite

        self.dst_dir.mkdir(parents=True, exist_ok=True)

    def process_single_image(self, src_file: Path) -> Tuple[str, bool, int, int, str]:
        """
        Xử lý 1 ảnh: Blur -> Darken -> Nén chất lượng -> Lưu file.
        Trả về: (filename, success, orig_size, new_size, message)
        """
        dst_file = self.dst_dir / src_file.name
        orig_size = src_file.stat().st_size

        if dst_file.exists() and not self.force_overwrite and dst_file.stat().st_size > 0:
            return src_file.name, True, orig_size, dst_file.stat().st_size, "Đã tồn tại (bỏ qua)"

        try:
            with Image.open(src_file) as img:
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")

                # 1. Làm mờ (Gaussian Blur)
                blurred = img.filter(ImageFilter.GaussianBlur(radius=self.blur_radius))

                # 2. Làm tối (Darken)
                enhancer = ImageEnhance.Brightness(blurred)
                darkened = enhancer.enhance(self.brightness_factor)

                # 3. Lưu ảnh với chất lượng nén tối ưu dung lượng (~20% dung lượng gốc)
                darkened.save(
                    dst_file,
                    format="JPEG",
                    quality=self.quality,
                    optimize=True,
                )

            new_size = dst_file.stat().st_size
            pct = (new_size / orig_size) * 100 if orig_size > 0 else 0
            msg = f"{orig_size / 1024:.1f} KB -> {new_size / 1024:.1f} KB ({pct:.1f}% gốc)"
            return src_file.name, True, orig_size, new_size, msg

        except Exception as e:
            return src_file.name, False, orig_size, 0, str(e)

    def run(self) -> None:
        """Quét và xử lý toàn bộ ảnh trong thư mục."""
        if not self.src_dir.exists():
            raise FileNotFoundError(f"Thư mục nguồn không tồn tại: {self.src_dir}")

        valid_extensions = {".jpg", ".jpeg", ".png", ".webp"}
        image_files: List[Path] = [
            f for f in sorted(self.src_dir.iterdir())
            if f.is_file() and f.suffix.lower() in valid_extensions
        ]

        if not image_files:
            logger.warning("Không tìm thấy ảnh hợp lệ nào trong %s", self.src_dir)
            return

        logger.info(
            "Bắt đầu xử lý %d ảnh: Blur (radius=%.1f), Tối %.0f%%, Chất lượng=%d",
            len(image_files),
            self.blur_radius,
            self.darken_ratio * 100,
            self.quality,
        )
        logger.info("Thư mục đầu ra: %s", self.dst_dir)

        total_orig_size = 0
        total_new_size = 0
        success_count = 0
        failed_count = 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {
                executor.submit(self.process_single_image, img_path): img_path
                for img_path in image_files
            }

            for future in as_completed(future_to_file):
                filename, success, orig_sz, new_sz, msg = future.result()
                total_orig_size += orig_sz
                total_new_size += new_sz
                if success:
                    success_count += 1
                    logger.info("✓ %s: %s", filename, msg)
                else:
                    failed_count += 1
                    logger.error("✗ %s lỗi: %s", filename, msg)

        overall_pct = (total_new_size / total_orig_size * 100) if total_orig_size > 0 else 0
        logger.info("=" * 60)
        logger.info("TỔNG KẾT XỬ LÝ BACKDROP BLUR:")
        logger.info(" - Thành công: %d/%d file", success_count, len(image_files))
        logger.info(" - Dung lượng ban đầu: %.2f MB", total_orig_size / (1024 * 1024))
        logger.info(" - Dung lượng sau xử lý: %.2f MB", total_new_size / (1024 * 1024))
        logger.info(" - Tỷ lệ dung lượng so với gốc: %.1f%% (Giảm %.1f%%)", overall_pct, 100 - overall_pct)
        logger.info("=" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Làm mờ, làm tối 60% và nén dung lượng backdrop xuống ~20%."
    )
    parser.add_argument(
        "--dir",
        type=Path,
        default=Path(__file__).parent,
        help="Thư mục làm việc chứa thư mục ảnh (mặc định: cùng thư mục với script)",
    )
    parser.add_argument(
        "--src-dir",
        type=str,
        default="backdrop-cleans",
        help="Thư mục nguồn chứa ảnh backdrop (mặc định: backdrop-cleans)",
    )
    parser.add_argument(
        "--dst-dir",
        type=str,
        default="backdrop-blur",
        help="Thư mục đích lưu ảnh mờ/tối (mặc định: backdrop-blur)",
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
        help="Tỷ lệ làm tối (mặc định: 0.50 tức tối 50%, sáng hơn 10% so với 60%)",
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=85,
        help="Chất lượng nén JPEG (mặc định: 85 để đạt ~20% dung lượng)",
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
        help="Ghi đè nếu file đã tồn tại",
    )

    args = parser.parse_args()

    processor = BackdropBlurProcessor(
        base_dir=args.dir,
        src_dirname=args.src_dir,
        dst_dirname=args.dst_dir,
        blur_radius=args.blur_radius,
        darken_ratio=args.darken,
        quality=args.quality,
        max_workers=args.workers,
        force_overwrite=args.force,
    )
    processor.run()


if __name__ == "__main__":
    main()
