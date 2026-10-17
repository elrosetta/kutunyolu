class_name BenguSac
extends Node2D
## Bengü'nün uzun saçı (stil v2): kurt başlığının arka kenarının altından çıkan gür bir at kuyruğu + iki ince örgü.
## Sprite'a çizilmez: her kare çalışma zamanında verlet zinciriyle benzetilir ve mürekkep-cel fırça şeridi olarak çizilir
## (shaders/bengu_sac.gdshader). Böylece koşuda arkaya akar, sıçrayışta aşağı, düşüşte yukarı savrulur, yuvarlanmada topla
## döner, saldırı ve geri tepmede gecikmeli sallanır, yön değişince kesmeden öbür yana geçer.
##
## Çapalar (tools/artgen/bengu_ink.py -> bengu_v2.json, her kare): 'sac' (ense, saçın başlıktan çıktığı nokta), 'sac_d'
## (kökün ilk doğrultusu, ekran açısı; yuvarlanmada topla döner), 'neck' / 'hip' (sırt çizgisi: saç gövdenin önüne geçmez).
## Çapalar SpriteAnim yerelinde (dünya birimi, yöne göre aynalı); benzetim küresel uzayda (ataletin gerçek olması için).
##
## Katmanlar: bu düğüm SpriteAnim'in ilk çocuğu (gövdenin arkası: at kuyruğu + uzak örgü); `on` düğümü gövde sprite'ından
## hemen sonra (yakın örgü omzun önünden sarkar, kol iskeletinin altında). İkisi de SpriteAnim'in çocuğu: gövdenin
## ezilme/esneme ve eğilmesini, görünürlüğünü (kurt dönüşümü, Don) birebir izler. Görünmezken benzetim durur; yeniden
## görünür olunca saç dinlenme duruşundan başlar (dönüşümden sonra eski yerinden "uçarak" gelmesin).

const SHADER := preload("res://shaders/bengu_sac.gdshader")
const DT := 1.0 / 120.0             # sabit alt adım (kare hızından bağımsız aynı davranış)
const G := 430.0                    # saça etki eden yerçekimi (oyuncu GRAV 1180; saç havada daha süzülür)
const SAC_A0 := 2.0915              # 'sac_d' taban açısı atan2(0.87, -0.5): baş dönüşü = sac_d - SAC_A0
const LIGHT := Vector2(-0.7408, -0.6717)  # dünya ışığı (sol üst; inkkit.LIGHT)
const MAX_STEPS := 8
const V_OLCEK := 64.0              # UV.y = uzunluk / V_OLCEK (0..1 aralığında kalsın; gölgelendirici geri çarpar)
const ITERS := 8                    # kısıt turu (alt adım başına)

# kipler (gölgelendiricideki COLOR.b)
const M_SAC := 0.0
const M_POST := 0.25
const M_ORGU := 0.5
const M_HALKA := 0.68
const M_BONCUK := 1.0


class Zincir:
	## Verlet zinciri: p şimdiki, o önceki konum (küresel). Kök (0) ve ikinci nokta başlığa bağlı.
	var ad := ""
	var p := PackedVector2Array()
	var o := PackedVector2Array()
	var n := 10
	var seg := 2.0
	var off := Vector2.ZERO          # kök ofseti: baş çerçevesinde, yüz sağa bakarken (dünya birimi)
	var ust := false                 # true: gövdenin önünde çizilir (on düğümü)
	var kip := 0.0
	var gen := 3.0                   # en geniş (dünya birimi)
	var kok_k := 0.6                 # ikinci noktanın kök doğrultusuna bağlılığı
	var surt := 4.2                  # hava sürtünmesi (1/sn): koşuda arkaya akış bununla
	var govde := true                # sırt çarpışması
	var bukul := 0.85                # bükülme: uçta i..i+2 en kısa uzaklık oranı (1 = dümdüz)
	var drot := 0.0                  # kök doğrultusuna ek dönüş (yüz sağa bakarken; radyan)
	var gr := 1.0                    # sırt kapsülü yarıçap çarpanı (önde çizilen saç silüetin biraz içinde yatar)
	var r0 := Vector2.ZERO           # kök: son alt adımdaki / bu karedeki (küresel)
	var r1 := Vector2.ZERO
	var d0 := Vector2.DOWN
	var d1 := Vector2.DOWN
	var faz := 0.0
	var yl := Vector2.ZERO           # yumuşatılmış kök (SpriteAnim yereli) ve doğrultu, son yön
	var yd := Vector2.DOWN
	var yf := 1


