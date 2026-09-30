# Movie Sample Data Catalog

Tập hợp dữ liệu mẫu (Mock Data, Layout Payload & Static Assets) phục vụ phát triển giao diện OTT, Web/App Streaming và kiểm thử Mock API.

Base Raw URL:
```text
https://raw.githubusercontent.com/kiendt-design/movie-sample-data/main/
```

---

## 📑 Mục lục Files Dữ liệu (JSON & JSONC Catalog)

| File | Số lượng | Mô tả | Định dạng | Raw Link |
| :--- | :---: | :--- | :--- | :--- |
| [`hero-banner-sample.jsonc`](file:///Users/kiendt/Documents/Projects/E2E-3.0/movie-sample-data/hero-banner-sample.jsonc) | **1** block | Cấu trúc dữ liệu chuẩn (FSD/Figma) cho Hero Banner component: gồm block config, tỷ lệ khung hình, auto-slide, danh sách banner item, tags, CTA buttons và actions | Object (JSONC) | [hero-banner-sample.jsonc](https://raw.githubusercontent.com/kiendt-design/movie-sample-data/main/hero-banner-sample.jsonc) |
| [`movies.json`](file:///Users/kiendt/Documents/Projects/E2E-3.0/movie-sample-data/movies.json) | **20** items | Danh sách thông tin chi tiết các bộ phim, metadata và bộ link ảnh UI (posters, backdrops) | Array of Objects | [movies.json](https://raw.githubusercontent.com/kiendt-design/movie-sample-data/main/movies.json) |
| [`buttons.json`](file:///Users/kiendt/Documents/Projects/E2E-3.0/movie-sample-data/buttons.json) | **3** items | Danh sách direct URL các icon nút bấm điều hướng UI (Play, Add to Watchlist, Info) | Array of Strings | [buttons.json](https://raw.githubusercontent.com/kiendt-design/movie-sample-data/main/buttons.json) |
| [`tags.json`](file:///Users/kiendt/Documents/Projects/E2E-3.0/movie-sample-data/tags.json) | **3** items | Danh sách direct URL các nhãn/badge hiển thị (Rating star, 4K UHD, Dolby Atmos) | Array of Strings | [tags.json](https://raw.githubusercontent.com/kiendt-design/movie-sample-data/main/tags.json) |
| [`titles.json`](file:///Users/kiendt/Documents/Projects/E2E-3.0/movie-sample-data/titles.json) | **4** items | Danh sách direct URL logo dạng chữ nghệ thuật (Title treatment logo PNG transparent) | Array of Strings | [titles.json](https://raw.githubusercontent.com/kiendt-design/movie-sample-data/main/titles.json) |

---

## 🔍 Chi tiết Schema & Cấu trúc Dữ liệu

### 1. `hero-banner-sample.jsonc` (Layout API Payload)
Payload mẫu chuẩn cấp cao nhất cho màn hình Home, ánh xạ chính xác theo đặc tả FSD và thiết kế Figma OTT:

* **Cấu hình khối (`blockConfig`):**
  * `blockId` / `blockType`: Định danh khối (`hero_banner_home` / `HERO_BANNER`).
  * `config.ui`: Tỷ lệ khung hình `aspectRatio: "3:4"` (368x480px), chu kỳ trượt tự động `interval: 5000ms`, hình thái indicator `DOT` | `PILL`, quy tắc căn lề `alignment: "CENTER"`.
  * `config.media`: Cấu hình autoplay (`autoplayMuted: true`).
* **Dữ liệu Banner (`items[]`):**
  * `bannerId` / `bannerType`: ID và loại nội dung (`MOVIE`, `SERIES`, `EVENT`).
  * `topTag`: Nhãn xếp hạng nổi bật phía trên tiêu đề (vd: `"Top 1 Action"`).
  * `metaInfo`: Dòng thông tin tổng hợp (`[Năm] • [Quốc gia] • [Thời lượng] • [Độ tuổi]`).
  * `images`: Bộ ảnh chuyên dụng cho banner (`titleImage`, `backdropClean`, `backdropBlur`, `posterClean`).
  * `tagsObject[]`: Mảng huy hiệu/nhãn phân loại (Icon + Text như Rating `4.9`, `4K`, `Dolby Atmos`, `Lồng tiếng`).
  * `buttons[]`: Bộ 3 nút CTA theo layout Figma (`Favorite` - Add, `Watch Now` - Play, `Details` - Info) kèm hành vi điều hướng `action`.
  * `action`: Action payload khi click vào toàn bộ banner.
* **Pagination & Cache:** `pageInfo` (`limit`, `hasMore`, `nextCursor`) và thời gian hết hạn CDN `expiresAt`.

---

### 2. `movies.json` (Catalog Metadata)
Chứa 20 bản ghi phim chuẩn hóa phục vụ grid/list/carousel.

* **Metadata:** `id`, `title`, `overview`, `language`, `releaseDate`, `popularity`, `voteAverage`, `voteCount`.
* **Bộ ảnh (`images`):**
  * `backdropClean`: Ảnh nền gốc chất lượng cao không text (16:9).
  * `backdropBlur`: Ảnh nền Gaussian Blur & giảm sáng 60% làm ambient background.
  * `posterClean`: Poster crop 2:3 từ backdrop (Center crop).
  * `posterLanscape`: Ảnh banner ngang.
  * `posterPotrait`: Poster dọc chuẩn rạp.

#### Sample Item:
```json
{
  "id": 640146,
  "title": "Ant-Man and the Wasp: Quantumania",
  "overview": "Super-Hero partners Scott Lang and Hope van Dyne...",
  "language": "en",
  "releaseDate": "2023-02-15",
  "popularity": 9272.643,
  "voteAverage": 6.5,
  "voteCount": 1856,
  "images": {
    "backdropClean": "https://raw.githubusercontent.com/kiendt-design/movie-sample-data/main/backdrop-cleans/8YFL5QQVPy3AgrEQxNYVSgiPEbe.jpg",
    "backdropBlur": "https://raw.githubusercontent.com/kiendt-design/movie-sample-data/main/backdrop-blur/8YFL5QQVPy3AgrEQxNYVSgiPEbe.jpg",
    "posterClean": "https://raw.githubusercontent.com/kiendt-design/movie-sample-data/main/poster-cleans/8YFL5QQVPy3AgrEQxNYVSgiPEbe.jpg",
    "posterLanscape": "https://raw.githubusercontent.com/kiendt-design/movie-sample-data/main/backdrop-cleans/8YFL5QQVPy3AgrEQxNYVSgiPEbe.jpg",
    "posterPotrait": "https://raw.githubusercontent.com/kiendt-design/movie-sample-data/main/posters/ngl2FKBlU4fhbdsrtdom9LVLBXw.jpg"
  }
}
```

---

### 3. UI Asset Lists (`buttons.json`, `tags.json`, `titles.json`)
Các mảng chuỗi đường dẫn trực tiếp (Direct CDN URLs) phục vụ rendering giao diện:

* **[`buttons.json`](file:///Users/kiendt/Documents/Projects/E2E-3.0/movie-sample-data/buttons.json) (3 icons):** Icon nút điều hướng dạng PNG trong suốt gồm `btn-plus-add.png` (Yêu thích/Thêm vào danh sách), `btn-play.png` (Xem ngay), và `btn-circle-info.png` (Chi tiết).
* **[`tags.json`](file:///Users/kiendt/Documents/Projects/E2E-3.0/movie-sample-data/tags.json) (3 badges):** Icon badge hiển thị trên thẻ gồm `tag-1.png` (Icon ngôi sao đánh giá), `tag-2.png` (Badge 4K), và `tag-3.png` (Huy hiệu Dolby Atmos).
* **[`titles.json`](file:///Users/kiendt/Documents/Projects/E2E-3.0/movie-sample-data/titles.json) (4 logos):** Title treatment logos (`title-1.png` đến `title-4.png`) dạng PNG trong suốt chất lượng cao đè lên banner thay thế plain text title.

---

## 📁 Cấu trúc Thư mục

```text
movie-sample-data/
├── README.md                 # Mục lục và tài liệu mô tả dataset
├── hero-banner-sample.jsonc  # Payload mẫu hoàn chỉnh cho Hero Banner component
├── movies.json               # Dataset 20 phim kèm metadata & image set
├── buttons.json              # Asset URLs cho action buttons (3 items)
├── tags.json                 # Asset URLs cho badges/tags (3 items)
├── titles.json               # Asset URLs cho title logos (4 items)
├── backdrop-blur/            # Ảnh nền mờ (Gaussian Blur + dim 60%)
├── backdrop-cleans/          # Ảnh nền gốc không text (16:9)
├── poster-cleans/            # Poster crop 2:3 từ backdrop
├── posters/                  # Poster dọc chính thức (2:3)
├── buttons/                  # Files ảnh nút điều hướng
├── tags/                     # Files ảnh tag/badge
├── titles/                   # Files ảnh title treatment logo
├── process_images.py         # Script tải & tiền xử lý tối ưu ảnh
└── process_blur.py           # Script xử lý blur & dim backdrop
```

---

## 🚀 Hướng dẫn Sử dụng Nhanh

### Fetch qua JavaScript/TypeScript:
```javascript
// 1. Lấy layout payload Hero Banner
const heroRes = await fetch("https://raw.githubusercontent.com/kiendt-design/movie-sample-data/main/hero-banner-sample.jsonc");
const heroBanner = await heroRes.json();

// 2. Lấy danh sách phim
const moviesRes = await fetch("https://raw.githubusercontent.com/kiendt-design/movie-sample-data/main/movies.json");
const movies = await moviesRes.json();
```

### Sử dụng qua cURL:
```bash
curl -s https://raw.githubusercontent.com/kiendt-design/movie-sample-data/main/hero-banner-sample.jsonc
```
