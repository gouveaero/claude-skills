# Aspect Ratio Presets

## Instagram Portrait (default)
```
ratio: 1080x1350
--slide-w: 1080px
--slide-h: 1350px
padding: 80px 72px
```
Best for: feed posts, carousels. Most engagement on Instagram.

## Instagram Square
```
ratio: 1080x1080
--slide-w: 1080px
--slide-h: 1080px
padding: 72px
```
Best for: reposts, older audiences.

## LinkedIn
```
ratio: 1200x1500 (portrait PDF)  or  1080x1350 (also accepted)
--slide-w: 1200px
--slide-h: 1500px
padding: 90px 80px
```
LinkedIn PDFs render at ~1584×2246. 1200×1500 at @2x = 2400×3000 → renders well.

## Instagram/TikTok Story
```
ratio: 1080x1920
--slide-w: 1080px
--slide-h: 1920px
padding: 96px 72px
```
Reduce font sizes by ~20% vs 1080×1350. More vertical room → more content possible.

## Default when unspecified
Use `1080x1350` (Instagram Portrait).

## How Phase 4 uses this
Insert these values into the `:root { --slide-w: Xpx; --slide-h: Ypx; }` block in the brand injection CSS.
