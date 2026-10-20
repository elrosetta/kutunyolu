class_name LevelGen
extends RefCounted
## v32 bölüm üretimi: Dead Cells tarzı oda çizgesi (eskiden soldan sağa tek yüzey + parçalar).
##
## Bölüm, SW x SH karolık "kesim"lerden (sektör) oluşan bir ızgaradır (stil başına sütun / satır sayısı STIL'de).
## Önce ÇİZGE kurulur: giriş kesimi (sol sütun) -> çıkış kesimi (sağ sütun) arasında yukarı / aşağı da kıvrılan bir
## ANA YOL; ana yoldan ayrılan 3-6 DAL (1-3 oda; sonu ÇIKMAZ ödül odası: tomar, hazine, sunak, pazar, seçkin
## bekçisi, zamanlı kapı); komşu odalar arasında DÖNGÜ kapıları; yan yana / üst üste odaların birleşip geniş salon ya da
## yüksek kuyu olması. Sonra her odanın içi türüne göre oyulur (salon, teras, çukur, mağara, kuyu, kule, köprü,
## harabe), kapılar duvara açılır: yan kapıların iki yanında iniş sekisi (6 karo düz), zemin sekiden 4 karodan
## alçaksa zikzak tek yönlü basamaklar (merdiven); dikey kapılar üst odanın tabanından alt odaya 6 karolık kuyu ve
## alt odada tabandan kuyuya tırmanan zikzak basamaklar. Kut Taşları (ışınlanma) giriş odasına, dallanma
## kavşaklarına ve çıkmaz ödül odalarına konur.
##
## Izgara değerleri: 0 hava, 1 katı, 2 tek yönlü platform, 3 tehlike. v25 kuralları korunur: yürünen her hücrede
## en az BAS_BOSLUGU (3) karo baş boşluğu (_open_headroom), yalnızca yuvarlanarak geçilen yer yok. Erişim modeli
## (_moves: tek / çift zıplama en çok 4 karo yukarı, ±5 sütun; düşüş 15 satır) ile girişten çıkışa yol ve her
## ulaşılan hücreden çıkışa dönüş (traps / fix_traps) denetlenir; geçmeyen taslak yeniden üretilir.
##
## generate(...) döndürür: grid, heights (ana yol odasının tabanı; eski surface_y için), style, chunks (ödül odası
## işaretleri: Level._place_rooms), rooms, doors, path (ana yol oda kimlikleri), spawn / exit (karo), tasi (Kut Taşı
## karoları), zamanli (zamanlı kapı sütunları), kaide (eşya kaidesi sütunları), bounds, metrics.

const STYLES := ["orman", "ucurum", "magara", "harabe", "bozkir", "kuyu"]
## v25: yürünen hücrelerin üstünde açık kalması gereken en az karo (ayakta durulan karo dahil; 3 karo = 72 px)
const BAS_BOSLUGU := 3
## Kesim (sektör) boyu: duvarlar dahil; iç alan (SW - 4) x (SH - 4) = 32 x 18 karo (yaklaşık bir ekran)
const SW := 36
const SH := 22
const KENAR := 2

## Stil parametreleri: kesim ızgarası (sütun x satır), gök açık mı (üst satır odalarının tavanı yok), ana yolun yönü
## (inis: giriş üstte / çıkış altta; cikis: tersi; serbest), oda türü havuzu, dallanma / döngü / birleşme eğilimleri
const STIL := {
	"orman": {"cols": 7, "rows": 3, "acik": true, "yon": "inis", "kinds": ["salon", "teras", "kopru", "salon", "cukur", "harabe"],
		"dal": [3, 5], "dongu": 0.35, "genis": 0.3, "yuksek": 0.15, "tavan": 0},
	"ucurum": {"cols": 6, "rows": 4, "acik": true, "yon": "inis", "kinds": ["teras", "kopru", "kule", "cukur", "teras", "salon"],
		"dal": [3, 5], "dongu": 0.3, "genis": 0.15, "yuksek": 0.35, "tavan": 0},
	"magara": {"cols": 6, "rows": 4, "acik": false, "yon": "inis", "kinds": ["magara", "magara", "kuyu", "cukur", "salon", "magara"],
		"dal": [4, 6], "dongu": 0.4, "genis": 0.2, "yuksek": 0.3, "tavan": 4},
	"harabe": {"cols": 6, "rows": 4, "acik": false, "yon": "serbest", "kinds": ["harabe", "kule", "salon", "kuyu", "kopru", "harabe"],
		"dal": [3, 6], "dongu": 0.35, "genis": 0.25, "yuksek": 0.3, "tavan": 2},
	"bozkir": {"cols": 7, "rows": 2, "acik": true, "yon": "serbest", "kinds": ["salon", "teras", "salon", "cukur", "kopru", "harabe"],
		"dal": [3, 4], "dongu": 0.4, "genis": 0.45, "yuksek": 0.1, "tavan": 0},
	"kuyu": {"cols": 5, "rows": 4, "acik": false, "yon": "inis", "kinds": ["kuyu", "magara", "kule", "cukur", "kopru", "kuyu"],
		"dal": [3, 5], "dongu": 0.3, "genis": 0.1, "yuksek": 0.45, "tavan": 3},
}

## Çıkmaz ödülleri (öncelik sırası; pazar istenirse başa eklenir). tomar: Kut Tomarı kaidesi; hazine: üst kademe
## eşya + altın (yükseltilmiş seki); sunak: tanrı lütfu; seckin: seçkin bekçi + eşya; zamanli: bölüm başından 90 sn
## içinde ulaşılırsa açık kalan kapı, ardında üst kademe eşya + altın
const ODULLER := ["tomar", "hazine", "sunak", "seckin", "zamanli", "tomar", "hazine"]
const ZAMANLI_SURE := 90.0

## Eski parça sözlüğü: ödül odası işaretleri (Level._place_rooms, tuccar_testi; "T" hazine kaidesi, "S" sunak, "E" seçkin,
## "M" tomar kaidesi, "P" pazar tezgâhı, "Z" zamanlı kapı ödülü)
const CHUNKS := {
	"hazine": ["   T   "],
	"sunak": ["   S   "],
	"seckin": ["  E T  "],
	"tomar": ["   M   "],
	"pazar": ["   P   "],
	"zamanli": ["   Z   "],
}

## Son üretimin giriş / çıkış hücresi (eski imzalı reach_set / traps / _reachable sarmalayıcıları için)
static var _son := {"sx": 5, "sy": 30, "gx": 250, "gy": 30}


static func generate(rng: RandomNumberGenerator, W: int, H: int, depth: int, allowed: Array = [], opts: Dictionary = {}) -> Dictionary:
	## Döndürür: bkz. dosya başı. opts: pazar (tüccar odası istensin), pazar_kapi (çıkışa yakın), rows / yon ezmesi.
	var pool: Array = allowed if not allowed.is_empty() else STYLES
	var style: String = pool[rng.randi_range(0, pool.size() - 1)]
	if depth == 1 and rng.randf() < 0.5:
		style = "orman"
	var best: Dictionary = {}
	var best_bad := 999999
	for attempt in 12:
		var r := _build(rng, W, H, style, opts)
		_son = {"sx": r["spawn"].x, "sy": r["spawn"].y, "gx": r["exit"].x, "gy": r["exit"].y}
		r["style"] = style
		r["carved"] = 0
		r["trapfix"] = 0
		r["headfix"] = 0
		var ok := false
		for round in 3:
			r["headfix"] = int(r["headfix"]) + _open_headroom(r["grid"], W, H, BAS_BOSLUGU)
			var reach := _reach(_haz_as_air(r["grid"]), W, H, r["heights"])
			if not reach["ok"]:
				break
			r["trapfix"] = int(r["trapfix"]) + fix_traps(r["grid"], W, H, r["heights"])
			r["headfix"] = int(r["headfix"]) + _open_headroom(r["grid"], W, H, BAS_BOSLUGU)
			if _reachable(r["grid"], W, H, r["heights"]) and traps(_haz_as_air(r["grid"]), W, H, r["heights"], r["grid"]).is_empty():
				ok = true
				break
		var bad := 0 if ok else (traps(_haz_as_air(r["grid"]), W, H, r["heights"], r["grid"]).size() + (0 if _reachable(r["grid"], W, H, r["heights"]) else 100000))
		r["attempts"] = attempt + 1
		if ok:
			best = r
			break
		if bad < best_bad:
			best_bad = bad
			best = r
	_son = {"sx": best["spawn"].x, "sy": best["spawn"].y, "gx": best["exit"].x, "gy": best["exit"].y}
	best["metrics"]["ok"] = _reachable(best["grid"], W, H, best["heights"]) and traps(_haz_as_air(best["grid"]), W, H, best["heights"], best["grid"]).is_empty()
	best["metrics"]["attempts"] = int(best.get("attempts", 1))
	best["metrics"]["trapfix"] = int(best.get("trapfix", 0))
	return best


static func _idx(x: int, y: int, W: int) -> int:
	return y * W + x


static func _put(g: PackedByteArray, x: int, y: int, W: int, H: int, v: int) -> void:
	if x >= 0 and x < W and y >= 0 and y < H:
		g[y * W + x] = v


static func _cell(g: PackedByteArray, x: int, y: int, W: int, H: int) -> int:
	if x < 0 or x >= W or y < 0 or y >= H:
		return 1
	return g[y * W + x]


