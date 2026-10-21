class_name BenguSac
extends Node2D
## Bengü'nün uzun saçı (stil v2, v21): kurt başlığının altından çıkan, altın bağla toplanmış gür, dökümlü bir yele + kulağın
## arkasından omza düşen tek ince örgü. Sprite'a çizilmez: her kare çalışma zamanında verlet zinciriyle benzetilir ve
## mürekkep-cel fırça tutamları olarak çizilir (shaders/bengu_sac.gdshaderinc).
##
## Görünüş: yele tek bir şerit değil; benzetilen omurgayı paylaşan bir gövde kütlesi (koyu, silüeti verir) + üstünde farklı
## en / boy / tonda yedi tutam (arka tutamlar koyu, ön tutamlar açık; uçta birbirinden ayrılıp ayrı sivri uçlarla biter) +
## kütleden kopan üç ince uçuşan tel. Her tutamın kendi evresiyle hafif dalgası vardır (uçta canlı, kökte sakin).
##
## Hareket: kök sert, uç gevşek (ebeveyne göre bükülme yayı, uca doğru zayıflar), hızın karesiyle artan hava sürtünmesi
## (koşuda arkaya akar, durunca öne salınıp yerleşir), yön değişiminde kök doğrultusu aşağıdan dolaşarak açısal hız sınırıyla
## döner (saç başın üstünden kamçılanmaz), baş + sırt kapsülü çarpışması, esinti bakış yönüne göre (durgunken öne sürüklenmez).
##
## Çapalar (tools/artgen/bengu_ink.py -> bengu_v2.json, her kare): 'sac' (ense, saçın başlıktan çıktığı nokta), 'sac_d'
## (kökün ilk doğrultusu, ekran açısı; yuvarlanmada topla döner), 'neck' / 'hip' (sırt çizgisi), 'head' (baş çemberi).
## Çapalar SpriteAnim yerelinde (dünya birimi, yöne göre aynalı); benzetim küresel uzayda (ataletin gerçek olması için).
##
## Katmanlar: bu düğüm ("Sac") SpriteAnim'in ilk çocuğu (gövdenin arkası); `on` düğümü gövde sprite'ından hemen sonra
## (yele post pelerinin üstüne düşer, örgü omzun önünden sarkar; kol iskeletinin altında). Çizim verisi her karede bir kez
## SpriteAnim yerelinde kurulur (`_ag`); hayalet izi ve darbe karesi aynı veriyi `kopya` ile dondurup çizer.

const SHADER := preload("res://shaders/bengu_sac.gdshader")
const SHADER_HAYALET := preload("res://shaders/bengu_sac_hayalet.gdshader")
const DT := 1.0 / 120.0             # sabit alt adım (kare hızından bağımsız aynı davranış)
const G := 900.0                    # saça etki eden yerçekimi (oyuncu GRAV 1180; saç havada daha süzülür)
const SAC_A0 := 2.0915              # 'sac_d' taban açısı atan2(0.87, -0.5): baş dönüşü = sac_d - SAC_A0
const LIGHT := Vector2(-0.7408, -0.6717)  # dünya ışığı (sol üst; inkkit.LIGHT)
const MAX_STEPS := 8
const V_OLCEK := 64.0              # UV.y = uzunluk / V_OLCEK (gölgelendirici geri çarpar)
const KOK_EKLEM := 3                # açı sınırlı kök eklemi sayısı
const ITERS := 6                    # kısıt turu (alt adım başına)
const DONUS_W := 15.0               # kök doğrultusunun en büyük açısal hızı (rad/sn): yön değişiminde kamçıyı keser
const SURT_L := 1.5                 # doğrusal hava sürtünmesi (1/sn): salınım yerleşsin
const SURT_Q := 0.024               # karesel hava sürtünmesi (1/birim): yavaş salınım serbest, koşuda güçlü akış
const SURT_I := 2.5                 # iç sürtünme (1/sn): köke göre bağıl hız sönümü (teller birbirine sürtünür: salınım
									# birkaç kez değil bir kez olur; duruşta yine de öne salınıp yerleşir)

# kipler (gölgelendiricideki COLOR.b): saç tutamı 0..0.14 (ton kodlu), tel 0.2, örgü 0.5, halka 0.68, boncuk 1
const M_SAC := 0.0
const M_TEL := 0.2
const M_ORGU := 0.5
const M_HALKA := 0.68
const M_BONCUK := 1.0

# yele tutamları: [u (enine yer, -1 sırt yanı .. +1 dış yan), boy, en çarpanı, ton (0 koyu arka .. 1 açık ön), tohum]
# çizim sırası: arka tutamlar önce, ön tutamlar en üstte
const TUTAMLAR := [
	[-0.62, 0.86, 0.50, 0.15, 0.11],
	[0.64, 0.78, 0.48, 0.22, 0.47],
	[0.26, 0.94, 0.54, 0.48, 0.83],
	[-0.30, 0.98, 0.52, 0.55, 1.29],
	[0.84, 0.64, 0.34, 0.62, 1.71],
	[0.02, 1.00, 0.56, 0.84, 2.13],
	[-0.78, 0.72, 0.32, 0.92, 2.59],
]
# uçuşan teller: [u, başlangıç (omurga oranı), boy, tohum]
const TELLER := [
	[1.05, 0.14, 0.62, 0.3],
	[-1.0, 0.22, 0.5, 1.9],
	[0.9, 0.42, 0.52, 3.3],
]
static var _IDX := {}               # şerit üçgen indeksleri (nokta sayısına göre)


