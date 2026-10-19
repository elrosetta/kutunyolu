class_name EnemyBar
extends Node2D
## v22 düşman can çubuğu (stil v2 mürekkep): başın üstünde küçük bir fırça darbesi. Tam canda görünmez; hasar alınca
## belirir, savaş dışında birkaç saniye sonra söner. Katmanlar: mürekkep zemin → gecikmeli "hasar parçası" (açık
## kemik rengi; art arda vuruşlar tek parçada birikir, 0,45 sn sonra erir) → kızıl dolgu ve fırça ucu. Altında
## duruş çizgisi (ağır yaratıkta biriken duruş hasarı, hafifte diretme parıltısı; kırılınca turuncu çatlak), solda
## seçkin yıldızı ya da kalkan tırnakları, sağda küçük durum simgeleri (yanma, don, zehir yükü, kanama, damga, nazar).
## Boyu yaratığın boyuyla ölçeklenir; sayı yazmaz (hızlı kombolarda kalabalık etmesin). Bosslarda yok (HUD çubuğu).

var host: Node2D
var _a := 0.0          # görünürlük 0..1
var _lag := 1.0        # gecikmeli parça (can oranı)
var _hold := 0.0       # parça erimeden önce bekleme
var _prev := -1.0
var _hit_at := -99.0
var _flash := 0.0
var _t := 0.0
var _w := 34.0
var _h := 3.0

const SHOW_T := 3.5       # son vuruştan sonra en az bu kadar görünür
const NEAR_T := 9.0       # yakındaki öfkeli düşmanda en çok bu kadar
const HOLD := 0.45
const RED := Color(0.84, 0.12, 0.1)
const BONE := Color(1.0, 0.8, 0.52)
const GOLD := Color(1.0, 0.82, 0.38)


func _ready() -> void:
	z_index = 84
	var m := CanvasItemMaterial.new()
	m.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	material = m
	InkDraw.prep(self)
	var sz: Vector2 = host.size * host.base_scale
	_w = clampf(sz.x * 0.8 + 16.0, 26.0, 62.0)
	_h = 2.6 + clampf(sz.y / 70.0, 0.0, 1.0) * 1.0 + (0.5 if host.elite else 0.0)
	_prev = float(host.hp)
	position = Vector2(0, -sz.y - 11.0)


func shown() -> bool:
	return _a > 0.35


func _process(delta: float) -> void:
	if host == null or not is_instance_valid(host):
		return
	_t += delta
	var mhp := maxf(1.0, float(host.max_hp))
	var hp := clampf(float(host.hp), 0.0, mhp)
	if hp < _prev - 0.01:
		_hit_at = Game.clock()
		_flash = 1.0
		_hold = HOLD
	_prev = hp
	var k := hp / mhp
	if _lag < k:
		_lag = k
	if _hold > 0.0:
		_hold -= delta
	else:
		_lag = move_toward(_lag, k, delta * maxf(0.4, (_lag - k) * 3.0))
	_flash = maxf(0.0, _flash - delta * 7.0)
	var want := 0.0
	if k < 0.999 and not host.dead:
		var since := Game.clock() - _hit_at
		var near := false
		if host.aggro and host.level and host.level.player:
			near = host.global_position.distance_squared_to(host.level.player.global_position) < 280.0 * 280.0
		if since < SHOW_T or (near and since < NEAR_T):
			want = 1.0
	_a = move_toward(_a, want, delta * (12.0 if want > _a else 1.7))
	if host.elite_star and is_instance_valid(host.elite_star):
		host.elite_star.visible = _a < 0.5
	if _a > 0.001:
		queue_redraw()
	elif visible and _lag != k:
		_lag = k


func _draw() -> void:
	if _a <= 0.001 or host == null or not is_instance_valid(host):
		return
	var k := clampf(float(host.hp) / maxf(1.0, float(host.max_hp)), 0.0, 1.0)
	_draw_ink(k)


func _fill_col() -> Color:
	if host.ofkeli:
		return Color(0.95, 0.3, 0.08)
	if host.elite:
		return Color(0.86, 0.14, 0.32)
	return RED


