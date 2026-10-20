class_name LevelGen
extends RefCounted
## v33 bölüm üretimi: küçük Dead Cells mağaraları (v32 oda çizgesinin küçültülmüş, hızlandırılmış hâli).
##
## Bölüm SW x SH = 24 x 13 karolık "kesim"lerden (sektör) bir ızgaradır (stil başına sütun / satır STIL'de; en çok
## 7 x 4 = Level.W x Level.H = 172 x 56 karo; v32: 256 x 90). Her kesime KÜÇÜK bir oda oturur (12-20 karo geniş,
## 6-9 karo hava yüksekliği, basamaklı tavan; kenarlarından 0-6 karo daralır). Yan yana odalar DAR KORİDORLA (4-16 karo
## uzun, 4-5 karo yüksek) bağlanır; üst üste odalar KUYUYLA: üst odanın tabanında 3 karoluk DÜŞÜŞ deliği (ana yol aşağı iniyorsa
## açık, değilse tek yönlü kapak: aşağı + zıpla ile düşülür) ve yanında ince ara duvarla ayrılmış 2 karoluk TIRMANIŞ
## bacası (3 satırda bir tek yönlü basamak; tepesi kapaklı). Aşağı iniş tek düşüştür; geri çıkış birkaç zıplama.
## Oda tabanları düzdür: kesimler arası taban farkı en çok 3 karo (yan kapı eşiği tek zıplama); merdiven / teras
## zinciri, zikzak basamak yok.
##
## Çizge v32'deki gibi: giriş (sol sütun) -> çıkış (sağ sütun) ANA YOL (iniş stillerinde düşerek iner; bir düşüşten
## sonra 1-2 kesim geri dönebilir: yılan); 2-4 DAL (1-2 oda; sonu ÇIKMAZ ödül odası: tomar, hazine, sunak, pazar,
## seçkin bekçisi, zamanlı kapı); komşu odalar arasında DÖNGÜ kapıları; yan yana ana yol odalarının birleşip geniş salon
## olması. Odaların içi türüne göre süslenir (salon, mağara, harabe, çukur, köprü, kuyu (tek yönlü üst güverte), kule,
## teras: tek basamak). Kut Taşları: giriş, ana yolun ortasındaki kavşak, uzak ödül odaları (3-4).
##
## Izgara değerleri: 0 hava, 1 katı, 2 tek yönlü platform, 3 tehlike. v25 kuralları korunur: yürünen her hücrede
## en az BAS_BOSLUGU (3) karo baş boşluğu (_open_headroom), yalnızca yuvarlanarak geçilen yer yok. Erişim modeli
## (_moves: tek / çift zıplama en çok 4 karo yukarı, ±5 sütun; düşüş 15 satır) ile girişten çıkışa yol ve her
## ulaşılan hücreden çıkışa dönüş (traps / fix_traps) denetlenir; geçmeyen taslak yeniden üretilir.
##
## generate(...) döndürür: grid, heights (ana yol odasının tabanı; eski surface_y için), style, chunks (ödül odası
## işaretleri: Level._place_rooms), rooms, doors, path (ana yol kesimleri), spawn / exit (karo), tasi (Kut Taşı
## karoları), zamanli (zamanlı kapı sütunları), kaide (eşya kaidesi karoları), bounds (dolu kesimlerin sıkı kutusu),
## metrics; v34: cepler (gizli cep: çatlak duvar karoları, cep alanı, içerik), kilitli (kilitli kapı sütunu), pencereler
## (parmaklık karoları). Bkz. aşağıdaki v34 sabitleri.

const STYLES := ["orman", "ucurum", "magara", "harabe", "bozkir", "kuyu"]
## v25: yürünen hücrelerin üstünde açık kalması gereken en az karo (ayakta durulan karo dahil; 3 karo = 72 px)
const BAS_BOSLUGU := 3
## Kesim (sektör) boyu: duvarlar dahil; odanın en geniş iç alanı (SW - 4) x 9 karo (yarım ekran kadar)
const SW := 24
const SH := 13
const KENAR := 2
## Kuyu: düşüş bacası 3 + ara duvar 1 + tırmanış bacası 2 sütun
const KUYU_W := 6

## Stil parametreleri: kesim ızgarası (sütun x satır), gök açık mı (üst satır odalarının tavanı yok), ana yolun yönü
## (inis: giriş üstte / çıkış altta; cikis: tersi; serbest), oda türü havuzu, dal sayısı, döngü / birleşme eğilimleri,
## tavan dalgası (mağara tavanı)
const STIL := {
	"orman": {"cols": 7, "rows": 3, "acik": true, "yon": "inis", "kinds": ["salon", "teras", "kopru", "salon", "cukur", "harabe"],
		"dal": [2, 4], "dongu": 0.3, "genis": 0.25, "tavan": 0},
	"ucurum": {"cols": 7, "rows": 4, "acik": true, "yon": "inis", "kinds": ["teras", "kopru", "kule", "cukur", "teras", "salon"],
		"dal": [2, 4], "dongu": 0.25, "genis": 0.15, "tavan": 0},
	"magara": {"cols": 7, "rows": 4, "acik": false, "yon": "inis", "kinds": ["magara", "magara", "kuyu", "cukur", "salon", "magara"],
		"dal": [3, 4], "dongu": 0.35, "genis": 0.2, "tavan": 2},
	"harabe": {"cols": 7, "rows": 4, "acik": false, "yon": "serbest", "kinds": ["harabe", "kule", "salon", "kuyu", "kopru", "harabe"],
		"dal": [2, 4], "dongu": 0.3, "genis": 0.25, "tavan": 1},
	"bozkir": {"cols": 7, "rows": 3, "acik": true, "yon": "serbest", "kinds": ["salon", "teras", "salon", "cukur", "kopru", "harabe"],
		"dal": [2, 3], "dongu": 0.35, "genis": 0.4, "tavan": 0},
	"kuyu": {"cols": 6, "rows": 4, "acik": false, "yon": "inis", "kinds": ["kuyu", "magara", "kule", "cukur", "kopru", "kuyu"],
		"dal": [2, 4], "dongu": 0.3, "genis": 0.1, "tavan": 2},
}

## Oda türüne göre hava yüksekliği (taban - tavan, karo): en az / en çok
const YUK := {"salon": [5, 8], "magara": [6, 9], "harabe": [6, 9], "cukur": [6, 8], "kopru": [6, 8], "teras": [6, 9],
	"kuyu": [8, 9], "kule": [7, 9], "odul": [5, 7], "giris": [6, 8]}

## Çıkmaz ödülleri (öncelik sırası; pazar istenirse başa eklenir). tomar: Kut Tomarı kaidesi; hazine: üst kademe
## eşya + altın (yükseltilmiş seki); sunak: tanrı lütfu; seckin: seçkin bekçi + eşya; zamanli: bölüm başından 90 sn
## içinde ulaşılırsa açık kalan kapı, ardında üst kademe eşya + altın
const ODULLER := ["tomar", "hazine", "sunak", "seckin", "zamanli", "tomar", "hazine"]
const ZAMANLI_SURE := 90.0

## Eski parça sözlüğü: ödül odası işaretleri (Level._place_rooms, tuccar_testi; "T" hazine kaidesi, "S" sunak, "E" seçkin,
## "M" tomar kaidesi, "P" pazar tezgâhı, "Z" zamanlı kapı ödülü; v34: "L" lanetli sandık, "K" anahtar)
const CHUNKS := {
	"hazine": ["   T   "],
	"sunak": ["   S   "],
	"seckin": ["  E T  "],
	"tomar": ["   M   "],
	"pazar": ["   P   "],
	"lanetli": ["   L   "],
	"zamanli": ["   Z   "],
}

