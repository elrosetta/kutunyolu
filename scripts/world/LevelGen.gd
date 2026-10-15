class_name LevelGen
extends RefCounted
## Bölüm üretimi: her koşuda farklı bir arazi biçimi (stil) + elle tasarlanmış parçalar (oda şablonları).
##   orman   : dalgalı tepeler, havada adalar, ahşap platformlar (açık arazi)
##   ucurum  : teraslar, derin çukurlar, basamak platformlar, uçurum kenarları
##   magara  : tavanlı tüneller, alçak sürünme geçitleri, sarkıt sütunlar, gökyüzüne açılan ağızlar
##   harabe  : çökmüş kule kuyuları (zikzak platformlarla tırmanış), taş duvarlar, kemerler
## Parçalar: '#' katı, '=' platform, '.' zorla hava, ' ' dokunma. Alt satır yüzeye oturur.
## Üretimden sonra erişilebilirlik denetimi yapılır (basit zıplama modeli); geçilemeyen bölüm yeniden üretilir.

const STYLES := ["orman", "ucurum", "magara", "harabe", "bozkir", "kuyu"]

## Yüzeyin altına inen satır sayısı (çukur gibi parçalar için)
const CHUNK_SINK := {"cukur": 5, "zehir_cukuru": 1, "kurgan": 3}

const CHUNKS := {
	"surunme": [  # alçak geçit: yalnızca yuvarlanarak (1 karo yükseklik)
		"            ",
		"  ########  ",
		"  ########  ",
		"  ########  ",
		"............",
	],
	"sutunlar": [
		"            ",
		"  #  #   #  ",
		"  #  #   #  ",
		"  #  #   #  ",
		"............",
	],
	"cukur": [
		"            ",
		"............",
		"............",
		"...=====....",
		"............",
		"............",
		"##........##",
	],
	"merdiven": [
		"          ##",
		"       ===##",
		"    ===   ##",
		" ===      ##",
		"          ##",
		"............",
	],
	"kemer": [  # yıkık köprü: altından yürünür, üstüne çıkılır
		"   ######   ",
		"  ########  ",
		"            ",
		"            ",
		"............",
	],
	"kule": [
		"    ###     ",
		"    ###     ",
		"  = ###     ",
		"    ### =   ",
		"=   ###     ",
		"    ###  =  ",
		"............",
	],
	"basamak": [
		"        ##  ",
		"     ##     ",
		"  ##        ",
		"            ",
		"............",
	],
	"mezar": [  # iki mezar taşı (2 karo: tek zıplamayla aşılır)
		"            ",
		"   ##   ##  ",
		"   ##   ##  ",
	],
	# --- v9 özel odalar ('H' tehlike, 'S' sunak işareti, 'T' hazine kaidesi, 'E' seçkin): işaretler hava sayılır
	"sunak": [  # tanrı sunağı: kaideye çıkılır, ortada sunak
		"              ",
		"              ",
		"     S        ",
		"   ######     ",
		"..............",
	],
	"hazine": [  # hazine odası: yüksek taş oda, içine üstten iniş; kaide üstünde eşya
		" ##########  ",
		" #........#  ",
		" #...T....#  ",
		" #........#  ",
		" #..====..#  ",
		" #........#  ",
		"..............",
	],
	"seckin": [  # seçkin odası: iki sütun arasında düz alan
		"  #        #  ",
		"  #        #  ",
		"  #   E    #  ",
		"  #        #  ",
		"..............",
	],
	"kurgan": [  # bozkır kurganı: yer altı mezar odası; üstten delikle girilir
		"              ",
		"     ....     ",
		"####....######",
		"#...........T#",
		"#............#",
		"##############",
	],
	"zehir_cukuru": [  # tehlike çukuru: üstünden zıplanır ya da platformlardan geçilir
		"              ",
		"              ",
		"   ========   ",
		"              ",
		"..HHHHHHHHHH..",
		"##HHHHHHHHHH##",
	],
}
## Tehlike çukuru parçaları yüzeyin altına iner