func _draw_ink(k: float) -> void:
	var a := _a
	var w := _w
	var h := _h
	var x0 := -w * 0.5
	var st := InkUI.tex("stroke")
	var ts := st.get_size()
	var now := Game.clock()
	var broken: bool = float(host.broken_t) > 0.0
	var armored: bool = now < float(host._poise_until) and not host.is_boss
	# zemin: kalın mürekkep darbesi (çerçeve) + koyu kızıl oluk
	var edge := Color(InkUI.INK, 0.88 * a)
	if broken:
		edge = Color(1.0, 0.55, 0.15, (0.55 + 0.35 * sin(_t * 18.0)) * a)
	elif armored:
		edge = Color(GOLD.lerp(InkUI.INK, 0.35), 0.85 * a)
	# gölge + iki kat mürekkep: açık zeminde (sis, kar, gün ışığı) de okunur
	draw_texture_rect(st, Rect2(x0 - 3.0 + 1.0, -h * 0.5 - 3.0 + 1.4, w + 6.0, h + 6.0), false, Color(0, 0, 0, 0.35 * a))
	draw_texture_rect(st, Rect2(x0 - 3.5, -h * 0.5 - 3.0, w + 7.0, h + 6.0), false, edge)
	draw_texture_rect(st, Rect2(x0 - 1.5, -h * 0.5 - 1.6, w + 3.0, h + 3.2), false, Color(InkUI.INK, 0.9 * a))
	if host.elite:
		# seçkin: üstte ince altın kıl
		draw_texture_rect(st, Rect2(x0 - 1.0, -h * 0.5 - 2.4, w + 2.0, 1.1), false, Color(GOLD, 0.8 * a))
	draw_texture_rect(st, Rect2(x0, -h * 0.5, w, h), false, Color(0.22, 0.03, 0.04, a))
	# gecikmeli hasar parçası (k .. lag)
	if _lag > k + 0.002:
		var lc := BONE.lerp(Color.WHITE, _flash * 0.6)
		var lx := x0 + w * k
		var lw := w * (_lag - k)
		draw_texture_rect_region(st, Rect2(lx, -h * 0.5 + 0.2, lw, h - 0.4), Rect2(ts.x * k, 0, ts.x * (_lag - k), ts.y), Color(lc, 0.92 * a))
	# dolgu: kızıl fırça (doku soldan kırpılır) + üst kıl parıltısı + fırça ucu
	if k > 0.0:
		var fc := _fill_col().lerp(Color(1.0, 0.95, 0.9), _flash * 0.35)
		var fw := w * k
		draw_texture_rect_region(st, Rect2(x0, -h * 0.5, fw, h), Rect2(0, 0, ts.x * k, ts.y), Color(fc, a))
		draw_texture_rect_region(st, Rect2(x0 + 1.0, -h * 0.5 + h * 0.12, maxf(0.0, fw - 2.0), maxf(0.7, h * 0.28)), Rect2(0, ts.y * 0.2, ts.x * k, ts.y * 0.5), Color(fc.lightened(0.5), 0.5 * a))
		InkDraw.blot(self, Vector2(x0 + fw, 0.0), h * 0.42, Color(fc.lightened(0.25), 0.85 * a), int(host.get_instance_id() % 7))
	# duruş çizgisi (altta)
	var py := h * 0.5 + 2.6
	if broken:
		for i in 3:
			var cx := x0 + w * (0.25 + 0.25 * i)
			InkDraw.stroke(self, Vector2(cx - 2.0, py - 1.4), Vector2(cx + 1.5, py + 1.6), 1.4, Color(1.0, 0.6, 0.2, 0.9 * a))
	elif host.heavy and not host.is_boss:
		var need := float(Enemy.POISE["heavy_pts"]) * (1.6 if host.elite else 1.0)
		var pk := clampf(float(host.poise_pts) / need, 0.0, 1.0)
		if pk > 0.02:
			draw_texture_rect(st, Rect2(x0, py - 0.7, w, 1.4), false, Color(InkUI.INK, 0.6 * a))
			draw_texture_rect_region(st, Rect2(x0, py - 0.6, w * pk, 1.2), Rect2(0, 0, ts.x * pk, ts.y), Color(GOLD, (0.75 + 0.25 * pk) * a))
	elif armored:
		draw_texture_rect(st, Rect2(x0 + w * 0.15, py - 0.6, w * 0.7, 1.2), false, Color(GOLD, 0.6 * a))
	# sol uç: seçkin yıldızı / kalkan tırnakları
	var lx0 := x0 - 6.5
	if host.elite:
		InkDraw.soft(self, Vector2(lx0, 0), 6.0, Color(0.8, 0.4, 1.0, 0.35 * a))
		InkDraw.star(self, Vector2(lx0, 0), 5.2, _t * 0.8, Color(0.4, 0.12, 0.5, a))
		InkDraw.star(self, Vector2(lx0, 0), 4.2, _t * 0.8, Color(GOLD, a))
		lx0 -= 9.0
	if (host.ai == "shield" or host.ai == "charger") and int(host.guard_hp) > 0:
		for i in int(host.guard_hp):
			var p := Vector2(lx0 - i * 3.6, 0.0)
			InkDraw.blot(self, p, 1.7, Color(InkUI.INK, 0.8 * a), i)
			InkDraw.blot(self, p, 1.1, Color(0.82, 0.86, 0.95, 0.95 * a), i + 3)
	# sağ uç: durum simgeleri
	var icons := _icons()
	var ix := -x0 + 6.0
	for ic in icons:
		_icon(String(ic[0]), Vector2(ix, 0.0), int(ic[1]), a)
		ix += 7.5