## v34 merak uyandıran bölümler (Dead Cells: görünür ama ulaşılmaz ödüller, gizli duvarlar, anahtarlı kapı, lanetli
## sandık; Kut Kapısı ana yolun ucunda değil):
##   SAPAK_SANS: Kut Kapısı ana yolun son yarısındaki bir kavşaktan (stil yönünde, kapaklı kuyu ya da yan koridor)
##   ayrılan çıkmaz odadadır; görünen koridor sapaktan sonra "uzantı" olarak sürer ve bir ödül odasında (seçkin bekçi /
##   lanetli sandık / hazine) biter.
##   PENCERE: ana yol odasının kapısız yanında demir parmaklıklı pencere; ardındaki ödül odasına yalnızca başka bir
##   kavşaktan dolaşarak (0-1 ara oda) varılır.
##   Gizli cepler (kırık duvar): oda kenarında çatlak mürekkep duvarı (1 sütun, 4 karo); vurulunca açılır, ardında 4 x 4
##   cep (altın / Kut / şifa / eşya / anahtar). Cep üretimde oyulmaz (Level kırınca oyar): erişim denetimi değişmez.
##   KILIT_SANS: yan kapılı bir ödül odasının koridoru kilitli (anahtar bölümde: önce gizli cepte, yoksa başka ödül odasında).
const SAPAK_SANS := 0.95
const PENCERE_EK := 0.4      # ikinci pencere dalı olasılığı
const KILIT_SANS := 0.75
const CEP_SAYI := [2, 3]
const UZANTI_ODUL := ["seckin", "lanetli", "hazine", "lanetli", "seckin"]

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
	var rows := clampi(int(opts.get("rows", P["rows"])), 1, (H - 2 * KENAR) / SH)
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
			# v33: çoğunlukla iner (Dead Cells ana yolları aşağı / yana akar); %25 çıkış girişten bir kat yüksekte
			sr = rng.randi_range(0, maxi(0, rows - 2))
			er = rng.randi_range(mini(rows - 1, sr + 1), rows - 1)
			if rows > 1 and rng.randf() < 0.25:
				er = rng.randi_range(0, rows - 2)
				sr = er + 1
	var path := _ana_yol(rng, cols, rows, sr, er, yon)
	# v34: Kut Kapısı sapağı: yol sapaktan sonra "uzantı" olarak sürer (sonu ödül), kapı yandaki çıkmaz odada
	var uzanti: Array = []
	if rng.randf() < SAPAK_SANS:
		var sap := _cikis_sapagi(rng, path, cols, rows, yon)
		if not sap.is_empty():
			path = sap[0]
			uzanti = sap[1]
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
			if i == path.size() - 1 and not uzanti.is_empty():
				# v34: Kut Kapısı odasına sapak: kuyuysa kapaklı (yürürken düşülmez: oyuncu seçer), yansa koridor
				doors[doors.size() - 1]["kapak"] = true
				rooms[id]["sapak"] = true
	# ödül sırası: tomar ve hazine kesin, kalanı (sunak / seçkin / zamanlı) karışık; pazar istenirse en başa
	var oduller: Array = ["tomar", "hazine"]
	var rest: Array = ["sunak", "seckin", "zamanli"]
	_shuffle(rng, rest)
	oduller.append_array(rest)
	oduller.append_array(["tomar", "hazine"])
	if bool(opts.get("pazar", false)):
		oduller.push_front("pazar")
	var n_dal := 0
	var n_cikmaz := 0
	# --- v34 uzantı: sapaktan sonra süren görünür koridor (dal odaları), sonu ödül odası
	var n_uzanti := uzanti.size()
	if not uzanti.is_empty():
		var prev: Vector2i = path[path.size() - 2]
		rooms[int(owner[prev.x][prev.y])]["kavsak"] = true
		var last := -1
		for ui in uzanti.size():
			var uc: Vector2i = uzanti[ui]
			last = _new_room(rooms, owner, uc, "dal")
			rooms[last]["uzanti"] = true
			rooms[last]["uz_i"] = path.size() - 1 + ui   # ana yol sırasının devamı (pencere / dal puanlaması)
			_add_door(doors, rooms, owner, prev, uc, "uzanti")
			doors[doors.size() - 1]["ileri"] = uc
			prev = uc
		rooms[last]["role"] = "odul"
		rooms[last]["odul"] = String(UZANTI_ODUL[rng.randi_range(0, UZANTI_ODUL.size() - 1)])
		rooms[last]["dal_uz"] = uzanti.size()
		n_dal += 1
		n_cikmaz += 1
	# --- v34 pencere dalları: ana yoldan parmaklık ardında görünen ödül, dolaşarak varılır
	var n_pencere := 0
	for t in 2:
		if t == 1 and rng.randf() >= PENCERE_EK:
			break
		var odl := "tomar" if oduller.has("tomar") and rng.randf() < 0.5 else "hazine"
		if _pencere_dali(rng, rooms, owner, doors, cols, rows, odl):
			oduller.erase(odl)
			n_pencere += 1
			n_dal += 1
			n_cikmaz += 1
	# --- dallar: kavşaklardan boş kesimlere 1-2 odalık yürüyüş, sonu çıkmaz (ödül)
	var dal_n: int = rng.randi_range(int(P["dal"][0]), int(P["dal"][1]))
	var junctions: Array = []
	for i in range(1, path.size() - 1):
		junctions.append(i)
	if bool(opts.get("pazar", false)) and bool(opts.get("pazar_kapi", false)):
		# boss öncesi: pazar çıkışa yakın kavşaktan ayrılır
		junctions.reverse()
	else:
		# v34: dallar ERKEN ayrılır (Dead Cells: ödül yolları bölümün başında görünür; çıkışa koşan oyuncu "bir şey
		# kaçırdım" der): kavşak sırası yol başına ağırlıklı, rastgele karışık
		var keyed: Array = []
		for i in junctions:
			keyed.append([float(i) / float(path.size()) + rng.randf() * 0.55, i])
		keyed.sort_custom(func(a: Array, b: Array) -> bool: return float(a[0]) < float(b[0]))
		junctions.clear()
		for kk in keyed:
			junctions.append(int(kk[1]))
	# yedek kavşaklar: çıkış ve giriş odası (ara odalardan dal çıkmazsa; en az 2 çıkmaz için)
	junctions.append(path.size() - 1)
	junctions.append(0)
	for ji in junctions:
		if n_dal - (1 if n_uzanti > 0 else 0) >= dal_n:
			break
		if ji == path.size() - 1 and n_uzanti > 0:
			continue   # v34: sapaktaki Kut Kapısı odası tek kapılı çıkmaz kalır
		var cur: Vector2i = path[ji]
		var chain: Array = []
		var ln := 1 + (1 if rng.randf() < 0.35 else 0)
		var prev := cur
		for step in ln:
			var opts2: Array = []
			for d in [Vector2i(0, -1), Vector2i(0, 1), Vector2i(1, 0), Vector2i(-1, 0)]:
				var n: Vector2i = prev + d
				if n.x < 0 or n.x >= cols or n.y < 0 or n.y >= rows or owner[n.x][n.y] >= 0:
					continue
				# v33: yan dal (koridor) ağırlıklı; dikey dal: kapaklı düşüşle inilen / birkaç zıplamayla çıkılan ödül
				var w := 1 if d.y != 0 else 2
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
	# v34: pazar istendiyse ve hiçbir dala düşmediyse (pencere / uzantı dalları sayıyı doldurdu) bir ödül odası pazar
	# olur: boss öncesinde uzantının sonu (çıkışa yakın), değilse sıradan dal, yoksa uzantı / pencere odası
	if oduller.has("pazar"):
		var aday: Dictionary = {}
		var puan := -1
		for rm in rooms:
			if rm["role"] != "odul":
				continue
			var p := 1
			if bool(rm.get("pencere", false)):
				p = 0
			elif bool(rm.get("uzanti", false)):
				p = 3 if bool(opts.get("pazar_kapi", false)) else 1
			else:
				p = 2
			if p > puan:
				puan = p
				aday = rm
		if not aday.is_empty():
			aday["odul"] = "pazar"
			oduller.erase("pazar")
	# --- döngüler: kapısız komşu odalar arasında (ödül odaları tek kapılı kalır)
	var n_dongu := 0
	for c in cols:
		for r in rows:
			var a: int = owner[c][r]
			if a < 0 or rooms[a]["role"] == "odul" or bool(rooms[a].get("sapak", false)):
				continue
			for d in [Vector2i(1, 0), Vector2i(0, 1)]:
				var n: Vector2i = Vector2i(c, r) + d
				if n.x >= cols or n.y >= rows:
					continue
				var b: int = owner[n.x][n.y]
				# v34: sapaktaki Kut Kapısı odası tek kapılı (uzantıdan döngüyle kapıya düşülmesin)
				if b < 0 or b == a or rooms[b]["role"] == "odul" or bool(rooms[b].get("sapak", false)) or _has_door(doors, a, b):
					continue
				if rng.randf() < float(P["dongu"]):
					_add_door(doors, rooms, owner, Vector2i(c, r), n, "dongu")
					n_dongu += 1
	# --- birleşme: yan yana ana yol odaları geniş salon (ödül odaları ve giriş birleşmez; v33: üst üste birleşme yok,
	# dikey geçiş hep kuyu)
	var n_genis := 0
	for i in range(path.size() - 1):
		var a: Vector2i = path[i]
		var b: Vector2i = path[i + 1]
		var ra: int = owner[a.x][a.y]
		var rb: int = owner[b.x][b.y]
		if ra == rb or rooms[ra]["role"] == "giris" or bool(rooms[rb].get("sapak", false)) or (rooms[ra]["cells"] as Array).size() > 1 or (rooms[rb]["cells"] as Array).size() > 1:
			continue
		if b.y == a.y and rng.randf() < float(P["genis"]):
			_merge(rooms, owner, doors, ra, rb)
			n_genis += 1
	# --- oda türleri, kutular, taban / tavan profilleri
	var kinds: Array = P["kinds"]
	for rm in rooms:
		if rm["role"] == "yok":
			_room_rect(rm)
			continue
		var cells: Array = rm["cells"]
		var role: String = rm["role"]
		if role == "odul":
			rm["kind"] = "odul"
		elif role == "giris":
			rm["kind"] = "salon"
		elif cells.size() > 1:
			rm["kind"] = ["salon", "harabe", "teras", "kopru", "kuyu"][rng.randi_range(0, 4)]
		else:
			rm["kind"] = String(kinds[rng.randi_range(0, kinds.size() - 1)])
		rm["acik"] = bool(P["acik"]) and int((cells[0] as Vector2i).y) == 0
		rm["clear"] = []
		rm["kuyular"] = []
		_room_box(rng, rm, doors)
		_profile(rng, rm, int(P["tavan"]))
	# --- kapı geometrisi (yan koridorlar, kuyular)
	for dr in doors:
		_door_geometry(rng, rooms, dr)
	# pazar dikey kapılı odaya düştüyse yan kapılı başka bir ödül odasıyla yer değiştirir (tüccar istendiyse kaybolmasın;
	# boss öncesi Bezirgân kesin). Yan kapılı ödül odası yoksa kuyulu odada kalır: tezgâh _odul_mid ile kuyudan uzak yana
	# kurulur (kuyu odanın bir ucuna yaslanır).
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
	# v34 kilitli ödül odası: yan kapılı (pazar, zamanlı, pencereli değil); anahtar sonra (_anahtar_yeri)
	var kilit_rm: Dictionary = {}
	if rng.randf() < KILIT_SANS:
		var kc: Array = []
		for rm in rooms:
			if rm["role"] == "odul" and String(rm.get("_door_side", "sol")) in ["sol", "sag"] and not (String(rm["odul"]) in ["pazar", "zamanli"]) and not bool(rm.get("pencere", false)):
				kc.append(rm)
		if not kc.is_empty():
			kilit_rm = kc[rng.randi_range(0, kc.size() - 1)]
			kilit_rm["kilit"] = true
	# Kut Kapısı önü (çıkış odasının sağ ucu, 9 sütun) düz ve boş kalır: sütun / kaya / çukurcuk / tehlike yok.
	# v34: kapı odaya sağdaki koridordan giriliyorsa (sapak) Kut Kapısı odanın SOL ucunda (kapıdan uzak yan)
	for rm in rooms:
		if rm["role"] == "cikis":
			rm["cikis_sol"] = bool(rm["_sag"]) and not bool(rm["_sol"])
			if bool(rm["cikis_sol"]):
				(rm["clear"] as Array).append(Rect2i(int(rm["ix0"]), 0, 10, 999))
			else:
				(rm["clear"] as Array).append(Rect2i(int(rm["ix1"]) - 9, 0, 10, 999))
	# --- oyma
	for rm in rooms:
		if rm["role"] != "yok":
			_carve_room(grid, W, H, rm)
	for rm in rooms:
		if rm["role"] != "yok":
			_features(grid, W, H, rng, rm, style)
	var n_kuyu := 0
	var n_acik := 0
	for dr in doors:
		_carve_door(grid, W, H, rooms, dr)
		if dr["kind"] != "sil" and dr["dir"] == "v":
			n_kuyu += 1
			if bool(dr.get("acik", false)):
				n_acik += 1
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
			var mk := _odul_marks(grid, W, H, rng, rm, zamanli, doors)
			chunks.append({"name": String(rm["odul"]), "x": int(rm["ix0"]), "marks": mk, "room": int(rm["id"])})
		elif rm["role"] in ["ana", "dal"]:
			_hazard_strips(grid, W, H, rng, rm, style)
	# v34 gizli cepler (kırık duvar), kilitli kapı ve anahtarı
	var cepler := _gizli_cepler(grid, W, H, rng, rooms)
	var kilitli: Array = []
	if not kilit_rm.is_empty():
		var kd := _yan_kapi_sutunu(kilit_rm, doors)
		var anahtar := false
		var cc: Array = []
		for cp in cepler:
			if int(cp["room"]) != int(kilit_rm["id"]):
				cc.append(cp)
		if not cc.is_empty():
			cc[rng.randi_range(0, cc.size() - 1)]["icerik"] = "anahtar"
			anahtar = true
		else:
			# gizli cep yoksa: başka bir ödül odasının köşesinde (pazar / kilitli değil)
			for ch in chunks:
				var orm: Dictionary = rooms[int(ch["room"])]
				if orm == kilit_rm or String(orm["odul"]) == "pazar":
					continue
				var kx := clampi(_odul_mid(orm) + (4 if _door_side(orm) != "sag" else -4), int(orm["ix0"]) + 2, int(orm["ix1"]) - 2)
				var ks := _floor_spot(grid, W, H, orm, kx)
				(ch["marks"] as Array).append(["K", ks.x, ks.y])
				anahtar = true
				break
		if anahtar:
			kilitli.append({"x": kd.x, "y": kd.y, "room": int(kilit_rm["id"])})
		else:
			kilit_rm["kilit"] = false
	# Kut Taşları (3-4): giriş (girişin 9 karo sağı); ana yolun ortasına en yakın kavşak (yoksa orta oda); girişten en
	# uzak 1-2 ödül odası (kapıya yakın)
	var g_rm: Dictionary = rooms[0]
	var spawn := Vector2i(int(g_rm["ix0"]) + 3, int(g_rm["fl"][3]) - 1)
	tasi.append(_floor_spot(grid, W, H, g_rm, int(g_rm["ix0"]) + 9))
	var nm := main_rooms.size()
	var mid_rm: Dictionary = main_rooms[nm / 2]
	var mid_d := 999
	for rm in main_rooms:
		if bool(rm.get("kavsak", false)) and rm["role"] == "ana" and absi(int(rm["ana_i"]) - nm / 2) < mid_d:
			mid_d = absi(int(rm["ana_i"]) - nm / 2)
			mid_rm = rm
	_tasi_ekle(tasi, _floor_spot(grid, W, H, mid_rm, (int(mid_rm["ix0"]) + int(mid_rm["ix1"])) / 2))
	var odul_rooms: Array = []
	for rm in rooms:
		if rm["role"] == "odul":
			odul_rooms.append(rm)
	var uzak := func(a: Dictionary, b: Dictionary) -> bool: return absi(int(a["ix0"]) - spawn.x) + 2 * absi(int(a["iy1"]) - spawn.y) > absi(int(b["ix0"]) - spawn.x) + 2 * absi(int(b["iy1"]) - spawn.y)
	odul_rooms.sort_custom(uzak)
	for rm in odul_rooms:
		if tasi.size() >= 4:
			break
		_tasi_ekle(tasi, _odul_tasi(grid, W, H, rm))
	if tasi.size() < 3:
		# yedek: ana yolun 3/4'ündeki oda
		var rq: Dictionary = main_rooms[clampi(nm * 3 / 4, 1, nm - 1)]
		tasi.append(_floor_spot(grid, W, H, rq, (int(rq["ix0"]) + int(rq["ix1"])) / 2))
	# eşya kaideleri: ana yolun 1/4, 2/4, 3/4'ündeki odaların ortası
	for q in [0.25, 0.5, 0.75]:
		var rm: Dictionary = main_rooms[clampi(int(round(q * (nm - 1))), 1, nm - 1)]
		kaide.append(_floor_spot(grid, W, H, rm, _bos_sutun(rm, (int(rm["ix0"]) + int(rm["ix1"])) / 2 + rng.randi_range(-3, 3))))
	# çıkış: çıkış odasının sağ ucu (v34: kapı odaya sağdan giriliyorsa sol ucu)
	var e_rm: Dictionary = main_rooms[nm - 1]
	var exit := _floor_spot(grid, W, H, e_rm, int(e_rm["ix0"]) + 4 if bool(e_rm.get("cikis_sol", false)) else int(e_rm["ix1"]) - 4)
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
		if rm["role"] == "yok":
			continue
		rmin = mini(rmin, int(rm["r0"]))
		rmax = maxi(rmax, int(rm["r1"]))
	var metrics := {"oda": rooms.size() - n_genis, "ana": path.size(), "dal": n_dal, "cikmaz": n_cikmaz, "dongu": n_dongu,
		"genis": n_genis, "yuksek": 0, "dikey_adim": dikey_adim, "satir": rmax - rmin + 1, "kapi": doors.size() - n_genis,
		"tasi": tasi.size(), "zamanli": zamanli.size(), "cols": cols, "rows": rows, "kuyu": n_kuyu, "acik_kuyu": n_acik}
	# v34 ölçümleri: sapak / uzantı, pencere, gizli cep, kilit, dalların ayrıldığı yer (ana yol sırası / uzunluk)
	var pencereler: Array = []
	for dr in doors:
		if dr["kind"] == "pencere" and dr.has("parmak"):
			pencereler.append({"cells": dr["parmak"], "a": int(dr["a"]), "b": int(dr["b"])})
	var kav_sum := 0.0
	var kav_n := 0
	for dr in doors:
		if not (dr["kind"] in ["dal", "pencere_dal"]):
			continue
		for k in ["a", "b"]:
			var jr: Dictionary = rooms[int(dr[k])]
			if int(jr.get("ana_i", -1)) >= 0:
				kav_sum += float(jr["ana_i"]) / float(maxi(1, path.size() - 1))
				kav_n += 1
	metrics["sapak"] = 1 if n_uzanti > 0 else 0
	metrics["uzanti"] = n_uzanti
	metrics["pencere"] = pencereler.size()
	metrics["cep"] = cepler.size()
	metrics["kilit"] = kilitli.size()
	metrics["dal_yeri"] = kav_sum / maxf(1.0, float(kav_n))
	var bnd := _sinirlar(grid, W, H)
	for cp in cepler:
		bnd = bnd.merge((cp["cep"] as Rect2i).grow(2)).intersection(Rect2i(0, 0, W, H))
	return {"grid": grid, "heights": heights, "chunks": chunks, "rooms": rooms, "doors": doors, "path": path, "spawn": spawn,
		"exit": exit, "tasi": tasi, "zamanli": zamanli, "kaide": kaide, "bounds": bnd, "metrics": metrics,
		"cepler": cepler, "kilitli": kilitli, "pencereler": pencereler}


