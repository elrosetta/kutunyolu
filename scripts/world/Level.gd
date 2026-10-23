class_name Level
extends Node2D
## Ötüken Ormanı bölümü: açık arazi üretimi, karo seçimi, süsler, ışıklar, paralaks,
## parçacıklar, düşman ve eşya yerleşimi. Düşmanlar ve mermiler için dünya sorgularını sağlar.

signal finished
signal player_died
signal scroll_requested(p: Pickup)
signal npc_requested(id: String)
signal slot_requested(p: Pickup)
signal lutuf_requested(p: Pickup)
signal boss_died
signal tuccar_requested   # v24: Bezirgân Sartak'ın pazarı (Main._on_tuccar)
signal tasi_bulundu(i: int)   # v32: Kut Taşı keşfedildi
signal harita_requested       # v32: Kut Taşı'nın dibinde W: harita (hızlı ışınlanma) açılsın

const TS := 24
const W := 172   # v25: 230'dan genişledi; v32: 256 (7 x 36 karolık kesim); v33: 7 x 24 karolık küçük kesim (LevelGen.SW)
const H := 56    # v32: 44'ten 90'a (4 x 22); v33: 4 satır x 13 karo (LevelGen.SH); yurt / konak / arena üst 30 satırı kullanır

## v32 oda çizgesi (LevelGen.generate): odalar, kapılar, giriş / çıkış karosu, sınırlar, ölçümler
var rooms: Array = []
var doors: Array = []
var spawn_cell := Vector2i(5, 29)
var exit_cell := Vector2i(249, 29)
var bounds := Rect2i(0, 0, W, 44)
var metrics: Dictionary = {}
var kaide_xs: Array = []      # eşya kaideleri (karo): ana yolun 1/4, 2/4, 3/4'ündeki odalar
## v32 harita ve ışınlanma
var harita: Harita
var tasi: Array = []          # KutTasi düğümleri
var zamanli: Array = []       # ZamanliKapi düğümleri
const ISIN_SURE := 0.9        # ışınlanma kanalı (sn): hasar alınırsa bozulur
const ISIN_DOKUNULMAZ := 0.6  # varışta dokunulmazlık (sn)
var isin_t := 0.0
var isin_hedef := -1
var isin_hp := 0.0
var isin_sayi := 0            # bu bölümde tamamlanan ışınlanma
var isin_bozuk := 0           # hasarla bozulan kanal
var harita_istek := -1        # bot: harita ekranından seçilecek taş (Main "harita" kipi)
# v34 merak uyandıran bölüm: gizli cepler (kırık duvar), parmaklıklı pencereler, kilitli kapı + anahtar, lanetli
# sandık, küpler; yaratık grupları (ölçüm) ve lanet
var kiriklar: Array = []      # KirikDuvar
var pencereler: Array = []    # Parmaklik
var kilitler: Array = []      # KilitliKapi
var anahtarlar: Array = []    # Anahtar (yerdeki)
var sandiklar: Array = []     # Sandik (lanetli)
var kupler: Array = []        # Kup
var gruplar: Array = []       # {oda, karisik, n}
var anahtar := 0              # taşınan anahtar
var sayac_ilk: Dictionary = {}   # bölüm kurulunca hazine / tomar / gizli / sandık toplamları (tam harita sayacı)
const LANET_OLDUR := 10       # lanetli sandık: bu kadar yaratık öldürülene dek alınan hasar iki kat
var lanet := 0                # kalan öldürme (0: lanet yok)
var _lanet_aura: Node2D

var rng := RandomNumberGenerator.new()
var grid := PackedByteArray()  # 0 hava, 1 katı, 2 platform
var heights: Array = []
var ground: TileMapLayer
var overlay: TileMapLayer
var player: Player
var camera: Camera2D
var fx_root: Node2D
var proj_root: Node2D
var actors: Node2D
var decor_root: Node2D
var pickups: Array = []
var style := "orman"
var chunks: Array = []
var carved := 0
var biome: Dictionary = {}
var art: Dictionary = {}
var exit_pos := Vector2.ZERO
var hub := false
var konak := false        # v32: derinlikler arası gezgin konak (Bengisu Usta, Umay Ocağı, bazen Bezirgân)
var konak_ates := Vector2.ZERO   # v32: Umay Ocağı (konak ateşi): yanından geçince taşınan Kut Umay'a ulaşır
var _ocak_done := false
var npcs: Array = []
var decal_root: Node2D
var hazard: TileMapLayer
var haz_kind := ""
var _haz_frame := 0
var _haz_t := 0.0
var boss_id := ""
var boss: Enemy
var boss_gate_open := false
var bezirgan: Bezirgan  # v24 tüccar (yoksa null)
var spawn_moved := 0     # v25: gövdesi sığmadığı için yakına taşınan düşman sayısı (yerleşim denetimi)
var spawn_skipped := 0   # v25: yakında sığacak yer bulunamadığı için konmayan düşman sayısı
var tuzak: Node2D        # v25: tehlike çukuru işaretleri ve diken fırlaması (Tuzak.gd)
static var bezirgan_zorla := false  # test: şanstan bağımsız yerleştir (tools/tests/tuccar_testi.gd)
const HUB_W := 92
var red_rect: ColorRect
var vig_mat: ShaderMaterial  # vinyet; hasar nabzı "hurt" parametresiyle
var _light_tex: GradientTexture2D
var _done := false
var _hub_floor: Node2D
var moon: DirectionalLight2D  # ay: yönlü ışık + arazi gölgeleri (GroundShadow kayma yönünü buradan okur)
var grid_surum := 0       # v38: oyun sırasında karo değişince artar (GroundShadow / Pickup zemin önbelleği)
var moon_shadow := 0.72  # ay gölgesindeki aktörde ay ışığının giden payı (toon_light moon_shade üst sınırı)
var _shadow_dir := Vector2(0, 1)  # ay ışığının gidiş yönü (karo engelleyicileri bu yöne göre seçilir)


func _exit_tree() -> void:
	Data.budama_planla()  # v38: eski bölümün paralaks dokuları VRAM'den bırakılır


func build(seed_value: int) -> void:
	var _pt := Time.get_ticks_usec()   # v38: --perf adım süreleri (Prof.on değilse yalnızca saat okuması)
	rng.seed = seed_value
	biome = Game.biome_for_depth(int(Game.run.get("depth", 1)))
	art = _stil_art(biome.get("art", {}))
	_derinlik_havasi()   # v40: biyomun ikinci derinliği kendi havasında (daha koyu / daha geç saat)
	Game.run["biome"] = biome.get("id", "otuken")
	Game.run["bezirgan_gordu"] = false   # v32: bu bölümün pazarı (_place_bezirgan) belirler; önceki kurulumdan kalmasın
	_plan_bezirgan()   # v24 / v32: tüccar bu bölümde çıkacak mı (pazar odası üretici tarafından açılır)
	_pt = _adim(&"kur_plan_bezirgan", _pt)
	_generate()
	_pt = _adim(&"kur_generate", _pt)
	Game.run["bolum_sure"] = 0.0   # v32: zamanlı kapılar için bölüm süresi
	# bölüm başı destan sayaçları
	Game.run["dumrul_used"] = false
	for k in ["kills_level", "bow_level", "low_kills"]:
		Adlar.set_stat(k, 0.0)
	_build_tiles()
	_pt = _adim(&"kur_build_tiles", _pt)
	decor_root = Node2D.new()
	decor_root.z_index = -2
	add_child(decor_root)
	decal_root = Node2D.new()
	decal_root.z_index = 1
	add_child(decal_root)
	actors = Node2D.new()
	add_child(actors)
	proj_root = Node2D.new()
	proj_root.z_index = 20
	add_child(proj_root)
	fx_root = Node2D.new()
	fx_root.z_index = 50
	add_child(fx_root)
	FX.root = fx_root
	FX.level = self
	_build_lighting()
	_pt = _adim(&"kur_build_lighting", _pt)
	_build_background()
	_pt = _adim(&"kur_build_background", _pt)
	_build_hazards()
	_pt = _adim(&"kur_build_hazards", _pt)
	_place_rooms()   # v32: ödül odaları ve pazar yeri önce (süsler tezgâhın üstüne binmesin)
	_pt = _adim(&"kur_place_rooms", _pt)
	_place_decor()
	_pt = _adim(&"kur_place_decor", _pt)
	_spawn_player()
	_pt = _adim(&"kur_spawn_player", _pt)
	_gizemler()      # v34: gizli cepler, parmaklıklı pencereler, kilitli kapı (yaratıklardan önce: karolar ve ızgara)
	_pt = _adim(&"kur_gizemler", _pt)
	_spawn_enemies()
	_pt = _adim(&"kur_spawn_enemies", _pt)
	_spawn_items()
	_pt = _adim(&"kur_spawn_items", _pt)
	_spawn_scrolls()
	_pt = _adim(&"kur_spawn_scrolls", _pt)
	_spawn_kesif()   # v25: eski gizli oda / Ülgen sunağı ganimeti artık bölümün kendisinde (v34: zula gizli cepte)
	_pt = _adim(&"kur_spawn_kesif", _pt)
	_kut_taslari()   # v32: ışınlanma taşları, zamanlı kapılar, harita sisi
	_pt = _adim(&"kur_kut_taslari", _pt)
	_build_particles()
	_pt = _adim(&"kur_build_particles", _pt)
	_build_overlay_fx()
	_pt = _adim(&"kur_build_overlay_fx", _pt)
	_place_bezirgan()
	_pt = _adim(&"kur_place_bezirgan", _pt)
	_bos_oda_doldur()     # v34: yaratıksız kalan ana yol / dal odasına bir yaratık
	_pt = _adim(&"kur_bos_oda_doldur", _pt)
	_kupler_yerlestir()   # v34: her odada "bir şey" (boş oda kalmaz)
	_pt = _adim(&"kur_kupler_yerlestir", _pt)
	sayac_ilk = sayac()
	_sinav_kur()          # v42: bölüm sınavları (Çabuk / Dokunulmaz / Avcı) ve Kut Kapısı önündeki Otağ Yeri
	Ses.music(biome.get("id", "otuken"))
	Perde.acilis("bolum")   # v40: mürekkep fırçası perdesi açılır
	HikayeSahne.kur(self)   # v42: bölüm sahnesi (sahne_yeri), hikâye odası (hikaye_yeri), ilk giriş görümü


func _derinlik_havasi() -> void:
	## v40: stil_v2.json "mood": biyomun kaçıncı derinliğinde olduğumuza göre ("0", "1") ışık / derece ezmeleri.
	## Sözlük anahtarlar ("grade", "huzme") iç içe birleşir, diğerleri yerine geçer.
	if not art.has("mood"):
		return
	var ds: Array = biome.get("depths", [1, 1])
	var i := int(Game.run.get("depth", 1)) - int(ds[0])
	var m: Dictionary = (art["mood"] as Dictionary).get(str(clampi(i, 0, 9)), {})
	_art_birlestir(m)


func _art_birlestir(m: Dictionary) -> void:
	for k in m:
		if m[k] is Dictionary and art.get(k) is Dictionary:
			var d: Dictionary = (art[k] as Dictionary).duplicate()
			for kk in m[k]:
				d[kk] = m[k][kk]
			art[k] = d
		else:
			art[k] = m[k]


func _adim(ad: StringName, t0: int) -> int:
	## v38 --perf: bölüm kurma adımının süresi Prof tablosuna (perf_testi "uretim" evresi)
	if Prof.on:
		Prof.ekle(ad, t0)
	return Time.get_ticks_usec()


func build_boss(seed_value: int, bid_boss: String) -> void:
	## Boss arenası: düz, geniş, iki yanı duvarlı; ortada birkaç platform; boss sağdan gelir
	rng.seed = seed_value
	boss_id = bid_boss
	var bdef: Dictionary = {}
	for b in Data.world["bosses"]:
		if b["id"] == bid_boss:
			bdef = b
	biome = Game.biome_for_depth(int(Game.run.get("depth", 1)))
	for b in Data.world["biomes"]:
		if b["id"] == bdef.get("biome", biome.get("id", "otuken")):
			biome = b
	art = _stil_art(biome.get("art", {}))
	# stil v2: boss arenasına özgü paralaks (ör. orta katmanda Şahmeran Ana'nın / Erlik Han'ın tahtı)
	if art.has("boss_bg"):
		art["bg"] = art["boss_bg"]
	art["ambient"] = art.get("boss_ambient", [0.36, 0.3, 0.42])
	# v40: arena derecesi / hüzmesi (stil_v2.json "boss_grade", "boss_huzme"): daha dar vinyet, daha sert karşıtlık
	if art.has("boss_grade"):
		_art_birlestir({"grade": art["boss_grade"]})
	if art.has("boss_huzme"):
		_art_birlestir({"huzme": art["boss_huzme"]})
	art["decor"] = ["kaya", "cira", "kam_diregi"]
	Game.run["biome"] = biome.get("id", "otuken")
	_generate_arena()
	_build_tiles()
	decor_root = Node2D.new()
	decor_root.z_index = -2
	add_child(decor_root)
	decal_root = Node2D.new()
	decal_root.z_index = 1
	add_child(decal_root)
	actors = Node2D.new()
	add_child(actors)
	proj_root = Node2D.new()
	proj_root.z_index = 20
	add_child(proj_root)
	fx_root = Node2D.new()
	fx_root.z_index = 50
	add_child(fx_root)
	FX.root = fx_root
	FX.level = self
	_build_lighting()
	_build_background()
	for x in [12, 30, 50, 70]:
		_decor("cira", x, surface_y(x), -2, true)
	for x in [20, 40, 60]:
		_decor("kam_diregi", x, surface_y(x), -3)
	_place_towers()
	if art.has("boss_extras"):
		_place_ink_extras_spec(art["boss_extras"])
	_spawn_player()
	camera.limit_right = 84 * TS
	# boss: sağdan, uzak (v38: burada kullanılmayan bir Enemy.new() ağaca girmeden kalıyor, her boss arenasında bir
	# yaratık + fizik gövdesi sızdırıyordu; kaldırıldı)
	var bx := 64
	boss = Boss.new()
	# v22: boss canı / hasarı Enemy.setup içinde Zorluk'tan (boss kendi derinliğinde; data/zorluk.json "boss")
	boss.setup(String(bdef.get("enemy", bid_boss)), false, int(Game.run.get("tier", 0)))
	boss.hp = boss.max_hp
	for arg in OS.get_cmdline_user_args():
		if String(arg).begins_with("--bossfaz="):
			boss.hp = boss.max_hp * (1.0 - 0.34 * (int(String(arg).trim_prefix("--bossfaz=")) - 1))
	boss.level = self
	boss.position = Vector2(bx * TS, surface_y(bx) * TS - 1)
	actors.add_child(boss)
	exit_pos = Vector2(78 * TS, surface_y(78) * TS)
	_build_particles()
	_build_overlay_fx()
	Ses.music("boss")
	if camera is CameraV2:
		(camera as CameraV2).boss_intro()   # v40: kamera kükreyen boss'a doğru süzülüp döner
	Perde.acilis("boss")
	HikayeSahne.boss(self)   # v42: kükreyişten sonra boss'un sözü


func _generate_arena() -> void:
	style = "arena"
	grid.resize(W * H)
	grid.fill(0)
	heights = []
	var top := 30
	for x in W:
		heights.append(top)
		for y in range(top, H):
			grid[idx(x, y)] = 1
		if x >= 84 or x <= 1:
			for y in H:
				grid[idx(x, y)] = 1
	# üç platform
	for px in [22, 42, 62]:
		for k in 4:
			grid[idx(px + k, top - 5)] = 2
	for y in range(top - 16, top):
		grid[idx(2, y)] = 1
		grid[idx(83, y)] = 1


func open_boss_gate() -> void:
	if boss_gate_open:
		return
	boss_gate_open = true
	var gate := KutGate.new()
	gate.position = exit_pos
	decor_root.add_child(gate)
	var portal := FX.anim("rift_portal", exit_pos + Vector2(0, -34), 0.0, 1.0, Color(0.6, 1.0, 1.0, 0.85))
	if portal:
		portal.loop = true
		portal.z_index = -1
		portal.reparent(decor_root)
	add_light(exit_pos + Vector2(0, -40), Color(0.45, 0.9, 1.0), 220.0, 1.4, decor_root)
	FX.ring(exit_pos + Vector2(0, -30), 60, Color(0.6, 1.0, 1.0), 0.6)
	Ses.play("kapi")


func _build_hazards() -> void:
	## Tehlike karoları (grid 3): biyoma göre diken / zehir / lav / buz; iki kare animasyon
	haz_kind = {"otuken": "diken", "bozkir": "diken", "sahmeran": "zehir", "kaf": "buz", "tamu": "lav"}.get(biome.get("id", "otuken"), "diken")
	# biyoma özgü mürekkep tehlike dokusu (hazards_<biyom>_v2.png; tools/artgen/ink_tehlike.py) varsa o, yoksa biyomdan
	# bağımsız mürekkep karoları (hazards_v2.png; tools/artgen/sus_ink.py); 4 doku pikseli / dünya birimi.
	# Satır yerleşimi assets/tiles/hazards.json (tür -> satır).
	var hz2 := "res://assets/tiles/hazards_%s_v2.png" % String(biome.get("id", ""))
	# sıvı havuzu (Şahmeran zehri, Tamu lavı: _build_hazards_ink) kendi ışıklarını kurar
	var liquid := art.has("hazard_v2") and ResourceLoader.exists("res://assets/tiles/hazard_%s_v2.png" % haz_kind)
	var v2h := ResourceLoader.exists(hz2)
	var hv2 := not v2h   # ortak atlas (env_ink gölgelendiricisi, ışıma katmanı hazards_v2_e)
	var hv2_path := hz2 if v2h else "res://assets/tiles/hazards_v2.png"
	var hp := 4 * Data.pack_scale(hv2_path)   # 4 doku pikseli / dünya birimi; HD paketinde 8 (TileSet gerçek boyutu kullanır)
	var ts := TileSet.new()
	ts.tile_size = Vector2i(TS * hp, TS * hp)
	var src := TileSetAtlasSource.new()
	var hct := CanvasTexture.new()
	hct.diffuse_texture = Data.tex_full(hv2_path)
	hct.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	src.texture = hct
	src.texture_region_size = Vector2i(TS * hp, TS * hp)
	ts.add_source(src, 0)
	for r in 4:
		for c in 2:
			src.create_tile(Vector2i(c, r))
	hazard = TileMapLayer.new()
	hazard.tile_set = ts
	hazard.scale = Vector2.ONE / float(hp)
	if v2h:
		hazard.material = _ink_mat()
	else:
		var m := ShaderMaterial.new()
		m.shader = load("res://shaders/env_ink.gdshader")
		m.set_shader_parameter("moon_gain", float(art.get("ground_moon_gain", 0.6)))
		hazard.material = m
	hazard.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	hazard.z_index = 2
	add_child(hazard)
	var hm: Dictionary = Data.load_json("res://assets/tiles/hazards.json")
	var row := int(hm["rows"].get(haz_kind, 0))
	var n := 0
	for y in H:
		for x in W:
			if cell(x, y) == 3:
				hazard.set_cell(Vector2i(x, y), 0, Vector2i(0, row))
				n += 1
				if haz_kind == "lav" and n % 2 == 0 and not liquid:
					add_light(Vector2(x * TS + 12, y * TS + 6), Color(1.0, 0.5, 0.2), 70.0, 0.9, self if hv2 else hazard)
	# glow katmanı (lav / zehir)
	if haz_kind in ["lav", "zehir"]:
		var glow := TileMapLayer.new()
		var ts2 := TileSet.new()
		var gc := TS * 4
		ts2.tile_size = Vector2i(gc, gc)
		var src2 := TileSetAtlasSource.new()
		src2.texture = load("res://assets/tiles/hazards_v2_e.png")
		src2.texture_region_size = Vector2i(gc, gc)
		ts2.add_source(src2, 0)
		for r in 4:
			for c in 2:
				src2.create_tile(Vector2i(c, r))
		glow.tile_set = ts2
		glow.scale = Vector2.ONE * (float(hp) / 4.0)  # ebeveyn (HD) katmanın küçültmesini dengele: parlama temel boyutlu
		glow.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
		var gm := CanvasItemMaterial.new()
		gm.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
		gm.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
		glow.material = gm
		glow.z_index = 3
		glow.modulate = Color(1.6, 1.4, 1.2)
		hazard.add_child(glow)
		for y in H:
			for x in W:
				if cell(x, y) == 3:
					glow.set_cell(Vector2i(x, y), 0, Vector2i(0, row))
	_build_hazards_ink()
	# v25: çukur işaretleri (dudaklarda mürekkep kazıklar, dışarı taşan diken uçları) ve değince fırlayan dikenler
	tuzak = Tuzak.new()
	tuzak.level = self
	tuzak.kind = haz_kind
	add_child(tuzak)


func _build_hazards_ink() -> void:
	## Stil v2: tehlike karoları yerine her bağlı bölgeye tek sıvı çokgeni (liquid_ink.gdshader; veri dokusu
	## assets/tiles/hazard_<tür>_v2.png). Karo katmanı yerinde kalır ama gizlenir: hazard_at / _hazard_tick aynı çalışır.
	var tp := "res://assets/tiles/hazard_%s_v2.png" % haz_kind
	var spec: Dictionary = art.get("hazard_v2", {})
	if not ResourceLoader.exists(tp) or spec.is_empty():
		return
	hazard.visible = false
	var root := Node2D.new()
	root.z_index = 2
	add_child(root)
	var seen := {}
	for y in H:
		for x in W:
			if cell(x, y) != 3 or seen.has(Vector2i(x, y)):
				continue
			# bağlı bölge (4 komşu) -> sınır kutusu
			var stack: Array = [Vector2i(x, y)]
			seen[Vector2i(x, y)] = true
			var r := Rect2i(x, y, 1, 1)
			while not stack.is_empty():
				var p: Vector2i = stack.pop_back()
				r = r.expand(p).expand(p + Vector2i.ONE)
				for o in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
					var q: Vector2i = p + o
					if q.x >= 0 and q.x < W and q.y >= 0 and q.y < H and cell(q.x, q.y) == 3 and not seen.has(q):
						seen[q] = true
						stack.append(q)
			var poly := Polygon2D.new()
			var w := float(r.size.x * TS)
			var h := float(r.size.y * TS)
			poly.polygon = PackedVector2Array([Vector2(0, -6), Vector2(w, -6), Vector2(w, h), Vector2(0, h)])
			poly.position = Vector2(r.position.x * TS, r.position.y * TS)
			var m := ShaderMaterial.new()
			m.shader = load("res://shaders/liquid_ink.gdshader")
			m.set_shader_parameter("noise_tex", Data.tex_full(tp))
			m.set_shader_parameter("surface_y", float(r.position.y * TS))
			for k in ["deep", "mid", "hot"]:
				if spec.has(k):
					var c: Array = spec[k]
					m.set_shader_parameter(k, Color(c[0], c[1], c[2]))
			for k in ["gain", "crust", "flow", "scale"]:
				if spec.has(k):
					m.set_shader_parameter(k, float(spec[k]))
			poly.material = m
			root.add_child(poly)
			var lc: Array = spec.get("light", [1.0, 0.5, 0.2])
			var step := 2 if haz_kind == "lav" else 4
			for k in range(0, r.size.x, step):
				var l := add_light(Vector2((r.position.x + k + 0.5) * TS, r.position.y * TS + 4.0), Color(lc[0], lc[1], lc[2]),
					float(spec.get("light_r", 90.0)), float(spec.get("light_e", 0.9)), root)
				titrek(l, "lav" if haz_kind == "lav" else "zehir")   # v40


func hazard_at(p: Vector2) -> String:
	var x := int(floor(p.x / TS))
	var y := int(floor(p.y / TS))
	if x < 0 or x >= W or y < 0 or y >= H:
		return ""
	return haz_kind if grid[idx(x, y)] == 3 else ""


func ice_at(p: Vector2) -> bool:
	return haz_kind == "buz" and hazard_at(p) == "buz"


func hazard_jab(p: Vector2, _hz: String) -> void:
	## v25: çukura değilen yerde dikenler fırlar (Tuzak.gd)
	if tuzak:
		tuzak.jab(p)


func safe_ground(feet: Vector2) -> bool:
	## v25: ayakların altı (iki yan dahil) yürünür ve bir karo çevresinde tehlike yok: çukurdan dönülecek güvenli zemin
	var tx := int(floor(feet.x / TS))
	var fy := int(floor((feet.y + 4.0) / TS))
	for x in range(tx - 1, tx + 2):
		var c := cell(x, fy)
		if c == 3 or cell(x, fy - 1) == 3:
			return false
		if x == tx and c != 1 and c != 2:
			return false
	return true


func pit_exit(feet: Vector2, prefer := 0) -> Vector2:
	## v25: tehlike çukurundan en yakın çıkış (yürünür, tehlikesiz, üstü açık zemin; ayak noktası). prefer yönü 3 karo
	## öncelikli. Yoksa Vector2.INF.
	var tx := int(floor(feet.x / TS))
	var ty := int(floor((feet.y - 2.0) / TS))
	var best := Vector2.INF
	var bc := 999
	for s in [-1, 1]:
		for d in range(1, 12):
			var x: int = tx + d * s
			var found := false
			for r in range(ty - 3, ty + 2):
				if cell(x, r) == 0 and cell(x, r - 1) != 1 and (cell(x, r + 1) == 1 or cell(x, r + 1) == 2) \
						and cell(x - 1, r + 1) != 3 and cell(x + 1, r + 1) != 3:
					var cost := d + (0 if (prefer == 0 or s == prefer) else 3)
					if cost < bc:
						bc = cost
						best = Vector2(x * TS + TS / 2.0, (r + 1) * TS - 1.0)
					found = true
					break
			if found:
				break
	return best


