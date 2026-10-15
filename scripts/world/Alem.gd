class_name Alem
extends Node2D
## Üç Âlem: kam transıyla (R) aynı bölümün gök âlemine (Ülgen) ya da yeraltına (Erlik, R + aşağı) geçilir.
##  gök  : altın bulut basamakları (yalnızca gökte basılır), ruh kuşları (Kut + kam gücü), bulut zincirinin
##         tepesinde Ülgen sunağı (eşya). Yerçekimi hafifler.
##  yer  : mühürlü ruh taşları çözülür; altındaki gizli odalara inilir (eşya + şifa + altın). Erlik'in
##         gölge ruhları belirir (yalnızca yeraltında vurulur, iki kat Kut).
##  Öbür âlemdeyken bu dünyanın yaratıkları sana dokunamaz, sen de onlara (soluk görünürler).

const CLOUD_W := 72.0
const GOK_COL := Color(1.0, 0.88, 0.55)
const YER_COL := Color(0.75, 0.4, 0.95)

var level: Node
var realm := ""
var rooms: Array = []  # {room: Rect2 (dünya), door: Rect2 (dünya), door_cells: Array}
var clouds: Array = []  # {body, vis}
var birds: Array = []
var slabs: Array = []
var cover: TileMapLayer
var _gok := 0.0
var _yer := 0.0
var _t := 0.0
var overlay: ColorRect
var _layer: CanvasLayer
var _motes: CPUParticles2D
var _spirits: Array = []
var _door_cells: Array = []


# ------------------------------------------------------------------ 1) ızgara oyma (karolar kurulmadan önce)
func carve() -> void:
	## Yüzeyin altına en çok iki gizli oda: 3 karelik ruh taşı kapak (ızgarada 4), altında 7x2 oda.
	var W: int = level.W
	var H: int = level.H
	var rng: RandomNumberGenerator = level.rng
	var cands: Array = []
	for x in range(16, W - 16):
		for y in range(4, H - 8):
			if level.cell(x, y) != 0 or level.cell(x, y + 1) != 1:
				continue
			var ok := true
			for dx in range(-3, 4):
				if level.cell(x + dx, y) != 0 or level.cell(x + dx, y - 1) != 0:
					ok = false
					break
				for dy in range(1, 6):
					if level.cell(x + dx, y + dy) != 1:
						ok = false
						break
				if not ok:
					break
			if ok:
				cands.append(Vector2i(x, y))
	cands.shuffle()
	var used: Array = []
	for c in cands:
		if used.size() >= 2:
			break
		var far := true
		for u in used:
			if absi((u as Vector2i).x - c.x) < 30:
				far = false
		if not far or rng.randf() < 0.15:
			continue
		used.append(c)
		var x: int = c.x
		var y: int = c.y
		var cells: Array = []
		for dx in range(-1, 2):
			level.grid[level.idx(x + dx, y + 1)] = 4
			cells.append(Vector2i(x + dx, y + 1))
		for dx in range(-3, 4):
			for dy in range(2, 4):
				level.grid[level.idx(x + dx, y + dy)] = 0
		var TS: float = level.TS
		rooms.append({
			"room": Rect2((x - 3) * TS, (y + 2) * TS, 7 * TS, 2 * TS),
			"door": Rect2((x - 1) * TS, (y + 1) * TS, 3 * TS, TS),
			"cells": cells, "x": x, "y": y,
		})
		_door_cells.append_array(cells)


# ------------------------------------------------------------------ 2) içerik (oyuncu ve düşmanlar yerleştikten sonra)
func populate() -> void:
	z_index = 6
	_build_cover()
	_build_slabs()
	_build_clouds()
	_build_overlay()
	for r in rooms:
		_room_loot(r)


