"""v39 Bengü kontak sayfası: bengu39_cekim.gd kırpımlarından bölüm başına satır.
python bengu39_sayfa.py <klasor> <cikti.jpg> [bolum[:bas:son:adim] ...] [--olcek=0.5] [--etiket=ÖNCE]
Birden çok klasör: --karsi=<klasor2> verilirse her bölüm için iki satır (üst: klasor, alt: klasor2)."""
import sys, os, glob
from PIL import Image, ImageDraw, ImageFont

def frames(d, name, a=0, b=None, st=1):
    fs = sorted(glob.glob(os.path.join(d, name + "_[0-9][0-9][0-9].png")))
    return fs[a:b:st]

def main():
    args = [x for x in sys.argv[1:] if not x.startswith("--")]
    opt = dict(x[2:].split("=", 1) for x in sys.argv[1:] if x.startswith("--") and "=" in x)
    d, out = args[0], args[1]
    d2 = opt.get("karsi")
    sc = float(opt.get("olcek", "0.5"))
    specs = args[2:]
    rows = []
    for sp in specs:
        p = sp.split(":")
        name = p[0]
        a = int(p[1]) if len(p) > 1 and p[1] else 0
        b = int(p[2]) if len(p) > 2 and p[2] else None
        st = int(p[3]) if len(p) > 3 else 1
        for dd, tag in ([(d, opt.get("etiket", "")), (d2, opt.get("etiket2", ""))] if d2 else [(d, opt.get("etiket", ""))]):
            fs = frames(dd, name, a, b, st)
            ims = [Image.open(f).convert("RGB") for f in fs]
            if ims:
                rows.append((f"{name} {tag}", ims))
    if not rows:
        print("boş"); return
    cw = int(rows[0][1][0].width * sc); ch = int(rows[0][1][0].height * sc)
    ncol = max(len(r[1]) for r in rows)
    lab = 110
    W = lab + ncol * cw; H = len(rows) * ch
    sheet = Image.new("RGB", (W, H), (20, 20, 24))
    dr = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except Exception:
        font = ImageFont.load_default()
    for ri, (t, ims) in enumerate(rows):
        dr.text((6, ri * ch + 8), t, fill=(230, 220, 200), font=font)
        for ci, im in enumerate(ims):
            sheet.paste(im.resize((cw, ch), Image.LANCZOS), (lab + ci * cw, ri * ch))
            dr.rectangle([lab + ci * cw, ri * ch, lab + ci * cw + cw - 1, ri * ch + ch - 1], outline=(50, 50, 60))
    sheet.save(out, quality=88)
    print(out, sheet.size)

main()
