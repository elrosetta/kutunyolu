class_name ExplosionFX
extends Node2D
## Piksel sanatı patlama (Medeiros / Penusbmic okulu): aşamalı, elle tasarlanmış, keskin.
##   0-35 ms      sert beyaz flaş diski (0,5R) + 4-6 ince beyaz ışın; ekran bir kare beyazlar
##   40-180 ms    ateş topu: 5-9 üst üste binen daire ("salkım") ease-out ile büyür; renk bantları
##                beyaz çekirdek → sarı → turuncu → koyu kızıl kenar (1-2 px daha koyu çevre çizgisi).
##                Çekirdek dış kabuktan hızlı küçülür; salkım yaşlandıkça ayrı yükselen tutamlara bölünür
##   120-750 ms   duman tutamları (3 ton sıcak koyu gri) yavaşça büyür, yükselir; piksel "erime" ile
##                parçalara bölünerek yok olur (alfa solması yok)
##   parçalar     6-14 piksel kütlesi (1-3 px kare, koyu + kor turuncusu) koni içinde fırlar, yerçekimi,
##                1 sekme; korlar 0,6-1,2 s titreyip söner
##   yer dalgası  yere yatık elips halka (en/boy 0,3) + iki yana kayan toz hattı
## Tüm koordinatlar ve yarıçaplar 1 px dünya ızgarasına oturur; gradyan ve kenar yumuşatma yok.
## big (R >= 50): 80 ms sonra ikinci iç patlama + ekran uzayı kırılma halkası (ShockwaveFX).
## juice: kamera (shake_dir / kick / hitstop / slowmo), kol titreşimi, ses, nokta ışığı.
## Stil v2 (ink): aynı evreler ve zamanlama, piksel diskleri yerine mürekkep: ateş topu tutamları dolu fırça
## lekeleri (bantlar aynı lekenin iç içe küçülen kopyaları), duman yıkama bulutu (erime yerine dağılıp solar),
## yer dalgası fırça halkası, parçalar kül pulu, korlar parlayan damla, flaş yumuşak hale + fırça ışınları.

var radius := 40.0
var col_hot := Color(1.0, 0.85, 0.3)   # sarı bandın rengi (zehir / buz patlamaları için değiştirilebilir)
var big := false
var juice := true
var away := Vector2.UP                  # patlamadan oyuncuya doğru yön (kamera sarsıntısı ekseni)
var ground_y := 6.0                     # yerel zemin çizgisi (parçaların sektiği yükseklik)
var life := 1.35

# zamanlama (saniye)
const T_FLASH := 0.035
const T_FIRE0 := 0.04
const T_FIRE1 := 0.18
const T_FIRE_END := 0.34
const T_SMOKE0 := 0.12
const T_SMOKE1 := 0.78
const T_RING0 := 0.02
const T_RING1 := 0.26
const T_BURST2 := 0.08

# paletler: düz tonlar, bant başına bir renk
const C_WHITE := Color(1.0, 0.98, 0.92)
const C_ORANGE := Color(1.0, 0.45, 0.1)
const C_RED := Color(0.62, 0.12, 0.07)
const C_RED_DARK := Color(0.3, 0.05, 0.06)
const C_SMOKE_D := Color(0.2, 0.16, 0.18)
const C_SMOKE_M := Color(0.33, 0.28, 0.3)
const C_SMOKE_L := Color(0.47, 0.41, 0.43)
const C_SMOKE_WARM := Color(0.72, 0.4, 0.26)
const C_SMOKE_WARM2 := Color(0.5, 0.33, 0.3)
const C_SAND := Color(0.92, 0.82, 0.62)
const C_DUST := Color(0.6, 0.52, 0.47)
const C_CHUNK := Color(0.16, 0.1, 0.11)
const C_EMBER := Color(1.0, 0.6, 0.15)
const C_EMBER_HOT := Color(1.0, 0.9, 0.5)
const C_EMBER_DIM := Color(0.6, 0.15, 0.06)

var _t := 0.0
var _frame := 0
var _puffs: Array = []      # ateş topu salkımı
var _puffs2: Array = []     # big: gecikmeli iç patlama
var _smoke: Array = []
var _debris: Array = []
var _rays: Array = []
var _glow: Node2D
var _seed := 0   # v2: mürekkep lekesinin dönüş tohumu (aynı tutamın bantları aynı biçimde)
var _band := 1   # v2: ateş bandı (0 kenar, 1 dış, 2 sıcak, 3 çekirdek): dış bantlar yıkama, çekirdek hale
var _frag := false


