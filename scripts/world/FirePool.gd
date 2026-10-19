class_name FirePool
extends Node2D
## Od Testisi'nin bıraktığı alev gölü: içindeki düşmanları yakar.
## v25 (stil v2): od unsurunun gerçekçi mürekkep alevi (shaders/ink_brush.gdshader, InkTrail ile aynı zerreler): kor yatağı
## (kara kabuk + kızgın çatlaklar), üstünde döngüyle doğup yükselen ve tepeden kopan alev dilleri, korlar, seyrek is.
## Tek çizim çağrısı; CPU parçacığı yok.

var level: Node
var radius := 32.0
var life := 4.0
var dps := 3.0
var _tick := 0.0
var _t := 0.0
var _seed := randf() * 10.0
var _vp := PackedVector2Array()
var _vuv := PackedVector2Array()
var _vcol := PackedColorArray()
var _vidx := PackedInt32Array()


func _ready() -> void:
	z_index = 8
	material = InkTrail.elem_material(Unsur.pal("od"), "od")


func _process(delta: float) -> void:
	_t += delta
	life -= delta
	if life <= 0.0:
		queue_free()
		return
	_tick -= delta
	if _tick <= 0.0:
		_tick = 0.4
		var box := Rect2(global_position + Vector2(-radius, -26), Vector2(radius * 2.0, 28))
		for e in get_tree().get_nodes_in_group("dusman"):
			if is_instance_valid(e) and not e.dead and box.intersects(e.hurt_rect()):
				e.take_hit(dps, {"burn": 3.0, "kb": 0.0})
	queue_redraw()


func _q(tail: Vector2, head: Vector2, hw: float, typ: int, age: float) -> void:
	## gölgelendirici zerre dörtgeni (InkTrail._elem_draw ile aynı kodlama: katman 3, UV.x = tür x 2 + u)
	var ax := head - tail
	var nrm := (ax.normalized().orthogonal() if ax.length() > 0.01 else Vector2.DOWN) * hw
	var st := _vp.size()
	var u0 := float(typ) * 2.0
	for e in [[tail - nrm, u0, 6.0], [tail + nrm, u0, 7.0], [head - nrm, u0 + 1.0, 6.0], [head + nrm, u0 + 1.0, 7.0]]:
		_vp.append(e[0])
		_vuv.append(Vector2(e[1], e[2]))
		_vcol.append(Color(1, 1, 1, age))
	_vidx.append_array([st, st + 1, st + 2, st + 1, st + 3, st + 2])


func _draw() -> void:
	var a := clampf(life, 0.0, 1.0)
	# v25: kor yatağı + döngüyle doğan alev dilleri (her dil kendi evresinde doğar, boy atar, yükselip tepeden
	# is tutamına kopar) + yükselen korlar + seyrek is. Göl söndükçe (son 1 sn) diller kısalır, yatak kararır.
	_vp.clear()
	_vuv.clear()
	_vcol.clear()
	_vidx.clear()
	var grow := clampf(_t / 0.2, 0.0, 1.0)
	var k_life := a * grow
	_q(Vector2(-radius * 1.15, -1.0), Vector2(radius * 1.15, -1.0), 4.5, 10, 1.0 - a * 0.85)
	var n := int(radius / 5.0) + 3
	for k in n:
		var fk := float(k) / float(maxi(1, n - 1))
		var ph := fmod(_t * (2.6 + 0.7 * sin(float(k) * 2.3 + _seed)) + float(k) * 0.37 + _seed, 1.0)
		var x := (fk * 2.0 - 1.0) * radius * 0.92 + sin(float(k) * 5.1 + _seed) * 3.0
		var edge := 1.0 - 0.55 * absf(fk * 2.0 - 1.0)
		var h := (16.0 + 12.0 * absf(sin(float(k) * 1.9 + _seed))) * edge * (0.55 + 0.45 * k_life)
		var rise := ph * 5.0
		var base := Vector2(x, 1.5 - rise)
		var lean := sin(_t * 3.0 + float(k)) * 0.12
		var ax := Vector2.from_angle(-PI * 0.5 + lean)
		_q(base - ax * h * 0.15, base + ax * h * 0.85, h * 0.36, 3, clampf(ph * 0.9 + (1.0 - k_life) * 0.5, 0.0, 1.0))
	for k in 4:
		var ph2 := fmod(_t * 1.6 + float(k) * 0.25 + _seed, 1.0)
		var ex := sin(float(k) * 3.7 + _seed + floor(_t * 1.6 + float(k) * 0.25)) * radius * 0.8
		var ep := Vector2(ex + sin(ph2 * 6.0 + float(k)) * 4.0, -4.0 - ph2 * 34.0)
		_q(ep + Vector2(0, 2.4), ep - Vector2(0, 2.4), 1.0, 8, ph2)
	for k in 2:
		var ph3 := fmod(_t * 0.9 + float(k) * 0.5 + _seed, 1.0)
		var sx := sin(float(k) * 4.1 + _seed + floor(_t * 0.9 + float(k) * 0.5)) * radius * 0.6
		var sp := Vector2(sx, -14.0 - ph3 * 22.0)
		var ss := 6.0 + ph3 * 6.0
		_q(sp - Vector2(ss, 0), sp + Vector2(ss, 0), ss, 6, clampf(ph3 + (1.0 - a) * 0.5, 0.0, 1.0))
	RenderingServer.canvas_item_add_triangle_array(get_canvas_item(), _vidx, _vp, _vcol, _vuv)
