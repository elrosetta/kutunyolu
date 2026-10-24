class_name GecitGen
extends RefCounted
## v43 DİKEY GEÇİT TÜRLERİ: v33-v42'nin her kuyusu aynıydı (3 sütun düşüş + ara duvar + 2 sütun basamak, 3 satırda bir).
## Artık her dikey bağlantı biyoma / bölüm türüne göre seçilen bir GEÇİT TÜRÜDÜR; her türün kendi biçimi, çizimi ve hissi
## var. Hepsi erişim modeline (LevelGen._moves: tek zıplama 3, çift 4 karo; ±5 sütun) sadıktır: tırmanılabilir yüzeyler
## (zincir, ip merdiven, kök / sarmaşık) oyuncu için tırmanma durumu sunar (Player v43 tırmanma bloğu), ama yanlarında
## her zaman zıplanabilir tutamaklar (halka rafı, ip basamağı, kök düğümü) vardır: bot ve model tırmanmayı varsaymaz.
##
##   ip        İp merdiven (Bozkır, Kaf, Ötüken): 3 sütun düşüş yolu + 2 sütun ip merdiven (basamaklar 3 satırda bir)
##   zincir    Demir zincir (Tamu, kale): ortada 2 sütun düşüş yolu, tavandan sarkan salınan zincir; iki duvarda sırayla
##             demir raflar (zikzak)
##   kok       Kök / sarmaşık duvarı (Ötüken, Şahmeran): 2 sütun düşüş, 3 sütun kök duvarı; düzensiz kök düğümleri (2-3 aralık)
##   merdiven  Kırık taş merdiven (kale, Bozkır kervansarayı, Tamu kemik kale): 8 sütun; iki yanda sırayla kırık taş
##             sahanlıklar (iç ucu bir basamak yüksek), dipte moloz yığını; ortada düşüş yolu
##   cikinti   Yar çıkıntıları (Kaf buz yarı, Bozkır, Şahmeran): 7 sütun; iki duvardan düzensiz genişlikte kaya çıkıntıları,
##             dipte kaya yığını
##   ruzgar    Rüzgâr bacası (Kaf): çıkıntılar + yukarı esen rüzgâr (Player: içindeyken yükseltir, düşüşü yavaşlatır)
##   iskele    Ahşap / buz iskele (Ötüken, Bozkır, Kaf): 2 sütun düşüş + kaydırmalı tahta kat iskelesi (dikmeler, çaprazlar)
##   dusus     Düşüş deliği (yalnız aşağı inen ana yol): 4 sütun açık delik, dipte yumuşak iniş (saman / kar / yaprak / su /
##             kül); geri dönüş yok (Dead Cells'in tek yönlü inişleri; ödüllere Kut Taşı ile dönülür)
##   kuyu      v33 kuyusu (yalnız "eski" tür / yedek)
## Her açık düşüş yolunun dibinde (6+ karo düşüşte) biyomun yumuşak iniş yığını: sersemletmez (Player._on_land).

const GENISLIK := {"ip": 5, "zincir": 6, "kok": 5, "merdiven": 8, "cikinti": 7, "ruzgar": 6, "iskele": 7, "dusus": 4, "kuyu": 6}
const AGIRLIK := {
	"otuken": {"kok": 4.0, "ip": 2.0, "iskele": 2.0, "cikinti": 1.5, "dusus": 1.0},
	"bozkir": {"ip": 4.0, "iskele": 3.0, "merdiven": 2.0, "cikinti": 1.0, "dusus": 1.0},
	"kaf": {"cikinti": 3.0, "ruzgar": 2.5, "ip": 2.0, "iskele": 1.5, "dusus": 1.0},
	"sahmeran": {"kok": 3.5, "cikinti": 2.5, "merdiven": 1.0, "dusus": 1.5, "ip": 0.5},
	"tamu": {"zincir": 4.5, "merdiven": 2.5, "iskele": 1.0, "cikinti": 1.0, "dusus": 0.7},
	"diger": {"ip": 2.0, "zincir": 1.0, "kok": 1.0, "merdiven": 1.0, "cikinti": 1.0, "iskele": 1.0},
}
const TUR_CARPAN := {"kale": {"merdiven": 2.0, "zincir": 1.5}, "magara": {"kok": 1.3, "cikinti": 1.3},
	"acik": {"iskele": 1.3, "ip": 1.2}}
const YUMUSAK := {"otuken": "yaprak", "bozkir": "saman", "kaf": "kar", "sahmeran": "su", "tamu": "kul"}


