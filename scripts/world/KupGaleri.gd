class_name KupGaleri
extends Node2D
## v44 Ata Kurganı / Silah Küpleri: yurdun girişinde (Bengü'nün uyandığı yerin arkasında) karaçam kütüklü kurgan duvarı;
## rafta her silah / kalkan için bir cam küp (Kupler.liste, 14 sütun x 4 raf). Silah küpün arka ve ön camı arasında süzülür
## (weapons_v2 atlası, sığacak boyda; uzun silahlar dik). Duruma göre:
##   kilitli  : kara gölge, bulanık sıvı, çatlak mühür        parsomen: soluk mavi biçim, küpe bağlı parşömen
##   acik     : renkli silah, Kut ışığı, yavaş süzülme        yeni    : kıvılcım + YENİ (kartı görülene dek)
## Yanından geçerken en yakın küpün kartı (HUD._draw_card) çıkar; W: küpleri gez (oyun durur, imleç ok tuşlarıyla),
## açık küpte Boşluk / Enter / J: başlangıç silahı (Kupler.sec; yurtta seçilen silah hemen kuşanılır), Esc / L: çık
## (W gezerken yukarı oktur).
## Demirci'nin açtığı ya da koşuda ilk kez kuşanılan silahın küpü, yurtta ilk görüldüğünde uyanır (mühür kırılır, silah
## karanlıktan renge döner, Kut halkası).
## Yerleşim sabitleri tools/artgen/kup_ink.py ile aynı (SUTUN, ARALIK, X0, RAF_Y).

const SUTUN := 14
const ARALIK := 26.5
const X0 := 14.0
const RAF_Y := [-144.0, -98.0, -52.0, -6.0]
const GEN := 400.0
## silahın küp içindeki kutusu (küp tabanına göre; tür a / b / c)
const KUTU := {"a": [Vector2(0, -14.5), Vector2(15.0, 20.0)], "b": [Vector2(0, -14.0), Vector2(19.0, 19.0)], "c": [Vector2(0, -16.0), Vector2(10.0, 26.0)]}
const KUT_RENK := Color(0.45, 1.0, 0.95)
const ALTIN_RENK := Color(1.0, 0.82, 0.42)

var level: Node
var kupler: Array = []        # [{id, i, pos, tur, kok, arka, silah, on, muhur, etiket, halo, durum, taban_y, uyan_t}]
var secili := -1              # gezme imleci / yürürken vurgulanan küp
var gez := false              # gezme kipi (HUD "kupler")
var yakin := false            # oyuncu duvarın önünde
var _satir := 3
var _t := 0.0
var _kart_t := 0.0
var _baslik: Label
var _sayac: Label
var _isaret: Node2D
var _yeni_ls: LabelSettings
var _uyanacak: Array = []
var _sayi := 0
var _altin := false
var _halo_tex: GradientTexture2D
var _kart_cache: Dictionary = {}
var kart_kapali := false      # çekim: kartı gösterme (duvarın tamamı)