func _place_rooms() -> void:
	## Oda işaretleri (v32: çıkmaz ödül odaları): S sunak (lütuf), T hazine kaidesi (üst kademe eşya + altın), E seçkin
	## bekçi, M Kut Tomarı kaidesi, P Bezirgân tezgâhı (yer planı), Z zamanlı kapı ödülü (üst kademe eşya + altın).
	## İşaret üretimde kaydedilen karosundan aşağı ilk zemine konur (Level._floor_below).
	for ch in chunks:
		for mk in ch.get("marks", []):
			var chr := String(mk[0])
			var tx := int(mk[1])
			var ty := _floor_below(tx, int(mk[2]))
			match chr:
				"S":
					_decor("sunak", tx, ty, -1, true)
					var p := Pickup.new()
					p.kind = "lutuf"
					p.level = self
					p.position = Vector2(tx * TS + TS / 2.0, ty * TS)
					add_child(p)
					pickups.append(p)
				"T", "Z":
					var it := ItemGen.random_drop(int(Game.run.get("tier", 0)) + 1)
					drop_item(it, Vector2(tx * TS + 12, ty * TS - 30), true)
					for g in 6:
						drop_orb("gold", Vector2(tx * TS + 12 + randf_range(-20, 20), ty * TS - 20))
				"E":
					var pool := _biome_pool()
					var kind: String = pool[rng.randi_range(0, pool.size() - 1)]
					# v34: bekçi Kut Taşı / giriş çevresine doğmaz (yakın bir sütuna kayar)
					for dx in [0, 3, -3, 6, -6, 9, -9]:
						if not _yaratik_yasak(tx + dx, ty - 1):
							tx += dx
							break
					ty = _floor_below(tx, int(mk[2]))
					spawn_enemy(kind, Vector2(tx * TS + TS / 2.0, ty * TS - 1), true, false, true)
				"M":
					drop_scroll(Vector2(tx * TS + 12, ty * TS))
				"P":
					_bz_plan = tx
					_bz_y = ty
				"L":
					# v34 lanetli sandık
					var sd := Sandik.new()
					sd.level = self
					sd.oda = int(ch.get("room", -1))
					sd.position = Vector2(tx * TS + TS / 2.0, ty * TS)
					add_child(sd)
					sandiklar.append(sd)
				"K":
					# v34 anahtar (kilitli ödül odasının; gizli cep yoksa başka bir ödül odasında)
					anahtar_birak(Vector2(tx * TS + TS / 2.0, ty * TS))


func _floor_below(tx: int, y0: int) -> int:
	## v25: (tx, y0) karosundan aşağı ilk yürünür zemin karosu (üstü hava); yoksa _ground_tile_y
	for y in range(maxi(1, y0), mini(H - 1, y0 + 10)):
		var c := cell(tx, y + 1)
		if cell(tx, y) == 0 and (c == 1 or c == 2):
			return y + 1
	return _ground_tile_y(tx)


func _ground_tile_y(tx: int) -> int:
	## Sütunda yukarıdan aşağı ilk "üstü hava" katı/platform karosu (oda içi dahil)
	for y in range(2, H - 1):
		if cell(tx, y) != 0 and cell(tx, y) != 3 and cell(tx, y - 1) == 0:
			return y
	return surface_y(tx)


func _biome_pool() -> Array:
	var bid: String = biome.get("id", "otuken")
	var pool: Array = []
	for e in Data.world["enemies"]:
		if e.get("biome", "") == bid and e.get("impl", false) and not String(e.get("ai", "")).begins_with("boss"):
			# v39: "havuz": false (çağrılan yavru) havuza girmez; "agirlik" kaç pay; "min_derinlik" ilk derinlik
			if not bool(e.get("havuz", true)) or int(Game.run.get("depth", 1)) < int(e.get("min_derinlik", 0)):
				continue
			for i in maxi(1, int(e.get("agirlik", 1))):
				pool.append(e["id"])
	if pool.is_empty():
		pool = ["kara_boru", "cor", "balbal"]
	return pool


func _hazard_tick(delta: float) -> void:
	if hazard == null:
		return
	_haz_t += delta
	if _haz_t > 0.45:
		_haz_t = 0.0
		_haz_frame = 1 - _haz_frame
		var hm: Dictionary = Data.load_json("res://assets/tiles/hazards.json")
		var row := int(hm["rows"].get(haz_kind, 0))
		for c in hazard.get_used_cells():
			hazard.set_cell(c, 0, Vector2i(_haz_frame, row))
		if haz_kind == "lav" and randf() < 0.6:
			var cells := hazard.get_used_cells()
			if not cells.is_empty():
				var c2: Vector2i = cells[randi() % cells.size()]
				FX.fire(Vector2(c2.x * TS + 12, c2.y * TS + 4), 2, 0.3, 6.0)
		elif haz_kind == "zehir" and randf() < 0.5:
			var cells := hazard.get_used_cells()
			if not cells.is_empty():
				var c3: Vector2i = cells[randi() % cells.size()]
				FX.bubbles(Vector2(c3.x * TS + 12, c3.y * TS + 6), 1)


func build_hub(seed_value: int) -> void:
	## Ulu Kayın yurdu: düşmansız düz alan; Umay Ana (Kut bankası + kalıcı armağan), Demirci (parşömen), Ozan (destan).
	hub = true
	rng.seed = seed_value
	biome = Game.biome_for_depth(1)
	art = biome.get("art", {}).duplicate()
	art["ambient"] = [0.5, 0.48, 0.62]
	art["sun_energy"] = 0.3
	art["particles"] = "ruh"
	art["decor_tint"] = [0.86, 0.84, 0.9]
	Game.run["biome"] = "yurt"
	_generate_hub()
	# mürekkep yurdu: kutsal gece göğü, kuzey ışıkları, dağların ardında Ulu Kayın (Bai-Terek), uzak oba (paralaks,
	# ışık, derecelendirme data/yurt_v2.json; süsler sus_v2.json)
	var yv2: Dictionary = Data.load_json("res://data/yurt_v2.json")
	for k in yv2:
		if not String(k).begins_with("_"):
			art[k] = yv2[k]
	HikayeSahne.yurt_sabah(art)   # v42: tan söktüyse yurt sabah ışığında
	_build_tiles()
	decor_root = Node2D.new()
	decor_root.z_index = -2
	add_child(decor_root)
	decal_root = Node2D.new()
	decal_root.z_index = 1
	add_child(decal_root)
	# yere serili kilimler ve taş yol: zeminin üstünde, oyuncu ve NPC'lerin altında (aynı z, ağaç sırası)
	_hub_floor = Node2D.new()
	add_child(_hub_floor)
	actors = Node2D.new()
	add_child(actors)
	proj_root = Node2D.new()
	proj_root.z_index = 20
	add_child(proj_root)
	fx_root = Node2D.new()
	fx_root.z_index = 50
	add_child(fx_root)
	FX.root = fx_root
	FX.level = self
	_build_lighting()
	_build_background()
	_place_hub()
	HikayeSahne.yurt(self)   # v42: Ulu Kayın'da alınan her örgü için altın yapraklar
	_spawn_player()
	camera.limit_right = HUB_W * TS
	_build_particles()
	_build_overlay_fx()
	Ses.music("yurt")
	Perde.acilis("yurt")
	if OS.get_cmdline_user_args().has("--yurt-tur"):
		var tour: Node = load("res://tools/tests/yurt_turu.gd").new()
		tour.set("level", self)
		add_child(tour)


func build_konak(seed_value: int) -> void:
	## v32 Konak: Kut Kapısı'ndan (ya da bosstan) sonra, bir sonraki derinliğin biyomunda kurulan gezgin kervan konağı.
	## Düşmansız kısa düz alan (data/konak.json): konak ateşi (Umay Ocağı), Bengisu Usta'nın tezgâhı, biyoma göre
	## çadır / kazan / fener / at / balbal, bir önceki bölümde pazar çıkmadıysa Bezirgân Sartak, sağda Kut Kapısı.
	konak = true
	rng.seed = seed_value
	var K: Dictionary = Data.load_json("res://data/konak.json")
	var G: Dictionary = K.get("genel", {})
	biome = Game.biome_for_depth(int(Game.run.get("depth", 1)))
	art = _stil_art(biome.get("art", {}))
	var B: Dictionary = K.get("biyom", {}).get(String(biome.get("id", "")), {})
	if B.has("ambient"):
		art["ambient"] = B["ambient"]
	# v40: konak derecesi (konak.json "genel.grade" / "genel.huzme", biyom girdisi üstüne biner): ocak sıcaklığı
	if G.has("grade"):
		_art_birlestir({"grade": G["grade"]})
	if G.has("huzme"):
		_art_birlestir({"huzme": G["huzme"]})
	if B.has("grade"):
		_art_birlestir({"grade": B["grade"]})
	art["decor_tint"] = B.get("decor_tint", [0.92, 0.9, 0.94])
	Game.run["biome"] = biome.get("id", "otuken")
	_generate_konak(int(G.get("genislik", 64)), int(G.get("yuzey", 30)))
	_build_tiles()
	decor_root = Node2D.new()
	decor_root.z_index = -2
	add_child(decor_root)
	decal_root = Node2D.new()
	decal_root.z_index = 1
	add_child(decal_root)
	_hub_floor = Node2D.new()
	add_child(_hub_floor)
	actors = Node2D.new()
	add_child(actors)
	proj_root = Node2D.new()
	proj_root.z_index = 20
	add_child(proj_root)
	fx_root = Node2D.new()
	fx_root.z_index = 50
	add_child(fx_root)
	FX.root = fx_root
	FX.level = self
	_build_lighting()
	_build_background()
	_place_konak(G, B)
	_spawn_player()
	camera.limit_right = int(G.get("genislik", 64)) * TS
	_build_particles()
	_build_overlay_fx()
	Usta.yeni_konak(seed_value)
	Ses.music(String(G.get("muzik", "yurt")))
	Perde.acilis("konak")   # v40: sıcak amber solma
	print("[konak] derinlik=%d biyom=%s tohum=%d bezirgan=%d" % [int(Game.run.get("depth", 1)), String(biome.get("id", "")), seed_value, 1 if bezirgan else 0])


func _generate_konak(w: int, top: int) -> void:
	## Düz zemin, iki yanı kapalı; sağ uçta kapıya doğru hafif seki
	style = "konak"
	grid.resize(W * H)
	grid.fill(0)
	heights = []
	for x in W:
		var h := top
		if x > w - 14:
			h = top - int((x - (w - 14)) / 7)
		heights.append(h)
		for y in range(h, H):
			grid[idx(x, y)] = 1
		if x >= w:
			for y in H:
				grid[idx(x, y)] = 1
	for y in range(0, top):
		grid[idx(0, y)] = 1


func _place_konak(G: Dictionary, B: Dictionary) -> void:
	## Konak yerleşimi (data/konak.json): yol taşları, biyom süsleri, Umay Ocağı, Bengisu Usta + tezgâh, Bezirgân, kapı
	var w := int(G.get("genislik", 64))
	var xk := 3.0
	var yi := 0
	while xk < w - 3.0:
		_hub_prop("yh_yol_%d" % (yi % 3 + 1), xk, 0, yi % 2 == 1, _hub_floor, 1.0)
		xk += 3.15
		yi += 1
	for pr in B.get("props", []):
		var z := int(pr[2]) if pr.size() > 2 else -3
		var flip: bool = bool(pr[3]) if pr.size() > 3 else false
		if String(pr[0]).begins_with("yh_hali"):
			_hub_prop(String(pr[0]), float(pr[1]), 1, flip, _hub_floor, 1.0)
			var cx := int(float(pr[1]))
			for x in range(cx - 2, cx + 3):
				overlay.erase_cell(Vector2i(x, surface_y(x) - 1))
		else:
			_hub_prop(String(pr[0]), float(pr[1]), z, flip)
	# Umay Ocağı: konak ateşi (ısı + kor), yanından geçince Kut Umay'a ulaşır
	var ax := float(G.get("ates", 22))
	_hub_prop("konak_ates", ax, -2)
	konak_ates = _hub_px(ax, 0.0)
	_hub_fire(_hub_px(ax, -30), Color(1.0, 0.62, 0.3), 260.0, 1.3)
	var sm := _hub_emitter(_hub_px(ax, -40), 10, 5.0, Color(0.5, 0.5, 0.56, 0.2), Vector2(3, 1), false, -8)
	sm.direction = Vector2(0.25, -1)
	sm.spread = 14.0
	sm.initial_velocity_min = 8.0
	sm.initial_velocity_max = 14.0
	sm.gravity = Vector2(3, -3)
	sm.scale_amount_min = 1.0
	sm.scale_amount_max = 1.8
	# Bengisu Usta: tezgâh (kütük örs + kor mangalı), kendisi tezgâhın 26 birim sağında (usta_ink.STAND_X)
	var tx := float(G.get("tezgah", 33))
	_hub_prop("usta_tezgah", tx, -3)
	titrek(add_light(_hub_px(tx, -22) + Vector2(-24, 0), Color(1.0, 0.5, 0.2), 150.0, 1.0, decor_root), "ocak")
	var n := NPC.new()
	n.id = "usta"
	n.display_name = Usta.ad()
	n.soz = Usta.soz(String(biome.get("id", "")), "usta_kisa")
	if Hikaye.parca_sayi() > 0 and int(Game.run.get("depth", 1)) % 2 == 0:
		n.soz = Hikaye.soz("usta", int(Game.run.get("depth", 1)))   # v42: dönen örgülere sözü
	n.level = self
	n.position = _hub_px(tx, 0.0) + Vector2(26.0, 0.0)
	actors.add_child(n)
	npcs.append(n)
	_konak_yoldaslar(G)   # v42: Umay Ana, Ozan, Demirci, Alp Ata kervanla
	# Bezirgân: bir önceki derinlikte pazar çıkmadıysa kervan konağa gelir
	if not bool(Game.run.get("bezirgan_gordu", false)) or Level.bezirgan_zorla:
		var bx := int(G.get("bezirgan", 47))
		bezirgan = Bezirgan.new()
		bezirgan.level = self
		bezirgan.position = Vector2(bx * TS + TS / 2.0, surface_y(bx) * TS)
		bezirgan.offers = Pazar.teklifler(int(Game.run.get("depth", 1)), false)
		bezirgan.soz = Usta.soz(String(biome.get("id", "")), "bezirgan")
		actors.add_child(bezirgan)
	Game.run["bezirgan_gordu"] = false
	# çıkış: Kut Kapısı (taş kemer)
	var ex := int(G.get("kapi", 58))
	exit_pos = Vector2(ex * TS + TS / 2.0, surface_y(ex) * TS)
	var gate := KutGate.new()
	gate.position = exit_pos
	decor_root.add_child(gate)
	var portal := FX.anim("rift_portal", exit_pos + Vector2(0, -34), 0.0, 1.0, Color(0.6, 1.0, 1.0, 0.85))
	if portal:
		portal.loop = true
		portal.z_index = -1
		portal.reparent(decor_root)
	add_light(exit_pos + Vector2(0, -60), Color(0.45, 0.9, 1.0), 240.0, 1.3, decor_root)
	_hub_fire(_hub_px(ex - 2.6, -50), Color(1.0, 0.6, 0.28), 150.0, 0.8)
	var kp := _hub_emitter(exit_pos + Vector2(0, -70), 14, 5.0, Color(0.6, 1.5, 1.5, 0.9), Vector2(40, 60), true, 6)
	kp.direction = Vector2(0, -1)
	kp.initial_velocity_min = 3.0
	kp.initial_velocity_max = 9.0
	kp.gravity = Vector2(0, -2)
	kp.scale_amount_min = 0.08
	kp.scale_amount_max = 0.16


func _konak_yoldaslar(G: Dictionary) -> void:
	## v42 Konak yoldaşları (data/konak.json "yoldas": [id, karo x]): yurdun dört sakini de kervanla yol alır — Umay Ana
	## ocağın başında (Kut armağanları), Ozan ateşin öbür yanında (destan özeti, açılışı yeniden dinlet), Demirci Kam
	## Kuzgun (parşömen), Alp Ata (savaş sanatı). Hizmet ekranları yurttakilerle aynı (Main._on_npc). Sözleri hikâye
	## ilerlemesine göre (Hikaye.soz); biyoma göre yerleri konak.json "biyom.<id>.yoldas" ile değişebilir.
	var salt := int(Game.run.get("depth", 1)) + int(Game.meta.get("runs", 0))
	var bid := String(biome.get("id", ""))
	var yer: Array = Data.load_json("res://data/konak.json").get("biyom", {}).get(bid, {}).get("yoldas", G.get("yoldas", []))
	var adlar: Dictionary = Data.story.get("npcs", {})
	for yd in yer:
		var id := String(yd[0])
		var n := NPC.new()
		n.id = id
		n.display_name = String(adlar.get(id, {}).get("name", id))
		n.soz = Hikaye.soz(id, salt, true)
		n.level = self
		n.position = _hub_px(float(yd[1]), 0.0)
		actors.add_child(n)
		npcs.append(n)
		salt += 1


func _konak_tick() -> void:
	## Umay Ocağı: oyuncu ateşin yanından geçince taşınan Kut Umay'a ulaşır (yurttaki Umay Ana gibi; kalıcı bankaya)
	if _ocak_done or player == null or player.dead:
		return
	if absf(player.global_position.x - konak_ates.x) < 40.0 and absf(player.global_position.y - konak_ates.y) < 48.0:
		_ocak_done = true
		var k := int(Game.run.get("kut", 0))
		if k > 0:
			Game.bank_run_kut()
			Ses.play("kut_banka")
			FX.soul(player.center(), Color(0.6, 1.0, 1.0), 30)
			FX.ring(konak_ates + Vector2(0, -24), 50, Color(0.6, 1.0, 1.0), 0.6)
			FX.text(konak_ates + Vector2(0, -60), "%d Kut Umay'a ulaştı" % k, Color(0.6, 1.0, 1.0), 9)
			var m: Node = get_parent()
			if m and m.get("hud"):
				m.hud.flash_msg = "Umay Ocağı: %d Kut Umay Ana'ya ulaştı (banka %d)." % [k, int(Game.meta.get("kut_bank", 0))]
				m.hud.flash_t = 3.5


func _generate_hub() -> void:
	style = "yurt"
	grid.resize(W * H)
	grid.fill(0)
	heights = []
	var top := 30
	for x in W:
		var h := top
		if x > 70:
			h = top - int((x - 70) / 10)  # çıkışa doğru hafif yokuş
		heights.append(h)
		for y in range(h, H):
			grid[idx(x, y)] = 1
		if x >= HUB_W:
			for y in H:
				grid[idx(x, y)] = 1
	# giriş duvarı: sol kenar kapalı
	for y in range(0, top):
		grid[idx(0, y)] = 1


func _place_hub() -> void:
	## v13 Ulu Kayın Yurdu: soldan sağa giriş tuğu ve kurgan, kutsal pınar, dilek kayını, Umay sunağı, han otağı,
	## demirci ocağı, kartal tüneği ve eğerli at, Ozan'ın kilimli köşesi, süslü yurt ve kazan, balballar, taç kapı.
	## Bütün süsler 1.5x yoğunlukta çizilip 2/3 ölçekle gösterilir (zeminle aynı doku pikseli).
	# --- zemin: taş yol ve kilimler
	var xk := 3.0
	var yi := 0
	while xk < 90.0:
		_hub_prop("yh_yol_%d" % (yi % 3 + 1), xk, 0, yi % 2 == 1, _hub_floor, 1.0)
		xk += 3.15
		yi += 1
	# kapı sekisinin basamak yüzleri: toprak yerine yontma taş
	_hub_prop("yh_seki", 79.5, 0, false, _hub_floor, 0.0)
	_hub_prop("yh_seki", 89.5, 0, false, _hub_floor, 0.0)
	for r in [["yh_hali_1", 40.5], ["yh_hali_2", 61.6], ["yh_hali_2", 30.2], ["yh_hali_1", 85.0]]:
		_hub_prop(r[0], float(r[1]), 1, false, _hub_floor, 1.0)
		var cx := int(float(r[1]))
		for x in range(cx - 2, cx + 3):
			overlay.erase_cell(Vector2i(x, surface_y(x) - 1))
	# --- giriş: tuğ, kandil, dikili taşlar, balballar
	_hub_prop("yh_tug_m", 2.6, -3)
	_hub_prop("yh_kandil", 7.6, -1)
	_hub_prop("yh_kurgan", 10.5, -4)
	_hub_prop("yh_balbal_1", 14.2, -2)
	_hub_prop("yh_balbal_2", 15.6, -3, true)
	# --- Umay köşesi
	_hub_prop("yh_kayin", 24.6, -6)
	_hub_prop("yh_pinar", 19.6, -4)
	_hub_prop("yh_sunak", 33.0, -3)
	_hub_prop("yh_mangal", 27.0, -1)
	_hub_prop("yh_fener", 35.0, -2)
	# --- han otağı ve iki yanında tuğlar
	_hub_prop("yh_otag", 40.5, -5)
	_hub_prop("yh_tug_k", 36.3, -6)
	_hub_prop("yh_tug_m", 44.9, -6, true)
	_hub_prop("yh_kandil", 37.7, -1)
	_hub_prop("yh_kandil", 43.4, -1)
	# --- demirci
	_hub_prop("yh_demirhane", 50.4, -4)
	_hub_prop("yh_ors", 45.6, 1)
	# --- kartal ve at
	_hub_prop("yh_kartal", 54.9, -3)
	_hub_prop("yh_at", 57.6, -2, true)
	# --- Ozan köşesi
	_hub_prop("yh_hali_sergi", 62.3, -4)
	_hub_prop("yh_mangal", 59.2, -1)
	_hub_prop("yh_fener", 65.4, -2, true)
	# --- süslü yurt, kazan, balballar
	_hub_prop("yh_cadir", 69.6, -5)
	_hub_prop("yh_tug_k", 73.2, -6)
	_hub_prop("yh_kazan", 75.3, -2)
	_hub_prop("yh_balbal_2", 77.8, -3)
	_hub_prop("yh_balbal_1", 79.0, -3, true)
	# --- taç kapı (Kut Kapısı'nın ardında) ve yanındaki tuğlar
	var ex := HUB_W - 7
	_hub_prop("yh_kapi", ex, -6)
	_hub_prop("yh_tug_m", ex - 4.4, -7)
	_hub_prop("yh_tug_k", ex + 3.6, -7, true)
	_hub_prop("yh_kandil", ex - 2.9, -1)
	_hub_prop("yh_kandil", ex + 3.0, -1)
	_hub_lights()
	_hub_strings()
	_hub_particles()
	var defs := [["umay", "Umay Ana", 30], ["demirci", "Demirci Kam Kuzgun", 47], ["ozan", "Ozan Bilge Kopuz", 61], ["alp_ata", "Alp Ata", 71]]   # v27 savaş sanatları ustası
	for d in defs:
		var n := NPC.new()
		n.id = d[0]
		n.display_name = d[1]
		n.soz = Hikaye.soz(String(d[0]), int(Game.meta.get("runs", 0)))   # v42: ilerlemeye göre söz
		n.level = self
		n.position = Vector2(int(d[2]) * TS + TS / 2.0, surface_y(int(d[2])) * TS)
		actors.add_child(n)
		npcs.append(n)
	# çıkış: Kut Kapısı
	exit_pos = Vector2(ex * TS + TS / 2.0, surface_y(ex) * TS)
	var gate := KutGate.new()
	gate.position = exit_pos
	if not _decor_v2("yh_kapi").is_empty():
		gate.frame = false  # v2: taç kapı kemeri çerçeve; içinde yalnızca eşik ve kut girdabı
		gate.portal_scale = 1.45
	decor_root.add_child(gate)
	var portal := FX.anim("rift_portal", exit_pos + Vector2(0, -34), 0.0, 1.0, Color(0.6, 1.0, 1.0, 0.85))
	if portal:
		portal.loop = true
		portal.z_index = -1
		portal.reparent(decor_root)
	add_light(exit_pos + Vector2(0, -60), Color(0.45, 0.9, 1.0), 260.0, 1.4, decor_root)


func _hub_px(tx: float, dy := 0.0) -> Vector2:
	## Karo x'i (kesirli) → o sütunun yüzeyindeki dünya noktası.
	return Vector2(tx * TS + TS / 2.0, surface_y(int(floor(tx))) * TS + dy)


func _hub_prop(dname: String, tx: float, z := 0, flip := false, parent: Node = null, dy := 2.0, glow := Color(1.5, 1.35, 1.2)) -> Sprite2D:
	## Yurt süsü: mürekkep "<ad>_v2" (sus_v2.json / decor_v2.json, doku pikseli / dünya birimi "texel"); yoksa null.
	var d2 := _decor_v2(dname)
	if d2.is_empty():
		return null
	return _hub_prop_ink(d2, dname, tx, z, flip, parent, dy, glow)