class Zincir:
	## Verlet zinciri: p şimdiki, o önceki konum (küresel). Kök (0) başlığa, ikinci nokta kök doğrultusuna sabit.
	var ad := ""
	var p := PackedVector2Array()
	var o := PackedVector2Array()
	var n := 10
	var seg := 2.0
	var off := Vector2.ZERO          # kök ofseti: baş çerçevesinde, yüz sağa bakarken (dünya birimi)
	var ust := true                  # true: gövdenin önünde çizilir (on düğümü)
	var kip := 0.0
	var gen := 3.0                   # en geniş (dünya birimi)
	var sert0 := 0.3                 # bükülme yayı: kökte (alt adım başına düzeltme oranı)
	var sert1 := 0.02                # bükülme yayı: uçta
	var govde := true                # sırt + baş çarpışması (örgü kulağın önünden sarktığı için kapalı)
	var bukul0 := 0.22               # kök eklem açısı sınırı (radyan): ilk eklemde
	var bukul := 0.6                 # son kök ekleminde (KOK_EKLEM)
	var drot := 0.0                  # kök doğrultusuna ek dönüş (yüz sağa bakarken; radyan)
	var gr := 1.0                    # sırt kapsülü yarıçap çarpanı
	var r0 := Vector2.ZERO           # kök: son alt adımdaki / bu karedeki (küresel)
	var r1 := Vector2.ZERO
	var a0 := 0.0                    # kök doğrultusu açısı (küresel, ekran): son alt adımdaki / bu karedeki
	var a1 := 0.0
	var faz := 0.0
	var yl := Vector2.ZERO           # yumuşatılmış kök (SpriteAnim yereli), son yön
	var yf := 1


class On:
	## Gövdenin önündeki saç katmanı: çizimi sahibi yapar.
	extends Node2D
	var sac: BenguSac

	func _draw() -> void:
		if sac:
			sac.ciz(self, true)


class Kopya:
	## Dondurulmuş saç çizimi (hayalet izi / darbe karesi): kurulduğu andaki üçgen dizileri.
	extends Node2D
	var ag: Array = []

	func _draw() -> void:
		for m in ag:
			RenderingServer.canvas_item_add_triangle_array(get_canvas_item(), m[0], m[1], m[2], m[3])


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
var _head := Vector2.ZERO
var _face := 1
var _son_anim := ""
var _ag_arka: Array = []           # bu karenin çizim verisi (SpriteAnim yereli): [indeks, köşe, renk, uv, hayalette mi]
var _ag_on: Array = []
var _yan := 1.0                    # tutam yayılımının yönü (bakışa doğru yumuşatılmış)
var _onb := {}                     # yele profilleri önbelleği (_onbellek)
var _ucus := 0.0                   # uç hızı (yumuşatılmış): tutam dalgası hareketle canlanır
var olcum_us := 0.0                # son karenin benzetim + çizim verisi süresi (mikrosaniye; test ölçer)


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
	s.name = "Sac"
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


static func bul(sprite: Node) -> BenguSac:
	## Bir SpriteAnim'in (ya da onun gövde sprite'ının) saçı; yoksa null.
	if sprite == null:
		return null
	if not (sprite is SpriteAnim) and sprite.get_parent() is SpriteAnim:
		sprite = sprite.get_parent()
	return sprite.get_node_or_null("Sac") as BenguSac


func _kur() -> void:
	# ağaç duraklıyken de çalışır (başlık ekranı / duraklatma): yalnızca ilk duruşu kurar ve çizer, benzetim durur
	process_mode = Node.PROCESS_MODE_ALWAYS
	mat = ShaderMaterial.new()
	mat.shader = SHADER
	material = mat
	on.material = mat
	# gür yele (sırttan beline iner) + yakın örgü (kulağın arkasından omuz üstüne)
	var y := _z("kuyruk", 13, 2.15, Vector2(1.3, 2.4), M_SAC, 9.0)
	y.gr = 0.8  # yele sırtın üstünde yatar (gövdenin önünde çizilir: post pelerinin üstüne düşer)
	y.bukul0 = 0.2
	y.bukul = 0.55
	y.sert0 = 0.05
	y.sert1 = 0.0
	var o := _z("yakin_orgu", 8, 1.8, Vector2(2.2, 2.6), M_ORGU, 1.5)
	o.govde = false
	o.drot = -0.55  # kulağın arkasından, başlığın yan postunun altından aşağı çıkar
	o.bukul0 = 0.25
	o.bukul = 0.6
	o.sert0 = 0.04
	o.sert1 = 0.0
	o.faz = 3.1
	zincirler = [y, o]


func _z(ad: String, n: int, seg: float, off: Vector2, kip: float, gen: float) -> Zincir:
	var z := Zincir.new()
	z.ad = ad
	z.n = n
	z.seg = seg
	z.off = off
	z.kip = kip
	z.gen = gen
	z.p.resize(n)
	z.o.resize(n)
	return z


func sarsil(v: Vector2) -> void:
	## Dışarıdan ani itki (ör. ağır darbe): uçlara doğru artan hız (birim/sn).
	for z in zincirler:
		for i in range(2, z.n):
			z.o[i] -= v * DT * (float(i) / float(z.n - 1))