func kur(lv: Node, x_sol: float, zemin_y: float) -> void:
	level = lv
	position = Vector2(x_sol, zemin_y)
	z_index = -7
	process_mode = Node.PROCESS_MODE_ALWAYS
	_sayi = Kupler.acilan()
	_altin = Kupler.esik_var("altin_isik")
	var mat := _env_mat()
	var dv: Dictionary = lv._decor_v2("kup_duvar")
	if not dv.is_empty():
		var s := _sprite(dv, Vector2.ZERO, mat)
		add_child(s)
	_halo_tex = GradientTexture2D.new()
	_halo_tex.width = 64
	_halo_tex.height = 64
	_halo_tex.fill = GradientTexture2D.FILL_RADIAL
	_halo_tex.fill_from = Vector2(0.5, 0.5)
	_halo_tex.fill_to = Vector2(1.0, 0.5)
	var gr := Gradient.new()
	gr.set_color(0, Color(1, 1, 1, 0.85))
	gr.set_color(1, Color(1, 1, 1, 0.0))
	gr.add_point(0.45, Color(1, 1, 1, 0.3))
	_halo_tex.gradient = gr
	var ids: Array = Kupler.liste()
	for i in ids.size():
		_kup_kur(String(ids[i]), i, mat)
	# baş tahtası yazısı (kurgan adı + sayaç)
	_baslik = _etiket("ATA KURGANI · SİLAH KÜPLERİ", 9, Color(1.0, 0.86, 0.5), true)
	_baslik.position = Vector2(GEN / 2.0 - 100.0, -205.0)
	_baslik.size = Vector2(200, 14)
	add_child(_baslik)
	_sayac = _etiket("", 8, Color(0.75, 1.0, 0.96), false)
	_sayac.position = Vector2(GEN / 2.0 - 100.0, -195.0)
	_sayac.size = Vector2(200, 12)
	add_child(_sayac)
	_sayac_yaz()
	# yer işaretleri / imleç (tek düğüm, _draw)
	_isaret = Node2D.new()
	_isaret.z_index = 3
	_isaret.draw.connect(_isaret_ciz)
	add_child(_isaret)
	# Kut ışıkları: duvar boyunca üç yumuşak firuze ışık (her küp için ayrı ışık yerine; altın eşikte sıcak)
	var lc := ALTIN_RENK if _altin else Color(0.5, 1.0, 0.95)
	for k in 3:
		lv.add_light(position + Vector2(GEN * (0.2 + 0.3 * k), -90.0), lc, 190.0, 0.55, lv.decor_root)
	# uyanacak küpler (yeni, henüz uyanmamış): biri görünene dek eski hâlinde bekler
	for k in kupler:
		if Kupler.yeni_mi(k["id"]) and not Kupler.uyandi_mi(k["id"]):
			_uyanacak.append(k)
			_hal(k, "uyku")


func _env_mat() -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = load("res://shaders/env_ink.gdshader")
	m.set_shader_parameter("moon_gain", float(level.art.get("ground_moon_gain", 0.6)))
	var dt: Array = level.art.get("decor_tint", [1.0, 1.0, 1.0])
	m.set_shader_parameter("tint", Color(dt[0], dt[1], dt[2]))
	return m


func _sprite(d: Dictionary, pos: Vector2, mat: Material) -> Sprite2D:
	var k := 1.0 / float(d.get("texel", 4.0))
	var s := Sprite2D.new()
	s.texture = d["tex"]
	s.centered = false
	s.offset = Vector2(-float(d["origin"][0]), -float(d["origin"][1]))
	s.scale = Vector2(k, k)
	s.position = pos
	s.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	if mat:
		s.material = mat
	return s


func _etiket(txt: String, size: int, col: Color, caps: bool) -> Label:
	var l := Label.new()
	l.text = txt
	var ls := LabelSettings.new()
	ls.font = InkUI.font("caps" if caps else "bold")
	ls.font_size = size
	ls.font_color = col
	ls.outline_size = 3
	ls.outline_color = Color(InkUI.INK, 0.92)
	l.label_settings = ls
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	return l


func kup_konum(i: int) -> Vector2:
	var c := i % SUTUN
	var r := i / SUTUN
	return Vector2(X0 + ARALIK * (c + 0.5), RAF_Y[r] - 1.2)


