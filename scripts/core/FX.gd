class_name FX
extends RefCounted
## Görsel efekt kütüphanesi (Dead Cells tarzı "görsel şölen" katmanı):
##   number / text     hasar sayıları, kısa yazılar (kritikte büyüyüp küçülür)
##   burst             genel parçacık patlaması
##   impact            darbe yıldızı: ışınlı parlama + beyaz flaş (her vuruşta)
##   sparks            yöne doğru saçılan kıvılcımlar (metal, taş)
##   blood             düşmana özgü renkte ağır, yere düşen sıçrantı
##   dust              koşu / iniş / yuvarlanma tozu (ışıktan etkilenmez, soluk)
##   ghost             hayalet iz (yuvarlanma, hücum): sprite'ın solan kopyası
##   trail             kılıç izi şeridi (WeaponTrail)
##   soul              ölümde göğe yükselen ruh zerreleri
##   corpse            ölen gövdenin savrulup dağılması
##   flash_light       anlık ışık parlaması (vuruş, patlama, savuşturma)
##   shock_line        yere vuruşta yanlara yayılan toz çizgisi
##   slash / ring      yay izi ve genişleyen halka
##   ground_slam       v16 yer çarpması: yerel flaş, zemini izleyen şok, toz, moloz, çatlak (GroundSlamFX)

static var root: Node2D
## v22 vuruş efekti yoğunluğu: Player._melee_hits bir isabetin süresince ayarlar (in_hit). hit_k 1 = tam efekt;
## < 1 = aynı düşmana hızlı ardışık vuruş / aynı savuruşun ek düşmanı: Enemy.take_hit'in sayısı, kanı, darbe çizgileri
## ve InkFX sıçrantısı küçülür (Enemy.gd'ye dokunmadan, efekt kütüphanesinde).
static var hit_k := 1.0
static var in_hit := false
static var _nums: Array = []       # v22: birleşen hasar sayıları [düğüm, etiket, değer, doğuş, konum]
static var _num_yer: Array = []    # v31: canlı sayıların doğuş yerleri [düğüm, doğuş, konum] (üst üste binmesin)
static var _ghost_t: Dictionary = {}  # v22: kaynak sprite -> son hayaletin anı (aynı karede üst üste binmesin)
static var dust_col := Color(0.62, 0.58, 0.6, 0.55)  # v11: biyom zemin tozu (Level ayarlar)
static var level: Node
static var _label_settings: Dictionary = {}
static var _dot_tex: Texture2D
static var _tex_cache: Dictionary = {}


## v2'de mürekkebe çevrilen darbe animasyonları (PVFX piksel kareleri) -> InkFX.hit türü
const INK_ANIM := {"crescent_slash": "cut", "resonant_break": "blunt", "mass_release": "blunt", "earth_rupture": "blunt",
	"electric_impact": "magic", "spectral_bloom": "magic", "void_implosion": "magic", "arcane_parry": "magic",
	"frost_nova": "magic", "acid_splash": "magic", "ember_jet": "magic", "warm_explosion": "magic", "leaf_gust": "magic",
	"solar_shrapnel": "pierce", "tether_catch": "magic"}


static func _ink_slash_sprite(n: String, pos: Vector2, rot: float, scale_v: Vector2, col: Color, flip_v: bool) -> void:
	## v2: büyük piksel kesik sprite'ları yerine mürekkep. Oyuncu savuruşlarının yayı/çizgisi/halkası mürekkep izinin
	## katmanlarıyla zaten çizilir (InkTrail); burada yalnızca vuruş işaretleri ve başkalarının (boss) yayları kalır.
	var p := InkFX.pal_from_color(col)
	match n:
		"spark_m":
			InkFX.hit("spark", pos, Vector2.from_angle(rot), p, 0, 0.9)
		"crit_burst":
			InkFX.stamp(pos)
		"kill_flash":
			InkFX.kill(pos, scale_v.x > 1.2)
		"arc_heavy", "arc", "arc_thin":
			# oyuncu dışı (boss) yay: kendiliğinden süpürülen fırça hilali
			if InkTrail.active == null or not is_instance_valid(InkTrail.active) or InkTrail.active.tip_dir() == Vector2.ZERO:
				var r := 0.4 * float(SlashFX.meta()[n]["w"]) * absf(scale_v.x)
				var f := 1 if scale_v.x >= 0.0 else -1
				var a0 := -2.3 + rot * f
				var a1 := 0.9 + rot * f
				InkTrail.auto_arc(pos, r, a1 if flip_v else a0, a0 if flip_v else a1, 0.09, p, f, n == "arc_heavy")


static func tex(n: String) -> Texture2D:
	## Kenney Particle Pack (CC0) dokuları: assets/fx/k_<ad>.png (64x64). v2: aynı boyda raporlanan mürekkep
	## karşılıkları (InkDraw.particle: fırça fiskesi kıvılcım, yıkama duman, fırça alev ...)
	return InkDraw.particle(n)