class Glow extends Node2D:
	## Toplamalı katman: flaş diski, ışınlar, sıcak hale (düz, tek tonlu diskler)
	var fx: ExplosionFX
	func _draw() -> void:
		if fx:
			fx._draw_glow(self)


func _ready() -> void:
	z_index = 60
	var m := CanvasItemMaterial.new()
	m.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	material = m
	_glow = Glow.new()
	_glow.fx = self
	_glow.z_index = 2
	var gm := CanvasItemMaterial.new()
	gm.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	gm.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	_glow.material = gm
	add_child(_glow)
	InkDraw.prep(self)
	_build()
	if juice:
		_juice()


func _build() -> void:
	var r := radius
	# ışınlar: 4-6, eşit aralıklı + küçük sapma
	var nr := 4 + randi() % 3
	var base := randf() * TAU
	for i in nr:
		_rays.append(base + TAU * float(i) / nr + randf_range(-0.25, 0.25))
	# ateş topu salkımı: merkezde bir büyük, çevrede 4-8 küçük
	var np := clampi(5 + int(r / 12.0), 5, 9)
	_puffs.append({"ang": 0.0, "d": 0.0, "s": 0.72, "rise": randf_range(0.5, 0.9), "ph": randf()})
	for i in np - 1:
		var a := TAU * float(i) / float(np - 1) + randf_range(-0.3, 0.3)
		_puffs.append({"ang": a, "d": randf_range(0.28, 0.5), "s": randf_range(0.42, 0.6), "rise": randf_range(0.6, 1.3), "ph": randf()})
	if big:
		_puffs2.append({"ang": 0.0, "d": 0.0, "s": 0.5, "rise": 0.8, "ph": randf()})
		for i in 4:
			var a := TAU * float(i) / 4.0 + randf_range(-0.4, 0.4)
			_puffs2.append({"ang": a, "d": randf_range(0.2, 0.35), "s": randf_range(0.3, 0.42), "rise": randf_range(0.8, 1.4), "ph": randf()})
	# duman tutamları: üst yarım düzlemde, ateş topunun kenarından doğar
	var ns := clampi(4 + int(r / 14.0), 4, 8)
	for i in ns:
		var a := -PI * 0.5 + (float(i) / float(ns - 1) - 0.5) * PI * 1.5 + randf_range(-0.2, 0.2)
		_smoke.append({"ang": a, "d": randf_range(0.45, 0.85), "s": randf_range(0.3, 0.5), "rise": randf_range(0.6, 1.2), "drift": randf_range(-0.25, 0.25), "ph": randf(), "frag": []})
		for j in 3:
			_smoke[i]["frag"].append(Vector2.from_angle(randf() * TAU) * randf_range(0.3, 0.7))
	# parçalar: koni yukarı/dışa
	var nd := clampi(6 + int(r / 7.0), 6, 14)
	for i in nd:
		var ember := randf() < 0.45
		var a := -PI * 0.5 + randf_range(-1.15, 1.15)
		var sp := randf_range(70.0, 150.0 + r * 1.6)
		_debris.append({
			"p": Vector2.from_angle(randf() * TAU) * randf() * r * 0.3,
			"v": Vector2.from_angle(a) * sp,
			"size": 1 + (randi() % 3 if not ember else (1 if randf() < 0.6 else 0)),
			"ember": ember,
			"life": randf_range(0.6, 1.2) if ember else randf_range(0.4, 0.75),
			"bounced": false, "rest": false, "ph": randi() % 3,
		})


func _juice() -> void:
	var lvl: Node = FX.level
	if lvl and lvl.has_method("flash_white"):
		if big:
			lvl.flash_white(0.25)
	var dir := away if away.length() > 0.01 else Vector2.UP
	Game.shake_dir(clampf(0.45 + radius / 150.0, 0.0, 0.9), dir)
	Game.kick(Vector2.DOWN, 3.0 + radius / 20.0)
	Game.rumble(0.7, 0.4, 0.22)
	Game.hitstop(0.04)
	Game.slowmo(0.6, 0.11)
	if Ses.has_method("boom"):
		Ses.call("boom", global_position, radius / 40.0)
	else:
		Ses.play("patlama", 0.0)
	if lvl and lvl.has_method("add_light"):
		# kısa, yerel ışık: HDR parıltısıyla birleşip tüm sahneyi yıkamasın
		var l: PointLight2D = lvl.add_light(global_position, Color(1.0, 0.6, 0.25), radius * 2.0, 1.1)
		var tw := l.create_tween()
		tw.tween_property(l, "energy", 0.0, 0.25)
		tw.tween_callback(l.queue_free)
	if big:
		FX.shockwave(global_position, radius * 1.7, 1.0)


