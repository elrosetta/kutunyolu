class_name KirikDuvar
extends Node2D
## v34 gizli cep (Dead Cells'in kırılan duvarları): oda kenarındaki 1 sütun x 4 karoluk ÇATLAK MÜREKKEP DUVARI.
## Kaya karoları gibi katıdır; üstünde fırça çatlakları, aralarından sızan soluk Kut ışığı (oyuncu yaklaşınca belirginleşir:
## "burada bir şey var"). Silah vuruşu (Player -> Level.break_cracks) ya da patlama VURUS_SAYI kez değince kırılır:
## karolar havaya döner, ardındaki 4 x 4 cep oyulur (LevelGen cebi üretimde oymaz: erişim denetimi değişmez), içerik
## (altın yığını / Kut / şifa / eşya zulası / anahtar) cebin tabanına bırakılır, haritada açılır.

const VURUS_SAYI := 2
const KUT := Color(0.36, 0.86, 0.9)
const ALTIN := {"altin": 7, "zula": 3, "kut": 3, "sifa": 3, "anahtar": 2}

var level: Node
var cells: Array = []          # çatlak duvar karoları (x sabit, 4 satır)
var cep := Rect2i()            # cep iç alanı (karo)
var oda := -1
var yon := 1                   # cep odanın hangi yanında (+1 sağ)
var icerik := "altin"
var altin := 0                 # beklenen altın tanesi (ölçüm: harita_testi)
var can := VURUS_SAYI
var kirildi := false
var _t := 0.0
var _vur_t := 0.0
var _yakin := 0.0
var _light: PointLight2D
var _seed := 0


func odalar() -> Array:
	return [oda]


func kur() -> void:
	altin = int(ALTIN.get(icerik, 0))


func _ready() -> void:
	z_index = 3
	InkDraw.prep(self)
	_seed = int(position.x) % 13
	if level:
		_light = level.add_light(Vector2(level.TS * 0.5 + yon * 14.0, -level.TS * 2.0), KUT, 70.0, 0.0, self)


func rect() -> Rect2:
	var TS := float(level.TS)
	var y0 := 99999
	var y1 := -1
	for c in cells:
		y0 = mini(y0, c.y)
		y1 = maxi(y1, c.y)
	var x := float((cells[0] as Vector2i).x)
	return Rect2(x * TS, y0 * TS, TS, (y1 - y0 + 1) * TS)


func vur(box: Rect2) -> bool:
	## Vuruş kutusu duvara (3 px payla) değiyorsa bir çatlak daha; VURUS_SAYI'da kırılır. true: değdi
	if kirildi or _vur_t > 0.0 or not box.grow(3.0).intersects(rect()):
		return false
	_vur_t = 0.18
	can -= 1
	var r := rect()
	FX.dust(Vector2(r.get_center().x - yon * 10.0, r.end.y - 30.0), Vector2(-yon, -0.4), 7, 0.35)
	FX.sparks(Vector2(r.get_center().x - yon * 10.0, r.get_center().y), Vector2(-yon, -0.3), Color(0.75, 0.7, 0.62), 5, 140.0)
	Ses.play("darbe_tas", -2.0, 0.85)
	Game.shake(1.5)
	if can <= 0:
		_kir()
	queue_redraw()
	return true


func _kir() -> void:
	kirildi = true
	var TS := float(level.TS)
	for c in cells:
		level.set_air(c.x, c.y)
	for y in range(cep.position.y, cep.end.y):
		for x in range(cep.position.x, cep.end.x):
			level.set_air(x, y)
	var r := rect()
	FX.dust(r.get_center(), Vector2(yon, -0.2), 18, 0.5)
	FX.smoke(r.get_center(), 6, 0.6)
	FX.flash_light(r.get_center() + Vector2(yon * 30.0, 0), KUT, 180.0, 1.4, 0.4)
	Ses.play("sarsinti", -3.0, 1.15)
	Ses.play("ruh_tasi", -10.0, 1.3)
	Game.shake(4.0)
	FX.text(r.get_center() + Vector2(yon * 30.0, -40.0), "Gizli cep!", Color(1.0, 0.85, 0.45), 9)
	if level.harita:
		level.harita.reveal(Vector2i(cep.position.x + 1, cep.end.y - 1))
	var fy := cep.end.y   # cep tabanı (katı satır)
	var cx := (cep.position.x + 2) * TS
	var py := fy * TS
	var tier := int(Game.run.get("tier", 0))
	match icerik:
		"altin":
			for i in altin:
				level.drop_orb("gold", Vector2(cx + randf_range(-30, 30), py - 14))
		"zula":
			# v25'in gizli yeraltı odası ganimeti (eşya + altın) artık duvar ardında
			level.drop_item(ItemGen.random_drop(tier + 1), Vector2(cx, py - 30), true)
			for i in altin:
				level.drop_orb("gold", Vector2(cx + randf_range(-24, 24), py - 14))
		"kut":
			for i in 6:
				level.drop_orb("kut", Vector2(cx + randf_range(-24, 24), py - 14))
			for i in altin:
				level.drop_orb("gold", Vector2(cx + randf_range(-24, 24), py - 14))
		"sifa":
			level.drop_orb("sifa", Vector2(cx, py - 16))
			for i in altin:
				level.drop_orb("gold", Vector2(cx + randf_range(-24, 24), py - 14))
		"anahtar":
			level.anahtar_birak(Vector2(cx, py - 4))
			for i in altin:
				level.drop_orb("gold", Vector2(cx + randf_range(-24, 24), py - 14))
	if _light:
		_light.energy = 0.0
	queue_redraw()