static func _cikis_sapagi(rng: RandomNumberGenerator, path: Array, cols: int, rows: int, yon: String) -> Array:
	## v34: ana yolun son %60'ındaki j. kesimden (yolun sonuna en az bir oda kala) boş bir komşu kesime Kut Kapısı
	## sapağı. Stil yönü korunur (inis: aşağı ya da yana; cikis: yukarı ya da yana). Döndürür [yeni yol (giriş .. j, sapak),
	## uzantı (eski yolun j+1 .. sonu)] ya da boş dizi.
	var n := path.size()
	if n < 5:
		return []
	var seen := {}
	for c in path:
		seen[c] = true
	var cands: Array = []   # [j, kesim, ağırlık]
	for j in range(maxi(2, int(ceil(n * 0.4))), n - 1):
		var cur: Vector2i = path[j]
		for d in [Vector2i(0, 1), Vector2i(0, -1), Vector2i(1, 0), Vector2i(-1, 0)]:
			var e: Vector2i = cur + d
			if e.x < 0 or e.x >= cols or e.y < 0 or e.y >= rows or seen.has(e):
				continue
			var w := 1
			match yon:
				"inis":
					if d.y < 0:
						continue
					w = 3 if d.y > 0 else 1
				"cikis":
					if d.y > 0:
						continue
					w = 3 if d.y < 0 else 1
				_:
					w = 2 if d.y != 0 else 1
			for k in w:
				cands.append([j, e])
	if cands.is_empty():
		return []
	var pick: Array = cands[rng.randi_range(0, cands.size() - 1)]
	var j: int = pick[0]
	var np: Array = path.slice(0, j + 1)
	np.append(pick[1])
	return [np, path.slice(j + 1)]


