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
var _light_tex: GradientTexture2D
var _done := false


func build(seed_value: int) -> void:
	rng.seed = seed_value
	biome = Game.biome_for_depth(int(Game.run.get("depth", 1)))
	art = biome.get("art", {})
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
	art = biome.get("art", {}).duplicate()
	art["ambient"] = [0.36, 0.3, 0.42]
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
	var ts := TileSet.new()
	ts.tile_size = Vector2i(TS, TS)
	var src := TileSetAtlasSource.new()
	src.texture = Data.canvas_tex("res://assets/tiles/hazards.png", "res://assets/tiles/hazards_n.png")
	src.texture_region_size = Vector2i(TS, TS)
	ts.add_source(src, 0)
	for r in 4:
		for c in 2:
			src.create_tile(Vector2i(c, r))
	hazard = TileMapLayer.new()
	hazard.tile_set = ts
	var m := ShaderMaterial.new()
	m.shader = Game.toon_shader
	hazard.material = m
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
				if haz_kind == "lav" and n % 2 == 0:
					add_light(Vector2(x * TS + 12, y * TS + 6), Color(1.0, 0.5, 0.2), 70.0, 0.9, hazard)
	# glow katmanı (lav / zehir)
	if haz_kind in ["lav", "zehir"]:
		var glow := TileMapLayer.new()
		var ts2 := TileSet.new()
		ts2.tile_size = Vector2i(TS, TS)
		var src2 := TileSetAtlasSource.new()
		src2.texture = load("res://assets/tiles/hazards_e.png")
		src2.texture_region_size = Vector2i(TS, TS)
		ts2.add_source(src2, 0)
		for r in 4:
			for c in 2:
				src2.create_tile(Vector2i(c, r))
		glow.tile_set = ts2
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
	art["ambient"] = [0.5, 0.47, 0.6]
	art["sun_energy"] = 0.3
	art["particles"] = "ruh"
	art["decor_tint"] = [0.8, 0.78, 0.84]
	Game.run["biome"] = "yurt"
	_generate_hub()
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
	_place_hub()
	_spawn_player()
	camera.limit_right = HUB_W * TS
	_build_particles()
	_build_overlay_fx()
	Ses.music("yurt")


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
	var sy := surface_y(34)
	_decor("ulu_kayin", 34, sy, -4)
	_decor("cadir", 68, surface_y(68), -3)
	_decor("ocak", 58, surface_y(58), -1, true)
	for x in [14, 46, 76]:
		_decor("cira", x, surface_y(x), -2, true)
	for x in [10, 22, 41, 52, 63, 73]:
		_decor(["cicek_1", "cicek_2", "kaya_1", "cicek_3"][x % 4], x, surface_y(x), 6)
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
	var ex := HUB_W - 7
	exit_pos = Vector2(ex * TS + TS / 2.0, surface_y(ex) * TS)
	var gate := KutGate.new()
	gate.position = exit_pos
	decor_root.add_child(gate)
	var portal := FX.anim("rift_portal", exit_pos + Vector2(0, -34), 0.0, 1.0, Color(0.6, 1.0, 1.0, 0.85))
	if portal:
		portal.loop = true
		portal.z_index = -1
		portal.reparent(decor_root)
	add_light(exit_pos + Vector2(0, -40), Color(0.45, 0.9, 1.0), 220.0, 1.4, decor_root)


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
	## pikseli 2x2 ekran pikseline düşer.
	return int(Data.tile_meta.get("tile", TS))


func _make_tileset() -> TileSet:
	var ac := _art_cell()
	var ts := TileSet.new()
	ts.tile_size = Vector2i(ac, ac)
	ts.add_physics_layer()
	ts.set_physics_layer_collision_layer(0, Game.LAYER_WORLD)
	ts.set_physics_layer_collision_mask(0, 0)
	ts.add_physics_layer()
	ts.set_physics_layer_collision_layer(1, Game.LAYER_PLATFORM)
	ts.set_physics_layer_collision_mask(1, 0)
	var src := TileSetAtlasSource.new()
	var bid: String = biome.get("id", "otuken")
	src.texture = Data.canvas_tex("res://assets/tiles/%s.png" % bid, "res://assets/tiles/%s_n.png" % bid)
	src.texture_region_size = Vector2i(ac, ac)
	ts.add_source(src, 0)
	var meta := Data.tile_meta
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
		td.set_collision_polygon_one_way_margin(phys, 0, float(_art_cell()) / TS)


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


func _build_tiles() -> void:
	var ts := _make_tileset()
	var gmat := ShaderMaterial.new()
	gmat.shader = load("res://shaders/ground.gdshader")
	var bid2: String = biome.get("id", "otuken")
	gmat.set_shader_parameter("soil_tex", load("res://assets/tiles/%s_soil.png" % bid2))
	gmat.set_shader_parameter("soil_n", load("res://assets/tiles/%s_soil_n.png" % bid2))
	var dc: Array = art.get("deep_color", [0.04, 0.03, 0.06])
	gmat.set_shader_parameter("deep_color", Color(dc[0], dc[1], dc[2]))
	gmat.set_shader_parameter("depth_tex", _depth_texture())
	gmat.set_shader_parameter("map_size_px", Vector2(W * TS, H * TS))
	gmat.set_shader_parameter("soil_density", float(_art_cell()) / TS)
	var emis_path := "res://assets/tiles/%s_soil_e.png" % bid2
	if ResourceLoader.exists(emis_path):
		gmat.set_shader_parameter("soil_e", load(emis_path))
	var bmeta: Dictionary = Data.load_json("res://assets/tiles/%s.json" % bid2)
	var gc = bmeta.get("glow")
	if gc is Array and (gc as Array).size() >= 3:
		gmat.set_shader_parameter("glow_col", Color(gc[0], gc[1], gc[2]))
	var tmat := ShaderMaterial.new()
	tmat.shader = Game.toon_shader
	var art_scale := Vector2.ONE * (float(TS) / _art_cell())
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
	var meta := Data.tile_meta
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