func _hub_prop_ink(d: Dictionary, dname: String, tx: float, z: int, flip: bool, parent: Node, dy: float, glow: Color) -> Sprite2D:
	var k := 1.0 / float(d.get("texel", 4.0))
	var s := Sprite2D.new()
	s.texture = d["tex"]
	s.centered = false
	s.offset = Vector2(-float(d["origin"][0]), -float(d["origin"][1]))
	s.scale = Vector2(-k if flip else k, k)
	s.position = _hub_px(tx, dy)
	s.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	var m := ShaderMaterial.new()
	m.shader = load("res://shaders/env_ink.gdshader")
	m.set_shader_parameter("moon_gain", float(art.get("ground_moon_gain", 0.6)))
	var dt: Array = art.get("decor_tint", [1.0, 1.0, 1.0])
	m.set_shader_parameter("tint", Color(dt[0], dt[1], dt[2]))
	s.material = m
	s.z_index = z
	(parent if parent else decor_root).add_child(s)
	if d.get("glow_tex") != null:
		var g := Sprite2D.new()
		g.texture = d["glow_tex"]
		g.centered = false
		g.offset = s.offset
		g.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
		var gm := CanvasItemMaterial.new()
		gm.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
		gm.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
		g.material = gm
		g.self_modulate = glow
		s.add_child(g)
		# alevler ve kut ışığı titrer / nefes alır
		var tw := g.create_tween().set_loops()
		var fast := dname in ["yh_mangal", "yh_kandil", "yh_kazan", "yh_kapi", "yh_sunak", "yh_demirhane", "yh_ors", "konak_ates", "usta_tezgah"]
		tw.tween_property(g, "self_modulate:a", 0.78, rng.randf_range(0.14, 0.2) if fast else 1.6)
		tw.tween_property(g, "self_modulate:a", 1.0, rng.randf_range(0.16, 0.24) if fast else 1.8)
	return s


func _hub_fire(pos: Vector2, col: Color, radius: float, energy: float, embers := true) -> void:
	## Titreyen sıcak ışık + yukarı süzülen kor.
	var l := add_light(pos, col, radius, energy, decor_root)
	titrek(l, "ocak")   # v40
	if embers:
		var p := _hub_emitter(pos + Vector2(0, 4), 7, 1.4, Color(1.6, 0.75, 0.3, 0.9), Vector2(3, 2), true)
		p.direction = Vector2(0, -1)
		p.spread = 25.0
		p.initial_velocity_min = 14.0
		p.initial_velocity_max = 30.0
		p.gravity = Vector2(4, -10)
		p.scale_amount_min = 0.06
		p.scale_amount_max = 0.12


func _hub_emitter(pos: Vector2, amount: int, life: float, col: Color, extents: Vector2, additive: bool, z := 4) -> CPUParticles2D:
	var p := CPUParticles2D.new()
	p.position = pos
	p.amount = amount
	p.lifetime = life
	p.preprocess = life
	p.texture = FX.dot_tex()
	p.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
	p.emission_rect_extents = extents
	p.local_coords = false
	p.color = col
	var g := Gradient.new()
	g.set_color(0, Color(1, 1, 1, 0))
	g.set_color(1, Color(1, 1, 1, 0))
	g.add_point(0.2, Color(1, 1, 1, 1))
	g.add_point(0.7, Color(1, 1, 1, 0.8))
	p.color_ramp = g
	if additive:
		var am := CanvasItemMaterial.new()
		am.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
		am.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
		p.material = am
	p.z_index = z
	decor_root.add_child(p)
	return p


func _hub_lights() -> void:
	## Sıcak (ateş, fener) / soğuk (kut, pınar) ışık karşıtlığı. Işık sayısı düşük tutulur: yakın kaynaklar
	## tek ışıkta birleşir, fenerlerin parıltısı ışık değil ışıma dokusudur.
	var warm := Color(1.0, 0.6, 0.28)
	_hub_fire(_hub_px(7.6, -52), warm, 170.0, 1.1)
	for tx in [27.0, 59.2]:
		_hub_fire(_hub_px(tx, -24), warm, 190.0, 1.25)
	# otağ: iki kandil ve kapıdan sızan altın ışık tek ışıkta
	_hub_fire(_hub_px(40.5, -40), Color(1.0, 0.66, 0.34), 240.0, 1.15)
	# demirci ocağı: güçlü, nabız gibi atan turuncu
	titrek(add_light(_hub_px(50.7, -10), Color(1.0, 0.45, 0.16), 230.0, 1.5, decor_root), "ocak")
	# kazan ateşi
	_hub_fire(_hub_px(75.3, -6), warm, 150.0, 1.0)
	# kut: pınar ve dilek kayını (soğuk turkuaz)
	add_light(_hub_px(22.0, -80), Color(0.45, 0.98, 0.95), 270.0, 0.85, decor_root)
	# taç kapının kandilleri (kapının turkuaz ışığı _place_hub'da)
	_hub_fire(_hub_px(HUB_W - 7, -60), warm, 230.0, 0.9)


func _hub_string(a: Vector2, b: Vector2, sag: float, lanterns: bool, z := -5) -> void:
	## İki direk arasında sarkık ip: renkli üçgen bayrakçıklar ya da küçük kehribar fenerler.
	## Bütün bayrakçıklar tek Polygon2D'de (köşe renkli çokgenler): bir çizim çağrısı.
	var line := Line2D.new()
	line.width = 1.0
	line.default_color = Color(0.16, 0.12, 0.1)
	# v2: kenar yumuşatmalı, mürekkep renkli kıl ip; bayrakçıkların arkasında koyu kontur çokgeni
	line.width = 0.9
	line.default_color = Color(0.08, 0.08, 0.11)
	line.antialiased = true
	line.z_index = z
	var n := 24
	for i in n + 1:
		var t := float(i) / n
		line.add_point(a.lerp(b, t) + Vector2(0, sin(t * PI) * sag))
	decor_root.add_child(line)
	var cols := [Color(0.78, 0.18, 0.2), Color(0.95, 0.75, 0.25), Color(0.2, 0.42, 0.8), Color(0.92, 0.9, 0.84), Color(0.2, 0.62, 0.52)]
	var shape := PackedVector2Array([Vector2(-1.5, 1), Vector2(1.5, 1), Vector2(2, 3), Vector2(1.5, 5), Vector2(-1.5, 5), Vector2(-2, 3)]) if lanterns 		else PackedVector2Array([Vector2(-2.5, 0), Vector2(2.5, 0), Vector2(0, 6)])
	var verts := PackedVector2Array()
	var vcols := PackedColorArray()
	var polys: Array = []
	var steps := int(a.distance_to(b) / (16.0 if lanterns else 8.0))
	for i in range(1, steps):
		var t := float(i) / steps
		var p := (a.lerp(b, t) + Vector2(0, sin(t * PI) * sag)).round()
		var col: Color = (Color(2.2, 1.3, 0.5) if i % 2 else Color(2.0, 0.6, 0.4)) if lanterns else cols[i % cols.size()]
		var rot := 0.0 if lanterns else sin(i * 1.7) * 0.2
		var idxs := PackedInt32Array()
		for v in shape:
			idxs.append(verts.size())
			verts.append(p + v.rotated(rot))
			vcols.append(col)
		polys.append(idxs)
	if verts.is_empty():
		return
	# mürekkep kontur: her bayrakçığın biraz büyütülmüş koyu kopyası arkada (kenar yumuşatmalı)
	var ov := PackedVector2Array()
	var oc := PackedColorArray()
	var ops: Array = []
	for fi in polys.size():
		var ix: PackedInt32Array = polys[fi]
		var c0 := Vector2.ZERO
		for j in ix:
			c0 += verts[j]
		c0 /= float(ix.size())
		var nx := PackedInt32Array()
		for j in ix:
			nx.append(ov.size())
			ov.append(c0 + (verts[j] - c0) * 1.0 + (verts[j] - c0).normalized() * 0.7)
			oc.append(Color(0.08, 0.08, 0.11))
		ops.append(nx)
	var po := Polygon2D.new()
	po.polygon = ov
	po.polygons = ops
	po.vertex_colors = oc
	po.antialiased = true
	po.z_index = z
	decor_root.add_child(po)
	# gölge yarısı: bayrakçıkların alt yarısı bir ton koyu (cel)
	for i in vcols.size():
		if not lanterns and i % 3 == 2:
			vcols[i] = vcols[i].darkened(0.35)
	var pg := Polygon2D.new()
	pg.polygon = verts
	pg.polygons = polys
	pg.vertex_colors = vcols
	pg.antialiased = true
	pg.z_index = z
	if lanterns:
		var um := CanvasItemMaterial.new()
		um.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
		pg.material = um
	decor_root.add_child(pg)


func _hub_strings() -> void:
	# tuğ tepeleri ↔ otağ tuğu: bayrakçık dizileri
	var otag_top := _hub_px(40.5, -176)
	_hub_string(_hub_px(36.3, -150) + Vector2(-8, 0), otag_top, 12.0, false, -7)
	_hub_string(otag_top, _hub_px(44.9, -150) + Vector2(8, 0), 12.0, false, -7)
	# otağ ↔ demirhane saçağı, Ozan ↔ yurt: fener dizileri
	_hub_string(_hub_px(44.9, -120) + Vector2(8, 0), _hub_px(47.5, -86), 6.0, true, -6)
	_hub_string(_hub_px(59.6, -84), _hub_px(65.4, -94) + Vector2(-8, 0), 10.0, true, -6)
	_hub_string(_hub_px(65.4, -94), _hub_px(69.6, -100), 8.0, false, -7)
	_hub_string(_hub_px(69.6, -100), _hub_px(73.2, -150) + Vector2(-8, 0), 10.0, false, -7)
	# taç kapı: iki tuğ arasında, kemerin üstünden geçen bayrakçıklar
	var ex := float(HUB_W - 7)
	_hub_string(_hub_px(ex - 4.4, -150) + Vector2(8, 0), _hub_px(ex, -176), 10.0, false, -8)
	_hub_string(_hub_px(ex, -176), _hub_px(ex + 3.6, -150) + Vector2(-8, 0), 10.0, false, -8)
	# dilek kayını ↔ fener: fener dizisi
	_hub_string(_hub_px(28.0, -120), _hub_px(35.0, -94), 14.0, true, -6)


func _hub_particles() -> void:
	var gy := 30.0 * TS
	# ateş böcekleri: yurt boyunca yere yakın, sarı-yeşil
	var ff := _hub_emitter(Vector2(HUB_W * TS / 2.0, gy - 46), 70, 6.0, Color(1.3, 1.5, 0.55, 0.9), Vector2(HUB_W * TS / 2.0, 40), true, 6)
	ff.direction = Vector2(1, -0.2)
	ff.spread = 180.0
	ff.initial_velocity_min = 3.0
	ff.initial_velocity_max = 10.0
	ff.gravity = Vector2(0, -1.5)
	ff.scale_amount_min = 0.1
	ff.scale_amount_max = 0.17
	# kut zerreleri: dilek kayınından ve pınardan göğe yükselen turkuaz ruhlar
	var sp := _hub_emitter(_hub_px(23.0, -60), 26, 7.0, Color(0.6, 1.5, 1.4, 0.9), Vector2(70, 50), true, 6)
	sp.direction = Vector2(0, -1)
	sp.spread = 40.0
	sp.initial_velocity_min = 4.0
	sp.initial_velocity_max = 12.0
	sp.gravity = Vector2(0, -3)
	sp.scale_amount_min = 0.1
	sp.scale_amount_max = 0.2
	# taç kapıdan süzülen kut
	var kp := _hub_emitter(_hub_px(HUB_W - 7, -70), 16, 5.0, Color(0.6, 1.5, 1.5, 0.9), Vector2(40, 60), true, 6)
	kp.direction = Vector2(0, -1)
	kp.initial_velocity_min = 3.0
	kp.initial_velocity_max = 9.0
	kp.gravity = Vector2(0, -2)
	kp.scale_amount_min = 0.08
	kp.scale_amount_max = 0.16
	# pınar serpintisi
	var wp := _hub_emitter(_hub_px(19.5, -8), 14, 1.2, Color(0.7, 1.4, 1.5, 0.8), Vector2(8, 2), true, 6)
	wp.direction = Vector2(0, -1)
	wp.spread = 60.0
	wp.initial_velocity_min = 10.0
	wp.initial_velocity_max = 26.0
	wp.gravity = Vector2(0, 60)
	wp.scale_amount_min = 0.06
	wp.scale_amount_max = 0.1
	# demirci ocağı kıvılcımları
	var fs := _hub_emitter(_hub_px(50.7, -12), 14, 0.9, Color(1.8, 0.9, 0.35, 1.0), Vector2(6, 2), true, 6)
	fs.direction = Vector2(0, -1)
	fs.spread = 35.0
	fs.initial_velocity_min = 30.0
	fs.initial_velocity_max = 80.0
	fs.gravity = Vector2(0, 120)
	fs.scale_amount_min = 0.06
	fs.scale_amount_max = 0.1
	# örste çekiç vuruşu: aralıklı kıvılcım patlaması
	var anvil := _hub_px(45.6, -26)
	var at := create_tween().set_loops()
	at.tween_interval(1.7)
	at.tween_callback(func() -> void: FX.sparks(anvil, Vector2(0.4, -1), Color(1.0, 0.75, 0.35), 7, 120.0))
	# duman: süslü yurdun tünlüğünden, kazandan ve ocak bacasından
	for spec in [[69.6, -96.0, 10], [75.3, -46.0, 8], [50.9, -138.0, 8]]:
		var sm := _hub_emitter(_hub_px(float(spec[0]), float(spec[1])), int(spec[2]), 6.0, Color(0.5, 0.5, 0.56, 0.22), Vector2(2, 1), false, -8)
		sm.direction = Vector2(0.3, -1)
		sm.spread = 12.0
		sm.initial_velocity_min = 6.0
		sm.initial_velocity_max = 12.0
		sm.gravity = Vector2(2, -2)
		sm.scale_amount_min = 0.9
		sm.scale_amount_max = 1.6


func nearest_npc() -> NPC:
	for n in npcs:
		if is_instance_valid(n) and n.near:
			return n
	return null


# ------------------------------------------------------------------ arazi üretimi
func idx(x: int, y: int) -> int:
	return y * W + x


func dump_png(path: String) -> void:
	## Hata ayıklama: ızgarayı 4x büyütülmüş PNG olarak yaz (katı kahve, platform sarı, hava koyu)
	var img := Image.create(W * 4, H * 4, false, Image.FORMAT_RGB8)
	for y in H:
		for x in W:
			var c := Color(0.08, 0.08, 0.12)
			match grid[idx(x, y)]:
				1:
					c = Color(0.55, 0.4, 0.3)
				2:
					c = Color(0.95, 0.8, 0.3)
			img.fill_rect(Rect2i(x * 4, y * 4, 4, 4), c)
	img.save_png(path)


func cell(x: int, y: int) -> int:
	if x < 0 or x >= W or y < 0:
		return 1
	if y >= H:
		return 1
	return grid[idx(x, y)]


func _generate() -> void:
	## v32: oda çizgesi; biyom "level" parametreleri (data/world.json: rows, yon) ve tüccar isteği üreticiye geçer
	var opts: Dictionary = {}
	for k in biome.get("level", {}):
		opts[k] = biome["level"][k]
	opts["pazar"] = _bz_istek
	opts["pazar_kapi"] = _bz_kapi
	# v41 bölüm türü: biyom + koşudaki önceki türler (art arda üç bölümün en az biri düz)
	opts["biyom"] = String(biome.get("id", "diger"))
	var gecmis: Array = Game.run.get("turler", [])
	opts["gecmis"] = gecmis
	opts["hikaye_odasi"] = HikayeSahne.oda_acik(int(Game.run.get("depth", 1)), int(rng.seed))   # v42: üç bölümde bir
	var r := LevelGen.generate(rng, W, H, int(Game.run.get("depth", 1)), art.get("styles", []), opts)
	tur = String(r.get("tur", "eski"))
	sahne_yeri = r.get("sahne", {})
	hikaye_yeri = r.get("hikaye", {})
	var gy: Array = gecmis.duplicate()
	gy.append(tur)
	if gy.size() > 6:
		gy = gy.slice(gy.size() - 6)
	Game.run["turler"] = gy
	grid = r["grid"]
	heights = r["heights"]
	style = r["style"]
	chunks = r["chunks"]
	carved = int(r.get("carved", 0))
	rooms = r["rooms"]
	doors = r["doors"]
	spawn_cell = r["spawn"]
	exit_cell = r["exit"]
	bounds = r["bounds"]
	metrics = r["metrics"]
	kaide_xs = r["kaide"]
	_gen = r
	print("[harita] derinlik=%d tür=%s stil=%s oda=%d ana=%d dal=%d çıkmaz=%d döngü=%d dikey=%d kapı=%d taşı=%d zamanlı=%d deneme=%d ok=%s" % [
		int(Game.run.get("depth", 1)), tur, style, int(metrics["oda"]), int(metrics["ana"]), int(metrics["dal"]), int(metrics["cikmaz"]),
		int(metrics["dongu"]), int(metrics["dikey_adim"]), int(metrics["kapi"]), int(metrics["tasi"]), int(metrics["zamanli"]), int(metrics["attempts"]), str(metrics["ok"])])


var _gen: Dictionary = {}   # üreticinin ham sonucu (tasi / zamanli listeleri)
## v41 bölüm türü (LevelGen.TURLER: acik / kale / inis / magara) ve anlatı kancaları: sahne_yeri (ana yolda en geniş
## düz taban {room, x0, x1, y}), hikaye_yeri (opts.hikaye_odasi ile ayrılan çıkmaz odanın ayakta durma hücresi {room, x, y})
var tur := "eski"
var sahne_yeri: Dictionary = {}
var hikaye_yeri: Dictionary = {}


func main_rooms() -> Array:
	## Ana yol odaları (giriş -> çıkış sırasıyla)
	var out: Array = []
	for rm in rooms:
		if int(rm.get("ana_i", -1)) >= 0 and rm["role"] != "yok":
			out.append(rm)
	out.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return int(a["ana_i"]) < int(b["ana_i"]))
	return out


func room_at(x: int, y: int) -> Dictionary:
	## Karoyu kapsayan oda (iç alan + 2 karo duvar payı); yoksa boş
	for rm in rooms:
		if rm["role"] == "yok":
			continue
		if x >= int(rm["ix0"]) - 2 and x <= int(rm["ix1"]) + 2 and y >= int(rm["iy0"]) - 2 and y <= int(rm["iy1"]) + 2:
			return rm
	return {}


func room_floor(rm: Dictionary, x: int) -> int:
	## Odanın x sütunundaki taban satırı (katı); sütun odanın dışındaysa en yakın kenar
	var fl: Array = rm["fl"]
	return int(fl[clampi(x - int(rm["ix0"]), 0, fl.size() - 1)])


func set_air(x: int, y: int) -> void:
	## v34: karo havaya döner (gizli cep, kilitli kapı): ızgara, zemin karosu silinir, komşu maskeleri ve sarkan örtü
	## (ot / kök) güncellenir, harita sisi yenilenir
	if x < 1 or x >= W - 1 or y < 1 or y >= H - 1 or grid[idx(x, y)] == 0:
		return
	grid[idx(x, y)] = 0
	grid_surum += 1
	if harita != null:
		harita.karo_degisti(x, y)
	if ground == null:
		return
	ground.erase_cell(Vector2i(x, y))
	overlay.erase_cell(Vector2i(x, y - 1))
	overlay.erase_cell(Vector2i(x, y + 1))
	_maske_yenile(x, y)


func set_solid(x: int, y: int) -> void:
	## v32: karo katı yapılır (zamanlı kapı): ızgara + zemin karo katmanı (komşu maskesiyle)
	if x < 0 or x >= W or y < 0 or y >= H:
		return
	grid[idx(x, y)] = 1
	grid_surum += 1
	if harita != null:
		harita.karo_degisti(x, y)
	if ground == null:
		return
	_maske_yenile(x, y)


func _maske_yenile(x: int, y: int) -> void:
	for p in [Vector2i(x, y), Vector2i(x - 1, y), Vector2i(x + 1, y), Vector2i(x, y - 1), Vector2i(x, y + 1)]:
		if cell(p.x, p.y) != 1 or _parmak.has(p):
			continue
		var m := 0
		if cell(p.x, p.y - 1) != 1:
			m |= 1
		if cell(p.x + 1, p.y) != 1:
			m |= 2
		if cell(p.x, p.y + 1) != 1:
			m |= 4
		if cell(p.x - 1, p.y) != 1:
			m |= 8
		ground.set_cell(p, 0, Vector2i(m, (p.x + p.y) % 3))


# ------------------------------------------------------------------ v34 merak: gizli cepler, pencereler, kilit, küpler
var _parmak := {}   # parmaklık karoları (ızgarada katı, karosu yok)
var _hazine_ilk: Array = []   # [Pickup, eşya]: kurulumdaki kaideli eşyalar (sayaç)


func _gizemler() -> void:
	## Üreticinin işaretlerinden düğümler: parmaklıklı pencereler, gizli cepler (kırık duvar), kilitli kapı (+ ödül odasına
	## ek altın). Lanet koşu boyunca sürer (Game.run "lanet").
	lanet = int(Game.run.get("lanet", 0))
	if lanet > 0:
		_lanet_aura_kur()
	for pw in _gen.get("pencereler", []):
		var pk := Parmaklik.new()
		pk.level = self
		pk.cells = pw["cells"]
		pk.oda_a = int(pw["a"])
		pk.oda_b = int(pw["b"])
		var c0: Vector2i = (pw["cells"] as Array)[0]
		var ymax := c0.y
		for c in pw["cells"]:
			ymax = maxi(ymax, int(c.y))
			_parmak[c] = true
		pk.position = Vector2(c0.x * TS, (ymax + 1) * TS)
		add_child(pk)
		pencereler.append(pk)
	for cp in _gen.get("cepler", []):
		var kd := KirikDuvar.new()
		kd.level = self
		kd.cells = cp["wall"]
		kd.cep = cp["cep"]
		kd.oda = int(cp["room"])
		kd.yon = int(cp["yon"])
		kd.icerik = String(cp["icerik"])
		kd.kur()
		var w0: Vector2i = (cp["wall"] as Array)[0]
		kd.position = Vector2(w0.x * TS, int(cp["taban"]) * TS)
		add_child(kd)
		kiriklar.append(kd)
	for kl in _gen.get("kilitli", []):
		var kk := KilitliKapi.new()
		kk.level = self
		kk.cell = Vector2i(int(kl["x"]), int(kl["y"]))
		kk.oda = int(kl["room"])
		kk.position = Vector2(kk.cell.x * TS, kk.cell.y * TS)
		add_child(kk)
		kilitler.append(kk)
		# kilitli odanın ödülüne ek: altın yığını (ödül işaretinin yanında)
		var rm: Dictionary = rooms[kk.oda]
		var om := LevelGen._odul_mid(rm)
		var oy := _floor_below(om, int(rm["iy0"]))
		for g in 8:
			drop_orb("gold", Vector2(om * TS + 12 + randf_range(-26, 26), oy * TS - 20))


func anahtar_birak(pos: Vector2) -> void:
	var an := Anahtar.new()
	an.level = self
	an.position = pos
	var rm := room_at(int(floor(pos.x / TS)), int(floor((pos.y - 8.0) / TS)))
	an.oda = int(rm.get("id", -1))
	add_child(an)
	anahtarlar.append(an)


func break_cracks(box: Rect2) -> void:
	## Player.gd her savuruşta çağırır (v34: önceden boştu): kırık duvarlar ve küpler
	for kd in kiriklar:
		if is_instance_valid(kd):
			kd.vur(box)
	for kp in kupler:
		if is_instance_valid(kp):
			kp.vur(box)


func _kupler_yerlestir() -> void:
	## v34 "her odada bir şey": içinde yaratık / ganimet / gizli cep / pencere / sandık / tehlike olmayan odaya 2-3 küp;
	## diğer dövüş odalarına %35 ihtimalle 1 küp. Taban hücresi: ayakta durulur, tehlike / kuyu ağzı değil, doğuş
	## noktası, Kut Kapısı, Kut Taşları ve tezgâhtan uzak.
	var dolu := {}
	for e in get_tree().get_nodes_in_group("dusman"):
		if is_instance_valid(e) and not e.is_queued_for_deletion() and e.get("level") == self:
			dolu[int(room_at(int(e.position.x / TS), int((e.position.y - 4.0) / TS)).get("id", -1))] = true
	for c in get_children():
		if c is Pickup:
			dolu[int(room_at(int(c.position.x / TS), int((c.position.y - 4.0) / TS)).get("id", -1))] = true
	for arr in [kiriklar, pencereler, sandiklar, kilitler, anahtarlar]:
		for n in arr:
			for id in n.odalar():
				dolu[int(id)] = true
	for rm in rooms:
		if rm["role"] == "yok" or String(rm.get("odul", "")) in ["pazar", "hikaye"]:
			continue
		var id := int(rm["id"])
		var haz := false
		for x in range(int(rm["ix0"]), int(rm["ix1"]) + 1):
			if cell(x, room_floor(rm, x)) == 3 or cell(x, room_floor(rm, x) + 1) == 3:
				haz = true
				break
		var n := 0
		if not dolu.has(id) and not haz:
			n = rng.randi_range(2, 3)
		elif rm["role"] in ["ana", "dal", "cikis", "giris"] and rng.randf() < 0.35:
			n = 1
		var tries := 0
		var placed: Array = []
		while n > 0 and tries < 24:
			tries += 1
			var x := rng.randi_range(int(rm["ix0"]) + 1, int(rm["ix1"]) - 1)
			var sp: Vector2i = LevelGen._floor_spot(grid, W, H, rm, x)
			if absi(sp.x - spawn_cell.x) < 4 and absi(sp.y - spawn_cell.y) < 3:
				continue
			if absi(sp.x - exit_cell.x) < 4 and absi(sp.y - exit_cell.y) < 3:
				continue
			if bezirgan_alani(sp.x, 2):
				continue
			var ok := cell(sp.x, sp.y) == 0 and (cell(sp.x, sp.y + 1) == 1 or cell(sp.x, sp.y + 1) == 2)
			for t in _gen.get("tasi", []):
				if absi(int(t.x) - sp.x) < 3 and absi(int(t.y) - sp.y) < 3:
					ok = false
			for q in placed:
				if absi(int(q) - sp.x) < 2:
					ok = false
			for kd in kiriklar:
				if absi(int((kd.cells[0] as Vector2i).x) - sp.x) < 2 and absi(int((kd.cells[0] as Vector2i).y) - sp.y) < 5:
					ok = false
			if not ok:
				continue
			var kp := Kup.new()
			kp.level = self
			kp.oda = id
			kp.boy = rng.randf_range(0.8, 1.2)
			kp.position = Vector2(sp.x * TS + TS / 2.0 + rng.randf_range(-5.0, 5.0), (sp.y + 1) * TS)
			add_child(kp)
			kupler.append(kp)
			placed.append(sp.x)
			n -= 1