# ================================================================== çizge
static func _build(rng: RandomNumberGenerator, W: int, H: int, style: String, opts: Dictionary) -> Dictionary:
	var P: Dictionary = STIL[style]
	var cols := mini(int(P["cols"]), (W - 2 * KENAR) / SW)
	var rows := mini(int(opts.get("rows", P["rows"])), (H - 2 * KENAR) / SH)
	var yon := String(opts.get("yon", P["yon"]))
	var grid := PackedByteArray()
	grid.resize(W * H)
	grid.fill(1)
	# --- kesim ızgarası ve ana yol
	var sr := 0
	var er := rows - 1
	match yon:
		"cikis":
			sr = rows - 1
			er = 0
		"serbest":
			sr = rng.randi_range(0, rows - 1)
			er = rng.randi_range(0, rows - 1)
			if rows > 1 and er == sr and rng.randf() < 0.7:
				er = (sr + 1 + rng.randi_range(0, rows - 2)) % rows
	var path := _ana_yol(rng, cols, rows, sr, er, yon)
	var owner: Array = []   # [c][r] -> oda kimliği
	for c in cols:
		var col: Array = []
		for r in rows:
			col.append(-1)
		owner.append(col)
	var rooms: Array = []
	var doors: Array = []
	for i in path.size():
		var cell: Vector2i = path[i]
		var role := "ana"
		if i == 0:
			role = "giris"
		elif i == path.size() - 1:
			role = "cikis"
		var id := _new_room(rooms, owner, cell, role)
		rooms[id]["ana_i"] = i
		if i > 0:
			_add_door(doors, rooms, owner, path[i - 1], cell, "ana")
	# --- dallar: kavşaklardan boş kesimlere 1-3 odalık yürüyüş, sonu çıkmaz (ödül)
	# ödül sırası: tomar ve hazine kesin, kalanı (sunak / seçkin / zamanlı) karışık; pazar istenirse en başa
	var oduller: Array = ["tomar", "hazine"]
	var rest: Array = ["sunak", "seckin", "zamanli"]
	_shuffle(rng, rest)
	oduller.append_array(rest)
	oduller.append_array(["tomar", "hazine"])
	if bool(opts.get("pazar", false)):
		oduller.push_front("pazar")
	var dal_n: int = rng.randi_range(int(P["dal"][0]), int(P["dal"][1]))
	var junctions: Array = []
	for i in range(1, path.size() - 1):
		junctions.append(i)
	if bool(opts.get("pazar", false)) and bool(opts.get("pazar_kapi", false)):
		# boss öncesi: pazar çıkışa yakın kavşaktan ayrılır
		junctions.reverse()
	else:
		_shuffle(rng, junctions)
	# yedek kavşaklar: çıkış ve giriş odası (ara odalardan dal çıkmazsa; en az 2 çıkmaz için)
	junctions.append(path.size() - 1)
	junctions.append(0)
	var n_dal := 0
	var n_cikmaz := 0
	for ji in junctions:
		if n_dal >= dal_n:
			break
		var cur: Vector2i = path[ji]
		var chain: Array = []
		var ln := 1 + (1 if rng.randf() < 0.45 else 0) + (1 if rng.randf() < 0.25 else 0)
		var prev := cur
		for step in ln:
			var opts2: Array = []
			for d in [Vector2i(0, -1), Vector2i(0, 1), Vector2i(1, 0), Vector2i(-1, 0)]:
				var n: Vector2i = prev + d
				if n.x < 0 or n.x >= cols or n.y < 0 or n.y >= rows or owner[n.x][n.y] >= 0:
					continue
				# dikey dal tercih edilir (derinlik hissi); giriş sütununa dal uzanmasın
				var w := 2 if d.y != 0 else 1
				for k in w:
					opts2.append(n)
			if opts2.is_empty():
				break
			var nxt: Vector2i = opts2[rng.randi_range(0, opts2.size() - 1)]
			var id := _new_room(rooms, owner, nxt, "dal")
			_add_door(doors, rooms, owner, prev, nxt, "dal")
			chain.append(id)
			prev = nxt
		if chain.is_empty():
			continue
		n_dal += 1
		rooms[int(owner[cur.x][cur.y])]["kavsak"] = true
		var last: int = chain[chain.size() - 1]
		rooms[last]["role"] = "odul"
		rooms[last]["odul"] = String(oduller.pop_front()) if not oduller.is_empty() else "hazine"
		rooms[last]["dal_uz"] = chain.size()
		n_cikmaz += 1
	# --- döngüler: kapısız komşu odalar arasında (ödül odaları tek kapılı kalır)
	var n_dongu := 0
	for c in cols:
		for r in rows:
			var a: int = owner[c][r]
			if a < 0 or rooms[a]["role"] == "odul":
				continue
			for d in [Vector2i(1, 0), Vector2i(0, 1)]:
				var n: Vector2i = Vector2i(c, r) + d
				if n.x >= cols or n.y >= rows:
					continue
				var b: int = owner[n.x][n.y]
				if b < 0 or b == a or rooms[b]["role"] == "odul" or _has_door(doors, a, b):
					continue
				if rng.randf() < float(P["dongu"]):
					_add_door(doors, rooms, owner, Vector2i(c, r), n, "dongu")
					n_dongu += 1
	# --- birleşme: yan yana geniş salon, üst üste yüksek kuyu / kule (ödül odaları ve giriş birleşmez)
	var n_genis := 0
	var n_yuksek := 0
	for i in range(path.size() - 1):
		var a: Vector2i = path[i]
		var b: Vector2i = path[i + 1]
		var ra: int = owner[a.x][a.y]
		var rb: int = owner[b.x][b.y]
		if ra == rb or rooms[ra]["role"] == "giris" or (rooms[ra]["cells"] as Array).size() > 1 or (rooms[rb]["cells"] as Array).size() > 1:
			continue
		if b.y == a.y and rng.randf() < float(P["genis"]):
			_merge(rooms, owner, doors, ra, rb)
			n_genis += 1
		elif b.x == a.x and rng.randf() < float(P["yuksek"]):
			_merge(rooms, owner, doors, ra, rb)
			n_yuksek += 1
	# --- oda türleri ve taban seviyeleri
	var kinds: Array = P["kinds"]
	for rm in rooms:
		_room_rect(rm)
		var role: String = rm["role"]
		if role == "yok":
			continue
		var cells: Array = rm["cells"]
		var tall: bool = cells.size() > 1 and cells[0].x == cells[1].x
		var wide: bool = cells.size() > 1 and cells[0].y == cells[1].y
		if role == "odul":
			rm["kind"] = "odul"
			rm["fb"] = int(rm["iy1"]) - 2
		elif role == "giris":
			rm["kind"] = "salon"
			rm["fb"] = int(rm["iy1"]) - rng.randi_range(1, 3)
		elif tall:
			rm["kind"] = ["kuyu", "kule"][rng.randi_range(0, 1)] if style != "orman" else "kule"
			rm["fb"] = int(rm["iy1"]) - rng.randi_range(0, 2)
		elif wide:
			rm["kind"] = ["salon", "harabe", "teras", "kopru"][rng.randi_range(0, 3)]
			rm["fb"] = int(rm["iy1"]) - rng.randi_range(1, 4)
		else:
			rm["kind"] = String(kinds[rng.randi_range(0, kinds.size() - 1)])
			rm["fb"] = int(rm["iy1"]) - rng.randi_range(0, 6)
		if rm["kind"] in ["kopru", "cukur"]:
			rm["fb"] = int(rm["iy1"]) - rng.randi_range(5, 6)
		if role == "cikis":
			rm["fb"] = int(rm["iy1"]) - rng.randi_range(0, 3)
		rm["acik"] = bool(P["acik"]) and int(rm["r0"]) == 0
		rm["flat"] = []
		rm["clear"] = []
		rm["ladder"] = []
		rm["landing"] = []
	# --- oda genişliği çeşitliliği: kapısız yanlarda iç alan 0-5 karo daralır (kalın duvar); ödül odaları 2-6
	for rm in rooms:
		if rm["role"] == "yok":
			continue
		var has_l := false
		var has_r := false
		for di in rm["doors"]:
			var d: Dictionary = doors[di]
			if d["dir"] != "h":
				has_l = true   # dikey kapılı oda tam genişlikte kalır (kuyu ağzı yeri)
				has_r = true
				continue
			if int(d["b"]) == int(rm["id"]):
				has_l = true
			if int(d["a"]) == int(rm["id"]):
				has_r = true
		var odul: bool = rm["role"] == "odul"
		if not has_l:
			rm["ix0"] = int(rm["ix0"]) + (rng.randi_range(2, 6) if odul else rng.randi_range(0, 5))
		if not has_r:
			rm["ix1"] = int(rm["ix1"]) - (rng.randi_range(2, 6) if odul else rng.randi_range(0, 5))
	# --- kapı yükseklikleri ve iniş sekileri
	for dr in doors:
		_door_geometry(rng, rooms, dr)
	# pazar dikey kapılı odaya düştüyse yan kapılı başka bir ödül odasıyla yer değiştirir (tüccar istendiyse kaybolmasın;
	# boss öncesi Bezirgân kesin). Yan kapılı ödül odası yoksa kuyulu odada kalır: tezgâh _odul_mid ile kuyudan uzak yana
	# kurulur (mid-5..mid+4; kuyu bölgesi hx-2..hx+7 dışında).
	for rm in rooms:
		if rm["role"] == "odul" and String(rm["odul"]) == "pazar" and String(rm.get("_door_side", "sol")) in ["ust", "alt"]:
			for rm2 in rooms:
				if rm2["role"] == "odul" and rm2 != rm and not (String(rm2.get("_door_side", "sol")) in ["ust", "alt"]):
					rm["odul"] = rm2["odul"]
					rm2["odul"] = "pazar"
					break
			break
	for rm in rooms:
		# zamanlı kapı yalnızca yan kapılı odada (dikey kuyuya kapı kurulmaz)
		if rm["role"] == "odul" and String(rm.get("_door_side", "sol")) in ["ust", "alt"] and String(rm["odul"]) == "zamanli":
			rm["odul"] = "hazine"
	# --- oyma
	for rm in rooms:
		if rm["role"] != "yok":
			_profile(rng, rm, style, int(P["tavan"]))
	for rm in rooms:
		if rm["role"] != "yok":
			_carve_room(grid, W, H, rng, rm)
	for rm in rooms:
		if rm["role"] != "yok":
			_features(grid, W, H, rng, rm, style)
	for rm in rooms:
		if rm["role"] != "yok":
			_carve_landings(grid, W, H, rm)
	for dr in doors:
		_carve_door(grid, W, H, rooms, dr)
	for rm in rooms:
		if rm["role"] == "yok":
			continue
		for ld in rm["ladder"]:
			_ladder(grid, W, H, int(ld[0]), int(ld[1]), int(ld[2]))
	_open_cliffs(grid, W, H, rooms, owner, cols, rows)
	# --- işaretler, tehlikeler, Kut Taşları, kaideler
	var chunks: Array = []
	var zamanli: Array = []
	var tasi: Array = []
	var kaide: Array = []
	var main_rooms: Array = []
	for rm in rooms:
		if int(rm.get("ana_i", -1)) >= 0 and rm["role"] != "yok":
			main_rooms.append(rm)
	main_rooms.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return int(a["ana_i"]) < int(b["ana_i"]))
	for rm in rooms:
		if rm["role"] == "odul":
			var mk := _odul_marks(grid, W, H, rng, rm, zamanli)
			chunks.append({"name": String(rm["odul"]), "x": int(rm["ix0"]), "marks": mk, "room": int(rm["id"])})
		elif rm["role"] in ["ana", "dal"]:
			_hazard_strips(grid, W, H, rng, rm, style)
	# giriş: Kut Taşı girişin 7 karo sağında; kavşaklar; ödül odaları (kapıya yakın) -> en çok 6
	var g_rm: Dictionary = rooms[0]
	var spawn := Vector2i(int(g_rm["ix0"]) + 3, int(g_rm["fl"][3]) - 1)
	tasi.append(_floor_spot(grid, W, H, g_rm, int(g_rm["ix0"]) + 9))
	for rm in rooms:
		if rm["role"] == "odul" and tasi.size() < 6:
			tasi.append(_odul_tasi(grid, W, H, rm))
	for rm in main_rooms:
		if bool(rm.get("kavsak", false)) and tasi.size() < 6 and rm["role"] == "ana":
			var sp := _floor_spot(grid, W, H, rm, (int(rm["ix0"]) + int(rm["ix1"])) / 2)
			var far := true
			for t in tasi:
				if absi(int(t.x) - sp.x) < 20 and absi(int(t.y) - sp.y) < 12:
					far = false
			if far:
				tasi.append(sp)
	# eşya kaideleri: ana yolun 1/4, 2/4, 3/4'ündeki odaların ortası
	var nm := main_rooms.size()
	for q in [0.25, 0.5, 0.75]:
		var rm: Dictionary = main_rooms[clampi(int(round(q * (nm - 1))), 1, nm - 1)]
		kaide.append(_floor_spot(grid, W, H, rm, (int(rm["ix0"]) + int(rm["ix1"])) / 2 + rng.randi_range(-4, 4)))
	# çıkış: çıkış odasının sağ ucu
	var e_rm: Dictionary = main_rooms[nm - 1]
	var exit := _floor_spot(grid, W, H, e_rm, int(e_rm["ix1"]) - 4)
	# heights: sütundaki ana yol odasının (ilk gelinen) tabanı; eski surface_y / süs / test çağrıları için
	var heights: Array = []
	heights.resize(W)
	heights.fill(H - 3)
	for i in range(main_rooms.size() - 1, -1, -1):
		var rm: Dictionary = main_rooms[i]
		for x in range(int(rm["ix0"]), int(rm["ix1"]) + 1):
			heights[x] = int(rm["fl"][x - int(rm["ix0"])])
	for x in range(0, int(rooms[0]["ix0"])):
		heights[x] = heights[int(rooms[0]["ix0"])]
	for x in range(int(e_rm["ix1"]) + 1, W):
		heights[x] = heights[int(e_rm["ix1"])]
	# giriş düzlüğü garantisi
	for x in range(int(g_rm["ix0"]), int(g_rm["ix0"]) + 8):
		var fy: int = int(g_rm["fl"][x - int(g_rm["ix0"])])
		for y in range(maxi(1, fy - 5), fy):
			_put(grid, x, y, W, H, 0)
		_put(grid, x, fy, W, H, 1)
	var dikey_adim := 0
	var rmin := rows
	var rmax := 0
	for i in range(1, path.size()):
		if path[i].y != path[i - 1].y:
			dikey_adim += 1
	for rm in rooms:
		rmin = mini(rmin, int(rm["r0"]))
		rmax = maxi(rmax, int(rm["r1"]))
	var metrics := {"oda": rooms.size(), "ana": path.size(), "dal": n_dal, "cikmaz": n_cikmaz, "dongu": n_dongu,
		"genis": n_genis, "yuksek": n_yuksek, "dikey_adim": dikey_adim, "satir": rmax - rmin + 1, "kapi": doors.size(),
		"tasi": tasi.size(), "zamanli": zamanli.size(), "cols": cols, "rows": rows}
	var bounds := Rect2i(0, 0, KENAR + cols * SW + KENAR, KENAR + rows * SH + KENAR)
	return {"grid": grid, "heights": heights, "chunks": chunks, "rooms": rooms, "doors": doors, "path": path, "spawn": spawn,
		"exit": exit, "tasi": tasi, "zamanli": zamanli, "kaide": kaide, "bounds": bounds, "metrics": metrics}