func _build_cover() -> void:
	## Gizli odaların üstünü normal toprakla örten karo katmanı (zeminle aynı karo seti ve gölgelendirici);
	## yeraltında saydamlaşır. Çarpışması yok.
	if rooms.is_empty() or level.ground == null:
		return
	cover = TileMapLayer.new()
	cover.tile_set = level.ground.tile_set
	cover.material = level.ground.material
	cover.scale = level.ground.scale
	cover.position = level.ground.position
	cover.collision_enabled = false
	cover.z_index = 6
	level.add_child(cover)
	for r in rooms:
		var x: int = r["x"]
		var y: int = r["y"]
		# kapak: üstü açık (çimenli) normal zemin karosu
		for dx in range(-1, 2):
			cover.set_cell(Vector2i(x + dx, y + 1), 0, Vector2i(1, (x + dx + y) % 3))
		# oda ve kenar payı: iç toprak karosu
		for dx in range(-4, 5):
			for dy in range(2, 5):
				if dy == 4 and absi(dx) <= 3:
					continue
				cover.set_cell(Vector2i(x + dx, y + dy), 0, Vector2i(0, (x + dx + y + dy) % 3))
		for dx in range(-3, 4):
			cover.set_cell(Vector2i(x + dx, y + 4), 0, Vector2i(0, (x + dx + y) % 3))
		for dx in [-3, -2, 2, 3]:
			cover.set_cell(Vector2i(x + dx, y + 1), 0, Vector2i(1, (x + dx + y) % 3))


func _build_slabs() -> void:
	## Ruh taşı kapak: normalde katı (katman HAYALET), yeraltında içinden geçilir.
	for r in rooms:
		var d: Rect2 = r["door"]
		var b := StaticBody2D.new()
		b.collision_layer = Game.LAYER_HAYALET
		b.collision_mask = 0
		var cs := CollisionShape2D.new()
		var sh := RectangleShape2D.new()
		sh.size = d.size
		cs.shape = sh
		b.position = d.get_center()
		b.add_child(cs)
		level.add_child(b)
		slabs.append({"body": b, "rect": d, "cs": cs})


func _build_clouds() -> void:
	## Gök: yerden 3-6 kare yukarıda, üstü açık havada altın bulut basamakları; bir zincirin tepesinde Ülgen sunağı.
	var rng: RandomNumberGenerator = level.rng
	var TS: float = level.TS
	var W: int = level.W
	var H: int = level.H
	var chains := 0
	var altar_done := false
	var tries := 0
	while chains < 6 and tries < 400:
		tries += 1
		var x := rng.randi_range(14, W - 14)
		var y := rng.randi_range(5, H - 6)
		if not _air_box(x, y, 2, 3):
			continue
		var gnd := -1
		for k in range(3, 7):
			if level.cell(x, y + k) != 0:
				gnd = k
				break
		if gnd < 0:
			continue
		var clear := true
		for k in range(1, gnd):
			if level.cell(x, y + k) != 0:
				clear = false
		if not clear:
			continue
		var too_close := false
		for c in clouds:
			if (c["pos"] as Vector2).distance_to(Vector2(x * TS, y * TS)) < 8 * TS:
				too_close = true
				break
		if too_close:
			continue
		chains += 1
		var cx := x
		var cy := y
		var links := rng.randi_range(2, 3)
		var top := Vector2.ZERO
		for i in links:
			_add_cloud(Vector2(cx * TS + TS / 2.0, cy * TS))
			top = Vector2(cx * TS + TS / 2.0, cy * TS)
			var sx := 4 if rng.randf() < 0.5 else -4
			if _air_box(cx + sx, cy - 3, 2, 3):
				cx += sx
				cy -= 3
			else:
				break
		# tepeye ödül: ilk uygun zincirde Ülgen sunağı, diğerlerinde ruh kuşu
		if not altar_done and rng.randf() < 0.7:
			altar_done = true
			var it := ItemGen.random_drop(int(Game.run.get("tier", 0)) + 1)
			level.drop_item(it, top + Vector2(0, -16), true)
			var pk: Pickup = level.pickups[-1]
			pk.set_meta("alem", "gok")
			pk.pedestal = false  # Ülgen sunağı: eşya bulutun üstünde süzülür (kaidesiz)
		else:
			_add_bird(top + Vector2(0, -34))
	# serbest ruh kuşları: yüksek boşluklarda
	var nb := 0
	tries = 0
	while nb < 4 and tries < 200:
		tries += 1
		var bx := rng.randi_range(10, W - 10)
		var by := rng.randi_range(3, H - 10)
		if _air_box(bx, by, 1, 2) and level.cell(bx, by + 4) == 0:
			_add_bird(Vector2(bx * TS + TS / 2.0, by * TS))
			nb += 1


