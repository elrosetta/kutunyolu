class_name MuhurDamga
extends Node2D
## v44 Mühür yolu: yaratığa basılan Erlik damgası (yaratığın çocuğu; MuhurYolu.dogdu verir, değerler zorluk.json
## "damgalar"). Enemy.take_hit başında hasar(), Enemy._die başında oldu() çağrılır (meta "muhur_damga").
##   ofkeli    (II+, seçkin) daha hızlı, daha sabırsız; kızıl kor halesi
##   kalkanli  (II+, seçkin) önden gelen vuruşu %65 keser; 6 ön vuruşta kırılır, kırılınca sersemler — arkadan vur
##   bolunen   (II+, seçkin) ölünce iki küçük gölge yavruya bölünür
##   tamu      (IV, sıradan yaratık, Tamu dışı bölüm) Tamu bekçisi: kömür karası / kor kızılı mürekkep, daha dayanıklı;
##             yeni hamle "kor yağmuru" (hazırlıkta göğsünde kor halkası büyür, sonra yay çizen üç kor atar) ve ölünce
##             gecikmeli patlar. Öldürene ek Kut / altın.

var e: Node
var turler: Array = []
var kalkan := 0
var _t := 0.0
var _atis := 3.0
var _hazir := -1.0
var _kirildi_t := -1.0
var atis_sayisi := 0      # test
var _kor: CPUParticles2D


static func ekle(en: Node, tl: Array) -> MuhurDamga:
	var d := MuhurDamga.new()
	d.e = en
	d.turler = tl.duplicate()
	d.name = "MuhurDamga"
	en.add_child(d)
	en.set_meta("muhur_damga", d)
	return d


func has(t: String) -> bool:
	return t in turler


func _ready() -> void:
	z_index = 6
	var tint: Color = e.base_tint
	if has("ofkeli"):
		var o: Dictionary = MuhurYolu.damga_def("ofkeli")
		e.speed *= float(o.get("hiz", 1.2))
		e._aggr *= float(o.get("saldirganlik", 1.3))
		e._wind_k *= float(o.get("hazirlik", 1.15))
		tint = tint * Color(1.2, 0.78, 0.72)
	if has("kalkanli"):
		kalkan = int(MuhurYolu.damga_def("kalkanli").get("vurus", 6))
	if has("bolunen"):
		tint = tint * Color(0.92, 0.85, 1.12)
	if has("tamu"):
		var tm: Dictionary = MuhurYolu.damga_def("tamu")
		e.max_hp *= float(tm.get("can", 1.4))
		e.hp = e.max_hp
		e.dmg *= float(tm.get("hasar", 1.15))
		tint = Color(1.5, 0.5, 0.36)
		e.base_scale = e.base_scale * 1.08
		if e.anim:
			e.anim.scale = e.base_scale
		var a: Array = tm.get("atis", [3.6, 5.2])
		_atis = randf_range(float(a[0]), float(a[1])) * 0.6
		if e.level:
			e.level.add_light(Vector2(0, -e.size.y * 0.5), Color(1.0, 0.32, 0.12), 110.0, 0.75, e)
		# Tamu'nun külü: gövdeden yükselen kor kıvılcımları (bekçi uzaktan seçilsin)
		var pe := CPUParticles2D.new()
		pe.amount = 14
		pe.lifetime = 1.3
		pe.position = Vector2(0, -e.size.y * 0.5)
		pe.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
		pe.emission_rect_extents = Vector2(e.size.x * 0.5, e.size.y * 0.45)
		pe.direction = Vector2(0, -1)
		pe.spread = 25.0
		pe.gravity = Vector2(0, -40)
		pe.initial_velocity_min = 8.0
		pe.initial_velocity_max = 22.0
		pe.scale_amount_min = 1.0
		pe.scale_amount_max = 2.2
		var gr := Gradient.new()
		gr.set_color(0, Color(1.0, 0.65, 0.25, 0.95))
		gr.set_color(1, Color(0.6, 0.08, 0.04, 0.0))
		pe.color_ramp = gr
		var pm := CanvasItemMaterial.new()
		pm.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
		pe.material = pm
		pe.z_index = 1
		add_child(pe)
		_kor = pe
	e.base_tint = tint
	if e.anim:
		e.anim.set_tint(tint)
	if e.get("_label") != null and is_instance_valid(e._label):
		var adlar: Array = []
		for t in turler:
			adlar.append(String(MuhurYolu.DAMGA_AD.get(t, t)).to_upper())
		e._label.text = "%s\n%s" % [" · ".join(adlar), e._label.text] if e._label.text != "" else " · ".join(adlar)
		e._label.position.y -= 10.0
		e._label.size.y = 24.0