func sayac() -> Dictionary:
	## v34 tam harita sayacı ("Hazine 1/3, Tomar 0/2"): kalan / toplam. Hazine: kaideli eşyalar + lanetli sandıklar;
	## Tomar: Kut Tomarları; Gizli: kırılmamış gizli cepler; Anahtar: yerdeki anahtar + kilitli kapı
	var hz := 0
	var tm := 0
	if sayac_ilk.is_empty():
		# kurulum anı: kaideli eşyalar (alınınca kaidede eski eşya kalabilir: aynı eşya mı diye bakılır)
		_hazine_ilk = []
		for p in pickups:
			if is_instance_valid(p) and p.kind == "item" and bool(p.pedestal):
				_hazine_ilk.append([p, p.item])
	for hp in _hazine_ilk:
		if is_instance_valid(hp[0]) and not (hp[0] as Node).is_queued_for_deletion() and is_same(hp[0].item, hp[1]):
			hz += 1
	for p in pickups:
		if not is_instance_valid(p) or p.is_queued_for_deletion():
			continue
		if p.kind == "tilsim":
			tm += 1
	for sd in sandiklar:
		if is_instance_valid(sd) and not sd.acildi:
			hz += 1
	var gz := 0
	for kd in kiriklar:
		if is_instance_valid(kd) and not kd.kirildi:
			gz += 1
	var kl := 0
	for kk in kilitler:
		if is_instance_valid(kk) and not kk.acik:
			kl += 1
	return {"hazine": hz, "tomar": tm, "gizli": gz, "kilit": kl}


func lanet_baslat() -> void:
	## v34 lanetli sandık açıldı: LANET_OLDUR yaratık öldürene dek alınan hasar iki kat
	lanet = LANET_OLDUR
	Game.run["lanet"] = lanet
	_lanet_aura_kur()
	if player:
		FX.text(player.center() + Vector2(0, -50), "LANETLENDİN: %d öldür" % lanet, Color(0.85, 0.55, 1.0), 10)


func _lanet_aura_kur() -> void:
	if _lanet_aura != null and is_instance_valid(_lanet_aura):
		return
	if player == null:
		return
	var au := Sandik.Aura.new()
	au.level = self
	player.add_child(au)
	_lanet_aura = au


func _lanet_oldurme() -> void:
	if lanet <= 0:
		return
	lanet -= 1
	Game.run["lanet"] = lanet
	if lanet <= 0 and player:
		FX.text(player.center() + Vector2(0, -50), "Lanet kalktı", Color(0.9, 0.8, 1.0), 10)
		FX.ring(player.center(), 40, Color(0.85, 0.6, 1.0), 0.5)
		Ses.play("ruh_tasi", -6.0, 1.2)


func sandik_yakin() -> Node:
	for sd in sandiklar:
		if is_instance_valid(sd) and sd.near and not sd.acildi:
			return sd
	return null


# ------------------------------------------------------------------ karolar
func _art_cell() -> int:
	## Atlas hücresi (doku pikseli). Zemin dokuları 1.5 kat yoğun üretilir (36 px) ve karo katmanları
	## TS / hücre oranında küçültülür: dünya ölçüleri (TS = 24) ve fizik değişmez, 1080p'de her doku
	## pikseli 2x2 ekran pikseline düşer. v2 mürekkep zemini 48 px (1080p'de 1:1).
	return int(_tmeta().get("tile", TS))


var _tile_meta_cache: Dictionary = {}


func _tmeta() -> Dictionary:
	## Karo atlası meta bilgisi: "<biyom>_v2.json" (hücre boyu, maske / çayır / ışıma dokuları, yerleşim sütun/satır)
	if _tile_meta_cache.is_empty():
		_tile_meta_cache = Data.load_json("res://assets/tiles/%s.json" % _tile_id())
	return _tile_meta_cache


func _stil_art(base: Dictionary) -> Dictionary:
	## data/stil_v2.json içindeki biyom girdisi art değerlerini ezer (paralaks katman listesi, ışık, ön plan, renk
	## derecelendirme)
	var a := base.duplicate(true)
	var path := "res://data/stil_%s.json" % Data.STIL
	if not FileAccess.file_exists(path):
		return a
	var over: Dictionary = Data.load_json(path).get(String(biome.get("id", "")), {})
	for k in over:
		a[k] = over[k]
	return a


var _tile_pack := 1  # karo atlası doku paketinden geldiyse çarpanı (TileSet gerçek doku boyutunu kullanır)


func _tile_px() -> int:
	## Karo atlas hücresinin gerçek doku pikseli (temel hücre x paket çarpanı)
	return _art_cell() * _tile_pack


func _atlas_tex(path: String) -> CanvasTexture:
	## Karo atlası: paket varsa gerçek boyutlu HD doku; normal yuvasında kaplama maskesi (UV ile örneklenir)
	var ct := CanvasTexture.new()
	ct.diffuse_texture = Data.tex_full(path)
	# mürekkep zemini: normal yuvasında toprak kaplama maskesi (ground_ink.gdshader), doğrusal süzgeç + mipmap.
	# HD paketinde maske de 2 kat (CanvasTexture normal yuvası atlasla aynı boyda olmalı, yoksa karolar kayar)
	ct.normal_texture = _same_size(Data.tex_full("res://assets/tiles/%s" % String(_tmeta().get("mask", ""))), ct.diffuse_texture)
	ct.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	return ct


func _same_size(t: Texture2D, ref: Texture2D) -> Texture2D:
	## Karo atlasıyla aynı TileSet'te kullanılan yardımcı doku (maske, ışıma) atlasla aynı boyda olmalı. Pakette HD
	## karşılığı yoksa (temel doku sonradan değişti) çalışma anında atlas boyuna büyütülür (yumuşak veri dokuları;
	## çizim ayrıntısı yok).
	if t == null or ref == null or t.get_size() == ref.get_size():
		return t
	var img: Image = t.get_image()
	if img == null or img.is_empty():
		return t
	if img.is_compressed():
		img.decompress()
	img.resize(int(ref.get_width()), int(ref.get_height()), Image.INTERPOLATE_BILINEAR)
	img.generate_mipmaps()
	return ImageTexture.create_from_image(img)


func _tile_id() -> String:
	## Karo/toprak dosya kimliği: "<biyom>_v2" (Data.stil_id)
	return Data.stil_id(String(biome.get("id", "otuken")), "res://assets/tiles/%s.png")


func _make_tileset() -> TileSet:
	var tpath := "res://assets/tiles/%s.png" % _tile_id()
	_tile_pack = Data.pack_scale(tpath)
	var ac := _tile_px()
	var ts := TileSet.new()
	ts.tile_size = Vector2i(ac, ac)
	ts.add_physics_layer()
	ts.set_physics_layer_collision_layer(0, Game.LAYER_WORLD)
	ts.set_physics_layer_collision_mask(0, 0)
	ts.add_physics_layer()
	ts.set_physics_layer_collision_layer(1, Game.LAYER_PLATFORM)
	ts.set_physics_layer_collision_mask(1, 0)
	# Işık engelleyici katmanı: ay (ve büyük çıralar) arazi gölgesi düşürsün. Engelleyiciler kapalı kare
	# değil, yalnızca ışığa SIRTI dönük yüzlerdeki açık doğru parçalarıdır (bkz. _tile): böylece zemin
	# kesitindeki toprak ay ışığını almaya devam eder, ama yar dipleri, çıkıntı altları ve mağaralar gölgelenir.
	ts.add_occlusion_layer()
	ts.set_occlusion_layer_light_mask(0, 1)
	ts.set_occlusion_layer_sdf_collision(0, false)
	var rot := deg_to_rad(float(art.get("sun_rot", 40)))
	_shadow_dir = Vector2(-sin(rot), cos(rot))
	var src := TileSetAtlasSource.new()
	var bid: String = _tile_id()
	src.texture = _atlas_tex("res://assets/tiles/%s.png" % bid)
	src.texture_region_size = Vector2i(ac, ac)
	ts.add_source(src, 0)
	var meta := _tmeta()
	var cols := int(meta["cols"])
	# çarpışma çokgenleri karo yerelinde (hücre pikseli); katman ölçeğiyle tam olarak TS'ye iner
	var h := ac * 0.5
	var full := PackedVector2Array([Vector2(-h, -h), Vector2(h, -h), Vector2(h, h), Vector2(-h, h)])
	var top := PackedVector2Array([Vector2(-h, -h), Vector2(h, -h), Vector2(h, -h * 0.5), Vector2(-h, -h * 0.5)])
	for r in int(meta["ground_rows"]):
		for c in cols:
			_tile(src, Vector2i(c, r), 0, full, false)
	var orow := int(meta["overlay_row"])
	for c in int(meta["grass_cols"]) + (meta["ceiling_cols"] as Array).size():
		_tile(src, Vector2i(c, orow), -1, full, false)
	var prow := int(meta["platform_row"])
	for c in 6:
		_tile(src, Vector2i(c, prow), 1, top, true)
	return ts


func _tile(src: TileSetAtlasSource, coords: Vector2i, phys: int, poly: PackedVector2Array, one_way: bool) -> void:
	src.create_tile(coords)
	if phys < 0:
		return
	var td := src.get_tile_data(coords, 0)
	td.add_collision_polygon(phys)
	td.set_collision_polygon_points(phys, 0, poly)
	if one_way:
		td.set_collision_polygon_one_way(phys, 0, true)
		# tek yönlü pay: katman ölçeğinden sonra da 1 dünya pikseli kalsın
		td.set_collision_polygon_one_way_margin(phys, 0, float(_tile_px()) / TS)
	_tile_occluders(td, coords, one_way)


func _tile_occluders(td: TileData, coords: Vector2i, one_way: bool) -> void:
	## Karonun açık yüzlerinden ay ışığına sırtı dönük olanlara (n·d > 0) açık doğru parçası engelleyici.
	## Havadaki bir noktadan aya giden ışın katıya hep böyle bir yüzden girer; dolayısıyla hava gölgeleri
	## tamdır. Işığa bakan yüzler (zemin üstü, aydınlık yamaç) engellemez: altlarındaki toprak kesiti
	## üstündeki zeminle aynı ışığı alır (kesit geleneği). Zemin karosunda açık yüzler atlas sütunundan
	## (m maskesi: 1 üst, 2 sağ, 4 alt, 8 sol hava), platformda ince levhanın altı ve uç yüzleri.
	var h := _tile_px() * 0.5
	var d := _shadow_dir
	var segs: Array = []
	if one_way:
		var kind := coords.x % 3  # 0 sol uç, 1 orta, 2 sağ uç
		var bot := -h * 0.5
		if d.y > 0.05:
			segs.append([Vector2(-h, bot), Vector2(h, bot)])
		elif d.y < -0.05:
			segs.append([Vector2(-h, -h), Vector2(h, -h)])
		if kind == 0 and d.x < -0.05:
			segs.append([Vector2(-h, -h), Vector2(-h, bot)])
		if kind == 2 and d.x > 0.05:
			segs.append([Vector2(h, -h), Vector2(h, bot)])
	else:
		var m := coords.x
		if (m & 1) and d.y < -0.05:
			segs.append([Vector2(-h, -h), Vector2(h, -h)])
		if (m & 4) and d.y > 0.05:
			segs.append([Vector2(-h, h), Vector2(h, h)])
		if (m & 8) and d.x < -0.05:
			segs.append([Vector2(-h, -h), Vector2(-h, h)])
		if (m & 2) and d.x > 0.05:
			segs.append([Vector2(h, -h), Vector2(h, h)])
	if segs.is_empty():
		return
	td.set_occluder_polygons_count(0, segs.size())
	for i in segs.size():
		var occ := OccluderPolygon2D.new()
		occ.closed = false
		occ.cull_mode = OccluderPolygon2D.CULL_DISABLED
		occ.polygon = PackedVector2Array([segs[i][0], segs[i][1]])
		td.set_occluder_polygon(0, i, occ)


func _depth_texture() -> ImageTexture:
	## Her karo için havaya uzaklık (0..1): yüzeyden uzaklaştıkça toprak yumuşakça kararır.
	var dist := PackedInt32Array()
	dist.resize(W * H)
	dist.fill(99)
	var frontier: Array = []
	for y in H:
		for x in W:
			if cell(x, y) != 1:
				dist[idx(x, y)] = 0
				frontier.append(Vector2i(x, y))
	var steps := 0
	while not frontier.is_empty() and steps < 10:
		var nf: Array = []
		for p in frontier:
			var d0: int = dist[idx(p.x, p.y)]
			for o in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
				var q: Vector2i = p + o
				if q.x >= 0 and q.x < W and q.y >= 0 and q.y < H and dist[idx(q.x, q.y)] > d0 + 1:
					dist[idx(q.x, q.y)] = d0 + 1
					nf.append(q)
		frontier = nf
		steps += 1
	var img := Image.create(W, H, false, Image.FORMAT_L8)
	for y in H:
		for x in W:
			var v := clampf((float(dist[idx(x, y)]) - 1.0) / 5.0, 0.0, 1.0)
			img.set_pixel(x, y, Color(v, v, v))
	return ImageTexture.create_from_image(img)


func _top_depth_texture() -> ImageTexture:
	## v2 çayırı için: her katı karonun üstündeki kesintisiz katı karo sayısı (yalnızca dikey), 4 karoda 1.
	## Yüzey karosu 0: üstteki 2-3 karo otluk görünür, yar yüzleri ve derinlik toprak kalır.
	var img := Image.create(W, H, false, Image.FORMAT_L8)
	for x in W:
		var run := 0
		for y in H:
			if cell(x, y) == 1:
				img.set_pixel(x, y, Color(1, 1, 1) * clampf(run / 4.0, 0.0, 1.0))
				run += 1
			else:
				run = 0
				img.set_pixel(x, y, Color(0, 0, 0))
	return ImageTexture.create_from_image(img)


func _build_tiles() -> void:
	## Mürekkep zemini: sanat + kaplama maskesi atlası, dünya uzayı toprak (ground_ink.gdshader);
	## örtü katmanı (ot öbekleri, kökler) env_ink.gdshader.
	var ts := _make_tileset()
	var bid2: String = _tile_id()
	var gmat := ShaderMaterial.new()
	gmat.shader = load("res://shaders/ground_ink.gdshader")
	# HD paketi: toprak ve çayır dokuları gerçek (2 kat) boyutlarıyla; gölgelendirici dünya konumunu textureSize ile
	# böldüğü için yoğunluk aynı çarpanla büyür (aynı dünya alanı, 2 kat ayrıntı). İkisi aynı ölçekte olmalı (ortak yoğunluk).
	var soil_path := "res://assets/tiles/%s_soil.png" % bid2
	var mp := "res://assets/tiles/%s" % String(_tmeta().get("meadow", ""))
	var has_meadow := _tmeta().has("meadow") and ResourceLoader.exists(mp)
	var gk := Data.pack_scale(soil_path)
	if has_meadow and Data.pack_scale(mp) != gk:
		gk = 1
	gmat.set_shader_parameter("soil_tex", Data.tex_full(soil_path) if gk > 1 else load(soil_path))
	gmat.set_shader_parameter("soil_density", float(_tmeta().get("soil_density", 2.0)) * float(gk))
	var dc: Array = art.get("deep_color", [0.06, 0.06, 0.08])
	gmat.set_shader_parameter("deep_color", Color(dc[0], dc[1], dc[2]))
	gmat.set_shader_parameter("deep_amount", float(art.get("deep_amount", 0.8)))
	gmat.set_shader_parameter("depth_tex", _depth_texture())
	gmat.set_shader_parameter("map_size_px", Vector2(W * TS, H * TS))
	gmat.set_shader_parameter("moon_gain", float(art.get("ground_moon_gain", 0.6)))
	if has_meadow:
		gmat.set_shader_parameter("meadow_tex", Data.tex_full(mp) if gk > 1 else load(mp))
		gmat.set_shader_parameter("top_tex", _top_depth_texture())
	else:
		gmat.set_shader_parameter("meadow_on", 0.0)
	if art.has("meadow_depth"):
		gmat.set_shader_parameter("meadow_depth", float(art["meadow_depth"]))
	elif _tmeta().has("meadow_depth"):
		gmat.set_shader_parameter("meadow_depth", float(_tmeta()["meadow_depth"]))
	# ışıyan kaya damarları (Şahmeran kristal, Tamu lav): dünya uzayı _soil_e, nabız atar
	var sep := "res://assets/tiles/%s" % String(_tmeta().get("soil_e", ""))
	if _tmeta().has("soil_e") and ResourceLoader.exists(sep):
		gmat.set_shader_parameter("soil_e", load(sep))
		gmat.set_shader_parameter("emit_gain", float(art.get("soil_emit", 1.6)))
		var ep: Array = art.get("emit_pulse", [0.25, 1.2])
		gmat.set_shader_parameter("emit_pulse", Vector2(float(ep[0]), float(ep[1])))
	var tmat := ShaderMaterial.new()
	tmat.shader = load("res://shaders/env_ink.gdshader")
	tmat.set_shader_parameter("moon_gain", float(art.get("ground_moon_gain", 0.6)))
	if art.has("tuft_sway"):
		# örtü öbekleri rüzgârda salınır (bozkır): hücre boyu atlas hücresi
		tmat.set_shader_parameter("sway_px", float(art["tuft_sway"]))
		tmat.set_shader_parameter("cell_px", float(_tile_px()))
	_lay_tiles(ts, gmat, tmat)
	ground.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	overlay.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	if _tmeta().has("emit"):
		_lay_emit_tiles(ts)


func _lay_emit_tiles(ts: TileSet) -> void:
	## Stil v2 ışıma atlası (<biyom>_v2_e.png, yerleşim sanat atlasıyla aynı): yalnızca ışıması olan hücreler (meta
	## "emit_cells") zemin ve örtü katmanından kopyalanır; ADD + gölgesiz, ortam ışığından bağımsız parlar.
	var ep := "res://assets/tiles/%s" % String(_tmeta()["emit"])
	if not ResourceLoader.exists(ep):
		return
	var cells := {}
	for c in _tmeta().get("emit_cells", []):
		cells[Vector2i(int(c[0]), int(c[1]))] = true
	var ets := ts.duplicate(true) as TileSet
	var src := ets.get_source(0) as TileSetAtlasSource
	var art_tex: Texture2D = (ts.get_source(0) as TileSetAtlasSource).texture
	src.texture = _same_size(Data.tex_full(ep), art_tex)   # karo boyu atlasınkiyle aynı (HD paketinde 2 kat)
	var layer := TileMapLayer.new()
	layer.tile_set = ets
	layer.scale = ground.scale
	layer.collision_enabled = false
	layer.occlusion_enabled = false
	layer.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	var gm := CanvasItemMaterial.new()
	gm.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	gm.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	layer.material = gm
	var ek: Array = art.get("tile_emit", [1.3, 1.3, 1.3])
	layer.modulate = Color(float(ek[0]), float(ek[1]), float(ek[2]))
	layer.z_index = 6
	add_child(layer)
	for L in [ground, overlay]:
		for c in (L as TileMapLayer).get_used_cells():
			var ac: Vector2i = (L as TileMapLayer).get_cell_atlas_coords(c)
			if cells.has(ac):
				layer.set_cell(c, 0, ac)


func _lay_tiles(ts: TileSet, gmat: ShaderMaterial, tmat: ShaderMaterial) -> void:
	var art_scale := Vector2.ONE * (float(TS) / _tile_px())
	ground = TileMapLayer.new()
	ground.tile_set = ts
	ground.material = gmat
	ground.z_index = 0
	ground.scale = art_scale
	add_child(ground)
	overlay = TileMapLayer.new()
	overlay.tile_set = ts
	overlay.scale = art_scale
	overlay.material = tmat
	overlay.collision_enabled = false
	overlay.z_index = 5
	add_child(overlay)
	var meta := _tmeta()
	var prow := int(meta["platform_row"])
	var orow := int(meta["overlay_row"])
	var gcols := int(meta["grass_cols"])
	var ccols: Array = meta["ceiling_cols"]
	for y in H:
		for x in W:
			var c := cell(x, y)
			if c == 1:
				var m := 0
				if cell(x, y - 1) != 1:
					m |= 1
				if cell(x + 1, y) != 1:
					m |= 2
				if cell(x, y + 1) != 1:
					m |= 4
				if cell(x - 1, y) != 1:
					m |= 8
				ground.set_cell(Vector2i(x, y), 0, Vector2i(m, (x + y) % 3))
				if (m & 1) and y > 0 and cell(x, y - 1) == 0 and rng.randf() < 0.75:
					overlay.set_cell(Vector2i(x, y - 1), 0, Vector2i(rng.randi_range(0, gcols - 1), orow))
				if (m & 4) and y + 1 < H and cell(x, y + 1) == 0 and rng.randf() < 0.55:
					overlay.set_cell(Vector2i(x, y + 1), 0, Vector2i(int(ccols[rng.randi_range(0, ccols.size() - 1)]), orow))
			elif c == 2:
				var kind := 1
				if cell(x - 1, y) != 2:
					kind = 0
				elif cell(x + 1, y) != 2:
					kind = 2
				ground.set_cell(Vector2i(x, y), 0, Vector2i(kind + 3 * rng.randi_range(0, 1), prow))


# ------------------------------------------------------------------ dünya sorguları
func ground_y_below(pos: Vector2, max_px := 80.0) -> float:
	## pos'un altındaki ilk zemin üst sınırı (piksel); yoksa -1
	var y := pos.y
	while y < pos.y + max_px:
		if solid_at(Vector2(pos.x, y)):
			return floorf(y / TS) * TS
		y += 4.0
	return -1.0


func solid_at(p: Vector2) -> bool:
	return cell(int(floor(p.x / TS)), int(floor(p.y / TS))) == 1


func moon_occluded(p: Vector2, max_d := 1400.0) -> bool:
	## p'den aya giden ışın katı bir karoya çarpıyor mu (çıkıntı altı, yar dibi, mağara). Haritanın üstü
	## ve yanları açık gök sayılır. Adım yarım karo: ince platformlar (tek yönlü) gölge düşürmez.
	var dir := -_shadow_dir
	var step := float(TS) * 0.5
	var n := int(max_d / step)
	for i in range(1, n):
		var q := p + dir * (step * float(i))
		var cx := int(floor(q.x / TS))
		var cy := int(floor(q.y / TS))
		if cy < 0 or cx < 0 or cx >= W:
			return false
		if cy < H and grid[idx(cx, cy)] == 1:
			return true
	return false


func ground_at(p: Vector2) -> bool:
	return cell(int(floor(p.x / TS)), int(floor(p.y / TS))) != 0


func los(a: Vector2, b: Vector2) -> bool:
	var n := int(a.distance_to(b) / 10.0) + 1
	for i in range(1, n):
		if solid_at(a.lerp(b, float(i) / n)):
			return false
	return true


func surface_y(x_tile: int, y_ref := -1) -> int:
	## Yürünen zemin: tabanın (heights: ana yol odasının tabanı) 8 karo altından yukarı tarayıp ilk "üstü hava, kendisi
	## katı" karo. v32: y_ref (karo) verilirse o satırdan aşağı ilk zemin (çok katlı odalarda aktörün kendi katı);
	## aşağıda yoksa yukarı aranır.
	var xt := clampi(x_tile, 0, W - 1)
	if y_ref >= 0:
		for y in range(maxi(1, y_ref), H):
			if cell(xt, y) != 0 and cell(xt, y - 1) == 0:
				return y
		for y in range(mini(H - 1, y_ref), 1, -1):
			if cell(xt, y) != 0 and cell(xt, y - 1) == 0:
				return y
	var y := mini(H - 1, int(heights[xt]) + 8)
	while y > 1:
		if cell(xt, y) != 0 and cell(xt, y - 1) == 0:
			return y
		y -= 1
	return H - 1


func floor_y_px(p: Vector2) -> float:
	## v32: dünya noktasının altındaki (aynı kattaki) zeminin üst kenarı (px)
	return float(surface_y(int(floor(p.x / TS)), int(floor(p.y / TS)) - 1) * TS)


# ------------------------------------------------------------------ ışık ve atmosfer
func light_tex() -> GradientTexture2D:
	if _light_tex == null:
		_light_tex = GradientTexture2D.new()
		_light_tex.width = 128
		_light_tex.height = 128
		_light_tex.fill = GradientTexture2D.FILL_RADIAL
		_light_tex.fill_from = Vector2(0.5, 0.5)
		_light_tex.fill_to = Vector2(1.0, 0.5)
		var g := Gradient.new()
		# v40: ters kare benzeri yumuşak düşüş (eski 0,45'te tek kırılma: sert halkalı ışık); çekirdek sıcak, etek uzun
		g.set_color(0, Color(1, 1, 1, 1))
		g.set_color(1, Color(1, 1, 1, 0))
		g.add_point(0.22, Color(1, 1, 1, 0.66))
		g.add_point(0.48, Color(1, 1, 1, 0.3))
		g.add_point(0.74, Color(1, 1, 1, 0.09))
		_light_tex.gradient = g
	return _light_tex


var _isik_say := 0  # v38: kurulan sabit süs ışığı sayısı (Ayarlar.isik_siniri)


