class_name OtagYeri
extends RefCounted
## v42 Otağ Yeri: bölüm sonundaki sınav otağlarının yerleşimi ve Çabuk sınavının süresi (yalnızca ızgara + oda verisi:
## üreticinin sonucuyla da (--harita, Level kurulmadan) aynı biçimde çalışır).
##
## Yerleşim: Kut Kapısı'nın odasından geriye (ana yol sırasıyla en çok 3 oda, dar bölümde 5) taban taranır; bir otağ yeri = 3 sütun düz,
## katı taban, üstünde 5 karo hava (tehlike / platform / kuyu ağzı değil), oda kenarından 2 karo içeride. Çıkış odasında
## yalnızca kapıya YAKLAŞILAN yanda ve kapıdan en az KAPI_PAY karo uzakta (Kut Kapısı önü boş kalır). Otağlar arası en az
## ARALIK karo (Han Otağı'nın yanı HAN_ARALIK); Kut Taşı, kaide, ödül işareti ve zamanlı kapının çevresi boş. En çok 4 yer: [0] Kut Kapısı'na en yakın
## (Han Otağı), sonra Çabuk, Dokunulmaz, Avcı (oyuncu kapıya giderken önce Avcı'nın otağını görür). Otağlar dünyada
## arka plandır (çarpışmasız): erişimi ve dönüşü değiştirmez.

const KAPI_PAY := 5
const ARALIK := 3      # küçük otağlar yan yana (68 birim genişlik, 72 birim aralık)
const HAN_ARALIK := 4  # Han Otağı (88 birim) ile komşusu
const BOS_UST := 5
const SIRA := ["han", "cabuk", "dokunulmaz", "avci"]


static func yerlesim(g: PackedByteArray, W: int, H: int, rooms: Array, exit: Vector2i, avoid: Array) -> Array:
	## Döndürür: [{x, y (ayakta durulan hava satırı), oda, sira}] (yakından uzağa). Önce sıkı kural, 4 yer çıkmazsa
	## gevşek (kapı payı 4, Han'ın yanı da 3).
	var r := _yerlesim(g, W, H, rooms, exit, avoid, ARALIK, KAPI_PAY, HAN_ARALIK, 3)
	if r.size() < 4:
		var r2 := _yerlesim(g, W, H, rooms, exit, avoid, ARALIK, 4, ARALIK, 3)
		if r2.size() > r.size():
			r = r2
	if r.size() < 4:
		# dar bölüm (kuyulu iniş / mağara): kapıya giden yolda iki oda daha geriye bakılır
		var r3 := _yerlesim(g, W, H, rooms, exit, avoid, ARALIK, 4, ARALIK, 5)
		if r3.size() > r.size():
			r = r3
	if r.size() < 4:
		# v42 birleştirme: düz tabanı az mağara / iniş bölümü (hikâye odası düzeni değiştirince): yol boyunca 8 odaya kadar
		var r4 := _yerlesim(g, W, H, rooms, exit, avoid, ARALIK, 3, ARALIK, 8)
		if r4.size() > r.size():
			r = r4
	return r


static func _ana(rooms: Array) -> Array:
	var out: Array = []
	for rm in rooms:
		if int(rm.get("ana_i", -1)) >= 0 and rm["role"] != "yok":
			out.append(rm)
	out.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return int(a["ana_i"]) > int(b["ana_i"]))
	return out