static func generate(rng: RandomNumberGenerator, W: int, H: int, depth: int, allowed: Array = []) -> Dictionary:
	## Döndürür: {grid, heights, style, chunks, carved, trapfix}. Geçilebilirlik + çıkmaz çukur onarımı garantili.
	var pool: Array = allowed if not allowed.is_empty() else STYLES
	var style: String = pool[rng.randi_range(0, pool.size() - 1)]
	if depth == 1 and rng.randf() < 0.5:
		style = "orman"
	var best: Dictionary = {}
	for attempt in 8:
		var r := _build(rng, W, H, style)
		if _reachable(r["grid"], W, H, r["heights"]):
			r["style"] = style
			best = r
			break
		if best.is_empty():
			best = r
			best["style"] = style
		style = pool[rng.randi_range(0, pool.size() - 1)]
	best["carved"] = 0
	best["trapfix"] = 0
	for round in 4:
		best["carved"] = int(best["carved"]) + guarantee(best["grid"], W, H, best["heights"])
		best["trapfix"] = int(best["trapfix"]) + fix_traps(best["grid"], W, H, best["heights"])
		if _reachable(best["grid"], W, H, best["heights"]) and traps(_haz_as_air(best["grid"]), W, H, best["heights"]).is_empty():
			break
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


static func _base_heights(rng: RandomNumberGenerator, W: int, amp := 1.0) -> Array:
	var p1 := rng.randf() * TAU
	var p2 := rng.randf() * TAU
	var p3 := rng.randf() * TAU
	var heights: Array = []
	var step := 0
	for x in W:
		if x > 20 and x < W - 20 and rng.randf() < 0.025:
			step += rng.randi_range(-3, 3)
			step = clampi(step, -5, 4)
		var n := (sin(x * 0.05 + p1) * 2.4 + sin(x * 0.13 + p2) * 1.1 + sin(x * 0.022 + p3) * 3.4) * amp
		var h := int(round(31.0 + n)) + step
		if x < 14:
			h = 31
		if x > W - 14:
			h = 30
		heights.append(clampi(h, 20, 38))
	for x in range(1, W):
		var d: int = heights[x] - heights[x - 1]
		if absi(d) > 4:
			heights[x] = heights[x - 1] + clampi(d, -4, 4)
	return heights


