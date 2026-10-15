class_name Pickup
extends Node2D
## Toplanabilirler: altın, kut taneleri, yerdeki eşyalar (E ile alınır / değiştirilir),
## tılsımlar (E ile ongun seçimi: Kurt / Kartal / Ayı) ve silah parşömenleri (dokununca toplanır).

var kind := "gold"
var item: Dictionary = {}
var item_id := ""  # parşömen: açılacak eşya
var velocity := Vector2.ZERO
var level: Node
var pedestal := false
var _t := 0.0
var _grounded := false
var spr: Sprite2D
var light: PointLight2D


func _ready() -> void:
	z_index = 15
	if kind == "item":
		spr = Sprite2D.new()
		spr.texture = Data.weapon_tex
		spr.region_enabled = true
		spr.centered = false
		var m := ShaderMaterial.new()
		m.shader = Game.toon_shader
		spr.material = m
		add_child(spr)
		_refresh()
		light = level.add_light(Vector2(0, -4), Color.WHITE, 60.0, 0.8, self)
		_refresh()
	elif kind == "tilsim":
		light = level.add_light(Vector2(0, -10), Color(1.0, 0.85, 0.5), 90.0, 1.0, self)
	elif kind == "parsomen":
		light = level.add_light(Vector2(0, -6), Color(0.6, 0.9, 1.0), 70.0, 0.9, self)
	elif kind == "don":
		light = level.add_light(Vector2.ZERO, Color(0.75, 0.55, 1.0), 90.0, 1.0, self)
	elif kind == "ruh_kusu":
		light = level.add_light(Vector2.ZERO, Color(1.0, 0.85, 0.5), 50.0, 0.6, self)


func reset_ground() -> void:
	## Değiştirilen eski eşya: yeniden düşsün
	_grounded = false
	pedestal = false


func _refresh() -> void:
	if spr and not item.is_empty() and Data.has_weapon_sprite(item["id"]):
		spr.region_rect = Data.weapon_region(item["id"], item["material"])
		spr.offset = -Data.weapon_pivot(item["id"])
		var cell: Array = Data.weapon_meta["cell"]
		if Data.weapon_pivot(item["id"]).x < 30:
			spr.offset.x += 16.0 - float(cell[0]) / 2.0 + 16.0
	if light and not item.is_empty():
		light.color = Color.from_string(Data.items["rarities"][int(item["rarity"])]["color"], Color.WHITE)