static func anim(n: String, pos: Vector2, rot := 0.0, scale_v := 1.0, col := Color(1, 1, 1), additive := true, flip_h := false, follow: Node2D = null) -> AnimFX:
	## PVFX Foundry (CC0) kare animasyonu oynat; bittiğinde kendini siler.
	if root == null or not AnimFX.has(n):
		return null
	if n == "rift_portal" and SusV2.on():
		return null  # v2: Kut Kapısı girdabını kendisi çizer (KutGate.gd, sus_v2 "kut_kapi_girdap")
	if INK_ANIM.has(n):
		# piksel darbe animasyonları yerine mürekkep. Oyuncunun taze savuruşunda kesik/sıçrantı zaten var.
		if not InkFX._near_player_swing(pos) and n != "crescent_slash":
			InkFX.hit(INK_ANIM[n], pos, Vector2.from_angle(rot) * (-1.0 if flip_h else 1.0), InkFX.pal_from_color(col), 1, clampf(scale_v * 1.4, 0.6, 2.0))
		return null
	if not AnimFX.meta_v2().has(n):
		# mürekkep karesi çizilmemiş eski animasyon kimliği: yerine büyü türü mürekkep sıçrantısı
		InkFX.hit("magic", pos, Vector2.from_angle(rot), InkFX.pal_from_color(col), 1, clampf(scale_v * 1.2, 0.6, 1.8))
		return null
	var a := AnimFX.new()
	a.setup(n, additive)
	a.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	if a.tex_k != 1.0:
		a.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	a.position = pos
	a.rotation = rot
	a.scale = Vector2(scale_v, scale_v) * a.tex_k
	a.modulate = col
	a.flip_h = flip_h
	if follow:
		a.follow = follow
		a.follow_off = pos - follow.global_position
	root.add_child(a)
	return a


static func number(pos: Vector2, value: float, crit := false, col := Color(1, 0.97, 0.9)) -> void:
	if root == null:
		return
	_ink_number(pos, value, crit, col)


## v27: aynı anda çıkan yazılar üst üste binmesin. Aynı metin 0,35 sn içinde yakında yeniden istenirse atlanır
## (iki düşmanın duruşu birlikte kırılınca tek "DURUŞ KIRILDI"); başka bir yazı aynı yere düşerse yukarı kaydırılır.
static var _son_yazilar: Array = []

static func text(pos: Vector2, s: String, col := Color(1, 1, 1), size := 9) -> void:
	if root == null:
		return
	var simdi := Time.get_ticks_msec()
	_son_yazilar = _son_yazilar.filter(func(r: Array) -> bool: return simdi - int(r[0]) < 350)
	for r in _son_yazilar:
		var rp: Vector2 = r[1]
		if String(r[2]) == s and absf(rp.x - pos.x) < 130.0 and absf(rp.y - pos.y) < 40.0:
			return
	for _i in 4:
		var cakisti := false
		for r in _son_yazilar:
			var rp2: Vector2 = r[1]
			if absf(rp2.x - pos.x) < 100.0 and absf(rp2.y - pos.y) < 13.0:
				cakisti = true
				break
		if not cakisti:
			break
		pos.y -= 14.0
	_son_yazilar.append([simdi, pos, s])
	var l := Label.new()
	l.text = s
	l.label_settings = _ink_ls_text(size, col, s)
	l.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	l.z_index = 100
	l.position = pos + Vector2(-60, -20)
	l.size = Vector2(120, 14)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	root.add_child(l)
	var tw := l.create_tween()
	tw.tween_property(l, "position:y", l.position.y - 14.0, 1.0)
	tw.parallel().tween_property(l, "modulate:a", 0.0, 0.4).set_delay(0.7)
	tw.tween_callback(l.queue_free)


## ---- v2 mürekkep yazıları: kalın fırça rakamlar (Kaushan Script), mürekkep dış çizgi ve fırça gölgesi;
## kritik: kızıl rakam + arkasında eğik kızıl mühür damgası (InkUI "seal").
static func _ink_ls_num(crit: bool, col: Color) -> LabelSettings:
	var key := "ink_n_%s_%s" % [str(crit), col.to_html()]
	if not _label_settings.has(key):
		var ls := LabelSettings.new()
		ls.font = InkUI.font("brush")
		ls.font_size = 14 if crit else 10   # v40: bir tık büyük fırça rakam (kritik 12 -> 14, sıradan 9 -> 10)
		ls.font_color = col
		ls.outline_size = 5 if crit else 3
		ls.outline_color = Color(InkUI.INK, 0.95)
		ls.shadow_color = Color(InkUI.INK, 0.6)
		ls.shadow_offset = Vector2(1.0, 1.2)
		ls.shadow_size = 2
		_label_settings[key] = ls
	return _label_settings[key]


static func _ink_ls_text(size: int, col: Color, s: String) -> LabelSettings:
	var caps := InkUI.is_caps(s)
	var key := "ink_t_%d_%s_%s" % [size, col.to_html(), str(caps)]
	if not _label_settings.has(key):
		var ls := LabelSettings.new()
		ls.font = InkUI.font("caps" if caps else "bold")
		ls.font_size = int(round(size * (0.8 if caps else 0.95)))
		ls.font_color = col
		ls.outline_size = 3
		ls.outline_color = Color(InkUI.INK, 0.92)
		ls.shadow_color = Color(InkUI.INK, 0.55)
		ls.shadow_offset = Vector2(1.2, 1.5)
		ls.shadow_size = 2
		_label_settings[key] = ls
	return _label_settings[key]