# ------------------------------------------------------------------ çapalar
func _kok(z: Zincir, delta: float) -> void:
	## Bu karenin kökü (r1) ve kök doğrultusu açısı (a1), küresel. Çapa sprite karesiyle (8-18 fps) basamaklı değişir: yerel
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
	if z.yf != f:  # yön değişti: yumuşatılmış çapa aynalanır (baş da aynalandı; kök başın içinden kaymasın)
		z.yl.x = -z.yl.x
		z.yf = f
	var dir_l := Vector2(cos(ang), sin(ang)).rotated(z.drot * f)
	var dg := anim.global_transform.basis_xform(dir_l)
	var tgt := atan2(dg.y, dg.x)
	if _reset or delta <= 0.0:
		z.yl = hedef
		z.a1 = tgt
	else:
		z.yl = z.yl.lerp(hedef, 1.0 - exp(-delta * 26.0))
		# kök doğrultusu küresel açıyla yumuşar; büyük dönüşte (yön değişimi) her zaman aşağıdan dolaşır ve açısal hızı
		# sınırlıdır: eski sürümde doğrultu anında aynalanıyor, zincir kökte katlanıp başın üstünden öne kamçılanıyordu
		var diff := wrapf(tgt - z.a1, -PI, PI)
		if absf(diff) > 1.2 and sin(z.a1 + diff * 0.5) < 0.0:
			diff -= signf(diff) * TAU
		var d := diff * (1.0 - exp(-delta * 22.0))
		z.a1 += clampf(d, -DONUS_W * delta, DONUS_W * delta)
		z.a1 = wrapf(z.a1, -PI, PI)
	z.r1 = anim.to_global(z.yl)


func _govde_capa() -> void:
	var f := anim.facing
	var nk: Variant = anim.anchor("neck")
	var hp: Variant = anim.anchor("hip")
	var hd: Variant = anim.anchor("head")
	_neck = anim.to_global(nk if nk != null else Vector2(4.0 * f, -40.0))
	_hip = anim.to_global(hp if hp != null else Vector2(0.0, -24.0))
	_head = anim.to_global((hd as Vector2) + Vector2(-0.6 * f, -0.8) if hd != null else Vector2(4.0 * f, -48.0))
	_face = f


func _dinlen(z: Zincir) -> void:
	## Dinlenme duruşu: kökten başlık doğrultusunda çıkar, sonra sırttan aşağı sarkar.
	var down := Vector2(-_face * 0.2, 1.0).normalized()
	var d1 := Vector2.from_angle(z.a1)
	var q := z.r1
	for i in z.n:
		if i > 0:
			var k := clampf(float(i - 1) / 3.0, 0.0, 1.0)
			q += d1.lerp(down, k).normalized() * z.seg
		z.p[i] = q
	for it in 12:
		_kisit(z, z.r1, d1)
		if z.govde:
			_govde(z)
	for i in z.n:
		z.o[i] = z.p[i]
	z.r0 = z.r1
	z.a0 = z.a1


# ------------------------------------------------------------------ benzetim
func _process(delta: float) -> void:
	if Prof.on:
		var t0 := Time.get_ticks_usec()
		_process_ic(delta)
		Prof.ekle(&"bengu", t0)
		return
	_process_ic(delta)


func _process_ic(delta: float) -> void:
	if anim == null or not is_visible_in_tree():
		_reset = true
		return
	var t0 := Time.get_ticks_usec()
	_t += delta
	_govde_capa()
	if _reset:
		_yan = float(_face)
	for z in zincirler:
		_kok(z, delta)
		if _reset or z.r1.distance_to(z.r0) > 48.0:  # ışınlanma (kapı, güvenli noktaya dönüş, dönüşüm bitişi)
			_dinlen(z)
	_reset = false
	mat.set_shader_parameter("vcol_linear", get_viewport().use_hdr_2d)
	if not (get_tree().paused or not anim.can_process()):
		# mat parametreleri gövdeden: vuruş parlaması, zehir tonu, ay gölgesi saçta da aynı
		if anim.mat:
			for k in ["flash", "tint", "moon_shade"]:
				var v: Variant = anim.mat.get_shader_parameter(k)
				if v != null:
					mat.set_shader_parameter(k, v)
		_eylem()
		_acc = minf(_acc + delta, DT * MAX_STEPS)
		var steps := int(_acc / DT)
		_acc -= steps * DT
		if steps > 0:
			var on_floor := pl != null and pl.is_on_floor()
			var floor_y := pl.global_position.y - 0.4 if pl else 1e9
			var hiz := absf(pl.velocity.x) if pl else 0.0
			for k in steps:
				var u := float(k + 1) / float(steps)
				for z in zincirler:
					var a := lerp_angle(z.a0, z.a1, u)
					_adim(z, z.r0.lerp(z.r1, u), _kok_yon(z, a), on_floor, floor_y, hiz)
			for z in zincirler:
				z.r0 = z.r1
				z.a0 = z.a1
		var y: Zincir = zincirler[0]
		var uv := (y.p[y.n - 1] - y.o[y.n - 1]).length() / DT
		_ucus = lerpf(_ucus, uv, 1.0 - exp(-delta * 6.0))
		_yan = move_toward(_yan, float(_face), delta * 6.0)
	_ag_kur()
	olcum_us = float(Time.get_ticks_usec() - t0)
	queue_redraw()
	on.queue_redraw()