func _physics_process(delta: float) -> void:
	_t += delta
	var pl: Node = level.player if level else null
	if kind == "don":
		# seçkinin ruhu: süzülür, dönen zerreler; dokununca emilir
		if int(_t * 60.0) % 4 == 0:
			FX.burst(global_position + Vector2(randf_range(-8, 8), randf_range(-8, 8)), Color(0.75, 0.55, 1.0), 1, 20, 0.6, 0.16, -40, true)
		if pl and not pl.dead and _t > 0.5 and pl.center().distance_to(global_position) < 26.0:
			pl.gain_don(item_id)
			level.pickups.erase(self)
			queue_free()
			return
		queue_redraw()
		return
	if kind == "ruh_kusu":
		# Ülgen'in ruh kuşu: yalnızca gök âleminde yakalanır
		position.y += sin(_t * 3.0) * 0.25
		if pl and not pl.dead and String(pl.realm) == "gok" and pl.center().distance_to(global_position) < 22.0:
			Game.run["kut"] = int(Game.run["kut"]) + 3
			pl.add_kut(6.0)
			pl.kam = minf(100.0, pl.kam + 18.0)
			FX.burst(global_position, Color(1.0, 0.9, 0.55), 12, 70, 0.5, 0.18, -40, true)
			FX.ring(global_position, 18, Color(1.0, 0.9, 0.55), 0.3)
			FX.text(global_position + Vector2(0, -16), "ruh kuşu", Color(1.0, 0.9, 0.6), 7)
			Ses.play("ruh_kusu", -2.0)
			level.pickups.erase(self)
			queue_free()
			return
		queue_redraw()
		return
	if kind == "lutuf":
		if int(_t * 60.0) % 8 == 0:
			FX.burst(global_position + Vector2(randf_range(-10, 10), -24), Color(1.0, 0.9, 0.6), 1, 24, 0.8, 0.14, -50, true)
		return
	if kind == "item" or kind == "tilsim" or kind == "parsomen":
		if not pedestal and not _grounded and not has_meta("alem"):
			velocity.y = minf(velocity.y + 900.0 * delta, 400.0)
			var nxt := position + velocity * delta
			if level.ground_at(nxt + Vector2(0, 12)):
				_grounded = true
				velocity = Vector2.ZERO
			else:
				position = nxt
		if spr:
			spr.position.y = sin(_t * 2.5) * 2.0 - 6.0
			if item != spr.get_meta("shown", {}):
				spr.set_meta("shown", item)
				_refresh()
		if light:
			light.energy = 0.9 + 0.25 * sin(_t * 4.0)
		if kind == "tilsim" and int(_t * 60.0) % 12 == 0:
			FX.burst(global_position + Vector2(randf_range(-8, 8), -10), Color(1.0, 0.85, 0.45), 1, 20, 0.7, 0.14, -50, true)
		if kind == "parsomen":
			if int(_t * 60.0) % 10 == 0:
				FX.burst(global_position + Vector2(randf_range(-6, 6), -8), Color(0.6, 0.9, 1.0), 1, 16, 0.6, 0.12, -40, true)
			if pl and not pl.dead and pl.center().distance_to(global_position + Vector2(0, -8)) < 22.0:
				_collect_blueprint(pl)
				return
		queue_redraw()
		return
	if pl and not pl.dead and _t > 0.45 and pl.center().distance_to(global_position) < 90.0:
		global_position = global_position.move_toward(pl.center(), (220.0 + 600.0 * _t) * delta)
		if pl.center().distance_to(global_position) < 10.0:
			if kind == "sifa":
				var h: float = float(Game.run["max_hp"]) * 0.35
				pl.heal(h)
				FX.anim("radiant_heal", pl.center(), 0.0, 1.0, Color(0.6, 1.0, 0.6))
				FX.ring(pl.center(), 26, Color(0.6, 1.0, 0.6), 0.3)
				FX.text(pl.center() + Vector2(0, -34), "Şifa Otu", Color(0.6, 1.0, 0.6), 8)
				Ses.play("sise", -4.0, 1.2)
				queue_free()
				return
			if kind == "gold":
				Game.run["gold"] = int(Game.run["gold"]) + randi_range(1, 3)
				FX.burst(global_position, Color(1.0, 0.85, 0.4), 3, 40, 0.25, 0.14, 0, true)
				Ses.play("altin", -8.0, 1.0 + 0.04 * (int(Game.run["gold"]) % 5), 0.03, 0.04)
			else:
				Game.run["kut"] = int(Game.run["kut"]) + 1
				pl.add_kut(2.0)
				FX.burst(global_position, Color(0.5, 0.95, 1.0), 4, 50, 0.3, 0.16, 0, true)
				FX.ring(global_position, 10, Color(0.6, 0.95, 1.0), 0.18)
				Ses.play("kut_tane", -4.0, 1.0 + 0.03 * (int(Game.run["kut"]) % 6), 0.02, 0.05)
				if level.get_parent() and level.get_parent().get("hud"):
					level.get_parent().hud.kut_pulse()
			queue_free()
		return
	velocity.y = minf(velocity.y + 900.0 * delta, 400.0)
	velocity.x = move_toward(velocity.x, 0.0, 120.0 * delta)
	var nxt2 := position + velocity * delta
	if level.ground_at(nxt2 + Vector2(0, 3)):
		velocity = Vector2(velocity.x * 0.5, -absf(velocity.y) * 0.3)
		if absf(velocity.y) < 30.0:
			velocity.y = 0.0
	else:
		position = nxt2
	queue_redraw()


func _collect_blueprint(pl: Node) -> void:
	var base := Data.find_item(item_id)
	var fresh := Game.add_blueprint(item_id)
	FX.text(pl.center() + Vector2(0, -34), "Parşömen: %s" % base.get("name", item_id), Color(0.6, 0.9, 1.0), 8)
	Ses.play("tilsim", -2.0, 1.15)
	if not fresh:
		Game.run["gold"] = int(Game.run["gold"]) + 15
	FX.soul(global_position + Vector2(0, -8), Color(0.6, 0.9, 1.0), 16)
	FX.ring(global_position + Vector2(0, -8), 22, Color(0.6, 0.9, 1.0), 0.3)
	level.pickups.erase(self)
	queue_free()