func adlar() -> String:
	var a: Array = []
	for t in turler:
		a.append(String(MuhurYolu.DAMGA_AD.get(t, t)))
	return ", ".join(a)


# ------------------------------------------------------------------ Enemy kancaları
func hasar(d: float, opts: Dictionary) -> float:
	if has("kalkanli") and kalkan > 0 and not bool(opts.get("exec", false)):
		var on: bool = signf(float(opts.get("dir", 1))) == -float(e.facing)
		if on:
			var kd: Dictionary = MuhurYolu.damga_def("kalkanli")
			kalkan -= 1
			d *= float(kd.get("hasar", 0.35))
			var c: Vector2 = e.center() + Vector2(float(e.facing) * e.size.x * 0.6, -4)
			FX.sparks(c, Vector2(float(e.facing), -0.5), Color(0.75, 0.6, 1.0), 6, 150.0)
			if kalkan <= 0:
				_kirildi_t = 0.0
				FX.ring(c, 26, Color(0.8, 0.6, 1.0), 0.4)
				FX.text(e.center() + Vector2(0, -e.size.y * 0.6 - 16), "kalkan kırıldı!", Color(0.85, 0.7, 1.0), 8)
				Ses.play("darbe_metal", -4.0)
				if e.has_method("stun"):
					e.stun(float(kd.get("sersem", 1.4)))
			queue_redraw()
	return d


func oldu() -> void:
	if e == null or e.level == null:
		return
	var lv: Node = e.level
	var c: Vector2 = e.center()
	if has("bolunen"):
		var bd: Dictionary = MuhurYolu.damga_def("bolunen")
		_bolun.call_deferred(lv, String(e.kind), e.global_position, int(bd.get("yavru", 2)), float(bd.get("can", 0.3)), float(bd.get("boy", 0.72)), float(e.max_hp))
	if has("tamu"):
		var tm: Dictionary = MuhurYolu.damga_def("tamu")
		var dmg := float(e.dmg) * 0.8
		FX.text(c + Vector2(0, -26), "!!", Color(1.0, 0.45, 0.15), 10)
		lv.get_tree().create_timer(float(tm.get("patlama", 0.55))).timeout.connect(Callable(lv, "explode").bind(c, 46.0, dmg, false))
		for i in 4:
			lv.drop_orb("kut", c)
		for i in 6:
			lv.drop_orb("gold", c)


static func _bolun(lv: Node, kind: String, pos: Vector2, n: int, can: float, boy: float, max_hp: float) -> void:
	if not is_instance_valid(lv):
		return
	MuhurYolu._yavru = true
	for i in n:
		var s := -1.0 if i % 2 == 0 else 1.0
		var y: Node = lv.spawn_enemy(kind, pos + Vector2(s * (14.0 + 8.0 * i), 0), false, false, true)
		if y == null:
			continue
		y.max_hp = max_hp * can
		y.hp = y.max_hp
		y.base_scale = Vector2(boy, boy)
		if y.anim:
			y.anim.scale = y.base_scale
			y.base_tint = Color(0.75, 0.62, 1.05)
			y.anim.set_tint(y.base_tint)
		y.velocity = Vector2(s * 160.0, -180.0)
		FX.anim("smoke_puff", y.center(), 0.0, 0.7, Color(0.55, 0.35, 0.85), false)
	MuhurYolu._yavru = false
	FX.text(pos + Vector2(0, -40), "bölündü!", Color(0.8, 0.6, 1.0), 8)


# ------------------------------------------------------------------ Tamu bekçisinin kor yağmuru
func _physics_process(delta: float) -> void:
	_t += delta
	if e == null or not is_instance_valid(e) or e.dead:
		set_physics_process(false)
		if _kor:
			_kor.emitting = false
		queue_redraw()
		return
	if _kirildi_t >= 0.0:
		_kirildi_t += delta
	if has("tamu"):
		_tamu(delta)
	if has("kalkanli") or has("ofkeli") or has("tamu") or has("bolunen"):
		queue_redraw()


func _tamu(delta: float) -> void:
	var lv: Node = e.level
	if lv == null or lv.player == null or lv.player.dead:
		return
	var tm: Dictionary = MuhurYolu.damga_def("tamu")
	var to_p: Vector2 = lv.player.center() - e.center()
	if _hazir >= 0.0:
		_hazir += delta
		if _hazir >= float(tm.get("hazirlik", 0.7)):
			_hazir = -1.0
			_kor_at(to_p, tm)
		return
	if String(e.get("state")) in ["dormant", "lurk", "perch"] or float(e.stun_t) > 0.0:
		return
	if absf(to_p.x) > 330.0 or absf(to_p.y) > 140.0:
		return
	_atis -= delta
	if _atis <= 0.0:
		var a: Array = tm.get("atis", [3.6, 5.2])
		_atis = randf_range(float(a[0]), float(a[1]))
		_hazir = 0.0
		e.facing = 1 if to_p.x > 0.0 else -1
		FX.text(e.center() + Vector2(0, -e.size.y * 0.6 - 10), "!", Color(1.0, 0.4, 0.15), 10)