static func _pencere_dali(rng: RandomNumberGenerator, rooms: Array, owner: Array, doors: Array, cols: int, rows: int, odul: String) -> bool:
	## v34 pencere dalı (Dead Cells'in "görünen ama ulaşılmayan" ödülü): boş R kesimi, yanındaki (yatay) bir yol odası
	## A'ya PARMAKLIKLI PENCEREYLE bakar; R'ye başka bir J odasından (0-1 ara oda) dolaşarak girilir. A erken, J A'dan
	## sonra gelsin (önce görülür, sonra yolu bulunur). true: kuruldu.
	var best: Array = []
	var best_s := -1e9
	var sira := func(id: int) -> float:
		var rm: Dictionary = rooms[id]
		if int(rm.get("ana_i", -1)) >= 0:
			return float(rm["ana_i"])
		return float(rm.get("uz_i", 99))
	var uygun := func(id: int) -> bool:
		if id < 0:
			return false
		var rm: Dictionary = rooms[id]
		return rm["role"] in ["giris", "ana"] or (rm["role"] == "dal" and bool(rm.get("uzanti", false)))
	for c in cols:
		for r in rows:
			if owner[c][r] >= 0:
				continue
			var R := Vector2i(c, r)
			for s in [-1, 1]:
				var A := R + Vector2i(s, 0)
				if A.x < 0 or A.x >= cols or not uygun.call(int(owner[A.x][A.y])):
					continue
				var a_id: int = owner[A.x][A.y]
				for d in [Vector2i(0, 1), Vector2i(0, -1), Vector2i(1, 0), Vector2i(-1, 0)]:
					var X: Vector2i = R + d
					if X == A or X.x < 0 or X.x >= cols or X.y < 0 or X.y >= rows:
						continue
					var xo: int = owner[X.x][X.y]
					if xo >= 0:
						# doğrudan: R, J'ye komşu
						if xo != a_id and uygun.call(xo):
							var sc: float = 1.0 + (2.0 if float(sira.call(xo)) > float(sira.call(a_id)) else 0.0) - 0.15 * float(sira.call(a_id)) + rng.randf() * 0.8
							if sc > best_s:
								best_s = sc
								best = [R, A, X, Vector2i(-1, -1)]
						continue
					# bir ara oda: X boş, X'in komşusu J (R ve A değil)
					for d2 in [Vector2i(0, 1), Vector2i(0, -1), Vector2i(1, 0), Vector2i(-1, 0)]:
						var J: Vector2i = X + d2
						if J == R or J.x < 0 or J.x >= cols or J.y < 0 or J.y >= rows:
							continue
						var jo: int = owner[J.x][J.y]
						if jo == a_id or not uygun.call(jo):
							continue
						var sc2: float = 2.5 + (2.0 if float(sira.call(jo)) > float(sira.call(a_id)) else 0.0) - 0.15 * float(sira.call(a_id)) + rng.randf() * 0.8
						if sc2 > best_s:
							best_s = sc2
							best = [R, A, J, X]
	if best.is_empty():
		return false
	var R2: Vector2i = best[0]
	var A2: Vector2i = best[1]
	var J2: Vector2i = best[2]
	var X2: Vector2i = best[3]
	rooms[int(owner[J2.x][J2.y])]["kavsak"] = true
	var prev := J2
	if X2.x >= 0:
		_new_room(rooms, owner, X2, "dal")
		_add_door(doors, rooms, owner, J2, X2, "dal")
		prev = X2
	var rid := _new_room(rooms, owner, R2, "odul")
	rooms[rid]["odul"] = odul
	rooms[rid]["pencere"] = true
	rooms[rid]["pencere_yan"] = "sol" if A2.x < R2.x else "sag"
	rooms[rid]["dal_uz"] = 2 if X2.x >= 0 else 1
	_add_door(doors, rooms, owner, prev, R2, "dal")
	_add_door(doors, rooms, owner, A2, R2, "pencere")
	return true


static func _yan_kapi_sutunu(rm: Dictionary, doors: Array) -> Vector2i:
	## Yan kapılı ödül odasının koridorunda odaya bitişik sütun ve taban satırı (zamanlı / kilitli kapı: 4 karo geçit)
	var side := _door_side(rm)
	var fl: Array = rm["fl"]
	var dx := int(rm["ix0"]) - 1 if side == "sol" else int(rm["ix1"]) + 1
	var dy := int(fl[0]) if side == "sol" else int(fl[fl.size() - 1])
	for di in rm["doors"]:
		var d: Dictionary = doors[di]
		if d["dir"] == "h" and d["kind"] != "sil" and d["kind"] != "pencere":
			dy = int(d["y"])
	return Vector2i(dx, dy)


static func _gizli_cepler(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rooms: Array) -> Array:
	## v34 gizli cepler: odanın kapısız yan duvarında (taban hizası) 1 sütunluk ÇATLAK DUVAR (4 karo) ve ardında 4 x 4
	## cep. Cep alanı (+1 karo pay) bütünüyle kaya olmalı (koridor / kuyu / başka oda yok). Cep oyulmaz (Level kırınca
	## oyar). İçerik: altın (çoğu), Kut, şifa, eşya ("zula": eski gizli yeraltı odalarının ganimeti), anahtar sonra.
	var want := rng.randi_range(int(CEP_SAYI[0]), int(CEP_SAYI[1]))
	var cands: Array = []
	for rm in rooms:
		if rm["role"] in ["yok", "cikis"] or (rm["fl"] as Array).is_empty():
			continue
		for s in [-1, 1]:
			if (s < 0 and bool(rm["_sol"])) or (s > 0 and bool(rm["_sag"])):
				continue
			cands.append([rm, s])
	_shuffle(rng, cands)
	var out: Array = []
	var used: Array = []
	for cd in cands:
		if out.size() >= want:
			break
		var rm: Dictionary = cd[0]
		var s: int = cd[1]
		var fl: Array = rm["fl"]
		var ex := int(rm["ix1"]) if s > 0 else int(rm["ix0"])        # odanın kenar sütunu
		var fy: int = int(fl[ex - int(rm["ix0"])])
		var ok := true
		# kenar ve yanındaki sütun: tabanı aynı ve katı, üstünde 4 karo hava (çatlak yüzü görünsün, önü yürünür)
		for kx in [ex, ex - s]:
			if _cell(g, kx, fy, W, H) != 1:
				ok = false
			for y in range(fy - 4, fy):
				if _cell(g, kx, y, W, H) != 0:
					ok = false
		if not ok:
			continue
		var wx := ex + s                       # çatlak duvar sütunu
		var px0 := wx + s if s > 0 else wx - 4  # cep sütunları px0 .. px0+3
		# duvar + cep + 1 sütun pay; tavan payı ve taban satırı dahil
		var r := Rect2i(wx, fy - 5, 6, 6) if s > 0 else Rect2i(wx - 5, fy - 5, 6, 6)
		if r.position.x < 2 or r.end.x > W - 2 or r.position.y < 2:
			continue
		for y in range(r.position.y, r.end.y):
			for x in range(r.position.x, r.end.x):
				if _cell(g, x, y, W, H) != 1:
					ok = false
		for u in used:
			if (u as Rect2i).grow(2).intersects(r):
				ok = false
		if not ok:
			continue
		used.append(r)
		var wall: Array = []
		for y in range(fy - 4, fy):
			wall.append(Vector2i(wx, y))
		var roll := rng.randf()
		var ic := "altin"
		if roll < 0.2:
			ic = "zula"
		elif roll < 0.35:
			ic = "kut"
		elif roll < 0.5:
			ic = "sifa"
		out.append({"wall": wall, "cep": Rect2i(px0, fy - 4, 4, 4), "room": int(rm["id"]), "yon": s, "taban": fy, "icerik": ic})
	return out


static func _tasi_ekle(tasi: Array, c: Vector2i) -> void:
	## Kut Taşı yalnızca diğerlerinden uzaksa (16 karo yatay ya da 8 karo dikey)
	for t in tasi:
		if absi(int(t.x) - c.x) < 16 and absi(int(t.y) - c.y) < 8:
			return
	tasi.append(c)


static func _sinirlar(g: PackedByteArray, W: int, H: int) -> Rect2i:
	## Katı olmayan karoların sıkı kutusu + 2 karo pay (kamera ve harita: bölüm parşömene sığar)
	var x0 := W
	var y0 := H
	var x1 := 0
	var y1 := 0
	for y in H:
		for x in W:
			if g[y * W + x] != 1:
				x0 = mini(x0, x)
				x1 = maxi(x1, x)
				y0 = mini(y0, y)
				y1 = maxi(y1, y)
	x0 = maxi(0, x0 - 2)
	y0 = maxi(0, y0 - 2)
	x1 = mini(W - 1, x1 + 2)
	y1 = mini(H - 1, y1 + 2)
	return Rect2i(x0, y0, x1 - x0 + 1, y1 - y0 + 1)


static func _shuffle(rng: RandomNumberGenerator, a: Array) -> void:
	for i in range(a.size() - 1, 0, -1):
		var j := rng.randi_range(0, i)
		var t = a[i]
		a[i] = a[j]
		a[j] = t


