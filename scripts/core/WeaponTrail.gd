class_name WeaponTrail
extends Node2D
## Savuruş izi (tek efekt): her karede bıçağın kök ve uç noktası kaydedilir; aralarına yaşla solan bir
## şerit çizilir. Bıçak boyunca renkli gövde, uç kenarında beyaz parlak çekirdek (Dead Cells savuruş izi).
## Eski örnekler hem solar hem de uca doğru incelir: iz, kılıcın arkasında kuyruklu bir yay gibi okunur.

var col := Color(1, 0.95, 0.8)
var width_mul := 1.0
var life := 0.14
var done := false
var _pts: Array = []  # [kök, uç, zaman]
var _t := 0.0


func _ready() -> void:
	z_index = 56
	var m := CanvasItemMaterial.new()
	m.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	m.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	material = m
	top_level = true


func add(base: Vector2, tip: Vector2) -> void:
	if _pts.size() > 0:
		var last: Array = _pts[_pts.size() - 1]
		if last[1].distance_to(tip) < 0.8:
			return
		# Hızlı savuruşta iki kare arasında bıçak 90°+ dönebilir: düz şerit yay yerine "V" çizer.
		# Ara örnekler kabza etrafında açı adım adım döndürülerek eklenir (en çok 0,22 rad).
		var lb: Vector2 = last[0]
		var lv: Vector2 = last[1] - lb
		var nv: Vector2 = tip - base
		if lv.length() > 1.0 and nv.length() > 1.0:
			var da := wrapf(nv.angle() - lv.angle(), -PI, PI)
			var steps := mini(int(ceil(absf(da) / 0.22)), 24)
			for s in range(1, steps):
				var k := float(s) / float(steps)
				var bb := lb.lerp(base, k)
				var vv := Vector2.from_angle(lv.angle() + da * k) * lerpf(lv.length(), nv.length(), k)
				_pts.append([bb, bb + vv, lerpf(float(last[2]), _t, k)])
	_pts.append([base, tip, _t])


func _process(delta: float) -> void:
	_t += delta
	while _pts.size() > 0 and _t - float(_pts[0][2]) > life:
		_pts.pop_front()
	if _pts.is_empty() and done:
		queue_free()
		return
	queue_redraw()


func _fill_quad(q: PackedVector2Array, c: Color) -> void:
	## Dışbükey dörtgeni tam sayı piksel satırlarıyla doldurur (tarama çizgisi): kenarlar merdiven, bulanıklık yok.
	var y0 := floori(minf(minf(q[0].y, q[1].y), minf(q[2].y, q[3].y)))
	var y1 := ceili(maxf(maxf(q[0].y, q[1].y), maxf(q[2].y, q[3].y)))
	for y in range(y0, y1):
		var yc := y + 0.5
		var xa := INF
		var xb := -INF
		for i in 4:
			var a: Vector2 = q[i]
			var b: Vector2 = q[(i + 1) % 4]
			if (a.y <= yc and b.y > yc) or (b.y <= yc and a.y > yc):
				var x := a.x + (yc - a.y) / (b.y - a.y) * (b.x - a.x)
				xa = minf(xa, x)
				xb = maxf(xb, x)
		if xa < xb:
			var l := roundf(xa)
			var r := roundf(xb)
			if r <= l:
				r = l + 1.0
			draw_rect(Rect2(l, y, r - l, 1), c)


func _draw() -> void:
	## Piksel savuruş izi: üç katı bant (koyu iç kenar, silah rengi gövde, beyaz uç çekirdeği).
	## Yaş üç kademede söner ve izin kökü uca doğru yenir; geçiş yumuşak değil, kare kare.
	if _pts.size() < 2:
		return
	var n := _pts.size()
	var body := Color(col.r * 1.1, col.g * 1.05, col.b * 1.0, 1.0)
	var inner := Color(col.r * 0.55, col.g * 0.5, col.b * 0.65, 1.0)
	var core := Color(1.4, 1.38, 1.3, 1.0)
	for i in range(n - 1):
		var a: Array = _pts[i]
		var b: Array = _pts[i + 1]
		var age := clampf((_t - float(b[2])) / life, 0.0, 1.0)
		var stage := int(age * 3.0)  # 0 taze, 1 orta, 2 sönmekte
		if stage >= 3:
			continue
		# iz = bıçağın UCUNUN süpürdüğü ince hilal (tüm bıçak boyu değil): başta kalın, kuyruğa doğru incelir
		var alpha: float = [0.9, 0.55, 0.25][stage]
		var w: float = [0.34, 0.22, 0.11][stage] * clampf(width_mul, 0.3, 1.4)
		var ta: Vector2 = a[1]
		var tb: Vector2 = b[1]
		var ia: Vector2 = ta + (a[0] - ta) * w
		var ib: Vector2 = tb + (b[0] - tb) * w
		var ma: Vector2 = ta + (a[0] - ta) * w * 0.7
		var mb: Vector2 = tb + (b[0] - tb) * w * 0.7
		_fill_quad(PackedVector2Array([ia, ma, mb, ib]), Color(inner, alpha * 0.7))
		_fill_quad(PackedVector2Array([ma, ta, tb, mb]), Color(body, alpha))
		if stage < 1:
			var ca: Vector2 = ta + (a[0] - ta) * 0.09
			var cb: Vector2 = tb + (b[0] - tb) * 0.09
			_fill_quad(PackedVector2Array([ca, ta, tb, cb]), Color(core, alpha))