func _eylem() -> void:
	## Animasyon başlangıcında küçük itkiler: saldırıda saç geride kalıp savrulur, darbede sıçrar, inişte çöker.
	var a := anim.anim
	if a == _son_anim:
		return
	_son_anim = a
	var f := float(_face)
	if a.begins_with("atk_"):
		sarsil(Vector2(-f * 70.0, -45.0))
	elif a == "hurt":
		sarsil(Vector2(-f * 40.0, -110.0))
	elif a == "land":
		sarsil(Vector2(0.0, 70.0))


func _kok_yon(z: Zincir, a: float) -> Vector2:
	## Saç bağı tam sabit değil: kök doğrultusu saçın kendi doğrultusuna doğru yarı yarıya döner (en çok ~105°). Düşüşte
	## saç bağdan itibaren yukarı kalkar, koşuda kökten arkaya akar; tam sabit kökte saç bağın altında U çizip çengel
	## gibi kıvrılıyordu. Yele yalnızca sırt yanındayken döner (başın üstüne / yüzün önüne yönelmez).
	var D := Vector2.from_angle(a)
	var h := z.p[z.n / 2] - z.p[0]  # zincirin ortası (kök bölgesi D'ye bağlı, ona bakmak kendini doğrulardı)
	if h.length_squared() < 1e-4:
		return D
	h = h.normalized()
	if z.govde and h.x * float(_face) > -0.05:
		return D
	var fark := clampf(D.angle_to(h) * 0.5, -1.85, 1.85)
	var e := D.rotated(fark)
	if z.govde and e.x * float(_face) > -0.1:  # sırt yanında kalsın
		return D
	return e


func _adim(z: Zincir, R: Vector2, D: Vector2, on_floor: bool, floor_y: float, hiz: float) -> void:
	var dt2 := DT * DT
	z.o[0] = z.p[0]
	z.p[0] = R
	var dR := R - z.o[0]
	var ic := maxf(0.0, 1.0 - SURT_I * DT)
	# esinti: bakış yönüne göre arkaya doğru hafif (durgun saç öne sürüklenmez) + iki yana eşit ara ara sağanak
	var gust := pow(maxf(0.0, sin(_t * 0.53 + z.faz * 0.3)), 3.0)
	var sway := sin(_t * 0.29 + 1.3) * pow(maxf(0.0, sin(_t * 0.41)), 2.0)
	var wind := Vector2(-float(_face) * (5.0 + 14.0 * gust) + 16.0 * sway, 0.0)
	var flap := clampf(hiz / 155.0, 0.0, 1.5)
	var last := float(z.n - 1)
	var ab := _hip - _neck
	var l2 := maxf(ab.length_squared(), 1.0)
	for i in range(1, z.n):
		var vel := dR + (z.p[i] - z.o[i] - dR) * ic
		var vl := vel.length() / DT
		# hava sürtünmesi: doğrusal + hızın karesi (yavaş salınım uzun sürer, koşuda saç arkaya akar)
		vel *= maxf(0.0, 1.0 - (SURT_L + SURT_Q * vl) * DT)
		z.o[i] = z.p[i]
		var fi := float(i) / last
		var acc := Vector2(0.0, G) + wind * (0.3 + fi)
		acc.y += sin(_t * 1.6 + i * 0.55 + z.faz) * 9.0 * fi
		if z.govde and i >= 3:
			# gövde çizgisinin önüne geçen saç yavaşça sırta döner (omzun üstünden arkaya kayar gibi); hafif tutulur ki
			# duruşta saç bir kez öne salınabilsin
			var tq := clampf((z.p[i] - _neck).dot(ab) / l2, 0.0, 1.3)
			var on_x := (z.p[i].x - (_neck.x + ab.x * tq)) * float(_face)
			if on_x > 0.0:
				acc.x -= float(_face) * 650.0 * minf(on_x / 6.0, 1.0)
		if flap > 0.05 and i >= 2:
			# koşuda omurga boyunca ilerleyen yumuşak dalga (şeride dik)
			var tg := (z.p[i] - z.p[i - 1]).normalized()
			acc += Vector2(-tg.y, tg.x) * sin(_t * 8.5 - i * 0.75 + z.faz) * 30.0 * flap * fi * fi
		z.p[i] += vel + acc * dt2
	# bükülme yayı: her parça ebeveyninin doğrultusunu sürdürmeye çalışır; kökte sert (saç bağı), uca doğru gevşek. Konum
	# düzeltmesi olduğundan hıza da yansır: ip gibi sarkmaz, jöle gibi de titremez (sürtünme sönümler)
	var prev := D
	for i in range(1, z.n):
		var fi := float(i - 1) / last
		var k := lerpf(z.sert1, z.sert0, (1.0 - fi) * (1.0 - fi))
		var want := z.p[i - 1] + prev * z.seg
		z.p[i] = z.p[i].lerp(want, k)
		var d := z.p[i] - z.p[i - 1]
		if d.length_squared() > 1e-8:
			prev = d.normalized()
	for it in ITERS:
		_kisit(z, R, D)
		if it == ITERS - 3:
			if z.govde:
				_govde(z)
			if z.govde:
				_bas(z)
			_zemin(z, on_floor, floor_y)
	# uzama sınırı: hızlanmada %4'ten fazla uzayan parça kısaltılır; önceki konum da aynı kaydırılır (hız eklenmez)
	for i in range(1, z.n):
		var d := z.p[i] - z.p[i - 1]
		var l := d.length()
		if l > z.seg * 1.04:
			var np := z.p[i - 1] + d * (z.seg * 1.04 / l)
			z.o[i] += np - z.p[i]
			z.p[i] = np


