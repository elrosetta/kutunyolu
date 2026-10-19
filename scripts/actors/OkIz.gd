class_name OkIz
extends Node2D
## v25 ok / fırlatılan silah mürekkep izi (stil v2). Okun arkasında çok ince (1080p'de 1,5-3 px), kısa, kuyruğa incelen,
## kenarı yumuşatılmış fırça çizgisi; rengi okun unsuruna göre:
##   od turuncu-kızıl (+ küçük alev kıvılcımı) · ayaz buz mavisi (+ kırağı zerresi) · yıldırım parlak mavi-beyaz
##   (çizgi titrer, minik kıvılcım) · kam mor (+ ruh zerresi) · yersu yeşil (+ yaprak) · altın tam bırakış
##   (+ minik yıldız) · unsursuz koyu mürekkep, soluk kızıl çekirdek.
## İz ayrı bir düğümdür (FX.root altında): ok saplanınca / düşmana değip yok olunca iz bir anda kaybolmaz, kalan
## noktalar yaşlanıp kuyruktan başa doğru incelerek erir (eskiden iz okla birlikte siliniyordu, hızlı okta
## neredeyse hiç görünmüyordu). Çizim tek üçgen şeridi + shaders/ok_iz.gdshader (kenar yumuşatma piksel genişliğinden).
## v31: iz başın hemen arkasında bir tık dolgun (basınç) sonra kıl inceliğine iner; güçlü atışta (tam gerilme, unsur)
## izin iki yanında hafifçe açılan iki kıl inceliğinde hava teli; ok ucunda titreşen küçük iğne yıldızı (unsur renginde
## parıltı, unsursuzda soluk çelik) — hepsi aynı çizim çağrısında.

const AGE := 0.07                 # bir nokta bu kadar yaşayınca düşer (iz boyu ~ hız x AGE)
const IZ_SHADER: Shader = preload("res://shaders/ok_iz.gdshader")
## unsur -> [çekirdek rengi (HDR olabilir), zerre]
const RENK := {
	"od": Color(1.25, 0.46, 0.14), "ayaz": Color(0.62, 0.9, 1.2), "yildirim": Color(1.05, 1.15, 1.45),
	"kam": Color(0.78, 0.5, 1.25), "yersu": Color(0.5, 1.0, 0.36), "altin": Color(1.3, 0.98, 0.45),
	"": Color(0.62, 0.1, 0.07)}
static var _mat: ShaderMaterial

var host: Node2D
var col := Color(0.62, 0.1, 0.07)
var unsur := ""
var w := 0.4                       # baştaki yarı genişlik (dünya birimi; 1080p'de x3,4 px)
var head_back := 6.0               # iz okun gövdesinin ortasından başlasın (ucun önüne taşmasın)
var _pts: Array = []               # [global konum, doğuş zamanı]
var _t := 0.0
var _stopped := false
var _jit: Array = []               # yıldırım: noktaların enine titreşimi
var _parca: Node2D = null
var _dir := Vector2.RIGHT


static func attach(h: Node2D, u: String, width := 0.4, back := 6.0) -> OkIz:
	## h (ok / fırlatılan silah) için iz oluşturur; v1 piksel kipinde ya da FX.root yoksa null
	if FX.root == null or h == null:
		return null
	var z := OkIz.new()
	z.host = h
	z.unsur = u if RENK.has(u) else ""
	z.col = RENK[z.unsur]
	z.w = width
	z.head_back = back
	FX.root.add_child(z)
	return z


func _ready() -> void:
	top_level = true
	global_position = Vector2.ZERO
	z_index = 19   # mermi (20) altında
	if _mat == null:
		_mat = ShaderMaterial.new()
		_mat.shader = IZ_SHADER
		_mat.set_shader_parameter("bristle", InkTrail.BRISTLE)
	material = _mat


func stop() -> void:
	_stopped = true


func _flying() -> bool:
	if host == null or not is_instance_valid(host) or host.is_queued_for_deletion():
		return false
	if host.has_method("iz_flying"):
		return bool(host.call("iz_flying"))
	return true


func _physics_process(delta: float) -> void:
	_t += delta
	if not _stopped and not _flying():
		_stopped = true
	if not _stopped:
		var v: Variant = host.get("velocity")
		if v is Vector2 and (v as Vector2).length() > 1.0:
			_dir = (v as Vector2).normalized()
		_pts.push_front([host.global_position - _dir * head_back, _t])
		_jit.push_front(randf_range(-1.0, 1.0))
		if int(_t * 60.0) % 3 == 0:
			_mote(host.global_position)
	while _pts.size() > 0 and _t - float(_pts[_pts.size() - 1][1]) > AGE:
		_pts.pop_back()
		_jit.pop_back()
	if _stopped and _pts.size() < 2:
		queue_free()
		return
	if unsur == "yildirim" and Engine.get_physics_frames() % 2 == 0:
		for i in _jit.size():
			_jit[i] = randf_range(-1.0, 1.0)
	queue_redraw()


