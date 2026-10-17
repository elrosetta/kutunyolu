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

const TS := 24
const W := 230
const H := 44

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
var npcs: Array = []
var decal_root: Node2D
var hazard: TileMapLayer
var haz_kind := ""
var _haz_frame := 0
var _haz_t := 0.0
var boss_id := ""
var boss: Enemy
var boss_gate_open := false
var alem: Alem  # v12 Üç Âlem
const HUB_W := 92
var red_rect: ColorRect
var vig_mat: ShaderMaterial  # vinyet; hasar nabzı "hurt" parametresiyle
var _light_tex: GradientTexture2D
var _done := false
var _hub_floor: Node2D
var moon: DirectionalLight2D  # ay: yönlü ışık + arazi gölgeleri (GroundShadow kayma yönünü buradan okur)
var moon_shadow := 0.72  # ay gölgesindeki aktörde ay ışığının giden payı (toon_light moon_shade üst sınırı)
var _shadow_dir := Vector2(0, 1)  # ay ışığının gidiş yönü (karo engelleyicileri bu yöne göre seçilir)


func build(seed_value: int) -> void:
	rng.seed = seed_value
	biome = Game.biome_for_depth(int(Game.run.get("depth", 1)))
	art = _stil_art(biome.get("art", {}))
	Game.run["biome"] = biome.get("id", "otuken")
	_generate()
	# v12: gizli yeraltı odaları karolar kurulmadan oyulur; bölüm başı destan sayaçları
	alem = Alem.new()
	alem.level = self
	alem.carve()
	Game.run["dumrul_used"] = false
	for k in ["kills_level", "bow_level", "low_kills"]:
		Adlar.set_stat(k, 0.0)
	Ses.alem_mix = ""
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
	_build_hazards()
	_place_decor()
	_spawn_player()
	_spawn_enemies()
	_spawn_items()
	_spawn_scrolls()
	_place_rooms()
	add_child(alem)
	alem.populate()
	_build_particles()
	_build_overlay_fx()
	Ses.music(biome.get("id", "otuken"))


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
	if ink():
		_place_towers()
		if art.has("boss_extras"):
			_place_ink_extras_spec(art["boss_extras"])
	_spawn_player()
	camera.limit_right = 84 * TS
	# boss: sağdan, uzak
	var en := Enemy.new()
	var bx := 64
	boss = Boss.new()
	boss.setup(String(bdef.get("enemy", bid_boss)), false, int(Game.run.get("tier", 0)))
	boss.max_hp = float(bdef.get("hp", boss.def.get("hp", 900))) * (1.0 + 0.35 * float(Game.run.get("tier", 0)))
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
	var hp := Data.pack_scale("res://assets/tiles/hazards.png")
	# stil v2 mürekkep: biyoma özgü tehlike dokusu (hazards_<biyom>_v2.png; tools/artgen/ink_tehlike.py) varsa o,
	# yoksa biyomdan bağımsız mürekkep karoları (hazards_v2.png; tools/artgen/sus_ink.py); 4 doku pikseli / dünya birimi
	var hz2 := "res://assets/tiles/hazards_%s_v2.png" % String(biome.get("id", ""))
	# stil v2 sıvı havuzu (Şahmeran zehri, Tamu lavı: _build_hazards_ink) kendi ışıklarını kurar
	var liquid := ink() and art.has("hazard_v2") and ResourceLoader.exists("res://assets/tiles/hazard_%s_v2.png" % haz_kind)
	var v2h := ink() and ResourceLoader.exists(hz2)
	var hv2 := not v2h and Data.stil == "v2" and ResourceLoader.exists("res://assets/tiles/hazards_v2.png")
	var hv2_path := hz2 if v2h else "res://assets/tiles/hazards_v2.png"
	if v2h or hv2:
		hp = 4 * Data.pack_scale(hv2_path)   # 4 doku pikseli / dünya birimi; HD paketinde 8 (TileSet gerçek boyutu kullanır)
	var ts := TileSet.new()
	ts.tile_size = Vector2i(TS * hp, TS * hp)
	var src := TileSetAtlasSource.new()
	if v2h or hv2:
		var hct := CanvasTexture.new()
		hct.diffuse_texture = Data.tex_full(hv2_path)
		hct.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
		src.texture = hct
	else:
		src.texture = _atlas_tex("res://assets/tiles/hazards.png", "res://assets/tiles/hazards_n.png")
	src.texture_region_size = Vector2i(TS * hp, TS * hp)
	ts.add_source(src, 0)
	for r in 4:
		for c in 2:
			src.create_tile(Vector2i(c, r))
	hazard = TileMapLayer.new()
	hazard.tile_set = ts
	hazard.scale = Vector2.ONE / float(hp)
	var m := ShaderMaterial.new()
	m.shader = Game.toon_shader
	if hv2:
		m.shader = load("res://shaders/env_ink.gdshader")
		m.set_shader_parameter("moon_gain", float(art.get("ground_moon_gain", 0.6)))
		hazard.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	hazard.material = m
	if v2h:
		hazard.material = _ink_mat()
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
		var gc := TS * (4 if hv2 else 1)
		ts2.tile_size = Vector2i(gc, gc)
		var src2 := TileSetAtlasSource.new()
		src2.texture = load("res://assets/tiles/hazards_v2_e.png" if hv2 else "res://assets/tiles/hazards_e.png")
		src2.texture_region_size = Vector2i(gc, gc)
		ts2.add_source(src2, 0)
		for r in 4:
			for c in 2:
				src2.create_tile(Vector2i(c, r))
		glow.tile_set = ts2
		glow.scale = Vector2.ONE * (float(hp) / 4.0 if hv2 else float(hp))  # ebeveyn (HD) katmanın küçültmesini dengele: parlama temel boyutlu
		if hv2:
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
	if ink():
		_build_hazards_ink()


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
				var tw := l.create_tween().set_loops()
				tw.tween_property(l, "energy", l.energy * 0.75, randf_range(0.5, 0.9))
				tw.tween_property(l, "energy", l.energy, randf_range(0.5, 0.9))