func _kisit(z: Zincir, R: Vector2, D: Vector2) -> void:
	# kök ve ikinci nokta sabit: saç başlığın altından belirli bir doğrultuda çıkar (yarı bağlı ikinci nokta, açı sınırıyla
	# sertleşen zincirin ağırlığıyla sürüklenip saçı başın üstüne devirebiliyordu)
	z.p[1] = R + D * z.seg
	for i in range(2, z.n):
		var d := z.p[i] - z.p[i - 1]
		var l := d.length()
		if l < 1e-5:
			continue
		var corr := d * ((l - z.seg) / l)
		if i == 2:
			z.p[i] -= corr
		else:
			z.p[i - 1] += corr * 0.5
			z.p[i] -= corr * 0.5
	# kök bölgesinde eklem açısı sınırı: ilk parçalar ebeveynine göre en çok bukul0..bukul kadar dönebilir (saç bağının
	# sertliği; saç kökte katlanıp başın üstüne devrilmez). Zincirin geri kalanı yalnızca yumuşak bükülme yayıyla
	# serbest: tüm zincirde açı sınırı olunca kıvrık saç kilitli bir mekanizma gibi donup kalıyordu; eski "i ile i+2 arası
	# en kısa uzaklık" kısıtı da noktayı dışarı iterek saçı yukarı katlayıp düğümlüyordu
	var pa := z.p[1] - z.p[0]
	for i in range(2, mini(z.n, KOK_EKLEM + 2)):
		var pb := z.p[i] - z.p[i - 1]
		var ang := pa.angle_to(pb)
		var lim := lerpf(z.bukul0, z.bukul, float(i - 2) / float(KOK_EKLEM - 1))
		if absf(ang) > lim:
			pb = pb.rotated(signf(ang) * lim - ang)
			z.p[i] = z.p[i - 1] + pb
		pa = pb


func _govde(z: Zincir) -> void:
	# sırt: gövde bir kapsül (boyun -> kalça, sprite silüetine denk yarıçap). Sırt yarısında içine giren nokta dışarı
	# itilir. Göğüs yarısındaki nokta itilmez (saç gövdenin yanından, önünden geçebilir; yön değişimi / yuvarlanmadan sonra
	# önde kalan saç `_adim`daki sırta dönüş ivmesiyle arkaya süzülür). Eski sürüm göğüs yanındaki noktayı kapsülün öbür
	# yanına zorluyordu; sertleşen zincirde saç gövdeye takılıp önde kıvrık kalabiliyordu.
	# Kapsül kökün altından (omuz hizası) başlar ve üst kapağı yoktur: kök kapsülün içinde kalınca saç boynun çevresine
	# atkı gibi dolanıp orada asılı kalıyordu.
	# Hızla öne savrulan nokta (duruşta öne salınım) kapsülden geçebilir: saç omzun yanından öne gelip geri döner
	var top := _neck + (_hip - _neck).normalized() * 4.0
	var ab := _hip - top
	var l2 := maxf(ab.length_squared(), 1.0)
	var dR := z.p[0] - z.o[0]
	for i in range(3, z.n):
		var q := z.p[i]
		if ((q - z.o[i] - dR).x * float(_face)) > 0.3 and i > z.n / 3:  # > ~36 birim/sn öne
			continue
		var t := (q - top).dot(ab) / l2
		if t < 0.0:
			continue
		t = minf(t, 1.3)
		var c := top + ab * t
		var rel := q - c
		var r := (lerpf(6.1, 5.4, minf(t, 1.0)) + maxf(0.0, t - 1.0) * 6.0) * z.gr   # v39: ince bel (x0,93; eski 6,6 -> 5,8)
		var dl := rel.length()
		if dl < r:
			var nrm := rel / dl if dl > 1e-3 else Vector2(-_face, 0.0)
			if nrm.x * float(_face) < 0.15:
				z.p[i] = q.lerp(c + nrm * r, 0.5)


func _bas(z: Zincir) -> void:
	# baş / başlık çemberi: saç başın üstünden ya da yüzün önünden geçmez. Yalnızca yüz yanı ve tepe iter (yüz yanındaki
	# nokta ense yanına çevrilir); kökün bulunduğu ense-alt yarı serbest (orada da itseydi saç başın çevresine dolanıp
	# takılabilirdi)
	var r := 6.4   # v39: başlık x0,86 küçük (7,2)
	for i in range(3, z.n):
		var rel := z.p[i] - _head
		var dl := rel.length()
		if dl < r:
			var nrm := rel / dl if dl > 1e-3 else Vector2(-_face, -0.3)
			var yuz := nrm.x * float(_face) > -0.2
			if not yuz and nrm.y > -0.45:
				continue
			if yuz:
				nrm = Vector2(-float(_face) * 0.75, minf(nrm.y, -0.2)).normalized()
			z.p[i] = z.p[i].lerp(_head + nrm * r, 0.6)


func _zemin(z: Zincir, on_floor: bool, floor_y: float) -> void:
	# zemin: yerdeyken saç toprağın içine girmez, sürtünür
	if on_floor:
		for i in range(2, z.n):
			if z.p[i].y > floor_y:
				z.p[i].y = floor_y
				z.o[i].x = lerpf(z.o[i].x, z.p[i].x, 0.35)