func add_light(pos: Vector2, col: Color, radius: float, energy := 1.0, parent: Node = null) -> PointLight2D:
	var l := PointLight2D.new()
	l.texture = light_tex()
	l.texture_scale = radius / 64.0
	l.color = col
	l.energy = energy
	l.height = 26.0
	l.position = pos
	(parent if parent else self).add_child(l)
	return l


func _build_lighting() -> void:
	# Kararan Ötüken: soğuk, loş ortam ışığı; "güneş" yerine ay. Sıcak ışık yalnızca
	# ocaklardan, çıralardan ve Bengü'nün Kut'undan gelir.
	var amb: Array = art.get("ambient", [0.40, 0.44, 0.62])
	var sun_c: Array = art.get("sun", [0.62, 0.72, 1.0])
	var cm := CanvasModulate.new()
	cm.color = Color(amb[0], amb[1], amb[2])
	add_child(cm)
	var moon := DirectionalLight2D.new()
	moon.color = Color(sun_c[0], sun_c[1], sun_c[2])
	moon.energy = float(art.get("sun_energy", 0.38))
	moon.height = 0.55
	moon.rotation_degrees = float(art.get("sun_rot", 40))
	add_child(moon)
	var env := Environment.new()
	env.background_mode = Environment.BG_CANVAS
	env.glow_enabled = true
	env.glow_intensity = 0.9
	env.glow_strength = 1.0
	env.glow_bloom = 0.04
	env.glow_hdr_threshold = 0.9
	env.glow_blend_mode = Environment.GLOW_BLEND_MODE_SOFTLIGHT
	env.adjustment_enabled = true
	env.adjustment_saturation = float(art.get("saturation", 0.96))
	env.adjustment_contrast = float(art.get("contrast", 1.08))
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)


func _build_background() -> void:
	var bg := ParallaxBG.new()
	bg.level = self
	var names: Array = art.get("bg", [])
	var fxs: Array = art.get("bg_fx", [])
	if not names.is_empty():
		var layers: Array = []
		for i in names.size():
			var f: Array = fxs[i] if i < fxs.size() else [0.3, 0.1, 0.0]
			layers.append(["res://assets/bg/%s.png" % names[i], float(f[0]), float(f[1]), float(f[2])])
		bg.layers = layers
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
	leaves.texture = lt
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
	match kind:
		"polen":
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


func _build_overlay_fx() -> void:
	var cl := CanvasLayer.new()
	cl.layer = 5
	add_child(cl)
	var vig := ColorRect.new()
	vig.set_anchors_preset(Control.PRESET_FULL_RECT)
	vig.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var sm := ShaderMaterial.new()
	sm.shader = load("res://shaders/vignette.gdshader")
	vig.material = sm
	cl.add_child(vig)
	red_rect = ColorRect.new()
	red_rect.set_anchors_preset(Control.PRESET_FULL_RECT)
	red_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	red_rect.color = Color(1, 0.1, 0.1, 0.0)
	cl.add_child(red_rect)


func flash_red() -> void:
	red_rect.color.a = 0.16
	var tw := create_tween()
	tw.tween_property(red_rect, "color:a", 0.0, 0.3)


# ------------------------------------------------------------------ süsler
func _decor(dname: String, tile_x: int, tile_y_surface: int, z := -2, glow_light := false) -> void:
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
	actors.add_child(player)
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
	player.add_child(camera)
	camera.position = Vector2(0, -40)
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
	## Ağır vuruşta tüm ekran bir an beyazlar (Dead Cells'in "kill flash"i)
	if red_rect == null:
		return
	red_rect.color = Color(1.0, 0.97, 0.9, a)
	var tw := red_rect.create_tween()
	tw.tween_property(red_rect, "color:a", 0.0, 0.12)
	tw.tween_callback(func() -> void: red_rect.color = Color(1, 0.1, 0.1, 0.0))


func explode(pos: Vector2, radius: float, dmg: float, by_player: bool) -> void:
	Game.shake(6.0)
	Game.kick(Vector2.DOWN, 5.0)
	Ses.play("patlama", 0.0)
	Game.slowmo(0.5, 0.08)
	FX.impact(pos, Vector2.UP, Color(1.0, 0.75, 0.35), 2.4)
	FX.anim("warm_explosion", pos + Vector2(0, 6), 0.0, 0.7 + radius / 50.0, Color(1.0, 0.9, 0.8))
	FX.smoke(pos, 8, 0.7)
	FX.fire(pos, 10, 0.4, radius * 0.4)
	FX.sparks(pos, Vector2.UP, Color(1.0, 0.8, 0.4), 16, 260.0)
	FX.shock_line(pos, radius * 0.8, Color(0.5, 0.4, 0.35, 0.6))
	FX.ring(pos, radius, Color(1.0, 0.7, 0.3), 0.35)
	FX.burst(pos, Color(1.0, 0.6, 0.2), 26, 220, 0.5, 0.3, 300, true)
	FX.burst(pos, Color(0.3, 0.25, 0.25), 14, 120, 0.9, 0.35, -30)
	var l := add_light(pos, Color(1.0, 0.6, 0.25), radius * 3.0, 2.0)
	var tw := l.create_tween()
	tw.tween_property(l, "energy", 0.0, 0.35)
	tw.tween_callback(l.queue_free)
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
