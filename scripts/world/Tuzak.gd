class_name Tuzak
extends Node2D
## v25 tehlike çukuru işaretleri (mürekkep): her çukur bölgesinin (grid 3, yatay şerit) üstünde
##   diken (Ötüken, Bozkır): çukur ağzından 6-9 px dışarı taşan kara demir / kemik diken sırası, uçları pas kızılı;
##                           iki dudakta eğik kazık ve üç kızıl fırça çentiği (uzaktan okunur uyarı)
##   zehir / lav / buz     : yalnızca dudak çentikleri (sıvı havuzu kendi ışığıyla okunur)
## jab(p): değilen yerde dikenler 0,28 sn fırlar (beyaz parlama + toz). Hasar ve sektirme Player._hazard_check'te.

const INK := Color(0.07, 0.05, 0.05)
const IRON := Color(0.22, 0.19, 0.18)
const RUST := Color(0.78, 0.16, 0.1)
const BONE := Color(0.93, 0.88, 0.78)

var level: Node
var kind := "diken"
var regions: Array = []   # {x0, x1 (karo, dahil), y (üst satır)}
var _jabs: Array = []     # {x (px), t}
var _t := 0.0


func _ready() -> void:
	z_index = 3
	InkDraw.prep(self)
	_scan()


func _scan() -> void:
	regions.clear()
	var W: int = level.W
	var H: int = level.H
	for y in H:
		var x := 0
		while x < W:
			if level.cell(x, y) == 3 and level.cell(x, y - 1) != 3:
				var x0 := x
				while x < W and level.cell(x, y) == 3 and level.cell(x, y - 1) != 3:
					x += 1
				regions.append({"x0": x0, "x1": x - 1, "y": y})
			else:
				x += 1


func jab(p: Vector2) -> void:
	_jabs.append({"x": p.x, "t": 0.0})
	if kind == "diken":
		FX.dust(Vector2(p.x, floorf(p.y / level.TS) * level.TS), Vector2.UP, 5, 0.25)
		Ses.play("darbe_kunt", -10.0, 1.4)


func _process(delta: float) -> void:
	_t += delta
	if not _jabs.is_empty():
		for j in _jabs:
			j["t"] = float(j["t"]) + delta
		_jabs = _jabs.filter(func(j: Dictionary) -> bool: return float(j["t"]) < 0.35)
		queue_redraw()
	elif Engine.get_process_frames() % 6 == 0:
		queue_redraw()


func _jab_k(x: float) -> float:
	var k := 0.0
	for j in _jabs:
		var d := absf(float(j["x"]) - x)
		if d < 40.0:
			var tt := float(j["t"])
			var a := clampf(tt / 0.05, 0.0, 1.0) * clampf((0.35 - tt) / 0.2, 0.0, 1.0)
			k = maxf(k, a * (1.0 - d / 40.0))
	return k


func _draw() -> void:
	var TS: float = level.TS
	for r in regions:
		var x0 := float(int(r["x0"])) * TS
		var x1 := float(int(r["x1"]) + 1) * TS
		var top := float(int(r["y"])) * TS
		if kind == "diken":
			_spikes(x0, x1, top, TS)
		_lip(x0, top, -1.0)
		_lip(x1, top, 1.0)


func _spikes(x0: float, x1: float, top: float, TS: float) -> void:
	## Çukurun içinden ağzının 6-9 px üstüne uzanan diken sırası (arkada koyu sıra, önde açık sıra)
	var n := int((x1 - x0) / 7.0)
	for row in 2:
		for i in n:
			var cx := x0 + 3.5 + i * 7.0 + (3.5 if row == 0 else 0.0)
			if cx > x1 - 2.0:
				continue
			var h := 7.0 + 2.5 * sin(cx * 0.37) + (0.0 if row == 1 else -2.0)
			var jk := _jab_k(cx)
			h += jk * 12.0
			var w := 3.2 if row == 1 else 2.6
			var base_y := top + TS * 0.85
			var tip := Vector2(cx + sin(cx * 1.7) * 1.2, top - h)
			var poly := PackedVector2Array([Vector2(cx - w, base_y), tip, Vector2(cx + w, base_y)])
			var body := IRON if row == 1 else INK
			draw_colored_polygon(poly, body.lerp(Color.WHITE, jk * 0.5))
			# uç: pas kızılı (önde kemik beyazı parıltı), nabız
			var tk := 0.42
			var mid_l := Vector2(cx - w, base_y).lerp(tip, 1.0 - tk)
			var mid_r := Vector2(cx + w, base_y).lerp(tip, 1.0 - tk)
			var pulse := 0.75 + 0.25 * sin(_t * 3.0 + cx * 0.05)
			var tipc := RUST.lerp(BONE, jk) if row == 1 else RUST.darkened(0.35)
			draw_colored_polygon(PackedVector2Array([mid_l, tip, mid_r]), Color(tipc, pulse if row == 1 else 0.8))
			draw_polyline(PackedVector2Array([Vector2(cx - w, base_y), tip, Vector2(cx + w, base_y)]), INK, 1.0, true)


func _lip(x: float, top: float, side: float) -> void:
	## Dudak uyarısı: eğik kazık (dikende) ve zeminde üç kızıl fırça çentiği
	var a := 0.55 + 0.2 * sin(_t * 2.2 + x * 0.01)
	if kind == "diken":
		var b := Vector2(x + side * 3.0, top + 2.0)
		var t := b + Vector2(side * 5.0, -15.0)
		draw_line(b, t, INK, 3.4, true)
		draw_line(b + Vector2(0.6, 0), t + Vector2(0.6, 0), IRON.lightened(0.15), 1.4, true)
		draw_colored_polygon(PackedVector2Array([t + Vector2(-2.2, 2.0), t + Vector2(side * 2.0, -4.0), t + Vector2(2.2, 2.0)]), RUST)
	for i in 3:
		var cx := x + side * (8.0 + i * 5.0)
		var p0 := Vector2(cx - 1.5, top - 1.0)
		var p1 := Vector2(cx + 1.5, top - 6.0 - (i % 2) * 2.0)
		InkDraw.stroke(self, p0, p1, 2.2, Color(RUST, a))