static func _ink_number(pos: Vector2, value: float, crit: bool, col: Color) -> void:
	# v22: aynı düşmanın üstünde (24 px) doğuşundan 0,3 sn içinde çıkan kritik olmayan sayılar tek sayıda toplanır (hızlı kombolarda
	# üst üste binen sayı yığını düşmanı örtüyordu); toplanan sayı küçük bir sıçrayışla güncellenir
	var now := Time.get_ticks_msec() / 1000.0
	if not crit:
		for i in range(_nums.size() - 1, -1, -1):
			var r: Array = _nums[i]
			if not is_instance_valid(r[0]) or now - float(r[3]) > 0.3:
				_nums.remove_at(i)
				continue
			if (r[4] as Vector2).distance_to(pos) < 24.0:
				r[2] = float(r[2]) + value
				(r[1] as Label).text = str(int(maxf(1.0, roundf(float(r[2])))))
				var nn: Node2D = r[0]
				nn.scale = Vector2.ONE * 1.12
				var tw2 := nn.create_tween()
				tw2.tween_property(nn, "scale", Vector2.ONE, 0.08)
				return
	# v31 çok hedef: aynı anda çıkan sayılar (yan yana düşmanlar, kritik + sıradan) üst üste binmez — doğuş yeri
	# canlı bir sayıya çok yakınsa yukarı ve dönüşümlü yana kaydırılır (en çok 4 basamak)
	var np := pos + Vector2(randf_range(-6, 6), -14)
	for i in range(_num_yer.size() - 1, -1, -1):
		var q: Array = _num_yer[i]
		if not is_instance_valid(q[0]) or now - float(q[1]) > 0.45:
			_num_yer.remove_at(i)
	for k in 4:
		var hit := false
		for q in _num_yer:
			var qp: Vector2 = q[2]
			if absf(qp.x - np.x) < (22.0 if crit else 18.0) and absf(qp.y - np.y) < 11.0:
				hit = true
				break
		if not hit:
			break
		np += Vector2(5.0 if k % 2 == 0 else -5.0, -12.0)
	var n := Node2D.new()
	n.z_index = 100
	n.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	n.position = np
	_num_yer.append([n, now, np])
	if crit:
		# kritik: arkada mürekkep sıçrantısı, sağ üstte eğik kızıl mühür damgası
		var sp := Sprite2D.new()
		sp.texture = InkUI.tex("splat")
		sp.modulate = Color(InkUI.INK, 0.78)
		sp.rotation = randf() * TAU
		sp.scale = Vector2.ONE * (34.0 / 512.0)
		n.add_child(sp)
		var s := Sprite2D.new()
		s.texture = InkUI.tex("seal")
		s.modulate = Color(InkUI.SEAL, 0.95)
		s.rotation = randf_range(-0.4, -0.15)
		s.scale = Vector2.ONE * (9.0 / 160.0)
		s.position = Vector2(11, -7)
		n.add_child(s)
	var l := Label.new()
	l.text = str(int(maxf(1.0, roundf(value))))
	l.label_settings = _ink_ls_num(crit, Color(1.0, 0.24, 0.16) if crit else col)
	l.size = Vector2(60, 20)
	l.position = Vector2(-30, -11)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	n.add_child(l)
	root.add_child(n)
	if not crit:
		_nums.append([n, l, value, now, pos])
		if in_hit and hit_k < 0.99:
			n.modulate.a = 0.85
			l.pivot_offset = l.size * 0.5
			l.scale = Vector2.ONE * 0.85
	var tw := n.create_tween()
	tw.set_parallel(true)
	# v40 hareket: mürekkep "damlar" gibi — büyükten yerine oturur (kritikte geri tepmeli), hafif eğik yaylanıp dikleşir,
	# yükselirken yavaşlar, sonda küçülerek solar
	n.scale = Vector2.ONE * (1.9 if crit else 1.25)
	n.rotation = randf_range(-0.2, 0.2) if crit else randf_range(-0.06, 0.06)
	tw.tween_property(n, "scale", Vector2.ONE, 0.22 if crit else 0.13).set_trans(Tween.TRANS_BACK if crit else Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tw.tween_property(n, "rotation", 0.0, 0.3 if crit else 0.2).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	# v22: sayılar daha kısa yaşar (sıradan 0,75 → 0,55 sn): hızlı kombolarda yığılmasın
	tw.tween_property(n, "position:y", n.position.y - (26.0 if crit else 16.0), 0.75 if crit else 0.55).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tw.tween_property(n, "modulate:a", 0.0, 0.3 if crit else 0.2).set_delay(0.55 if crit else 0.35)
	tw.tween_property(n, "scale", Vector2.ONE * 0.8, 0.3 if crit else 0.2).set_delay(0.55 if crit else 0.35)
	tw.chain().tween_callback(n.queue_free)


static func dot_tex() -> Texture2D:
	return InkDraw.particle("soft_dot")  # v2: 16x16 piksel nokta yerine yumuşak fırça dokunuşu


static func _particles(pos: Vector2, col: Color, amount: int, life: float, additive: bool, z := 60, texture_name := "") -> CPUParticles2D:
	var p := CPUParticles2D.new()
	p.position = pos
	p.one_shot = true
	p.explosiveness = 0.95
	p.amount = amount
	p.lifetime = life
	p.texture = dot_tex() if texture_name == "" else tex(texture_name)
	p.color = col
	var g := Gradient.new()
	g.set_color(0, Color(1, 1, 1, 1))
	g.set_color(1, Color(1, 1, 1, 0))
	p.color_ramp = g
	p.z_index = z
	p.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS  # v2: mürekkep dokusu, küçültmede mipmap
	var m := CanvasItemMaterial.new()
	m.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	if additive:
		m.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	p.material = m
	root.add_child(p)
	p.emitting = true
	p.finished.connect(p.queue_free)
	return p


static func burst(pos: Vector2, col: Color, amount := 12, speed := 90.0, life := 0.5, scale_size := 0.25, gravity := 300.0, additive := false) -> void:
	if root == null:
		return
	var p := _particles(pos, col, Ayarlar.efekt_say(amount, 2), life, additive)  # v38: efekt yoğunluğu (sayı)
	p.direction = Vector2.UP
	p.spread = 180.0
	p.initial_velocity_min = speed * 0.4
	p.initial_velocity_max = speed
	p.gravity = Vector2(0, gravity)
	p.scale_amount_min = scale_size * 0.5
	p.scale_amount_max = scale_size


static func sparks(pos: Vector2, dir: Vector2, col: Color, amount := 8, speed := 200.0) -> void:
	## Metal kıvılcımı: darbe yönünde dar koni, hızlı, yerçekimiyle düşer, kısa ömür.
	if root == null:
		return
	var p := _particles(pos, col, Ayarlar.efekt_say(amount, 3), 0.32, true, 60, "k_spark")  # v38: efekt yoğunluğu
	p.direction = dir.normalized() if dir.length() > 0.01 else Vector2.UP
	p.spread = 38.0
	p.initial_velocity_min = speed * 0.45
	p.initial_velocity_max = speed
	p.gravity = Vector2(0, 520)
	p.damping_min = 60.0
	p.damping_max = 140.0
	p.particle_flag_align_y = true  # çizgi doku hız yönüne döner: kıvılcım çizgileri
	p.scale_amount_min = 0.14
	p.scale_amount_max = 0.3
	# yıldız parıltıları: bir iki tane, daha büyük
	var q := _particles(pos, Color(1.0, 1.0, 0.9), 2, 0.25, true, 61, "k_star")
	q.direction = dir.normalized() if dir.length() > 0.01 else Vector2.UP
	q.spread = 60.0
	q.initial_velocity_min = 20.0
	q.initial_velocity_max = 70.0
	q.scale_amount_min = 0.25
	q.scale_amount_max = 0.45
	q.angular_velocity_min = -300.0
	q.angular_velocity_max = 300.0


static func blood(pos: Vector2, dir: Vector2, col: Color, amount := 10) -> void:
	## Düşmana özgü renkte sıçrantı. v13: damlalar gerçek kan sistemine gider (yere/duvara yapışır, süzülür);
	## burada yalnızca ince, hızla sönen bir çekirdek sıçrama kalır.
	if root == null:
		return
	Blood.spray(pos, dir, col, amount * 2)
	amount = maxi(2, amount / 3)
	var p := _particles(pos, col, amount, 0.55, false, 45)
	p.direction = (dir.normalized() + Vector2(0, -0.5)).normalized() if dir.length() > 0.01 else Vector2.UP
	p.spread = 55.0
	p.initial_velocity_min = 60.0
	p.initial_velocity_max = 190.0
	p.gravity = Vector2(0, 700)
	p.scale_amount_min = 0.14
	p.scale_amount_max = 0.34
	# v2: hız yönünde uzayan mürekkep damlaları
	p.texture = InkDraw.particle("damla")
	p.particle_flag_align_y = true


static func dust(pos: Vector2, dir: Vector2, amount := 5, size := 0.32, col := Color(0.62, 0.58, 0.6, 0.55)) -> void:
	## Toz: yavaş, yukarı süzülen, büyüyerek solan soluk bulut. Varsayılan renk biyomun zemin tozudur.
	if root == null:
		return
	if col == Color(0.62, 0.58, 0.6, 0.55):
		col = dust_col
	var p := _particles(pos, col, amount, 0.55, false, 30, "k_smoke2")
	p.direction = dir.normalized() if dir.length() > 0.01 else Vector2.UP
	p.spread = 50.0
	p.initial_velocity_min = 18.0
	p.initial_velocity_max = 55.0
	p.gravity = Vector2(0, -22)
	p.damping_min = 40.0
	p.damping_max = 80.0
	p.angular_velocity_min = -90.0
	p.angular_velocity_max = 90.0
	p.scale_amount_min = size * 1.2
	p.scale_amount_max = size * 2.0
	var sc := Curve.new()
	sc.add_point(Vector2(0, 0.5))
	sc.add_point(Vector2(0.4, 1.0))
	sc.add_point(Vector2(1, 1.3))
	p.scale_amount_curve = sc


static func soul(pos: Vector2, col: Color, amount := 24) -> void:
	## Ruh zerreleri: yavaşça göğe yükselir, uzun yaşar, toplamalı parlar.
	if root == null:
		return
	var p := _particles(pos, col, amount, 1.1, true, 60, "k_star2")
	p.direction = Vector2.UP
	p.spread = 40.0
	p.initial_velocity_min = 25.0
	p.initial_velocity_max = 90.0
	p.gravity = Vector2(0, -90)
	p.damping_min = 20.0
	p.damping_max = 40.0
	p.angular_velocity_min = -120.0
	p.angular_velocity_max = 120.0
	p.scale_amount_min = 0.12
	p.scale_amount_max = 0.3
	p.emission_shape = CPUParticles2D.EMISSION_SHAPE_SPHERE
	p.emission_sphere_radius = 9.0


static func fire(pos: Vector2, amount := 6, size := 0.35, spread_px := 6.0) -> void:
	## Alev: yükselen alev dilleri, turuncudan kızıla solar.
	if root == null:
		return
	var p := _particles(pos, Color(1.0, 0.75, 0.35), amount, 0.5, true, 62, "k_flame")
	p.direction = Vector2.UP
	p.spread = 25.0
	p.initial_velocity_min = 30.0
	p.initial_velocity_max = 80.0
	p.gravity = Vector2(0, -140)
	p.emission_shape = CPUParticles2D.EMISSION_SHAPE_SPHERE
	p.emission_sphere_radius = spread_px
	p.scale_amount_min = size * 0.6
	p.scale_amount_max = size * 1.1
	var sc := Curve.new()
	sc.add_point(Vector2(0, 0.6))
	sc.add_point(Vector2(0.3, 1.0))
	sc.add_point(Vector2(1, 0.15))
	p.scale_amount_curve = sc
	var g := Gradient.new()
	g.set_color(0, Color(1.0, 0.98, 0.75, 1.0))
	g.add_point(0.3, Color(1.0, 0.6, 0.15, 0.95))
	g.add_point(0.7, Color(0.9, 0.2, 0.05, 0.6))
	g.set_color(1, Color(0.25, 0.03, 0.03, 0.0))
	p.color_ramp = g
	# kor zerreleri: yükselirken savrulur, uzun ömürlü
	var e := _particles(pos, Color(1.0, 0.7, 0.3), maxi(2, amount / 2), 0.9, true, 63, "k_spark")
	e.direction = Vector2.UP
	e.spread = 50.0
	e.initial_velocity_min = 40.0
	e.initial_velocity_max = 120.0
	e.gravity = Vector2(0, -60)
	e.scale_amount_min = 0.08
	e.scale_amount_max = 0.16
	e.emission_shape = CPUParticles2D.EMISSION_SHAPE_SPHERE
	e.emission_sphere_radius = spread_px
	var g2 := Gradient.new()
	g2.set_color(0, Color(1.0, 0.95, 0.7, 1.0))
	g2.add_point(0.5, Color(1.0, 0.5, 0.15, 0.9))
	g2.set_color(1, Color(0.6, 0.1, 0.05, 0.0))
	e.color_ramp = g2
	if amount >= 6:
		flash_light(pos, Color(1.0, 0.55, 0.2), 60.0 + spread_px * 4.0, 0.9, 0.25)


static func bubbles(pos: Vector2, amount := 3, col := Color(0.5, 1.0, 0.3)) -> void:
	## Zehir kabarcıkları: yükselen, salınan, patlayarak sönen halkalar
	if root == null:
		return
	var p := _particles(pos, col, amount, 0.9, true, 61, "k_ring")
	p.direction = Vector2.UP
	p.spread = 30.0
	p.initial_velocity_min = 12.0
	p.initial_velocity_max = 30.0
	p.gravity = Vector2(0, -25)
	p.emission_shape = CPUParticles2D.EMISSION_SHAPE_SPHERE
	p.emission_sphere_radius = 7.0
	p.scale_amount_min = 0.06
	p.scale_amount_max = 0.14
	var sc := Curve.new()
	sc.add_point(Vector2(0, 0.6))
	sc.add_point(Vector2(0.8, 1.2))
	sc.add_point(Vector2(1, 1.6))
	p.scale_amount_curve = sc


static func frost(pos: Vector2, amount := 3) -> void:
	## Ayaz: dönerek düşen buz parıltıları
	if root == null:
		return
	var p := _particles(pos, Color(0.75, 0.93, 1.0), amount, 0.7, true, 61, "k_star")
	p.direction = Vector2.DOWN
	p.spread = 60.0
	p.initial_velocity_min = 8.0
	p.initial_velocity_max = 26.0
	p.gravity = Vector2(0, 40)
	p.emission_shape = CPUParticles2D.EMISSION_SHAPE_SPHERE
	p.emission_sphere_radius = 9.0
	p.angular_velocity_min = -200.0
	p.angular_velocity_max = 200.0
	p.scale_amount_min = 0.1
	p.scale_amount_max = 0.2


static func smoke(pos: Vector2, amount := 5, size := 0.5, col := Color(0.3, 0.28, 0.32, 0.7)) -> void:
	## Duman: yavaş yükselir, döner, büyüyerek dağılır.
	if root == null:
		return
	var p := _particles(pos, col, Ayarlar.efekt_say(amount, 2), 1.1, false, 44, "k_smoke")  # v38: efekt yoğunluğu
	p.direction = Vector2.UP
	p.spread = 40.0
	p.initial_velocity_min = 15.0
	p.initial_velocity_max = 45.0
	p.gravity = Vector2(0, -35)
	p.angular_velocity_min = -60.0
	p.angular_velocity_max = 60.0
	p.scale_amount_min = size * 0.7
	p.scale_amount_max = size * 1.4
	var sc := Curve.new()
	sc.add_point(Vector2(0, 0.4))
	sc.add_point(Vector2(1, 1.6))
	p.scale_amount_curve = sc


static func slash_sprite(n: String, pos: Vector2, rot := 0.0, scale_v := Vector2.ONE, col := Color(1, 1, 1), flip_v := false, pivot := Vector2(-1, -1), follow: Node2D = null, fps := 26.0) -> SlashFX:
	## Prosedürel kesik sprite'ı (arc / arc_thin / arc_heavy / arc_short / line / ring / x / impact_*).
	if root == null or not SlashFX.has(n):
		return null
	_ink_slash_sprite(n, pos, rot, scale_v, col, flip_v)
	return null


static func impact_sprite(kind: String, pos: Vector2, dir: Vector2, col: Color, size := 1.0) -> void:
	## Silah sınıfına göre darbe sprite'ı: cut (kılıç), blunt (çekiç), pierce (mızrak), magic (ruh/büyü)
	InkFX.hit(kind, pos, dir, InkFX.pal_from_color(col), 2 if size >= 1.25 else 1, clampf(size, 0.6, 1.8))


static func decal(n: String, pos: Vector2, rot := 0.0, life := 9.0, scale_v := 1.0, col := Color(1, 1, 1)) -> void:
	## Yere yapışan kalıcı iz (kan sıçrantısı, çatlak): süre sonunda solar.
	if level == null or not SlashFX.has(n) or level.get("decal_root") == null:
		return
	var s: Sprite2D
	# v2: piksel çıkartma yerine yere yatık mürekkep sıçrantısı / dallanan fırça çatlağı (assets/fx/ink_p)
	var crack := n.begins_with("decal_crack")
	var i := int(n.right(1))
	s = Sprite2D.new()
	s.texture = InkDraw.tex(("catlak_%d" % (i % 2)) if crack else ("kan_%d" % (i % 3)))
	InkDraw.prep(s)
	var m := CanvasItemMaterial.new()
	m.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	s.material = m
	var ks := Vector2(64.0 / 256.0, 20.0 / 64.0) * 1.1 if crack else Vector2(40.0 / 128.0, 16.0 / 128.0) * 1.35
	s.scale = Vector2(ks.x * scale_v * (1.0 if randf() < 0.5 else -1.0), ks.y * scale_v)
	s.modulate = Color(0.07, 0.05, 0.07, 0.8) if crack and col == Color(1, 1, 1) else col
	s.rotation = rot
	s.position = pos
	s.z_index = 1
	level.decal_root.add_child(s)
	var tw := s.create_tween()
	tw.tween_interval(life * 0.75)
	tw.tween_property(s, "modulate:a", 0.0, life * 0.25)
	tw.tween_callback(s.queue_free)
	# en çok 60 çıkartma: en eskisini sil
	if level.decal_root.get_child_count() > 60:
		level.decal_root.get_child(0).queue_free()


static func impact(pos: Vector2, dir: Vector2, col: Color, size := 1.0) -> void:
	if root == null:
		return
	InkFX.hit("spark", pos, dir, InkFX.pal_from_color(col), 0 if size < 1.2 else 1, clampf(size, 0.5, 1.6))


static func ghost(src: Sprite2D, col: Color, life := 0.25, z := 1) -> void:
	## Sprite'ın anlık kopyası: aynı doku/bölge/yön, ışıksız, solarak kaybolur.
	if root == null or src == null or src.texture == null:
		return
	# v22: aynı sprite'tan kısa süre içinde ikinci hayalet yok (toplamalı hayaletler üst üste binip bembeyaz siluet
	# oluyordu: geri itilen / havaya atılan düşman her 3 karede bir hayalet bırakıyor, vuruş donmasında da birikiyordu).
	# Oyuncu 40 ms, düşman 120 ms; mürekkep stilinde hayalet daha soluk (oyuncu ×0,6, düşman ×0,4).
	var host: Node = src.get_parent().get_parent() if src.get_parent() != null else null
	var is_pl := host is Player
	var gid := src.get_instance_id()
	var gnow := Time.get_ticks_msec() / 1000.0
	if gnow - float(_ghost_t.get(gid, -9.0)) < (0.04 if is_pl else 0.12):
		return
	_ghost_t[gid] = gnow
	if _ghost_t.size() > 64:
		_ghost_t.clear()
	col.a *= 0.6 if is_pl else 0.4
	var g := Sprite2D.new()
	g.texture = src.texture
	g.region_enabled = src.region_enabled
	g.region_rect = src.region_rect
	g.centered = src.centered
	g.flip_h = src.flip_h
	g.offset = src.offset
	g.global_transform = src.global_transform
	g.z_index = z
	var m := CanvasItemMaterial.new()
	m.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	m.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	g.material = m
	g.modulate = col
	root.add_child(g)
	var tw := g.create_tween()
	tw.tween_property(g, "modulate:a", 0.0, life)
	tw.tween_callback(g.queue_free)
	# Bengü'nün fizikli saçı sprite'ta yok: hayaletin saçı aynı anın donmuş saç çizimiyle eklenir
	var sac := BenguSac.bul(src)
	if sac:
		sac.hayalet(col, life, z)


static func trail(col: Color, width := 1.0) -> WeaponTrail:
	if root == null:
		return null
	var it := InkTrail.acquire(root)
	it.col = col
	it.width_mul = width
	return it


static func corpse(src: Sprite2D, vel: Vector2, col: Color) -> void:
	if root == null or src == null or src.texture == null:
		return
	var c := Corpse.new()
	c.setup(src, vel, col)
	root.add_child(c)


static func flash_light(pos: Vector2, col: Color, radius: float, energy := 1.5, life := 0.18) -> void:
	if level == null or not level.has_method("add_light"):
		return
	var l: PointLight2D = level.add_light(pos, col, radius, energy, root)
	var tw := l.create_tween()
	tw.tween_property(l, "energy", 0.0, life)
	tw.tween_callback(l.queue_free)


static func shock_line(pos: Vector2, half_w: float, col := Color(0.6, 0.55, 0.5, 0.6)) -> void:
	## Yere vuruş: iki yana yayılan toz hattı + ilerleyen taş parçaları.
	if root == null:
		return
	for side in [-1, 1]:
		var p := _particles(pos, col, 10, 0.45, false, 30)
		p.direction = Vector2(side, -0.35)
		p.spread = 18.0
		p.initial_velocity_min = half_w * 1.6
		p.initial_velocity_max = half_w * 2.6
		p.gravity = Vector2(0, 160)
		p.scale_amount_min = 0.2
		p.scale_amount_max = 0.4
		var q := _particles(pos, Color(0.5, 0.48, 0.52), 6, 0.5, false, 46, "k_dirt")  # kül pulu
		q.direction = Vector2(side, -1.0)
		q.spread = 30.0
		q.initial_velocity_min = 90.0
		q.initial_velocity_max = 200.0
		q.gravity = Vector2(0, 700)
		q.scale_amount_min = 0.12
		q.scale_amount_max = 0.22


static func slash(pos: Vector2, facing: int, a0: float, a1: float, radius: float, width: float, col: Color, life := 0.14) -> void:
	if root == null:
		return
	InkTrail.auto_arc(pos, radius, a0, a1, life * 0.6, InkFX.pal_from_color(col), facing, width > 9.0)


static func ring(pos: Vector2, radius: float, col: Color, life := 0.3, aspect := 1.0) -> void:
	## aspect < 1: yere yatık (perspektifli) halka; yer şoklarında kullanılır.
	if root == null:
		return
	InkFX.ring(pos, radius, InkFX.pal_from_color(col), life, aspect)


static func streak(a: Vector2, b: Vector2, col := Color(1, 0.95, 0.8), life := 0.12) -> void:
	## Hız çizgisi: a'dan b'ye incelen, hızla solan parlak çizgi (saplama, ok, atılma)
	if root == null:
		return
	# v22: düşmanın büyük vuruştaki darbe çizgileri (5 ışın) seyreldi; hızlı ardışık vuruşta hiç yok
	if in_hit and (hit_k < 0.99 or randf() < 0.6):
		return
	var s := StreakFX.new()
	s.a = a
	s.b = b
	s.col = col
	s.life = life
	root.add_child(s)


static func lightning(a: Vector2, b: Vector2, col := Color(0.7, 0.85, 1.0)) -> void:
	## Kırık çizgili şimşek: iki nokta arasında zikzak, hızla söner.
	if root == null:
		return
	var l := LightningFX.new()
	l.a = a
	l.b = b
	l.col = col
	root.add_child(l)


static func pop(node: Node2D, from: Vector2, dur := 0.18) -> void:
	## Squash & stretch: ölçeği 'from' değerinden (1,1)'e esneterek getirir.
	if node == null:
		return
	node.scale = from
	var tw := node.create_tween()
	tw.tween_property(node, "scale", Vector2(1, 1), dur).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)