static func _build(rng: RandomNumberGenerator, W: int, H: int, style: String) -> Dictionary:
	var grid := PackedByteArray()
	grid.resize(W * H)
	grid.fill(0)
	var heights := _base_heights(rng, W, 1.0 if style != "ucurum" else 0.6)
	var chunks: Array = []
	match style:
		"ucurum":
			_terraces(rng, W, heights)
	for x in W:
		for y in range(int(heights[x]), H):
			_put(grid, x, y, W, H, 1)
	for y in H:
		_put(grid, 0, y, W, H, 1)
		_put(grid, W - 1, y, W, H, 1)
	match style:
		"orman":
			_valley(rng, grid, W, H, heights)
			_islands(rng, grid, W, H, heights, 9)
			_wood_platforms(rng, grid, W, H, heights, 10)
		"ucurum":
			_pits(rng, grid, W, H, heights, 3)
			_islands(rng, grid, W, H, heights, 4)
			_wood_platforms(rng, grid, W, H, heights, 14)
		"magara":
			_cave_roof(rng, grid, W, H, heights)
			_wood_platforms(rng, grid, W, H, heights, 6)
		"harabe":
			_shafts(rng, grid, W, H, heights, 2)
			_islands(rng, grid, W, H, heights, 3)
			_wood_platforms(rng, grid, W, H, heights, 8)
		"bozkir":
			# geniş açık ova: seyrek adalar, kurgan tümsekleri (yüzeyde yumuşak kabarıklıklar)
			_mounds(rng, grid, W, H, heights, 4)
			_islands(rng, grid, W, H, heights, 3)
			_wood_platforms(rng, grid, W, H, heights, 5)
		"kuyu":
			# derin kuyular + mağara tavanı: dikey iniş-çıkışlar
			_cave_roof(rng, grid, W, H, heights)
			_pits(rng, grid, W, H, heights, 3)
			_wood_platforms(rng, grid, W, H, heights, 8)
	# elle tasarlanmış parçalar: genel 2-3 + biyom odaları (sunak her bölümde, hazine/seçkin/kurgan şans)
	var names: Array = ["surunme", "sutunlar", "cukur", "merdiven", "kemer", "kule", "basamak", "mezar"]
	var x := 30 + rng.randi_range(0, 10)
	var n_ch := rng.randi_range(2, 3)
	var specials: Array = ["sunak"]
	if rng.randf() < 0.75:
		specials.append("hazine")
	if rng.randf() < 0.6:
		specials.append("seckin")
	if style == "bozkir":
		specials.append("kurgan")
	if style in ["magara", "kuyu", "harabe", "ucurum"] and rng.randf() < 0.7:
		specials.append("zehir_cukuru")
	while (n_ch > 0 or not specials.is_empty()) and x < W - 40:
		var nm: String
		if not specials.is_empty() and (n_ch <= 0 or rng.randf() < 0.5):
			nm = specials.pop_front()
		else:
			nm = names[rng.randi_range(0, names.size() - 1)]
			if style in ["magara", "kuyu"] and nm in ["kule", "basamak"]:
				nm = "surunme"
			n_ch -= 1
		_stamp(grid, W, H, heights, nm, x)
		chunks.append({"name": nm, "x": x})
		x += 12 + rng.randi_range(16, 34)
	_hazard_patches(rng, grid, W, H, heights, style)
	_ensure_path(grid, W, H, heights)
	return {"grid": grid, "heights": heights, "chunks": chunks}


static func _mounds(rng: RandomNumberGenerator, grid: PackedByteArray, W: int, H: int, heights: Array, count: int) -> void:
	## Bozkır kurgan tümsekleri: 10-16 karolık yumuşak kabarıklık (2-3 karo)
	for i in count:
		var cx := rng.randi_range(40, W - 40)
		var wd := rng.randi_range(10, 16)
		var hh := rng.randi_range(2, 3)
		for x in range(cx - wd / 2, cx + wd / 2):
			if x < 2 or x >= W - 2:
				continue
			var k := 1.0 - absf(float(x - cx)) / (wd / 2.0)
			var up := int(round(hh * sin(k * PI / 2.0)))
			var top: int = int(heights[x]) - up
			for y in range(top, int(heights[x])):
				_put(grid, x, y, W, H, 1)
			heights[x] = top


static func _hazard_patches(rng: RandomNumberGenerator, grid: PackedByteArray, W: int, H: int, heights: Array, style: String) -> void:
	## Yüzeyde 2-4 karolık tehlike yamaları (değer 3): tek zıplamayla aşılır; giriş ve çıkışa uzak
	var n := rng.randi_range(3, 6)
	for i in n:
		var x0 := rng.randi_range(36, W - 40)
		var wd := rng.randi_range(2, 4)
		var ok := true
		for x in range(x0 - 2, x0 + wd + 2):
			var gy := _ground(grid, x, W, H, heights)
			if absi(gy - _ground(grid, x0, W, H, heights)) > 0 or _cell(grid, x, gy, W, H) != 1:
				ok = false
		if not ok:
			continue
		var gy0 := _ground(grid, x0, W, H, heights)
		for x in range(x0, x0 + wd):
			_put(grid, x, gy0, W, H, 3)