static func _ana_yol(rng: RandomNumberGenerator, cols: int, rows: int, sr: int, er: int, yon: String) -> Array:
	## Giriş (0, sr) -> çıkış (cols-1, er): sağa, dikey (stile göre: inis yalnız aşağı, cikis yalnız yukarı, serbest
	## çoğunlukla aşağı ve en çok bir yukarı) ve v33'te bir dikey adımdan sonra 1-2 kesim SOLA (yılan: Dead Cells'in
	## kıvrılan ana yolu). Her adımda çıkışa hâlâ varılabildiği (boş kesimlerden) denetlenir. Hedef uzunluk:
	## sütun + satır farkı + 2-4.
	var target := cols + absi(er - sr) + rng.randi_range(2, 4)
	var goal := Vector2i(cols - 1, er)
	var best: Array = []
	for attempt in 40:
		var path: Array = [Vector2i(0, sr)]
		var seen := {Vector2i(0, sr): true}
		var cur := Vector2i(0, sr)
		var last := Vector2i.ZERO
		var sola := 0
		var up_n := 0
		var guard := 0
		while cur != goal and guard < 80:
			guard += 1
			var cand: Array = []   # [kesim, ağırlık]
			var kalan := target - path.size()   # hedefe kalan oda
			var en_az := (goal.x - cur.x) + absi(goal.y - cur.y)
			if cur.x < cols - 1:
				cand.append([cur + Vector2i(1, 0), 3 if kalan <= en_az + 1 else 2])
			if cur.x > 0 and cur.y != sr and (last.y != 0 or (last.x < 0 and sola < 2)) and kalan >= en_az + 2:
				cand.append([cur + Vector2i(-1, 0), 3])
			for dy in [-1, 1]:
				var w := 0
				match yon:
					"inis":
						w = 3 if dy > 0 else 0
					"cikis":
						w = 3 if dy < 0 else 0
					_:
						w = 2 if dy > 0 else (1 if up_n == 0 else 0)
				if last.y != 0:
					w = mini(w, 1) if dy > 0 else 0   # art arda iki düşüş seyrek; art arda iki tırmanış yok
				if cur.x == cols - 1:
					w = 4 if signi(goal.y - cur.y) == dy else 0
				if w > 0:
					cand.append([cur + Vector2i(0, dy), w])
			var opts: Array = []
			for cd in cand:
				var n: Vector2i = cd[0]
				if n.x < 0 or n.x >= cols or n.y < 0 or n.y >= rows or seen.has(n):
					continue
				if not _yol_varir(seen, n, goal, cols, rows, yon, up_n + (1 if n.y < cur.y else 0)):
					continue
				for k in int(cd[1]):
					opts.append(n)
			if opts.is_empty():
				break
			var nxt: Vector2i = opts[rng.randi_range(0, opts.size() - 1)]
			var mv := nxt - cur
			if mv.x < 0:
				sola += 1
			elif mv.x > 0:
				sola = 0
			if mv.y < 0:
				up_n += 1
			last = mv
			path.append(nxt)
			seen[nxt] = true
			cur = nxt
		if cur == goal:
			if path.size() >= target - 1:
				return path
			if path.size() > best.size():
				best = path
	if not best.is_empty():
		return best
	# yedek: düz sağa, son sütunda dikey
	var p2: Array = []
	for c in cols:
		p2.append(Vector2i(c, sr))
	var r := sr
	while r != er:
		r += signi(er - sr)
		p2.append(Vector2i(cols - 1, r))
	return p2


static func _yol_varir(seen: Dictionary, from: Vector2i, goal: Vector2i, cols: int, rows: int, yon: String, up_n: int) -> bool:
	## from kesiminden çıkışa, görülmemiş kesimlerden (stilin dikey yönü kuralıyla) varılabilir mi
	var q: Array = [from]
	var vis := {from: true}
	var qi := 0
	while qi < q.size():
		var c: Vector2i = q[qi]
		qi += 1
		if c == goal:
			return true
		for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
			if yon == "inis" and d.y < 0:
				continue
			if yon == "cikis" and d.y > 0:
				continue
			if yon == "serbest" and d.y < 0 and up_n > 0:
				continue
			var n: Vector2i = c + d
			if n.x < 0 or n.x >= cols or n.y < 0 or n.y >= rows or seen.has(n) or vis.has(n):
				continue
			vis[n] = true
			q.append(n)
	return false


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
	## ca ile cb komşu kesimler; kapı yönü ca'dan cb'ye (a: sol / üst oda, b: sağ / alt oda)
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
	## Kesim kapsamı (c0..c1, r0..r1) ve en geniş iç alan (kenar duvarları 2 karo)
	var cells: Array = rm["cells"]
	if cells.is_empty():
		for k in ["ix0", "ix1", "iy0", "iy1", "r0", "r1", "c0", "c1"]:
			rm[k] = 0
		rm["fl"] = []
		rm["ce"] = []
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
	rm["iy0"] = KENAR + r0 * SH + 1
	rm["iy1"] = KENAR + r0 * SH + 10


static func _sector_x0(c: int) -> int:
	return KENAR + c * SW


static func _sector_y0(r: int) -> int:
	return KENAR + r * SH


static func _room_box(rng: RandomNumberGenerator, rm: Dictionary, doors: Array) -> void:
	## Odanın kesim içindeki kutusu: yanlardan 0-4 karo daralır (kuyulu oda daha az: kuyu + ödül / tezgâh sığsın);
	## kesim başına taban satırı y0+8..y0+10 (yan yana kesimlerde en çok 2 karo fark), hava yüksekliği türe göre (YUK).
	_room_rect(rm)
	var nv := 0
	var has_l := false
	var has_r := false
	var pen_l := false   # v34: pencere yanı daralmaz (parmaklık ardındaki ödül yakından görünsün)
	var pen_r := false
	for di in rm["doors"]:
		var d: Dictionary = doors[di]
		if d["kind"] == "sil":
			continue
		if d["dir"] == "v":
			nv += 1
		elif int(d["b"]) == int(rm["id"]):
			has_l = true
			pen_l = pen_l or d["kind"] == "pencere"
		else:
			has_r = true
			pen_r = pen_r or d["kind"] == "pencere"
	rm["_sol"] = has_l
	rm["_sag"] = has_r
	rm["_nv"] = nv
	var role: String = rm["role"]
	var maxs := 4
	if role == "giris" or nv >= 2:
		maxs = 0
	elif role == "odul":
		maxs = 0 if nv > 0 else 3
	elif nv == 1 or role == "cikis":
		maxs = 2
	elif (rm["cells"] as Array).size() == 1:
		maxs = 6
	var sl := rng.randi_range(0, maxs)
	var sr := rng.randi_range(0, maxs)
	rm["ix0"] = int(rm["ix0"]) + (0 if pen_l else sl)
	rm["ix1"] = int(rm["ix1"]) - (0 if pen_r else sr)
	var yk: Array = YUK.get("giris" if role == "giris" else String(rm["kind"]), [5, 8])
	var fbs: Array = []
	var hs: Array = []
	for c in range(int(rm["c0"]), int(rm["c1"]) + 1):
		var y0 := _sector_y0(int(rm["r0"]))
		var fb := y0 + 7 + rng.randi_range(0, 3)
		if not fbs.is_empty():
			fb = clampi(fb, int(fbs[fbs.size() - 1]) - 2, int(fbs[fbs.size() - 1]) + 2)
		var hmax := mini(int(yk[1]), fb - (y0 + 1))
		fbs.append(fb)
		hs.append(rng.randi_range(mini(maxi(int(yk[0]) + 1, 6), hmax), hmax))   # oda koridordan (4) belirgin yüksek
	rm["fbs"] = fbs
	rm["hs"] = hs
	rm["fb"] = int(fbs[0])


static func _profile(rng: RandomNumberGenerator, rm: Dictionary, tavan: int) -> void:
	## fl[x] taban satırı (ilk katı), ce[x] tavan (ilk hava satırı). v33: taban kesim başına düz; geniş odada kesim
	## sınırında en çok 2 karoluk tek basamak; teras: kapısız yanda tek 2-3 karoluk seki. Mağara tavanı dalgalı.
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var n := ix1 - ix0 + 1
	var c0 := int(rm["c0"])
	var y0 := _sector_y0(int(rm["r0"]))
	var kind: String = rm["kind"]
	var fl: Array = []
	var ce: Array = []
	fl.resize(n)
	ce.resize(n)
	var p1 := rng.randf() * TAU
	var p2 := rng.randf() * TAU
	var amp := tavan + (1 if kind == "magara" else 0)
	for i in n:
		var k := clampi((ix0 + i - KENAR) / SW - c0, 0, (rm["fbs"] as Array).size() - 1)
		var f: int = int(rm["fbs"][k])
		fl[i] = f
		var cv: int = f - int(rm["hs"][k])
		if amp > 0 and not bool(rm["acik"]):
			cv -= int(round((sin(i * 0.31 + p1) + 1.0) * 0.5 * amp * (0.6 + 0.4 * sin(i * 0.13 + p2))))
		ce[i] = clampi(cv, y0 + 1, f - 5)
		if bool(rm["acik"]):
			ce[i] = 1
	if not bool(rm["acik"]):
		# basamaklı tavan (Dead Cells odalarının girintili çıkıntılı silueti): 4-9 sütunluk parçalar 0-3 karo alçalır;
		# %20 parça tavana açılan cep (3-5 karo yukarı)
		var x := 0
		while x < n:
			var ln := rng.randi_range(4, 9)
			var off := rng.randi_range(0, 3)
			if rng.randf() < 0.2:
				off = -rng.randi_range(3, 5)
			for i in range(x, mini(n, x + ln)):
				ce[i] = clampi(int(ce[i]) + off, y0 + 1, int(fl[i]) - 5)
			x += ln
	if kind == "teras" and n >= 14 and int(rm["_nv"]) == 0 and not (bool(rm["_sol"]) and bool(rm["_sag"])) and rm["role"] != "cikis":
		# tek seki: kapısız yanın 1/3-1/2'si 2-3 karo yüksek (tek zıplama)
		var raise_l: bool = not bool(rm["_sol"]) if bool(rm["_sag"]) else (rng.randf() < 0.5)
		var s := rng.randi_range(n / 3, n / 2)
		var dh := rng.randi_range(2, 3)
		for j in s:
			var i: int = j if raise_l else n - 1 - j
			fl[i] = int(fl[i]) - dh
			if not bool(rm["acik"]):
				ce[i] = mini(int(ce[i]), int(fl[i]) - 5)
	rm["fl"] = fl
	rm["ce"] = ce
	var lo := 999
	var hi := 0
	for i in n:
		lo = mini(lo, int(ce[i]))
		hi = maxi(hi, int(fl[i]))
	rm["iy0"] = lo
	rm["iy1"] = hi