func _kup_kur(id: String, i: int, mat: Material) -> void:
	var tr := Kupler.tur(id)
	var k := {"id": id, "i": i, "tur": tr, "pos": kup_konum(i), "uyan_t": -1.0}
	var kok := Node2D.new()
	kok.position = k["pos"]
	add_child(kok)
	k["kok"] = kok
	var arka: Dictionary = level._decor_v2("kup_%s_arka" % tr)
	var on: Dictionary = level._decor_v2("kup_%s_on" % tr)
	var bx: Array = KUTU[tr]
	# arkadaki Kut ışıması (toplamalı, açık küpte)
	var halo := Sprite2D.new()
	halo.texture = _halo_tex
	halo.scale = Vector2(0.62, 0.78) if tr != "c" else Vector2(0.48, 0.84)
	halo.position = bx[0]
	var hm := CanvasItemMaterial.new()
	hm.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	hm.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	halo.material = hm
	k["halo"] = halo
	if not arka.is_empty():
		var a := _sprite(arka, Vector2.ZERO, mat)
		kok.add_child(a)
		k["arka"] = a
		if arka.get("glow_tex") != null:
			var g := Sprite2D.new()
			g.texture = arka["glow_tex"]
			g.centered = false
			g.offset = a.offset
			g.material = hm
			a.add_child(g)
			k["arka_isik"] = g
	kok.add_child(halo)
	# silah: atlas bölgesi, kutuya sığacak boyda; yatay silahlar dik (ucu yukarı), hafif eğik
	var sil := Sprite2D.new()
	sil.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	if id == Kupler.RASTGELE:
		sil.texture = _zar_tex()
		sil.scale = Vector2.ONE * 0.5
	else:
		var d: Dictionary = Data.weapon_sprite(id, "demir")
		if d.get("tex") != null:
			sil.texture = d["tex"]
			sil.region_enabled = true
			sil.region_rect = d["region"]
			var reg: Vector2 = (d["region"] as Rect2).size
			var dik := reg.x > reg.y * 1.3
			var w := reg.y if dik else reg.x
			var h := reg.x if dik else reg.y
			var sc := minf((bx[1] as Vector2).x / w, (bx[1] as Vector2).y / h)
			sil.scale = Vector2.ONE * sc
			sil.rotation = (-PI / 2.0 + 0.16) if dik else 0.0
	sil.position = bx[0]
	kok.add_child(sil)
	k["silah"] = sil
	k["taban_y"] = (bx[0] as Vector2).y
	if not on.is_empty():
		var o := _sprite(on, Vector2.ZERO, mat)
		kok.add_child(o)
		k["on"] = o
	var mh := Sprite2D.new()
	mh.position = Vector2(0, -27.0 if tr != "c" else -29.0) + Vector2(5.0 if tr != "c" else 4.2, 0)
	kok.add_child(mh)
	k["muhur"] = mh
	kupler.append(k)
	_hal(k, Kupler.durum(id))


func _zar_tex() -> Texture2D:
	## Rastgele küp: içinde dönen Kut sarmalı ve "?" (çizim düğümü yerine küçük doku; bir kez)
	var img := Image.create(48, 64, false, Image.FORMAT_RGBA8)
	img.fill(Color(0, 0, 0, 0))
	for y in 64:
		for x in 48:
			var p := Vector2(x - 24, y - 32) / Vector2(20, 28)
			var r := p.length()
			var a := atan2(p.y, p.x)
			var sp := absf(sin(a * 2.0 + r * 9.0))
			var v := clampf((1.0 - r) * 1.4, 0.0, 1.0) * (0.35 + 0.65 * sp)
			if v > 0.02:
				img.set_pixel(x, y, Color(0.6, 1.0, 0.95, v * 0.8))
	return ImageTexture.create_from_image(img)