# ------------------------------------------------------------------ çizim verisi
func _draw() -> void:
	ciz(self, false)


func ciz(ci: CanvasItem, front: bool) -> void:
	var rid := ci.get_canvas_item()
	for m in (_ag_on if front else _ag_arka):
		RenderingServer.canvas_item_add_triangle_array(rid, m[0], m[1], m[2], m[3])


func kopya(xform: Transform2D, m: Material, sade := false) -> Kopya:
	## Bu karenin saç çiziminin dondurulmuş kopyası (hayalet izi, darbe karesi). xform: SpriteAnim'in o anki dönüşümü
	## (kopyanın ebeveyn uzayında). sade: yalnızca silüet şeritleri (yele kütlesi + örgü gövdesi): toplamalı hayalette üst
	## üste binen tutamlar parlaklığı katlıyordu. Ağaca eklemek çağıranın işi.
	var k := Kopya.new()
	for m2 in _ag_arka + _ag_on:
		if not sade or m2[4]:
			k.ag.append(m2)
	k.transform = xform
	k.material = m
	return k


func hayalet(col: Color, life: float, z := 1) -> void:
	## FX.ghost'un saç eşi: aynı renkte, toplamalı, solan kopya (gövde hayaletiyle aynı yerde).
	if FX.root == null or not is_visible_in_tree() or _ag_on.is_empty():
		return
	var m := ShaderMaterial.new()
	m.shader = SHADER_HAYALET
	m.set_shader_parameter("hayalet_col", col)
	m.set_shader_parameter("vcol_linear", get_viewport().use_hdr_2d)
	var k := kopya(anim.global_transform, m, true)
	k.z_index = z
	FX.root.add_child(k)
	k.global_transform = anim.global_transform
	var tw := k.create_tween()
	tw.tween_method(func(a: float) -> void: m.set_shader_parameter("hayalet_col", Color(col, a)), col.a, 0.0, life)
	tw.tween_callback(k.queue_free)


func _ag_kur() -> void:
	## Bu karenin üçgen dizileri (SpriteAnim yereli). Yele: kütle + tutamlar + teller + saç bağı; örgü.
	_ag_arka = []
	_ag_on = []
	var inv := anim.get_global_transform().affine_inverse()
	var L := (inv.basis_xform(LIGHT)).normalized()
	for z in zincirler:
		var pts := PackedVector2Array()
		pts.resize(z.n)
		for i in z.n:
			pts[i] = inv * z.p[i]
		pts[0] = inv * z.r1
		var sm := _yumusat(pts, 2)
		var hedef: Array = _ag_on if z.ust else _ag_arka
		if z.kip == M_SAC:
			_yele(hedef, sm, z, L)
		else:
			_orgu(hedef, sm, z, L)


func _w_kutle(s: float, W: float) -> float:
	## yelenin gövde kütlesi: kökte bağda toplu, ortaya doğru en gür, 0,88'de sivri biter
	return W * (0.34 + 0.66 * sin(minf(s * 2.2, 1.0) * PI * 0.5)) * pow(maxf(0.0, 1.0 - s / 0.88), 0.5)


func _onbellek(m: int, W: float) -> Dictionary:
	## Yelenin karadan kareye değişmeyen profilleri (omurga nokta sayısına göre bir kez): kütle eni, tutam / tel ofset,
	## dalga genliği ve en profilleri. Her karede yalnızca omurga, yön (yan) ve zaman değişir.
	if _onb.get("m", -1) == m:
		return _onb
	var last := float(m - 1)
	var d := {"m": m}
	var mm := int(last * 0.88) + 1
	var khw := PackedFloat32Array()
	khw.resize(mm)
	for i in mm:
		khw[i] = _w_kutle(float(i) / last, W) * 0.5
	d["kutle"] = khw
	var tl_list := []
	for td in TUTAMLAR:
		var cnt := maxi(3, int(round(last * float(td[1]))) + 1)
		var off := PackedFloat32Array()
		var amp := PackedFloat32Array()
		var lw := PackedFloat32Array()
		off.resize(cnt)
		amp.resize(cnt)
		lw.resize(cnt)
		for i in cnt:
			var s := float(i) / last
			var tt := float(i) / float(cnt - 1)
			var wk := _w_kutle(minf(s, 0.45), W)
			# enine yer + uçta ayrılma + tutama özgü hafif uç kıvrımı (bazısı içe, bazısı dışa döner: düz diken gibi durmaz)
			off[i] = float(td[0]) * (wk * 0.4 * (0.75 + 0.3 * tt) + 0.7 * tt * tt * tt) + sin(float(td[4]) * 2.7) * 0.9 * pow(tt, 2.5)
			amp[i] = tt * tt
			lw[i] = W * float(td[2]) * (0.45 + 0.55 * sin(minf(tt * 2.0, 1.0) * PI * 0.5)) * pow(maxf(0.0, 1.0 - tt), 0.6) * 0.5
		tl_list.append([cnt, off, amp, lw])
	d["tutam"] = tl_list
	var te_list := []
	for tl in TELLER:
		var bas := int(last * float(tl[1]))
		var cnt2 := mini(int(last * float(tl[2])), m - 1 - bas)
		var off2 := PackedFloat32Array()
		var amp2 := PackedFloat32Array()
		var tt2s := PackedFloat32Array()
		var lw2 := PackedFloat32Array()
		off2.resize(cnt2)
		amp2.resize(cnt2)
		tt2s.resize(cnt2)
		lw2.resize(cnt2)
		for j in cnt2:
			var s2 := float(bas + j) / last
			var tt2 := float(j) / float(cnt2 - 1)
			var wk2 := _w_kutle(minf(s2, 0.5), W)
			off2[j] = float(tl[0]) * (wk2 * 0.5 * (1.0 - tt2) + (wk2 * 0.25 + 2.2) * tt2 * tt2)
			amp2[j] = tt2 * tt2
			tt2s[j] = tt2 * 7.0
			lw2[j] = 0.2 * sin(minf(1.0, tt2 * 1.4 + 0.15) * PI) + 0.02
		te_list.append([bas, cnt2, off2, amp2, tt2s, lw2])
	d["tel"] = te_list
	d["bag"] = PackedFloat32Array([W * 0.18, W * 0.19, W * 0.2])
	_onb = d
	return d