func _icons() -> Array:
	var out: Array = []
	if float(host.burn_t) > 0.0:
		out.append(["ates", 0])
	var chill := 0
	if host.has_meta("unsur"):
		chill = int(host.get_meta("unsur").get("chill", 0))
	if float(host.freeze_t) > 0.0 or chill > 0 or int(host.frost) > 0:
		out.append(["buz", chill + int(host.frost)])
	if int(host.poison) > 0:
		out.append(["zehir", int(host.poison)])
	if int(host.bleed) > 0:
		out.append(["kan", int(host.bleed)])
	if host.has_meta("unsur") and float(host.get_meta("unsur").get("mark_t", 0.0)) > 0.0:
		out.append(["damga", 0])
	if float(host.cursed_t) > 0.0:
		out.append(["nazar", 0])
	return out


func _icon(kind: String, p: Vector2, n: int, a: float) -> void:
	match kind:
		"ates":
			InkDraw.flame(self, p + Vector2(0, 2.8), 3.8, 6.5, Color(1.0, 0.55, 0.15, a), sin(_t * 18.0) * 0.3)
			InkDraw.flame(self, p + Vector2(0, 2.8), 2.0, 3.4, Color(1.0, 0.95, 0.5, a))
		"buz":
			var frozen: bool = float(host.freeze_t) > 0.0
			InkDraw.star(self, p, 3.4 if frozen else 2.8, 0.0, Color(0.75, 0.95, 1.0, a))
			InkDraw.star(self, p, 2.3, PI * 0.25, Color(0.88, 1.0, 1.0, 0.8 * a))
		"zehir":
			InkDraw.drop(self, p + Vector2(0, 0.4), 2.4, PI * 0.5, Color(0.45, 0.9, 0.25, a))
		"kan":
			InkDraw.drop(self, p + Vector2(0, 0.4), 2.3, PI * 0.5, Color(0.88, 0.12, 0.15, a))
		"damga":
			InkDraw.ring(self, p, 3.0, 3.0, Color(0.8, 0.95, 0.75, 0.9 * a), _t * 2.0)
			InkDraw.blot(self, p, 1.2, Color(0.85, 1.0, 0.8, a))
		"nazar":
			InkDraw.ellipse(self, p, 3.4, 2.1, Color(0.3, 0.5, 1.0, 0.9 * a))
			InkDraw.blot(self, p, 1.1, Color(0.95, 0.97, 1.0, a))
	# yük: simgenin altında küçük noktalar (zehir / kanama / don yükü)
	if n > 1:
		for i in mini(n, 5):
			InkDraw.blot(self, p + Vector2(-2.4 + i * 1.6, 4.4), 0.7, Color(1.0, 0.95, 0.85, 0.85 * a), i)