func add_light(pos: Vector2, col: Color, radius: float, energy := 1.0, parent: Node = null, shadows := false) -> PointLight2D:
	## shadows: arazi gölgesi düşürür (her gölgeli nokta ışığı kadrajdaki engelleyicileri 4 yöne çizer;
	## yalnızca büyük, sabit ışıklar için: süs çıraları, ocak, Kut Kapısı). Büyük sabit süs ışıkları
	## (decor_root altı, yarıçap >= 200) kendiliğinden gölgeli olur.
	var l := PointLight2D.new()
	# v38 Ayarlar > Işık ve parlama: sabit süs ışıkları (decor_root altı) sınırı aşınca kapalı kurulur (düğüm yine
	# döner; çağıran enerjisini / rengini değiştirebilir). Gölge yalnızca "Tam"da.
	var cap := Ayarlar.isik_siniri()
	if cap > 0 and parent == decor_root and decor_root != null:
		_isik_say += 1
		if _isik_say > cap:
			l.enabled = false
	l.texture = light_tex()
	l.texture_scale = radius / 64.0
	l.color = col
	l.energy = energy
	l.height = 26.0
	l.position = pos
	if (shadows or (parent == decor_root and decor_root != null and radius >= 200.0)) and Ayarlar.isik_golge() and not _golgesiz:
		l.shadow_enabled = true
		# v40: yumuşak gölge (PCF5): keskin kenarlı karo gölgeleri mürekkep yıkamasına uyar; yoğunluk ve renk biyomdan
		# (art "shadow_col" / "shadow_density": gölge siyah değil, ortamın koyu tonu)
		if _sertgolge:
			l.shadow_filter = Light2D.SHADOW_FILTER_NONE
		else:
			l.shadow_filter = Light2D.SHADOW_FILTER_PCF5
			l.shadow_filter_smooth = 2.6
		var sc: Array = art.get("shadow_col", [0.05, 0.04, 0.08])
		l.shadow_color = Color(sc[0], sc[1], sc[2], float(art.get("shadow_density", 0.78)))
		l.shadow_item_cull_mask = 1
	(parent if parent else self).add_child(l)
	return l


static var _golgesiz := OS.get_cmdline_user_args().has("--golgesiz")   # v40 ölçüm: nokta ışığı gölgeleri kapalı
static var _sertgolge := OS.get_cmdline_user_args().has("--sertgolge")   # v40 ölçüm: gölge süzgeci yok (v38 gibi keskin)


func titrek(l: PointLight2D, kind := "mesale") -> PointLight2D:
	## v40: ışığa doğal titreme ekler (IsikTitrek); ışığı geri verir (zincirleme kullanım)
	IsikTitrek.attach(l, kind)
	return l


func _build_lighting() -> void:
	# Kararan Ötüken: soğuk, loş ortam ışığı; "güneş" yerine ay. Sıcak ışık yalnızca
	# ocaklardan, çıralardan ve Bengü'nün Kut'undan gelir.
	var amb: Array = art.get("ambient", [0.40, 0.44, 0.62])
	var sun_c: Array = art.get("sun", [0.62, 0.72, 1.0])
	var cm := CanvasModulate.new()
	# Ortam tabanı bir tık düşer, fark ayın gölge düşüren katkısına taşınır: aydınlık/gölge ayrımı okunur,
	# toplam pozlama yaklaşık aynı kalır (gölgedeki düşman ortam ışığıyla görünür).
	var amb_k := float(art.get("ambient_k", 0.8))
	cm.color = Color(amb[0] * amb_k, amb[1] * amb_k, amb[2] * amb_k)
	add_child(cm)
	moon = DirectionalLight2D.new()
	moon.color = Color(sun_c[0], sun_c[1], sun_c[2])
	moon.energy = float(art.get("sun_energy", 0.38)) * float(art.get("sun_k", 2.5))
	moon.height = float(art.get("sun_height", 0.55))
	moon.rotation_degrees = float(art.get("sun_rot", 40))
	# Arazi gölgeleri: karo engelleyicileri (bkz. _tile_occluders) yar diplerini, çıkıntı altlarını ve
	# mağaraları gölgeler. Gölge rengi siyah değil, ayın soğuk renginin kısık hâli: gölgedeki düşman
	# ortam ışığı (CanvasModulate) + bu kalıntı ile okunur kalır. Süzgeç yok: piksel sanatına uygun keskin kenar.
	# Motor gölgesi KAPALI: yan kesitte basamakların gölgesi toprağın içine uzun çapraz şeritler
	# düşürüyordu ve Godot'da gölgeyi alan öğe seçilemiyor (shadow_item_cull_mask engelleyicileri seçer,
	# TileMapLayer light_mask'i çizime aktarmıyor). Aktörlerin ay gölgesi moon_occluded() ile hesaplanır
	# (GroundShadow → toon_light "moon_shade"). Karo engelleyicileri büyük süs ışıklarının gölgesi için kalır.
	moon.shadow_enabled = false
	var sh := float(art.get("shadow", 0.72))  # gölgede ay ışığının ne kadarı gider (0..1)
	moon_shadow = sh
	# Not: gölge rengi motor tarafında ışık renginden çok daha büyük bir ölçekle toplanır; siyaha yakın
	# soğuk bir değer bile belirgin kalıntı verir. sh: 1 = ay ışığı gölgede tamamen gider.
	moon.shadow_color = Color(0.012 * (1.0 - sh) / 0.28, 0.014 * (1.0 - sh) / 0.28, 0.024 * (1.0 - sh) / 0.28, 1.0)
	moon.shadow_filter = Light2D.SHADOW_FILTER_NONE
	moon.shadow_item_cull_mask = 1
	moon.max_distance = 2400.0
	add_child(moon)
	var env := Environment.new()
	env.background_mode = Environment.BG_CANVAS
	env.glow_enabled = true
	# Parlama biyoma göre: gündüz biyomlarında eşik yüksek ve şiddet düşük, yoksa açık toprak/gök
	# yumuşak ışık karışımıyla patlar (göz yakan beyaz alanlar).
	env.glow_intensity = float(art.get("glow", 0.9))
	env.glow_strength = 1.0
	env.glow_bloom = float(art.get("glow_bloom", 0.04))
	env.glow_hdr_threshold = float(art.get("glow_threshold", 0.9))
	env.glow_blend_mode = Environment.GLOW_BLEND_MODE_SOFTLIGHT
	# v40: parlama katmanları (set_glow_level sırası 0..6 = glow_levels/1..7): dar (2.) ışık kaynaklarının çekirdeğini
	# yarım güçle, orta (3.) alev / kristal haleyi, geniş (5.) sisli ortamın yumuşak hâlesini verir (Godot varsayılanı
	# 3. + 5.). Yumuşak ışık karışımı açık dokuları yıkamaz.
	# v38 Ayarlar > Işık ve parlama: Az = parlama kapalı; Hafif = yalnızca geniş (5.) seviye, şiddet dengelenir
	var seviye := {1: 0.5, 2: 1.0, 4: 1.0}
	if Ayarlar.parlama() == 1:
		seviye = {4: 1.0}
		env.glow_intensity *= 0.85
	for i in range(0, 7):
		env.set_glow_level(i, float(seviye.get(i, 0.0)))
	if Ayarlar.parlama() == 0:
		env.glow_enabled = false
	env.adjustment_enabled = true
	env.adjustment_brightness = float(art.get("brightness", 1.0))
	env.adjustment_saturation = float(art.get("saturation", 0.96))
	env.adjustment_contrast = float(art.get("contrast", 1.08))
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)
	# Toprak derinlik kararması (ground.gdshader deep_amount/deep_color): yüzeyden içeri doğru ortam
	# kapanması. Biyom art'ı ezebilir; zemin _build_tiles'ta bu fonksiyondan önce kurulur.
	if ground and ground.material is ShaderMaterial:
		var gm := ground.material as ShaderMaterial
		if art.has("deep_amount"):
			gm.set_shader_parameter("deep_amount", float(art["deep_amount"]))


func _build_background() -> void:
	var bg := ParallaxBG.new()
	bg.level = self
	var names: Array = art.get("bg", [])
	var fxs: Array = art.get("bg_fx", [])
	if not names.is_empty():
		var layers: Array = []
		for i in names.size():
			var f: Array = fxs[i] if i < fxs.size() else [0.3, 0.1, 0.0]
			var kinds: Array = art.get("bg_kind", [])
			layers.append(["res://assets/bg/%s.png" % Data.stil_id(String(names[i]), "res://assets/bg/%s.png"), float(f[0]), float(f[1]), float(f[2]), kinds[i] if i < kinds.size() else "", float(f[3]) if f.size() > 3 else 0.0])
		bg.layers = layers
	add_child(bg)


func _build_particles() -> void:
	var kind: String = art.get("particles", "ruh")
	FX.dust_col = {"otuken": Color(0.55, 0.5, 0.42, 0.55), "bozkir": Color(0.8, 0.7, 0.48, 0.55), "sahmeran": Color(0.46, 0.56, 0.46, 0.5),
		"kaf": Color(0.92, 0.95, 1.0, 0.65), "tamu": Color(0.36, 0.28, 0.28, 0.6), "cini_saray": Color(0.7, 0.65, 0.72, 0.5)}.get(String(biome.get("id", "")), Color(0.62, 0.58, 0.6, 0.55))
	# havada süzülen zerreler: biyoma göre ruh kıvılcımı / polen / spor / kar / kor
	var pollen := CPUParticles2D.new()
	pollen.amount = 30
	pollen.lifetime = 7.0
	pollen.preprocess = 7.0
	pollen.texture = FX.dot_tex()
	pollen.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
	pollen.emission_rect_extents = Vector2(380, 220)
	pollen.direction = Vector2(1, -0.3)
	pollen.spread = 60.0
	pollen.initial_velocity_min = 4.0
	pollen.initial_velocity_max = 14.0
	pollen.gravity = Vector2(0, -3)
	pollen.scale_amount_min = 0.08
	pollen.scale_amount_max = 0.18
	pollen.color = Color(0.55, 1.15, 1.05, 0.8)
	match kind:
		"polen":
			pollen.color = Color(1.3, 1.1, 0.6, 0.8)
			pollen.amount = 40
		"spor":
			pollen.color = Color(0.6, 1.3, 0.8, 0.8)
			pollen.amount = 44
			pollen.gravity = Vector2(0, 4)
		"kar":
			pollen.color = Color(1.0, 1.0, 1.0, 0.95)
			pollen.amount = 90
			pollen.direction = Vector2(-0.3, 1)
			pollen.gravity = Vector2(-8, 22)
			pollen.initial_velocity_min = 10.0
			pollen.initial_velocity_max = 30.0
			pollen.scale_amount_min = 0.1
			pollen.scale_amount_max = 0.2
		"kor":
			pollen.color = Color(1.4, 0.7, 0.25, 0.9)
			pollen.amount = 60
			pollen.direction = Vector2(0.2, -1)
			pollen.gravity = Vector2(0, -14)
			pollen.initial_velocity_min = 8.0
			pollen.initial_velocity_max = 26.0
			pollen.scale_amount_min = 0.06
			pollen.scale_amount_max = 0.16
	pollen.local_coords = false
	pollen.z_index = 40
	var am := CanvasItemMaterial.new()
	am.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	am.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	pollen.material = am
	camera.add_child(pollen)
	var leaves := CPUParticles2D.new()
	leaves.amount = 22
	leaves.lifetime = 9.0
	leaves.preprocess = 9.0
	leaves.texture = InkDraw.particle("yaprak")  # fırça yaprak
	leaves.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
	leaves.emission_rect_extents = Vector2(380, 10)
	leaves.position = Vector2(0, -220)
	leaves.direction = Vector2(1, 1)
	leaves.spread = 30.0
	leaves.initial_velocity_min = 10.0
	leaves.initial_velocity_max = 25.0
	leaves.gravity = Vector2(6, 18)
	leaves.angular_velocity_min = -180.0
	leaves.angular_velocity_max = 180.0
	leaves.scale_amount_min = 1.0
	leaves.scale_amount_max = 1.6
	var cg := Gradient.new()
	# kurumuş yapraklar
	cg.set_color(0, Color(0.36, 0.24, 0.13))
	cg.set_color(1, Color(0.26, 0.15, 0.11))
	cg.add_point(0.33, Color(0.44, 0.33, 0.14))
	cg.add_point(0.66, Color(0.2, 0.26, 0.15))
	leaves.color_initial_ramp = cg
	leaves.local_coords = false
	leaves.z_index = 40
	if art.has("leaf_tex"):
		# v2: referanstaki gibi koyu siluet yapraklar (dönerek süzülür), biraz daha çok ve iri
		leaves.texture = load(String(art["leaf_tex"]))
		leaves.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
		leaves.amount = int(art.get("leaf_amount", 30))
		leaves.scale_amount_min = 0.15
		leaves.scale_amount_max = 0.3
		leaves.angle_min = 0.0
		leaves.angle_max = 360.0
		leaves.emission_rect_extents = Vector2(520, 10)
		leaves.position = Vector2(80, -300)
		leaves.direction = Vector2(-0.5, 1)
		leaves.gravity = Vector2(-4, 14)
		var lg := Gradient.new()
		lg.set_color(0, Color(0.13, 0.07, 0.12))
		lg.set_color(1, Color(0.16, 0.2, 0.15))
		leaves.color_initial_ramp = lg
		var lm := CanvasItemMaterial.new()
		lm.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
		leaves.material = lm
		pollen.amount = int(art.get("pollen_amount", pollen.amount))
		if art.has("leaf_ramp"):
			# biyoma özgü parçacık (bozkır: rüzgârla yatay savrulan kuru ot kırıntısı)
			var rr: Array = art["leaf_ramp"]
			lg.set_color(0, Color(String(rr[0])))
			lg.set_color(1, Color(String(rr[1])))
			var ld: Array = art.get("leaf_dir", [-0.5, 1.0])
			var lgv: Array = art.get("leaf_grav", [-4.0, 14.0])
			var lv: Array = art.get("leaf_vel", [10.0, 25.0])
			leaves.direction = Vector2(float(ld[0]), float(ld[1]))
			leaves.gravity = Vector2(float(lgv[0]), float(lgv[1]))
			leaves.initial_velocity_min = float(lv[0])
			leaves.initial_velocity_max = float(lv[1])
			leaves.emission_rect_extents = Vector2(520, 220)
			leaves.position = Vector2(-560, -60)
	match kind:
		"polen":
			if not art.has("leaf_ramp"):
				leaves.amount = 10  # bozkırda birkaç kuru ot parçası
		"kar":
			leaves.amount = 1
			leaves.visible = false
		"spor":
			leaves.amount = 1
			leaves.visible = false
		"kor":
			# kül: ağır, gri, düşen
			var ag := Gradient.new()
			ag.set_color(0, Color(0.5, 0.45, 0.45))
			ag.set_color(1, Color(0.25, 0.2, 0.2))
			leaves.color_initial_ramp = ag
			leaves.amount = 30
			leaves.gravity = Vector2(2, 10)
	if leaves.visible:
		camera.add_child(leaves)
	else:
		leaves.free()
	# v40 ortam cilası: temas gölgeleri, hava canlıları, rüzgâr esintisi, bakış anıtları (scripts/world/OrtamCila.gd)
	OrtamCila.kur(self, leaves if is_instance_valid(leaves) else null)
	if art.has("drip_tex"):
		# v2 mağara: tavandan düşen su damlaları (düz aşağı, hızlanarak; ışıklı ince damla)
		var dr := CPUParticles2D.new()
		dr.amount = int(art.get("drip_amount", 10))
		dr.lifetime = 1.4
		dr.preprocess = 1.4
		dr.texture = load(String(art["drip_tex"]))
		dr.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
		dr.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
		dr.emission_rect_extents = Vector2(520, 10)
		dr.position = Vector2(0, -260)
		dr.direction = Vector2(0, 1)
		dr.spread = 0.0
		dr.initial_velocity_min = 10.0
		dr.initial_velocity_max = 40.0
		dr.gravity = Vector2(0, 420)
		dr.scale_amount_min = 0.22
		dr.scale_amount_max = 0.36
		var dc: Array = art.get("drip_col", [0.6, 1.0, 0.9, 0.7])
		dr.color = Color(dc[0], dc[1], dc[2], dc[3])
		dr.local_coords = false
		dr.z_index = 40
		var dm := CanvasItemMaterial.new()
		dm.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
		dm.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
		dr.material = dm
		camera.add_child(dr)


func _build_overlay_fx() -> void:
	var cl := CanvasLayer.new()
	cl.layer = 5
	add_child(cl)
	var vig := ColorRect.new()
	vig.set_anchors_preset(Control.PRESET_FULL_RECT)
	vig.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var sm := ShaderMaterial.new()
	sm.shader = load("res://shaders/vignette.gdshader")
	if not OS.get_cmdline_user_args().has("--derecesiz") and Ayarlar.parlama() > 0:
		# v2: sahneyi okuyan renk derecelendirme + vinyet (aynı "hurt" nabzı); test: --derecesiz kapatır
		sm.shader = load("res://shaders/grade_v2.gdshader")
		var gr: Dictionary = art.get("grade", {})
		for k in gr:
			var v = gr[k]
			if v is Array and (v as Array).size() == 3:
				sm.set_shader_parameter(k, Vector3(v[0], v[1], v[2]))
			elif v is Array and (v as Array).size() == 4:
				sm.set_shader_parameter(k, Color(v[0], v[1], v[2], v[3]))
			else:
				sm.set_shader_parameter(k, float(v))
		if art.has("heat_haze"):
			sm.set_shader_parameter("heat", float(art["heat_haze"]))
		# v42: dönen örgüler ufku ısıtır; tan söktükten sonra yurt tam sabah
		sm.set_shader_parameter("safak", 1.5 if hub and Hikaye.safak() else Hikaye.safak_k())
	vig.material = sm
	vig_mat = sm
	cl.add_child(vig)
	_build_huzme()
	red_rect = ColorRect.new()
	red_rect.set_anchors_preset(Control.PRESET_FULL_RECT)
	red_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	red_rect.color = Color(1, 0.1, 0.1, 0.0)
	red_rect.visible = false  # v38: saydamken çizilmez (tam ekran boş dörtgen piksel doldurur)
	cl.add_child(red_rect)
	if art.has("fg"):
		var fg := ForegroundV2.new()
		fg.spec = art["fg"]
		fg.level = self
		add_child(fg)


var huzme_mat: ShaderMaterial   # v40 ekran uzayı ışık hüzmesi geçişi (yalnızca Işık ve parlama Tam)
var _mist_y := 0.68


func _build_huzme() -> void:
	## v40: hacimli ışık hissi veren tam ekran toplamalı geçiş (shaders/isik_huzme.gdshader; biyom art "huzme").
	## Dünyanın üstünde (katman 2), vinyet / derecelendirmenin (5) altında. Az / Hafif düzeylerde ve --derecesiz ile yok.
	if not art.has("huzme") or Ayarlar.parlama() < 2 or OS.get_cmdline_user_args().has("--derecesiz") or OS.get_cmdline_user_args().has("--huzmesiz"):
		return
	var H: Dictionary = art["huzme"]
	if float(H.get("intensity", 0.0)) <= 0.0:
		return
	var cl := CanvasLayer.new()
	cl.layer = 2
	add_child(cl)
	# Hüzme çeyrek çözünürlükte ayrı bir görüntü alanına çizilir (480x270, HDR; mantıksal 960x540'ın yarısı: 1080p'de
	# 16 kat az piksel) ve toplamalı karışımla ekrana gerilir: hüzme zaten yumuşak, fark görünmez; tam ekran geçiş UHD 750'de
	# ~2,5 ms'ydi (v40 ölçümü), bu yolla < 0,5 ms.
	var sv := SubViewport.new()
	sv.size = Vector2i(480, 270)
	sv.transparent_bg = true
	sv.disable_3d = true
	sv.use_hdr_2d = true
	sv.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	cl.add_child(sv)
	var r := ColorRect.new()
	r.position = Vector2.ZERO
	r.size = Vector2(480, 270)
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var sm := ShaderMaterial.new()
	sm.shader = load("res://shaders/isik_huzme.gdshader")
	for k in H:
		var v = H[k]
		if v is Array and (v as Array).size() >= 3:
			sm.set_shader_parameter(k, Color(v[0], v[1], v[2], 1.0))
		else:
			sm.set_shader_parameter(k, float(v))
	var vs := get_viewport().get_visible_rect().size
	sm.set_shader_parameter("aspect", vs.x / maxf(1.0, vs.y))
	r.material = sm
	sv.add_child(r)
	var tr := TextureRect.new()
	tr.texture = sv.get_texture()
	tr.set_anchors_preset(Control.PRESET_FULL_RECT)
	tr.stretch_mode = TextureRect.STRETCH_SCALE
	tr.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	tr.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var am := CanvasItemMaterial.new()
	am.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	am.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	tr.material = am
	cl.add_child(tr)
	huzme_mat = sm


func _isik_tick() -> void:
	## v40: her kare — sis bandı oyuncunun ayak çizgisinin hemen altında (ekran oranı; kamera yükselince sis aşağı
	## kayar: yerin pusu), hüzmeler kamera ile hafifçe kayar (ortama bağlı hissi)
	if camera == null or player == null:
		return
	var vp := get_viewport().get_visible_rect().size
	if vig_mat != null and vig_mat.shader != null and String(vig_mat.shader.resource_path).ends_with("grade_v2.gdshader"):
		var sy: float = player.get_global_transform_with_canvas().origin.y / maxf(1.0, vp.y)
		var want := clampf(sy + 0.06, 0.4, 1.1)
		_mist_y = lerpf(_mist_y, want, 0.08)
		vig_mat.set_shader_parameter("mist_y", _mist_y)
	if huzme_mat != null:
		huzme_mat.set_shader_parameter("scroll", camera.get_screen_center_position().x * Game.base_zoom / maxf(1.0, vp.x) * 0.12)


func flash_red() -> void:
	## Hasar: kenarlardan kısa kırmızı vinyet nabzı (eskiden tüm ekran düz kırmızı boyanıyordu; karanlık
	## biyomlarda sahneyi kapatıyordu). Vuruş duraklaması/ağır çekim uzatmaz.
	## v40: aynı nabızda kısa renk sapması (ca: mercek ayrışması, yalnızca 0,18 sn; Sarsıntı ve flaş ile ölçeklenir)
	if vig_mat == null:
		return
	vig_mat.set_shader_parameter("hurt", 0.9 * maxf(0.4, Game.fx_scale))
	var tw := create_tween()
	tw.set_ignore_time_scale(true)
	tw.tween_method(func(v: float) -> void: vig_mat.set_shader_parameter("hurt", v), 0.9 * maxf(0.4, Game.fx_scale), 0.0, 0.35)
	if Game.fx_scale > 0.05:
		var tw2 := create_tween()
		tw2.set_ignore_time_scale(true)
		tw2.tween_method(func(v: float) -> void: vig_mat.set_shader_parameter("ca", v), 1.6 * Game.fx_scale, 0.0, 0.18).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)


# ------------------------------------------------------------------ süsler
var _decor_v2_meta: Dictionary = {}
var _decor_v2_tex: Dictionary = {}


func _decor_v2(dname: String) -> Dictionary:
	## Mürekkep süsü: assets/decor/<ad>_v2.png (+ _e ışıma), decor_v2.json (boyut/köken doku pikseli,
	## "texel" = dünya birimi başına doku pikseli). Yoksa boş sözlük (süs konmaz).
	if _decor_v2_meta.is_empty():
		_decor_v2_meta = Data.load_json("res://assets/decor/decor_v2.json") if FileAccess.file_exists("res://assets/decor/decor_v2.json") else {"_": {}}
		# ortak mürekkep süsleri (yurt, sunak, totem, kapı...: tools/artgen/export_sus.py) ayrı dosyada
		if FileAccess.file_exists("res://assets/decor/sus_v2.json"):
			var sus: Dictionary = Data.load_json("res://assets/decor/sus_v2.json")
			for k in sus:
				if not _decor_v2_meta.has(k):
					_decor_v2_meta[k] = sus[k]
		# biyoma özgü süsler ayrı dosyada (tools/artgen/<biyom>_ink_decor.py): ortak tabloya eklenir
		var bjp := "res://assets/decor/decor_v2_%s.json" % String(biome.get("id", ""))
		if FileAccess.file_exists(bjp):
			var bm: Dictionary = Data.load_json(bjp)
			for k in bm:
				_decor_v2_meta[k] = bm[k]
	var key := dname + "_v2"
	var bkey := "%s_%s_v2" % [dname, String(biome.get("id", ""))]
	if _decor_v2_meta.has(bkey):
		key = bkey
	if not _decor_v2_meta.has(key):
		return {}
	if not _decor_v2_tex.has(key):
		var d: Dictionary = (_decor_v2_meta[key] as Dictionary).duplicate()
		d["tex"] = Data.tex("res://assets/decor/%s.png" % key)
		var gp := "res://assets/decor/%s_e.png" % key
		d["glow_tex"] = load(gp) if ResourceLoader.exists(gp) else null
		_decor_v2_tex[key] = d
	return _decor_v2_tex[key]