func _yele(out: Array, sm: PackedVector2Array, z: Zincir, L: Vector2) -> void:
	var nr := _normaller(sm)
	var m := sm.size()
	var last := float(m - 1)
	var ob := _onbellek(m, z.gen)
	var canli := clampf(_ucus / 120.0, 0.0, 1.0)  # hareketle tutam dalgası büyür
	# u = -1 sırt yanı: sarkan saçın normali sola bakar, yüz sağa bakarken bu dış yan; yön değişince yumuşakça aynalanır
	# (tutamlar dönüşte birbirinin üstünden çaprazlanarak geçer)
	var yan := _yan
	# sıkı kıvrımda en daralır: şerit yarı eni eğrilik yarıçapını aşınca iç kenar kendi üstüne katlanıp saçı kalın bir boru
	# gibi gösteriyordu (düşüşte yukarı savrulan saç)
	var dar := PackedFloat32Array()
	dar.resize(m)
	var wyar := z.gen * 0.5
	for i in m:
		var a0 := sm[maxi(0, i - 1)]
		var a2 := sm[mini(m - 1, i + 1)]
		var d1 := sm[i] - a0
		var d2 := a2 - sm[i]
		var don := absf(d1.angle_to(d2)) if d1.length_squared() > 1e-6 and d2.length_squared() > 1e-6 else 0.0
		var yaricap := (d1.length() + d2.length()) * 0.5 / maxf(don, 1e-3)
		dar[i] = clampf(yaricap * 1.1 / wyar, 0.4, 1.0)
	for i in range(1, m - 1):  # komşularla yumuşat
		dar[i] = minf(dar[i], (dar[i - 1] + dar[i] + dar[i + 1]) / 3.0)
	# 1) kütle: silüeti verir, en koyu ton (tutamların arasındaki boşluk derinlik olarak okunur)
	var khw: PackedFloat32Array = (ob["kutle"] as PackedFloat32Array).duplicate()
	for i in khw.size():
		khw[i] *= dar[i]
	_serit(out, sm.slice(0, khw.size()), khw, M_SAC, 0.0, L, 0.0, 0.88)
	# 2) tutamlar: aynı omurga, enine yayılmış; uçta birbirinden ayrılır (ayrı sivri uçlar), kendi evresiyle dalgalanır
	var ws := _t * (1.1 + 1.6 * canli)
	var wa := 0.25 + 0.35 * canli
	var tl_list: Array = ob["tutam"]
	for k in TUTAMLAR.size():
		var td: Array = TUTAMLAR[k]
		var c: Array = tl_list[k]
		var cnt: int = c[0]
		var off: PackedFloat32Array = c[1]
		var amp: PackedFloat32Array = c[2]
		var ph: float = float(td[4]) * 2.3 - ws
		var lw0: PackedFloat32Array = c[3]
		var lw := lw0.duplicate()
		var q := PackedVector2Array()
		q.resize(cnt)
		for i in cnt:
			q[i] = sm[i] + nr[i] * ((off[i] * yan + sin(float(i) / last * 6.0 + ph) * wa * amp[i]) * dar[i])
			lw[i] *= dar[i]
		_serit(out, q, lw, M_SAC, float(td[3]), L, float(td[4]), float(td[1]))
	# 3) uçuşan teller: kütlenin kenarından kopan ince, uzun kıvrımlar (gecikmeli, canlı)
	var ws2 := _t * (1.7 + 2.0 * canli)
	var wa2 := 0.5 + 0.6 * canli
	var te_list: Array = ob["tel"]
	for k in TELLER.size():
		var c2: Array = te_list[k]
		var bas: int = c2[0]
		var cnt2: int = c2[1]
		var off2: PackedFloat32Array = c2[2]
		var amp2: PackedFloat32Array = c2[3]
		var tts: PackedFloat32Array = c2[4]
		var ph2: float = float(TELLER[k][3]) - ws2
		var q2 := PackedVector2Array()
		q2.resize(cnt2)
		for j in cnt2:
			q2[j] = sm[bas + j] + nr[bas + j] * (off2[j] * yan + sin(tts[j] + ph2) * wa2 * amp2[j])
		_serit(out, q2, c2[5], M_TEL, 0.6, L, float(TELLER[k][3]), 1.0)
	# 4) saç bağı: başlığın altından çıkan kökte iki sıra altın sargı
	_serit(out, sm.slice(0, 3), ob["bag"], M_HALKA, 0.0, L, 0.0, 0.08)