func _hal(k: Dictionary, st: String) -> void:
	## Küpün görünümünü duruma getir: kilitli / parsomen / acik / uyku (yeni ama henüz uyanmamış: eski durumu)
	var id: String = k["id"]
	if st == "uyku":
		st = "parsomen" if Data.find_item(id).has("upgrade_of") else "kilitli"
	k["durum"] = st
	var sil: Sprite2D = k["silah"]
	var halo: Sprite2D = k["halo"]
	var mh: Sprite2D = k["muhur"]
	var arka: Sprite2D = k.get("arka")
	var ai: Sprite2D = k.get("arka_isik")
	var renk := ALTIN_RENK if _altin else KUT_RENK
	match st:
		"acik":
			sil.modulate = Color(1, 1, 1, 1)
			halo.visible = true
			halo.modulate = Color(renk, 0.42)
			if arka:
				arka.modulate = Color(1, 1, 1)
			if ai:
				ai.visible = true
				ai.self_modulate = Color(renk.r * 1.2, renk.g * 1.2, renk.b * 1.2, 0.9)
			_muhur_tex(mh, "")   # açık küpün mührü kırılmış: yalnızca silah öne çıkar
		"parsomen":
			sil.modulate = Color(0.32, 0.52, 0.62, 0.7)
			halo.visible = true
			halo.modulate = Color(0.4, 0.6, 0.9, 0.16)
			if arka:
				arka.modulate = Color(0.7, 0.78, 0.85)
			if ai:
				ai.visible = true
				ai.self_modulate = Color(0.5, 0.6, 0.9, 0.35)
			_muhur_tex(mh, "kup_parsomen")
		_:
			# kilitli: bulanık sıvının sönük ışığı önünde kara gölge (biçimi seçilir, kimliği değil)
			sil.modulate = Color(0.02, 0.025, 0.05, 0.96)
			halo.visible = true
			halo.modulate = Color(0.45, 0.6, 0.7, 0.1)
			if arka:
				arka.modulate = Color(0.5, 0.52, 0.6)
			if ai:
				ai.visible = true
				ai.self_modulate = Color(0.4, 0.55, 0.6, 0.3)
			_muhur_tex(mh, "kup_muhur_catlak")
	if k["id"] == Kupler.RASTGELE and st == "kilitli":
		sil.modulate = Color(0.3, 0.3, 0.35, 0.5)
	# YENİ etiketi ve kıvılcım
	var yeni := st == "acik" and Kupler.yeni_mi(id)
	if yeni and not k.has("etiket"):
		var l := _etiket("YENİ", 6, Color(1.0, 0.9, 0.45), true)
		l.position = Vector2(-20, -10.5)   # camın önünde, sıvının üstünde
		l.size = Vector2(40, 10)
		k["kok"].add_child(l)
		k["etiket"] = l
		var p := CPUParticles2D.new()
		p.amount = 6
		p.lifetime = 1.2
		p.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
		p.emission_rect_extents = Vector2(8, 12)
		p.position = (KUTU[k["tur"]][0] as Vector2)
		p.gravity = Vector2(0, -12)
		p.initial_velocity_min = 2.0
		p.initial_velocity_max = 6.0
		p.scale_amount_min = 0.8
		p.scale_amount_max = 1.6
		p.color = Color(1.4, 1.3, 0.8, 0.9)
		var cm := CanvasItemMaterial.new()
		cm.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
		p.material = cm
		k["kok"].add_child(p)
		k["kivilcim"] = p
	elif not yeni and k.has("etiket"):
		(k["etiket"] as Node).queue_free()
		(k["kivilcim"] as Node).queue_free()
		k.erase("etiket")
		k.erase("kivilcim")


func _muhur_tex(mh: Sprite2D, ad: String) -> void:
	var d: Dictionary = level._decor_v2(ad) if ad != "" else {}
	if d.is_empty():
		mh.texture = null
		return
	mh.texture = d["tex"]
	mh.centered = false
	mh.offset = Vector2(-float(d["origin"][0]), -float(d["origin"][1]))
	var kk := 0.8 / float(d.get("texel", 4.0))
	mh.scale = Vector2(kk, kk)
	mh.position.y = -27.0 if ad != "kup_parsomen" else -9.0
	mh.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS


func _sayac_yaz() -> void:
	_sayi = Kupler.acilan()
	_sayac.text = "Açılan silahlar %d/%d" % [_sayi, Kupler.toplam()]   # sonraki eşik kartın altında (hud_ciz)


# ------------------------------------------------------------------ kare
func _process(delta: float) -> void:
	_t += delta
	var pl: Node2D = level.player if level else null
	var oyunda: bool = not get_tree().paused
	# yürürken: oyuncunun önündeki sütun (satır: son gezilen, ilk açılışta alt raf)
	if pl and not gez:
		var lx := pl.global_position.x - global_position.x
		yakin = lx > X0 - 6.0 and lx < X0 + ARALIK * SUTUN + 6.0 and absf(pl.global_position.y - global_position.y) < 60.0
		if yakin:
			var c := clampi(int(floor((lx - X0) / ARALIK)), 0, SUTUN - 1)
			var ni := mini(c + _satir * SUTUN, kupler.size() - 1)
			if ni != secili:
				secili = ni
				_kart_t = 0.0
		else:
			secili = -1
	_kart_t += delta
	if secili >= 0 and _kart_t > 0.9 and Kupler.yeni_mi(kupler[secili]["id"]) and kupler[secili]["durum"] == "acik":
		Kupler.goruldu(kupler[secili]["id"])   # kartı görüldü: YENİ söner
		_hal(kupler[secili], "acik")
	# görünür küplerde süzülme (yalnızca açıklar), ışıma nefesi
	var vis := _gorunur()
	if vis:
		for k in kupler:
			if k["durum"] == "acik":
				var sil: Sprite2D = k["silah"]
				sil.position.y = float(k["taban_y"]) + sin(_t * 1.5 + float(k["i"]) * 0.7) * 1.1
				(k["halo"] as Sprite2D).modulate.a = 0.36 + 0.1 * sin(_t * 2.0 + float(k["i"]))
	# uyanış: yeni küp oyunda ilk görüldüğünde (oyuncu yakınsa) sırayla
	if oyunda and vis and not _uyanacak.is_empty() and pl:
		var k: Dictionary = _uyanacak[0]
		if float(k["uyan_t"]) < 0.0:
			k["uyan_t"] = 0.0
		_uyanis(k, delta)
	_isaret.queue_redraw()