static func _ground(g: PackedByteArray, x: int, W: int, H: int, heights: Array) -> int:
	## Yürünen zemin: tabanın 8 karo altından yukarı taranan ilk "üstü hava" katı/platform karosu
	var y := mini(H - 1, int(heights[clampi(x, 0, W - 1)]) + 8)
	while y > 1:
		if _cell(g, x, y, W, H) != 0 and _cell(g, x, y - 1, W, H) == 0:
			return y
		y -= 1
	return H - 1


static func _ensure_path(g: PackedByteArray, W: int, H: int, heights: Array) -> void:
	## Soldan sağa yürüyüş: her sütun geçişi tek zıplama, çift zıplama ya da yuvarlanmayla aşılabilir olmalı.
	##  * 4+ karo yükseliş: duvarın önüne 3 karoda bir 2 karolık platform basamakları (üstleri boşaltılır)
	##  * yükselişte baş boşluğu: zıplanan sütunda ve varılan sütunda en az 2 karo hava
	##  * düz/iniş: bir sonraki sütunda bel hizası (ayakta durulan karo) hava olmalı -> en kötü 1 karo sürünme
	for x in range(2, W - 3):
		var s0 := _ground(g, x, W, H, heights)
		var s1 := _ground(g, x + 1, W, H, heights)
		var rise := s0 - s1
		if rise >= 3:
			# önce basamak sütunlarının havası açılır, sonra 3 karo genişliğinde platformlar konur
			for cx in [x - 2, x - 1, x]:
				for yy in range(s1 - 2, s0):
					if _cell(g, cx, yy, W, H) == 1:
						_put(g, cx, yy, W, H, 0)
			# basamaklar 2 karoda bir: her biri tek zıplamayla çıkılır; son basamak tepeye en çok 2 karo
			var y := s0 - 2
			while y > s1:
				for cx in [x - 2, x - 1, x]:
					_put(g, cx, y, W, H, 2)
				y -= 2
			_put(g, x + 1, s1 - 1, W, H, 0)
			_put(g, x + 1, s1 - 2, W, H, 0)
		elif rise > 0:
			for yy in range(s1 - 2, s0):
				_put(g, x, yy, W, H, 0)
			_put(g, x + 1, s1 - 1, W, H, 0)
			_put(g, x + 1, s1 - 2, W, H, 0)
		else:
			if _cell(g, x + 1, s0 - 1, W, H) == 1:
				_put(g, x + 1, s0 - 1, W, H, 0)


# ------------------------------------------------------------------ stil parçaları
static func _terraces(rng: RandomNumberGenerator, W: int, heights: Array) -> void:
	## Uçurum: 10-22 karoda bir büyük basamak (3-6 karo). Yükseliş basamakları sonra platformla kapatılır.
	var x := 24
	var level := 0
	while x < W - 30:
		var len := rng.randi_range(10, 22)
		var d := rng.randi_range(3, 6) * (1 if rng.randf() < 0.5 else -1)
		if level + d > 6:
			d = -absi(d)
		if level + d < -8:
			d = absi(d)
		level += d
		for k in range(x, mini(W - 14, x + len)):
			heights[k] = clampi(int(heights[k]) - level, 14, 40)
		x += len
	# son: taban seviyesine geri getir
	for k in range(maxi(0, x - 2), W):
		heights[k] = clampi(int(heights[k]), 14, 40)


static func _valley(rng: RandomNumberGenerator, grid: PackedByteArray, W: int, H: int, heights: Array) -> void:
	var vx := rng.randi_range(70, 90)
	for x in range(vx, vx + 8):
		heights[x] = mini(40, int(heights[x]) + 4)
		for y in range(int(heights[x]) - 4, int(heights[x])):
			if y >= 0:
				_put(grid, x, y, W, H, 0)
		for y in range(int(heights[x]), H):
			_put(grid, x, y, W, H, 1)
	for x in range(vx + 1, vx + 7):
		if x % 3 != 0:
			_put(grid, x, int(heights[vx - 1]) - 1, W, H, 2)