func _process(delta: float) -> void:
	if Prof.on:
		var t0 := Time.get_ticks_usec()
		_process_ic(delta)
		Prof.ekle(&"fx", t0)
		return
	_process_ic(delta)


func _process_ic(delta: float) -> void:
	# flaş evresi gerçek zamanda akar (vuruş duraklaması flaşı 1-2 karede tutar; ateş topu sonra donar)
	_t += maxf(delta, 1.0 / 60.0) if _t < T_FIRE0 else delta
	_frame += 1
	if _t >= life:
		queue_free()
		return
	_step_debris(delta)
	queue_redraw()
	if _t < T_FIRE_END + 0.05:
		_glow.queue_redraw()


func _step_debris(delta: float) -> void:
	for d in _debris:
		if d["rest"]:
			continue
		var v: Vector2 = d["v"]
		v.y += 650.0 * delta
		v.x = move_toward(v.x, 0.0, 40.0 * delta)
		var p: Vector2 = d["p"] + v * delta
		if p.y >= ground_y and v.y > 0.0:
			p.y = ground_y
			if d["bounced"]:
				d["rest"] = true
				v = Vector2.ZERO
			else:
				d["bounced"] = true
				v.y = -v.y * 0.32
				v.x *= 0.55
		d["p"] = p
		d["v"] = v


# ------------------------------------------------------------------ yardımcılar
static func _eo(k: float) -> float:
	## ease-out (önce hızlı, sonra yavaş)
	k = clampf(k, 0.0, 1.0)
	return 1.0 - pow(1.0 - k, 3.0)


static func _ph(t0: float, t1: float, t: float) -> float:
	return clampf((t - t0) / (t1 - t0), 0.0, 1.0)


func _blob(c: Vector2, pr: float, col: Color) -> void:
	## v1: piksel diski (tam sayı yarıçap); v2: mürekkep lekesi (kesirli yarıçap, titremeden büyür)
	if _band == 3:
		InkDraw.soft(self, c, maxf(pr, 0.8) * 1.25, col, _seed)
	elif _band <= 1 or _frag:
		InkDraw.cloud(self, c, maxf(pr, 0.8) * 1.12, col, _seed)
	else:
		InkDraw.blot(self, c, maxf(pr, 0.8), col, _seed)


func _disc(c: Vector2, r: int, col: Color) -> void:
	## Piksel diski: tarama satırları, tam sayı ızgara, kenar yumuşatma yok
	var cx := floorf(c.x)
	var cy := floorf(c.y)
	if r <= 0:
		draw_rect(Rect2(cx, cy, 1, 1), col)
		return
	var rr := float(r * r + r)
	for y in range(-r, r + 1):
		var hw := int(floor(sqrt(maxf(0.0, rr - float(y * y)))))
		draw_rect(Rect2(cx - hw, cy + y, 2 * hw + 1, 1), col)


func _ring_px(c: Vector2, rx: float, ry: float, col: Color, drop := 0.0, seed_v := 7) -> void:
	## Piksel elips halkası: parametrik adım, tekrarlanan piksel atlanır; drop 0..1 oranında piksel silinir (erime)
	if rx < 1.0:
		return
	InkDraw.ring(self, c, rx, ry, Color(col, col.a * (1.0 - drop)), float(seed_v))


# ------------------------------------------------------------------ çizim
func _draw() -> void:
	var t := _t
	_draw_ground(t)
	_draw_smoke(t)
	_draw_fire(_puffs, t, 1.0)
	if big:
		_draw_fire(_puffs2, t - T_BURST2, 0.62, false)
	_draw_debris(t)


func _draw_glow(g: Node2D) -> void:
	var t := _t
	var r := radius
	# flaş: 2 kare sert beyaz disk + ince ışınlar
	_ink_glow(g, t, r)


