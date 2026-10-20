class_name Tehlike
extends Node2D
## v23 yer tehlikeleri (düşman ve boss hamleleri): önce kurulur (delay boyunca soluk, titreşen uyarı), sonra life
## boyunca içindeki oyuncuya tick aralığıyla vurur. Hepsi mürekkep fırçasıyla çizilir (InkDraw; doğrusal süzgeç).
##   zehir   yeşil zehir gölü (zehirler)          ates   alev gölü (Od İyesi, Erlik)
##   catlak  Tepegöz'ün gürz çatlağı: kurulunca kor fışkırır, sonra için için yanar
##   buz     buz dikenleri (Yelbegen): kurulunca fırlar, kısa sürer
##   lav     Erlik'in âlem kayması: zemini kaplayan lav (platformlara çık)
##   sutun   gökten / yerden sütun (kor, buz): uzun boylu, kısa ömürlü
##   serit   yalnızca uyarı şeridi (hasar yok): hücum / tarama hattı

var level: Node
var source: Node
var kind := "zehir"
var w := 40.0          # yarı genişlik (px)
var h := 26.0          # hasar yüksekliği (px)
var delay := 0.6       # kurulma (uyarı) süresi
var life := 3.0        # kurulduktan sonraki ömür
var dmg := 10.0
var tick := 0.5
var _t := 0.0
var _tick_t := 0.0
var _armed := false
var _seed := 0


static func spawn(lv: Node, k: String, pos: Vector2, half_w: float, dly: float, lf: float, d: float, src: Node, on_ground := true) -> Tehlike:
	var t := Tehlike.new()
	t.level = lv
	t.kind = k
	t.w = half_w
	t.delay = dly
	t.life = lf
	t.dmg = d
	t.source = src
	t._seed = randi() % 997
	match k:
		"sutun":
			t.h = 260.0
			t.tick = 0.3
		"lav":
			t.h = 14.0
			t.tick = 0.45
		"buz":
			t.h = 40.0
			t.tick = 0.4
		"catlak":
			t.h = 22.0
		"serit":
			t.dmg = 0.0
	if on_ground and lv:
		var ty := int(floor(pos.x / Level.TS))
		t.position = Vector2(pos.x, lv.surface_y(ty, int(floor(pos.y / Level.TS)) - 2) * Level.TS)
	else:
		t.position = pos
	lv.add_child(t)
	return t


func _ready() -> void:
	z_index = 7 if kind != "sutun" else 22
	InkDraw.prep(self)
	if kind in ["ates", "lav", "sutun", "catlak"]:
		var m := CanvasItemMaterial.new()
		m.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
		material = m
		if level and level.has_method("add_light") and kind != "serit":
			level.add_light(Vector2(0, -10), Color(1.0, 0.5, 0.2) if kind != "zehir" else Color(0.5, 1.0, 0.4), w * 2.4, 0.9, self)


func _process(delta: float) -> void:
	_t += delta
	if not _armed and _t >= delay:
		_armed = true
		_tick_t = 0.0
		_on_arm()
	if _armed and _t >= delay + life:
		queue_free()
		return
	if _armed and dmg > 0.0:
		_tick_t -= delta
		if _tick_t <= 0.0:
			var pl: Node = level.player if level else null
			if pl and not pl.dead and _rect().intersects(pl.hurt_rect()):
				_tick_t = tick
				if pl.take_hit(dmg, source if is_instance_valid(source) else null):
					if kind == "zehir" and pl.has_method("apply_poison"):
						pl.apply_poison(2.5)
	if _armed and Engine.get_process_frames() % 4 == 0:
		match kind:
			"ates", "lav":
				FX.fire(global_position + Vector2(randf_range(-w, w), -2), 1, 0.3, 2.0)
			"zehir":
				FX.bubbles(global_position + Vector2(randf_range(-w, w), -3), 1, Color(0.5, 1.0, 0.35))
			"catlak":
				if randf() < 0.5:
					FX.smoke(global_position + Vector2(randf_range(-w, w), -4), 1, 0.3, Color(0.3, 0.22, 0.2, 0.5))
	queue_redraw()