func _gorunur() -> bool:
	var vp := get_viewport()
	if vp == null:
		return false
	var cam := vp.get_camera_2d()
	if cam == null:
		return true
	var c := cam.get_screen_center_position()
	return c.x - 400.0 < global_position.x + GEN and c.x + 400.0 > global_position.x


func _uyanis(k: Dictionary, delta: float) -> void:
	## 0-0,5 sn: mühür titrer, 0,5: kırılır (halka + kıvılcım), 0,5-1,6: silah karanlıktan renge, ışık parlar, YENİ
	var t0 := float(k["uyan_t"])
	var t1 := t0 + delta
	k["uyan_t"] = t1
	var kok: Node2D = k["kok"]
	var mh: Sprite2D = k["muhur"]
	var sil: Sprite2D = k["silah"]
	var wp: Vector2 = kok.global_position + (KUTU[k["tur"]][0] as Vector2)
	var renk := ALTIN_RENK if _altin else KUT_RENK
	if t1 < 0.5:
		mh.position.x = (5.0 if k["tur"] != "c" else 4.2) + sin(t1 * 60.0) * 0.8
		kok.scale = Vector2.ONE * (1.0 + 0.04 * sin(t1 * 40.0))
	if t0 < 0.5 and t1 >= 0.5:
		kok.scale = Vector2.ONE
		_hal(k, "acik")
		sil.modulate = Color(0, 0, 0, 0.9)
		FX.ring(wp, 26, renk, 0.5)
		FX.burst(wp, renk, 16, 80, 0.6, 0.18, -40, true)
		Ses.play("seviye", -6.0, 1.2)
	if t1 >= 0.5 and t1 < 1.6:
		var a := clampf((t1 - 0.5) / 1.0, 0.0, 1.0)
		sil.modulate = Color(a, a, a, 0.9 + 0.1 * a)
		(k["halo"] as Sprite2D).modulate = Color(renk, 0.42 + 0.9 * (1.0 - a) * a * 2.0)
		sil.scale = sil.scale  # boyut sabit
	if t0 < 1.6 and t1 >= 1.6:
		sil.modulate = Color(1, 1, 1, 1)
		FX.soul(wp, renk, 10)
		FX.text(wp + Vector2(0, -30), kup_adi(k["id"]), renk, 8)
		Kupler.uyandir(k["id"])
		_uyanacak.pop_front()
		_sayac_yaz()


func kup_adi(id: String) -> String:
	if id == Kupler.RASTGELE:
		return "Ata'nın Zarı"
	return String(Data.find_item(id).get("name", id))


func acildi(id: String) -> void:
	## Demirci açtı / ilk kez kuşanıldı (yurttayken): küp bir sonraki görünüşünde uyanır
	for k in kupler:
		if k["id"] == id and not (k in _uyanacak):
			_hal(k, "uyku")
			_uyanacak.append(k)
		elif k["id"] == Kupler.RASTGELE and Kupler.yeni_mi(Kupler.RASTGELE) and not (k in _uyanacak) and k["durum"] != "acik":
			_uyanacak.append(k)
	_sayac_yaz()