func hazard_at(p: Vector2) -> String:
	var x := int(floor(p.x / TS))
	var y := int(floor(p.y / TS))
	if x < 0 or x >= W or y < 0 or y >= H:
		return ""
	return haz_kind if grid[idx(x, y)] == 3 else ""


func ice_at(p: Vector2) -> bool:
	return haz_kind == "buz" and hazard_at(p) == "buz"


func _place_rooms() -> void:
	## Oda işaretleri: sunak (lütuf), hazine kaidesi, seçkin, kurgan ganimeti
	for ch in chunks:
		var nm: String = ch["name"]
		var x0: int = ch["x"]
		var rows: Array = LevelGen.CHUNKS.get(nm, [])
		var base: int = heights[clampi(x0 + 6, 0, W - 1)] if nm != "zehir_cukuru" else 0
		for r in rows.size():
			var line: String = rows[r]
			for cidx in line.length():
				var chr := line[cidx]
				if chr in ["S", "T", "E"]:
					var tx := x0 + cidx
					var ty := _ground_tile_y(tx)
					match chr:
						"S":
							_decor("sunak", tx, ty, -1, true)
							var p := Pickup.new()
							p.kind = "lutuf"
							p.level = self
							p.position = Vector2(tx * TS + TS / 2.0, ty * TS)
							add_child(p)
							pickups.append(p)
						"T":
							var it := ItemGen.random_drop(int(Game.run.get("tier", 0)) + 1)
							drop_item(it, Vector2(tx * TS + 12, ty * TS - 30), true)
							for g in 6:
								drop_orb("gold", Vector2(tx * TS + 12 + randf_range(-20, 20), ty * TS - 20))
						"E":
							var pool := _biome_pool()
							var kind: String = pool[rng.randi_range(0, pool.size() - 1)]
							spawn_enemy(kind, Vector2(tx * TS + TS / 2.0, ty * TS - 1), true)


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
	# v13: yurda özel paralaks: kutsal gece göğü, dağların ardında Ulu Kayın (Bai-Terek), uzak oba, yakın fenerli sırt
	art["bg"] = ["yurt_0_sky", "yurt_1_tree", "yurt_2_camp", "yurt_3_mid", "otuken_5_fog"]
	art["bg_fx"] = [[0.0, 0.0, 0.0], [0.03, 0.02, 0.0], [0.16, 0.08, 0.0], [0.36, 0.16, 0.0], [0.5, 0.22, 7.0]]
	art["rays"] = [0.55, 0.95, 0.88, 0.05]
	Game.run["biome"] = "yurt"
	_generate_hub()
	if ink() and FileAccess.file_exists("res://data/yurt_v2.json"):
		# stil v2: mürekkep yurdu (gece göğü, kuzey ışıkları, Ulu Kayın; süsler sus_v2.json, v2 kamerası)
		var yv2: Dictionary = Data.load_json("res://data/yurt_v2.json")
		for k in yv2:
			if not String(k).begins_with("_"):
				art[k] = yv2[k]
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
	_spawn_player()
	camera.limit_right = HUB_W * TS
	_build_particles()
	_build_overlay_fx()
	Ses.music("yurt")
	if OS.get_cmdline_user_args().has("--yurt-tur"):
		var tour: Node = load("res://tools/tests/yurt_turu.gd").new()
		tour.set("level", self)
		add_child(tour)


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
	var defs := [["umay", "Umay Ana", 30], ["demirci", "Demirci Kam Kuzgun", 47], ["ozan", "Ozan Bilge Kopuz", 61]]
	for d in defs:
		var n := NPC.new()
		n.id = d[0]
		n.display_name = d[1]
		n.level = self
		n.position = Vector2(int(d[2]) * TS + TS / 2.0, surface_y(int(d[2])) * TS)
		actors.add_child(n)
		npcs.append(n)
	# çıkış: Kut Kapısı
	exit_pos = Vector2(ex * TS + TS / 2.0, surface_y(ex) * TS)
	var gate := KutGate.new()
	gate.position = exit_pos
	if ink() and not _decor_v2("yh_kapi").is_empty():
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
	## Yurt süsü: decor.json'daki "k" yoğunluğuna göre ölçeklenir (1.5x çizim → 2/3 ölçek).
	## Stil v2 mürekkep zemininde "<ad>_v2" (sus_v2.json, doku pikseli / dünya birimi "texel") kullanılır.
	if ink():
		var d2 := _decor_v2(dname)
		if not d2.is_empty():
			return _hub_prop_ink(d2, dname, tx, z, flip, parent, dy, glow)
	var d := Data.decor(dname)
	if d.is_empty() or not d.has("size"):
		return null
	var k := float(d.get("k", 1.0))
	var s := Sprite2D.new()
	s.texture = d["tex"]
	s.centered = false
	s.offset = Vector2(-float(d["origin"][0]), -float(d["origin"][1]))
	s.scale = Vector2(-1.0 if flip else 1.0, 1.0) / k
	s.position = _hub_px(tx, dy)
	var m := ShaderMaterial.new()
	m.shader = Game.toon_shader
	var dt: Array = art.get("decor_tint", [0.86, 0.84, 0.9])
	m.set_shader_parameter("tint", Color(dt[0], dt[1], dt[2]))
	s.material = m
	s.z_index = z
	(parent if parent else decor_root).add_child(s)
	if d.get("glow_tex") != null:
		var g := Sprite2D.new()
		g.texture = d["glow_tex"]
		g.centered = false
		g.offset = s.offset
		var gm := CanvasItemMaterial.new()
		gm.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
		gm.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
		g.material = gm
		g.self_modulate = glow
		s.add_child(g)
	return s


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
		var fast := dname in ["yh_mangal", "yh_kandil", "yh_kazan", "yh_kapi", "yh_sunak", "yh_demirhane", "yh_ors"]
		tw.tween_property(g, "self_modulate:a", 0.78, rng.randf_range(0.14, 0.2) if fast else 1.6)
		tw.tween_property(g, "self_modulate:a", 1.0, rng.randf_range(0.16, 0.24) if fast else 1.8)
	return s