func _physics_process(delta: float) -> void:
	_t += delta
	_vur_t = maxf(0.0, _vur_t - delta)
	if kirildi or level == null or level.player == null:
		return
	var d: float = level.player.global_position.distance_to(global_position + Vector2(level.TS * 0.5, -level.TS * 2.0))
	_yakin = clampf(1.0 - (d - 60.0) / 160.0, 0.0, 1.0)
	if _light:
		_light.energy = 0.12 + 0.45 * _yakin * (0.75 + 0.25 * sin(_t * 3.0))
	if Engine.get_process_frames() % 3 == 0:
		queue_redraw()


func _draw() -> void:
	if kirildi or level == null:
		return
	var TS := float(level.TS)
	var n := cells.size()
	var h := n * TS
	# duvar yüzü (odaya bakan yan): kayadan biraz açık, pürüzlü kenarlı taş örgü yaması (diğer kaya yüzlerinden
	# ayrışsın: "burası başka"), üstünde koyu çatlaklar ve açık kırık kenarları; kırıldıkça çatlak çoğalır
	var face := 0.0 if yon > 0 else TS
	var ink := Color(0.03, 0.02, 0.04, 0.95)
	var tas := Color(0.36, 0.33, 0.34, 0.92)
	var acik := Color(0.78, 0.74, 0.66, 0.9)
	var hasar := VURUS_SAYI - can
	var w := TS * 0.8
	var yama := PackedVector2Array()
	for k in 7:
		var yy := -h + 3.0 + (h - 6.0) * k / 6.0
		yama.append(Vector2(face + yon * (w + 3.0 * sin(k * 2.3 + _seed)), yy))
	yama.append(Vector2(face, -3.0))
	yama.append(Vector2(face, -h + 3.0))
	draw_colored_polygon(yama, tas)
	# taş örgü derzleri (3 sıra)
	for r in 3:
		var yy := -h + (r + 1) * h / 4.0
		InkDraw.stroke(self, Vector2(face, yy), Vector2(face + yon * w, yy + 2.0 * sin(r + _seed)), 1.4, Color(ink, 0.6))
	# ana çatlak (zikzak) ve dallar
	var pts := PackedVector2Array()
	var y := -h + 4.0
	var x := face + yon * 5.0
	pts.append(Vector2(x, y))
	var i := 0
	while y < -6.0:
		y += 9.0 + 3.0 * sin(i * 1.9 + _seed)
		x = face + yon * (4.0 + 11.0 * absf(sin(i * 1.3 + _seed * 0.7)))
		pts.append(Vector2(x, minf(y, -4.0)))
		i += 1
	InkDraw.line(self, pts, 3.2, 1.6, ink)
	for k in pts.size():
		var p: Vector2 = pts[k]
		draw_line(p + Vector2(yon * 1.6, -1.0), p + Vector2(yon * 4.0, 2.0), acik, 1.0, true)   # kırık kenarı ışık alır
	for k in pts.size() - 1:
		if k % 2 == 0:
			var a: Vector2 = pts[k]
			InkDraw.stroke(self, a, a + Vector2(yon * (9.0 + 4.0 * hasar), -5.0 + 3.0 * sin(k + _seed)), 1.8, ink)
	if hasar > 0:
		# ikinci darbe öncesi: derin yarık ve dökülen taş kırıntıları
		InkDraw.stroke(self, Vector2(face + yon * 3.0, -h * 0.75), Vector2(face + yon * 20.0, -h * 0.3), 3.0, ink)
		InkDraw.blot(self, Vector2(face - yon * 6.0, -3.0), 3.0, tas, _seed)
		InkDraw.blot(self, Vector2(face - yon * 12.0, -2.0), 2.0, tas, _seed + 1)
	# çatlaklardan sızan soluk Kut ışığı (yaklaşınca belirgin)
	var a2 := 0.18 + 0.4 * _yakin * (0.7 + 0.3 * sin(_t * 3.0 + _seed))
	for k in range(1, pts.size() - 1, 2):
		InkDraw.soft(self, (pts[k] as Vector2) + Vector2(yon * 2.0, 0), 3.5 + 2.0 * _yakin, Color(KUT, a2), k)