func _decor_ink(d: Dictionary, dname: String, tile_x: int, tile_y_surface: int, z: int, glow_light: bool) -> Sprite2D:
	if bezirgan_alani(tile_x, 3):
		return null   # v24: tüccarın tezgâhı
	var s := Sprite2D.new()
	s.texture = d["tex"]
	s.centered = false
	var k := 1.0 / float(d.get("texel", 2.0))
	s.scale = Vector2(k, k)
	s.offset = Vector2(-float(d["origin"][0]), -float(d["origin"][1]))
	s.position = Vector2(tile_x * TS + TS / 2.0 + rng.randf_range(-4, 4), tile_y_surface * TS + 2)
	s.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	var m := ShaderMaterial.new()
	m.shader = load("res://shaders/env_ink.gdshader")
	m.set_shader_parameter("moon_gain", float(art.get("ground_moon_gain", 0.6)))
	if not dname.begins_with("cira"):
		var dt: Array = art.get("decor_tint", [1.0, 1.0, 1.0])
		m.set_shader_parameter("tint", Color(dt[0], dt[1], dt[2]))
	s.material = m
	s.z_index = z
	# yönlü ışıkla çizilmiş biyom süsleri ("noflip") aynalanmaz; rng çağrısı yine yapılır (dizi değişmesin)
	if rng.randf() < 0.5 and dname != "kam_diregi" and not bool(d.get("noflip", false)):
		s.flip_h = true
	decor_root.add_child(s)
	if d.get("glow_tex") != null:
		var g := Sprite2D.new()
		g.texture = d["glow_tex"]
		g.centered = false
		g.offset = s.offset
		g.flip_h = s.flip_h
		g.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
		var gm := CanvasItemMaterial.new()
		gm.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
		gm.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
		g.material = gm
		g.self_modulate = Color(1.6, 1.4, 1.2)
		s.add_child(g)
		var tw := g.create_tween().set_loops()
		if d.has("glow_pulse"):
			# soğuk ışıma (buz kristali): yavaş nefes, titreme yok
			var gp: float = float(d["glow_pulse"])
			g.self_modulate = Color(1.2, 1.3, 1.4)
			tw.tween_property(g, "self_modulate:a", 0.55, gp).set_trans(Tween.TRANS_SINE)
			tw.tween_property(g, "self_modulate:a", 1.0, gp).set_trans(Tween.TRANS_SINE)
		else:
			tw.tween_property(g, "self_modulate:a", 0.8, 0.16)
			tw.tween_property(g, "self_modulate:a", 1.0, 0.2)
	if glow_light:
		var tcol: Array = art.get("torch_col", [1.0, 0.58, 0.26])
		var l := add_light(s.position + Vector2(0, -56), Color(tcol[0], tcol[1], tcol[2]), 240.0, 1.35, decor_root)
		titrek(l, "kristal" if d.has("glow_pulse") else "mesale")   # v40: doğal alev titremesi (kristal: yavaş nefes)
	return s


func _decor(dname: String, tile_x: int, tile_y_surface: int, z := -2, glow_light := false) -> void:
	if bezirgan_alani(tile_x, 3):
		return   # v24: tüccarın tezgâhıyla üst üste binmesin
	var d2 := _decor_v2(dname)
	if not d2.is_empty():
		_decor_ink(d2, dname, tile_x, tile_y_surface, z, glow_light)


func _place_ink_extras() -> void:
	## Stil v2: platform altlarına gözetleme kulesi ayakları (yalnızca görsel; çarpışma değişmez) ve seyrek balballar.
	## Biyom art'ında "ink_extras" varsa balballar yerine o liste (bkz. _place_ink_extras_spec).
	_place_towers()
	if art.has("ink_extras"):
		_place_ink_extras_spec(art["ink_extras"])
		return
	var nxt := 30 + rng.randi_range(0, 20)
	while nxt < W - 12:
		var sy := surface_y(nxt)
		var roofed := cell(nxt, sy - 5) == 1 or cell(nxt, sy - 6) == 1
		if cell(nxt, sy) == 1 and not roofed:
			_decor("balbal", nxt, sy, -3)
			if rng.randf() < 0.4:
				_decor("balbal", nxt + 1, sy, -3)
		nxt += rng.randi_range(38, 70)


func _place_ink_extras_spec(spec: Array) -> void:
	## Biyoma özgü ek süsler (data/stil_v2.json "ink_extras" / "boss_extras"): her girdi {"names": [...], "every": [en az,
	## en çok] karo aralığı, "start": [a, b], "z", "light": çıra ışığı, "open": tavan altına konmaz} ya da sabit "at": [x...].
	for e in spec:
		var names: Array = e.get("names", [])
		if names.is_empty():
			continue
		var xs: Array = []
		if e.has("at"):
			xs = e["at"]
		else:
			var ev: Array = e.get("every", [40, 70])
			var st: Array = e.get("start", [24, 44])
			var nx := rng.randi_range(int(st[0]), int(st[1]))
			while nx < W - 12:
				xs.append(nx)
				nx += rng.randi_range(int(ev[0]), int(ev[1]))
		for xv in xs:
			var x := int(xv)
			var sy := surface_y(x)
			var roofed := cell(x, sy - 5) == 1 or cell(x, sy - 6) == 1
			if cell(x, sy) != 1 or (roofed and bool(e.get("open", true))):
				continue
			_decor(String(names[rng.randi_range(0, names.size() - 1)]), x, sy, int(e.get("z", -3)), bool(e.get("light", false)))


func _place_towers() -> void:
	## Her tek yönlü platform koşusunun altına kule ayakları (bkz. _tower_under)
	var y := 1
	while y < H - 1:
		var x := 0
		while x < W:
			if cell(x, y) == 2:
				var x0 := x
				while x < W and cell(x, y) == 2:
					x += 1
				_tower_under(x0, x - 1, y)
			else:
				x += 1
		y += 1


func _ground_below(x: int, y: int, max_d := 7) -> int:
	## v33: 14 -> 7: kuyu kapağının / tırmanış basamağının altına uzun iskele ayağı çizilmez
	## (x, y) altında ilk katı karo satırı; bulunamazsa -1
	for d in range(1, max_d + 1):
		if y + d >= H:
			return -1
		var c := cell(x, y + d)
		if c == 1:
			return y + d
		if c == 2:
			return -1
	return -1


func _tower_under(x0: int, x1: int, y: int) -> void:
	## Platform koşusunun (x0..x1, satır y) iki ucundan zemine inen kütük ayaklar; geniş ve yüksekse X destek ve kiriş.
	var d: Dictionary = _decor_v2("kule_dikme")
	if d.is_empty():
		return
	var k := 1.0 / float(d.get("texel", 2.0))
	var ends: Array = []
	var gl := _ground_below(x0, y)
	if gl > 0:
		ends.append([x0 * TS + 4.5, gl])
	var gr := _ground_below(x1, y)
	if gr > 0 and (x1 > x0 or gl < 0):
		ends.append([x1 * TS + TS - 4.5, gr])
	var top := (y + 1) * TS - 1.0
	for e in ends:
		var bottom := float(e[1]) * TS + 3.0
		_log_sprite(d, Vector2(float(e[0]), top), Vector2(float(e[0]), bottom), k, -1)
	if ends.size() == 2 and x1 - x0 >= 2:
		var gy := minf(float(ends[0][1]), float(ends[1][1])) * TS
		var h := gy - top
		if h > TS * 2.5 and bool(art.get("tower_brace", true)):
			var c: Dictionary = _decor_v2("kule_capraz")
			var a := Vector2(float(ends[0][0]), top + 6.0)
			var b := Vector2(float(ends[1][0]), gy - 8.0)
			var a2 := Vector2(float(ends[1][0]), top + 6.0)
			var b2 := Vector2(float(ends[0][0]), gy - 8.0)
			if not c.is_empty():
				_log_sprite(c, a, b, k, -2, true)
				_log_sprite(c, a2, b2, k, -2, true)
				var mid := top + h * 0.55
				_log_sprite(c, Vector2(float(ends[0][0]) - 6.0, mid), Vector2(float(ends[1][0]) + 6.0, mid), k, -1, true)
				var bag: Dictionary = _decor_v2("kule_bag")
				if not bag.is_empty():
					for e in ends:
						for yy in [mid, top + 6.0]:
							var s := Sprite2D.new()
							s.texture = bag["tex"]
							s.scale = Vector2(k, k)
							s.position = Vector2(float(e[0]), yy)
							s.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
							s.material = _ink_mat()
							s.z_index = 0
							decor_root.add_child(s)


var _ink_mat_cache: ShaderMaterial


func _ink_mat() -> ShaderMaterial:
	if _ink_mat_cache == null:
		_ink_mat_cache = ShaderMaterial.new()
		_ink_mat_cache.shader = load("res://shaders/env_ink.gdshader")
		_ink_mat_cache.set_shader_parameter("moon_gain", float(art.get("ground_moon_gain", 0.6)))
	return _ink_mat_cache


func _log_sprite(d: Dictionary, a: Vector2, b: Vector2, k: float, z: int, horizontal := false) -> void:
	## Döşenen kütük dokusunu a'dan b'ye uzat (dikme: doku dikeyde, kiriş: yatayda tekrarlanır)
	var s := Sprite2D.new()
	s.texture = d["tex"]
	s.texture_repeat = CanvasItem.TEXTURE_REPEAT_ENABLED
	s.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	s.region_enabled = true
	var ln := a.distance_to(b) / k
	var tw := float((d["size"] as Array)[0])
	var th := float((d["size"] as Array)[1])
	if horizontal:
		s.region_rect = Rect2(0, 0, ln, th)
		s.rotation = (b - a).angle()
	else:
		s.region_rect = Rect2(0, 0, tw, ln)
		s.rotation = (b - a).angle() - PI / 2.0
	s.scale = Vector2(k, k)
	s.position = (a + b) * 0.5
	s.material = _ink_mat()
	s.z_index = z
	decor_root.add_child(s)


func _has_decor(n: String) -> bool:
	return n in art.get("decor", ["dilek_agaci", "kam_diregi", "mantar", "cicek", "kaya", "cira"])


func _place_decor() -> void:
	## v32: süsler her odanın tabanı boyunca (çok katlı bölüm); giriş odasında dilek ağacı ve çıra
	var sx0 := spawn_cell.x
	if _has_decor("dilek_agaci"):
		_decor("dilek_agaci", sx0 + 3, surface_y(sx0 + 3, spawn_cell.y), -3)
	_decor("cira", sx0 + 7, surface_y(sx0 + 7, spawn_cell.y), -2, true)
	for rm in rooms:
		if rm["role"] == "yok":
			continue
		var ix0 := int(rm["ix0"])
		var ix1 := int(rm["ix1"])
		var next_torch: int = ix0 + rng.randi_range(6, 14)
		# v40: süs yoğunluğu oda türüne göre (odak noktaları yoğun, geçitler sakin): ödül odası ve harabe / mağara dolu,
		# köprü ve kuyu seyrek; eşikler ölçeklenir, rng çağrı sayısı değişmez
		var yog := 1.0
		var kind: String = String(rm.get("kind", ""))
		if OrtamCila.KAPALI:
			pass
		elif rm["role"] == "odul":
			yog = 1.5
		elif kind in ["harabe", "magara"]:
			yog = 1.3
		elif kind in ["kopru", "kuyu"]:
			yog = 0.7
		elif kind == "teras" and bool(rm.get("acik", false)):
			yog = 1.2
		for x in range(ix0, ix1 + 1):
			var sy := room_floor(rm, x)
			if cell(x, sy) != 1 or cell(x, sy - 1) != 0:
				continue
			if x >= next_torch:
				_decor("cira", x, sy, -2, true)
				next_torch = x + (rng.randi_range(26, 36) if style != "magara" else rng.randi_range(14, 22))
				continue
			var r := rng.randf() / yog
			# tavan altında ağaç/direk olmaz; mağarada mantar ve kaya çoğalır
			var roofed := cell(x, sy - 5) == 1 or cell(x, sy - 6) == 1
			if r < 0.02 and not roofed and _has_decor("cicek"):
				_decor(["cicek_1", "cicek_2", "cicek_3"][rng.randi_range(0, 2)], x, sy, 6)
			elif r < (0.18 if style == "magara" else 0.11) and _has_decor("mantar"):
				_decor(["mantar_1", "mantar_2"][rng.randi_range(0, 1)], x, sy, 6)
			elif r < (0.26 if style in ["magara", "harabe"] else 0.14) and _has_decor("kaya"):
				_decor(["kaya_1", "kaya_2"][rng.randi_range(0, 1)], x, sy, -1)
			elif r < 0.275 and not roofed and _has_decor("kam_diregi"):
				_decor("kam_diregi", x, sy, -3)
			elif r < 0.285 and not roofed and style != "harabe" and _has_decor("dilek_agaci"):
				_decor("dilek_agaci", x, sy, -3)
	_place_ink_extras()
	# çıkış: Kut Kapısı (çıkış odasının sağ ucu)
	exit_pos = Vector2(exit_cell.x * TS + TS / 2.0, (exit_cell.y + 1) * TS)
	var gate := KutGate.new()
	gate.position = exit_pos
	decor_root.add_child(gate)
	var portal := FX.anim("rift_portal", exit_pos + Vector2(0, -34), 0.0, 1.0, Color(0.6, 1.0, 1.0, 0.85))
	if portal:
		portal.loop = true
		portal.z_index = -1
		portal.reparent(decor_root)
	var gc: Array = art.get("gate_col", [0.45, 0.9, 1.0])
	add_light(exit_pos + Vector2(0, -40), Color(gc[0], gc[1], gc[2]), 220.0, 1.4, decor_root)


# ------------------------------------------------------------------ oyuncu, düşman, eşya
func _spawn_player() -> void:
	player = Player.new()
	player.level = self
	player.position = Vector2(5 * TS, surface_y(5) * TS - 2)
	if not rooms.is_empty():
		player.position = Vector2(spawn_cell.x * TS + TS / 2.0, (spawn_cell.y + 1) * TS - 2)
	if OS.get_cmdline_user_args().has("--tehlikeye"):
		# test / çekim: oyuncuyu ilk tehlike havuzunun (zehir / lav) solundaki zemine koy
		for x in W:
			var found := false
			for y in H:
				if cell(x, y) == 3:
					var tx := maxi(2, x - 3)
					player.position = Vector2(tx * TS + TS / 2.0, surface_y(tx) * TS - 2)
					print("[tehlikeye] %s x=%d y=%d" % [haz_kind, x, y])
					found = true
					break
			if found:
				break
	actors.add_child(player)
	# yakın çekim kamera (art "camera_zoom", stil_v2.json; CameraV2: öncü kayma, dikey pencere, boss sığdırma)
	var cv := CameraV2.new()
	cv.level = self
	cv.player = player
	camera = cv
	camera.limit_left = 0
	camera.limit_top = 0
	camera.limit_right = W * TS
	var deepest := 0
	for h in heights:
		deepest = maxi(deepest, int(h))
	camera.limit_bottom = mini(H, deepest + 4) * TS
	if not rooms.is_empty():
		# v32: çok katlı bölüm: sınırlar kesim ızgarasından; v33: dolu kesimlerin sıkı kutusu (sol / üst de)
		camera.limit_left = bounds.position.x * TS
		camera.limit_top = bounds.position.y * TS
		camera.limit_right = bounds.end.x * TS
		camera.limit_bottom = bounds.end.y * TS
	add_child(camera)
	Game.base_zoom = float(art.get("camera_zoom", 1.0))
	camera.zoom = Vector2.ONE * Game.base_zoom
	camera.process_mode = Node.PROCESS_MODE_ALWAYS
	camera.make_current()
	camera.reset_smoothing.call_deferred()
	Game.camera = camera
	# Kut ışığı: karanlık ormanda Bengü'nün çevresi hep okunur kalsın
	add_light(Vector2(0, -26), Color(1.0, 0.88, 0.68), 150.0, 0.7, player)


func _spawn_enemies() -> void:
	## Biyomun tüm türleri, oda başına grup grup. v34 (geri bildirim: "katların çoğu boş, boşuna yürüyorum"): yoğunluk
	## data/world.json "yogunluk": dövüş odalarının (ana / dal / çıkış; uzantı dahil) tabanı boyunca "aralik" karoda bir
	## GRUP (v33: 15-22 karoda bir tek yaratık; derinlikle Zorluk.yogunluk kadar sıklaşır); her ana yol ve dal odasında
	## en az bir grup; grupların "karisik" payı yakın + uzak dövüşçü (okçu / büyücü / uçan) ikilisi; yüksek odalarda
	## "ucan_ek" ihtimalle havada bir uçan; ödül odalarında "odul_bekci" ihtimalle bekçi grubu (bazen seçkin). Giriş
	## noktasının "giris_bos", Kut Taşlarının "tasi_bos" karo çevresi ve Kut Kapısı önü boş kalır. Pusucular odanın
	## yüksek yerlerine (platform / ada / seki üstü). Seçkinler ana yolun 3. odasından sonra, aralarında en az 4 yaratık.
	var cfg: Dictionary = Data.world.get("yogunluk", {})
	var aralik: Array = cfg.get("aralik", [9, 13])
	var en_az := int(cfg.get("en_az_aralik", 7))
	var depth := int(Game.run.get("depth", 1))
	var st := {"elites": 0, "since": 99, "pool": _biome_pool(), "depth": depth, "karisik": float(cfg.get("karisik", 0.45))}
	gruplar = []
	for rm in rooms:
		if not (rm["role"] in ["ana", "dal", "cikis", "giris"]):
			continue
		var ix0 := int(rm["ix0"])
		var ix1 := int(rm["ix1"])
		var placed := 0
		var x := ix0 + 3 + rng.randi_range(0, 4)
		while x < ix1 - 2:
			if not _yaratik_yasak(x, room_floor(rm, x) - 1):
				placed += _grup(rm, x, st, false)
			x += maxi(en_az, rng.randi_range(int(aralik[0]), int(aralik[1])) - Zorluk.yogunluk(depth))
		if placed == 0 and rm["role"] != "giris":
			# en az bir grup: odanın yasak olmayan bir sütunu (orta önce)
			var cols: Array = []
			for tx in range(ix0 + 2, ix1 - 1):
				cols.append(tx)
			var mid := (ix0 + ix1) / 2
			cols.sort_custom(func(a: int, b: int) -> bool: return absi(a - mid) < absi(b - mid))
			for tx in cols:
				if not _yaratik_yasak(tx, room_floor(rm, tx) - 1):
					placed += _grup(rm, tx, st, false)
					if placed > 0:
						break
		# yüksek odada havada bir uçan (Dead Cells'in katmanlı dövüşü: yerde yakın, havada uzak)
		var hava := room_floor(rm, (ix0 + ix1) / 2) - int(rm["iy0"])
		if hava >= 7 and rng.randf() < float(cfg.get("ucan_ek", 0.3)) and rm["role"] != "giris":
			var uc := _tur_sec(st["pool"], "ucan")
			var ux := rng.randi_range(ix0 + 4, maxi(ix0 + 4, ix1 - 4))
			if uc != "" and not _yaratik_yasak(ux, room_floor(rm, ux) - 1):
				var e := spawn_enemy(uc, Vector2(ux * TS + TS / 2.0, room_floor(rm, ux) * TS - 1), false, rng.randf() < Zorluk.ofkeli_sans(), true)
				if _yerlesim_denetle(e):
					gruplar.append({"oda": int(rm["id"]), "karisik": false, "n": 1})
	# ödül odası bekçileri (pazar ve seçkin odası hariç: seçkin odasının bekçisi _place_rooms)
	for rm in rooms:
		if rm["role"] != "odul" or String(rm.get("odul", "")) in ["pazar", "seckin", "hikaye"]:
			continue
		if rng.randf() >= float(cfg.get("odul_bekci", 0.7)):
			continue
		var ix0 := int(rm["ix0"])
		var ix1 := int(rm["ix1"])
		var om := LevelGen._odul_mid(rm)
		# bekçi ödülle kapı arasında (ödülün 4-6 karo kapı yanı)
		var side := String(rm.get("_door_side", "sol"))
		var tx := om - rng.randi_range(4, 6) if side != "sag" else om + rng.randi_range(4, 6)
		tx = clampi(tx, ix0 + 2, ix1 - 2)
		var sec: bool = rng.randf() < float(cfg.get("bekci_seckin", 0.35)) * (0.5 if depth <= 1 else 1.0)
		if not _yaratik_yasak(tx, room_floor(rm, tx) - 1):
			_grup(rm, tx, st, sec)


func _bos_oda_doldur() -> void:
	## v34: yerleşim denetimi (find_spawn kaydırması, yasak bölge, pazar temizliği) bir ana yol / dal odasını yaratıksız
	## bıraktıysa: odanın ortasından dışa sütun sütun tek yaratık dener; yaratık bu odada kalmazsa kaldırılır
	var say := {}
	for e in get_tree().get_nodes_in_group("dusman"):
		if is_instance_valid(e) and not e.is_queued_for_deletion() and e.get("level") == self:
			var id := int(room_at(int(e.position.x / TS), int((e.position.y - 4.0) / TS)).get("id", -1))
			say[id] = int(say.get(id, 0)) + 1
	var pool := _biome_pool()
	for rm in rooms:
		if not (rm["role"] in ["ana", "cikis", "dal"]) or int(say.get(int(rm["id"]), 0)) > 0:
			continue
		var ix0 := int(rm["ix0"])
		var ix1 := int(rm["ix1"])
		var mid := (ix0 + ix1) / 2
		var cols: Array = []
		for tx in range(ix0 + 1, ix1):
			cols.append(tx)
		cols.sort_custom(func(a: int, b: int) -> bool: return absi(a - mid) < absi(b - mid))
		var kind := _tur_sec(pool, "yakin")
		if kind == "":
			kind = String(pool[0])
		# v39: seçilen tür odaya sığmazsa (iri gövdeler: Ağ Ana, Tepegöz Yavrusu ...) havuzun öbür türleri denenir
		var adaylar: Array = [kind]
		for k2 in pool:
			if not adaylar.has(k2):
				adaylar.append(k2)
		var konan := false
		# v39: tüccar tezgâhı dar bir ana yol odasına taşmışsa ikinci geçişte yalnızca tezgâhın kendisi yasak
		var denemeler: Array = []
		for pay in [4, 0]:
			for kk in adaylar:
				denemeler.append([kk, pay])
		for dn in denemeler:
			if konan:
				break
			var kk: String = dn[0]
			for tx in cols:
				var fy := room_floor(rm, tx)
				if _yaratik_yasak(tx, fy - 1) or bezirgan_alani(tx, int(dn[1])):
					continue
				var e := spawn_enemy(String(kk), Vector2(tx * TS + TS / 2.0, fy * TS - 1), false, false, true)
				if e == null:
					continue
				if int(room_at(int(e.position.x / TS), int((e.position.y - 4.0) / TS)).get("id", -1)) != int(rm["id"]) or _yaratik_yasak(int(e.position.x / TS), int((e.position.y - 4.0) / TS)):
					e.remove_from_group("dusman")
					e.queue_free()
					continue
				gruplar.append({"oda": int(rm["id"]), "karisik": false, "n": 1})
				konan = true
				break


func _yaratik_yasak(tx: int, ty: int) -> bool:
	## v34: giriş noktası, Kut Taşları ve Kut Kapısı çevresinde yaratık doğmaz (data/world.json "yogunluk")
	var cfg: Dictionary = Data.world.get("yogunluk", {})
	var gb := int(cfg.get("giris_bos", 12))
	var tb := int(cfg.get("tasi_bos", 4))
	if absi(tx - spawn_cell.x) < gb and absi(ty - spawn_cell.y) < 7:
		return true
	if absi(tx - exit_cell.x) < 4 and absi(ty - exit_cell.y) < 4:
		return true
	for c in _gen.get("tasi", []):
		if absi(tx - int(c.x)) < tb and absi(ty - int(c.y)) < 5:
			return true
	return false


func _ai_of(kind: String) -> String:
	var d := Data.enemy_def(kind)
	return String(d.get("ai", Data.enemy_def(String(d.get("sprite", kind))).get("ai", "lunger")))


func _tur_sec(pool: Array, sinif: String) -> String:
	## v34: havuzdan sınıfa göre tür ("uzak": okçu / büyücü / uçan atıcı; "ucan"; "yakin"); yoksa ""
	var c: Array = []
	for k in pool:
		var ai := _ai_of(String(k))
		var uzak: bool = ai in ["flyer_ranged", "illusionist", "archer", "caster", "charmer", "summoner", "healer"]
		var ucan: bool = ai in ["flyer_ranged", "diver", "swarm", "swooper"]
		if (sinif == "uzak" and uzak) or (sinif == "ucan" and ucan) or (sinif == "yakin" and not uzak and not ucan):
			c.append(k)
	if c.is_empty():
		return ""
	return String(c[rng.randi_range(0, c.size() - 1)])


func _yerlesim_denetle(e: Enemy) -> bool:
	## Yerleşim denetimi yaratığı yasak bölgeye (giriş / taş / kapı önü) taşıdıysa kaldırır. true: kaldı
	if e == null:
		return false
	if _yaratik_yasak(int(floor(e.position.x / TS)), int(floor((e.position.y - 4.0) / TS))):
		e.remove_from_group("dusman")
		e.queue_free()
		spawn_skipped += 1
		return false
	return true