func _draw_fire(puffs: Array, t: float, scale_v: float, rim_on := true) -> void:
	if t < T_FIRE0 or t >= T_FIRE_END or puffs.is_empty():
		return
	var r := radius * scale_v
	var k := _ph(T_FIRE0, T_FIRE1, t)              # genişleme
	var age := _ph(T_FIRE1, T_FIRE_END, t)          # dağılma / kararma
	var hot := _ph(0.07, 0.26, t)                   # çekirdek sönümü (kabuktan hızlı)
	var rf := r * (0.3 + 0.7 * _eo(k)) * 0.8
	# bant renkleri zamanla kayar: turuncu → kızıl → koyu kızıl → duman
	var outer := C_ORANGE
	var rim := C_RED
	if age > 0.36:
		outer = C_RED
		rim = C_RED_DARK
	if age > 0.66:
		outer = C_RED_DARK
		rim = C_SMOKE_D
	if age > 0.88:
		outer = C_SMOKE_D
		rim = C_SMOKE_D
	var mid := col_hot
	var core := C_WHITE
	# dört geçiş: her bant tüm tutamlar için birlikte çizilir → bantlar salkımın siluetini izler
	for band in 4:
		var pi := 0
		for p in puffs:
			pi += 1
			var dir := Vector2.from_angle(float(p["ang"]))
			var dd := float(p["d"])
			var c: Vector2 = dir * (dd * rf + age * r * 0.35) + Vector2(0, -age * r * 0.5 * float(p["rise"]))
			var pr: float = float(p["s"]) * rf * (1.0 - 0.55 * age)
			if pr < 0.5:
				continue
			var frag := age > 0.7
			_seed = pi * 3 + 1
			_band = band
			_frag = frag
			match band:
				0:
					# iç patlamanın kenar çizgisi yok: ana topun üstünde hedef halkası gibi görünmesin
					if rim_on or age > 0.4:
						_fire_blob(c, pr + 1.0 + (1.0 if r >= 50 else 0.0), rim, frag, p)
				1:
					_fire_blob(c, pr, outer, frag, p)
				2:
					# sıcak bant silüetin içine, merkeze doğru kayar (ışık içeriden)
					# soğurken dış tutamlar sarıyı önce yitirir (benekler yerine tek göbek küçülür)
					var keep := int(ceil(float(puffs.size()) * (1.0 - hot * 1.15)))
					var mr: float = pr * (0.82 - 0.3 * hot) * (1.0 - 0.3 * dd)
					if mr >= 1.0 and age < 0.5 and pi <= maxi(1, keep):
						_fire_blob(c - dir * pr * 0.22, mr, mid, false, p)
				3:
					# beyaz çekirdek yalnız merkez tutam + ilk iki komşu: tek bir sıcak göbek
					var cr: float = pr * (0.5 - 0.6 * hot)
					if cr >= 1.0 and age < 0.3 and pi <= 3:
						_fire_blob(c - dir * pr * 0.3, cr, core, false, p)


func _fire_blob(c: Vector2, pr: float, col: Color, frag: bool, p: Dictionary) -> void:
	if not frag:
		_blob(c, pr, col)
		return
	# yaşlı tutam: üç küçük parçaya bölünür (erime)
	var ph: float = p["ph"]
	for j in 3:
		var a := ph * TAU + TAU * float(j) / 3.0
		_blob(c + Vector2.from_angle(a) * pr * 0.5, pr * 0.5, col)


func _draw_smoke(t: float) -> void:
	if t < T_SMOKE0 or t >= T_SMOKE1:
		return
	var r := radius
	var k := _ph(T_SMOKE0, T_SMOKE1, t)
	var ds := _ph(0.58, 1.0, k)                      # erime
	var lit := C_SMOKE_L
	if k < 0.22:
		lit = C_SMOKE_WARM
	elif k < 0.4:
		lit = C_SMOKE_WARM2
	_ink_smoke(t, r, k, ds, lit)