func _hub_fire(pos: Vector2, col: Color, radius: float, energy: float, embers := true) -> void:
	## Titreyen sıcak ışık + yukarı süzülen kor.
	var l := add_light(pos, col, radius, energy, decor_root)
	var tw := l.create_tween().set_loops()
	tw.tween_property(l, "energy", energy * 0.82, rng.randf_range(0.14, 0.22))
	tw.tween_property(l, "energy", energy * 1.08, rng.randf_range(0.16, 0.26))
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
	var fl := add_light(_hub_px(50.7, -10), Color(1.0, 0.45, 0.16), 230.0, 1.5, decor_root)
	var tw := fl.create_tween().set_loops()
	tw.tween_property(fl, "energy", 1.15, 0.5).set_trans(Tween.TRANS_SINE)
	tw.tween_property(fl, "energy", 1.6, 0.6).set_trans(Tween.TRANS_SINE)
	# kazan ateşi
	_hub_fire(_hub_px(75.3, -6), warm, 150.0, 1.0)
	# kut: pınar ve dilek kayını (soğuk turkuaz)
	add_light(_hub_px(22.0, -80), Color(0.45, 0.98, 0.95), 270.0, 0.85, decor_root)
	# taç kapının kandilleri (kapının turkuaz ışığı _place_hub'da)
	_hub_fire(_hub_px(HUB_W - 7, -60), warm, 230.0, 0.9)


func _hub_string(a: Vector2, b: Vector2, sag: float, lanterns: bool, z := -5) -> void:
	## İki direk arasında sarkık ip: renkli üçgen bayrakçıklar ya da küçük kehribar fenerler.
	## Bütün bayrakçıklar tek Polygon2D'de (köşe renkli çokgenler): bir çizim çağrısı.
	var inkv2 := ink()
	var line := Line2D.new()
	line.width = 1.0
	line.default_color = Color(0.16, 0.12, 0.1)
	if inkv2:
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
	if inkv2:
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
	pg.antialiased = inkv2
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
	var r := LevelGen.generate(rng, W, H, int(Game.run.get("depth", 1)), art.get("styles", []))
	grid = r["grid"]
	heights = r["heights"]
	style = r["style"]
	chunks = r["chunks"]
	carved = int(r.get("carved", 0))