class On:
	## Gövdenin önündeki saç katmanı: çizimi sahibi yapar.
	extends Node2D
	var sac: BenguSac

	func _draw() -> void:
		if sac:
			sac.draw_layer(self, true)


var anim: SpriteAnim
var pl: CharacterBody2D
var on: On
var mat: ShaderMaterial
var zincirler: Array = []
var _acc := 0.0
var _reset := true
var _t := 0.0
var _neck := Vector2.ZERO
var _hip := Vector2.ZERO
var _face := 1


static func ekle(sprite: SpriteAnim, owner_body: CharacterBody2D) -> BenguSac:
	## Oyuncunun gövde SpriteAnim'ine saçı takar (yalnızca stil v2 mürekkep sayfası ve 'sac' çapası varsa).
	if sprite == null or not Data.is_linear(sprite.meta):
		return null
	var any := false
	for an in sprite.meta["anims"].values():
		var d: Array = an.get("data", [])
		if d.size() > 0 and (d[0] as Dictionary).has("sac"):
			any = true
			break
	if not any:
		return null
	var s := BenguSac.new()
	s.anim = sprite
	s.pl = owner_body
	sprite.add_child(s)
	sprite.move_child(s, 0)  # gövde sprite'ından önce: arkada
	s.on = On.new()
	s.on.sac = s
	sprite.add_child(s.on)
	sprite.move_child(s.on, sprite.base.get_index() + 1)  # gövdenin hemen önünde, kol iskeletinin altında
	s._kur()
	return s


func _kur() -> void:
	# ağaç duraklıyken de çalışır (başlık ekranı / duraklatma): yalnızca ilk duruşu kurar ve çizer, benzetim durur
	process_mode = Node.PROCESS_MODE_ALWAYS
	mat = ShaderMaterial.new()
	mat.shader = SHADER
	material = mat
	on.material = mat
	# uzak örgü (en arkada, kısa), gür at kuyruğu, yakın örgü (omzun önünden)
	zincirler = [
		_z("uzak_orgu", 9, 2.0, Vector2(0.6, 0.6), false, M_ORGU, 2.0, 0.8, 7.0),
		_z("kuyruk", 12, 2.2, Vector2(1.4, 2.6), true, M_SAC, 6.6, 0.86, 6.6),
		_z("yakin_orgu", 8, 1.9, Vector2(2.2, 2.6), true, M_ORGU, 1.9, 0.82, 7.2),
	]
	(zincirler[2] as Zincir).govde = false
	(zincirler[2] as Zincir).drot = -0.55  # yakın örgü kulağın arkasından, başlığın yan postunun altından aşağı çıkar (omuz üstüne düşer)
	(zincirler[1] as Zincir).gr = 0.8  # at kuyruğu sırtın üstünde yatar (gövdenin önünde çizilir: post pelerinin üstüne düşer)
	(zincirler[1] as Zincir).faz = 0.0
	(zincirler[0] as Zincir).faz = 1.7
	(zincirler[2] as Zincir).faz = 3.1


func _z(ad: String, n: int, seg: float, off: Vector2, ust: bool, kip: float, gen: float, bukul: float, surt: float) -> Zincir:
	var z := Zincir.new()
	z.ad = ad
	z.n = n
	z.seg = seg
	z.off = off
	z.ust = ust
	z.kip = kip
	z.gen = gen
	z.bukul = bukul
	z.surt = surt
	z.p.resize(n)
	z.o.resize(n)
	return z


func sarsil(v: Vector2) -> void:
	## Dışarıdan ani itki (ör. ağır darbe): uçlara doğru artan hız.
	for z in zincirler:
		for i in range(2, z.n):
			z.o[i] -= v * DT * (float(i) / z.n)