static func sirala(rng: RandomNumberGenerator, biyom: String, tur: String, kullanilan: Dictionary, dusus_ok: bool) -> Array:
	## Ağırlıklı rastgele sıra (aynı bölümde kullanılmış türler seyrekleşir: tekrar etmesin)
	var ag: Dictionary = AGIRLIK.get(biyom, AGIRLIK["diger"])
	var cp: Dictionary = TUR_CARPAN.get(tur, {})
	var havuz: Array = []
	for t in ag:
		var w := float(ag[t]) * float(cp.get(t, 1.0))
		if t == "dusus" and not dusus_ok:
			continue
		var n := int(kullanilan.get(t, 0))
		if n == 1:
			w *= 0.3
		elif n >= 2:
			w *= 0.12
		havuz.append([t, w])
	var out: Array = []
	while not havuz.is_empty():
		var top := 0.0
		for h in havuz:
			top += float(h[1])
		var r := rng.randf() * top
		var k := havuz.size() - 1
		for i in havuz.size():
			r -= float(havuz[i][1])
			if r <= 0.0:
				k = i
				break
		out.append(String(havuz[k][0]))
		havuz.remove_at(k)
	return out


static func _x(hx: int, gw: int, c: int, flip: bool) -> int:
	return hx + (gw - 1 - c if flip else c)


static func _bas(g: PackedByteArray, W: int, H: int, x: int, y: int, v: int) -> void:
	if x >= 0 and x < W and y >= 0 and y < H:
		g[y * W + x] = v


static func oy(g: PackedByteArray, W: int, H: int, d: Dictionary, biyom: String) -> Dictionary:
	## d: kapı (x = hx, gw, gecit, flip, acik, y = fyA üst taban, y2 = fyB alt taban). Izgarayı oyar, çizim / tırmanma
	## verisini döndürür: {tip, x0, x1, ust, alt, lane [x0, x1], tirman [[x0, y0, x1, y1] karo dörtgenleri], basamak
	## [[x, y]] (görünmez platform karoları: kendi çizimi var), kapak [[x, y]], kati [[x, y]] (sahanlık / çıkıntı
	## karoları), yumusak [x0, x1, y], ruzgar [x0, y0, x1, y1], capa (zincirin asıldığı satır)}
	var tip := String(d["gecit"])
	var hx := int(d["x"])
	var gw := int(d["gw"])
	var fyA := int(d["y"])
	var fyB := int(d["y2"])
	var flip: bool = d["flip"]
	var acik: bool = d["acik"]
	var out := {"tip": tip, "x0": hx, "x1": hx + gw - 1, "ust": fyA, "alt": fyB, "tirman": [], "basamak": [], "kapak": [],
		"kati": [], "yumusak": [], "ruzgar": [], "capa": int(d.get("capa", fyA - 6)), "flip": flip, "biyom": biyom, "acik": acik}
	var lane: Array = []
	match tip:
		"ip":
			lane = [0, 2]
		"zincir":
			lane = [2, 3]
		"kok":
			lane = [0, 1]
		"merdiven":
			lane = [3, 4]
		"cikinti":
			lane = [2, 4]
		"ruzgar":
			lane = [2, 3]
		"iskele":
			lane = [0, 1]
		"dusus":
			lane = [0, 3]
	# gövde: bütün genişlik üst tabandan alt tabana boş; üst satır tek yönlü kapak (düşüş yolu açıksa delik)
	for c in gw:
		var x := _x(hx, gw, c, flip)
		for y in range(fyA + 1, fyB):
			_bas(g, W, H, x, y, 0)
		var in_lane: bool = c >= int(lane[0]) and c <= int(lane[1])
		if in_lane and acik:
			_bas(g, W, H, x, fyA, 0)
		else:
			_bas(g, W, H, x, fyA, 2)
			out["kapak"].append([x, fyA])
	var lx0 := _x(hx, gw, int(lane[0]), flip)
	var lx1 := _x(hx, gw, int(lane[1]), flip)
	out["lane"] = [mini(lx0, lx1), maxi(lx0, lx1)]
	match tip:
		"ip":
			for ry in _basamak_satirlari(fyA, fyB, 3):
				for c in [3, 4]:
					_platform(g, W, H, out, _x(hx, gw, c, flip), ry)
			var cx := _x(hx, gw, 3, flip)
			var cx2 := _x(hx, gw, 4, flip)
			out["tirman"].append([float(mini(cx, cx2)), float(fyA - 1), float(maxi(cx, cx2) + 1), float(fyB)])
		"zincir":
			var yan := 0
			for ry in _basamak_satirlari(fyA, fyB, 3):
				for c in ([0, 1] if yan == 0 else [4, 5]):
					_platform(g, W, H, out, _x(hx, gw, c, flip), ry)
				yan = 1 - yan
			var zx := float(mini(_x(hx, gw, 2, flip), _x(hx, gw, 3, flip))) + 1.0
			out["tirman"].append([zx - 0.45, float(out["capa"]), zx + 0.45, float(fyB) - 1.0])
		"kok":
			# düzensiz kök düğümleri: 2-3 satır aralık, 2 sütun, yanlara bir sütun kayarak
			var ry := fyA + 3
			var kay := 0
			var rows: Array = []
			while fyB - ry >= 2:
				rows.append([ry, kay])
				var adim := 3 if (rows.size() % 3 != 2) else 2
				kay = 1 - kay
				ry += adim
			if not rows.is_empty() and fyB - int(rows[rows.size() - 1][0]) > 4:
				rows.append([fyB - 2, 1 - int(rows[rows.size() - 1][1])])
			for rr in rows:
				var c0 := 2 + int(rr[1])
				for c in [c0, c0 + 1]:
					_platform(g, W, H, out, _x(hx, gw, c, flip), int(rr[0]))
			var kx0 := mini(_x(hx, gw, 2, flip), _x(hx, gw, 4, flip))
			out["tirman"].append([float(kx0) + 0.3, float(fyA - 1), float(kx0) + 2.7, float(fyB)])
		"merdiven", "cikinti", "ruzgar":
			_sahanliklar(g, W, H, out, hx, gw, fyA, fyB, flip, tip, d)
			if tip == "ruzgar":
				out["ruzgar"] = [float(out["lane"][0]), float(fyA - 4), float(out["lane"][1] + 1), float(fyB)]
		"iskele":
			var yan2 := 0
			for ry in _basamak_satirlari(fyA, fyB, 3):
				var cs: Array = [2, 3, 4] if yan2 == 0 else [4, 5, 6]
				for c in cs:
					_platform(g, W, H, out, _x(hx, gw, c, flip), ry)
				yan2 = 1 - yan2
		"dusus":
			pass
	if fyB - fyA >= 6 or tip == "dusus":
		out["yumusak"] = [out["lane"][0], out["lane"][1], fyB]
	return out