static func _islands(rng: RandomNumberGenerator, grid: PackedByteArray, W: int, H: int, heights: Array, count: int) -> void:
	var placed := 0
	var tries := 0
	while placed < count and tries < 200:
		tries += 1
		var ix := rng.randi_range(22, W - 24)
		var iw := rng.randi_range(5, 9)
		var gy: int = heights[ix]
		var iy := gy - rng.randi_range(6, 8)
		var ok := true
		for x in range(ix - 2, ix + iw + 2):
			for y in range(iy - 3, iy + 4):
				if _cell(grid, x, y, W, H) != 0:
					ok = false
		if not ok:
			continue
		for x in range(ix, ix + iw):
			_put(grid, x, iy, W, H, 1)
			if x > ix and x < ix + iw - 1:
				_put(grid, x, iy + 1, W, H, 1)
			if x > ix + 1 and x < ix + iw - 2:
				_put(grid, x, iy + 2, W, H, 1)
			if x > ix + 2 and x < ix + iw - 3 and rng.randf() < 0.7:
				_put(grid, x, iy + 3, W, H, 1)
		var px := ix - 3 if rng.randf() < 0.5 else ix + iw
		var py := iy + 3
		if _cell(grid, px, py, W, H) == 0 and _cell(grid, px + 1, py, W, H) == 0 and _cell(grid, px + 2, py, W, H) == 0 and py < int(heights[clampi(px, 0, W - 1)]) - 1:
			for k in 3:
				_put(grid, px + k, py, W, H, 2)
		placed += 1


static func _wood_platforms(rng: RandomNumberGenerator, grid: PackedByteArray, W: int, H: int, heights: Array, count: int) -> void:
	for i in count:
		var px := rng.randi_range(20, W - 20)
		var py: int = heights[px] - rng.randi_range(3, 4)
		var ln := rng.randi_range(3, 5)
		var ok2 := true
		for k in range(-1, ln + 1):
			if _cell(grid, px + k, py, W, H) != 0 or _cell(grid, px + k, py - 1, W, H) != 0 or _cell(grid, px + k, py - 2, W, H) != 0:
				ok2 = false
		if ok2:
			for k in ln:
				_put(grid, px + k, py, W, H, 2)


static func _pits(rng: RandomNumberGenerator, grid: PackedByteArray, W: int, H: int, heights: Array, count: int) -> void:
	## Derin çukur: 3-5 karo genişlik, dibinde platformlarla geçiş; düşersen aşağıdan tırmanırsın
	for i in count:
		var px := rng.randi_range(40, W - 40)
		var wd := rng.randi_range(3, 5)
		var top: int = heights[px]
		for x in range(px, px + wd):
			for y in range(top, mini(H - 2, top + 7)):
				_put(grid, x, y, W, H, 0)
			heights[x] = mini(H - 2, top + 7)
		# dipten çıkış: zikzak platformlar
		var y := top + 5
		var side := 0
		while y > top:
			var sx := px + (0 if side == 0 else wd - 2)
			for k in 2:
				if sx + k < px + wd:
					_put(grid, sx + k, y, W, H, 2)
			y -= 2
			side = 1 - side


static func _cave_roof(rng: RandomNumberGenerator, grid: PackedByteArray, W: int, H: int, heights: Array) -> void:
	## Mağara: tavan bantları, sarkıt sütunlar, alçak sürünme geçitleri, aralarda gökyüzü ağızları
	var x := 18
	while x < W - 18:
		var len := rng.randi_range(14, 34)
		var open := rng.randf() < 0.25
		if not open:
			var clearance := rng.randi_range(4, 6)
			for k in range(x, mini(W - 14, x + len)):
				var top := int(heights[k]) - clearance
				for y in range(maxi(0, top - 12), top):
					_put(grid, k, y, W, H, 1)
				# tavandan sarkan sütunlar
				if rng.randf() < 0.12 and k > x + 2 and k < x + len - 3:
					for y in range(top, int(heights[k]) - 2):
						_put(grid, k, y, W, H, 1)
			# alçak geçit: 2-4 karo boyunca tavan 1 karoya iner
			if len > 18 and rng.randf() < 0.6:
				var gx := x + rng.randi_range(5, len - 8)
				for k in range(gx, gx + rng.randi_range(2, 4)):
					for y in range(int(heights[k]) - clearance - 12, int(heights[k]) - 1):
						if y >= 0:
							_put(grid, k, y, W, H, 1)
		x += len + rng.randi_range(2, 6)