# ------------------------------------------------------------------ çapalar
func _kok(z: Zincir, delta: float) -> void:
	## Bu karenin kökü (r1) ve kök doğrultusu (d1), küresel. Çapa sprite karesiyle (8-18 fps) basamaklı değişir: yerel
	## uzayda kısa bir yumuşatmadan geçer, yoksa koşunun her karesindeki baş sıçraması saçı kamçılar.
	var f := anim.facing
	var sac: Variant = anim.anchor("sac")
	var ang := 0.0
	if sac == null:
		var hd: Variant = anim.anchor("head")
		sac = (hd as Vector2) + Vector2(-3.3 * f, 2.2) if hd != null else Vector2(-3.0 * f, -44.0)
		ang = PI - SAC_A0 if f < 0 else SAC_A0
	else:
		ang = anim.anchor_angle("sac_d")
	var raw := ang if f > 0 else PI - ang
	var rot := raw - SAC_A0
	var off_l := Vector2(z.off.x * f, z.off.y).rotated(rot * f)
	var hedef: Vector2 = (sac as Vector2) + off_l
	var dir := Vector2(cos(ang), sin(ang)).rotated(z.drot * f)
	if z.yf != f:  # yön değişti: yumuşatılmış çapa aynalanır (kök başın içinden kaymasın)
		z.yl.x = -z.yl.x
		z.yd.x = -z.yd.x
		z.yf = f
	if _reset or delta <= 0.0:
		z.yl = hedef
		z.yd = dir
	else:
		var k := 1.0 - exp(-delta * 26.0)
		z.yl = z.yl.lerp(hedef, k)
		z.yd = z.yd.lerp(dir, k).normalized()
	z.r1 = anim.to_global(z.yl)
	z.d1 = anim.global_transform.basis_xform(z.yd).normalized()


func _sirt() -> void:
	var f := anim.facing
	var nk: Variant = anim.anchor("neck")
	var hp: Variant = anim.anchor("hip")
	_neck = anim.to_global(nk if nk != null else Vector2(4.0 * f, -40.0))
	_hip = anim.to_global(hp if hp != null else Vector2(0.0, -24.0))
	_face = f


func _dinlen(z: Zincir) -> void:
	## Dinlenme duruşu: kökten başlık doğrultusunda çıkar, sonra sırttan aşağı sarkar.
	var down := Vector2(-_face * 0.25, 1.0).normalized()
	var q := z.r1
	for i in z.n:
		if i > 0:
			var k := clampf(float(i - 1) / 2.5, 0.0, 1.0)
			q += z.d1.lerp(down, k).normalized() * z.seg
		z.p[i] = q
	# sırta otursun: birkaç tur kısıt + gövde (hızsız)
	for it in 12:
		_kisit(z, z.r1, z.d1)
		if z.govde:
			_govde(z)
	for i in z.n:
		z.o[i] = z.p[i]
	z.r0 = z.r1
	z.d0 = z.d1


# ------------------------------------------------------------------ benzetim
func _process(delta: float) -> void:
	if anim == null or not is_visible_in_tree():
		_reset = true
		return
	_t += delta
	_sirt()
	for z in zincirler:
		_kok(z, delta)
		if _reset or z.r1.distance_to(z.r0) > 48.0:  # ışınlanma (kapı, güvenli noktaya dönüş, dönüşüm bitişi)
			_dinlen(z)
	_reset = false
	mat.set_shader_parameter("vcol_linear", get_viewport().use_hdr_2d)
	if get_tree().paused or not anim.can_process():
		queue_redraw()
		on.queue_redraw()
		return
	# mat parametreleri gövdeden: vuruş parlaması, zehir tonu, ay gölgesi saçta da aynı
	if anim.mat:
		for k in ["flash", "tint", "moon_shade"]:
			var v: Variant = anim.mat.get_shader_parameter(k)
			if v != null:
				mat.set_shader_parameter(k, v)
	_acc = minf(_acc + delta, DT * MAX_STEPS)
	var steps := int(_acc / DT)
	_acc -= steps * DT
	if steps > 0:
		var on_floor := pl != null and pl.is_on_floor()
		var floor_y := pl.global_position.y - 0.4 if pl else 1e9
		var hiz := pl.velocity.length() if pl else 0.0
		for k in steps:
			var u := float(k + 1) / float(steps)
			for z in zincirler:
				_adim(z, z.r0.lerp(z.r1, u), z.d0.slerp(z.d1, u).normalized(), on_floor, floor_y, hiz)
		for z in zincirler:
			z.r0 = z.r1
			z.d0 = z.d1
	queue_redraw()
	on.queue_redraw()