static func _shuffle(rng: RandomNumberGenerator, a: Array) -> void:
	for i in range(a.size() - 1, 0, -1):
		var j := rng.randi_range(0, i)
		var t = a[i]
		a[i] = a[j]
		a[j] = t


static func _ana_yol(rng: RandomNumberGenerator, cols: int, rows: int, sr: int, er: int, yon: String) -> Array:
	## Giriş (0, sr) -> çıkış (cols-1, er): sağa ve dikey adımlar; hedef uzunluk sütun + satır + 0-2
	var path: Array = [Vector2i(0, sr)]
	var seen := {Vector2i(0, sr): true}
	var c := 0
	var r := sr
	# hedef uzunluk: sütun + satır (+0-2); 2 satırlı ızgarada (bozkır) dallara yer kalsın diye kısa
	var target := cols + rows + rng.randi_range(0, 2) if rows > 2 else cols + 1
	var guard := 0
	var last_dikey := false
	var dikey_n := 0
	var max_dikey := 2 if rows <= 2 else rows + 1   # 2 satırda en çok 2 dikey adım: kesimler dallara kalsın
	while not (c == cols - 1 and r == er) and guard < 200:
		guard += 1
		var opts: Array = []
		if c < cols - 1:
			var wr := 3
			if path.size() < target and rows > 1:
				wr = 2
			for k in wr:
				opts.append(Vector2i(c + 1, r))
		for dy in [-1, 1]:
			var n := Vector2i(c, r + dy)
			if n.y < 0 or n.y >= rows or seen.has(n):
				continue
			if (last_dikey or dikey_n >= max_dikey) and c < cols - 1:
				continue   # art arda iki dikey adım yok; dikey adım sayısı sınırlı (kesimler dallara kalsın)
			var w := 2
			if yon == "inis":
				w = 3 if dy > 0 else 1
			elif yon == "cikis":
				w = 3 if dy < 0 else 1
			if c == cols - 1:
				w = 4 if signi(er - r) == dy else 0
			elif path.size() >= target + 2:
				w = 1 if absi(n.y - er) < absi(r - er) else 0
			for k in w:
				opts.append(n)
		if opts.is_empty():
			break
		var nxt: Vector2i = opts[rng.randi_range(0, opts.size() - 1)]
		last_dikey = nxt.x == c
		if last_dikey:
			dikey_n += 1
		path.append(nxt)
		seen[nxt] = true
		c = nxt.x
		r = nxt.y
	return path


static func _new_room(rooms: Array, owner: Array, cell: Vector2i, role: String) -> int:
	var id := rooms.size()
	rooms.append({"id": id, "cells": [cell], "role": role, "odul": "", "ana_i": -1, "doors": [], "kavsak": false})
	owner[cell.x][cell.y] = id
	return id


static func _has_door(doors: Array, a: int, b: int) -> bool:
	for d in doors:
		if (int(d["a"]) == a and int(d["b"]) == b) or (int(d["a"]) == b and int(d["b"]) == a):
			return true
	return false


static func _add_door(doors: Array, rooms: Array, owner: Array, ca: Vector2i, cb: Vector2i, kind: String) -> void:
	## ca ile cb komşu kesimler; kapı yönü ca'dan cb'ye
	var a: int = owner[ca.x][ca.y]
	var b: int = owner[cb.x][cb.y]
	var d := {"a": a, "b": b, "ca": ca, "cb": cb, "dir": "h" if cb.y == ca.y else "v", "kind": kind, "x": 0, "y": 0}
	if d["dir"] == "h" and cb.x < ca.x:
		d = {"a": b, "b": a, "ca": cb, "cb": ca, "dir": "h", "kind": kind, "x": 0, "y": 0}
	elif d["dir"] == "v" and cb.y < ca.y:
		d = {"a": b, "b": a, "ca": cb, "cb": ca, "dir": "v", "kind": kind, "x": 0, "y": 0}
	doors.append(d)
	(rooms[a]["doors"] as Array).append(doors.size() - 1)
	(rooms[b]["doors"] as Array).append(doors.size() - 1)


static func _merge(rooms: Array, owner: Array, doors: Array, ra: int, rb: int) -> void:
	## rb odası ra'ya katılır; aralarındaki kapı silinir (kind "sil": geometri ve oyma atlar), rb'nin diğer kapıları
	## ra'ya bağlanır; çıkış rolü ve kavşaklık korunur, ana yol dizini küçüğü olur. rb "yok" rolüyle boş kalır.
	var rm_a: Dictionary = rooms[ra]
	var rm_b: Dictionary = rooms[rb]
	for cell in rm_b["cells"]:
		(rm_a["cells"] as Array).append(cell)
		owner[cell.x][cell.y] = ra
	for di in doors.size():
		var d: Dictionary = doors[di]
		if (int(d["a"]) == ra and int(d["b"]) == rb) or (int(d["a"]) == rb and int(d["b"]) == ra):
			d["kind"] = "sil"
			continue
		if int(d["a"]) == rb:
			d["a"] = ra
		if int(d["b"]) == rb:
			d["b"] = ra
	rm_a["doors"] = []
	for di in doors.size():
		var d: Dictionary = doors[di]
		if d["kind"] != "sil" and (int(d["a"]) == ra or int(d["b"]) == ra):
			(rm_a["doors"] as Array).append(di)
	if rm_b["role"] == "cikis":
		rm_a["role"] = "cikis"
	rm_a["ana_i"] = mini(int(rm_a["ana_i"]), int(rm_b["ana_i"]))
	rm_a["kavsak"] = bool(rm_a["kavsak"]) or bool(rm_b["kavsak"])
	rm_b["cells"] = []
	rm_b["doors"] = []
	rm_b["role"] = "yok"
	rm_b["ana_i"] = -1


static func _room_rect(rm: Dictionary) -> void:
	var cells: Array = rm["cells"]
	if cells.is_empty():
		rm["ix0"] = 0
		rm["ix1"] = 0
		rm["iy0"] = 0
		rm["iy1"] = 0
		rm["r0"] = 0
		rm["r1"] = 0
		rm["c0"] = 0
		rm["c1"] = 0
		return
	var c0 := 999
	var c1 := -1
	var r0 := 999
	var r1 := -1
	for cell in cells:
		c0 = mini(c0, cell.x)
		c1 = maxi(c1, cell.x)
		r0 = mini(r0, cell.y)
		r1 = maxi(r1, cell.y)
	rm["c0"] = c0
	rm["c1"] = c1
	rm["r0"] = r0
	rm["r1"] = r1
	rm["ix0"] = KENAR + c0 * SW + 2
	rm["ix1"] = KENAR + (c1 + 1) * SW - 3
	rm["iy0"] = KENAR + r0 * SH + 2
	rm["iy1"] = KENAR + (r1 + 1) * SH - 3


static func _sector_x0(c: int) -> int:
	return KENAR + c * SW


static func _sector_y0(r: int) -> int:
	return KENAR + r * SH