func _kor_at(to_p: Vector2, tm: Dictionary) -> void:
	atis_sayisi += 1
	var from: Vector2 = e.center() + Vector2(float(e.facing) * 8.0, -e.size.y * 0.2)
	var g := 300.0
	var tt := clampf(absf(to_p.x) / 220.0, 0.55, 1.2)
	for k in 3:
		var dx := to_p.x + (k - 1) * 46.0
		var v := Vector2(dx / tt, to_p.y / tt - 0.5 * g * tt)
		e._spit("fireball", from, v, float(e.dmg) * float(tm.get("kor_hasar", 0.6)), 0.0, g, 2.6)
	FX.burst(from, Color(1.0, 0.5, 0.2), 12, 90, 0.4, 0.2, -60, true)
	Game.shake(1.5)


func _draw() -> void:
	if e == null or not is_instance_valid(e) or e.dead:
		return
	var h: float = e.size.y * float(e.base_scale.y)
	var c := Vector2(0, -h * 0.5)
	if has("kalkanli") and kalkan > 0:
		# önde yarım ay kalkan: kalan vuruş kadar kalın, mor mürekkep
		var f := float(e.facing)
		var r := h * 0.62
		var k := float(kalkan) / float(MuhurYolu.damga_def("kalkanli").get("vurus", 6))
		var a0 := -PI * 0.42 if f > 0 else PI - PI * 0.42
		var col := Color(0.72, 0.55, 1.0, 0.55 + 0.25 * sin(_t * 5.0))
		draw_arc(c, r, a0, a0 + PI * 0.84, 18, Color(0.1, 0.05, 0.16, 0.7), 4.0 + 3.0 * k, true)
		draw_arc(c, r, a0, a0 + PI * 0.84, 18, col, 1.5 + 2.0 * k, true)
	if _kirildi_t >= 0.0 and _kirildi_t < 0.4:
		draw_arc(c, h * 0.62 + _kirildi_t * 60.0, 0, TAU, 24, Color(0.85, 0.7, 1.0, 1.0 - _kirildi_t / 0.4), 2.0, true)
	if has("ofkeli"):
		var p := 0.5 + 0.5 * sin(_t * 9.0)
		draw_arc(c, h * 0.45, 0, TAU, 20, Color(1.0, 0.3, 0.15, 0.12 + 0.1 * p), 5.0, true)
	if has("bolunen"):
		for i in 2:
			var a := _t * 1.6 + PI * i
			draw_circle(c + Vector2(cos(a), sin(a) * 0.5) * h * 0.5, 2.5, Color(0.7, 0.5, 1.0, 0.7))
	if has("tamu"):
		# göğüste kor; hazırlıkta büyüyen kızıl halka (kor yağmurunun uyarısı)
		var ember := Color(1.0, 0.42, 0.12, 0.55 + 0.25 * sin(_t * 7.0))
		draw_circle(c + Vector2(0, -2), 3.0, ember)
		if _hazir >= 0.0:
			var u := clampf(_hazir / float(MuhurYolu.damga_def("tamu").get("hazirlik", 0.7)), 0.0, 1.0)
			draw_arc(c, 6.0 + 18.0 * (1.0 - u), 0, TAU, 24, Color(1.0, 0.35, 0.1, 0.25 + 0.5 * u), 1.5 + 1.5 * u, true)
			draw_circle(c, 3.0 + 4.0 * u, Color(1.0, 0.6, 0.2, 0.4 * u))
		# isimlik (sıradan yaratığın etiketi yok)
		var f: Font = InkUI.font("caps")
		var s := "TAMU BEKÇİSİ"
		var w := f.get_string_size(s, HORIZONTAL_ALIGNMENT_LEFT, -1, 7).x
		draw_string_outline(f, Vector2(-w * 0.5, -h - 12), s, HORIZONTAL_ALIGNMENT_LEFT, -1, 7, 3, Color(0.08, 0.02, 0.02, 0.9))
		draw_string(f, Vector2(-w * 0.5, -h - 12), s, HORIZONTAL_ALIGNMENT_LEFT, -1, 7, Color(1.0, 0.5, 0.3))