# ------------------------------------------------------------------ işaretler ve imleç
func _isaret_ciz() -> void:
	var ci := _isaret
	var s_m := Kupler.secili("melee")
	var s_s := Kupler.secili("second")
	for k in kupler:
		var id: String = k["id"]
		if id == s_m or id == s_s:
			# başlangıç silahı: rafın önünde altın tamga (♦) ve ince çizgi
			var p: Vector2 = k["pos"] + Vector2(0, 2.4)
			ci.draw_line(p + Vector2(-9, 0), p + Vector2(9, 0), Color(1.0, 0.82, 0.38, 0.9), 1.2, true)
			ci.draw_colored_polygon(PackedVector2Array([p + Vector2(0, -2.6), p + Vector2(2.6, 0), p + Vector2(0, 2.6), p + Vector2(-2.6, 0)]), Color(1.0, 0.85, 0.4))
	if secili >= 0 and (yakin or gez):
		var k: Dictionary = kupler[secili]
		var p: Vector2 = k["pos"]
		var w := 13.5 if k["tur"] != "b" else 15.5
		var a := 0.55 + 0.3 * sin(_t * 5.0) if gez else 0.35
		var col := Color(1.0, 0.85, 0.45, a) if k["durum"] == "acik" else Color(0.75, 0.8, 0.9, a * 0.8)
		var r := Rect2(p + Vector2(-w, -42), Vector2(w * 2.0, 44))
		# köşe ayraçları (fırça imleci)
		var L := 5.0
		for c in [r.position, Vector2(r.end.x, r.position.y), r.end, Vector2(r.position.x, r.end.y)]:
			var sx := 1.0 if c.x < p.x else -1.0
			var sy := 1.0 if c.y < p.y - 20.0 else -1.0
			ci.draw_line(c, c + Vector2(L * sx, 0), col, 1.4, true)
			ci.draw_line(c, c + Vector2(0, L * sy), col, 1.4, true)


# ------------------------------------------------------------------ gezme kipi (Main._on_npc "kupler" → hud.mode "kupler")
func gez_ac() -> void:
	gez = true
	if secili < 0:
		secili = clampi(3 * SUTUN, 0, kupler.size() - 1)
	_kart_t = 0.0


func gez_kapat() -> void:
	gez = false
	_satir = secili / SUTUN if secili >= 0 else 3


func gez_tasi(dx: int, dy: int) -> void:
	var c := secili % SUTUN
	var r := secili / SUTUN
	c = (c + dx + SUTUN) % SUTUN
	r = clampi(r + dy, 0, RAF_Y.size() - 1)
	var ni := r * SUTUN + c
	if ni >= kupler.size():
		ni = kupler.size() - 1
	if ni != secili:
		secili = ni
		_kart_t = 0.0
		Ses.play("ui_gez")


func sec_secili() -> String:
	## Seçili açık küpü başlangıç silahı yap. Döner: "" (olmadı), "secildi", "kaldirildi"
	if secili < 0:
		return ""
	var k: Dictionary = kupler[secili]
	var id: String = k["id"]
	if Kupler.durum(id) != "acik":
		Ses.play("ui_iptal")
		return ""
	if k in _uyanacak:   # henüz uyanmamış yeni küp: uyanış atlanır
		_uyanacak.erase(k)
		Kupler.uyandir(id)
		_hal(k, "acik")
	var sl := Kupler.yuva(id)
	var once := Kupler.secili(sl)
	Kupler.sec(id)
	var kaldirildi := once == id
	# yurtta koşu henüz başlamadı: seçilen silah hemen kuşanılır (kaldırılırsa varsayılan başlangıç silahı)
	if level and level.hub and not Game.run.is_empty():
		var ust := Game.umay_level("silah") > 0
		var it: Dictionary
		if kaldirildi:
			var vid := "alp_kilici" if sl == "melee" else "turk_yayi"
			it = ItemGen.roll(vid, 1 if ust else 0, "tunc" if ust else "demir", 1 if ust else 0)
		else:
			it = Kupler.esya(id, ust)
		if not it.is_empty():
			Game.run["slots"][sl] = it
			if level.player and level.player.has_method("on_equip"):
				level.player.on_equip()
	var wp: Vector2 = (k["kok"] as Node2D).global_position + (KUTU[k["tur"]][0] as Vector2)
	var renk := ALTIN_RENK
	FX.ring(wp, 22, renk, 0.4)
	FX.burst(wp, renk, 10, 60, 0.5, 0.16, -40, true)
	Ses.play("esya_kusan")
	if Kupler.yeni_mi(id):
		Kupler.goruldu(id)
		_hal(k, "acik")
	return "kaldirildi" if kaldirildi else "secildi"