# ================================================================== kapılar
static func _door_geometry(rng: RandomNumberGenerator, rooms: Array, d: Dictionary) -> void:
	## Yan kapı: duvar sütunları (A'nın sağ duvarı + B'nin sol duvarı, 4 karo), yd taban satırı; iki odada iniş sekisi.
	## Dikey kapı: üst odanın (A) tabanından alt odaya (B) 6 karolık kuyu; alt odada basamaklar.
	if d["kind"] == "sil":
		return
	var A: Dictionary = rooms[int(d["a"])]
	var B: Dictionary = rooms[int(d["b"])]
	if d["dir"] == "h":
		var ca: Vector2i = d["ca"]
		var cb: Vector2i = d["cb"]
		var xw := _sector_x0(cb.x) - 2   # duvar başlangıcı (4 sütun: xw..xw+3)
		var y0 := _sector_y0(ca.y)
		var iy0 := y0 + 2
		var iy1 := y0 + SH - 3
		var fa := int(A["fb"])
		var fbv := int(B["fb"])
		var cands: Array = []
		if fa >= iy0 + 7 and fa <= iy1:
			for k in 4:
				cands.append(fa)
		if fbv >= iy0 + 7 and fbv <= iy1:
			for k in 3:
				cands.append(fbv)
		if A["role"] == "odul" and fa >= iy0 + 7 and fa <= iy1:
			cands = [fa]
		elif B["role"] == "odul" and fbv >= iy0 + 7 and fbv <= iy1:
			cands = [fbv]
		elif rng.randf() < 0.3 or cands.is_empty():
			cands.append(rng.randi_range(iy0 + 7, iy1))
		var yd: int = cands[rng.randi_range(0, cands.size() - 1)]
		d["x"] = xw
		d["y"] = yd
		_landing(A, "sag", yd, ca)
		_landing(B, "sol", yd, cb)
		if A["role"] == "odul":
			A["_door_side"] = "sag"
			A["_door_x"] = xw
		if B["role"] == "odul":
			B["_door_side"] = "sol"
			B["_door_x"] = xw
	else:
		var ca: Vector2i = d["ca"]
		var x0 := _sector_x0(ca.x)
		# kuyu ağzı (hx..hx+5; düz bölge hx-2..hx+7) iki odanın da yan kapı sekisi + merdiven bölgesine (10 sütun)
		# girmez: 32 karolık odada tam ortaya düşer, geniş odalarda serbest
		var lo := maxi(maxi(x0 + 12, int(A["ix0"]) + 12), int(B["ix0"]) + 11)
		var hi := mini(mini(x0 + SW - 3 - 19, int(A["ix1"]) - 19), int(B["ix1"]) - 15)
		var hx := rng.randi_range(lo, maxi(lo, hi))
		d["x"] = hx
		d["y"] = int(A["fb"])   # kesinleşmiş değer _carve_door'da A.fl'den okunur
		# üst oda: kuyu ağzının iki yanı düz, üstü açık
		(A["flat"] as Array).append([hx - 2, hx + 7, -1])   # -1: odanın doğal tabanı (fb)
		(A["clear"] as Array).append(Rect2i(hx - 2, int(A["iy0"]), 10, int(A["iy1"]) - int(A["iy0"]) + 1))
		# alt oda: kuyu altı boydan boya açık (basamaklar _carve_door'da)
		(B["clear"] as Array).append(Rect2i(hx - 1, int(B["iy0"]), 8, int(B["iy1"]) - int(B["iy0"]) + 1))
		(B["flat"] as Array).append([hx - 2, hx + 7, -1])
		B["ust_kapi"] = true
		if A["role"] == "odul":
			A["_door_side"] = "alt"
			A["_door_x"] = hx
		if B["role"] == "odul":
			B["_door_side"] = "ust"
			B["_door_x"] = hx


static func _landing(rm: Dictionary, side: String, yd: int, cell: Vector2i) -> void:
	## Kapının iç yanında 4 karo düz seki (taban yd): odanın tabanını değiştirmez, oda oyulduktan sonra duvara asılı
	## bir çıkıntı / tabana oyulmuş bir cep olarak kazılır (_carve_landings; yüksek odada aynı duvara iki kapı olabilir).
	## Odanın doğal tabanı sekiden 4 karodan alçaksa sekiye tırmanan merdiven (6 sütun: seki + merdiven = 10 sütun; kuyu
	## ağzı bölgesi 10: 32 karolık odaya ikisi de sığar); taban sekiden yüksekse tabana çıkan 2 karolık basamaklar.
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var fb := int(rm["fb"])
	(rm["landing"] as Array).append([side, yd])
	if side == "sol":
		(rm["clear"] as Array).append(Rect2i(ix0 - 2, yd - 7, 8, 9))
		if fb > yd + 4:
			(rm["clear"] as Array).append(Rect2i(ix0 + 3, yd - 5, 9, fb - yd + 5))
		elif fb < yd - 1:
			(rm["clear"] as Array).append(Rect2i(ix0 + 3, fb - 6, (yd - fb) / 2 + 2, yd - fb + 7))
	else:
		(rm["clear"] as Array).append(Rect2i(ix1 - 5, yd - 7, 8, 9))
		if fb > yd + 4:
			(rm["clear"] as Array).append(Rect2i(ix1 - 11, yd - 5, 9, fb - yd + 5))
		elif fb < yd - 1:
			(rm["clear"] as Array).append(Rect2i(ix1 - 4 - (yd - fb) / 2 - 1, fb - 6, (yd - fb) / 2 + 2, yd - fb + 7))


static func _carve_landings(g: PackedByteArray, W: int, H: int, rm: Dictionary) -> void:
	## Kapı sekileri: 4 sütunda yd-5..yd-1 hava, yd.. katı (taban yakınsa tabana dek dolu, uzaksa 2 karo kalın asılı
	## çıkıntı); doğal taban 4+ karo alçaksa merdiven, 2+ karo yüksekse tabana çıkan 2 karolık basamaklar
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var fl: Array = rm["fl"]
	for L in rm["landing"]:
		var side := String(L[0])
		var yd := int(L[1])
		var left := side == "sol"
		var cols: Array = range(ix0, ix0 + 4) if left else range(ix1 - 3, ix1 + 1)
		var inner := ix0 + 4 if left else ix1 - 4
		var dir := 1 if left else -1
		var fn: int = int(fl[clampi(inner - ix0, 0, fl.size() - 1)])
		var solid_to: int = yd + 1 if fn > yd + 4 else maxi(yd + 1, fn)
		for x in cols:
			for y in range(yd - 5, yd):
				_put(g, x, y, W, H, 0)
			for y in range(yd, solid_to + 1):
				_put(g, x, y, W, H, 1)
		if fn > yd + 4:
			_ladder(g, W, H, inner if left else inner - 5, yd, fn)
		elif fn < yd - 1:
			# tabana çıkan basamaklar: her sütunda taban 2 karo yükselir, üstünde 5 karo hava
			var t := yd
			var j := 0
			while t - 2 > fn and j < 10:
				t -= 2
				var col := inner + dir * j
				for y in range(t - 5, t):
					if _cell(g, col, y, W, H) == 1:
						_put(g, col, y, W, H, 0)
				for y in range(t, t + 2):
					_put(g, col, y, W, H, 1)
				j += 1


static func _carve_door(g: PackedByteArray, W: int, H: int, rooms: Array, d: Dictionary) -> void:
	if d["kind"] == "sil":
		return
	var A: Dictionary = rooms[int(d["a"])]
	var B: Dictionary = rooms[int(d["b"])]
	if d["dir"] == "h":
		var xw := int(d["x"])
		var yd := int(d["y"])
		for x in range(xw, xw + 4):
			for y in range(yd - 5, yd):
				_put(g, x, y, W, H, 0)
			for y in range(yd, yd + 4):
				_put(g, x, y, W, H, 1)
	else:
		var hx := int(d["x"])
		var fu: int = int(A["fl"][hx - int(A["ix0"])])
		d["y"] = fu
		var top_b := int(B["iy0"])
		for x in range(hx, hx + 6):
			for y in range(fu, top_b):
				_put(g, x, y, W, H, 0)
		# alt odanın tabanı kuyunun altında
		var fd: int = int(B["fl"][clampi(hx + 2 - int(B["ix0"]), 0, (B["fl"] as Array).size() - 1)])
		_ladder(g, W, H, hx, fu, fd)


static func _ladder(g: PackedByteArray, W: int, H: int, xa: int, y_hi: int, y_lo: int) -> void:
	## Zikzak tek yönlü basamaklar: xa..xa+5 sütunlarında, y_hi (varılacak taban satırı) + 3, +6, ... y_lo (alt taban)
	## satırına dek; en alt basamak alt tabana en çok 4 karo. Basamak alanı önce havaya açılır.
	if y_lo - y_hi < 3:
		return
	for x in range(xa - 1, xa + 7):
		for y in range(y_hi - 4, y_lo):
			if _cell(g, x, y, W, H) == 1:
				_put(g, x, y, W, H, 0)
	var rows: Array = []
	var y := y_hi + 3
	while y < y_lo - 1:
		rows.append(y)
		y += 3
	if not rows.is_empty() and y_lo - int(rows[rows.size() - 1]) > 4:
		rows.append(y_lo - 3)
	elif rows.is_empty() and y_lo - y_hi > 4:
		rows.append(y_lo - 3)
	for i in rows.size():
		var py: int = rows[i]
		var sx := xa if i % 2 == 0 else xa + 3
		for k in 3:
			_put(g, sx + k, py, W, H, 2)