# ------------------------------------------------------------------ karolar
func _art_cell() -> int:
	## Atlas hücresi (doku pikseli). Zemin dokuları 1.5 kat yoğun üretilir (36 px) ve karo katmanları
	## TS / hücre oranında küçültülür: dünya ölçüleri (TS = 24) ve fizik değişmez, 1080p'de her doku
	## pikseli 2x2 ekran pikseline düşer. v2 mürekkep zemini 48 px (1080p'de 1:1).
	return int(_tmeta().get("tile", TS))


var _tile_meta_cache: Dictionary = {}


func _tmeta() -> Dictionary:
	## Karo atlası meta bilgisi: v1'de ortak otuken.json (Data.tile_meta); --stil=v2'de varsa "<biyom>_v2.json"
	## (hücre boyu, "ink": mürekkep zemini, "filter": doğrusal süzgeç). Yerleşim (sütun/satır) her ikisinde aynı.
	if _tile_meta_cache.is_empty():
		var tid := _tile_id()
		var jp := "res://assets/tiles/%s.json" % tid
		if tid.ends_with("_" + Data.stil) and FileAccess.file_exists(jp):
			_tile_meta_cache = Data.load_json(jp)
		if _tile_meta_cache.is_empty():
			_tile_meta_cache = Data.tile_meta
	return _tile_meta_cache


func ink() -> bool:
	## Stil v2 "mürekkep" ortamı etkin mi (el çizimi, doğrusal süzgeçli zemin; tools/artgen/otuken_ink*.py)
	return bool(_tmeta().get("ink", false))


func _stil_art(base: Dictionary) -> Dictionary:
	## Görsel stil v1 dışındaysa data/stil_<stil>.json içindeki biyom girdisi art değerlerini ezer
	## (paralaks katman listesi, ışık, ön plan, renk derecelendirme). v1'de art olduğu gibi döner.
	var a := base.duplicate(true)
	if Data.stil == "v1":
		return a
	var path := "res://data/stil_%s.json" % Data.stil
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


func _atlas_tex(path: String, normal: String) -> CanvasTexture:
	## Karo atlası: paket varsa gerçek boyutlu HD doku + temel normal map (UV ile örneklenir)
	var ct := CanvasTexture.new()
	ct.diffuse_texture = Data.tex_full(path)
	if ink():
		# v2 mürekkep: normal yuvasında toprak kaplama maskesi (ground_ink.gdshader), doğrusal süzgeç + mipmap.
		# HD paketinde maske de 2 kat (CanvasTexture normal yuvası atlasla aynı boyda olmalı, yoksa karolar kayar)
		ct.normal_texture = _same_size(Data.tex_full("res://assets/tiles/%s" % String(_tmeta().get("mask", ""))), ct.diffuse_texture)
		ct.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
		return ct
	if ResourceLoader.exists(normal):
		ct.normal_texture = _same_size(load(normal), ct.diffuse_texture)
	ct.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	return ct


func _same_size(t: Texture2D, ref: Texture2D) -> Texture2D:
	## Karo atlasıyla aynı TileSet'te kullanılan yardımcı doku (maske, normal, ışıma) atlasla aynı boyda olmalı. Pakette
	## HD karşılığı yoksa (eski v1 paketi, temel doku sonradan değişti) çalışma anında atlas boyuna büyütülür (yumuşak
	## veri dokuları; çizim ayrıntısı yok).
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
	## Karo/toprak dosya kimliği: biyom kimliği, --stil=v2 ise varsa "<biyom>_v2" (Data.stil_id)
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
	src.texture = _atlas_tex("res://assets/tiles/%s.png" % bid, "res://assets/tiles/%s_n.png" % bid)
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
	if ink():
		_build_tiles_ink()
		return
	var ts := _make_tileset()
	var gmat := ShaderMaterial.new()
	gmat.shader = load("res://shaders/ground.gdshader")
	var bid2: String = _tile_id()
	# toprak dokusu: paket varsa yüksek çözünürlüklü (shader dünya ızgarasından gerçek doku boyutuyla okur)
	var soil_path := "res://assets/tiles/%s_soil.png" % bid2
	var soil_k := Data.pack_scale(soil_path)
	gmat.set_shader_parameter("soil_tex", Data.tex_full(soil_path))
	gmat.set_shader_parameter("soil_n", load("res://assets/tiles/%s_soil_n.png" % bid2))
	var dc: Array = art.get("deep_color", [0.04, 0.03, 0.06])
	gmat.set_shader_parameter("deep_color", Color(dc[0], dc[1], dc[2]))
	gmat.set_shader_parameter("depth_tex", _depth_texture())
	gmat.set_shader_parameter("map_size_px", Vector2(W * TS, H * TS))
	gmat.set_shader_parameter("soil_density", float(_art_cell()) / TS * float(soil_k))
	var emis_path := "res://assets/tiles/%s_soil_e.png" % bid2
	if ResourceLoader.exists(emis_path):
		gmat.set_shader_parameter("soil_e", load(emis_path))
	var bmeta: Dictionary = Data.load_json("res://assets/tiles/%s.json" % bid2)
	var gc = bmeta.get("glow")
	if gc is Array and (gc as Array).size() >= 3:
		gmat.set_shader_parameter("glow_col", Color(gc[0], gc[1], gc[2]))
	var tmat := ShaderMaterial.new()
	tmat.shader = Game.toon_shader
	_lay_tiles(ts, gmat, tmat)


