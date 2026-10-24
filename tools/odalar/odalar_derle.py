# -*- coding: utf-8 -*-
"""v43 oda şablonu derleyici: tools/odalar/*.txt -> data/odalar/<dosya>.json

Kaynak biçimi (bkz. docs/TASARIM.md "v43: el yapımı odalar ve geçitler"):

    @ ad | dosya=ortak | biyom=* | tur=* | rol=ana,dal | tip=salon | gok=1 | simge=0 | agirlik=1
    ####################
    #..................#
    ...

Boş satır ya da sonraki "@" bloğu bitirir. "#" ile başlayan başlık dışı satırlar haritanın parçasıdır (yorum yok).
Satırlar sağdan boşlukla (dış kaya) doldurulur. Kullanım: python tools/odalar/odalar_derle.py
"""
import json
import os
import sys

KOK = os.path.dirname(os.path.abspath(__file__))
PROJE = os.path.dirname(os.path.dirname(KOK))
CIKTI = os.path.join(PROJE, "data", "odalar")
GECERLI = set("#.-=^LRTBga$*td~w ")


def oku(yol):
    odalar = []
    cur = None
    with open(yol, encoding="utf-8") as f:
        for ham in f.read().splitlines():
            satir = ham.rstrip("\r")
            if satir.startswith("@"):
                if cur:
                    odalar.append(cur)
                parca = [p.strip() for p in satir[1:].split("|")]
                cur = {"ad": parca[0], "dosya": "ortak", "biyom": ["*"], "tur": ["*"], "rol": ["ana", "dal"],
                       "tip": "salon", "gok": False, "simge": False, "agirlik": 1.0, "harita": []}
                for p in parca[1:]:
                    if "=" not in p:
                        continue
                    k, v = [x.strip() for x in p.split("=", 1)]
                    if k in ("biyom", "tur", "rol"):
                        cur[k] = [x.strip() for x in v.split(",") if x.strip()]
                    elif k in ("gok", "simge"):
                        cur[k] = v in ("1", "evet", "true")
                    elif k == "agirlik":
                        cur[k] = float(v)
                    else:
                        cur[k] = v
                continue
            if cur is None:
                continue
            if satir.strip() == "":
                if cur["harita"]:
                    odalar.append(cur)
                    cur = None
                continue
            cur["harita"].append(satir)
    if cur and cur["harita"]:
        odalar.append(cur)
    return odalar


def denetle(o):
    sorun = []
    w = max(len(s) for s in o["harita"])
    h = len(o["harita"])
    if not (w <= 20 or 28 <= w <= 44):
        sorun.append("genişlik %d" % w)
    if h > 12:
        sorun.append("yükseklik %d" % h)
    for y, s in enumerate(o["harita"]):
        for c in s:
            if c not in GECERLI:
                sorun.append("geçersiz karakter %r satır %d" % (c, y))
        if len(s) != w:
            sorun.append("satır %d uzunluğu %d (%d olmalı)" % (y, len(s), w))
    return sorun


def main():
    tum = {}
    hata = 0
    for ad in sorted(os.listdir(KOK)):
        if not ad.endswith(".txt"):
            continue
        for o in oku(os.path.join(KOK, ad)):
            s = denetle(o)
            if s:
                hata += 1
                print("SORUN %s: %s" % (o["ad"], "; ".join(s)))
            d = o.pop("dosya")
            tum.setdefault(d, []).append(o)
    os.makedirs(CIKTI, exist_ok=True)
    n = 0
    for d, liste in tum.items():
        with open(os.path.join(CIKTI, d + ".json"), "w", encoding="utf-8", newline="\n") as f:
            f.write('{\n "aciklama": "v43 el yapımı oda şablonları (tools/odalar/*.txt kaynağından odalar_derle.py ile)",\n "odalar": [\n')
            for i, o in enumerate(liste):
                harita = ",\n".join('    "%s"' % s for s in o["harita"])
                meta = {k: o[k] for k in ("ad", "biyom", "tur", "rol", "tip", "gok", "simge", "agirlik")}
                m = json.dumps(meta, ensure_ascii=False)[:-1]
                f.write('  %s, "harita": [\n%s\n  ]}%s\n' % (m, harita, "," if i < len(liste) - 1 else ""))
            f.write(" ]\n}\n")
        n += len(liste)
        print("%s.json: %d oda" % (d, len(liste)))
    print("TOPLAM %d şablon, sorunlu %d" % (n, hata))
    return 1 if hata else 0


if __name__ == "__main__":
    sys.exit(main())