# ================================================================== oda profilleri ve oyma
static func _profile(rng: RandomNumberGenerator, rm: Dictionary, style: String, tavan: int) -> void:
	## fl[x] taban satırı, ce[x] tavan satırı (iç sütunlar); düz bölgeler (sekiler) rampalarla bağlanır
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var iy0 := int(rm["iy0"])
	var iy1 := int(rm["iy1"])
	var n := ix1 - ix0 + 1
	var fb := int(rm["fb"])
	var kind: String = rm["kind"]
	var fl: Array = []
	var ce: Array = []
	fl.resize(n)
	ce.resize(n)
	var p1 := rng.randf() * TAU
	var p2 := rng.randf() * TAU
	# arazi parçaları: 2-4 bölümde taban seviyesi ±3 oynar (rampalar sütun başına 2 karo: zıplanarak çıkılır)
	var seg_lvl: Array = []
	var seg_end: Array = []
	if kind in ["salon", "harabe", "magara", "kuyu", "kule"] and rm["role"] != "giris":
		var x := 0
		var lvl := fb
		while x < n:
			var ln := rng.randi_range(8, 16)
			seg_lvl.append(lvl)
			seg_end.append(mini(n, x + ln))
			x += ln
			lvl = clampi(fb + rng.randi_range(-3, 1), iy0 + 8, iy1)
	var tavan_oda := rng.randi_range(0, 3) if (tavan > 0 and not bool(rm["acik"])) else 0
	for i in n:
		var v := fb
		var si := 0
		while si < seg_end.size() and i >= int(seg_end[si]):
			si += 1
		var base: int = int(seg_lvl[si]) if si < seg_lvl.size() else fb
		match kind:
			"salon", "kuyu", "kule":
				v = base + int(round(sin(i * 0.35 + p1) * 0.6))
			"odul", "kopru", "cukur", "teras":
				v = fb
			"magara":
				v = base + int(round(sin(i * 0.3 + p1) * 1.2 + sin(i * 0.11 + p2) * 1.4))
			"harabe":
				v = base + int(round(sin(i * 0.5 + p1) * 0.5))
		fl[i] = clampi(v, iy0 + 8, iy1)
		var cv := iy0
		if bool(rm["acik"]):
			cv = 1
		elif kind == "magara" or tavan > 0:
			cv = iy0 + tavan_oda + clampi(int(round((sin(i * 0.27 + p2) + 1.0) * 0.5 * (tavan + (2 if kind == "magara" else 0)))), 0, 6)
		ce[i] = cv
	if kind == "teras":
		# 7-11 sütunlu basamaklar; her basamak ±2..4 (iy0+8 .. iy1 arası)
		var x := 0
		var lvl := fb
		while x < n:
			var ln := rng.randi_range(7, 11)
			for k in range(x, mini(n, x + ln)):
				fl[k] = lvl
			x += ln
			var dlt := rng.randi_range(2, 4) * (1 if rng.randf() < 0.5 else -1)
			lvl = clampi(lvl + dlt, iy0 + 8, iy1)
	# düz bölgeler (kapı sekileri / kuyu ağızları): -1 = odanın doğal tabanı (fb)
	var flats: Array = rm["flat"]
	for f in flats:
		var y: int = int(f[2]) if int(f[2]) >= 0 else fb
		for x in range(int(f[0]), int(f[1]) + 1):
			var i := x - ix0
			if i >= 0 and i < n:
				fl[i] = y
	# rampalar: düz bölgeden dışarı doğru sütun başına en çok 2 karo
	var fixed := PackedByteArray()
	fixed.resize(n)
	fixed.fill(0)
	for f in flats:
		for x in range(int(f[0]), int(f[1]) + 1):
			var i := x - ix0
			if i >= 0 and i < n:
				fixed[i] = 1
	for i in range(1, n):
		if fixed[i] == 0 and absi(int(fl[i]) - int(fl[i - 1])) > 2:
			fl[i] = int(fl[i - 1]) + clampi(int(fl[i]) - int(fl[i - 1]), -2, 2)
	for i in range(n - 2, -1, -1):
		if fixed[i] == 0 and absi(int(fl[i]) - int(fl[i + 1])) > 2:
			fl[i] = int(fl[i + 1]) + clampi(int(fl[i]) - int(fl[i + 1]), -2, 2)
	for i in n:
		fl[i] = clampi(int(fl[i]), iy0 + 7, iy1)
		ce[i] = mini(int(ce[i]), int(fl[i]) - 7)
	rm["fl"] = fl
	rm["ce"] = ce


static func _carve_room(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rm: Dictionary) -> void:
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var fl: Array = rm["fl"]
	var ce: Array = rm["ce"]
	for x in range(ix0, ix1 + 1):
		var i := x - ix0
		for y in range(int(ce[i]), int(fl[i])):
			_put(g, x, y, W, H, 0)
		for y in range(int(fl[i]), int(rm["iy1"]) + 3):
			_put(g, x, y, W, H, 1)
	# yükseliş basamakları (odanın içinde 3-4 karo dik taban farkları: teraslar): alçak yanda 2 karoda bir platform.
	# 5+ karo farklar kapı sekisi uçurumlarıdır: oraya merdiven (_ladder) kurulur.
	for x in range(ix0, ix1):
		var i := x - ix0
		var a := int(fl[i])
		var b := int(fl[i + 1])
		if a - b >= 3 and a - b <= 4:
			_steps(g, W, H, x, a, b, -1)
		elif b - a >= 3 and b - a <= 4:
			_steps(g, W, H, x + 1, b, a, 1)


static func _steps(g: PackedByteArray, W: int, H: int, x_low: int, y_low: int, y_high: int, side: int) -> void:
	## x_low sütunu alçak tabanda (y_low), komşu sütun yüksek (y_high): alçak yanda 3 karolık platform basamakları
	var y := y_low - 2
	while y > y_high:
		for k in 3:
			var cx := x_low + side * k
			if _cell(g, cx, y, W, H) == 0:
				_put(g, cx, y, W, H, 2)
		y -= 2


static func _in_clear(rm: Dictionary, x: int, y: int) -> bool:
	for c in rm["clear"]:
		if (c as Rect2i).has_point(Vector2i(x, y)):
			return true
	return false


static func _free_span(g: PackedByteArray, W: int, H: int, rm: Dictionary, x0: int, y: int, ln: int, up: int, down: int) -> bool:
	## x0..x0+ln-1 sütunlarında y satırı ve üstünde up, altında down satır hava mı; temiz bölgeye girmiyor mu
	for x in range(x0 - 1, x0 + ln + 1):
		if x < int(rm["ix0"]) or x > int(rm["ix1"]):
			return false
		for yy in range(y - up, y + down + 1):
			if _cell(g, x, yy, W, H) != 0 or _in_clear(rm, x, yy):
				return false
	return true


static func _features(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rm: Dictionary, style: String) -> void:
	## Oda türüne göre iç parçalar: platformlar, adalar, sütunlar, kemerler, sarkıtlar, çukurlar, köprü, kuyu basamakları
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var iy0 := int(rm["iy0"])
	var iy1 := int(rm["iy1"])
	var fl: Array = rm["fl"]
	var ce: Array = rm["ce"]
	var n := ix1 - ix0 + 1
	var kind: String = rm["kind"]
	var role: String = rm["role"]
	if role == "odul":
		_odul_shape(g, W, H, rng, rm)
		return
	if role == "giris":
		_platforms(g, W, H, rng, rm, 2, 4, 5)
		return
	var wide: bool = (rm["cells"] as Array).size() > 1 and n > 40
	var kx := 2 if wide else 1
	match kind:
		"salon":
			_islands(g, W, H, rng, rm, rng.randi_range(1, 2) * kx)
			_platforms(g, W, H, rng, rm, rng.randi_range(4, 7) * kx, 4, 9)
			_wall_ledges(g, W, H, rng, rm, rng.randi_range(1, 2))
			_dips(g, W, H, rng, rm, rng.randi_range(0, 2) * kx)
			_alcoves(g, W, H, rng, rm, rng.randi_range(0, 2))
			_stalactites(g, W, H, rng, rm, rng.randi_range(0, 2) * kx, 4)
		"teras":
			_platforms(g, W, H, rng, rm, rng.randi_range(2, 4) * kx, 4, 7)
			_wall_ledges(g, W, H, rng, rm, 1)
			_alcoves(g, W, H, rng, rm, rng.randi_range(0, 1))
		"harabe":
			_pillars(g, W, H, rng, rm, rng.randi_range(2, 4) * kx)
			_arches(g, W, H, rng, rm, rng.randi_range(1, 2) * kx)
			_platforms(g, W, H, rng, rm, rng.randi_range(2, 4) * kx, 4, 8)
			_dips(g, W, H, rng, rm, rng.randi_range(0, 2))
			_wall_ledges(g, W, H, rng, rm, rng.randi_range(1, 2))
			_stalactites(g, W, H, rng, rm, rng.randi_range(0, 2), 3)
			_alcoves(g, W, H, rng, rm, rng.randi_range(0, 2))
		"magara":
			_stalactites(g, W, H, rng, rm, rng.randi_range(3, 6) * kx, 3)
			_boulders(g, W, H, rng, rm, rng.randi_range(2, 4) * kx)
			_platforms(g, W, H, rng, rm, rng.randi_range(3, 5) * kx, 4, 8)
			_islands(g, W, H, rng, rm, rng.randi_range(0, 1))
			_alcoves(g, W, H, rng, rm, rng.randi_range(1, 2))
			_wall_ledges(g, W, H, rng, rm, rng.randi_range(0, 2))
		"cukur":
			_pit(g, W, H, rng, rm)
			_platforms(g, W, H, rng, rm, rng.randi_range(2, 3) * kx, 5, 8)
			_wall_ledges(g, W, H, rng, rm, rng.randi_range(0, 2))
			_stalactites(g, W, H, rng, rm, rng.randi_range(0, 2), 2)
		"kopru":
			_bridge(g, W, H, rng, rm)
			_stalactites(g, W, H, rng, rm, rng.randi_range(0, 2), 2)
		"kuyu":
			_well(g, W, H, rng, rm)
			_alcoves(g, W, H, rng, rm, rng.randi_range(0, 2))
		"kule":
			_tower(g, W, H, rng, rm)
			_alcoves(g, W, H, rng, rm, rng.randi_range(0, 1))


static func _platforms(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rm: Dictionary, count: int, h0: int, h1: int) -> void:
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var fl: Array = rm["fl"]
	var tries := 0
	var placed := 0
	while placed < count and tries < 40:
		tries += 1
		var ln := rng.randi_range(3, 5)
		var x := rng.randi_range(ix0 + 2, ix1 - ln - 2)
		var y: int = int(fl[x - ix0]) - rng.randi_range(h0, h1)
		if not _free_span(g, W, H, rm, x, y, ln, 3, 2):
			continue
		for k in ln:
			_put(g, x + k, y, W, H, 2)
		placed += 1


static func _islands(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rm: Dictionary, count: int) -> void:
	## Havada taş ada (4-6 karo, 2 kalın) tabandan 7-9 yukarıda; altında en az 4, üstünde 4 karo açık; yanında basamak
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var fl: Array = rm["fl"]
	var tries := 0
	var placed := 0
	while placed < count and tries < 40:
		tries += 1
		var ln := rng.randi_range(4, 6)
		var x := rng.randi_range(ix0 + 4, ix1 - ln - 4)
		var y: int = int(fl[x - ix0]) - rng.randi_range(7, 9)
		if y < int(rm["iy0"]) + 5 or not _free_span(g, W, H, rm, x, y, ln, 4, 5):
			continue
		for k in ln:
			_put(g, x + k, y, W, H, 1)
			if k > 0 and k < ln - 1:
				_put(g, x + k, y + 1, W, H, 1)
		# yanında tek yönlü basamak (ada 7-9 yukarıda: iki zıplama)
		var sx := x - 4 if rng.randf() < 0.5 else x + ln + 1
		var sy := y + 4
		if _free_span(g, W, H, rm, sx, sy, 3, 2, 1):
			for k in 3:
				_put(g, sx + k, sy, W, H, 2)
		placed += 1