func _draw() -> void:
	match kind:
		"don":
			# mor ruh: iç içe halkalar, yörüngede dönen üç zerre
			var p2 := 1.0 + sin(_t * 5.0) * 0.15
			draw_circle(Vector2.ZERO, 9.0 * p2, Color(0.55, 0.3, 0.9, 0.25))
			draw_circle(Vector2.ZERO, 5.5 * p2, Color(0.8, 0.6, 1.0, 0.6))
			draw_circle(Vector2.ZERO, 2.5, Color(1.0, 0.95, 1.0))
			for k in 3:
				var a := _t * 3.0 + k * TAU / 3.0
				draw_circle(Vector2(cos(a), sin(a) * 0.6) * 12.0, 1.4, Color(0.9, 0.75, 1.0))
		"ruh_kusu":
			# altın kuş: kanat çırpar
			var fl := sin(_t * 14.0)
			var c := Color(1.0, 0.88, 0.5)
			draw_line(Vector2(0, 0), Vector2(-6, -3 - fl * 3.0), c, 1.5)
			draw_line(Vector2(0, 0), Vector2(6, -3 - fl * 3.0), c, 1.5)
			draw_circle(Vector2(0, 0), 1.8, Color(1.0, 0.97, 0.8))
			draw_circle(Vector2(0, 0), 5.0, Color(1.0, 0.85, 0.4, 0.18))
		"gold":
			var w := 2.0 + absf(sin(_t * 6.0)) * 1.5
			draw_rect(Rect2(-w / 2.0, -5, w, 5), Color(1.0, 0.82, 0.3))
			draw_rect(Rect2(-w / 2.0, -5, w, 1), Color(1.0, 0.96, 0.7))
		"sifa":
			# şifa otu: yeşil yaprak demeti, ortada ışıyan tohum
			var bb := sin(_t * 3.0) * 1.5
			for k in 3:
				var a := -PI / 2.0 + (k - 1) * 0.7
				draw_line(Vector2(0, -2 + bb), Vector2(cos(a) * 7.0, -2 + bb + sin(a) * 7.0), Color(0.35, 0.8, 0.35), 2.0)
			draw_circle(Vector2(0, -6 + bb), 3.0, Color(0.6, 1.0, 0.6, 0.35 + 0.15 * sin(_t * 6.0)))
			draw_circle(Vector2(0, -6 + bb), 1.6, Color(0.9, 1.0, 0.8))
		"kut":
			var pulse := 1.0 + sin(_t * 8.0) * 0.25
			draw_circle(Vector2(0, -3), 4.0 * pulse, Color(0.4, 0.95, 1.0, 0.3))
			draw_circle(Vector2(0, -3), 2.0, Color(0.8, 1.0, 1.0))
		"item":
			if pedestal:
				draw_rect(Rect2(-10, 18, 20, 12), Color(0.36, 0.38, 0.46))
				draw_rect(Rect2(-12, 16, 24, 3), Color(0.55, 0.58, 0.66))
			var col := Color.from_string(Data.items["rarities"][int(item.get("rarity", 0))]["color"], Color.WHITE)
			for k in 3:
				var a := _t * 2.0 + k * TAU / 3.0
				draw_circle(Vector2(cos(a) * 14.0, -6.0 + sin(a) * 4.0), 1.0, col)
		"tilsim":
			# taş kaide üstünde asılı, üç renkli kam tılsımı (kurt kızılı, kartal mavisi, ayı yeşili)
			var bob := sin(_t * 2.2) * 2.0
			draw_rect(Rect2(-9, -4, 18, 4), Color(0.3, 0.32, 0.4))
			draw_rect(Rect2(-7, -6, 14, 2), Color(0.5, 0.52, 0.6))
			var c := Vector2(0, -20 + bob)
			draw_circle(c, 9.0, Color(1.0, 0.85, 0.5, 0.18 + 0.08 * sin(_t * 5.0)))
			draw_circle(c, 5.5, Color(0.2, 0.14, 0.1))
			draw_arc(c, 5.5, 0, TAU, 24, Color(0.9, 0.75, 0.4), 1.2)
			var cols := [Color(1.0, 0.42, 0.3), Color(0.37, 0.78, 1.0), Color(0.61, 0.88, 0.4)]
			for k in 3:
				var a := -PI / 2.0 + k * TAU / 3.0 + _t * 0.8
				draw_circle(c + Vector2(cos(a), sin(a)) * 2.8, 1.6, cols[k])
			for k in 3:
				var a2 := _t * 1.5 + k * TAU / 3.0
				draw_line(c + Vector2(cos(a2), sin(a2)) * 7.0, c + Vector2(cos(a2), sin(a2)) * 10.0, Color(1.0, 0.9, 0.6, 0.6), 1.0)
		"parsomen":
			# rulo parşömen: iki sarılı uç, ortada mühür
			var bob := sin(_t * 3.0) * 1.5
			var y := -10.0 + bob
			draw_rect(Rect2(-7, y - 4, 14, 8), Color(0.85, 0.78, 0.6))
			draw_rect(Rect2(-8, y - 5, 3, 10), Color(0.6, 0.5, 0.35))
			draw_rect(Rect2(5, y - 5, 3, 10), Color(0.6, 0.5, 0.35))
			draw_rect(Rect2(-4, y - 2, 8, 1), Color(0.4, 0.3, 0.25))
			draw_rect(Rect2(-4, y + 1, 6, 1), Color(0.4, 0.3, 0.25))
			draw_circle(Vector2(0, y), 2.0, Color(0.4, 0.7, 1.0))