# ------------------------------------------------------------------ v14: aşamalı piksel VFX (patlama / şok dalgası / gök gürlemesi)
static var _screen_layer: CanvasLayer


static func screen_layer() -> CanvasLayer:
	## Ekran uzayı efekt katmanı (kırılma halkası, tam ekran flaş). Vinyet (5) ve darbe karesinin (6) altında,
	## dünyanın üstünde. Ağaç köküne bir kez eklenir; bölüm değişse de kalır.
	if _screen_layer != null and is_instance_valid(_screen_layer) and _screen_layer.is_inside_tree():
		return _screen_layer
	if root == null or not root.is_inside_tree():
		return null
	var cl := CanvasLayer.new()
	cl.layer = 4
	root.get_tree().root.add_child(cl)
	_screen_layer = cl
	return cl


static func screen_flash(a := 0.8, frames := 1, col := Color(1.0, 0.98, 0.94)) -> void:
	## Tam ekran düz renk, tam olarak `frames` kare (gerçek zaman; vuruş duraklamasından etkilenmez).
	var cl := screen_layer()
	if cl == null:
		return
	var r := ColorRect.new()
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	r.color = Color(col.r, col.g, col.b, a * (0.4 + 0.6 * Game.fx_scale))  # Ayarlar > Sarsıntı ve flaş
	cl.add_child(r)
	# CanvasLayer altındaki kök Control çapayla boyutlanmaz: görünür dikdörtgene elle oturt
	r.position = Vector2.ZERO
	r.size = cl.get_viewport().get_visible_rect().size
	cl.get_tree().create_timer(float(frames) / 60.0 - 0.002, true, false, true).timeout.connect(r.queue_free)