func _grup(rm: Dictionary, x: int, st: Dictionary, bekci_seckin: bool) -> int:
	## Bir yaratık grubu: çapa tür (havuzdan), v22 sürü / kurt ikilisi, v34 karışık grup (yakın + uzak dövüşçü 3 karo
	## içeride). Döndürür: konan yaratık sayısı.
	var pool: Array = st["pool"]
	var depth: int = st["depth"]
	var ix0 := int(rm["ix0"])
	var ix1 := int(rm["ix1"])
	var kind: String = pool[rng.randi_range(0, pool.size() - 1)]
	var ai := _ai_of(kind)
	var kinds: Array = [kind]
	if Data.enemy_def(kind).get("sprite", kind) == "kara_boru" and ai == "lunger" and rng.randf() < 0.5:
		kinds.append(kind)
	elif not (ai in ["pouncer", "flyer_ranged", "diver", "swooper", "summoner", "healer", "slammer", "chainer"]) and rng.randf() < Zorluk.suru(depth):
		kinds.append(kind)   # v22: derinde ikili gruplar (sürü)
	var karisik := false
	if rng.randf() < float(st["karisik"]):
		var uzak: bool = ai in ["flyer_ranged", "illusionist", "archer", "caster", "charmer", "summoner", "healer"]
		var es := _tur_sec(pool, "yakin" if uzak else "uzak")
		if es != "":
			kinds.append(es)
			karisik = true
	var perches: Array = []
	for kk in kinds:
		if _ai_of(String(kk)) == "pouncer":
			for px in range(ix0, ix1 + 1):
				var fy := room_floor(rm, px)
				for py in range(int(rm["iy0"]), fy - 3):
					if cell(px, py) != 0 and cell(px, py) != 3 and cell(px, py - 1) == 0 and cell(px, py - 2) == 0:
						perches.append(Vector2i(px, py))
			break
	var n := 0
	var dir := 1 if x < (ix0 + ix1) / 2 else -1   # eşlikçiler odanın içine doğru
	for k in kinds.size():
		var kk: String = kinds[k]
		var tx := clampi(x + dir * k * (3 if karisik and k == kinds.size() - 1 else 2), ix0 + 1, ix1 - 1)
		var is_elite := bekci_seckin and k == 0
		if not is_elite:
			var sira := int(rm.get("ana_i", -1))
			if bool(rm.get("uzanti", false)):
				sira = 99
			is_elite = int(st["elites"]) < Zorluk.seckin_sayi(depth) and sira >= 3 and int(st["since"]) >= 4 and rng.randf() < 0.3
			if is_elite:
				st["elites"] = int(st["elites"]) + 1
		if is_elite:
			st["since"] = 0
		else:
			st["since"] = int(st["since"]) + 1
		var pos := Vector2(tx * TS + TS / 2.0, room_floor(rm, tx) * TS - 1)
		if _ai_of(kk) == "pouncer" and not perches.is_empty():
			var best: Vector2i = perches[0]
			var bd := 9999.0
			for pc in perches:
				var dd := absf(float(pc.x - tx))
				if dd < bd:
					bd = dd
					best = pc
			if bd < 20.0:
				pos = Vector2(best.x * TS + TS / 2.0, best.y * TS - 1)
		var en := spawn_enemy(kk, pos, is_elite, not is_elite and rng.randf() < Zorluk.ofkeli_sans(), true)
		if not _yerlesim_denetle(en):
			continue
		if en.sprite_kind == "kara_boru" and k == 1 and kk == kind:
			en.flank = 1  # ikinci kurt arkadan dolaşır
		n += 1
	if n > 0:
		gruplar.append({"oda": int(rm["id"]), "karisik": karisik and n >= 2, "n": n})
	return n


func spawn_enemy(kind: String, pos: Vector2, is_elite := false, is_ofkeli := false, check := false) -> Enemy:
	## check (v25, bölüm yerleşimi): gövde sığmıyorsa yakında sığan yere taşınır, hiç yer yoksa konmaz (null)
	var e: Enemy = Boss.new() if String(Data.enemy_def(kind).get("ai", "")).begins_with("boss") else Enemy.new()
	e.setup(kind, is_elite, int(Game.run.get("tier", 0)), is_ofkeli)
	e.level = self
	var lift := 70.0 if kind == "cor" or e.flying else 0.0   # v39: bütün uçanlar havada doğar
	e.position = pos - Vector2(0, lift)
	if check:
		# görsel ölçek Enemy._ready'de kurulur: seçkin 1,3, öfkeli 1,1
		var sc := 1.3 if e.elite else (1.1 if e.ofkeli else 1.0)
		var q := find_spawn(e.size * sc, e.flying, pos, lift)
		if q == Vector2.INF:
			spawn_skipped += 1
			e.free()
			return null
		if q.distance_to(e.position) > 1.0:
			spawn_moved += 1
		e.position = q
	actors.add_child(e)
	return e


# ------------------------------------------------------------------ v25 yerleşim denetimi
func spawn_ok(sz: Vector2, flying: bool, pos: Vector2) -> bool:
	## Gövde (sz; ayak noktası pos) ve 6 px baş payı katı / tehlike karosuna girmez. Yerdeki yaratık: ayaklarının altı
	## boydan boya yürünür, aynı satırda gövde + her yanda 1 karo düz ve üstü gövde boyu açık alan (dar oyuğa konmaz).
	var r := Rect2(pos.x - sz.x / 2.0, pos.y - sz.y - 6.0, sz.x, sz.y + 6.0).grow(-1.0)
	for x in range(int(floor(r.position.x / TS)), int(floor(r.end.x / TS)) + 1):
		for y in range(int(floor(r.position.y / TS)), int(floor(r.end.y / TS)) + 1):
			var c := cell(x, y)
			if c == 1 or c == 3:
				return false
	if flying:
		return true
	var fy := int(floor((pos.y + 4.0) / TS))
	var fx0 := int(floor((pos.x - sz.x / 2.0 + 2.0) / TS))
	var fx1 := int(floor((pos.x + sz.x / 2.0 - 2.0) / TS))
	for x in range(fx0, fx1 + 1):
		var f := cell(x, fy)
		if f != 1 and f != 2:
			return false
	var hc := int(ceil((sz.y + 6.0) / TS))
	var run := fx1 - fx0 + 1
	for s in [-1, 1]:
		var x: int = (fx0 - 1) if s < 0 else (fx1 + 1)
		for i in 2:
			if not _col_free(x, fy, hc):
				break
			run += 1
			x += s
	return run >= int(ceil(sz.x / TS)) + 2


func _col_free(x: int, fy: int, hc: int) -> bool:
	var f := cell(x, fy)
	if f != 1 and f != 2:
		return false
	for k in range(1, hc + 1):
		var c := cell(x, fy - k)
		if c == 1 or c == 3:
			return false
	return true


func find_spawn(sz: Vector2, flying: bool, pos: Vector2, lift := 0.0) -> Vector2:
	## pos (zemin ayak noktası; uçan "cor" lift px yukarıda doğar) sığmıyorsa en yakın sütunlarda (±18 karo) sığan zemin;
	## yoksa Vector2.INF
	if spawn_ok(sz, flying, pos - Vector2(0, lift)):
		return pos - Vector2(0, lift)
	var tx := int(floor(pos.x / TS))
	for d in range(0, 19):
		for s in ([1] if d == 0 else [1, -1]):
			var x: int = tx + d * s
			if x < 20 or x > W - 10:
				continue
			var rows: Array = []
			for y in range(2, H - 1):
				var c := cell(x, y)
				if cell(x, y - 1) == 0 and (c == 1 or c == 2):
					rows.append(y)
			rows.sort_custom(func(a: int, b: int) -> bool: return absf(a * TS - pos.y) < absf(b * TS - pos.y))
			for y in rows:
				var p := Vector2(x * TS + TS / 2.0, y * TS - 1.0 - lift)
				if spawn_ok(sz, flying, p):
					return p
	return Vector2.INF


func _spawn_kesif() -> void:
	## v25: Üç Âlem'le birlikte kalkan gizli yeraltı odalarının (eşya + şifa + altın) ve Ülgen sunağının (eşya) ganimeti
	## bölümün kendisine dağıtıldı: girişten ulaşılan yüksek bir çıkıntıda (ada, kule, sütun tepesi; yüzeyden en az 3 karo
	## yukarıda) bir üst kademe eşya kaidesi + şifa + 4 altın; %50 ihtimalle yolda ikinci bir zula (eşya + 3 altın).
	## Kaidelere, tüccara ve birbirlerine uzak.
	var seen := LevelGen.reach_from(grid, W, H, spawn_cell.x, spawn_cell.y)
	var used: Array = []
	for kc in kaide_xs:
		used.append(int(kc.x))
	for ch in chunks:
		for mk in ch.get("marks", []):
			used.append(int(mk[1]))
	var high: Array = []
	var low: Array = []
	for x in range(bounds.position.x + 12, bounds.end.x - 12):
		if bezirgan_alani(x, 6) or absi(x - spawn_cell.x) < 14 or absi(x - exit_cell.x) < 10:
			continue
		var far := true
		for u in used:
			if absi(int(u) - x) < 14:
				far = false
				break
		if not far:
			continue
		var sy := surface_y(x)
		for y in range(4, H - 2):
			if seen[idx(x, y)] == 0 or cell(x, y + 1) != 1:
				continue
			if cell(x, y - 1) != 0 or cell(x, y - 2) != 0 or cell(x - 1, y + 1) == 3 or cell(x + 1, y + 1) == 3:
				continue
			if y + 1 <= sy - 3:
				high.append(Vector3i(x, y + 1, sy - (y + 1)))
			elif y + 1 == sy:
				low.append(Vector2i(x, y + 1))
	var tier := int(Game.run.get("tier", 0))
	var spot := Vector2i(-1, -1)
	if not high.is_empty():
		high.sort_custom(func(a: Vector3i, b: Vector3i) -> bool: return a.z > b.z)
		var top: Vector3i = high[rng.randi_range(0, mini(high.size(), maxi(4, high.size() / 4)) - 1)]
		spot = Vector2i(top.x, top.y)
	elif not low.is_empty():
		spot = low[rng.randi_range(0, low.size() - 1)]
	if spot.x >= 0:
		drop_item(ItemGen.random_drop(tier + 1), Vector2(spot.x * TS + 12, spot.y * TS - 30), true)
		var sp := Pickup.new()
		sp.kind = "sifa"
		sp.level = self
		sp.position = Vector2(spot.x * TS + 12 - 26, spot.y * TS - 8)
		add_child(sp)
		for g in 4:
			drop_orb("gold", Vector2(spot.x * TS + 12 + randf_range(-18, 18), spot.y * TS - 20))
		used.append(spot.x)
	# v34: ikinci zula artık gizli cepte (kırık duvar "zula" içeriği); cep yoksa eskisi gibi yolda
	if rng.randf() < 0.5 and not low.is_empty() and kiriklar.is_empty():
		low.shuffle()
		for c in low:
			var ok := true
			for u in used:
				if absi(int(u) - c.x) < 22:
					ok = false
					break
			if ok:
				drop_item(ItemGen.random_drop(tier), Vector2(c.x * TS + 12, c.y * TS - 30), true)
				for g in 3:
					drop_orb("gold", Vector2(c.x * TS + 12 + randf_range(-16, 16), c.y * TS - 20))
				break


func _spawn_items() -> void:
	## v32: üç eşya kaidesi ana yolun 1/4, 2/4, 3/4'ündeki odaların tabanında (LevelGen "kaide")
	for kc in kaide_xs:
		var it := ItemGen.random_drop(int(Game.run.get("tier", 0)))
		drop_item(it, Vector2(int(kc.x) * TS + 12, (int(kc.y) + 1) * TS - 30), true)


func _spawn_scrolls() -> void:
	## Kut Tomarları (v23; eski adı tılsım): her bölümde üç tane. v32: çıkmaz "tomar" odaları (M işareti, _place_rooms)
	## önce; kalanlar ana yolda: biri yolun ortasındaki odanın tabanında, biri girişten ulaşılan yüksek bir çıkıntıda
	## (keşif ödülü).
	var n := 0
	for ch in chunks:
		for mk in ch.get("marks", []):
			if String(mk[0]) == "M":
				n += 1
	var mr := main_rooms()
	if n < 3 and mr.size() >= 3:
		var rm: Dictionary = mr[mr.size() / 2]
		var sp: Vector2i = LevelGen._floor_spot(grid, W, H, rm, (int(rm["ix0"]) + int(rm["ix1"])) / 2 + rng.randi_range(-6, 6))
		drop_scroll(Vector2(sp.x * TS + 12, (sp.y + 1) * TS))
		n += 1
	if n < 3:
		var seen := LevelGen.reach_from(grid, W, H, spawn_cell.x, spawn_cell.y)
		var best := Vector2.ZERO
		for x in range(bounds.position.x + 12, bounds.end.x - 12):
			var sy := surface_y(x)
			for y in range(bounds.position.y + 2, bounds.end.y - 2):
				if cell(x, y) == 1 and cell(x, y - 1) == 0 and seen[idx(x, y - 1)] == 1 and y < sy - 3 and absi(x - spawn_cell.x) > 14:
					if best == Vector2.ZERO or rng.randf() < 0.08:
						best = Vector2(x * TS + 12, y * TS)
		if best != Vector2.ZERO:
			drop_scroll(best)
			n += 1
	while n < 3 and mr.size() >= 2:
		# yine eksikse (dal yok): ana yolun başka odalarının tabanı
		var rm2: Dictionary = mr[clampi(1 + n, 1, mr.size() - 1)]
		var sp2: Vector2i = LevelGen._floor_spot(grid, W, H, rm2, (int(rm2["ix0"]) + int(rm2["ix1"])) / 2 + 5)
		drop_scroll(Vector2(sp2.x * TS + 12, (sp2.y + 1) * TS))
		n += 1


func drop_scroll(pos: Vector2) -> void:
	var p := Pickup.new()
	p.kind = "tilsim"
	p.level = self
	p.position = pos
	p.pedestal = true
	add_child(p)
	pickups.append(p)


func drop_blueprint(id: String, pos: Vector2) -> void:
	var p := Pickup.new()
	p.kind = "parsomen"
	p.item_id = id
	p.level = self
	p.position = pos
	p.velocity = Vector2(randf_range(-40, 40), -160)
	add_child(p)
	pickups.append(p)


func drop_sanat_tomari(id: String, pos: Vector2) -> void:
	## v27 Sanat Tomarı: dokununca açılmamış bir savaş sanatını kalıcı olarak öğretir (id boşsa rastgele; yerdekiler hariç)
	if id == "":
		var pool := SavasSanati.kilitli()
		for q in pickups:
			if is_instance_valid(q) and q.kind == "parsomen" and String(q.item_id).begins_with("sanat:"):
				pool.erase(String(q.item_id).trim_prefix("sanat:"))
		if pool.is_empty():
			return
		id = String(pool[randi_range(0, pool.size() - 1)])
	var p := Pickup.new()
	p.kind = "parsomen"
	p.item_id = "sanat:" + id
	p.level = self
	p.position = pos
	p.velocity = Vector2(randf_range(-40, 40), -170)
	add_child(p)
	pickups.append(p)


func drop_item(it: Dictionary, pos: Vector2, pedestal := false) -> void:
	if it.is_empty():
		return
	var p := Pickup.new()
	p.kind = "item"
	p.item = it
	p.level = self
	p.position = pos
	p.pedestal = pedestal
	add_child(p)
	pickups.append(p)


func drop_orb(kind: String, pos: Vector2) -> void:
	var p := Pickup.new()
	p.kind = kind
	p.level = self
	p.position = pos
	p.velocity = Vector2(randf_range(-80, 80), randf_range(-200, -120))
	add_child(p)


func nearest_item(pos: Vector2) -> Pickup:
	var best: Pickup = null
	var bd := 28.0
	for p in pickups:
		if not is_instance_valid(p) or (p.kind != "item" and p.kind != "tilsim" and p.kind != "lutuf"):
			continue
		var d: float = p.global_position.distance_to(pos)
		if d < bd:
			bd = d
			best = p
	return best


func slot_options(it: Dictionary) -> Array:
	## Dead Cells gibi: silah ve kalkanlar iki silah yuvasından birine (J / K), teçhizat iki teçhizat yuvasından birine (U / I).
	return ["g1", "g2"] if it.get("cat", "") == "gadgets" else ["melee", "second"]


func natural_slot(it: Dictionary) -> String:
	if it.get("cat", "") == "gadgets":
		return "g1"
	return "second" if Player.is_second_item(it) else "melee"


func try_equip(p: Pickup) -> void:
	## Boş uygun yuva varsa doğrudan oraya; ikisi de doluysa oyuncuya hangi yuvayı değiştireceği sorulur.
	var slots: Dictionary = Game.run["slots"]
	var nat := natural_slot(p.item)
	if slots.get(nat, {}).is_empty():
		equip(p, nat)
		return
	for sl in slot_options(p.item):
		if slots.get(sl, {}).is_empty():
			equip(p, sl)
			return
	slot_requested.emit(p)


func equip(p: Pickup, slot := "") -> void:
	var it: Dictionary = p.item
	if slot == "":
		slot = natural_slot(it)
	var old: Dictionary = Game.run["slots"].get(slot, {})
	Game.run["slots"][slot] = it
	var rcol := Color.from_string(Data.items["rarities"][it["rarity"]]["color"], Color.WHITE)
	FX.text(player.center() + Vector2(0, -30), it["name"], rcol, 8)
	FX.ring(player.center(), 20, rcol, 0.25)
	FX.burst(player.center(), rcol, 10, 60, 0.4, 0.16, -60, true)
	player.vis_scale = Vector2(0.9, 1.1)
	if player.has_method("on_equip"):
		player.on_equip()
	Ses.play("esya_kusan")
	if old.is_empty():
		pickups.erase(p)
		p.queue_free()
	else:
		# eski eşya yere düşer (biraz yana sekerek, hemen yeniden alınmasın diye)
		p.item = old
		p.velocity = Vector2(-player.facing * 60.0, -150.0)
		p.reset_ground()


# ------------------------------------------------------------------ savaş yardımcıları
func add_projectile(p: Projectile) -> void:
	p.level = self
	proj_root.add_child(p)


func flash_white(a := 0.35) -> void:
	## Ağır vuruşta tüm ekran bir an beyazlar (Dead Cells'in "kill flash"i). Göz yormasın: en çok 0,18 alfa,
	## 2-3 kare; ağır çekim/vuruş duraklaması uzatmaz (gerçek zamanlı). Ayarlar > Sarsıntı ve flaş ile ölçeklenir.
	if red_rect == null:
		return
	a = minf(a * 0.5, 0.18) * Game.fx_scale
	if a <= 0.01:
		return
	red_rect.color = Color(1.0, 0.97, 0.9, a)
	red_rect.visible = true
	var tw := red_rect.create_tween()
	tw.set_ignore_time_scale(true)
	tw.tween_property(red_rect, "color:a", 0.0, 0.06)
	tw.tween_callback(func() -> void:
		red_rect.color = Color(1, 0.1, 0.1, 0.0)
		red_rect.visible = false)


func explode(pos: Vector2, radius: float, dmg: float, by_player: bool) -> void:
	## v14: aşamalı piksel patlama (ExplosionFX): flaş → ateş topu → duman + parçalar; kamera, ses ve ışık içinde
	var away := Vector2.UP
	if player and is_instance_valid(player):
		var d: Vector2 = player.center() - pos
		if d.length() > 1.0:
			away = d.normalized()
	FX.explosion(pos, radius, Color(1.0, 0.85, 0.3), radius >= 50.0, away)
	if by_player:
		break_cracks(Rect2(pos - Vector2(radius, radius), Vector2(radius, radius) * 2.0))   # v34: gizli duvar / küp
	if by_player:
		for e in get_tree().get_nodes_in_group("dusman"):
			if is_instance_valid(e) and not e.dead and e.center().distance_to(pos) < radius + 14.0:
				e.take_hit(dmg, {"kb": 220.0, "dir": sign(e.center().x - pos.x), "stun": 0.4})
	elif player and player.center().distance_to(pos) < radius + 8.0:
		player.take_hit(dmg, null)


func fire_pool(pos: Vector2, radius: float, duration: float, dps: float) -> void:
	var fp := FirePool.new()
	fp.level = self
	fp.radius = radius
	fp.life = duration
	fp.dps = dps
	var ty := int(floor(pos.x / TS))
	fp.position = Vector2(pos.x, surface_y(ty, int(floor(pos.y / TS)) - 2) * TS)
	add_child(fp)
	titrek(add_light(Vector2(0, -6), Color(1.0, 0.55, 0.2), radius * 3.0, 1.3, fp), "mesale")   # v40 titrek alev ışığı


func quake(pos: Vector2, radius: float, dmg: float, it: Dictionary, pl: Node) -> void:
	## Mancınık taşı: çarptığı yerde sarsıntı; alanındaki düşmanlar sersemler
	Game.shake(5.0)
	Game.kick(Vector2.DOWN, 4.0)
	FX.ring(pos + Vector2(0, 4), radius * 0.6, Color(0.9, 0.8, 0.6), 0.3, 0.3)
	FX.shock_line(pos, radius * 0.5)
	FX.anim("earth_rupture", pos + Vector2(0, 6), 0.0, 0.5 + radius / 90.0, Color(0.9, 0.85, 0.7), false)
	FX.dust(pos, Vector2.UP, 10, 0.4)
	for e in get_tree().get_nodes_in_group("dusman"):
		if is_instance_valid(e) and not e.dead and e.center().distance_to(pos) < radius * 0.5 + 16.0:
			if pl and pl.has_method("_deal"):
				pl._deal(e, dmg, it, {"kb": 150.0, "dir": signf(e.center().x - pos.x), "stun": 0.8, "falling": true})


func spawn_spirit_wolf(pos: Vector2, life: float, dmg: float, sprite_name := "kara_boru") -> void:
	var w := SpiritWolf.new()
	w.level = self
	w.life = life
	w.dmg = dmg
	w.sprite_name = sprite_name
	w.position = pos
	actors.add_child(w)


func telegraph_ground(pos: Vector2, t: float) -> void:
	var m := GroundMarker.new()
	m.life = t
	m.position = Vector2(pos.x, surface_y(int(floor(pos.x / TS)), int(floor(pos.y / TS)) - 2) * TS)
	fx_root.add_child(m)


func spawn_roots(pos: Vector2, dmg: float, source: Node) -> void:
	var r := RootSpikes.new()
	r.level = self
	r.dmg = dmg
	r.source = source
	r.position = Vector2(pos.x, surface_y(int(floor(pos.x / TS)), int(floor(pos.y / TS)) - 2) * TS)
	fx_root.add_child(r)


func on_enemy_died(e: Enemy) -> void:
	if e == boss and e != null:
		_on_boss_died(e)
		return
	_v12_on_kill(e)
	if e.has_meta("yavru"):
		return   # v39: çağrılan Şulmus yavrusu ganimet bırakmaz
	if sinav != null:
		sinav.olduruldu(e)   # v42 Avcı sınavı
	_lanet_oldurme()   # v34
	# v24: seçkin +6 -> +10 tane (tüccar ekonomisi). v34: yaratık sayısı ~1,9 kat: sıradan yaratığın altını 2-4 -> 1-2
	# tane (+%25 bir tane daha); bölüm başına altın v33'ün ~1,5 katı (küp / gizli cep / lanetli sandık dahil)
	for i in randi_range(1, 2) + (1 if randf() < 0.25 else 0) + (10 if e.elite else 0):
		drop_orb("gold", e.center())


	# Kut taneleri (Dead Cells hücreleri): her düşman en az bir tane; seçkinler dört; şans eseri fazladan
	for i in (4 if e.elite else 1) + (1 if randf() < 0.3 else 0):
		drop_orb("kut", e.center())
	if e.elite or randf() < 0.025:   # v23: sıradan düşmandan eşya %4 -> %2,5 (iyi eşya seyrek)
		drop_item(ItemGen.random_drop(int(Game.run.get("tier", 0)) + (1 if e.elite else 0)), e.center() + Vector2(0, -10))
	if e.elite or randf() < Zorluk.sifa_dusme():
		drop_orb("sifa", e.center() + Vector2(0, -6))
	# parşömen: açılmamış bir eşyanın tarifi (seçkinlerden kesin, diğerlerinden seyrek)
	var locked := ItemGen.locked_implemented()
	if not locked.is_empty() and (e.elite or randf() < 0.07):
		drop_blueprint(locked[randi_range(0, locked.size() - 1)], e.center() + Vector2(0, -6))
	# v27 Sanat Tomarı: seçkinden %12 (açılmamış bir savaş sanatı kaldıysa)
	if e.elite and randf() < 0.12:
		drop_sanat_tomari("", e.center() + Vector2(0, -10))




func _v12_on_kill(e: Enemy) -> void:
	## Destanlar, don ruhu
	var pl := player
	var at := e.center()
	if Adlar.add_stat("kills_level") >= 40.0:
		Adlar.deed("salur_kazan", pl.center() if pl else at)
	if pl and float(Game.run["hp"]) < float(Game.run["max_hp"]) * 0.15:
		if Adlar.add_stat("low_kills") >= 5.0:
			Adlar.deed("deli_dumrul", pl.center())
	if e.elite:
		if pl and float(Game.run["hp"]) >= float(Game.run["max_hp"]) * 0.999:
			Adlar.deed("bogac", pl.center())
		# Don: seçkinin ruhu kalır; dokununca emilir, G ile onun kılığına girilir
		var d := Pickup.new()
		d.kind = "don"
		d.item_id = e.kind
		d.level = self
		d.position = at + Vector2(0, -18)
		add_child(d)
		pickups.append(d)