func _air_box(x: int, y: int, hw: int, hh: int) -> bool:
	for dx in range(-hw, hw + 1):
		for dy in range(-hh, 1):
			if level.cell(x + dx, y + dy) != 0:
				return false
	return true


func _add_cloud(top_center: Vector2) -> void:
	var b := StaticBody2D.new()
	b.collision_layer = Game.LAYER_GOK
	b.collision_mask = 0
	var cs := CollisionShape2D.new()
	var sh := RectangleShape2D.new()
	sh.size = Vector2(CLOUD_W, 8)
	cs.shape = sh
	cs.one_way_collision = true
	cs.position = Vector2(0, 4)
	b.add_child(cs)
	b.position = top_center
	level.add_child(b)
	var v := _CloudVis.new()
	v.seed_v = int(top_center.x * 7 + top_center.y)
	v.position = top_center
	v.z_index = 4
	level.add_child(v)
	clouds.append({"body": b, "vis": v, "pos": top_center})


func _add_bird(pos: Vector2) -> void:
	var p := Pickup.new()
	p.kind = "ruh_kusu"
	p.level = level
	p.position = pos
	level.add_child(p)
	level.pickups.append(p)
	birds.append(p)


func _room_loot(r: Dictionary) -> void:
	## Gizli oda: Erlik'in sakladığı hazine (eşya kaidesi + şifa + altın), kandil ışığı
	var rm: Rect2 = r["room"]
	var floor_y := rm.end.y
	var it := ItemGen.random_drop(int(Game.run.get("tier", 0)) + 1)
	level.drop_item(it, Vector2(rm.get_center().x, floor_y - 30), true)
	level.drop_orb("sifa", Vector2(rm.position.x + 24, floor_y - 8))
	for i in 6:
		level.drop_orb("gold", Vector2(rm.position.x + 40 + i * 14, floor_y - 10))
	level.add_light(Vector2(rm.get_center().x, floor_y - 30), YER_COL, 120.0, 0.9)


func _build_overlay() -> void:
	_layer = CanvasLayer.new()
	_layer.layer = 4
	level.add_child(_layer)
	overlay = ColorRect.new()
	overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var m := ShaderMaterial.new()
	m.shader = load("res://shaders/alem.gdshader")
	overlay.material = m
	overlay.visible = false
	_layer.add_child(overlay)
	_motes = CPUParticles2D.new()
	_motes.amount = 50
	_motes.lifetime = 3.5
	_motes.emitting = false
	_motes.texture = FX.dot_tex()
	_motes.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
	_motes.emission_rect_extents = Vector2(340, 200)
	_motes.spread = 40.0
	_motes.initial_velocity_min = 8.0
	_motes.initial_velocity_max = 26.0
	_motes.scale_amount_min = 0.1
	_motes.scale_amount_max = 0.25
	_motes.z_index = 40
	var gm := CanvasItemMaterial.new()
	gm.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	_motes.material = gm
	level.add_child(_motes)