static func explosion(pos: Vector2, radius: float, col_hot := Color(1.0, 0.85, 0.3), big := false, away := Vector2.UP, juice := true) -> ExplosionFX:
	## Aşamalı piksel patlama: flaş → ateş topu → duman + parçalar + yer dalgası (ExplosionFX).
	## radius: dünya pikseli (bomba 40). big: ikinci iç patlama + ekran kırılma halkası. away: patlamadan
	## oyuncuya doğru yön (sarsıntı ekseni). juice=false: yalnız görsel (kamera / ses / ışık yok).
	if root == null:
		return null
	var e := ExplosionFX.new()
	e.position = pos
	e.radius = radius
	e.col_hot = col_hot
	e.big = big or radius >= 50.0
	e.away = away
	e.juice = juice
	root.add_child(e)
	return e


static func shockwave(pos: Vector2, radius: float, strength := 1.0) -> void:
	## Ekran uzayı kırılma halkası (shaders/shockwave.gdshader): 0 → radius ~0,35 s'de ease-out ile
	## genişler; strength 1 = en çok 3 mantıksal px (1080p'de 6 ekran px) kayma. Patlama, yer çarpması, gürleme.
	var cl := screen_layer()
	if cl == null:
		return
	if Game.fx_scale <= 0.0:
		return
	var s := ShockwaveFX.new()
	s.world_pos = pos
	s.max_r = radius
	s.strength = 3.0 * strength
	s.thickness = 6.0 + 4.0 * clampf(strength, 0.0, 1.5)
	s.life = 0.35
	cl.add_child(s)