static func _platform(g: PackedByteArray, W: int, H: int, out: Dictionary, x: int, y: int) -> void:
	_bas(g, W, H, x, y, 2)
	out["basamak"].append([x, y])


static func _basamak_satirlari(fyA: int, fyB: int, adim: int) -> Array:
	## v33 kuyusunun basamak düzeni: tepeden adım satırda bir; tabana 4 kalırsa ara basamak (tabana 2)
	var rows: Array = []
	var r := fyA
	while fyB - (r + adim) >= 2:
		r += adim
		rows.append(r)
	if fyB - r == 4:
		rows.append(fyB - 2)
	return rows


static func _sahanliklar(g: PackedByteArray, W: int, H: int, out: Dictionary, hx: int, gw: int, fyA: int, fyB: int, flip: bool, tip: String, d: Dictionary) -> void:
	## Katı sahanlık / çıkıntılar iki duvardan sırayla (3 satır arayla); en alttakinin altında 3 karo baş boşluğu kalsın
	## diye en alttaki sahanlık tabandan en az 4 yukarıda, karşı yanda tabanda 1-3 karoluk moloz / kaya yığını (tek zıplama).
	var rows: Array = []
	var r := fyA + 3
	rows.append(r)
	while fyB - (r + 3) >= 4:
		r += 3
		rows.append(r)
	var yan := 0 if bool(d.get("flip2", false)) else 1
	var rng_w: Array = d.get("genislikler", [])
	for i in rows.size():
		var ry: int = rows[i]
		var gen := 3
		if tip == "cikinti":
			gen = int(rng_w[i % rng_w.size()]) if not rng_w.is_empty() else 3
		elif tip == "ruzgar":
			gen = 2
		var cs: Array = []
		for k in gen:
			cs.append(k if yan == 0 else gw - 1 - k)
		for c in cs:
			var x := _x(hx, gw, c, flip)
			_bas(g, W, H, x, ry, 1)
			out["kati"].append([x, ry])
		if tip == "merdiven":
			# kırık merdiven: iç uç bir basamak yüksek
			var ic: int = cs[cs.size() - 1]
			var x2 := _x(hx, gw, ic, flip)
			_bas(g, W, H, x2, ry - 1, 1)
			out["kati"].append([x2, ry - 1])
		yan = 1 - yan
	# dip yığını: son sahanlığın karşı yanında
	var D := fyB - int(rows[rows.size() - 1])
	var p := clampi(D - 3, 1, 3)
	if D - 1 > p and tip != "merdiven":
		p = mini(3, maxi(p, D - 3))
	var yg := 3 if tip == "merdiven" else 2
	for k in yg:
		var c := k if yan == 0 else gw - 1 - k
		var x := _x(hx, gw, c, flip)
		for y in range(fyB - p, fyB):
			_bas(g, W, H, x, y, 1)
			out["kati"].append([x, y])
	out["yigin"] = [p, yan]