func _build_tiles_ink() -> void:
	## Stil v2 mürekkep zemini: sanat + kaplama maskesi atlası, dünya uzayı toprak (ground_ink.gdshader);
	## örtü katmanı (ot öbekleri, kökler) env_ink.gdshader. Karo/çarpışma düzeni v1 ile birebir aynı.
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


func surface_y(x_tile: int) -> int:
	## Yürünen zemin: tabanın (heights) 8 karo altından yukarı tarayıp ilk "üstü hava, kendisi katı" karo.
	## Çukurlarda çukur tabanını, mağarada tavanı değil zemini, düz yerde tabanı verir.
	var xt := clampi(x_tile, 0, W - 1)
	var y := mini(H - 1, int(heights[xt]) + 8)
	while y > 1:
		if cell(xt, y) != 0 and cell(xt, y - 1) == 0:
			return y
		y -= 1
	return H - 1


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
		g.set_color(0, Color(1, 1, 1, 1))
		g.set_color(1, Color(1, 1, 1, 0))
		g.add_point(0.45, Color(1, 1, 1, 0.45))
		_light_tex.gradient = g
	return _light_tex


func add_light(pos: Vector2, col: Color, radius: float, energy := 1.0, parent: Node = null, shadows := false) -> PointLight2D:
	## shadows: arazi gölgesi düşürür (her gölgeli nokta ışığı kadrajdaki engelleyicileri 4 yöne çizer;
	## yalnızca büyük, sabit ışıklar için: süs çıraları, ocak, Kut Kapısı). Büyük sabit süs ışıkları
	## (decor_root altı, yarıçap >= 200) kendiliğinden gölgeli olur.
	var l := PointLight2D.new()
	l.texture = light_tex()
	l.texture_scale = radius / 64.0
	l.color = col
	l.energy = energy
	l.height = 26.0
	l.position = pos
	if shadows or (parent == decor_root and decor_root != null and radius >= 200.0):
		l.shadow_enabled = true
		l.shadow_filter = Light2D.SHADOW_FILTER_NONE
		l.shadow_color = Color(0.05, 0.04, 0.08, 0.8)
		l.shadow_item_cull_mask = 1
	(parent if parent else self).add_child(l)
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
	bg.smooth = ink()
	var rc: Array = art.get("rays", [0.62, 0.8, 1.0, 0.07])
	bg.ray_color = Color(rc[0], rc[1], rc[2], rc[3])
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
	var lt := GradientTexture2D.new()
	lt.width = 3
	lt.height = 2
	leaves.texture = lt if not ink() else InkDraw.particle("yaprak")  # v2: 3x2 piksel yerine fırça yaprak
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
	if ink() and art.has("leaf_tex"):
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
			if not (ink() and art.has("leaf_ramp")):
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
	if ink() and art.has("drip_tex"):
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
	if ink() and not OS.get_cmdline_user_args().has("--derecesiz"):
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
	vig.material = sm
	vig_mat = sm
	cl.add_child(vig)
	red_rect = ColorRect.new()
	red_rect.set_anchors_preset(Control.PRESET_FULL_RECT)
	red_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	red_rect.color = Color(1, 0.1, 0.1, 0.0)
	cl.add_child(red_rect)
	if ink() and art.has("fg"):
		var fg := ForegroundV2.new()
		fg.spec = art["fg"]
		fg.level = self
		add_child(fg)


func flash_red() -> void:
	## Hasar: kenarlardan kısa kırmızı vinyet nabzı (eskiden tüm ekran düz kırmızı boyanıyordu; karanlık
	## biyomlarda sahneyi kapatıyordu). Vuruş duraklaması/ağır çekim uzatmaz.
	if vig_mat == null:
		return
	vig_mat.set_shader_parameter("hurt", 0.9 * maxf(0.4, Game.fx_scale))
	var tw := create_tween()
	tw.set_ignore_time_scale(true)
	tw.tween_method(func(v: float) -> void: vig_mat.set_shader_parameter("hurt", v), 0.9 * maxf(0.4, Game.fx_scale), 0.0, 0.35)