# ------------------------------------------------------------------ HUD (HUD._draw_hud sonunda; ekran birimi)
func kart_esya(id: String) -> Dictionary:
	if not _kart_cache.has(id):
		var it := ItemGen.roll(id, 0, "demir", 0, "")
		it["quality"] = 100
		_kart_cache[id] = it
	return _kart_cache[id]


func hud_ciz(hud: Control, vp: Vector2) -> void:
	if secili < 0 or not (yakin or gez) or kupler.is_empty() or kart_kapali:
		return
	var k: Dictionary = kupler[secili]
	var id: String = k["id"]
	var st: String = k["durum"]
	var x := vp.x - 198.0
	var y := 66.0
	var baslik := "KÜP %d/%d · %s" % [secili + 1, kupler.size(), Kupler.sinif_adi(id).to_upper()]
	var not_satir := ""
	if id == Kupler.RASTGELE:
		_kucuk_kart(hud, Rect2(x, y, 190, 66), "Ata'nın Zarı" if st == "acik" else "???", baslik,
			"Açık küplerden rastgele bir yakın dövüş silahıyla, bir kademe nadir başla." if st == "acik" else Kupler.ipucu(id), st == "acik")
		y += 76.0
	elif st == "kilitli":
		_kucuk_kart(hud, Rect2(x, y, 190, 60), "???", baslik, Kupler.ipucu(id), false)
		y += 70.0
	else:
		var it := kart_esya(id)
		hud._draw_card(it, Vector2(x, y), baslik)
		y += hud._card_h(it) + 8.0
		if st == "parsomen":
			not_satir = Kupler.ipucu(id)
	var sl := Kupler.yuva(id)
	if st == "acik":
		var sec_m := Kupler.secili(sl) == id
		not_satir = ("Başlangıç silahın (%s). Yeniden seçersen varsayılana döner." if sec_m else "Boşluk: koşuya bununla başla (%s yuvası).") % ["yakın dövüş" if sl == "melee" else "ikincil"]
		if not gez:
			not_satir = "W: küpleri gez · " + ("başlangıç silahın" if sec_m else "açık küp")
	if not_satir != "":
		for l in PixUI.wrap(not_satir, 186):
			PixUI.text(hud, Vector2(x + 2, y), l, PixUI.GOLD if st == "acik" else PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 2)
			y += 10.0
	# sayaç ve eşik (sol üstte değil: kartın altında)
	y += 4.0
	PixUI.text(hud, Vector2(x + 2, y), "Açılan silahlar %d/%d" % [_sayi, Kupler.toplam()], PixUI.KUT, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 2)
	y += 10.0
	var e := Kupler.sonraki_esik()
	if not e.is_empty():
		for l in PixUI.wrap("%d küpte: %s — %s" % [int(e["n"]), String(e["ad"]), String(e["desc"])], 186):
			PixUI.text(hud, Vector2(x + 2, y), l, PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 2)
			y += 10.0
	if gez:
		hud._hint(vp, [["←→↑↓", "gez"], ["Boşluk", "başlangıç silahı"], ["Esc", "çık"]])
	elif level and level.player:
		var sp: Vector2 = (hud.get_viewport().get_canvas_transform() * ((k["kok"] as Node2D).global_position + Vector2(0, -50))) / Ayarlar.ui_scale()
		hud._world_prompt(sp, "W", "Küpleri gez")


func _kucuk_kart(hud: Control, r: Rect2, ad: String, ust: String, metin: String, acik: bool) -> void:
	var col := PixUI.KUT if acik else Color(0.55, 0.55, 0.62)
	PixUI.panel(hud, r, col.darkened(0.2))
	PixUI.text(hud, Vector2(r.position.x + 4, r.position.y - 19.0), ust, PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 2)
	var y := InkUI.card_head(hud, r, col, ad, "Kilitli küp" if not acik else "Kurgan armağanı")
	for l in PixUI.wrap(metin, 176):
		PixUI.text(hud, Vector2(r.position.x + 6, y), l, PixUI.TEXT if acik else PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
		y += 10.0