# ------------------------------------------------------------------ 3) âlem değiştirme
func set_realm(r: String) -> void:
	var prev := realm
	realm = r
	if r == "yer":
		_summon_spirits()
	elif prev == "yer":
		_dismiss_spirits()
	if _motes:
		_motes.emitting = r != ""
		if r == "gok":
			_motes.direction = Vector2(0.2, -1)
			_motes.gravity = Vector2(0, -6)
			_motes.color = Color(1.4, 1.2, 0.7, 0.8)
		elif r == "yer":
			_motes.direction = Vector2(0, -1)
			_motes.gravity = Vector2(0, -14)
			_motes.color = Color(1.2, 0.5, 1.4, 0.8)


func player_in_slab(rect: Rect2) -> bool:
	for s in slabs:
		if (s["rect"] as Rect2).intersects(rect.grow(-1.0)):
			return true
	return false


func room_of(p: Vector2) -> Dictionary:
	for r in rooms:
		if (r["room"] as Rect2).grow(4.0).has_point(p):
			return r
	return {}


func _summon_spirits() -> void:
	## Erlik'in gölge ruhları: yalnızca yeraltında var olurlar
	var pl: Node = level.player
	if pl == null:
		return
	_spirits = _spirits.filter(func(e: Variant) -> bool: return is_instance_valid(e) and not e.dead)
	var kinds := ["kayip_ruh", "kara_kus_yavrusu"]
	for i in maxi(0, 2 - _spirits.size()):
		var side := -1.0 if i % 2 == 0 else 1.0
		var pos: Vector2 = pl.global_position + Vector2(side * randf_range(120, 170), -60)
		var e: Enemy = level.spawn_enemy(kinds[i % kinds.size()], pos)
		e.realm = "yer"
		e.aggro = true
		e.anim.set_tint(Color(0.85, 0.55, 1.3))
		FX.anim("smoke_puff", e.center(), 0.0, 1.0, YER_COL, false)
		FX.soul(e.center(), YER_COL, 10)
		_spirits.append(e)


func _dismiss_spirits() -> void:
	for e in _spirits:
		if is_instance_valid(e) and not e.dead:
			FX.anim("smoke_puff", e.center(), 0.0, 0.9, YER_COL, false)
			e.remove_from_group("dusman")
			e.queue_free()
	_spirits = []


func _process(delta: float) -> void:
	_t += delta
	_gok = move_toward(_gok, 1.0 if realm == "gok" else 0.0, delta * 3.0)
	_yer = move_toward(_yer, 1.0 if realm == "yer" else 0.0, delta * 3.0)
	if overlay:
		overlay.visible = _gok > 0.0 or _yer > 0.0
		if overlay.visible:
			var m := overlay.material as ShaderMaterial
			m.set_shader_parameter("gok", _gok)
			m.set_shader_parameter("yer", _yer)
			m.set_shader_parameter("t", _t)
	if _motes and level.player:
		_motes.global_position = level.player.global_position + Vector2(0, -60)
	if cover:
		cover.modulate.a = lerpf(1.0, 0.12, _yer)
	for c in clouds:
		var v: Node2D = c["vis"]
		v.alpha = lerpf(0.16, 1.0, _gok)
		v.lit = _gok
	for b in birds:
		if is_instance_valid(b):
			b.modulate.a = lerpf(0.22, 1.0, _gok)
	# bu dünyanın yaratıkları öbür âlemden soluk görünür; âlem ruhları yalnızca kendi âleminde
	if Engine.get_process_frames() % 3 == 0:
		var pr := realm
		for e in get_tree().get_nodes_in_group("dusman"):
			if not is_instance_valid(e):
				continue
			var er: String = e.realm
			var a := 1.0 if er == pr else (0.3 if er == "" else 0.0)
			e.modulate.a = move_toward(e.modulate.a, a, 0.25)
	queue_redraw()