# ------------------------------------------------------------------ süsler
var _decor_v2_meta: Dictionary = {}
var _decor_v2_tex: Dictionary = {}


func _decor_v2(dname: String) -> Dictionary:
	## Stil v2 mürekkep süsü: assets/decor/<ad>_v2.png (+ _e ışıma), decor_v2.json (boyut/köken doku pikseli,
	## "texel" = dünya birimi başına doku pikseli). Yoksa boş sözlük (v1 süsü kullanılır).
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
		var tw2 := l.create_tween().set_loops()
		tw2.tween_property(l, "energy", 1.1, 0.18)
		tw2.tween_property(l, "energy", 1.45, 0.22)
	return s


func _decor(dname: String, tile_x: int, tile_y_surface: int, z := -2, glow_light := false) -> void:
	if ink():
		var d2 := _decor_v2(dname)
		if not d2.is_empty():
			_decor_ink(d2, dname, tile_x, tile_y_surface, z, glow_light)
			return
	var d := Data.decor(dname)
	if d.is_empty() or not d.has("size"):
		return
	var s := Sprite2D.new()
	s.texture = d["tex"]
	s.centered = false
	s.offset = Vector2(-float(d["origin"][0]), -float(d["origin"][1]))
	s.position = Vector2(tile_x * TS + TS / 2.0 + rng.randf_range(-4, 4), tile_y_surface * TS + 2)
	var m := ShaderMaterial.new()
	m.shader = Game.toon_shader
	# süs tonu biyoma göre (ateş ve mantar hariç); Ötüken'de dilek çaputları kararmış
	if not dname.begins_with("cira") and not dname.begins_with("mantar"):
		var dt: Array = art.get("decor_tint", [0.66, 0.68, 0.78])
		var tc := Color(dt[0], dt[1], dt[2])
		if dname == "dilek_agaci" and biome.get("id", "") == "otuken":
			tc = Color(0.52, 0.56, 0.68)
		m.set_shader_parameter("tint", tc)
	s.material = m
	s.z_index = z
	if rng.randf() < 0.5 and dname != "kam_diregi":
		s.flip_h = true
	decor_root.add_child(s)
	if d.get("glow_tex") != null:
		var g := Sprite2D.new()
		g.texture = d["glow_tex"]
		g.centered = false
		g.offset = s.offset
		g.flip_h = s.flip_h
		var gm := CanvasItemMaterial.new()
		gm.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
		gm.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
		g.material = gm
		g.self_modulate = Color(1.8, 1.6, 1.4)
		s.add_child(g)
	if glow_light:
		var tcol: Array = art.get("torch_col", [1.0, 0.58, 0.26])
		var l := add_light(s.position + Vector2(0, -52), Color(tcol[0], tcol[1], tcol[2]), 240.0, 1.35, decor_root)
		var tw := l.create_tween().set_loops()
		tw.tween_property(l, "energy", 1.1, 0.18)
		tw.tween_property(l, "energy", 1.45, 0.22)


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


func _ground_below(x: int, y: int, max_d := 14) -> int:
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
	if _has_decor("dilek_agaci"):
		_decor("dilek_agaci", 8, surface_y(8), -3)
	_decor("cira", 12, surface_y(12), -2, true)
	var next_torch := 40
	for x in range(16, W - 6):
		var sy := surface_y(x)
		if cell(x, sy) != 1:
			continue
		if x == next_torch:
			_decor("cira", x, sy, -2, true)
			next_torch += rng.randi_range(26, 36) if style != "magara" else rng.randi_range(14, 22)
			continue
		var r := rng.randf()
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
	if ink():
		_place_ink_extras()
	# çıkış: Kut Kapısı
	var ex := W - 7
	exit_pos = Vector2(ex * TS + TS / 2.0, surface_y(ex) * TS)
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
	# stil v2 mürekkep ortamı: yakın çekim kamera (art "camera_zoom", stil_v2.json; CameraV2: öncü kayma, dikey pencere,
	# boss sığdırma). v1 çerçevesi değişmez: oyuncunun çocuğu Camera2D + Player._look_ahead.
	var v2cam := ink()
	if v2cam:
		var cv := CameraV2.new()
		cv.level = self
		cv.player = player
		camera = cv
	else:
		camera = Camera2D.new()
		camera.position_smoothing_enabled = true
		camera.position_smoothing_speed = 7.0
	camera.limit_left = 0
	camera.limit_top = 0
	camera.limit_right = W * TS
	var deepest := 0
	for h in heights:
		deepest = maxi(deepest, int(h))
	camera.limit_bottom = mini(H, deepest + 4) * TS
	if v2cam:
		add_child(camera)
	else:
		player.add_child(camera)
		camera.position = Vector2(0, -40)
	Game.base_zoom = float(art.get("camera_zoom", 1.0)) if ink() else 1.0
	camera.zoom = Vector2.ONE * Game.base_zoom
	camera.process_mode = Node.PROCESS_MODE_ALWAYS
	camera.make_current()
	camera.reset_smoothing.call_deferred()
	Game.camera = camera
	# Kut ışığı: karanlık ormanda Bengü'nün çevresi hep okunur kalsın
	add_light(Vector2(0, -26), Color(1.0, 0.88, 0.68), 150.0, 0.7, player)