static func _pillars(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rm: Dictionary, count: int) -> void:
	## Yıkık taş sütunlar (2 karo geniş, 2-3 yüksek) tabanda; üstünden zıplanır
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var fl: Array = rm["fl"]
	var tries := 0
	var placed := 0
	while placed < count and tries < 40:
		tries += 1
		var x := rng.randi_range(ix0 + 3, ix1 - 5)
		var hh := rng.randi_range(2, 3)
		var fy: int = int(fl[x - ix0])
		if int(fl[x + 1 - ix0]) != fy or _in_clear(rm, x, fy - 1) or _in_clear(rm, x + 1, fy - 1):
			continue
		if not _free_span(g, W, H, rm, x, fy - 1, 2, 5, 0):
			continue
		for k in 2:
			for y in range(fy - hh, fy):
				_put(g, x + k, y, W, H, 1)
		placed += 1


static func _arches(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rm: Dictionary, count: int) -> void:
	## Kemer: tabandan 5 karo yukarıda 6 karolık taş kiriş (altından yürünür, üstüne platformla çıkılır)
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var fl: Array = rm["fl"]
	var tries := 0
	var placed := 0
	while placed < count and tries < 30:
		tries += 1
		var ln := 6
		var x := rng.randi_range(ix0 + 3, ix1 - ln - 3)
		var y: int = int(fl[x - ix0]) - 5
		if not _free_span(g, W, H, rm, x, y, ln, 4, 4):
			continue
		for k in ln:
			_put(g, x + k, y, W, H, 1)
			if k > 0 and k < ln - 1 and rng.randf() < 0.5:
				_put(g, x + k, y - 1, W, H, 1)
		var sx := x - 4 if rng.randf() < 0.5 else x + ln + 1
		if _free_span(g, W, H, rm, sx, y + 2, 3, 2, 1):
			for k in 3:
				_put(g, sx + k, y + 2, W, H, 2)
		placed += 1


static func _stalactites(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rm: Dictionary, count: int, wmax := 2) -> void:
	## Tavandan sarkan sütunlar / kaya kütleleri (1-wmax geniş, 2-4 uzun); her sütun kendi tavanından başlar (yanında
	## hava cebi kalmaz: _open_headroom baca açmasın); altında en az 5 karo açık kalır
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var fl: Array = rm["fl"]
	var ce: Array = rm["ce"]
	if bool(rm["acik"]):
		return
	var tries := 0
	var placed := 0
	while placed < count and tries < 40:
		tries += 1
		var wd := rng.randi_range(1, wmax)
		var x := rng.randi_range(ix0 + 2, ix1 - 2 - wd)
		var ln := rng.randi_range(2, 4)
		var ok := true
		for k in wd:
			var i := x + k - ix0
			var top: int = int(ce[i])
			if top < 2 or int(fl[i]) - (top + ln) < 5:
				ok = false
			for y in range(top, top + ln):
				if _in_clear(rm, x + k, y):
					ok = false
		if not ok:
			continue
		for k in wd:
			var i := x + k - ix0
			var top: int = int(ce[i])
			var d := ln - (1 if (k == 0 or k == wd - 1) and wd > 1 else 0)
			for y in range(top, top + d):
				_put(g, x + k, y, W, H, 1)
		placed += 1


static func _alcoves(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rm: Dictionary, count: int) -> void:
	## Yan duvara oyulmuş cepler (2 karo derin, 4 yüksek, 3-5 geniş görünür); kapı sekilerinden uzak; duvar 4 karo
	## kalın olduğundan komşu odaya açılmaz. Taban hizasında ya da yüksekte (platformla çıkılır).
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var fl: Array = rm["fl"]
	var iy0 := int(rm["iy0"])
	for n in count:
		var left := rng.randf() < 0.5
		var xw := ix0 - 1 if left else ix1 + 1
		var xin := ix0 if left else ix1
		var fy: int = int(fl[xin - ix0])
		var yb: int = fy if rng.randf() < 0.6 else fy - rng.randi_range(5, 8)
		if yb - 4 < iy0 + 1:
			continue
		var ok := true
		for y in range(yb - 5, yb + 1):
			if _in_clear(rm, xin, y) or _in_clear(rm, xw, y):
				ok = false
		for y in range(yb - 4, yb):
			if _cell(g, xin, y, W, H) != 0:
				ok = false
		if not ok:
			continue
		for d in 2:
			var x := xw - d if left else xw + d
			for y in range(yb - 4, yb):
				_put(g, x, y, W, H, 0)
			_put(g, x, yb, W, H, 1)
		if yb < fy:
			# yüksek cep: altına çıkış platformu
			var px := xin + (1 if left else -3)
			if _free_span(g, W, H, rm, px, yb + 3, 3, 2, 1):
				for k in 3:
					_put(g, px + k, yb + 3, W, H, 2)


static func _dips(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rm: Dictionary, count: int) -> void:
	## Tabanda 2-3 karo geniş, 2 karo derin çukurcuklar (zıplanarak çıkılır); seki ve merdivenlerden uzak
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var fl: Array = rm["fl"]
	for n in count:
		var wd := rng.randi_range(2, 3)
		var x0 := rng.randi_range(ix0 + 4, ix1 - 4 - wd)
		var fy: int = int(fl[x0 - ix0])
		var ok := true
		for x in range(x0 - 2, x0 + wd + 2):
			if int(fl[x - ix0]) != fy or _in_clear(rm, x, fy - 1) or _cell(g, x, fy, W, H) != 1:
				ok = false
		if not ok:
			continue
		for x in range(x0, x0 + wd):
			_put(g, x, fy, W, H, 0)
			_put(g, x, fy + 1, W, H, 0)
			_put(g, x, fy + 2, W, H, 1)
			fl[x - ix0] = fy + 2


static func _wall_ledges(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rm: Dictionary, count: int) -> void:
	## Yan duvarlara yaslı 3 karolık sekiler (yüksekte): odanın üst yarısına tırmanış ve pusu noktaları
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var fl: Array = rm["fl"]
	var iy0 := int(rm["iy0"])
	for n in count:
		var left := rng.randf() < 0.5
		var sx := ix0 if left else ix1 - 2
		var fy: int = int(fl[sx - ix0])
		var y := fy - rng.randi_range(4, 9)
		if y < iy0 + 3:
			continue
		if _free_span(g, W, H, rm, sx, y, 3, 3, 1):
			for k in 3:
				_put(g, sx + k, y, W, H, 2)


static func _boulders(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rm: Dictionary, count: int) -> void:
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var fl: Array = rm["fl"]
	for i in count:
		var x := rng.randi_range(ix0 + 2, ix1 - 3)
		var fy: int = int(fl[x - ix0])
		if _in_clear(rm, x, fy - 1) or not _free_span(g, W, H, rm, x, fy - 1, 2, 4, 0):
			continue
		_put(g, x, fy - 1, W, H, 1)
		if rng.randf() < 0.5:
			_put(g, x + 1, fy - 1, W, H, 1)


static func _pit(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rm: Dictionary) -> void:
	## Ortada 8-12 karo tehlike çukuru (5 derin), üstünde kırık köprü platformları; dibinde tehlike şeridi
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var fl: Array = rm["fl"]
	var wd := rng.randi_range(8, 12)
	var mid := (ix0 + ix1) / 2
	var x0 := mid - wd / 2
	for x in range(x0 - 1, x0 + wd + 1):
		if _in_clear(rm, x, int(fl[x - ix0]) - 1):
			return
	var fy: int = int(fl[mid - ix0])
	for x in range(x0, x0 + wd):
		for y in range(fy, fy + 5):
			_put(g, x, y, W, H, 0)
		_put(g, x, fy + 4, W, H, 3)
		_put(g, x, fy + 5, W, H, 1)
	# köprü: 3 karolık parçalar, aralar en çok 3
	var bx := x0 + 1
	var row := fy - 1
	while bx < x0 + wd - 1:
		var ln := 3 if rng.randf() < 0.7 else 2
		for k in ln:
			if bx + k < x0 + wd:
				_put(g, bx + k, row, W, H, 2)
		bx += ln + rng.randi_range(2, 3)
		row = fy - 1 if rng.randf() < 0.6 else fy - 2


static func _bridge(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rm: Dictionary) -> void:
	## Köprü odası: iki uçta yüksek taban, ortada 6 karo derin uçurum (dibinde taş zemin; çıkış basamakları), üstte
	## kırık köprü platformları (aralar 2-3 karo)
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var fl: Array = rm["fl"]
	var iy1 := int(rm["iy1"])
	var a := ix0 + 9
	var b := ix1 - 9
	var fy: int = int(fl[a - ix0])
	# uçurum yalnızca temiz bölgeye (kuyu ağzı, seki) değmeyen en uzun aralıkta açılır (içinde duvar kalmasın)
	var best_a := -1
	var best_b := -2
	var ra := a
	while ra <= b:
		if _in_clear(rm, ra, fy - 1) or _in_clear(rm, ra, fy + 3):
			ra += 1
			continue
		var rb := ra
		while rb + 1 <= b and not (_in_clear(rm, rb + 1, fy - 1) or _in_clear(rm, rb + 1, fy + 3)):
			rb += 1
		if rb - ra > best_b - best_a:
			best_a = ra
			best_b = rb
		ra = rb + 1
	a = best_a
	b = best_b
	if b - a < 10:
		return
	var bottom := mini(iy1, fy + 6)
	for x in range(a, b + 1):
		for y in range(fy, bottom):
			_put(g, x, y, W, H, 0)
		_put(g, x, bottom, W, H, 1)
		fl[x - ix0] = bottom
	# dipten çıkış: iki uçta basamak
	_ladder(g, W, H, a, fy, bottom)
	_ladder(g, W, H, b - 5, fy, bottom)
	var bx := a + 2
	while bx < b - 2:
		var ln := rng.randi_range(2, 4)
		var row := fy - 1 - (1 if rng.randf() < 0.3 else 0)
		for k in ln:
			if bx + k < b - 1:
				_put(g, bx + k, row, W, H, 2)
		bx += ln + rng.randi_range(2, 3)
	# dipte seyrek tehlike şeridi (orta)
	if rng.randf() < 0.5:
		var mid := (a + b) / 2
		for hx in range(mid - 2, mid + 2):
			if _cell(g, hx, bottom - 1, W, H) == 0:
				_put(g, hx, bottom - 1, W, H, 3)