func _adim(z: Zincir, R: Vector2, D: Vector2, on_floor: bool, floor_y: float, hiz: float) -> void:
	var dt2 := DT * DT
	var damp := 1.0 - z.surt * DT
	z.o[0] = z.p[0]
	z.p[0] = R
	# rüzgâr: hafif sürekli esinti + ara ara sağanak; koşuda uçlarda çırpınma (şeride dik)
	var gust := pow(maxf(0.0, sin(_t * 0.55 + z.faz * 0.3)), 3.0)
	var wind := Vector2(-(18.0 + 60.0 * gust), 0.0)
	var flap := clampf(hiz / 160.0, 0.0, 1.6)
	for i in range(1, z.n):
		var v := (z.p[i] - z.o[i]) * damp
		z.o[i] = z.p[i]
		var fi := float(i) / float(z.n - 1)
		var acc := Vector2(0.0, G) + wind * (0.4 + fi)
		acc.y += sin(_t * 1.7 + i * 0.6 + z.faz) * 14.0
		if flap > 0.05 and i >= 2:
			var tg := (z.p[i] - z.p[i - 1]).normalized()
			acc += Vector2(-tg.y, tg.x) * sin(_t * 15.0 - i * 0.95 + z.faz) * 38.0 * flap * fi
		z.p[i] += v + acc * dt2
	# kısıtlar (Jakobsen gevşetmesi; "lideri izle" kamçılanıp titriyordu): her turda ikinci nokta kök doğrultusuna
	# çekilir, parça boyları iki yönlü düzeltilir (kök sabit), bükülme = i ile i+2 arası en kısa uzaklık (kökte neredeyse
	# düz, uca doğru serbest): saç katlanıp zikzak yapmaz, yumuşak kavis alır
	for it in ITERS:
		_kisit(z, R, D)
		if it == ITERS - 3:
			if z.govde:
				_govde(z)
			_zemin(z, on_floor, floor_y)
	# uzama sınırı: hızlanmada %4'ten fazla uzayan parça kısaltılır; önceki konum da aynı kaydırılır (hız eklenmez,
	# "lideri izle"nin kamçı titremesi olmaz)
	for i in range(1, z.n):
		var d := z.p[i] - z.p[i - 1]
		var l := d.length()
		if l > z.seg * 1.04:
			var np := z.p[i - 1] + d * (z.seg * 1.04 / l)
			z.o[i] += np - z.p[i]
			z.p[i] = np


func _kisit(z: Zincir, R: Vector2, D: Vector2) -> void:
	z.p[1] = z.p[1].lerp(R + D * z.seg, z.kok_k)
	for i in range(1, z.n):
		var d := z.p[i] - z.p[i - 1]
		var l := d.length()
		if l < 1e-5:
			continue
		var corr := d * ((l - z.seg) / l)
		if i == 1:
			z.p[i] -= corr
		else:
			z.p[i - 1] += corr * 0.5
			z.p[i] -= corr * 0.5
	for i in range(2, z.n):
		var d2 := z.p[i] - z.p[i - 2]
		var l2b := d2.length()
		var k := 1.0 - float(i) / float(z.n)
		var minl := z.seg * 2.0 * lerpf(z.bukul, 0.99, k)
		if l2b < minl and l2b > 1e-5:
			z.p[i] += d2 * ((minl - l2b) / l2b) * 0.5


func _govde(z: Zincir) -> void:
	# sırt: gövde bir kapsül (boyun -> kalça, sprite silüetine denk yarıçap). İçine giren nokta dışarı itilir; göğüs
	# yanındaysa (yön değişiminden hemen sonra) sırt yanına doğru itilir: saç gövdenin içinden süzülerek arkaya geçer.
	var ab := _hip - _neck
	var l2 := maxf(ab.length_squared(), 1.0)
	for i in range(3, z.n):
		var q := z.p[i]
		var t := clampf((q - _neck).dot(ab) / l2, 0.0, 1.25)
		var c := _neck + ab * t
		var rel := q - c
		var r := (lerpf(6.6, 5.8, minf(t, 1.0)) + maxf(0.0, t - 1.0) * 6.0) * z.gr
		var dl := rel.length()
		if dl < r:
			var nrm := rel / dl if dl > 1e-3 else Vector2(-_face, 0.0)
			if nrm.x * float(_face) > -0.2:  # göğüs yanı: sırt yanına çevir
				nrm = Vector2(-float(_face) * 0.9, nrm.y * 0.45).normalized()
			z.p[i] = q.lerp(c + nrm * r, 0.5)


func _zemin(z: Zincir, on_floor: bool, floor_y: float) -> void:
	# zemin: yerdeyken saç toprağın içine girmez, sürtünür
	if on_floor:
		for i in range(2, z.n):
			if z.p[i].y > floor_y:
				z.p[i].y = floor_y
				z.o[i].x = lerpf(z.o[i].x, z.p[i].x, 0.35)