func _spawn_enemies() -> void:
	## Biyomun tüm türleri: yakın dövüşçüler yüzeye, pusucular yüksek adalara, uçanlar havaya; derinlikle yoğunluk artar
	var x := 26
	var elite_done := false
	var pool := _biome_pool()
	var depth := int(Game.run.get("depth", 1))
	var perches: Array = []
	for px in range(24, W - 24):
		for py in range(6, 34):
			if cell(px, py) != 0 and cell(px, py) != 3 and cell(px, py - 1) == 0 and py < surface_y(px) - 3:
				perches.append(Vector2i(px, py))
	while x < W - 18:
		var kind: String = pool[rng.randi_range(0, pool.size() - 1)]
		var ai: String = Data.enemy_def(kind).get("ai", Data.enemy_def(String(Data.enemy_def(kind).get("sprite", kind))).get("ai", "lunger"))
		var count := 1
		if Data.enemy_def(kind).get("sprite", kind) == "kara_boru" and ai == "lunger" and rng.randf() < 0.5:
			count = 2
		for k in count:
			var tx := x + k * 2
			var is_elite := not elite_done and x > 100 and rng.randf() < 0.3
			if is_elite:
				elite_done = true
			var pos := Vector2(tx * TS + TS / 2.0, surface_y(tx) * TS - 1)
			if ai == "pouncer" and not perches.is_empty():
				# en yakın yüksek yer
				var best: Vector2i = perches[0]
				var bd := 9999.0
				for pc in perches:
					var dd := absf(float(pc.x - tx))
					if dd < bd:
						bd = dd
						best = pc
				if bd < 30.0:
					pos = Vector2(best.x * TS + TS / 2.0, best.y * TS - 1)
			var en := spawn_enemy(kind, pos, is_elite)
			if en.sprite_kind == "kara_boru" and k == 1:
				en.flank = 1  # ikinci kurt arkadan dolaşır
		x += rng.randi_range(13, 20) - mini(4, depth / 2)


func spawn_enemy(kind: String, pos: Vector2, is_elite := false) -> Enemy:
	var e: Enemy = Boss.new() if String(Data.enemy_def(kind).get("ai", "")).begins_with("boss") else Enemy.new()
	e.setup(kind, is_elite, int(Game.run.get("tier", 0)))
	e.level = self
	e.position = pos
	if kind == "cor":
		e.position.y -= 70
	actors.add_child(e)
	return e


func _spawn_items() -> void:
	for tx in [34, 104, 168]:
		var it := ItemGen.random_drop(int(Game.run.get("tier", 0)))
		drop_item(it, Vector2(tx * TS + 12, surface_y(tx) * TS - 30), true)


func _spawn_scrolls() -> void:
	## Tılsımlar: her bölümde üç tane; ikisi yolda, biri havadaki bir adada (keşif ödülü).
	var xs := [58 + rng.randi_range(-6, 6), 128 + rng.randi_range(-8, 8)]
	for tx in xs:
		var t := clampi(tx, 20, W - 20)
		drop_scroll(Vector2(t * TS + 12, surface_y(t) * TS))
	var best := Vector2.ZERO
	for x in range(30, W - 30):
		for y in range(8, 30):
			if cell(x, y) == 1 and cell(x, y - 1) == 0 and y < surface_y(x) - 3:
				if best == Vector2.ZERO or rng.randf() < 0.08:
					best = Vector2(x * TS + 12, y * TS)
	if best != Vector2.ZERO:
		drop_scroll(best)


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
		if p.has_meta("oda") and alem and not alem.loot_open(p):
			continue  # gizli oda ganimeti: bu dünyadan alınmaz
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
	var tw := red_rect.create_tween()
	tw.set_ignore_time_scale(true)
	tw.tween_property(red_rect, "color:a", 0.0, 0.06)
	tw.tween_callback(func() -> void: red_rect.color = Color(1, 0.1, 0.1, 0.0))


