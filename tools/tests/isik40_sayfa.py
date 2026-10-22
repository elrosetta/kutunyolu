"""v40 ışık / renk: önce-sonra sayfaları.

    python tools/tests/isik40_sayfa.py <cekim_klasoru> <cikti_klasoru> [--w 960]

<cekim_klasoru>/once_<sahne>.png ve sonra_<sahne>.png çiftlerini yan yana (önce | sonra) birleştirir, biyom başına
bir sayfa (giriş + orta, iki derinlik), geçiş şeridi (perde / ışınlanma / ölüm / boss tanıtımı) ve tek karelik
karşılaştırmalar yazar. Ayrıca her çift için ortalama parlaklık / doygunluk / kırpılan piksel yüzdesi (tonal denetim).
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

BIYOM = {"otuken": (1, 2), "bozkir": (3, 4), "sahmeran": (5, 6), "kaf": (7, 8), "tamu": (9, 10)}


def _font(sz):
    for p in ["C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


def _load(path, w):
    im = Image.open(path).convert("RGB")
    h = int(im.height * w / im.width)
    return im.resize((w, h), Image.LANCZOS)


def _stats(path):
    a = np.asarray(Image.open(path).convert("RGB")).astype(np.float32) / 255.0
    lum = a @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    mx = a.max(axis=2)
    mn = a.min(axis=2)
    sat = np.where(mx > 0.001, (mx - mn) / np.maximum(mx, 0.001), 0.0)
    return {
        "parlaklik": float(lum.mean()),
        "doygunluk": float(sat.mean()),
        "koyu%": float((lum < 0.03).mean() * 100.0),
        "patlak%": float((lum > 0.97).mean() * 100.0),
        "karsitlik": float(lum.std()),
    }


def _pair(src, sahne, w, font):
    o = os.path.join(src, "once_%s.png" % sahne)
    s = os.path.join(src, "sonra_%s.png" % sahne)
    if not os.path.exists(s):
        return None, ""
    ims = [_load(o, w) if os.path.exists(o) else None, _load(s, w)]
    h = ims[1].height
    out = Image.new("RGB", (w * 2 + 12, h + 28), (18, 18, 24))
    d = ImageDraw.Draw(out)
    for i, im in enumerate(ims):
        if im is None:
            continue
        out.paste(im, (i * (w + 12), 28))
    st = _stats(s)
    so = _stats(o) if os.path.exists(o) else None
    txt = "%s   önce → sonra" % sahne
    d.text((6, 6), txt, fill=(230, 225, 210), font=font)
    rep = "%s: parlaklık %.3f%s doygunluk %.3f%s koyu %%%.1f%s patlak %%%.2f%s" % (
        sahne, st["parlaklik"], (" (önce %.3f)" % so["parlaklik"]) if so else "",
        st["doygunluk"], (" (önce %.3f)" % so["doygunluk"]) if so else "",
        st["koyu%"], (" (önce %.1f)" % so["koyu%"]) if so else "",
        st["patlak%"], (" (önce %.2f)" % so["patlak%"]) if so else "")
    d.text((w + 18, 6), rep[len(sahne) + 2:][:150], fill=(180, 200, 190), font=font)
    return out, rep


def _stack(parts, title, font):
    parts = [p for p in parts if p is not None]
    if not parts:
        return None
    w = max(p.width for p in parts)
    h = sum(p.height for p in parts) + 36
    out = Image.new("RGB", (w, h), (18, 18, 24))
    ImageDraw.Draw(out).text((8, 8), title, fill=(240, 230, 200), font=font)
    y = 36
    for p in parts:
        out.paste(p, (0, y))
        y += p.height
    return out


def main():
    src = sys.argv[1]
    dst = sys.argv[2]
    w = 960
    if "--w" in sys.argv:
        w = int(sys.argv[sys.argv.index("--w") + 1])
    os.makedirs(dst, exist_ok=True)
    font = _font(16)
    rapor = []
    for b, (d0, d1) in BIYOM.items():
        parts = []
        for d in (d0, d1):
            for k in ("giris", "orta"):
                im, rep = _pair(src, "d%02d_%s" % (d, k), w, font)
                parts.append(im)
                if rep:
                    rapor.append(rep)
        sh = _stack(parts, "v40 ışık ve renk: %s (%d. ve %d. derinlik)" % (b, d0, d1), font)
        if sh:
            sh.save(os.path.join(dst, "biyom_%s.jpg" % b), quality=88)
    for grp, names in {
        "yurt_konak": ["yurt", "yurt_otag", "konak_d02", "konak_d06", "konak_d10"],
        "boss": ["boss_kara_boru_han_a", "boss_kara_boru_han_b", "boss_kara_boru_han_c", "boss_kara_boru_han_d",
                 "boss_sahmeran_c", "boss_sahmeran_d", "boss_erlik_han_c", "boss_erlik_han_d"],
        "gecisler": ["gecis_a", "gecis_b", "gecis_c", "isin_kapanis", "isin_varis", "isin_acilis", "olum_a", "olum_b", "olum_c", "olum_d"],
    }.items():
        parts = []
        for n in names:
            im, rep = _pair(src, n, w, font)
            parts.append(im)
            if rep:
                rapor.append(rep)
        sh = _stack(parts, "v40 ışık ve renk: %s" % grp, font)
        if sh:
            sh.save(os.path.join(dst, "%s.jpg" % grp), quality=88)
    with open(os.path.join(dst, "tonal_rapor.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(rapor))
    print("\n".join(rapor))


if __name__ == "__main__":
    main()