static func ground_slam(pos: Vector2, facing := 1, power := 1.0, col := Color(1.0, 0.85, 0.6), metal := true, fire := false, juice := true) -> GroundSlamFX:
	## v16 yer çarpması (GroundSlamFX): pos = temas noktası, zemin yüzeyinde (karonun üst satırı). Baştaki 2 karelik
	## yerel flaş → zemini izleyen şok cephesi + iki yana toz → biyom renginde moloz (sekme) → çatlak çıkartması;
	## metalde kıvılcım, od silahında kor. power: 0,6 kılıç · 1 ağır · 1,5 tam şarj / bitiriş · 2 boss.
	## juice: kısa aşağı yönlü sarsıntı + itiş + titreşim + yerel ışık (ses çağırana aittir).
	if root == null:
		return null
	# v20: silah mürekkebi sıçrantısı küçültüldü; yer çarpmasının asıl görseli toz (GroundSlamFX -> InkDust)
	InkFX.slam(pos, facing, power * 0.5, InkFX.pal_from_color(col) if col.s >= 0.45 else InkFX.player_pal)
	var g := GroundSlamFX.new()
	g.position = pos
	g.facing = 1 if facing >= 0 else -1
	g.power = power
	g.col = col
	g.metal = metal
	g.fire = fire
	g.juice = juice
	root.add_child(g)
	return g


static func thunder(pos: Vector2, strength := 1.0, col := Color(0.72, 0.86, 1.0)) -> void:
	## Gök gürlemesi: ön kıvılcım → 1 kare beyaz ekran + gökten inen şimşek + yer flaşı → ~90 ms sonra
	## sarsıntı / titreşim / gürleme sesi (ThunderFX). strength 0,6 hafif, 1 Gök Asası, 1,5 patron.
	if root == null:
		return
	var t := ThunderFX.new()
	t.position = pos
	t.strength = strength
	t.col = col
	root.add_child(t)