# ------------------------------------------------------------------ çizim
func _draw() -> void:
	draw_layer(self, false)


func draw_layer(ci: CanvasItem, front: bool) -> void:
	var inv := ci.get_global_transform().affine_inverse()
	var L := (inv.basis_xform(LIGHT)).normalized()
	for z in zincirler:
		if z.ust != front:
			continue
		var pts := PackedVector2Array()
		pts.resize(z.n)
		for i in z.n:
			pts[i] = inv * z.p[i]
		pts[0] = inv * z.r1
		var sm := _yumusat(pts, 3)
		if z.kip == M_SAC:
			_kuyruk(ci, sm, z, L)
		else:
			_orgu(ci, sm, z, L)


func _kuyruk(ci: CanvasItem, sm: PackedVector2Array, z: Zincir, L: Vector2) -> void:
	## Gür at kuyruğu: aynı eğri üzerinde beş tutam (uca doğru açılır, boyları farklı; aralarındaki kontur tel ayrımı
	## olur) + iki ince uçuşan tel: fırça ucu gibi ayrışan, kâkülsü sivri uçlar. Dış tutamlar önce, orta tutam en üstte.
	var nr := _normaller(sm)
	var W := z.gen
	var last := float(sm.size() - 1)
	for k in [-2, 2, -1, 1, 0]:
		var boy: float = {-2: 0.8, -1: 0.93, 0: 1.0, 1: 0.86, 2: 0.72}[k]
		var wk: float = {-2: 0.42, -1: 0.56, 0: 0.66, 1: 0.56, 2: 0.42}[k]
		var m := maxi(2, int(round(last * boy)) + 1)
		var q := PackedVector2Array()
		q.resize(m)
		for i in m:
			var s := float(i) / last
			var w := _w_kuyruk(s, W)
			q[i] = sm[i] + nr[i] * (w * 0.16 * float(k) * (1.0 + 1.2 * s * s) + sin(s * 8.0 + float(k) * 1.7 + z.faz) * 0.22 * s)
		_serit(ci, q, func(s: float) -> float: return _w_kuyruk(s * boy, W) * wk, M_SAC, L, boy)
	# uçuşan teller: tutamların kenarından ayrılan ince, uzun kıvrımlar
	for k in [-1, 1]:
		var q2 := PackedVector2Array()
		var m2 := sm.size()
		q2.resize(m2)
		for i in m2:
			var s := float(i) / last
			var w := _w_kuyruk(s, W)
			q2[i] = sm[i] + nr[i] * (w * 0.42 * float(k) + sin(s * 11.0 + float(k) * 3.0 + z.faz + _t * 2.0) * 0.5 * s * s)
		_serit(ci, q2, func(s: float) -> float: return 0.55 * sin(minf(1.0, s * 1.6) * PI) * (1.0 - s * 0.3), M_SAC, L, 1.0)
	# saç bağı: başlığın altından çıkan kökte altın halka (şerit başı burada saklanır)
	_serit(ci, sm.slice(0, 3), func(_s: float) -> float: return W * 0.62, M_HALKA, L, 1.0)


func _w_kuyruk(s: float, W: float) -> float:
	## kökte toplu (başlığın altında bağlı), ilk üçte birde en gür, uca doğru sivrilir
	return W * (0.6 + 0.4 * sin(minf(s * 2.4, 1.0) * PI * 0.5)) * pow(maxf(0.0, 1.0 - s), 0.62)


func _orgu(ci: CanvasItem, sm: PackedVector2Array, z: Zincir, L: Vector2) -> void:
	## Örgü: V lobları; ucunda altın halka ve serbest saç püskülü; yakın örgünün kökünde de halka (başlığın altından çıkış),
	## halkada turkuaz boncuk.
	var n := sm.size()
	var cut := int(n * 0.8)
	var W := z.gen
	var body := sm.slice(0, cut + 1)
	_serit(ci, body, func(s: float) -> float: return W * (1.0 - 0.18 * s), M_ORGU, L, 1.0)
	var tuft := sm.slice(cut - 1, n)
	_serit(ci, tuft, func(s: float) -> float: return W * 1.25 * sin(minf(1.0, s * 3.0 + 0.35) * PI * 0.5) * pow(1.0 - s, 0.7), M_SAC, L, 1.0)
	var band := sm.slice(maxi(0, cut - 2), mini(n, cut + 1))
	_serit(ci, band, func(_s: float) -> float: return W * 1.28, M_HALKA, L, 1.0)
	if z.ust:
		_serit(ci, sm.slice(0, 3), func(_s: float) -> float: return W * 1.3, M_HALKA, L, 1.0)
		var bc := sm[mini(n - 1, cut)]
		var nr := _normaller(sm)
		var bpos := bc + nr[mini(n - 1, cut)] * W * 0.2 + Vector2(0, 0.9)
		_boncuk(ci, bpos, 0.85)