func _draw_ground(t: float) -> void:
	if t < T_RING0 or t >= T_RING1:
		return
	var k := _ph(T_RING0, T_RING1, t)
	var r := radius
	var rr := r * (0.25 + 1.15 * _eo(k))
	var c := Vector2(0, ground_y - 2.0)
	var col := C_SAND if k < 0.45 else C_DUST
	var drop := _ph(0.4, 1.0, k) * 0.85
	_ring_px(c, rr, rr * 0.3, col, drop)
	if k < 0.8:
		# iç, daha sönük halka: toprak dalgası
		_ring_px(c, rr * 0.62, rr * 0.3 * 0.62, C_DUST, 0.35 + drop * 0.6, 13)
	# toz hattı: iki yana kayan 2 px kalın çizgiler
	if k > 0.08 and k < 0.9:
		var x0 := floorf(rr * 0.62)
		var x1 := floorf(rr)
		var y := floorf(c.y - 1.0)
		var dcol := C_DUST if k < 0.6 else Color(C_DUST, 0.6)
		InkDraw.stroke(self, Vector2(x0, y + 1.0), Vector2(x1, y + 1.0), 3.0, dcol)
		InkDraw.stroke(self, Vector2(-x0, y + 1.0), Vector2(-x1, y + 1.0), 3.0, dcol)
		return


func _draw_debris(t: float) -> void:
	for d in _debris:
		var age: float = t / float(d["life"])
		if age >= 1.0:
			continue
		var p: Vector2 = d["p"]
		var sz: int = d["size"]
		var col := C_CHUNK
		if d["ember"]:
			# kor: titrer (3 kare döngü), sonlara doğru söner
			var ph: int = (_frame + int(d["ph"])) % 3
			if age > 0.75 and ph != 0:
				continue
			col = C_EMBER_HOT if (ph == 0 and age < 0.5) else C_EMBER
			if age > 0.6:
				col = C_EMBER_DIM
		elif age > 0.8:
			continue
		if d["ember"]:
			InkDraw.soft(self, p, 1.6 + sz, Color(col, 0.45))
			InkDraw.drop(self, p, 1.0 + sz * 0.7, (d["v"] as Vector2).angle(), col)
		else:
			InkDraw.flake(self, p, 1.6 + sz * 1.3, float(d["ph"]) * 2.1 + age * 6.0, col)


# ------------------------------------------------------------------ v2 mürekkep
func _ink_glow(g: Node2D, t: float, r: float) -> void:
	if t < T_FLASH:
		var fr := r * 0.5
		InkDraw.soft(g, Vector2.ZERO, fr * 1.5, Color(1.0, 1.0, 1.0, 0.9))
		InkDraw.blot(g, Vector2.ZERO, fr * 0.8, Color(1.0, 1.0, 1.0), 7)
		for a in _rays:
			var d := Vector2.from_angle(a)
			InkDraw.stroke(g, d * fr * 0.7, d * (r * 1.35 + 4.0), 3.2, Color(1.0, 1.0, 1.0))
	var hk := _ph(T_FIRE0, 0.2, t)
	if t >= T_FIRE0 and hk < 1.0:
		InkDraw.soft(g, Vector2.ZERO, r * (0.9 - 0.5 * hk) * 1.2, Color(0.6, 0.25, 0.08, 0.45 * (1.0 - hk)))
	if big and t >= T_BURST2 and t < T_BURST2 + T_FLASH:
		InkDraw.soft(g, Vector2(0, -r * 0.15), r * 0.45, Color(1.0, 1.0, 1.0))


func _ink_smoke(t: float, r: float, k: float, ds: float, lit: Color) -> void:
	## Duman: koyu yıkama bulutu + ateşe bakan açık yüz; erime evresinde büyüyüp solar (piksel kırılması yok)
	var i := 0
	for p in _smoke:
		i += 1
		var dir := Vector2.from_angle(float(p["ang"]))
		var c: Vector2 = dir * (float(p["d"]) * r * (0.55 + 0.45 * k)) + Vector2(float(p["drift"]) * r * k, -float(p["rise"]) * r * 0.85 * _eo(k))
		var pr: float = float(p["s"]) * r * (0.35 + 0.65 * _eo(k)) * (1.0 + 0.35 * ds)
		if pr < 1.0:
			continue
		var a := 1.0 - ds
		InkDraw.cloud(self, c, pr, Color(C_SMOKE_D, 0.92 * a), i)
		var lo: Vector2 = (-dir * pr * 0.25) if k < 0.4 else Vector2(-pr * 0.2, -pr * 0.28)
		InkDraw.cloud(self, c + lo, pr * 0.62, Color(C_SMOKE_M, 0.85 * a), i + 1)
		InkDraw.cloud(self, c + lo * 1.5, pr * 0.32, Color(lit, 0.8 * a), i + 2)