static func _well(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rm: Dictionary) -> void:
	## Kuyu: tabandan tavana ortada zikzak basamak sütunu; duvar diplerinde 3 karolık sekiler 4 satırda bir
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var iy0 := int(rm["iy0"])
	var fl: Array = rm["fl"]
	var mid := (ix0 + ix1) / 2 - 3
	var fy: int = int(fl[mid - ix0])
	var top := iy0 + 4
	if fy - top > 6 and not bool(rm.get("ust_kapi", false)):
		_ladder(g, W, H, mid, top, fy)
	for side in [ix0 + 1, ix1 - 3]:
		var y: int = int(fl[side - ix0]) - 4
		while y > iy0 + 3:
			if _free_span(g, W, H, rm, side, y, 3, 3, 1):
				for k in 3:
					_put(g, side + k, y, W, H, 2)
			y -= rng.randi_range(4, 5)


static func _tower(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rm: Dictionary) -> void:
	## Kule: ortada 4 karo geniş taş sütun (tavana 5 karo kala biter), iki yanında ve duvarlarda yükselen sekiler
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var iy0 := int(rm["iy0"])
	var fl: Array = rm["fl"]
	var ce: Array = rm["ce"]
	var cx := (ix0 + ix1) / 2 - 2
	var fy: int = int(fl[cx - ix0])
	# sütunun tepesi tavandan (en alçak noktasından) 5 karo aşağıda: üstünden geçilir
	var top := iy0 + 5
	for x in range(cx - 1, cx + 5):
		top = maxi(top, int(ce[clampi(x - ix0, 0, ce.size() - 1)]) + 5)
	var ok := true
	for x in range(cx, cx + 4):
		for y in range(top, fy):
			if _in_clear(rm, x, y):
				ok = false
	if ok and fy - top > 8:
		# kırık sütun: tabandan 4 karo yükselen güdük (tek çift zıplamayla aşılır) + tavandan sarkan baş; arada geçit
		var stump := fy - 4
		for x in range(cx, cx + 4):
			for y in range(stump, fy):
				_put(g, x, y, W, H, 1)
			if stump - top >= 8:
				for y in range(top, top + 3):
					_put(g, x, y, W, H, 1)
		# güdüğün iki yanında yükselen sekiler (üst kata çıkış)
		var y := fy - 3
		var s := 0
		while y > top + 4:
			var sx := cx - 3 if s == 0 else cx + 4
			var free := true
			for k in 3:
				for yy in range(y - 3, y + 1):
					if _cell(g, sx + k, yy, W, H) != 0 or _in_clear(rm, sx + k, yy):
						free = false
			if free:
				for k in 3:
					_put(g, sx + k, y, W, H, 2)
			y -= 3
			s = 1 - s
	for side in [ix0 + 1, ix1 - 3]:
		var y: int = int(fl[side - ix0]) - 4
		while y > iy0 + 3:
			if _free_span(g, W, H, rm, side, y, 3, 3, 1):
				for k in 3:
					_put(g, side + k, y, W, H, 2)
			y -= rng.randi_range(4, 6)


static func _odul_shape(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rm: Dictionary) -> void:
	## Ödül odası: ortada düz; hazine / zamanlıda 2 karolık taş seki; seçkinde geniş açık alan
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var fl: Array = rm["fl"]
	var mid := _odul_mid(rm)
	var fy: int = int(fl[mid - ix0])
	match String(rm["odul"]):
		"hazine", "zamanli":
			for x in range(mid - 4, mid + 5):
				if _in_clear(rm, x, fy - 1):
					continue
				for y in range(fy - 2, fy):
					_put(g, x, y, W, H, 1)
				fl[x - ix0] = fy - 2
			for k in 3:
				if _cell(g, mid - 8 + k, fy - 3, W, H) == 0 and not _in_clear(rm, mid - 8 + k, fy - 3):
					_put(g, mid - 8 + k, fy - 3, W, H, 2)
		"sunak", "tomar":
			_platforms(g, W, H, rng, rm, 2, 4, 5)


static func _odul_mid(rm: Dictionary) -> int:
	## Ödülün sütunu: odanın ortası; kapı tavanda / tabanda (kuyu) ise kuyudan uzak yan
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var mid := (ix0 + ix1) / 2
	var side := _door_side(rm)
	if side in ["ust", "alt"]:
		var hx := int(rm.get("_door_x", mid))
		mid = hx + 13 if hx + 13 <= ix1 - 5 else hx - 8
	return clampi(mid, ix0 + 5, ix1 - 5)


static func _odul_marks(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rm: Dictionary, zamanli: Array) -> Array:
	## Ödül odası işaretleri [[karakter, x, y_hava]]; zamanlı kapı sütunu kaydedilir
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var fl: Array = rm["fl"]
	var mid := _odul_mid(rm)
	var fy: int = int(fl[mid - ix0])
	var marks: Array = []
	match String(rm["odul"]):
		"hazine":
			marks.append(["T", mid, fy - 1])
		"sunak":
			marks.append(["S", mid, fy - 1])
		"tomar":
			marks.append(["M", mid, fy - 1])
		"pazar":
			marks.append(["P", mid + 2, fy - 1])
		"seckin":
			marks.append(["E", mid - 2, fy - 1])
			marks.append(["T", mid + 5, int(fl[mid + 5 - ix0]) - 1])
		"zamanli":
			marks.append(["Z", mid, fy - 1])
			# kapı: tek kapının iç kenarında, sekinin bittiği sütun (4 karo yüksek geçit kapanır)
			var side := _door_side(rm)
			var dx := ix0 + 6 if side == "sol" else ix1 - 6
			var dy := int(fl[dx - ix0])
			zamanli.append({"x": dx, "y": dy, "room": int(rm["id"]), "sure": ZAMANLI_SURE})
	return marks


static func _door_side(rm: Dictionary) -> String:
	## Ödül odasının tek kapısı hangi yanda (sol / sag / ust: tavandaki kuyu / alt: tabandaki kuyu)
	return String(rm.get("_door_side", "sol"))


static func _odul_tasi(g: PackedByteArray, W: int, H: int, rm: Dictionary) -> Vector2i:
	## Ödül odasının Kut Taşı: kapı sekisinin iç ucu (ödülden uzak); kuyu kapısında kuyunun yanı
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var side := _door_side(rm)
	var x := ix0 + 8 if side == "sol" else ix1 - 8
	if side in ["ust", "alt"]:
		var hx := int(rm.get("_door_x", (ix0 + ix1) / 2))
		x = hx + 8 if hx + 13 <= ix1 - 5 else hx - 3
	return _floor_spot(g, W, H, rm, x)


static func _floor_spot(g: PackedByteArray, W: int, H: int, rm: Dictionary, x: int) -> Vector2i:
	## Odada x sütununda (yakınında) ayakta durulacak hava hücresi (altı katı, üstünde 3 karo hava); tehlike / platform değil
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var fl: Array = rm["fl"]
	for d in range(0, 14):
		for s in ([0] if d == 0 else [1, -1]):
			var cx := clampi(x + d * s, ix0 + 1, ix1 - 1)
			var fy: int = int(fl[cx - ix0])
			# taban satırından yukarı ilk hava hücresi
			var y := fy - 1
			while y > int(rm["iy0"]) and _cell(g, cx, y, W, H) == 1:
				y -= 1
			if _cell(g, cx, y, W, H) == 0 and _cell(g, cx, y + 1, W, H) == 1 and _cell(g, cx, y - 1, W, H) == 0 and _cell(g, cx, y - 2, W, H) == 0 and _cell(g, cx - 1, y + 1, W, H) != 3 and _cell(g, cx + 1, y + 1, W, H) != 3:
				return Vector2i(cx, y)
	return Vector2i(x, int(fl[clampi(x - ix0, 0, fl.size() - 1)]) - 1)


static func _hazard_strips(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rm: Dictionary, style: String) -> void:
	## Dövüş odalarının düz tabanında 2-3 karolık tehlike şeridi (tek zıplamayla aşılır); kapı sekilerine / merdivenlere uzak
	if rng.randf() > 0.55:
		return
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var fl: Array = rm["fl"]
	for t in 8:
		var wd := rng.randi_range(2, 3)
		var x0 := rng.randi_range(ix0 + 8, ix1 - 8 - wd)
		var fy: int = int(fl[x0 - ix0])
		var ok := true
		for x in range(x0 - 3, x0 + wd + 3):
			if int(fl[x - ix0]) != fy or _in_clear(rm, x, fy - 1) or _cell(g, x, fy, W, H) != 1 or _cell(g, x, fy - 1, W, H) != 0:
				ok = false
		if not ok:
			continue
		for x in range(x0, x0 + wd):
			_put(g, x, fy, W, H, 3)
		return


static func _open_cliffs(g: PackedByteArray, W: int, H: int, rooms: Array, owner: Array, cols: int, rows: int) -> void:
	## Gök açık stillerde üst satır odaları arasındaki duvarın tepesi tabandan 10 karo yukarıda biter (kaya yar);
	## üstü gökyüzü. Kapı olmayan duvarlar da öyle (zıplanamaz: 10 > 4).
	for c in range(cols - 1):
		var a: int = owner[c][0]
		var b: int = owner[c + 1][0]
		if a < 0 or b < 0 or a == b:
			continue
		if not bool(rooms[a]["acik"]) or not bool(rooms[b]["acik"]):
			continue
		var fa: int = int((rooms[a]["fl"] as Array)[(rooms[a]["fl"] as Array).size() - 1])
		var fb: int = int((rooms[b]["fl"] as Array)[0])
		var top := mini(fa, fb) - 10
		var xw := _sector_x0(c + 1) - 2
		for x in range(xw, xw + 4):
			for y in range(1, top):
				_put(g, x, y, W, H, 0)


# ================================================================== erişilebilirlik
static func _open_headroom(g: PackedByteArray, W: int, H: int, need: int) -> int:
	## v25: yürünen her hücrenin (hava ya da tehlike; altı katı / platform) üstünde need karo katı olmayan alan:
	## tavana / ada altına / parça duvarına 1-2 karo kalan yerlerde katı karolar açılır (sürünme geçidi kalmaz).
	## Platform (tek yönlü) baş boşluğunu kesmez. Döndürür: açılan karo sayısı.
	var n := 0
	for x in range(1, W - 1):
		for y in range(2, H - 1):
			var c := _cell(g, x, y, W, H)
			if c != 0 and c != 3:
				continue
			var b := _cell(g, x, y + 1, W, H)
			if b != 1 and b != 2:
				continue
			for k in range(1, need):
				var yy := y - k
				if yy < 1:
					break
				if _cell(g, x, yy, W, H) == 1:
					_put(g, x, yy, W, H, 0)
					n += 1
	return n