func _on_boss_died(e: Enemy) -> void:
	if boss_id == "tepegoz":
		Adlar.deed("basat", e.center())
	elif boss_id == "erlik_han":
		Adlar.deed("alp_er_tunga", e.center())
	Game.slowmo(0.25, 1.2)
	Game.shake(10.0)
	Game.zoom_punch(0.1)
	if has_method("flash_white"):
		flash_white(0.5)
	for i in 30:   # v24: 16 -> 30 tane; boss altını bir sonraki tüccara
		drop_orb("gold", e.center())
	for i in 10:
		drop_orb("kut", e.center())
	drop_orb("sifa", e.center() + Vector2(-20, -10))
	drop_item(ItemGen.random_drop(int(Game.run.get("tier", 0)) + 1), e.center() + Vector2(30, -10))   # v23: +2 -> +1
	drop_scroll(e.global_position + Vector2(-34, 0))   # v23: boss bir Kut Tomarı bırakır (zorluk.json tomar.boss)
	var locked := ItemGen.locked_implemented()
	if not locked.is_empty():
		drop_blueprint(locked[randi_range(0, locked.size() - 1)], e.center() + Vector2(0, -16))
	drop_sanat_tomari("", e.center() + Vector2(-56, -16))   # v27: boss bir Sanat Tomarı bırakır (açılmamış sanat kaldıysa)
	var bd: Array = Game.run.get("boss_done", [])
	bd.append(boss_id)
	Game.run["boss_done"] = bd
	FX.text(e.center() + Vector2(0, -e.size.y - 20), "%s DEVRİLDİ" % String(e.def.get("name", "")).to_upper(), Color(1.0, 0.85, 0.5), 14)
	if boss_id == "erlik_han":
		Game.meta["wins"] = int(Game.meta.get("wins", 0)) + 1
		Game.save_meta()
		FX.text(e.center() + Vector2(0, -e.size.y - 44), "GÜNEŞ YENİDEN DOĞUYOR", Color(1.0, 0.95, 0.6), 16)
		# v22 Kut Mühürleri: son boss bir sonraki zorluk kademesini açar (bir sonraki koşuda takılı gelir)
		if Zorluk.on_final_boss():
			FX.text(e.center() + Vector2(0, -e.size.y - 66), "YENİ KUT MÜHRÜ: %s" % Zorluk.muhur_adi(Zorluk.muhur_acik()).to_upper(), Color(0.95, 0.5, 0.35), 12)
	HikayeSahne.boss_dustu(self, e)   # v42: son söz + Gün Örgüsü
	boss = null
	boss_died.emit()
	get_tree().create_timer(1.6).timeout.connect(open_boss_gate)


# ------------------------------------------------------------------ v24 tüccar
## Tüccar alanının karo sınırları (tüccarın ayak karosuna göre): tezgâh solda 7 karo, tüccar ve sırt küfesi sağda 2
const BZ_SOL := -7
const BZ_SAG := 2
const BZ_BOS := 4          # tezgâhın üstünde boş kalması gereken karo
const BZ_SAPMA := 2        # düzlenebilecek en büyük yükselti farkı (karo)
const BZ_KAZI := 14        # düzlerken temizlenebilecek en çok katı karo (mağara tavanını oymasın)
var _bz_plan := -1         # planlanan tüccar karosu (-1: bu bölümde yok)
var _bz_y := -1            # tüccarın taban satırı (pazar odası)
var _bz_sebep := ""
var _bz_istek := false     # v32: üreticiden pazar odası istendi mi
var _bz_kapi := false      # boss öncesi: pazar çıkışa yakın kavşaktan ayrılsın


func _plan_bezirgan() -> void:
	## v24: Bezirgân Sartak bazı bölümlerde durur (data/tuccar.json "yer"). Boss öncesi bölümde (Game.BOSS_AFTER) kesin;
	## 1. derinlikte %35, diğerlerinde %55 şansla. v32: tezgâh artık düzlenen bir yüzey parçası değil, üreticinin açtığı
	## çıkmaz PAZAR odasıdır (LevelGen "pazar" ödülü; boss öncesinde çıkışa en yakın kavşaktan ayrılır). Burada yalnızca
	## istek kararı verilir; yer _place_rooms'taki "P" işaretinden gelir. Ayrı rng (bölüm tohumundan): bölümün geri
	## kalanı aynı kalır.
	_bz_plan = -1
	_bz_y = -1
	_bz_istek = false
	var cfg: Dictionary = Pazar.data().get("yer", {})
	var d := int(Game.run.get("depth", 1))
	var boss_once: bool = Game.BOSS_AFTER.has(d) and not (String(Game.BOSS_AFTER[d]) in Game.run.get("boss_done", []))
	_bz_kapi = boss_once
	var r := RandomNumberGenerator.new()
	r.seed = rng.seed + 7919
	if not boss_once and not bezirgan_zorla and not OS.get_cmdline_user_args().has("--tuccar_her"):
		var sans := float(cfg.get("ilk", 0.35)) if d <= 1 else float(cfg.get("sans", 0.55))
		if r.randf() >= sans:
			_bz_sebep = "şans"
			return
	_bz_istek = true
	_bz_sebep = "pazar odası açılmadı"


func bezirgan_alani(x: int, pay := 5) -> bool:
	## Tüccarın tezgâhı ve çevresi (v25: keşif ganimeti buraya konmaz)
	return _bz_plan >= 0 and x >= _bz_plan + BZ_SOL - pay and x <= _bz_plan + BZ_SAG + pay


func _place_bezirgan() -> void:
	## Planlanan yere (pazar odasının "P" işareti) tüccarı ve tezgâhı kur, mallarını yuvarla; tezgâhın üstüne düşmüş
	## ganimeti yana al, yakındaki sıradan yaratıkları kaldır (tezgâh sakin bir köşe).
	var d := int(Game.run.get("depth", 1))
	if _bz_plan < 0:
		print("[tuccar] derinlik=%d bezirgan=0 (%s)" % [d, _bz_sebep])
		return
	var boss_once: bool = Game.BOSS_AFTER.has(d) and not (String(Game.BOSS_AFTER[d]) in Game.run.get("boss_done", []))
	var tx := _bz_plan
	var ty := _bz_y if _bz_y >= 0 else surface_y(tx)
	bezirgan = Bezirgan.new()
	bezirgan.level = self
	bezirgan.position = Vector2(tx * TS + TS / 2.0, ty * TS)
	bezirgan.offers = Pazar.teklifler(d, boss_once)
	actors.add_child(bezirgan)
	Game.run["bezirgan_gordu"] = true   # v32: bu derinlikte pazar vardı; konağa gelmez
	var wr := bezirgan.world_rect()
	for p in pickups:
		if is_instance_valid(p) and wr.grow(20.0).has_point(p.position):
			var nx := wr.position.x - 40.0
			p.position = Vector2(nx, surface_y(int(floor(nx / TS)), ty - 2) * TS - (0.0 if p.kind == "tilsim" else 30.0))
	var temiz := float(Pazar.data().get("yer", {}).get("temiz", 9)) * TS
	var moved := 0
	for e in get_tree().get_nodes_in_group("dusman"):
		# v32: çok katlı bölüm: yalnızca tezgâhın katındakiler (üst / alt kattaki yaratıklar kalır)
		# v34: yalnızca pazar odasındakiler (yandaki ana yol odası kalabalık kalsın)
		if is_instance_valid(e) and not e.elite and absf(e.global_position.x - bezirgan.position.x) < temiz and absf(e.global_position.y - bezirgan.position.y) < 10.0 * TS and int(room_at(int(e.global_position.x / TS), int((e.global_position.y - 4.0) / TS)).get("id", -2)) == int(room_at(tx, ty - 1).get("id", -3)):
			e.queue_free()
			moved += 1
	print("[tuccar] derinlik=%d bezirgan=1 x=%d boss_oncesi=%s mal=%d duvar_ok=%s kaldirilan=%d" % [d, tx, str(boss_once), bezirgan.offers.size(), str(bezirgan_ok()), moved])


func bezirgan_ok() -> bool:
	## Denetim (test ve [tuccar] satırı): tezgâh + tüccar alanında katı karo yok, ayak altı boyunca zemin katı
	if bezirgan == null:
		return true
	var wr := bezirgan.world_rect()
	var y := wr.position.y
	while y < wr.end.y - 3.0:
		var x := wr.position.x
		while x <= wr.end.x:
			if cell(int(floor(x / TS)), int(floor(y / TS))) != 0:
				return false
			x += 6.0
		y += 6.0
	var x2 := wr.position.x
	while x2 <= wr.end.x:
		if not solid_at(Vector2(x2, wr.end.y + 4.0)):
			return false
		x2 += 6.0
	return true


func on_player_died() -> void:
	# v40: ölüm derecesi (renk çekilir, soğur, vinyet daralır; duraklatmada da sürer) ve kameranın yavaş yaklaşması
	Perde.olum(vig_mat)
	if camera is CameraV2:
		(camera as CameraV2).olum()
	await get_tree().create_timer(1.4).timeout
	player_died.emit()


# ------------------------------------------------------------------ v32 Kut Taşları, zamanlı kapılar, ışınlanma
func _kut_taslari() -> void:
	## Üreticinin seçtiği karolara Kut Taşı (KutTasi) diker, harita sisini kurar, zamanlı kapı düğümlerini açar
	harita = Harita.new()
	harita.setup(self)
	var i := 0
	for c in _gen.get("tasi", []):
		var cell_v: Vector2i = c
		var rm := room_at(cell_v.x, cell_v.y)
		var rol := String(rm.get("role", "ana"))
		var ad := "Kavşak Taşı"
		match rol:
			"giris":
				ad = "Yol Başı Taşı"
			"odul":
				ad = {"tomar": "Tomar Taşı", "hazine": "Hazine Taşı", "sunak": "Sunak Taşı", "pazar": "Pazar Taşı", "seckin": "Bekçi Taşı", "zamanli": "Zaman Taşı", "lanetli": "Lanet Taşı"}.get(String(rm.get("odul", "")), "Ödül Taşı")
			"cikis":
				ad = "Kapı Taşı"
		if rol == "ana" and bool(rm.get("kavsak", false)):
			ad = "%d. Kavşak Taşı" % (int(rm.get("ana_i", 0)))
		var ks := KutTasi.new()
		ks.level = self
		ks.idx = i
		ks.ad = ad
		ks.position = Vector2(cell_v.x * TS + TS / 2.0, (cell_v.y + 1) * TS)
		decor_root.add_child(ks)
		tasi.append(ks)
		harita.tasi_ekle(cell_v, ad, int(rm.get("id", -1)), rol)
		i += 1
	for z in _gen.get("zamanli", []):
		var zk := ZamanliKapi.new()
		zk.level = self
		zk.cell = Vector2i(int(z["x"]), int(z["y"]))
		zk.sure = float(z.get("sure", LevelGen.ZAMANLI_SURE))
		var rm2: Dictionary = rooms[int(z["room"])]
		zk.ic_yon = 1 if String(rm2.get("_door_side", "sol")) == "sol" else -1
		zk.oda = Rect2i(int(rm2["ix0"]) - 1, int(rm2["iy0"]) - 1, int(rm2["ix1"]) - int(rm2["ix0"]) + 3, int(rm2["iy1"]) - int(rm2["iy0"]) + 3)
		zk.position = Vector2(zk.cell.x * TS, zk.cell.y * TS)
		add_child(zk)
		zamanli.append(zk)
	harita.reveal(spawn_cell)


func tasi_yakin() -> int:
	## Oyuncunun dibinde durduğu Kut Taşı (yoksa -1)
	for t in tasi:
		if is_instance_valid(t) and t.near and t.bulundu:
			return t.idx
	return -1


func isinlan(i: int) -> bool:
	## Bulunmuş i. Kut Taşı'na ışınlanma kanalını başlat (ISIN_SURE; hasar bozar). false: olmaz (bulunmadı, ölü,
	## yakalanmış, zaten orada, kanal sürüyor)
	if harita == null or i < 0 or i >= harita.tasi.size() or not bool(harita.tasi[i]["bulundu"]):
		return false
	if player == null or player.dead or isin_t > 0.0 or player.grabbed_by != null or hub or boss_id != "":
		return false
	if tasi_yakin() == i:
		return false
	isin_t = ISIN_SURE
	isin_hedef = i
	isin_hp = float(Game.run.get("hp", 0.0))
	FX.ring(player.center(), 34, KutTasi.KUT, 0.5)
	FX.flash_light(player.center(), KutTasi.KUT, 160.0, 1.0, 0.4)
	Ses.play("kut_donusum", -8.0, 1.25)
	return true


func _isin_tick(delta: float) -> void:
	if isin_t <= 0.0 or player == null:
		return
	if player.dead or float(Game.run.get("hp", 0.0)) < isin_hp - 0.01 or player.grabbed_by != null:
		if isin_t <= 0.16:
			Perde.isin(false)   # v40: kapanmaya başlayan perde geri çekilir
		isin_t = 0.0
		isin_hedef = -1
		isin_bozuk += 1
		FX.text(player.center() + Vector2(0, -40), "Işınlanma bozuldu!", Color(1.0, 0.45, 0.4), 9)
		Ses.play("ui_iptal", -4.0)
		return
	var k := 1.0 - isin_t / ISIN_SURE
	var t_once := isin_t
	isin_t -= delta
	player.vis_scale = Vector2(1.0 - 0.25 * k, 1.0 + 0.35 * k)
	if int(isin_t * 30.0) % 4 == 0:
		FX.soul(player.center() + Vector2(randf_range(-10, 10), randf_range(-16, 8)), KutTasi.KUT, 2)
	# v40: kanalın son 0,16 sn'sinde mürekkep çözülmesi ekranı kaplar; varışta çekilir (kesme perdenin ardında kalır)
	if t_once > 0.16 and isin_t <= 0.16:
		Perde.isin(true)
	if isin_t <= 0.0:
		_isin_bitir()
		Perde.isin(false)


func _isin_bitir() -> void:
	var td: Dictionary = harita.tasi[isin_hedef]
	var c: Vector2i = td["cell"]
	var from := player.center()
	FX.burst(from, Color(0.1, 0.08, 0.12), 14, 110.0, 0.5, 0.3, 120.0, false)
	FX.soul(from, KutTasi.KUT, 22)
	FX.ring(from, 40, KutTasi.KUT, 0.45)
	player.global_position = Vector2(c.x * TS + TS / 2.0, (c.y + 1) * TS - 1.0)
	player.velocity = Vector2.ZERO
	player.last_safe = player.global_position
	player.inv_t = maxf(player.inv_t, ISIN_DOKUNULMAZ)
	player.vis_scale = Vector2(0.7, 1.3)
	if camera and camera.has_method("snap"):
		camera.snap()
	var to := player.center()
	FX.soul(to, KutTasi.KUT, 22)
	FX.ring(to, 44, KutTasi.KUT, 0.5)
	FX.flash_light(to, KutTasi.KUT, 260.0, 1.8, 0.45)
	FX.text(to + Vector2(0, -44), String(td["ad"]), KutTasi.KUT, 9)
	Ses.play("kut_donusum", -4.0, 0.9)
	harita.reveal(c)
	isin_sayi += 1
	isin_hedef = -1


## v23 etkileşim tuşu: W / ↑ (oyun kolunda yön yukarı ya da Back). Yukarı aynı zamanda ↑+J göğe savurmanın yönü
## olduğu için etkileşim kısa dokunuşun BIRAKILIŞINDA tetiklenir; tuş basılıyken saldırı, zıplama, yuvarlanma,
## teçhizat, şişe ya da Kut basılırsa (yerdeki eşyanın üstünde göğe savurma) iptal olur; 0,45 sn'den uzun basış da.
const ETKILES_BOZAN := ["saldiri1", "saldiri2", "zipla", "yuvarlan", "techizat1", "techizat2", "sise", "kut", "don"]
const ETKILES_SURE := 0.45
var _etk_t0 := -1.0
var _etk_bozuk := false


func _etkiles_tap() -> bool:
	if Input.is_action_just_pressed("etkiles"):
		_etk_t0 = Game.clock()
		_etk_bozuk = false
	if _etk_t0 < 0.0:
		return false
	for a in ETKILES_BOZAN:
		if Input.is_action_pressed(a):
			_etk_bozuk = true
	if not Input.is_action_pressed("etkiles"):
		var ok := not _etk_bozuk and Game.clock() - _etk_t0 <= ETKILES_SURE
		_etk_t0 = -1.0
		return ok
	return false


func _process(_delta: float) -> void:
	if Prof.on:
		var t0 := Time.get_ticks_usec()
		_process_ic(_delta)
		Prof.ekle(&"bolum", t0)
		return
	_process_ic(_delta)


func _process_ic(_delta: float) -> void:
	_isik_tick()   # v40: sis bandı / hüzme kayması (yurt ve konakta da)
	# v25: kapının kemeri boyunca (yerden 96 px yukarıya dek) geçmek yeter: zıplayarak kapının içinden geçen oyuncu
	# (eskiden yalnızca ayak noktası 30 px yakınsa) kapıyı kaçırıp bölüm sonundaki duvara takılmaz
	var dpe: Vector2 = player.global_position - exit_pos if player else Vector2(999, 999)
	if player and not _done and absf(dpe.x) < 30.0 and dpe.y < 12.0 and dpe.y > -96.0 and (boss_id == "" or boss_gate_open):
		_done = true
		Ses.play("kapi")
		finished.emit()
	if player and not player.dead:
		Game.run["time"] = float(Game.run.get("time", 0.0)) + _delta
		var tap := _etkiles_tap()
		if hub or konak:
			# v24: Demirci'nin dövdüğü eşya yurtta yerde durur: yakınsa önce o alınır, yoksa NPC ile konuşulur
			# v32: konakta da (Bezirgân'ın kilimine düşen mal; Usta ve Sartak)
			if konak:
				_konak_tick()
			var hp_item := nearest_item(player.global_position + Vector2(0, -10))
			if hp_item and tap and hp_item.kind == "item":
				try_equip(hp_item)
				return
			if hp_item and tap and hp_item.kind == "tilsim":
				scroll_requested.emit(hp_item)
				return
			var n := nearest_npc()
			if n and tap:
				n.talk()
				npc_requested.emit(n.id)
			elif tap and bezirgan != null and bezirgan.near:
				bezirgan.talk()
				tuccar_requested.emit()
			return
		var p := nearest_item(player.global_position + Vector2(0, -10))
		if p and tap:
			if p.kind == "tilsim":
				scroll_requested.emit(p)
			elif p.kind == "lutuf":
				lutuf_requested.emit(p)
			else:
				try_equip(p)
		elif tap and bezirgan != null and bezirgan.near:
			bezirgan.talk()
			tuccar_requested.emit()
		elif tap and otag_yakin() != null:
			otag_gir(otag_yakin())   # v42 sınav otağı
		elif tap and sandik_yakin() != null:
			sandik_yakin().ac()   # v34 lanetli sandık
		elif tap and tasi_yakin() >= 0 and isin_t <= 0.0:
			harita_requested.emit()   # v32: Kut Taşı'nın dibinde W: harita (hızlı ışınlanma)
		# v32: harita sisi, zamanlı kapı süresi, ışınlanma kanalı
		if harita != null:
			harita.tick(_delta, player.global_position)
		Game.run["bolum_sure"] = float(Game.run.get("bolum_sure", 0.0)) + _delta
		if sinav != null:
			sinav.tick(_delta)   # v42
		_isin_tick(_delta)
	_hazard_tick(_delta)


# ------------------------------------------------------------------ v42 sınavlar ve otağlar
## Sinav (scripts/core/Sinav.gd): üç mühür; OtagYeri (yerleşim, Çabuk süresi); Otag (otağ düğümü); OtagIc (otağ içi).
var sinav: Sinav
var otaglar: Array = []        # Otag düğümleri (Kut Kapısı'na yakından uzağa: han, cabuk, dokunulmaz, avci)
var otag_yerleri: Array = []   # OtagYeri.yerlesim sonucu
var otag_ic: Node              # açık otağ içi (OtagIc; test)


func _sinav_kur() -> void:
	sinav = Sinav.new()
	var avoid: Array = []
	for c in _gen.get("tasi", []):
		avoid.append(c)
	for kc in kaide_xs:
		avoid.append(Vector2i(int(kc.x), int(kc.y)))
	for z in _gen.get("zamanli", []):
		avoid.append(Vector2i(int(z["x"]), int(z["y"]) - 1))
	for ch in chunks:
		for mk in ch.get("marks", []):
			avoid.append(Vector2i(int(mk[1]), int(mk[2])))
	if bezirgan != null:
		# Bezirgân'ın tezgâhı ve kilimi (bezirgan_alani) otağsız kalır
		var bc := Vector2i(int(floor(bezirgan.global_position.x / TS)), int(floor(bezirgan.global_position.y / TS)) - 1)
		for dx in range(-8, 9, 2):
			avoid.append(bc + Vector2i(dx, 0))
	var gen_avoid := avoid.duplicate()
	for p in pickups:
		if is_instance_valid(p):
			avoid.append(Vector2i(int(floor(p.position.x / TS)), int(floor(p.position.y / TS))))
	for n in sandiklar + kilitler:
		if is_instance_valid(n):
			avoid.append(Vector2i(int(floor(n.position.x / TS)), int(floor(n.position.y / TS)) - 1))
	otag_yerleri = _otag_yer_sec(avoid)
	if otag_yerleri.size() < 4:
		# yerdeki ganimet otağ yerini kapattıysa: üreticinin işaretleri dışındakiler otağın önünde kalabilir
		var y2 := _otag_yer_sec(gen_avoid)
		if y2.size() > otag_yerleri.size():
			otag_yerleri = y2
	sinav.kur(self, rng)
	var turler: Array = OtagYeri.SIRA if otag_yerleri.size() >= 4 else ["cabuk", "dokunulmaz", "avci"]
	for i in mini(otag_yerleri.size(), turler.size()):
		var y: Dictionary = otag_yerleri[i]
		var o := Otag.new()
		o.level = self
		o.tur = String(turler[i])
		o.cell = Vector2i(int(y["x"]), int(y["y"]))
		o.position = Vector2(o.cell.x * TS + TS / 2.0, (o.cell.y + 1) * TS)
		decor_root.add_child(o)
		otaglar.append(o)
	print("[otag] yer=%d otağ=%d par=%d sn (yol %.1f sn) av=%s (%s x%d)" % [otag_yerleri.size(), otaglar.size(), int(sinav.par), sinav.yol_sn, sinav.av_mod, sinav.av_tur, sinav.av_gerek])


func _otag_yer_sec(avoid: Array) -> Array:
	var r := OtagYeri.yerlesim(grid, W, H, rooms, exit_cell, avoid)
	if bezirgan != null:
		r = r.filter(func(y: Dictionary) -> bool: return not bezirgan_alani(int(y["x"]), 4))
	return r


func otag_yerinde() -> bool:
	## Otağ Yeri'ne varıldı mı: bir otağın 2,5 karo yanı ya da Kut Kapısı'nın 7 karo önü (aynı kat)
	if player == null:
		return false
	var p := player.global_position
	for o in otaglar:
		if absf(p.x - o.position.x) < 2.5 * TS and absf(p.y - o.position.y) < 3.0 * TS:
			return true
	return absf(p.x - exit_pos.x) < 7.0 * TS and absf(p.y - exit_pos.y) < 4.0 * TS


func otag_yakin() -> Otag:
	for o in otaglar:
		if is_instance_valid(o) and o.near:
			return o
	return null


func otag_gir(o: Otag) -> bool:
	## Açık ve alınmamış otağa gir (OtagIc); kapalıysa kısa açıklama. true: girildi
	if o == null or (otag_ic != null and is_instance_valid(otag_ic)):
		return false
	if not o.acik():
		var d := o.durum()
		var msg := "Mühür çatladı: otağ kapalı" if d == -1 else ("Kapalı · " + sinav.aciklama(o.tur))
		FX.text(o.global_position + Vector2(0, -78), msg, Color(0.8, 0.76, 0.7), 8)
		Ses.play("ui_iptal", -6.0)
		return false
	if o.alindi:
		FX.text(o.global_position + Vector2(0, -78), "Otağ boş", Color(0.8, 0.76, 0.7), 8)
		return false
	o.alindi = true
	var d2 := int(Game.run.get("depth", 1))
	var od := Sinav.odul(o.tur, d2, int(Game.run.get("tier", 0)), rng)
	if o.tur != "han" and sinav.hepsi() and not _han_otagi_var() and not _han_verildi:
		# Han Otağı'na yer çıkmadıysa (dar bölüm) onun ödülü ilk açılan otağa katılır
		_han_verildi = true
		var hn := Sinav.odul("han", d2, int(Game.run.get("tier", 0)), rng)
		od["altin"] = int(od["altin"]) + int(hn["altin"])
		od["kut"] = int(od["kut"]) + int(hn["kut"])
		(od["items"] as Array).append_array(hn["items"])
	var cl := CanvasLayer.new()
	cl.layer = 12
	cl.process_mode = Node.PROCESS_MODE_ALWAYS
	add_child(cl)
	var ic := OtagIc.new()
	ic.level = self
	ic.otag = o
	ic.odul = od
	cl.add_child(ic)
	otag_ic = ic
	return true


var _han_verildi := false


func _han_otagi_var() -> bool:
	for o in otaglar:
		if o.tur == "han":
			return true
	return false


func otag_odul_ver(o: Otag, od: Dictionary) -> void:
	## Otağ sandığının ödülü: altın ve Kut doğrudan, eşya / tomar / parşömen otağın kapısına
	var at := o.global_position
	if int(od.get("altin", 0)) > 0:
		Game.run["gold"] = int(Game.run.get("gold", 0)) + int(od["altin"])
		Game.run["altin_kazanc"] = int(Game.run.get("altin_kazanc", 0)) + int(od["altin"])
		Ses.play("altin", -4.0)
	if int(od.get("kut", 0)) > 0:
		Game.run["kut"] = int(Game.run.get("kut", 0)) + int(od["kut"])
		if player:
			player.add_kut(2.0 * float(od["kut"]))
	var dx := -16.0
	for it in od.get("items", []):
		drop_item(it, at + Vector2(dx, -30))
		dx += 32.0
	if int(od.get("tomar", 0)) > 0:
		drop_scroll(at + Vector2(dx, 0))
		dx += 32.0
	if String(od.get("parsomen", "")) != "":
		drop_blueprint(String(od["parsomen"]), at + Vector2(dx, -10))
	FX.ring(at + Vector2(0, -20), 40, Sinav.RENK.get(o.tur, Color(1, 0.85, 0.45)), 0.5)
	o.tazele()


func otag_tazele() -> void:
	for o in otaglar:
		if is_instance_valid(o):
			o.tazele()