func _boncuk(ci: CanvasItem, c: Vector2, r: float) -> void:
	var v := PackedVector2Array([c + Vector2(-r, -r), c + Vector2(r, -r), c + Vector2(r, r), c + Vector2(-r, r)])
	var col := Color(0.5, r / 4.0, M_BONCUK, 1.0)
	var cols := PackedColorArray([col, col, col, col])
	var uv := PackedVector2Array([Vector2(0, 0), Vector2(1, 0), Vector2(1, 1), Vector2(0, 1)])
	RenderingServer.canvas_item_add_triangle_array(ci.get_canvas_item(), PackedInt32Array([0, 1, 2, 0, 2, 3]), v, cols, uv)


func _serit(ci: CanvasItem, q: PackedVector2Array, wf: Callable, kip: float, L: Vector2, s_end: float) -> void:
	## Fırça şeridi: her noktada sol/sağ köşe; UV.x enine, UV.y kökten uzunluk; renkte ışık yanı, yarı genişlik, kip.
	var m := q.size()
	if m < 2:
		return
	var nr := _normaller(q)
	var verts := PackedVector2Array()
	var cols := PackedColorArray()
	var uvs := PackedVector2Array()
	verts.resize(m * 2)
	cols.resize(m * 2)
	uvs.resize(m * 2)
	var acc := 0.0
	for i in m:
		if i > 0:
			acc += q[i].distance_to(q[i - 1])
		var s := float(i) / float(m - 1)
		var hw := maxf(0.02, float(wf.call(s)) * 0.5)
		var nl := nr[i].dot(L)
		var col := Color(nl * 0.5 + 0.5, hw / 4.0, kip, s * s_end)
		verts[i * 2] = q[i] + nr[i] * hw
		verts[i * 2 + 1] = q[i] - nr[i] * hw
		cols[i * 2] = col
		cols[i * 2 + 1] = col
		uvs[i * 2] = Vector2(0.0, acc / V_OLCEK)
		uvs[i * 2 + 1] = Vector2(1.0, acc / V_OLCEK)
	var idx := PackedInt32Array()
	idx.resize((m - 1) * 6)
	for i in m - 1:
		var a := i * 2
		idx[i * 6] = a
		idx[i * 6 + 1] = a + 1
		idx[i * 6 + 2] = a + 2
		idx[i * 6 + 3] = a + 1
		idx[i * 6 + 4] = a + 3
		idx[i * 6 + 5] = a + 2
	RenderingServer.canvas_item_add_triangle_array(ci.get_canvas_item(), idx, verts, cols, uvs)


static func _normaller(q: PackedVector2Array) -> PackedVector2Array:
	var m := q.size()
	var out := PackedVector2Array()
	out.resize(m)
	for i in m:
		var t := q[mini(m - 1, i + 1)] - q[maxi(0, i - 1)]
		if t.length_squared() < 1e-8:
			t = Vector2.DOWN
		t = t.normalized()
		out[i] = Vector2(-t.y, t.x)
	return out


static func _yumusat(p: PackedVector2Array, k: int) -> PackedVector2Array:
	## Catmull-Rom alt bölme: her parçaya k ara nokta (yumuşak fırça eğrisi).
	var m := p.size()
	var out := PackedVector2Array()
	for i in m - 1:
		var p0 := p[maxi(0, i - 1)]
		var p1 := p[i]
		var p2 := p[i + 1]
		var p3 := p[mini(m - 1, i + 2)]
		for j in k:
			var t := float(j) / float(k)
			var t2 := t * t
			var t3 := t2 * t
			out.append(0.5 * ((2.0 * p1) + (-p0 + p2) * t + (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * t2 + (-p0 + 3.0 * p1 - 3.0 * p2 + p3) * t3))
	out.append(p[m - 1])
	return out