static func _shafts(rng: RandomNumberGenerator, grid: PackedByteArray, W: int, H: int, heights: Array, count: int) -> void:
	## Harabe: çökmüş kule kuyusu: 6 karo genişlik, 10 karo derinlik, iki yanda taş duvar, içeride zikzak platformlar
	for i in count:
		var px := rng.randi_range(50 + i * 70, 90 + i * 70)
		var wd := 6
		var top: int = heights[px]
		var depth := 10
		for x in range(px - 1, px + wd + 1):
			for y in range(maxi(0, top - 12), top):
				if x == px - 1 or x == px + wd:
					_put(grid, x, y, W, H, 1)  # kule duvarları
		for x in range(px, px + wd):
			for y in range(top, mini(H - 2, top + depth)):
				_put(grid, x, y, W, H, 0)
			heights[x] = mini(H - 2, top + depth)
		# duvarın tepesinde kemer açıklığı: içeri girmek için
		for y in range(top - 12, top - 8):
			if y >= 0:
				_put(grid, px - 1, y, W, H, 0)
				_put(grid, px + wd, y, W, H, 0)
		# giriş: sol duvarda alçak kapı
		for y in range(top - 3, top):
			_put(grid, px - 1, y, W, H, 0)
			_put(grid, px + wd, y, W, H, 0)
		var y := top + depth - 2
		var side := 0
		while y > top - 8:
			var sx := px + (0 if side == 0 else wd - 2)
			for k in 2:
				_put(grid, sx + k, y, W, H, 2)
			y -= 2
			side = 1 - side


static func _stamp(grid: PackedByteArray, W: int, H: int, heights: Array, name: String, x0: int) -> void:
	var rows: Array = CHUNKS[name]
	var hgt := rows.size()
	var sink: int = CHUNK_SINK.get(name, 0)
	var base: int = heights[clampi(x0 + 6, 0, W - 1)]
	var wd: int = rows[0].length()
	# 1) parça sütunlarında arazi tabana düzlenir: taban ve altı katı, üstü (parça yüksekliği + 3) hava
	for cidx in wd:
		var x := x0 + cidx
		if x <= 1 or x >= W - 2:
			continue
		for y in range(maxi(0, base - hgt - 3), base):
			_put(grid, x, y, W, H, 0)
		for y in range(base, H):
			_put(grid, x, y, W, H, 1)
		heights[x] = base
	# 2) karakterler basılır; alt satır tabanın `sink` karo altına oturur
	for r in hgt:
		var line: String = rows[r]
		var y := base - (hgt - r) + sink
		for cidx in line.length():
			var ch := line[cidx]
			var x := x0 + cidx
			if x <= 1 or x >= W - 2 or y < 0 or y >= H:
				continue
			match ch:
				"#":
					_put(grid, x, y, W, H, 1)
				"=":
					_put(grid, x, y, W, H, 2)
				".":
					_put(grid, x, y, W, H, 0)
				"H":
					_put(grid, x, y, W, H, 3)
				"S", "T", "E":
					_put(grid, x, y, W, H, 0)


# ------------------------------------------------------------------ erişilebilirlik
static func _standable(g: PackedByteArray, x: int, y: int, W: int, H: int) -> bool:
	## Hava karosu, altı katı/platform, üstünde en az 1 karo hava (sürünme) olan yer; tehlike (3) üstünde durulmaz
	if _cell(g, x, y, W, H) != 0:
		return false
	var below := _cell(g, x, y + 1, W, H)
	return below == 1 or below == 2