# ================================================================== kapılar
static func _door_geometry(rng: RandomNumberGenerator, rooms: Array, d: Dictionary) -> void:
	## Yan kapı: A'nın sağ kenarından B'nin sol kenarına koridor; taban satırı yd iki odanın kapı yanındaki tabanından
	## yüksek olanı (öbür yanda en çok 2-3 karoluk eşik), 4-5 karo yüksek. Dikey kapı: kuyu (bkz. dosya başı).
	if d["kind"] == "sil":
		return
	var A: Dictionary = rooms[int(d["a"])]
	var B: Dictionary = rooms[int(d["b"])]
	if d["dir"] == "h":
		var fa: int = int(A["fl"][(A["fl"] as Array).size() - 1])
		var fbv: int = int(B["fl"][0])
		var yd := mini(fa, fbv)
		var ch := 4 if (A["role"] == "odul" or B["role"] == "odul" or rng.randf() < 0.8) else 5
		d["x"] = int(A["ix1"]) + 1
		d["x2"] = int(B["ix0"]) - 1
		d["y"] = yd
		d["h"] = ch
		(A["clear"] as Array).append(Rect2i(int(A["ix1"]) - 3, yd - ch - 1, 4, fa - yd + ch + 1))
		(B["clear"] as Array).append(Rect2i(int(B["ix0"]), yd - ch - 1, 4, fbv - yd + ch + 1))
		if d["kind"] == "pencere":
			return   # v34: pencere ödül odasının kapısı değil (kapı yanı / zamanlı kapı / Kut Taşı yeri gerçek kapıdan)
		if A["role"] == "odul":
			A["_door_side"] = "sag"
			A["_door_x"] = int(d["x"])
		if B["role"] == "odul":
			B["_door_side"] = "sol"
			B["_door_x"] = int(d["x2"])
	else:
		var ca: Vector2i = d["ca"]
		var sx := _sector_x0(ca.x)
		var lo := maxi(maxi(int(A["ix0"]), int(B["ix0"])), sx + 2) + 2
		var hi := mini(mini(int(A["ix1"]), int(B["ix1"])), sx + SW - 3) - 2 - (KUYU_W - 1)
		for R in [A, B]:
			if R["role"] == "giris":
				lo = maxi(lo, int(R["ix0"]) + 11)   # doğuş yeri ve giriş taşı (ix0+3, ix0+9) düz kalsın
			if R["role"] == "cikis" and int(R["c1"]) == ca.x:
				hi = mini(hi, int(R["ix1"]) - 8 - (KUYU_W - 1))   # Kut Kapısı (ix1-4) kuyudan uzak
		var cands: Array = []
		for hx in range(lo, maxi(lo, hi) + 1):
			var ok := true
			for R in [A, B]:
				for k in R["kuyular"]:
					if hx <= int(k[1]) + 3 and hx + KUYU_W - 1 >= int(k[0]) - 3:
						ok = false
			if ok:
				cands.append(hx)
		var hx: int = lo
		if not cands.is_empty():
			hx = cands[rng.randi_range(0, cands.size() - 1)]
			if A["role"] == "odul" or B["role"] == "odul":
				hx = cands[0] if rng.randf() < 0.5 else cands[cands.size() - 1]   # ödül / tezgâh öbür yana sığsın
		d["x"] = hx
		d["y"] = int(A["fl"][clampi(hx - int(A["ix0"]), 0, (A["fl"] as Array).size() - 1)])
		d["flip"] = rng.randf() < 0.5
		# ana yol yukarıdan aşağı iniyorsa düşüş deliği açık; dal / döngü / tırmanılan ana yol: tek yönlü kapak
		d["acik"] = d["kind"] == "ana" and int(A["ana_i"]) >= 0 and int(B["ana_i"]) > int(A["ana_i"])
		# v34: uzantı (sapaktan sonra süren yol) aşağı iniyorsa açık düşüş (yol gibi görünür); Kut Kapısı sapağı kapaklı
		if d["kind"] == "uzanti" and d.get("ileri", Vector2i(-1, -1)) == d["cb"]:
			d["acik"] = true
		if bool(d.get("kapak", false)):
			d["acik"] = false
		for R in [A, B]:
			(R["kuyular"] as Array).append([hx, hx + KUYU_W - 1])
			(R["clear"] as Array).append(Rect2i(hx - 1, 0, KUYU_W + 2, 999))
		if A["role"] == "odul":
			A["_door_side"] = "alt"
			A["_door_x"] = hx
		if B["role"] == "odul":
			B["_door_side"] = "ust"
			B["_door_x"] = hx


static func _carve_door(g: PackedByteArray, W: int, H: int, rooms: Array, d: Dictionary) -> void:
	if d["kind"] == "sil":
		return
	var A: Dictionary = rooms[int(d["a"])]
	var B: Dictionary = rooms[int(d["b"])]
	if d["dir"] == "h":
		var yd := int(d["y"])
		var ch := int(d["h"])
		# koridor + iki odanın kenarındaki ağız (oda tavanı alçaksa da geçit açık)
		for x in range(int(A["ix1"]) - 1, int(B["ix0"]) + 2):
			for y in range(yd - ch, yd):
				_put(g, x, y, W, H, 0)
		for x in range(int(d["x"]), int(d["x2"]) + 1):
			_put(g, x, yd, W, H, 1)
		if d["kind"] == "pencere":
			# v34 parmaklıklı pencere: koridorun ortasındaki sütun ızgarada katı (geçilmez; erişim modeli de duvar
			# sayar); Level karosunu siler, yerine görünür demir parmaklık + çarpışma kutusu koyar
			var bx := (int(d["x"]) + int(d["x2"])) / 2
			var cells: Array = []
			for y in range(yd - ch, yd):
				_put(g, bx, y, W, H, 1)
				cells.append(Vector2i(bx, y))
			d["parmak"] = cells
	else:
		var hx := int(d["x"])
		var fyA: int = int(A["fl"][clampi(hx - int(A["ix0"]), 0, (A["fl"] as Array).size() - 1)])
		var fyB: int = int(B["fl"][clampi(hx - int(B["ix0"]), 0, (B["fl"] as Array).size() - 1)])
		d["y"] = fyA
		d["y2"] = fyB
		var flip: bool = d["flip"]
		var dx0 := hx + 3 if flip else hx          # düşüş bacası (3)
		var wx := hx + 2 if flip else hx + 3       # ara duvar (1)
		var cx0 := hx if flip else hx + 4          # tırmanış bacası (2)
		d["dus_x"] = dx0
		d["tir_x"] = cx0
		for x in range(dx0, dx0 + 3):
			for y in range(fyA, fyB):
				_put(g, x, y, W, H, 0)
			if not bool(d["acik"]):
				_put(g, x, fyA, W, H, 2)   # kapak: üstünden yürünür, aşağı + zıpla ile düşülür
		for x in range(cx0, cx0 + 2):
			for y in range(fyA + 1, fyB):
				_put(g, x, y, W, H, 0)
			_put(g, x, fyA, W, H, 2)
		for y in range(fyA, fyB - 3):
			_put(g, wx, y, W, H, 1)
		# tırmanış basamakları: tepeden 3 satırda bir; tabana 4 kalırsa ara basamak (2)
		var rungs: Array = []
		var r := fyA
		while fyB - (r + 3) >= 2:
			r += 3
			rungs.append(r)
		if fyB - r == 4:
			rungs.append(fyB - 2)
		for ry in rungs:
			for x in range(cx0, cx0 + 2):
				_put(g, x, ry, W, H, 2)


# ================================================================== oda oyma ve süsler
static func _carve_room(g: PackedByteArray, W: int, H: int, rm: Dictionary) -> void:
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var fl: Array = rm["fl"]
	var ce: Array = rm["ce"]
	for x in range(ix0, ix1 + 1):
		var i := x - ix0
		for y in range(int(ce[i]), int(fl[i])):
			_put(g, x, y, W, H, 0)


static func _in_clear(rm: Dictionary, x: int, y: int) -> bool:
	for c in rm["clear"]:
		if (c as Rect2i).has_point(Vector2i(x, y)):
			return true
	return false


