class_name GunParcasi
extends Node2D
## v42 Gün Örgüsü: boss devrilince düşen, Gün Ana'nın kesilmiş beş ışık örgüsünden biri (Al / Ak / Gök / Sarı / Altın;
## data/story.json "orguler"). Havada süzülür, yere iner, kendi rengiyle nefes alan sarmal bir örgü; oyuncu dokununca
## (ya da 3 sn sonra oyuncuya akar) alınır: kalıcı kayda yazılır (Hikaye.parca_al), Gün Ana görümü oynar, ekranın ufku
## o an ısınır (grade_v2 "safak" yükselir). Erlik'in Altın Örgüsü son sinemayı başlatır (Main.hikaye_son).

signal alindi(bid: String)

var bid := ""
var level: Node
var _t := 0.0
var _vy := -60.0
var _yerde := false
var _alindi := false
var _renk := Color(1.0, 0.8, 0.4)
var _isik: PointLight2D


func _ready() -> void:
	z_index = 30
	_renk = Hikaye.orgu_renk(bid)
	if level and level.has_method("add_light"):
		_isik = level.add_light(Vector2.ZERO, _renk.lerp(Color(1.0, 0.8, 0.45), 0.4), 220.0, 1.6, self)
	FX.ring(global_position, 70, _renk, 0.6)
	Ses.play("acilis", -4.0, 0.8)


func _physics_process(delta: float) -> void:
	_t += delta
	if _alindi:
		return
	if not _yerde:
		_vy = minf(_vy + 260.0 * delta, 120.0)
		var gy: float = level.ground_y_below(global_position, 60.0) if level else -1.0
		position.y += _vy * delta
		if gy > 0.0 and global_position.y >= gy - 34.0:
			global_position.y = gy - 34.0
			_yerde = true
	var pl: Node = level.player if level else null
	if pl == null or pl.dead:
		queue_redraw()
		return
	var hedef: Vector2 = pl.center() if pl.has_method("center") else pl.global_position
	var d := global_position.distance_to(hedef)
	if _t > 3.0:
		# oyuncuya akar (kapı açılmadan önce mutlaka alınsın)
		global_position = global_position.move_toward(hedef, (120.0 + (_t - 3.0) * 160.0) * delta)
	if (_t > 0.9 and d < 34.0) or d < 8.0:
		_al()
	queue_redraw()


func _al() -> void:
	_alindi = true
	var yeni := Hikaye.parca_al(bid)
	var o := Hikaye.orgu(bid)
	var pc: Vector2 = level.player.center() if level and level.player else global_position
	FX.ring(pc, 90, _renk, 0.8)
	FX.soul(pc, _renk, 40)
	FX.flash_light(pc, Color(1.0, 0.8, 0.45), 420.0, 2.4, 0.9)
	Game.slowmo(0.35, 0.6)
	Ses.play("kut_banka", -2.0, 0.85)
	Ses.play("ad_toren", -6.0, 1.1)
	var baslik := "%s · %s" % [InkHUD.tr_upper(String(o.get("ad", "Gün Örgüsü"))), String(o.get("alt", ""))]
	Gorum.gorum(String(o.get("gorum", "")), baslik, _renk, 6.0)
	Hikaye.gorum_isaretle("orgu:" + bid)
	# ufuk ısınır: ekran derecesinin "safak" değeri yeni örgü sayısına süzülür
	if level and level.get("vig_mat") != null:
		var vm: ShaderMaterial = level.vig_mat
		var tw := level.create_tween()
		tw.tween_method(func(v: float) -> void: vm.set_shader_parameter("safak", v), maxf(0.0, Hikaye.safak_k() - 0.11), Hikaye.safak_k() + 0.25, 1.6)
		tw.tween_method(func(v: float) -> void: vm.set_shader_parameter("safak", v), Hikaye.safak_k() + 0.25, Hikaye.safak_k(), 2.5)
	var m: Node = level.get_parent() if level else null
	if m and m.get("hud") != null:
		m.hud.flash_msg = ("%s döndü: Gün Ana'nın %d. örgüsü. Dünya bir tık ısındı." % [String(o.get("ad", "")), Hikaye.parca_sayi()]) if yeni else ("%s yine senin; Gün Ana seni tanıdı." % String(o.get("ad", "")))
		m.hud.flash_t = 5.0
	alindi.emit(bid)
	if m and m.has_method("hikaye_orgu_alindi"):
		m.hikaye_orgu_alindi(bid, yeni)
	var tw2 := create_tween()
	tw2.tween_property(self, "modulate:a", 0.0, 0.4)
	tw2.tween_callback(queue_free)


func _draw() -> void:
	## Sarmal örgü: üç iç içe geçen altın tel, rengiyle nefes alan hâle
	var nef := 0.8 + 0.2 * sin(_t * 3.0)
	var bob := sin(_t * 2.2) * 3.0
	draw_circle(Vector2(0, bob), 26.0 * nef, Color(_renk, 0.12), true, -1.0, true)
	draw_circle(Vector2(0, bob), 15.0 * nef, Color(_renk, 0.2), true, -1.0, true)
	for k in 3:
		var pts := PackedVector2Array()
		for i in 25:
			var u := float(i) / 24.0
			var y := lerpf(-24.0, 20.0, u) + bob
			var x := sin(u * TAU * 1.5 + _t * 2.0 + k * TAU / 3.0) * (7.0 - u * 3.0)
			pts.append(Vector2(x, y))
		var c := _renk.lerp(Color(1.0, 0.92, 0.7), 0.35 * float(k == 0))
		draw_polyline(pts, Color(0.05, 0.03, 0.02, 0.7), 4.0, true)
		draw_polyline(pts, c, 2.4, true)
	draw_circle(Vector2(0, -26 + bob), 3.0, Color(1.0, 0.95, 0.75), true, -1.0, true)
	if _isik:
		_isik.energy = 1.2 + 0.5 * nef