func explode(pos: Vector2, radius: float, dmg: float, by_player: bool) -> void:
	## v14: aşamalı piksel patlama (ExplosionFX): flaş → ateş topu → duman + parçalar; kamera, ses ve ışık içinde
	var away := Vector2.UP
	if player and is_instance_valid(player):
		var d: Vector2 = player.center() - pos
		if d.length() > 1.0:
			away = d.normalized()
	FX.explosion(pos, radius, Color(1.0, 0.85, 0.3), radius >= 50.0, away)
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
	fp.position = Vector2(pos.x, surface_y(ty) * TS)
	add_child(fp)
	add_light(Vector2.ZERO, Color(1.0, 0.55, 0.2), radius * 3.0, 1.3, fp)


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
	m.position = Vector2(pos.x, surface_y(int(floor(pos.x / TS))) * TS)
	fx_root.add_child(m)


func spawn_roots(pos: Vector2, dmg: float, source: Node) -> void:
	var r := RootSpikes.new()
	r.level = self
	r.dmg = dmg
	r.source = source
	r.position = Vector2(pos.x, surface_y(int(floor(pos.x / TS))) * TS)
	fx_root.add_child(r)


func break_cracks(_rect: Rect2) -> void:
	pass


func on_enemy_died(e: Enemy) -> void:
	if e == boss and e != null:
		_on_boss_died(e)
		return
	_v12_on_kill(e)
	for i in randi_range(2, 4) + (6 if e.elite else 0):
		drop_orb("gold", e.center())


	# Kut taneleri (Dead Cells hücreleri): her düşman en az bir tane; seçkinler dört; şans eseri fazladan
	for i in (4 if e.elite else 1) + (1 if randf() < 0.3 else 0):
		drop_orb("kut", e.center())
	if e.elite or randf() < 0.04:
		drop_item(ItemGen.random_drop(int(Game.run.get("tier", 0)) + (1 if e.elite else 0)), e.center() + Vector2(0, -10))
	if e.elite or randf() < 0.05:
		drop_orb("sifa", e.center() + Vector2(0, -6))
	# parşömen: açılmamış bir eşyanın tarifi (seçkinlerden kesin, diğerlerinden seyrek)
	var locked := ItemGen.locked_implemented()
	if not locked.is_empty() and (e.elite or randf() < 0.07):
		drop_blueprint(locked[randi_range(0, locked.size() - 1)], e.center() + Vector2(0, -6))




func _v12_on_kill(e: Enemy) -> void:
	## Destanlar, don ruhu, âlem ödülleri
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
	if e.realm == "yer":
		for i in 3:
			drop_orb("kut", at)
		FX.soul(at, Color(0.75, 0.4, 0.95), 16)
	if pl:
		pl.kam = minf(100.0, pl.kam + 8.0)


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
	for i in 16:
		drop_orb("gold", e.center())
	for i in 10:
		drop_orb("kut", e.center())
	drop_orb("sifa", e.center() + Vector2(-20, -10))
	drop_item(ItemGen.random_drop(int(Game.run.get("tier", 0)) + 2), e.center() + Vector2(30, -10))
	var locked := ItemGen.locked_implemented()
	if not locked.is_empty():
		drop_blueprint(locked[randi_range(0, locked.size() - 1)], e.center() + Vector2(0, -16))
	var bd: Array = Game.run.get("boss_done", [])
	bd.append(boss_id)
	Game.run["boss_done"] = bd
	FX.text(e.center() + Vector2(0, -e.size.y - 20), "%s DEVRİLDİ" % String(e.def.get("name", "")).to_upper(), Color(1.0, 0.85, 0.5), 14)
	if boss_id == "erlik_han":
		Game.meta["wins"] = int(Game.meta.get("wins", 0)) + 1
		Game.save_meta()
		FX.text(e.center() + Vector2(0, -e.size.y - 44), "GÜNEŞ YENİDEN DOĞUYOR", Color(1.0, 0.95, 0.6), 16)
	boss = null
	boss_died.emit()
	get_tree().create_timer(1.6).timeout.connect(open_boss_gate)


func on_player_died() -> void:
	await get_tree().create_timer(1.4).timeout
	player_died.emit()


func _process(_delta: float) -> void:
	if player and not _done and player.global_position.distance_to(exit_pos) < 30.0 and (boss_id == "" or boss_gate_open):
		_done = true
		Ses.play("kapi")
		finished.emit()
	if player and not player.dead:
		Game.run["time"] = float(Game.run.get("time", 0.0)) + _delta
		if hub:
			var n := nearest_npc()
			if n and Input.is_action_just_pressed("etkiles"):
				n.talk()
				npc_requested.emit(n.id)
			return
		var p := nearest_item(player.global_position + Vector2(0, -10))
		if p and Input.is_action_just_pressed("etkiles"):
			if p.kind == "tilsim":
				scroll_requested.emit(p)
			elif p.kind == "lutuf":
				lutuf_requested.emit(p)
			else:
				try_equip(p)
	_hazard_tick(_delta)