static func _moves(g: PackedByteArray, W: int, H: int, cx: int, cy: int) -> Array:
	## Fizik sadık hamleler (oyuncu 2 karo boy, sürünürken 1): yürüme/sürünme ±1; düşme ±5 sütun / 15 satır;
	## zıplama en çok 5 karo yukarı (çift zıplama), çıkış sütununda baş boşluğu, yörünge tepesi açık olmalı.
	var out: Array = []
	var tall: bool = _cell(g, cx, cy - 1, W, H) == 0
	var head := 0
	while head < 5 and _cell(g, cx, cy - 1 - head, W, H) == 0:
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
			var crawl_dest: bool = _cell(g, nx, ny - 1, W, H) != 0
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
					if _cell(g, k, apex, W, H) != 0 and _cell(g, k, apex + 1, W, H) != 0:
						blocked = true
						break
				if blocked:
					continue
				if dy > 0 and _cell(g, nx, ny - 1, W, H) != 0:
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


static func _reach(g: PackedByteArray, W: int, H: int, heights: Array) -> Dictionary:
	## Girişten sağ uca erişim: {ok, x, y} (x,y: en sağa ulaşılan ayakta durma hücresi)
	var sx := 5
	var sy: int = heights[sx] - 1
	var seen := PackedByteArray()
	seen.resize(W * H)
	seen.fill(0)
	var q: Array = [_idx(sx, sy, W)]
	seen[q[0]] = 1
	var target_x := W - 7
	var best := [sx, sy]
	var qi := 0
	while qi < q.size():
		var id: int = q[qi]
		qi += 1
		var cx := id % W
		var cy := id / W
		if cx > best[0]:
			best = [cx, cy]
		if cx >= target_x:
			return {"ok": true, "x": cx, "y": cy}
		for n in _moves(g, W, H, cx, cy):
			if seen[n] == 0:
				seen[n] = 1
				q.append(n)
	return {"ok": false, "x": best[0], "y": best[1]}


static func traps(g: PackedByteArray, W: int, H: int, heights: Array) -> Array:
	## Tuzaklar: girişten ulaşılabilen ama çıkışa (sağ uç) ulaşamayan ayakta durma hücreleri (düşülen çıkmaz çukurlar).
	var sx := 5
	var sy: int = heights[sx] - 1
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
		if id % W >= W - 7:
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
		var tr := traps(gh, W, H, heights)
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


static func _carve(g: PackedByteArray, W: int, H: int, heights: Array, x0: int, y0: int) -> void:
	## Takılan noktadan sağa 7 sütunluk düz koridor: yerdeki boşluklar doldurulur, 3 karo baş boşluğu açılır.
	for cx in range(x0 + 1, mini(W - 2, x0 + 8)):
		for yy in range(y0 - 2, y0 + 1):
			_put(g, cx, yy, W, H, 0)
		if _cell(g, cx, y0 + 1, W, H) == 0:
			_put(g, cx, y0 + 1, W, H, 1)
		heights[cx] = y0 + 1


static func _reachable(g: PackedByteArray, W: int, H: int, heights: Array) -> bool:
	return _reach(_haz_as_air(g), W, H, heights)["ok"]


static func _haz_as_air(g: PackedByteArray) -> PackedByteArray:
	var c := g.duplicate()
	for i in c.size():
		if c[i] == 3:
			c[i] = 0
	return c


static func guarantee(g: PackedByteArray, W: int, H: int, heights: Array) -> int:
	## Girişten çıkışa yol yoksa takılan yerden koridor açar; açılan koridor sayısını döndürür.
	var n := 0
	for i in 80:
		var r := _reach(_haz_as_air(g), W, H, heights)
		if r["ok"]:
			return n
		_carve(g, W, H, heights, int(r["x"]), int(r["y"]))
		n += 1
	return n