func _rect() -> Rect2:
	return Rect2(global_position + Vector2(-w, -h), Vector2(w * 2.0, h + 4.0))


func _on_arm() -> void:
	match kind:
		"catlak":
			Game.shake(3.0)
			FX.burst(global_position, Color(1.0, 0.5, 0.2), 16, 160, 0.5, 0.22, 380)
			FX.dust(global_position, Vector2.UP, 8, 0.34)
			Ses.play("sarsinti", -8.0, 1.2, 0.08, 0.03, global_position)
		"buz":
			FX.frost(global_position + Vector2(0, -14), 8)
			Ses.play("buz_kir" if Ses.has("buz_kir") else "darbe_tas", -6.0, 1.2, 0.08, 0.03, global_position)
		"sutun":
			Game.shake(2.5)
			FX.flash_light(global_position + Vector2(0, -60), Color(1.0, 0.55, 0.25), 140.0, 1.4, 0.25)
			Ses.play("buyu", -8.0, 0.8, 0.08, 0.03, global_position)
		"zehir":
			FX.anim("acid_splash", global_position + Vector2(0, -6), 0.0, 0.7, Color(0.6, 1.0, 0.4))


func _draw() -> void:
	var tt := Time.get_ticks_msec() / 1000.0
	var fade := clampf((delay + life - _t) / 0.4, 0.0, 1.0)
	if not _armed:
		# kurulma: titreşen kızıl / türüne göre renkli fırça uyarısı (ortası kalın, iki yana incelen)
		var k := clampf(_t / maxf(0.05, delay), 0.0, 1.0)
		var on := int(_t * 14.0) % 2 == 0
		var c := Color(1.0, 0.3, 0.2, 0.55 + 0.35 * k) if on else Color(1.0, 0.8, 0.3, 0.45 + 0.3 * k)
		if kind == "zehir":
			c = Color(0.55, 1.0, 0.35, 0.5 + 0.4 * k) if on else Color(0.9, 1.0, 0.5, 0.4 + 0.3 * k)
		elif kind == "buz":
			c = Color(0.6, 0.85, 1.0, 0.5 + 0.4 * k) if on else Color(0.95, 1.0, 1.0, 0.4 + 0.3 * k)
		InkDraw.stroke(self, Vector2(-2, -1), Vector2(-w, -1), 4.5, c)
		InkDraw.stroke(self, Vector2(2, -1), Vector2(w, -1), 4.5, c)
		if kind == "sutun":
			InkDraw.ellipse(self, Vector2(0, -2), w * (0.6 + 0.4 * k), 5.0, Color(c, 0.35 * k))
			InkDraw.soft(self, Vector2(0, -6), 8.0 + 10.0 * k, Color(1.0, 0.6, 0.3, 0.3 * k))
		if kind == "serit":
			for i in int(w / 18.0):
				var x := -w + 9.0 + i * 18.0 + fmod(_t * 60.0, 18.0)
				InkDraw.stroke(self, Vector2(x, -3), Vector2(x + 9.0, -3), 2.5, Color(c, 0.6))
		return
	var at := _t - delay
	match kind:
		"zehir":
			InkDraw.ellipse(self, Vector2(0, -1), w * 1.05, 5.0, Color(0.12, 0.3, 0.08, 0.7 * fade), "duman_0")
			InkDraw.ellipse(self, Vector2(0, -2), w * 0.92, 3.6, Color(0.42, 0.95, 0.3, 0.75 * fade))
			for i in 5:
				var x := -w * 0.8 + i * w * 0.4
				var r := 3.0 + 2.0 * absf(sin(tt * 3.0 + i * 1.7 + _seed))
				InkDraw.soft(self, Vector2(x, -4 - absf(sin(tt * 2.0 + i)) * 4.0), r, Color(0.7, 1.0, 0.45, 0.55 * fade), i)
		"ates", "lav":
			InkDraw.ellipse(self, Vector2(0, -1), w * 1.05, 5.0, Color(1.0, 0.32, 0.06, 0.45 * fade), "duman_0")
			var n := maxi(4, int(w / 9.0))
			for i in n:
				var x := -w + (i + 0.5) * (2.0 * w / n)
				var hh := (8.0 + absf(sin(tt * 9.0 + i * 1.7 + _seed)) * 10.0) * (1.4 if kind == "lav" else 1.0)
				var sw := sin(tt * 7.0 + i) * 0.6
				InkDraw.flame(self, Vector2(x, 1), 8.0, hh, Color(1.3, 0.5, 0.14, 0.6 * fade), sw)
				InkDraw.flame(self, Vector2(x, 1), 4.0, hh * 0.6, Color(1.6, 1.1, 0.45, 0.8 * fade), sw * 0.6)
		"catlak":
			var glow := 0.5 + 0.5 * absf(sin(tt * 5.0 + _seed))
			var burst := clampf(1.0 - at / 0.35, 0.0, 1.0)
			InkDraw.ellipse(self, Vector2(0, -1), w * 1.1, 6.0, Color(0.08, 0.05, 0.05, 0.75 * fade), "duman_0")
			var rng := RandomNumberGenerator.new()
			rng.seed = _seed
			var x0 := -w
			var pts := PackedVector2Array()
			while x0 < w:
				pts.append(Vector2(x0, -1.5 + rng.randf_range(-2.0, 2.0)))
				x0 += rng.randf_range(7.0, 13.0)
			pts.append(Vector2(w, -1))
			InkDraw.line(self, pts, 5.0, 2.0, Color(0.06, 0.04, 0.04, 0.9 * fade))
			InkDraw.line(self, pts, 2.6, 1.0, Color(1.4, 0.6 + 0.3 * glow, 0.2, (0.6 + 0.4 * glow) * fade))
			for i in range(1, pts.size() - 1, 2):
				var p0: Vector2 = pts[i]
				InkDraw.stroke(self, p0, p0 + Vector2(rng.randf_range(-6, 6), -rng.randf_range(3, 8)), 2.0, Color(1.3, 0.55, 0.2, 0.6 * fade))
			if burst > 0.0:
				for i in 6:
					var x := -w + (i + 0.5) * (2.0 * w / 6.0)
					InkDraw.flame(self, Vector2(x, 0), 10.0, 26.0 * burst, Color(1.5, 0.6, 0.18, 0.8 * burst), sin(i * 2.0) * 0.4)
		"buz":
			var k2 := clampf(at / 0.08, 0.0, 1.0) * fade
			var n2 := maxi(3, int(w / 8.0))
			for i in n2:
				var x := -w + (i + 0.5) * (2.0 * w / n2)
				var hh := (22.0 + 16.0 * absf(sin(i * 2.3 + _seed))) * k2
				var pts2 := PackedVector2Array([Vector2(x - 4.5, 1), Vector2(x + sin(i * 1.3) * 2.0, -hh), Vector2(x + 4.5, 1)])
				draw_colored_polygon(pts2, Color(0.72, 0.9, 1.0, 0.85 * fade))
				draw_polyline(pts2, Color(0.15, 0.25, 0.4, 0.9 * fade), 1.2, true)
				InkDraw.stroke(self, Vector2(x - 1.0, -2.0), Vector2(x, -hh * 0.8), 1.6, Color(1.0, 1.0, 1.0, 0.7 * fade))
		"sutun":
			var k3 := clampf(at / 0.1, 0.0, 1.0) * fade
			var colr := Color(1.4, 0.55, 0.15) if not (source and "kind" in source and String(source.kind) == "yelbegen") else Color(0.7, 0.92, 1.3)
			InkDraw.quad(self, "alev", Vector2(0, -h * 0.5 * k3), Vector2(w * 2.4, h * k3), 0.0, Color(colr, 0.75 * k3))
			InkDraw.quad(self, "alev", Vector2(0, -h * 0.45 * k3), Vector2(w * 1.2, h * 0.9 * k3), 0.0, Color(1.6, 1.3, 0.7, 0.8 * k3))
			InkDraw.ellipse(self, Vector2(0, -2), w * 1.3, 6.0, Color(colr, 0.5 * k3), "duman_0")
		"serit":
			pass