static func _bos_sutun(rm: Dictionary, x: int) -> int:
	## x'e en yakın, kuyu / kapı ağzı bölgesine girmeyen sütun (taban hizasında)
	var fl: Array = rm["fl"]
	for d in range(0, 20):
		for s in ([0] if d == 0 else [1, -1]):
			var cx := clampi(x + d * s, int(rm["ix0"]) + 1, int(rm["ix1"]) - 1)
			if not _in_clear(rm, cx, int(fl[cx - int(rm["ix0"])]) - 1):
				return cx
	return x


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
	## Oda türüne göre iç parçalar (küçük odaya ölçekli): tek yönlü platformlar (tabandan 3 karo: tek zıplama),
	## sütunlar, kemer, sarkıtlar, kayalar, yan cepler, çukur, köprü, üst güverte
	var kind: String = rm["kind"]
	var role: String = rm["role"]
	if role == "odul":
		_odul_shape(g, W, H, rng, rm)
		return
	if role == "giris":
		_platforms(g, W, H, rng, rm, 1, 3, 3)
		_alcoves(g, W, H, rng, rm, rng.randi_range(0, 1))
		return
	var kx := 2 if (rm["cells"] as Array).size() > 1 else 1
	match kind:
		"salon":
			_platforms(g, W, H, rng, rm, rng.randi_range(1, 2) * kx, 3, 3)
			_pillars(g, W, H, rng, rm, rng.randi_range(0, 1) * kx)
			_dips(g, W, H, rng, rm, rng.randi_range(0, 1))
			_alcoves(g, W, H, rng, rm, rng.randi_range(0, 1))
			_stalactites(g, W, H, rng, rm, rng.randi_range(0, 1) * kx, 2)
		"teras":
			_platforms(g, W, H, rng, rm, rng.randi_range(1, 2) * kx, 3, 3)
			_alcoves(g, W, H, rng, rm, rng.randi_range(0, 1))
		"harabe":
			_pillars(g, W, H, rng, rm, rng.randi_range(1, 2) * kx)
			_arches(g, W, H, rng, rm, rng.randi_range(0, 1) * kx)
			_platforms(g, W, H, rng, rm, rng.randi_range(0, 1) * kx, 3, 3)
			_alcoves(g, W, H, rng, rm, rng.randi_range(0, 1))
			_stalactites(g, W, H, rng, rm, rng.randi_range(0, 1), 2)
		"magara":
			_stalactites(g, W, H, rng, rm, rng.randi_range(2, 4) * kx, 2)
			_boulders(g, W, H, rng, rm, rng.randi_range(1, 3) * kx)
			_platforms(g, W, H, rng, rm, rng.randi_range(0, 1) * kx, 3, 3)
			_alcoves(g, W, H, rng, rm, rng.randi_range(1, 2))
		"cukur":
			_pit(g, W, H, rng, rm)
			_platforms(g, W, H, rng, rm, rng.randi_range(0, 1) * kx, 3, 3)
			_stalactites(g, W, H, rng, rm, rng.randi_range(0, 1), 2)
		"kopru":
			_bridge(g, W, H, rng, rm)
			_stalactites(g, W, H, rng, rm, rng.randi_range(0, 1), 2)
		"kuyu":
			_deck(g, W, H, rng, rm)
			_alcoves(g, W, H, rng, rm, rng.randi_range(0, 1))
			_stalactites(g, W, H, rng, rm, rng.randi_range(0, 2) * kx, 2)
		"kule":
			_pillars(g, W, H, rng, rm, 1 * kx)
			_platforms(g, W, H, rng, rm, rng.randi_range(1, 2) * kx, 3, 4)
			_alcoves(g, W, H, rng, rm, rng.randi_range(0, 1))


static func _platforms(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rm: Dictionary, count: int, h0: int, h1: int) -> void:
	## Tek yönlü platformlar (3-5 karo) tabandan h0-h1 karo yukarıda; üstünde 3, altında 2 karo boşluk
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var fl: Array = rm["fl"]
	var tries := 0
	var placed := 0
	while placed < count and tries < 30:
		tries += 1
		var ln := rng.randi_range(3, 5)
		if ix1 - ln - 2 < ix0 + 2:
			return
		var x := rng.randi_range(ix0 + 2, ix1 - ln - 2)
		var y: int = int(fl[x - ix0]) - rng.randi_range(h0, h1)
		if not _free_span(g, W, H, rm, x, y, ln, 3, 2):
			continue
		var flat := true
		for k in ln:
			if int(fl[x + k - ix0]) != int(fl[x - ix0]):
				flat = false
		if not flat:
			continue
		for k in ln:
			_put(g, x + k, y, W, H, 2)
		placed += 1


static func _pillars(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rm: Dictionary, count: int) -> void:
	## Yıkık taş sütunlar (2 karo geniş, 2 yüksek) tabanda; üstünden tek zıplamayla geçilir
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var fl: Array = rm["fl"]
	var tries := 0
	var placed := 0
	while placed < count and tries < 30:
		tries += 1
		var x := rng.randi_range(ix0 + 4, ix1 - 5)
		var fy: int = int(fl[x - ix0])
		if int(fl[x + 1 - ix0]) != fy or _in_clear(rm, x, fy - 1) or _in_clear(rm, x + 1, fy - 1):
			continue
		if not _free_span(g, W, H, rm, x, fy - 1, 2, 4, 0):
			continue
		for k in 2:
			for y in range(fy - 2, fy):
				_put(g, x + k, y, W, H, 1)
		placed += 1


static func _arches(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rm: Dictionary, count: int) -> void:
	## Kemer: tabandan 4 karo yukarıda 5-6 karolık taş kiriş (altından yürünür; üstüne çift zıplamayla çıkılır)
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var fl: Array = rm["fl"]
	var tries := 0
	var placed := 0
	while placed < count and tries < 20:
		tries += 1
		var ln := rng.randi_range(5, 6)
		if ix1 - ln - 3 < ix0 + 3:
			return
		var x := rng.randi_range(ix0 + 3, ix1 - ln - 3)
		var y: int = int(fl[x - ix0]) - 4
		if not _free_span(g, W, H, rm, x, y, ln, 3, 3):
			continue
		for k in ln:
			_put(g, x + k, y, W, H, 1)
		placed += 1


static func _stalactites(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rm: Dictionary, count: int, wmax := 2) -> void:
	## Tavandan sarkan kaya (1-wmax geniş, 1-2 uzun); her sütun kendi tavanından başlar; altında en az 5 karo açık kalır
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var fl: Array = rm["fl"]
	var ce: Array = rm["ce"]
	if bool(rm["acik"]):
		return
	var tries := 0
	var placed := 0
	while placed < count and tries < 30:
		tries += 1
		var wd := rng.randi_range(1, wmax)
		var x := rng.randi_range(ix0 + 2, ix1 - 2 - wd)
		var ln := rng.randi_range(1, 2)
		var ok := true
		for k in wd:
			var i := x + k - ix0
			var top: int = int(ce[i])
			if top < 2 or int(fl[i]) - (top + ln) < 5:
				ok = false
			for y in range(top, top + ln + 1):
				if _in_clear(rm, x + k, y) or _cell(g, x + k, y, W, H) == 2:
					ok = false
		if not ok:
			continue
		for k in wd:
			var i := x + k - ix0
			var top: int = int(ce[i])
			for y in range(top, top + ln):
				_put(g, x + k, y, W, H, 1)
		placed += 1


static func _alcoves(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rm: Dictionary, count: int) -> void:
	## Kapısız yan duvara oyulmuş taban hizasında cep (2 karo derin, 4 yüksek): Dead Cells'in küçük çıkıntıları
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var fl: Array = rm["fl"]
	for n in count:
		var left := rng.randf() < 0.5
		if left and bool(rm["_sol"]):
			left = false
		if not left and bool(rm["_sag"]):
			if bool(rm["_sol"]):
				return
			left = true
		var xin := ix0 if left else ix1
		var fy: int = int(fl[xin - ix0])
		var ok := true
		for y in range(fy - 5, fy + 1):
			if _in_clear(rm, xin, y):
				ok = false
		for y in range(fy - 4, fy):
			if _cell(g, xin, y, W, H) != 0:
				ok = false
		if not ok:
			continue
		for d in 2:
			var x := xin - 1 - d if left else xin + 1 + d
			for y in range(fy - 4, fy):
				_put(g, x, y, W, H, 0)
			_put(g, x, fy, W, H, 1)


static func _dips(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rm: Dictionary, count: int) -> void:
	## Tabanda 2-3 karo geniş, 2 karo derin çukurcuk (tek zıplamayla çıkılır); kapı ağzı ve kuyulardan uzak
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var fl: Array = rm["fl"]
	for n in count:
		var wd := rng.randi_range(2, 3)
		if ix1 - 4 - wd < ix0 + 4:
			return
		var x0 := rng.randi_range(ix0 + 4, ix1 - 4 - wd)
		var fy: int = int(fl[x0 - ix0])
		var ok := true
		for x in range(x0 - 2, x0 + wd + 2):
			if int(fl[x - ix0]) != fy or _in_clear(rm, x, fy - 1) or _cell(g, x, fy, W, H) != 1 or _cell(g, x, fy - 1, W, H) != 0:
				ok = false
		if not ok:
			continue
		for x in range(x0, x0 + wd):
			_put(g, x, fy, W, H, 0)
			_put(g, x, fy + 1, W, H, 0)
			_put(g, x, fy + 2, W, H, 1)
			fl[x - ix0] = fy + 2


static func _boulders(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rm: Dictionary, count: int) -> void:
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var fl: Array = rm["fl"]
	for i in count:
		var x := rng.randi_range(ix0 + 3, ix1 - 4)
		var fy: int = int(fl[x - ix0])
		if _in_clear(rm, x, fy - 1) or _in_clear(rm, x + 1, fy - 1) or not _free_span(g, W, H, rm, x, fy - 1, 2, 4, 0):
			continue
		_put(g, x, fy - 1, W, H, 1)
		if rng.randf() < 0.5:
			_put(g, x + 1, fy - 1, W, H, 1)


static func _span_free(rm: Dictionary, a: int, b: int, y: int) -> bool:
	## a..b sütunları y satırında temiz bölgeye (kapı ağzı, kuyu) girmiyor ve taban düz mü
	var fl: Array = rm["fl"]
	for x in range(a, b + 1):
		if x - 1 < int(rm["ix0"]) or x + 1 > int(rm["ix1"]):
			return false
		if _in_clear(rm, x, y) or int(fl[x - int(rm["ix0"])]) != y + 1:
			return false
	return true


static func _pit(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rm: Dictionary) -> void:
	## Ortada 3-4 karo tehlike çukuru (tek zıplamayla aşılır; düşen oyuncu çukurdan sektirilir); geniş odada 5-6 karo
	## ve ortasında tek yönlü basamak
	var ix0 := int(rm["ix0"])
	var fl: Array = rm["fl"]
	var wide: bool = int(rm["ix1"]) - ix0 > 24
	var wd := rng.randi_range(5, 6) if wide else rng.randi_range(3, 4)
	if int(rm["ix1"]) - 4 - wd < ix0 + 4:
		return
	for t in 10:
		var x0 := rng.randi_range(ix0 + 4, int(rm["ix1"]) - 4 - wd)
		var fy: int = int(fl[x0 - ix0])
		if not _span_free(rm, x0 - 2, x0 + wd + 1, fy - 1):
			continue
		for x in range(x0, x0 + wd):
			_put(g, x, fy, W, H, 0)
			_put(g, x, fy + 1, W, H, 3)
			_put(g, x, fy + 2, W, H, 1)
		if wd >= 5:
			for k in 2:
				_put(g, x0 + wd / 2 - 1 + k, fy - 1, W, H, 2)
		return