func _mote(at: Vector2) -> void:
	## unsur zerresi: okun ardında küçük, kısa ömürlü mürekkep parçacığı (Unsur.Parca; piksel kare yok)
	if unsur == "":
		return
	if _parca == null or not is_instance_valid(_parca) or _parca.is_queued_for_deletion():
		_parca = Unsur.parca(at, true)
		if _parca == null:
			return
	var p: Unsur.Parca = _parca
	var side := Vector2(-_dir.y, _dir.x) * randf_range(-2.0, 2.0)
	match unsur:
		"od":
			p.add("alev", at + side, -_dir * 30.0 + Vector2(0, -30), Vector2(2.4, 3.4) * randf_range(0.8, 1.2), 0.22, Color(1.0, 0.5, 0.18, 0.9), -60.0)
		"ayaz":
			p.add("kul", at + side, -_dir * 20.0 + Vector2(randf_range(-15, 15), 10), Vector2(1.8, 1.8), 0.35, Color(0.7, 0.92, 1.0, 0.85), 30.0, true)
		"yildirim":
			p.add("kivilcim", at + side, Vector2.from_angle(randf() * TAU) * 70.0, Vector2(0.9, 3.4), 0.11, Color(0.85, 0.92, 1.0, 1.0))
		"kam":
			p.add("nokta", at + side, -_dir * 15.0 + Vector2(0, -20), Vector2(2.6, 2.6), 0.4, Color(0.7, 0.5, 1.0, 0.7), -25.0)
		"yersu":
			p.add("yaprak", at + side, -_dir * 25.0 + Vector2(0, -10), Vector2(2.4, 2.4), 0.45, Color(0.5, 0.88, 0.32, 0.9), 40.0, true)
		"altin":
			p.add("yildiz", at + side, -_dir * 10.0, Vector2(2.2, 2.2), 0.2, Color(1.0, 0.88, 0.5, 0.9), 0.0, true)


func _draw() -> void:
	var m := _pts.size()
	if m < 2:
		return
	var pts := PackedVector2Array()
	var uvs := PackedVector2Array()
	var cols := PackedColorArray()
	var idx := PackedInt32Array()
	var along := 0.0
	var prev: Vector2 = _pts[0][0]
	var crackle := 1.4 if unsur == "yildirim" else 0.0
	for i in m:
		var g: Vector2 = _pts[i][0]
		if i > 0:
			along += g.distance_to(prev)
		var d: Vector2 = (prev - g) if i > 0 else (g - (_pts[1][0] as Vector2))
		d = d.normalized() if d.length() > 0.001 else _dir
		var nrm := Vector2(-d.y, d.x)
		var age := clampf((_t - float(_pts[i][1])) / AGE, 0.0, 1.0)
		var u := maxf(age, float(i) / float(m - 1) * 0.35)
		var hw := w * (1.0 - 0.8 * u) * (1.0 + 0.35 * (1.0 - smoothstep(0.0, 0.22, u)) * smoothstep(0.0, 0.05, u))
		var gj := g + nrm * float(_jit[i]) * crackle * (1.0 - u * 0.5) if i > 0 else g
		pts.append(gj + nrm * hw)
		pts.append(gj - nrm * hw)
		uvs.append(Vector2(along / 40.0, 0.0))
		uvs.append(Vector2(along / 40.0, 1.0))
		var c := Color(col.r, col.g, col.b, u)
		cols.append(c)
		cols.append(c)
		if i > 0:
			var s := (i - 1) * 2
			idx.append_array([s, s + 1, s + 2, s + 1, s + 3, s + 2])
		prev = g
	# hava telleri (güçlü atış): izin iki yanında kuyruğa doğru açılan kıl inceliğinde çizgiler
	if w >= 0.42 or unsur != "":
		for sgn: float in [-1.0, 1.0]:
			var st := pts.size()
			var cnt := 0
			for i in range(0, m, 2):
				var g2: Vector2 = _pts[i][0]
				var age2 := clampf((_t - float(_pts[i][1])) / AGE, 0.0, 1.0)
				var u2 := maxf(age2, float(i) / float(m - 1) * 0.35)
				var off := Vector2(-_dir.y, _dir.x) * sgn * (w * 2.2 + u2 * 3.0)
				var hw2 := 0.16 * (1.0 - u2)
				var nr2 := Vector2(-_dir.y, _dir.x)
				pts.append(g2 + off + nr2 * hw2)
				pts.append(g2 + off - nr2 * hw2)
				uvs.append(Vector2(float(i) * 0.37, 0.0))
				uvs.append(Vector2(float(i) * 0.37, 1.0))
				var c2 := Color(col.r, col.g, col.b, clampf(0.25 + u2 * 1.2, 0.0, 1.0))
				cols.append(c2)
				cols.append(c2)
				cnt += 1
			for j in cnt - 1:
				var q := st + j * 2
				idx.append_array([q, q + 1, q + 2, q + 1, q + 3, q + 2])
	# ok ucu parıltısı (yalnızca uçarken)
	if not _stopped and head_back >= 6.0 and host != null and is_instance_valid(host):
		var tipp: Vector2 = host.global_position + _dir * (5.0 + head_back * 0.8)
		var gs := 3.6 * (0.85 + 0.25 * sin(_t * 47.0)) * (1.25 if (w >= 0.42 or unsur != "") else 0.9)
		var gx := _dir * gs * 1.6
		var gy := Vector2(-_dir.y, _dir.x) * gs
		var gk := 0.55 if unsur == "" else 1.1
		var gc := Color(col.r * 1.6, col.g * 1.6, col.b * 1.6, gk) if unsur != "" else Color(1.2, 1.15, 1.05, gk)
		var st2 := pts.size()
		pts.append_array([tipp - gx - gy, tipp + gx - gy, tipp - gx + gy, tipp + gx + gy])
		uvs.append_array([Vector2(0, 2), Vector2(1, 2), Vector2(0, 3), Vector2(1, 3)])
		cols.append_array([gc, gc, gc, gc])
		idx.append_array([st2, st2 + 1, st2 + 2, st2 + 1, st2 + 3, st2 + 2])
	RenderingServer.canvas_item_add_triangle_array(get_canvas_item(), idx, pts, cols, uvs)