static func _standable(g: PackedByteArray, x: int, y: int, W: int, H: int) -> bool:
	## Hava karosu, altı katı/platform olan yer; tehlike (3) üstünde durulmaz
	if _cell(g, x, y, W, H) != 0:
		return false
	var below := _cell(g, x, y + 1, W, H)
	return below == 1 or below == 2


static func _moves(g: PackedByteArray, W: int, H: int, cx: int, cy: int) -> Array:
	## Fizik sadık hamleler (oyuncu 2 karo boy, sürünürken 1): yürüme/sürünme ±1; düşme ±5 sütun / 15 satır;
	## zıplama en çok 4 karo yukarı (çift zıplama), çıkış sütununda baş boşluğu, yörünge tepesi açık olmalı.
	## v25: tek yönlü platform (2) baş boşluğunu ve zıplama yörüngesini kesmez (oyuncu altından içinden zıplar).
	var out: Array = []
	var tall: bool = _cell(g, cx, cy - 1, W, H) != 1
	var head := 0
	while head < 5 and _cell(g, cx, cy - 1 - head, W, H) != 1:
		head += 1
	var max_up := (head - 1) if tall else 0
	for dx in range(-5, 6):
		for dy in range(-5, 16):
			var nx := cx + dx
			var ny := cy + dy
			if nx < 1 or nx >= W - 1 or ny < 1 or ny >= H - 1:
				continue
			if dy < 0 and -dy > max_up:
				continue
			if dx == 0 and dy == 0:
				continue
			if not _standable(g, nx, ny, W, H):
				continue
			var crawl_dest: bool = _cell(g, nx, ny - 1, W, H) == 1
			if crawl_dest and not (dy == 0 and absi(dx) == 1):
				continue
			if not (dy == 0 and absi(dx) == 1):
				if not tall and dy < 0:
					continue
				var apex := mini(cy, ny) - 1 - (1 if dy > 2 else 0)
				if dy < 0:
					apex = ny - 1
				var blocked := false
				var step := 1 if dx > 0 else -1
				var k := cx
				while k != nx:
					k += step
					if _cell(g, k, apex, W, H) == 1 and _cell(g, k, apex + 1, W, H) == 1:
						blocked = true
						break
				if blocked:
					continue
				if dy > 0 and _cell(g, nx, ny - 1, W, H) == 1:
					continue
				# düşüş: düşülen sütunda iniş yolu (varışın üstü) boydan boya açık olmalı
				if dy > 1 and dx != 0:
					var clear := true
					for yy in range(mini(cy, ny) - 1, ny):
						if _cell(g, nx, yy, W, H) == 1:
							clear = false
							break
					if not clear and _cell(g, cx + step, cy, W, H) != 0:
						continue
			out.append(_idx(nx, ny, W))
	return out


static func _goal(cx: int, cy: int) -> bool:
	return absi(cx - int(_son["gx"])) <= 3 and absi(cy - int(_son["gy"])) <= 1


static func _reach(g: PackedByteArray, W: int, H: int, _heights: Array) -> Dictionary:
	## Girişten çıkışa erişim: {ok, x, y} (x,y: çıkışa en yakın ulaşılan ayakta durma hücresi)
	var sx := int(_son["sx"])
	var sy := int(_son["sy"])
	var seen := PackedByteArray()
	seen.resize(W * H)
	seen.fill(0)
	var q: Array = [_idx(sx, sy, W)]
	seen[q[0]] = 1
	var best := [sx, sy]
	var bd := 999999
	var qi := 0
	while qi < q.size():
		var id: int = q[qi]
		qi += 1
		var cx := id % W
		var cy := id / W
		var d := absi(cx - int(_son["gx"])) * 2 + absi(cy - int(_son["gy"]))
		if d < bd:
			bd = d
			best = [cx, cy]
		if _goal(cx, cy):
			return {"ok": true, "x": cx, "y": cy}
		for n in _moves(g, W, H, cx, cy):
			if seen[n] == 0:
				seen[n] = 1
				q.append(n)
	return {"ok": false, "x": best[0], "y": best[1]}


static func reach_set(g: PackedByteArray, W: int, H: int, _heights: Array) -> PackedByteArray:
	## Girişten ulaşılabilen ayakta durma hücreleri (1 = ulaşılır; tehlike hava sayılır). Keşif ganimeti, harita testi.
	return reach_from(g, W, H, int(_son["sx"]), int(_son["sy"]))


static func reach_from(g: PackedByteArray, W: int, H: int, sx: int, sy: int) -> PackedByteArray:
	var gh := _haz_as_air(g)
	var seen := PackedByteArray()
	seen.resize(W * H)
	seen.fill(0)
	var s0 := _idx(sx, sy, W)
	seen[s0] = 1
	var q: Array = [s0]
	var qi := 0
	while qi < q.size():
		var id: int = q[qi]
		qi += 1
		for n in _moves(gh, W, H, id % W, id / W):
			if seen[n] == 0:
				seen[n] = 1
				q.append(n)
	return seen


static func traps(g: PackedByteArray, W: int, H: int, _heights: Array, orig: PackedByteArray = PackedByteArray()) -> Array:
	## Tuzaklar: girişten ulaşılabilen ama çıkışa ulaşamayan ayakta durma hücreleri (düşülen çıkmaz çukurlar).
	## orig verilirse tehlike (3) tabanlı hücreler sayılmaz (çukur oyuncuyu kendisi dışarı sektirir).
	var sx := int(_son["sx"])
	var sy := int(_son["sy"])
	var seen := PackedByteArray()
	seen.resize(W * H)
	seen.fill(0)
	var rev: Dictionary = {}
	var q: Array = [_idx(sx, sy, W)]
	seen[q[0]] = 1
	var qi := 0
	var goals: Array = []
	while qi < q.size():
		var id: int = q[qi]
		qi += 1
		if _goal(id % W, id / W):
			goals.append(id)
		for n in _moves(g, W, H, id % W, id / W):
			if not rev.has(n):
				rev[n] = []
			rev[n].append(id)
			if seen[n] == 0:
				seen[n] = 1
				q.append(n)
	var good := PackedByteArray()
	good.resize(W * H)
	good.fill(0)
	var rq: Array = goals.duplicate()
	for gq in goals:
		good[gq] = 1
	var ri := 0
	while ri < rq.size():
		var id2: int = rq[ri]
		ri += 1
		for pr in rev.get(id2, []):
			if good[pr] == 0:
				good[pr] = 1
				rq.append(pr)
	var out: Array = []
	for id3 in q:
		if good[id3] == 0:
			if not orig.is_empty() and orig[id3] == 3:
				continue
			out.append(id3)
	return out


static func fix_traps(g: PackedByteArray, W: int, H: int, heights: Array) -> int:
	## Çıkmazları kapat: en derindeki tuzak hücresinin üstüne zikzak tek yönlü basamaklar koy (2 karoda bir);
	## olmazsa çukur tabanını bir karo yükselt. Döndürür: yapılan düzeltme sayısı.
	var gh := _haz_as_air(g)
	var fixes := 0
	if not _reach(gh, W, H, heights)["ok"]:
		return 0
	for it in 60:
		var tr := traps(gh, W, H, heights, g)
		if tr.is_empty():
			break
		var deep: int = tr[0]
		for id in tr:
			if id / W > deep / W:
				deep = id
		var x := deep % W
		var y := deep / W
		if it < 40:
			var side := 1
			var placed := false
			var py := y - 2
			while py > y - 14 and py > 2:
				var px := x + (0 if side > 0 else -2)
				for k in 3:
					if _cell(gh, px + k, py, W, H) == 0 and _cell(gh, px + k, py - 1, W, H) == 0:
						_put(g, px + k, py, W, H, 2)
						_put(gh, px + k, py, W, H, 2)
						placed = true
				side = -side
				py -= 2
			if not placed:
				_put(g, x, y, W, H, 1)
				_put(gh, x, y, W, H, 1)
		else:
			for k in range(-1, 2):
				if _cell(gh, x + k, y, W, H) == 0:
					_put(g, x + k, y, W, H, 1)
					_put(gh, x + k, y, W, H, 1)
		fixes += 1
	return fixes


static func _reachable(g: PackedByteArray, W: int, H: int, heights: Array) -> bool:
	return _reach(_haz_as_air(g), W, H, heights)["ok"]


static func _haz_as_air(g: PackedByteArray) -> PackedByteArray:
	var c := g.duplicate()
	for i in c.size():
		if c[i] == 3:
			c[i] = 0
	return c


static func guarantee(g: PackedByteArray, W: int, H: int, heights: Array) -> int:
	## Eski imza: girişten çıkışa yol yoksa 0 döndürür (v32: onarım fix_traps ve yeniden üretimle)
	return 0 if _reachable(g, W, H, heights) else 0


# ================================================================== yol bulma (bot / rehber)
static func path_cells(g: PackedByteArray, W: int, H: int, sx: int, sy: int, gx: int, gy: int, max_nodes := 60000) -> Array:
	## Girişten hedefe en kısa hamle dizisi (hücre dizinleri; ilk öğe başlangıç). Hedef: gx±2, gy±1. Boşsa yol yok.
	var gh := _haz_as_air(g)
	var seen := PackedByteArray()
	seen.resize(W * H)
	seen.fill(0)
	var par := PackedInt32Array()
	par.resize(W * H)
	par.fill(-1)
	var s0 := _idx(sx, sy, W)
	seen[s0] = 1
	var q: Array = [s0]
	var qi := 0
	var goal := -1
	while qi < q.size() and qi < max_nodes:
		var id: int = q[qi]
		qi += 1
		var cx := id % W
		var cy := id / W
		if absi(cx - gx) <= 2 and absi(cy - gy) <= 1:
			goal = id
			break
		for n in _moves(gh, W, H, cx, cy):
			if seen[n] == 0:
				seen[n] = 1
				par[n] = id
				q.append(n)
	var out: Array = []
	if goal < 0:
		return out
	var c := goal
	while c >= 0:
		out.append(c)
		c = par[c]
	out.reverse()
	return out


static func stand_cell(g: PackedByteArray, W: int, H: int, px: float, py: float, TS: int) -> Vector2i:
	## Dünya ayak noktasından en yakın ayakta durma hücresi (tehlike hava sayılır)
	var gh := _haz_as_air(g)
	var x := clampi(int(floor(px / TS)), 1, W - 2)
	var y := clampi(int(floor((py - 2.0) / TS)), 1, H - 2)
	for d in range(0, 6):
		for dy in range(-d, d + 1):
			for dx in range(-d, d + 1):
				if absi(dx) != d and absi(dy) != d:
					continue
				if _standable(gh, x + dx, y + dy, W, H):
					return Vector2i(x + dx, y + dy)
	return Vector2i(x, y)