static func _bridge(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rm: Dictionary) -> void:
	## Köprü: ortada 6-10 karo, 3 karo derin yarık; taban hizasında kırık tek yönlü köprü tahtaları (aralar 1-2);
	## yarığa düşen tek zıplamayla çıkar
	var ix0 := int(rm["ix0"])
	var fl: Array = rm["fl"]
	if int(rm["ix1"]) - ix0 - 10 < 6:
		return
	var wd := rng.randi_range(6, mini(10, int(rm["ix1"]) - ix0 - 10))
	for t in 10:
		var a := rng.randi_range(ix0 + 4, int(rm["ix1"]) - 4 - wd)
		var fy: int = int(fl[a - ix0])
		if not _span_free(rm, a - 1, a + wd, fy - 1):
			continue
		for x in range(a, a + wd):
			for y in range(fy, fy + 3):
				_put(g, x, y, W, H, 0)
			fl[x - ix0] = fy + 3
		var bx := a + rng.randi_range(0, 1)
		while bx < a + wd - 1:
			var ln := rng.randi_range(2, 3)
			for k in ln:
				if bx + k < a + wd:
					_put(g, bx + k, fy, W, H, 2)
			bx += ln + rng.randi_range(1, 2)
		if rng.randf() < 0.4:
			var mid := a + wd / 2
			for hx in range(mid - 1, mid + 1):
				_put(g, hx, fy + 2, W, H, 3)
		return


static func _deck(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rm: Dictionary) -> void:
	## Kuyu türü (yüksek oda): tabandan 4 karo yukarıda tek yönlü üst güverte (odanın yarısı-üçte ikisi, 2-3 parça);
	## aşağı + zıpla ile inilir, çift zıplamayla çıkılır
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var fl: Array = rm["fl"]
	var x := ix0 + rng.randi_range(2, 5)
	while x < ix1 - 4:
		var ln := rng.randi_range(4, 7)
		var y: int = int(fl[x - ix0]) - 4
		var ok := true
		for k in ln:
			var xx := x + k
			if xx > ix1 - 2 or int(fl[xx - ix0]) != y + 4 or _in_clear(rm, xx, y):
				ok = false
				break
			for yy in range(y - 3, y + 4):
				if _cell(g, xx, yy, W, H) != 0:
					ok = false
		if ok:
			for k in ln:
				_put(g, x + k, y, W, H, 2)
			x += ln + rng.randi_range(3, 5)
		else:
			x += 2


static func _odul_shape(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rm: Dictionary) -> void:
	## Ödül odası: düz; hazine / zamanlıda 2 karolık taş seki (tek zıplama); seçkinde açık alan
	var ix0 := int(rm["ix0"])
	var fl: Array = rm["fl"]
	var mid := _odul_mid(rm)
	var fy: int = int(fl[mid - ix0])
	match String(rm["odul"]):
		"hazine", "zamanli":
			for x in range(mid - 3, mid + 4):
				if _in_clear(rm, x, fy - 1):
					continue
				for y in range(fy - 2, fy):
					_put(g, x, y, W, H, 1)
				fl[x - ix0] = fy - 2
		"sunak", "tomar":
			_platforms(g, W, H, rng, rm, 1, 3, 3)
		"lanetli":
			# v34 lanetli sandık: alçak taş seki (1 karo) ve iki yanda tek yönlü çıkıntı (uzantının sonu: bekçili oda gibi)
			for x in range(mid - 2, mid + 3):
				if _in_clear(rm, x, fy - 1):
					continue
				_put(g, x, fy - 1, W, H, 1)
				fl[x - ix0] = fy - 1
			_platforms(g, W, H, rng, rm, 1, 3, 3)


static func _odul_mid(rm: Dictionary) -> int:
	## Ödülün sütunu: odanın ortası; kapı tavanda / tabanda (kuyu) ise kuyudan uzak yanın ortası
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var mid := (ix0 + ix1) / 2
	var side := _door_side(rm)
	if side in ["ust", "alt"]:
		var hx := int(rm.get("_door_x", mid))
		var sol := hx - 1 - ix0
		var sag := ix1 - (hx + KUYU_W)
		mid = (hx + KUYU_W + 1 + ix1) / 2 + 1 if sag >= sol else (ix0 + hx - 2) / 2
	elif bool(rm.get("pencere", false)):
		# v34: pencereli ödül odası: ödül parmaklığın yakınında (ana yoldan görünsün)
		mid = ix0 + 7 if String(rm.get("pencere_yan", "sol")) == "sol" else ix1 - 6
	return clampi(mid, ix0 + 5, ix1 - 4)


static func _odul_marks(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rm: Dictionary, zamanli: Array, doors: Array) -> Array:
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
			var tx := clampi(mid + 5, ix0 + 2, ix1 - 2)
			if _door_side(rm) == "sag":
				tx = clampi(mid - 5, ix0 + 2, ix1 - 2)
			marks.append(["E", mid + (2 if _door_side(rm) == "sag" else -2), fy - 1])
			marks.append(["T", tx, int(fl[tx - ix0]) - 1])
		"zamanli":
			marks.append(["Z", mid, fy - 1])
			# kapı: koridorun odaya bitişik sütunu (4 karo yüksek geçit kapanır)
			var kd := _yan_kapi_sutunu(rm, doors)
			zamanli.append({"x": kd.x, "y": kd.y, "room": int(rm["id"]), "sure": ZAMANLI_SURE})
		"lanetli":
			marks.append(["L", mid, fy - 1])
	return marks


static func _door_side(rm: Dictionary) -> String:
	## Ödül odasının tek kapısı hangi yanda (sol / sag / ust: tavandaki kuyu / alt: tabandaki kuyu)
	return String(rm.get("_door_side", "sol"))


static func _odul_tasi(g: PackedByteArray, W: int, H: int, rm: Dictionary) -> Vector2i:
	## Ödül odasının Kut Taşı: kapının iç yanı (ödülden uzak); kuyu kapısında kuyunun ödülsüz yanı
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var side := _door_side(rm)
	var x := ix0 + 4 if side == "sol" else ix1 - 4
	if side in ["ust", "alt"]:
		var hx := int(rm.get("_door_x", (ix0 + ix1) / 2))
		x = hx - 2 if _odul_mid(rm) > hx else hx + KUYU_W + 1
	return _floor_spot(g, W, H, rm, x)


static func _floor_spot(g: PackedByteArray, W: int, H: int, rm: Dictionary, x: int) -> Vector2i:
	## Odada x sütununda (yakınında) ayakta durulacak hava hücresi (altı katı, üstünde 3 karo hava); tehlike / platform /
	## kuyu ağzı değil
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
			if _cell(g, cx, y, W, H) == 0 and _cell(g, cx, y + 1, W, H) == 1 and _cell(g, cx, y - 1, W, H) == 0 and _cell(g, cx, y - 2, W, H) == 0 and _cell(g, cx - 1, y + 1, W, H) != 3 and _cell(g, cx + 1, y + 1, W, H) != 3 and _cell(g, cx - 1, y + 1, W, H) != 0 and _cell(g, cx + 1, y + 1, W, H) != 0:
				return Vector2i(cx, y)
	return Vector2i(x, int(fl[clampi(x - ix0, 0, fl.size() - 1)]) - 1)


static func _hazard_strips(g: PackedByteArray, W: int, H: int, rng: RandomNumberGenerator, rm: Dictionary, style: String) -> void:
	## Dövüş odalarının düz tabanında 2-3 karolık tehlike şeridi (tek zıplamayla aşılır); kapı ağzı ve kuyulardan uzak
	if rng.randf() > 0.5:
		return
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var fl: Array = rm["fl"]
	for t in 8:
		var wd := rng.randi_range(2, 3)
		if ix1 - 5 - wd < ix0 + 5:
			return
		var x0 := rng.randi_range(ix0 + 5, ix1 - 5 - wd)
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
				# v33 düzeltmeleri (eskiden kayanın / tek yönlü platformun içinden düşülebiliyordu):
				# dikine iniş yalnızca durulan tek yönlü platformdan (aşağı + zıpla); altındaki sütun ilk tutunulacak
				# yere dek boş (araya giren platform / katı karo düşüşü orada keser: o ayrı bir hamledir)
				if dx == 0 and dy > 0:
					if _cell(g, cx, cy + 1, W, H) != 2:
						continue
					var thru := true
					for yy in range(cy + 2, ny):
						if _tutar(_cell(g, cx, yy, W, H)):
							thru = false
							break
					if not thru:
						continue
				# yana düşüş: düşülen sütunda iniş yolu boş olmalı (başlangıç ayak hizasının altındaki platform da
				# tutar); değilse kenardan yürüyüp komşu sütunda düşülür: komşu sütun boş ve varış satırının üstü
				# komşudan varışa dek açık
				if dy > 1 and dx != 0:
					var clear := true
					for yy in range(mini(cy, ny) - 1, ny):
						var cc := _cell(g, nx, yy, W, H)
						if cc == 1 or (cc == 2 and yy > cy):
							clear = false
							break
					if not clear:
						var c1 := cx + step
						var ok2 := true
						for yy in range(cy - 1, ny):
							var cc := _cell(g, c1, yy, W, H)
							if cc == 1 or (cc == 2 and yy > cy):
								ok2 = false
								break
						var k2 := c1
						while ok2 and k2 != nx:
							k2 += step
							if _cell(g, k2, ny - 1, W, H) == 1 or (k2 != nx and _cell(g, k2, ny, W, H) == 2):
								ok2 = false
						if not ok2:
							continue
			out.append(_idx(nx, ny, W))
	return out


static func _tutar(c: int) -> bool:
	## Düşen oyuncuyu tutan karo: katı ya da tek yönlü platform (üstten çarpışır)
	return c == 1 or c == 2


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