static func _yerlesim(g: PackedByteArray, W: int, H: int, rooms: Array, exit: Vector2i, avoid: Array, aralik: int, kapi_pay: int, han_aralik: int, oda_say: int) -> Array:
	var ana := _ana(rooms)
	var out: Array = []
	if ana.is_empty():
		return out
	var cands: Array = []   # [puan, x, y, oda id]
	for ri in mini(oda_say, ana.size()):
		var rm: Dictionary = ana[ri]
		var ix0 := int(rm["ix0"])
		var ix1 := int(rm["ix1"])
		var fl: Array = rm["fl"]
		if fl.is_empty():
			continue
		var cikis := ri == 0 and String(rm["role"]) == "cikis"
		var sag_sonra := true   # sonraki (kapıya yakın) oda sağda mı
		if ri > 0:
			var nx: Dictionary = ana[ri - 1]
			sag_sonra = (int(nx["ix0"]) + int(nx["ix1"])) >= (ix0 + ix1)
		for x in range(ix0 + 2, ix1 - 1):
			if cikis:
				var yon := 1 if bool(rm.get("cikis_sol", false)) else -1   # kapıya yaklaşılan yan (+1: kapının sağı)
				if (x - exit.x) * yon < kapi_pay:
					continue
			var fy: int = int(fl[x - ix0])
			var ok := true
			for dx in [-1, 0, 1]:
				var cx: int = x + dx
				if cx < ix0 or cx > ix1 or int(fl[cx - ix0]) != fy or LevelGen._cell(g, cx, fy, W, H) != 1:
					ok = false
					break
				for h in range(1, BOS_UST + 1):
					if LevelGen._cell(g, cx, fy - h, W, H) != 0:
						ok = false
						break
				if not ok:
					break
			if not ok:
				continue
			for a in avoid:
				var av: Vector2i = a
				if absi(av.x - x) < 3 and absi(av.y - (fy - 1)) < 4:
					ok = false
					break
			if not ok:
				continue
			var puan := 0.0
			if cikis:
				puan = float(absi(x - exit.x))
			else:
				puan = 100.0 * ri + float(ix1 - x if sag_sonra else x - ix0)
			cands.append([puan, x, fy - 1, int(rm.get("id", -1))])
	cands.sort_custom(func(a: Array, b: Array) -> bool: return float(a[0]) < float(b[0]))
	for c in cands:
		var ok2 := true
		for s in out:
			var ar := han_aralik if int(s["sira"]) == 0 else aralik
			if absi(int(s["x"]) - int(c[1])) < ar and absi(int(s["y"]) - int(c[2])) < 6:
				ok2 = false
				break
		if ok2:
			out.append({"x": int(c[1]), "y": int(c[2]), "oda": int(c[3]), "sira": out.size()})
			if out.size() >= 4:
				break
	return out


# ------------------------------------------------------------------ Çabuk sınavının süresi
const KOSU_KARO := 6.46     # yürüme 155 px/sn (Player.RUN)
const PAR_TABAN := 30.0     # sn: kapıyı / otağları görme, ilk dövüş
const PAR_YOL := 2.0        # yolun koşu süresinin katı (dövüşerek ilerleme)
const PAR_ODA := 5.0        # ana yol odası başına (kalabalık oda; v34 yoğunluğu)
const PAR_DERIN := 2.0      # derinlik başına (derin yaratıklar daha dayanıklı)


static func yol_suresi(g: PackedByteArray, W: int, H: int, spawn: Vector2i, exit: Vector2i) -> float:
	## Girişten Kut Kapısı'na model hamleleriyle (LevelGen._moves) en kısa yolun koşu süresi (sn): yatay karo / koşu hızı +
	## dikey karo x 0,12 sn. Yol yoksa -1.
	var gh := LevelGen._haz_as_air(g)
	var par := PackedInt32Array()
	par.resize(W * H)
	par.fill(-2)
	var s0 := spawn.y * W + spawn.x
	var goal := exit.y * W + exit.x
	par[s0] = -1
	var q: Array = [s0]
	var qi := 0
	var found := false
	while qi < q.size():
		var id: int = q[qi]
		qi += 1
		if id == goal:
			found = true
			break
		for n in LevelGen._moves(gh, W, H, id % W, id / W):
			if par[n] != -2:
				continue
			par[n] = id
			q.append(n)
	if not found:
		# kapı hücresi model hamleleriyle tam tutturulamadıysa: en yakın ulaşılan hücre
		var best := -1
		var bd := 1 << 30
		for id2 in q:
			var d := absi(int(id2) % W - exit.x) + absi(int(id2) / W - exit.y) * 2
			if d < bd:
				bd = d
				best = int(id2)
		if best < 0 or bd > 6:
			return -1.0
		goal = best
	var yat := 0
	var dik := 0
	var c := goal
	while par[c] >= 0:
		var p: int = par[c]
		yat += absi(c % W - p % W)
		dik += absi(c / W - p / W)
		c = p
	return float(yat) / KOSU_KARO + float(dik) * 0.12


static func par_sure(yol_sn: float, ana_oda: int, derinlik: int) -> float:
	## Çabuk sınavının süresi (sn): 30 + yol x 2 + oda x 5 + derinlik x 2; 5'e yuvarlanır, 75-240 sn
	var s := PAR_TABAN + maxf(10.0, yol_sn) * PAR_YOL + float(ana_oda) * PAR_ODA + float(derinlik) * PAR_DERIN
	return clampf(round(s / 5.0) * 5.0, 75.0, 240.0)