func _draw() -> void:
	## Ruh taşlarının üstünde nabız gibi atan mühür izleri (gizli odanın ipucu)
	var pulse := 0.35 + 0.25 * sin(_t * 2.4)
	for s in slabs:
		var d: Rect2 = s["rect"]
		var col := Color(YER_COL, pulse * (1.0 - _yer * 0.5))
		for i in 3:
			var cx := d.position.x + 12.0 + i * 24.0
			var cy := d.position.y + 12.0
			draw_line(Vector2(cx - 4, cy - 3), Vector2(cx, cy + 4), col, 1.0)
			draw_line(Vector2(cx, cy + 4), Vector2(cx + 4, cy - 3), col, 1.0)
			draw_line(Vector2(cx - 2, cy - 5), Vector2(cx + 2, cy - 5), col, 1.0)
		if _yer > 0.0:
			draw_rect(d, Color(YER_COL, 0.18 * _yer + 0.1 * sin(_t * 9.0) * _yer), true)


class _CloudVis:
	extends Node2D
	## Altın bulut (piksel sanat): öbeklerin birleşimi; üstü ışıklı, altı altın gölgeli, koyu kenar çizgisi,
	## ara tonlar damalı. 1,5 kat yoğunlukta çizilir (zemin karolarıyla aynı piksel ızgarası), 2/3 ölçekle gösterilir.
	var seed_v := 0
	var alpha := 0.16
	var lit := 0.0
	var _t := 0.0
	var spr: Sprite2D

	func _ready() -> void:
		var r := RandomNumberGenerator.new()
		r.seed = seed_v
		var W := 126
		var H := 40
		var blobs: Array = []
		for i in 8:
			var bx := r.randf_range(-44, 44)
			blobs.append(Vector3(W / 2.0 + bx, 22.0 + r.randf_range(-6, 2) + absf(bx) * 0.08, r.randf_range(10, 17) * (1.0 - absf(bx) / 110.0)))
		var inside := func(x: int, y: int) -> bool:
			if y > 30 or y < 0 or x < 0 or x >= W:
				return false
			for b in blobs:
				var dx: float = x - b.x
				var dy: float = (y - b.y) * 1.35
				if dx * dx + dy * dy < b.z * b.z:
					return true
			return false
		var img := Image.create(W, H, false, Image.FORMAT_RGBA8)
		var hi := Color(1.0, 0.98, 0.9)
		var mid := Color(0.99, 0.89, 0.68)
		var low := Color(0.9, 0.68, 0.44)
		var deep := Color(0.74, 0.5, 0.32)
		var ink := Color(0.45, 0.28, 0.2)
		for x in W:
			var top := -1
			for y in H:
				if inside.call(x, y):
					top = y
					break
			if top < 0:
				continue
			for y in range(top, H):
				if not inside.call(x, y):
					continue
				var edge: bool = not inside.call(x - 1, y) or not inside.call(x + 1, y) or not inside.call(x, y - 1) or not inside.call(x, y + 1)
				var d := y - top
				var bot := 0
				while inside.call(x, y + bot + 1) and bot < 12:
					bot += 1
				var c := mid
				if d <= 1:
					c = hi
				elif d <= 3 and (x + y) % 2 == 0:
					c = hi
				if bot <= 1:
					c = deep
				elif bot <= 3:
					c = low if (x + y) % 2 == 0 or bot <= 2 else mid
				if edge:
					c = ink if bot <= 2 else c.darkened(0.25)
				img.set_pixel(x, y, c)
		spr = Sprite2D.new()
		spr.texture = ImageTexture.create_from_image(img)
		spr.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		spr.scale = Vector2(2.0 / 3.0, 2.0 / 3.0)
		spr.centered = true
		spr.position = Vector2(0, 2)
		add_child(spr)

	func _process(delta: float) -> void:
		_t += delta
		var bob := roundf(sin(_t * 1.6 + seed_v) * 1.5 * lit)
		if spr:
			spr.position.y = 2.0 + bob
			spr.modulate = Color(0.8 + 0.12 * lit, 0.78 + 0.1 * lit, 0.8, alpha)