func _orgu(out: Array, sm: PackedVector2Array, z: Zincir, L: Vector2) -> void:
	## Örgü: ince, V loblu; ucunda altın halka ve üç küçük sivri püskül, halkada turkuaz boncuk; kökte halka.
	var n := sm.size()
	var cut := int(n * 0.8)
	var W := z.gen
	var body := sm.slice(0, cut + 1)
	var hw := PackedFloat32Array()
	hw.resize(body.size())
	for i in body.size():
		hw[i] = W * (1.0 - 0.25 * float(i) / float(body.size() - 1)) * 0.5
	_serit(out, body, hw, M_ORGU, 0.0, L, 0.0, 0.8)
	var tuft := sm.slice(cut - 1, n)
	var nr := _normaller(tuft)
	var tm := tuft.size()
	for k in [-1, 1, 0]:
		var q := PackedVector2Array()
		var lw := PackedFloat32Array()
		q.resize(tm)
		lw.resize(tm)
		for i in tm:
			var tt := float(i) / float(tm - 1)
			q[i] = tuft[i] + nr[i] * (float(k) * W * 0.35 * tt + sin(tt * 5.0 + _t * 1.5 + float(k)) * 0.15 * tt)
			lw[i] = W * (0.75 if k == 0 else 0.55) * sin(minf(1.0, tt * 3.0 + 0.4) * PI * 0.5) * pow(1.0 - tt, 0.8) * 0.5
		_serit(out, q, lw, M_SAC, 0.75 if k == 0 else 0.4, L, 5.0 + k, 1.0)
	var band := sm.slice(maxi(0, cut - 2), mini(n, cut + 1))
	_serit(out, band, _sabit(band.size(), W * 0.62), M_HALKA, 0.0, L, 0.0, 0.8)
	_serit(out, sm.slice(0, 3), _sabit(3, W * 0.66), M_HALKA, 0.0, L, 0.0, 0.08)
	var nb := _normaller(sm)
	var bc := sm[mini(n - 1, cut)]
	_boncuk(out, bc + nb[mini(n - 1, cut)] * W * 0.2 + Vector2(0, 0.9), 0.8)


static func _sabit(m: int, v: float) -> PackedFloat32Array:
	var a := PackedFloat32Array()
	a.resize(m)
	a.fill(v)
	return a


func _boncuk(out: Array, c: Vector2, r: float) -> void:
	var v := PackedVector2Array([c + Vector2(-r, -r), c + Vector2(r, -r), c + Vector2(r, r), c + Vector2(-r, r)])
	var col := Color(0.5, r / 4.0, M_BONCUK, 1.0)
	var cols := PackedColorArray([col, col, col, col])
	var uv := PackedVector2Array([Vector2(0, 0), Vector2(1, 0), Vector2(1, 1), Vector2(0, 1)])
	out.append([PackedInt32Array([0, 1, 2, 0, 2, 3]), v, cols, uv, false])


func _serit(out: Array, q: PackedVector2Array, hw: PackedFloat32Array, kip: float, ton: float, L: Vector2, tohum: float, s_end: float) -> void:
	## Fırça şeridi: her noktada sol/sağ köşe. UV.x enine (0..1), UV.y kökten uzunluk (+ tohum: tutam başına desen kayması);
	## renk: r ışık yanı, g yarı genişlik / 4, b kip (saçta ton kodlu), a omurga oranı (0 kök .. s_end).
	var m := q.size()
	if m < 2:
		return
	var verts := PackedVector2Array()
	var cols := PackedColorArray()
	var uvs := PackedVector2Array()
	verts.resize(m * 2)
	cols.resize(m * 2)
	uvs.resize(m * 2)
	var b := kip + ton * 0.14 if kip == M_SAC else kip
	var acc := tohum * 0.37
	var ds := s_end / float(m - 1)
	var son := m - 1
	var onceki := q[0]
	for i in m:
		var p := q[i]
		acc += p.distance_to(onceki) / V_OLCEK
		onceki = p
		var tg := q[mini(son, i + 1)] - q[maxi(0, i - 1)]
		var nrm := Vector2(-tg.y, tg.x).normalized()
		var h := maxf(0.02, hw[i])
		var col := Color(nrm.dot(L) * 0.5 + 0.5, h * 0.25, b, float(i) * ds)
		var i2 := i * 2
		verts[i2] = p + nrm * h
		verts[i2 + 1] = p - nrm * h
		cols[i2] = col
		cols[i2 + 1] = col
		uvs[i2] = Vector2(0.0, acc)
		uvs[i2 + 1] = Vector2(1.0, acc)
	# 5. öğe: hayalet kopyasına girer mi (yalnızca silüet: yele kütlesi, örgü gövdesi)
	out.append([_indeks(m), verts, cols, uvs, (kip == M_SAC and ton == 0.0) or kip == M_ORGU])


static func _indeks(m: int) -> PackedInt32Array:
	## m noktalı şeridin üçgen indeksleri (nokta sayısına göre önbellekte; diziler salt okunur paylaşılır)
	var idx: Variant = _IDX.get(m)
	if idx != null:
		return idx
	var a2 := PackedInt32Array()
	a2.resize((m - 1) * 6)
	for i in m - 1:
		var a := i * 2
		a2[i * 6] = a
		a2[i * 6 + 1] = a + 1
		a2[i * 6 + 2] = a + 2
		a2[i * 6 + 3] = a + 1
		a2[i * 6 + 4] = a + 3
		a2[i * 6 + 5] = a + 2
	_IDX[m] = a2
	return a2


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
