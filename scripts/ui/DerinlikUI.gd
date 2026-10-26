class_name DerinlikUI
extends RefCounted
## v44 arayüzü (v40 mürekkep tasarım sistemi: InkUI belirteçleri, Cinzel / Alegreya / Kaushan): Damga Taşı ekranı,
## HUD'da etkin Damgalar, Ozan'ın Destanı (kodeks: Yaratıklar · Silahlar · Damgalar · Destan · Başarımlar · Rekorlar),
## koşu özeti (ölüm ve zafer), başarım bildirimi. Çizim HUD'un menü tuvalinde (640x360 tasarım), girdi
## Main._unhandled_input → girdi(). Durum burada (statik): ekranlar HUD.mode ile açılır ("damga", "kodeks", "zafer").

const SEKMELER := ["YARATIKLAR", "SİLAHLAR", "DAMGALAR", "DESTAN", "BAŞARIMLAR", "REKORLAR"]
const DAMGA_TEX := "res://assets/ui/ink/damga44.png"

static var sekme := 0
static var sec := 0
static var kaydir := 0
static var geri := "play"
static var damga_sec := 0
static var damga_adim := 0       # 0 kart seç, 1 (yuva dolu) silinecek Damgayı seç
static var damga_yer := 0
static var damga_sonuc := ""     # vurulan Damga (damga basma animasyonu)
static var damga_t := 0.0
static var son_ozet: Dictionary = {}
static var _t0 := 0.0


static func tamga(ci: CanvasItem, id: String, c: Vector2, s: float, col: Color, golge := true) -> void:
	var t: Texture2D = InkUI.tex("damga44") if ResourceLoader.exists(DAMGA_TEX) else null
	if t == null or not Damga.D.has(id):
		return
	var i := int(Damga.D[id][1])
	var px := t.get_height() if t.get_height() > 0 else 128
	var rg := Rect2(i * px, 0, px, px)
	var r := Rect2(c - Vector2(s, s) * 0.5, Vector2(s, s))
	if golge:
		ci.draw_texture_rect_region(t, Rect2(r.position + Vector2(0.8, 1.0), r.size), rg, Color(0, 0, 0, 0.5 * col.a))
	ci.draw_texture_rect_region(t, r, rg, col)


static func _now() -> float:
	return Time.get_ticks_msec() / 1000.0


# ================================================================== açılışlar (Main)
static func damga_ac(main: Node) -> void:
	var hud: Node = main.hud
	if Damga.secildi():
		hud.flash_msg = "Bu konakta Damgan vuruldu. Taş bir sonraki konakta yeniden konuşur."
		hud.flash_t = 3.0
		main._start_play()
		return
	if Damga.teklif().is_empty():
		Damga.yeni_konak(randi())
	damga_sec = 0
	damga_adim = 0
	damga_yer = 0
	damga_sonuc = ""
	hud.mode = "damga"
	hud.open_anim()
	Ses.play("usta_damga", -4.0)
	Ses.play("ui_ac", -4.0)
	main.get_tree().paused = true


static func kodeks_ac(main: Node, sek := -1) -> void:
	var hud: Node = main.hud
	geri = String(hud.mode)
	if sek >= 0:
		sekme = sek
	sec = 0
	kaydir = 0
	hud.mode = "kodeks"
	hud.open_anim()
	Ses.play("ui_ac", -4.0)
	Basarim.olay("kodeks")
	main.get_tree().paused = true


static func ozet_kur(zafer: bool) -> void:
	son_ozet = KosuOzet.bitir(zafer)
	_t0 = _now()


# ================================================================== girdi
static func girdi(main: Node, ev: InputEvent) -> bool:
	var hud: Node = main.hud
	var go: bool = ev.is_action_pressed("zipla") or (ev is InputEventKey and ev.pressed and ev.physical_keycode == KEY_ENTER)
	var geri_tus: bool = ev.is_action_pressed("duraklat") or ev.is_action_pressed("yuvarlan")
	match String(hud.mode):
		"damga":
			_girdi_damga(main, ev, go, geri_tus)
			return true
		"kodeks":
			_girdi_kodeks(main, ev, go, geri_tus)
			return true
		"zafer":
			if go and _now() - _t0 > 0.8:
				Ses.play("ui_onay")
				main._start_play()
			elif ev.is_action_pressed("kodeks"):
				kodeks_ac(main, 5)
			return true
		"dead":
			if ev.is_action_pressed("kodeks"):
				kodeks_ac(main, 5)
				return true
		"ozan":
			if ev.is_action_pressed("techizat2") or ev.is_action_pressed("kodeks"):
				kodeks_ac(main, 0)
				return true
		"play":
			if main.get_tree().paused and ev.is_action_pressed("kodeks"):
				kodeks_ac(main, 0)
				return true
	return false


static func _girdi_damga(main: Node, ev: InputEvent, go: bool, geri_tus: bool) -> void:
	var hud: Node = main.hud
	var tk: Array = Damga.teklif()
	if damga_sonuc != "":
		if (go or geri_tus) and _now() - damga_t > 0.5:
			damga_sonuc = ""
			main._start_play()
		return
	if damga_adim == 1:
		var a: Array = Damga.etkin()
		if ev.is_action_pressed("sol") or ev.is_action_pressed("yukari"):
			damga_yer = (damga_yer + a.size() - 1) % maxi(1, a.size())
			Ses.play("ui_gez")
		elif ev.is_action_pressed("sag") or ev.is_action_pressed("asagi"):
			damga_yer = (damga_yer + 1) % maxi(1, a.size())
			Ses.play("ui_gez")
		elif go:
			_vur(main, String(tk[damga_sec]), String(a[damga_yer]))
		elif geri_tus:
			damga_adim = 0
			Ses.play("ui_iptal")
		return
	if tk.is_empty():
		if go or geri_tus:
			main._start_play()
		return
	if ev.is_action_pressed("sol") or ev.is_action_pressed("yukari"):
		damga_sec = (damga_sec + tk.size() - 1) % tk.size()
		Ses.play("ui_gez")
	elif ev.is_action_pressed("sag") or ev.is_action_pressed("asagi"):
		damga_sec = (damga_sec + 1) % tk.size()
		Ses.play("ui_gez")
	elif ev.is_action_pressed("techizat2"):
		var r := Damga.oy()
		hud.flash_msg = String(r["msg"])
		hud.flash_t = 2.5
		Ses.play("usta_nakis" if r["ok"] else "ui_sec", -3.0 if r["ok"] else 0.0, 1.0 if r["ok"] else 0.7)
		if r["ok"]:
			hud.open_anim()
	elif go:
		if Damga.etkin().size() >= Damga.yuva():
			damga_adim = 1
			damga_yer = 0
			Ses.play("ui_gez")
		else:
			_vur(main, String(tk[damga_sec]), "")
	elif geri_tus:
		Ses.play("ui_iptal")
		main._start_play()


static func _vur(main: Node, id: String, yerine: String) -> void:
	var r := Damga.al(id, yerine)
	main.hud.flash_msg = String(r["msg"])
	main.hud.flash_t = 4.0
	if not r["ok"]:
		Ses.play("ui_sec", 0.0, 0.7)
		return
	damga_sonuc = id
	damga_t = _now()
	damga_adim = 0
	Ses.play("usta_damga", -1.0)
	Ses.play("destan", -4.0)
	var lv: Node = main.level
	if lv and lv.player:
		var c := Damga.renk(id)
		FX.soul(lv.player.center(), c, 26)
		FX.ring(lv.player.center(), 50, c, 0.5)
		FX.text(lv.player.center() + Vector2(0, -44), Damga.ad(id), c, 10)
	Game.save_meta()


static func _girdi_kodeks(main: Node, ev: InputEvent, go: bool, geri_tus: bool) -> void:
	var hud: Node = main.hud
	var n := _kodeks_n()
	var cols := _kodeks_cols()
	if ev.is_action_pressed("techizat1") or ev.is_action_pressed("sise"):
		sekme = (sekme + SEKMELER.size() - 1) % SEKMELER.size()
		sec = 0
		kaydir = 0
		hud.open_anim()
		Ses.play("ui_gez")
	elif ev.is_action_pressed("techizat2"):
		sekme = (sekme + 1) % SEKMELER.size()
		sec = 0
		kaydir = 0
		hud.open_anim()
		Ses.play("ui_gez")
	elif ev.is_action_pressed("sol") and n > 0:
		sec = (sec + n - 1) % n
		Ses.play("ui_gez")
	elif ev.is_action_pressed("sag") and n > 0:
		sec = (sec + 1) % n
		Ses.play("ui_gez")
	elif ev.is_action_pressed("yukari") and n > 0:
		sec = clampi(sec - cols, 0, n - 1)
		Ses.play("ui_gez")
	elif ev.is_action_pressed("asagi") and n > 0:
		sec = clampi(sec + cols, 0, n - 1)
		Ses.play("ui_gez")
	elif go and sekme == 4:
		var bid: String = Basarim.B.keys()[clampi(sec, 0, Basarim.B.size() - 1)]
		var b: Array = Basarim.B[bid]
		if String(b[3]) == "renk" and Basarim.acik(bid):
			var rid := String(b[4])
			Game.meta["hud_renk"] = "" if String(Game.meta.get("hud_renk", "")) == rid else rid
			Game.save_meta()
			Ses.play("ui_onay")
			hud.flash_msg = "HUD çerçevesi: %s" % String(Basarim.RENK[String(Game.meta["hud_renk"])][0])
			hud.flash_t = 2.0
	elif geri_tus or ev.is_action_pressed("kodeks"):
		Ses.play("ui_kapa")
		hud.mode = geri
		hud.open_anim()
		if geri == "play":
			main.get_tree().paused = true


static func _kodeks_n() -> int:
	match sekme:
		0:
			return Kodeks.yaratiklar().size()
		1:
			return Kodeks.silahlar().size()
		2:
			return Damga.D.size()
		3:
			return Kodeks.destan_kayitlari().size()
		4:
			return Basarim.B.size()
	return 0


static func _kodeks_cols() -> int:
	match sekme:
		0, 1:
			return 6
		2, 4:
			return 5
		3:
			return 1
	return 1


# ================================================================== HUD: etkin Damgalar, bildirim
static func hud(h: Control, x: float, y: float, t: float) -> void:
	var a: Array = Damga.etkin()
	if Game.run.is_empty() or (a.is_empty() and Damga.yuva() <= 1 and not h.level.konak):
		return
	var n := Damga.yuva()
	var edge := Basarim.hud_renk()
	for i in n:
		var c := Vector2(x + 9.0 + i * 21.0, y + 9.0)
		h.draw_circle(c + Vector2(0.6, 0.8), 9.6, Color(0, 0, 0, 0.45), true, -1.0, true)
		h.draw_circle(c, 9.2, Color(0.06, 0.05, 0.08, 0.9), true, -1.0, true)
		if i < a.size():
			var id := String(a[i])
			var col := Damga.renk(id)
			var uy := Damga.uyum(id)
			h.draw_arc(c, 9.2, 0, TAU, 24, Color(col, 0.85 if uy else 0.55), 1.4 if uy else 1.0, true)
			if uy:
				h.draw_arc(c, 11.0, -PI * 0.5, -PI * 0.5 + TAU * (0.5 + 0.5 * sin(t * 2.0)) , 20, Color(col, 0.35), 0.8, true)
			tamga(h, id, c, 15.0, col.lightened(0.15), false)
		else:
			h.draw_arc(c, 9.2, 0, TAU, 24, Color(edge, 0.35), 0.8, true)
			h.draw_circle(c, 1.4, Color(edge, 0.4), true, -1.0, true)


static func toast(h: Control, vp: Vector2) -> void:
	var q: Array = Basarim.kuyruk
	if q.is_empty():
		return
	var now := Game.clock()
	var e: Array = q[0]
	var dt := now - float(e[1])
	if dt > 4.6:
		q.pop_front()
		if not q.is_empty():
			q[0][1] = now
		return
	var id := String(e[0])
	var b: Array = Basarim.B.get(id, ["?", "", "yildiz", "", ""])
	var k := clampf(minf(dt / 0.3, (4.6 - dt) / 0.4), 0.0, 1.0)
	var ek := 1.0 - pow(1.0 - k, 3.0)
	var w := maxf(190.0, InkUI.width(String(b[0])) + 100.0)
	var r := Rect2(vp.x - w - 10.0 + (1.0 - ek) * (w + 20.0), 36.0 if String(h.get("mode")) == "play" else 4.0, w, 30.0)
	InkUI.panel(h, r, Color(InkUI.GOLD, ek), Color(0.06, 0.05, 0.08, 0.95 * ek))
	InkUI.kilim(h, Rect2(r.position.x + 8, r.end.y - 4, r.size.x - 16, 2.2), Color(InkUI.GOLD, 0.5 * ek))
	rozet(h, id, Vector2(r.position.x + 18.0, r.get_center().y), 26.0, true, ek, minf(1.0, dt / 0.45))
	InkUI.text(h, Vector2(r.position.x + 36.0, r.position.y + 3.0), "DESTAN BAŞARISI", Color(InkUI.GOLD, 0.9 * ek), 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 1)
	InkUI.text(h, Vector2(r.position.x + 36.0, r.position.y + 15.0), String(b[0]), Color(InkUI.BONE, ek), 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 1)
	var od := odul_txt(id)
	InkUI.text(h, Vector2(r.position.x, r.position.y + 15.0), od, Color(InkUI.MUTED, ek), 1, HORIZONTAL_ALIGNMENT_RIGHT, r.size.x - 10.0, 0)


static func rozet(ci: CanvasItem, id: String, c: Vector2, s: float, acik: bool, a := 1.0, bas := 1.0) -> void:
	## Başarım rozeti: kızıl yuvarlak mühür üstünde kâğıt rengi simge (kapalıysa soluk mürekkep)
	var b: Array = Basarim.B.get(id, ["", "", "yildiz"])
	var scl := lerpf(1.8, 1.0, 1.0 - pow(1.0 - clampf(bas, 0.0, 1.0), 3.0))
	var ss := s * scl
	var col := Color(InkUI.VERMILION, 0.96 * a) if acik else Color(0.22, 0.2, 0.26, 0.9 * a)
	InkUI.seal_round(ci, c + Vector2(0.8, 1.0), ss, Color(0, 0, 0, 0.45 * a), 0.3)
	InkUI.seal_round(ci, c, ss, col, 0.3)
	var ic := String(b[2])
	var icol := Color(InkUI.PAPER, 0.95 * a) if acik else Color(0.5, 0.47, 0.52, 0.7 * a)
	if InkUI.has_icon(ic):
		InkUI.icon_at(ci, ic, c, ss * 0.5, icol, false)


static func odul_txt(id: String) -> String:
	var b: Array = Basarim.B[id]
	match String(b[3]):
		"kut":
			return "+%d Kut" % int(b[4])
		"renk":
			return "çerçeve: %s" % String(Basarim.RENK.get(String(b[4]), ["?"])[0])
		"soz":
			return "Ozan dizesi"
	return ""


# ================================================================== Damga Taşı ekranı
static func ciz_damga(h: Control, vp: Vector2) -> void:
	h._dim(vp, 0.8)
	var e: float = h._ease_open()
	var t: float = h._t
	var bid := String(h.level.biome.get("id", "")) if h.level else ""
	h._title(vp, 24, "DAMGA TAŞI", InkUI.GOLD, "«Taşa hangi izi vuralım, alp? Tamga bir kez vurulur, yol boyunca seninle yürür.»")
	var tk: Array = Damga.teklif()
	var cw := 164.0
	var ch := 186.0
	var gap := 14.0
	var x0 := roundf((vp.x - (cw * tk.size() + gap * maxf(0.0, tk.size() - 1))) * 0.5)
	var y0 := 74.0 + (1.0 - e) * 14.0
	for i in tk.size():
		var id := String(tk[i])
		var on := i == damga_sec and damga_adim == 0
		var r := Rect2(x0 + i * (cw + gap), y0 - (6.0 if on else 0.0), cw, ch)
		_damga_kart(h, r, id, on, e, t)
		if damga_sonuc == id:
			_damga_bas(h, r.get_center() + Vector2(0, -28), "VURULDU", Damga.renk(id))
	# alt: etkin Damgalar ve yuvalar
	var ay := y0 + ch + 18.0
	var a: Array = Damga.etkin()
	var n := Damga.yuva()
	var lbl := "DAMGALARIN  %d / %d YUVA" % [a.size(), n]
	if damga_adim == 1:
		lbl = "YUVALAR DOLU: HANGİ DAMGA SİLİNSİN?"
	InkUI.text(h, Vector2(0, ay - 2), lbl, InkUI.BAD if damga_adim == 1 else InkUI.MUTED, 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x, 1)
	var gtxt := "%d altın" % int(Game.run.get("gold", 0))
	InkUI.icon_at(h, "altin", Vector2(vp.x - 36.0 - InkUI.width(gtxt), ay + 4.0), 10.0, InkUI.GOLD)
	InkUI.text(h, Vector2(0, ay - 2), gtxt, InkUI.GOLD, 1, HORIZONTAL_ALIGNMENT_RIGHT, vp.x - 26.0, 2)
	var sw := 150.0
	var sx := roundf((vp.x - (sw * 3 + 8.0 * 2)) * 0.5)
	for i in 3:
		var r := Rect2(sx + i * (sw + 8.0), ay + 12.0, sw, 22.0)
		if i < a.size():
			var id := String(a[i])
			var col := Damga.renk(id)
			var hedef := damga_adim == 1 and i == damga_yer
			InkUI.panel(h, r, Color(col, 0.9 if hedef else 0.5), Color(0.08, 0.06, 0.1, 0.92))
			if hedef:
				InkUI.select_mark(h, r, InkUI.BAD, t)
			tamga(h, id, Vector2(r.position.x + 12.0, r.get_center().y), 16.0, col)
			InkUI.text(h, Vector2(r.position.x + 24.0, r.position.y + 6.0), Damga.ad(id), col.lightened(0.2), 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 1)
			if Damga.uyum(id):
				InkUI.text(h, Vector2(r.position.x, r.position.y + 6.0), "uyum", InkUI.GOOD, 1, HORIZONTAL_ALIGNMENT_RIGHT, r.size.x - 6.0, 0)
		elif i < n:
			InkUI.panel(h, r, Color(InkUI.MUTED, 0.3), Color(0.05, 0.045, 0.07, 0.7))
			InkUI.text(h, Vector2(r.position.x, r.position.y + 6.0), "boş yuva", Color(InkUI.MUTED, 0.7), 1, HORIZONTAL_ALIGNMENT_CENTER, r.size.x, 0)
		else:
			InkUI.panel(h, r, Color(0.3, 0.28, 0.32, 0.4), Color(0.03, 0.03, 0.04, 0.6))
			InkUI.icon_at(h, "muhur", Vector2(r.position.x + 12.0, r.get_center().y), 11.0, Color(0.5, 0.47, 0.52, 0.7))
			InkUI.text(h, Vector2(r.position.x + 22.0, r.position.y + 6.0), "kilitli yuva", Color(0.55, 0.52, 0.56), 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
	if n < 3:
		InkUI.text(h, Vector2(0, ay + 38.0), Damga.yuva_ipucu(), Color(InkUI.MUTED, 0.8), 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x, 0)
	if damga_sonuc != "":
		h._hint(vp, [["Boşluk", "yola devam"]])
	elif damga_adim == 1:
		h._hint(vp, [["A/D", "silinecek Damga"], ["Boşluk", "sil ve vur"], ["Esc", "geri"]])
	else:
		var c := Damga.oyma_bedel()
		h._hint(vp, [["A/D", "seç"], ["Boşluk", "vur"], ["R", "Bengisu yeniden oysun (%d altın)" % c], ["Esc", "ayrıl"]])
	h._reveal(vp)


static func _damga_kart(h: Control, r: Rect2, id: String, on: bool, e: float, t: float) -> void:
	var d: Array = Damga.D[id]
	var col := Damga.renk(id)
	var a := e
	if on:
		InkUI.splat(h, r.get_center(), r.size.x * 1.15, Color(col, 0.07 * a), 0.4)
	InkUI.fancy_panel(h, r, Color(col, (0.95 if on else 0.55) * a), Color(0.075, 0.06, 0.095, 0.96 * a))
	# tamga mührü
	var c := Vector2(r.get_center().x, r.position.y + 42.0)
	var pk := 0.5 + 0.5 * sin(t * 3.0)
	InkUI.ring(h, c, 26.0, 1.0 if on else 0.0, Color(col, (0.5 + 0.3 * pk) * a if on else 0.3 * a))
	tamga(h, id, c, 40.0 + (2.0 * pk if on else 0.0), Color(col.lightened(0.2 if on else 0.0), a))
	# ad
	var ny := r.position.y + 76.0
	InkUI.text(h, Vector2(r.position.x, ny), String(d[0]), Color(InkUI.BONE if on else InkUI.BONE.darkened(0.12), a), 2, HORIZONTAL_ALIGNMENT_CENTER, r.size.x, 2)
	var og := String(d[2])
	var tag := ("%s tomarıyla" % String(Data.items["ongun"][og]["name"])) if og != "" else "renksiz"
	InkUI.text(h, Vector2(r.position.x, ny + 26.0), "%s · %s" % [tag, String(d[5])], Color(col, 0.9 * a), 1, HORIZONTAL_ALIGNMENT_CENTER, r.size.x, 0)
	InkUI.kilim(h, Rect2(r.position.x + 18.0, ny + 39.0, r.size.x - 36.0, 2.2), Color(col, 0.45 * a))
	var yy := ny + 45.0
	for ln in PixUI.wrap(String(d[4]), r.size.x - 18.0):
		InkUI.text(h, Vector2(r.position.x, yy), String(ln), Color(InkUI.BONE, 0.95 * a), 1, HORIZONTAL_ALIGNMENT_CENTER, r.size.x, 0)
		yy += 11.0
	InkUI.text(h, Vector2(r.position.x, r.end.y - 34.0), "«%s»" % String(d[6]), Color(InkUI.MUTED, 0.75 * a), 1, HORIZONTAL_ALIGNMENT_CENTER, r.size.x, 0)
	# rozetler: uyum / nadir / yeni
	var bx := r.position.x + 8.0
	var by := r.end.y - 18.0
	if Damga.uyum(id):
		_rozet_yazi(h, Vector2(bx, by), "UYUM ×1,25", InkUI.GOOD, a)
		bx += 64.0
	elif og != "":
		_rozet_yazi(h, Vector2(bx, by), "%s önde olunca ×1,25" % String(Data.items["ongun"][og]["name"]), Color(InkUI.MUTED, 0.8), a)
		bx += 0.0
	if bool(d[3]):
		_rozet_yazi(h, Vector2(r.end.x - 42.0, by), "NADİR", InkUI.VERMILION.lightened(0.2), a)
	elif Kodeks.damga_alinan(id) == 0:
		_rozet_yazi(h, Vector2(r.end.x - 38.0, by), "YENİ", InkUI.GOLD, a)


static func _rozet_yazi(h: Control, p: Vector2, s: String, col: Color, a: float) -> void:
	var w := InkUI.width(s) + 8.0
	InkUI.panel(h, Rect2(p, Vector2(w, 12.0)), Color(col, 0.7 * a), Color(0.05, 0.04, 0.06, 0.9 * a), false)
	InkUI.text(h, p + Vector2(4.0, 1.0), s, Color(col, a), 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)


static func _damga_bas(h: Control, c: Vector2, txt: String, col: Color) -> void:
	var dt := _now() - damga_t
	var k := clampf(dt / 0.35, 0.0, 1.0)
	var scl := lerpf(3.6, 1.7, 1.0 - pow(1.0 - k, 3.0))
	var a := clampf(k * 2.0, 0.0, 1.0)
	var w := InkUI.width(txt) + 26.0
	h.draw_set_transform(c * HUD.MENU_SCALE, -0.16, Vector2.ONE * HUD.MENU_SCALE * scl)
	InkUI.splat(h, Vector2.ZERO, 30.0, Color(InkUI.VERMILION, 0.22 * a), 0.7)
	InkUI.seal(h, Rect2(-w / 2.0, -11.0, w, 22.0), Color(InkUI.VERMILION, a))
	InkUI.text(h, Vector2(-w / 2.0, -5.0), txt, Color(InkUI.PAPER, a), 1, HORIZONTAL_ALIGNMENT_CENTER, w, 1)
	h.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE * HUD.MENU_SCALE)
	if k >= 1.0 and dt < 0.6:
		var kk := (dt - 0.35) / 0.25
		for i in 7:
			var ang := float(i) / 7.0 * TAU + 0.4
			h.draw_circle(c + Vector2.from_angle(ang) * (34.0 + 40.0 * kk), 3.4 * (1.0 - kk), Color(col, 0.8 * (1.0 - kk)), true, -1.0, true)


# ================================================================== Ozan'ın Destanı (kodeks)
static func ciz_kodeks(h: Control, vp: Vector2) -> void:
	h._dim(vp, 0.94)
	var e: float = h._ease_open()
	var t: float = h._t
	var tam := Kodeks.tamamlanma()
	h._title(vp, 16, "OZAN'IN DESTANI", InkUI.GOLD, "")
	# tamamlanma: sağ üstte halka
	var rc := Vector2(vp.x - 40.0, 30.0)
	InkUI.ring(h, rc, 16.0, tam, InkUI.GOLD)
	InkUI.text(h, Vector2(rc.x - 20, rc.y - 6), "%%%d" % int(round(tam * 100.0)), InkUI.BONE, 1, HORIZONTAL_ALIGNMENT_CENTER, 40, 2)
	InkUI.text(h, Vector2(rc.x - 40, rc.y + 18), "tamamlandı", InkUI.MUTED, 1, HORIZONTAL_ALIGNMENT_CENTER, 80, 0)
	# sekmeler
	var tx := 24.0
	var ty := 50.0
	for i in SEKMELER.size():
		var s: String = SEKMELER[i]
		var w := InkUI.width(s) + 16.0
		var r := Rect2(tx, ty, w, 16.0)
		if i == sekme:
			InkUI.panel(h, r, InkUI.GOLD, Color(0.12, 0.09, 0.08, 0.95))
		InkUI.text(h, Vector2(tx, ty + 3), s, InkUI.GOLD if i == sekme else Color(InkUI.MUTED, 0.85), 1, HORIZONTAL_ALIGNMENT_CENTER, w, 1)
		tx += w + 6.0
	InkUI.key_cap(h, Vector2(8, ty + 3), "E", InkUI.GOLD)
	InkUI.key_cap(h, Vector2(tx + 2, ty + 3), "R", InkUI.GOLD)
	var area := Rect2(16, 76, vp.x - 32, vp.y - 106)
	match sekme:
		0:
			_kod_yaratik(h, area, e, t)
		1:
			_kod_silah(h, area, e, t)
		2:
			_kod_damga(h, area, e, t)
		3:
			_kod_destan(h, area, e, t)
		4:
			_kod_basarim(h, area, e, t)
		5:
			_kod_rekor(h, area, e, t)
	var hint: Array = [["E/R", "sekme"], ["W/A/S/D", "gez"], ["Esc", "kapat"]]
	if sekme == 4:
		hint.insert(2, ["Boşluk", "çerçeve rengini seç"])
	h._hint(vp, hint)
	h._reveal(vp)


static func _grid(h: Control, area: Rect2, n: int, cols: int, cell: float, t: float) -> Array:
	## Izgara hücreleri (kaydırma: seçili satır görünür kalır). Dönen: [[i, Rect2], ...]
	var rows_vis := int(floor((area.size.y - 4.0) / (cell + 4.0)))
	var row := sec / cols
	if row < kaydir:
		kaydir = row
	if row >= kaydir + rows_vis:
		kaydir = row - rows_vis + 1
	var out: Array = []
	for i in n:
		var r_i := i / cols - kaydir
		if r_i < 0 or r_i >= rows_vis:
			continue
		var c := i % cols
		out.append([i, Rect2(area.position.x + c * (cell + 4.0), area.position.y + r_i * (cell + 4.0), cell, cell)])
	# kaydırma çubuğu
	var total_rows := int(ceil(float(n) / cols))
	if total_rows > rows_vis:
		var gx := area.position.x + cols * (cell + 4.0) + 1.0
		var gh := rows_vis * (cell + 4.0) - 4.0
		h.draw_rect(Rect2(gx, area.position.y, 2.0, gh), Color(InkUI.MUTED, 0.2))
		var k0 := float(kaydir) / total_rows
		var k1 := float(kaydir + rows_vis) / total_rows
		h.draw_rect(Rect2(gx, area.position.y + gh * k0, 2.0, gh * (k1 - k0)), Color(InkUI.GOLD, 0.7))
	return out


static func _hucre(h: Control, r: Rect2, on: bool, col: Color, t: float) -> void:
	InkUI.nine(h, Rect2(r.position + Vector2(1.5, 2.0), r.size), InkUI.tex("fill"), 32.0, Color(0, 0, 0, 0.4))
	InkUI.nine(h, r, InkUI.tex("fill"), 32.0, Color(0.1, 0.085, 0.12, 0.95))
	InkUI.nine(h, r.grow(2.0), InkUI.tex("frame_line"), 48.0, Color(col, 0.9 if on else 0.35), 4.0)
	if on:
		var k := 0.5 + 0.5 * sin(t * 5.0)
		InkUI.nine(h, r.grow(3.5), InkUI.tex("frame_line"), 48.0, Color(InkUI.GOLD, 0.35 + 0.4 * k), 4.0)


static func _detay_panel(h: Control, r: Rect2, col: Color) -> void:
	InkUI.fancy_panel(h, r, Color(col, 0.75), Color(0.07, 0.06, 0.09, 0.96))


static func _satirlar(h: Control, x: float, y: float, w: float, s: String, col: Color, lh := 11.0, max_n := 99) -> float:
	var n := 0
	for ln in PixUI.wrap(s, w):
		if n >= max_n:
			break
		InkUI.text(h, Vector2(x, y), String(ln), col, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
		y += lh
		n += 1
	return y


static func _kod_yaratik(h: Control, area: Rect2, e: float, t: float) -> void:
	var ids := Kodeks.yaratiklar()
	var gw := 6 * 46.0
	var cells := _grid(h, Rect2(area.position, Vector2(gw, area.size.y)), ids.size(), 6, 42.0, t)
	for c in cells:
		var i := int(c[0])
		var r: Rect2 = c[1]
		var id := String(ids[i])
		var n := Kodeks.oldurme(id)
		var boss := Kodeks.boss_mu(id)
		_hucre(h, r, i == sec, InkUI.VERMILION if boss else InkUI.GOLD, t)
		var pr := r.grow(-3.0)
		if n > 0:
			Kodeks.portre(h, id, pr)
			InkUI.text(h, Vector2(r.position.x, r.end.y - 11.0), str(n), InkUI.BONE, 1, HORIZONTAL_ALIGNMENT_RIGHT, r.size.x - 3.0, 2)
			if Kodeks.zaaf_acik(id):
				InkUI.icon_at(h, "nisan", r.position + Vector2(7, 7), 8.0, InkUI.GOOD, false)
		else:
			Kodeks.portre(h, id, pr, Color(0.2, 0.18, 0.24, 0.9))
			InkUI.text(h, Vector2(r.position.x, r.position.y + 14.0), "?", Color(InkUI.MUTED, 0.6), 2, HORIZONTAL_ALIGNMENT_CENTER, r.size.x, 2)
	if ids.is_empty():
		return
	var id := String(ids[clampi(sec, 0, ids.size() - 1)])
	var d := Kodeks.def(id)
	var n := Kodeks.oldurme(id)
	var boss := Kodeks.boss_mu(id)
	var col := InkUI.VERMILION.lightened(0.2) if boss else InkUI.GOLD
	var pr := Rect2(area.position.x + gw + 14.0, area.position.y, area.end.x - area.position.x - gw - 14.0, area.size.y)
	_detay_panel(h, pr, col)
	var por := Rect2(pr.position.x + 10.0, pr.position.y + 8.0, 118.0, 104.0)
	InkUI.nine(h, por, InkUI.tex("fill"), 32.0, Color(0.13, 0.11, 0.15, 0.9))
	InkUI.splat(h, por.get_center() + Vector2(0, 20), 90.0, Color(col, 0.08), 0.3)
	if n > 0:
		Kodeks.portre(h, id, por.grow(-6.0))
	else:
		Kodeks.portre(h, id, por.grow(-6.0), Color(0, 0, 0, 0.92))
	var x := por.end.x + 10.0
	var w := pr.end.x - x - 10.0
	var nm := Kodeks.ad(id) if n > 0 else "???"
	InkUI.text(h, Vector2(x, pr.position.y + (6.0 if InkUI.width(nm, 2) <= w else 14.0)), nm, InkUI.BONE, 2 if InkUI.width(nm, 2) <= w else 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 2)
	var tur := "BOSS" if boss else "YARATIK"
	InkUI.text(h, Vector2(x, pr.position.y + 34.0), tur, col, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 1)
	InkUI.text(h, Vector2(x, pr.position.y + 48.0), "Devrilen: %d   ·   Seni devirdi: %d" % [n, Kodeks.devirme(id)], InkUI.MUTED, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
	var yy := pr.position.y + 62.0
	if n > 0:
		yy = _satirlar(h, x, yy, w, String(d.get("desc", "")), Color(InkUI.BONE, 0.9), 11.0, 5)
	else:
		yy = _satirlar(h, x, yy, w, "Ozan bu yaratığı henüz anlatmadı. Bir kez devir, sayfası açılsın.", Color(InkUI.MUTED, 0.8))
	var zy := maxf(yy + 6.0, por.end.y + 10.0)
	InkUI.divider(h, pr.position.x + 10.0, zy, pr.size.x - 20.0, Color(col, 0.5))
	InkUI.text(h, Vector2(pr.position.x + 10.0, zy + 6.0), "ZAAF", InkUI.GOOD if Kodeks.zaaf_acik(id) else InkUI.MUTED, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 1)
	var esik := Kodeks.BOSS_ZAAF_N if boss else Kodeks.ZAAF_N
	if Kodeks.zaaf_acik(id):
		_satirlar(h, pr.position.x + 50.0, zy + 6.0, pr.size.x - 62.0, Kodeks.zaaf(id), InkUI.BONE)
	else:
		InkUI.text(h, Vector2(pr.position.x + 50.0, zy + 6.0), "%d öldürmede açılır (%d / %d)" % [esik, mini(n, esik), esik], Color(InkUI.MUTED, 0.8), 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
		InkUI.bar(h, Rect2(pr.position.x + 50.0, zy + 20.0, 120.0, 4.0), float(n) / esik, InkUI.GOOD, Color(0.12, 0.1, 0.14))
	var by := zy + 46.0
	if Kodeks.bilgi_acik(id) and not boss:
		InkUI.text(h, Vector2(pr.position.x + 10.0, by), "BİLGİ", InkUI.GOLD, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 1)
		InkUI.text(h, Vector2(pr.position.x + 50.0, by), "Can %d · Hasar %d · Hız %d (1. derinlik)" % [int(d.get("hp", 0)), int(d.get("dmg", 0)), int(d.get("speed", 0))], InkUI.BONE, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
	elif not boss:
		InkUI.text(h, Vector2(pr.position.x + 10.0, by), "BİLGİ", InkUI.MUTED, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 1)
		InkUI.text(h, Vector2(pr.position.x + 50.0, by), "%d öldürmede açılır" % Kodeks.BILGI_N, Color(InkUI.MUTED, 0.8), 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
	# özet satırı
	var gor := 0
	for yid in ids:
		if Kodeks.oldurme(yid) > 0:
			gor += 1
	InkUI.text(h, Vector2(pr.position.x, pr.end.y - 16.0), "Görülen %d / %d   ·   zaafı bilinen %d   ·   toplam %d devirme" % [gor, ids.size(), Kodeks.zaaf_sayi(), Kodeks.toplam_oldurme()], Color(InkUI.MUTED, 0.85), 1, HORIZONTAL_ALIGNMENT_CENTER, pr.size.x, 0)


static func _kod_silah(h: Control, area: Rect2, e: float, t: float) -> void:
	var ids := Kodeks.silahlar()
	var gw := 6 * 46.0
	var cells := _grid(h, Rect2(area.position, Vector2(gw, area.size.y)), ids.size(), 6, 42.0, t)
	for c in cells:
		var i := int(c[0])
		var r: Rect2 = c[1]
		var id := String(ids[i])
		var base := Data.find_item(id)
		var gor := Kodeks.silah_gorulen(id)
		var rc := InkUI.GOLD if Game.is_unlocked(id) else InkUI.MUTED
		_hucre(h, r, i == sec, rc, t)
		var it := {"id": id, "material": "demir"}
		if gor:
			InkUI.weapon(h, it, r.get_center(), r.size - Vector2(10, 10))
		else:
			var d: Dictionary = Data.weapon_sprite(id, "demir")
			if d.get("linear", false):
				var reg: Rect2 = d["region"]
				var s := minf((r.size.x - 10.0) / reg.size.x, (r.size.y - 10.0) / reg.size.y)
				var sz := reg.size * minf(1.0, s)
				h.draw_texture_rect_region(d["tex"], Rect2(r.get_center() - sz * 0.5, sz), reg, Color(0.2, 0.18, 0.24, 0.9))
			InkUI.text(h, Vector2(r.position.x, r.position.y + 14.0), "?", Color(InkUI.MUTED, 0.55), 2, HORIZONTAL_ALIGNMENT_CENTER, r.size.x, 2)
		if Kodeks.kavanozda(id):
			InkUI.icon_at(h, "sise", r.position + Vector2(7, 7), 8.0, InkUI.TURQUOISE, false)
		var k := Kodeks.silah_oldurme(id)
		if k > 0:
			InkUI.text(h, Vector2(r.position.x, r.end.y - 11.0), str(k), InkUI.BONE, 1, HORIZONTAL_ALIGNMENT_RIGHT, r.size.x - 3.0, 2)
	if ids.is_empty():
		return
	var id := String(ids[clampi(sec, 0, ids.size() - 1)])
	var base := Data.find_item(id)
	var gor := Kodeks.silah_gorulen(id)
	var pr := Rect2(area.position.x + gw + 14.0, area.position.y, area.end.x - area.position.x - gw - 14.0, area.size.y)
	var og := Game.item_onguns(base)
	var col := PixUI.ongun_col(String(og[0])) if not og.is_empty() else InkUI.GOLD
	_detay_panel(h, pr, col)
	var wr := Rect2(pr.position.x + 10.0, pr.position.y + 8.0, 118.0, 80.0)
	InkUI.nine(h, wr, InkUI.tex("fill"), 32.0, Color(0.13, 0.11, 0.15, 0.9))
	if gor:
		InkUI.weapon(h, {"id": id, "material": "demir"}, wr.get_center(), wr.size - Vector2(16, 16))
	var x := wr.end.x + 10.0
	var w := pr.end.x - x - 10.0
	var snm := String(base.get("name", id)) if gor else "???"
	if InkUI.width(snm, 2) <= w:
		InkUI.text(h, Vector2(x, pr.position.y + 6.0), snm, InkUI.BONE, 2, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 2)
	else:
		InkUI.text(h, Vector2(x, pr.position.y + 14.0), snm, InkUI.BONE, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 2)
	var cat := String(HUD.CAT_TXT.get(_cat_of(id), "Silah"))
	var dur := "açık" if Game.is_unlocked(id) else ("parşömen bekliyor" if id in Game.meta.get("blueprints", []) else "kilitli (parşömeni bul)")
	InkUI.text(h, Vector2(x, pr.position.y + 34.0), "%s · %s" % [cat, dur], col, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 1)
	PixUI.ongun_stripe(h, Rect2(x, pr.position.y + 48.0, 40.0, 3.0), og, String(og[0]) if not og.is_empty() else "")
	InkUI.text(h, Vector2(x + 48.0, pr.position.y + 44.0), "Bu silahla devrilen: %d%s" % [Kodeks.silah_oldurme(id), "   ·   kavanozda" if Kodeks.kavanozda(id) else ""], InkUI.MUTED, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
	var yy := pr.position.y + 60.0
	if gor:
		if base.has("dmg"):
			InkUI.text(h, Vector2(x, yy), "Taban hasar %s · saniyede %s savuruş · kritik %%%d" % [ItemGen.fmt(float(base.get("dmg", 0))), ItemGen.fmt(float(base.get("aps", 1.0))), int(float(base.get("crit", 0.0)) * (100.0 if float(base.get("crit", 0.0)) <= 1.0 else 1.0))], InkUI.BONE, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
			yy += 12.0
		var md := String(base.get("crit_desc", base.get("mech", "")))
		if md != "":
			yy = _satirlar(h, pr.position.x + 10.0, maxf(yy, wr.end.y + 8.0), pr.size.x - 20.0, "Kritik: " + md, InkUI.GOLD)
		var ds := String(base.get("desc", ""))
		if ds != "":
			_satirlar(h, pr.position.x + 10.0, maxf(yy + 4.0, wr.end.y + 8.0), pr.size.x - 20.0, ds, Color(InkUI.BONE, 0.9), 11.0, 6)
	else:
		_satirlar(h, pr.position.x + 10.0, wr.end.y + 10.0, pr.size.x - 20.0, "Henüz eline geçmedi. Bölümlerde, sandıklarda, Bezirgân'ın kilimi üstünde ya da Demirci'nin ocağında bulunur.", Color(InkUI.MUTED, 0.85))
	var gs := 0
	for sid in ids:
		if Kodeks.silah_gorulen(sid):
			gs += 1
	InkUI.text(h, Vector2(pr.position.x, pr.end.y - 16.0), "Görülen %d / %d eşya" % [gs, ids.size()], Color(InkUI.MUTED, 0.85), 1, HORIZONTAL_ALIGNMENT_CENTER, pr.size.x, 0)


static func _cat_of(id: String) -> String:
	for cat in ["weapons", "shields", "gadgets"]:
		for it in Data.items.get(cat, []):
			if String(it.get("id", "")) == id:
				return cat
	return "weapons"


static func _kod_damga(h: Control, area: Rect2, e: float, t: float) -> void:
	var ids := Damga.ids()
	var gw := 5 * 50.0
	var cells := _grid(h, Rect2(area.position, Vector2(gw, area.size.y)), ids.size(), 5, 46.0, t)
	for c in cells:
		var i := int(c[0])
		var r: Rect2 = c[1]
		var id := String(ids[i])
		var col := Damga.renk(id)
		var al := Kodeks.damga_alinan(id)
		var gor := Kodeks.damga_gorulen(id)
		_hucre(h, r, i == sec, col if gor else InkUI.MUTED, t)
		tamga(h, id, r.get_center(), 32.0, Color(col, 1.0) if al > 0 else (Color(col, 0.35) if gor else Color(0, 0, 0, 0.9)))
		if al > 0:
			InkUI.text(h, Vector2(r.position.x, r.end.y - 11.0), str(al), InkUI.BONE, 1, HORIZONTAL_ALIGNMENT_RIGHT, r.size.x - 3.0, 2)
		if Damga.has(id):
			InkUI.icon_at(h, "yildiz", r.position + Vector2(8, 8), 8.0, InkUI.GOLD, false)
	var id := String(ids[clampi(sec, 0, ids.size() - 1)])
	var d: Array = Damga.D[id]
	var col := Damga.renk(id)
	var gor := Kodeks.damga_gorulen(id)
	var pr := Rect2(area.position.x + gw + 14.0, area.position.y, area.end.x - area.position.x - gw - 14.0, area.size.y)
	_detay_panel(h, pr, col)
	var c0 := Vector2(pr.position.x + 50.0, pr.position.y + 46.0)
	InkUI.ring(h, c0, 32.0, 1.0 if gor else 0.0, Color(col, 0.6))
	tamga(h, id, c0, 50.0, col if gor else Color(0, 0, 0, 0.9))
	var x := pr.position.x + 96.0
	InkUI.text(h, Vector2(x, pr.position.y + 10.0), String(d[0]) if gor else "???", InkUI.BONE, 2, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 2)
	var og := String(d[2])
	InkUI.text(h, Vector2(x, pr.position.y + 38.0), (("%s tomarıyla uyumlu" % String(Data.items["ongun"][og]["name"])) if og != "" else "Renksiz") + (" · nadir" if bool(d[3]) else ""), col, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 1)
	InkUI.text(h, Vector2(x, pr.position.y + 52.0), "Vurulma: %d kez%s" % [Kodeks.damga_alinan(id), "   ·   şu an üzerinde" if Damga.has(id) else ""], InkUI.MUTED, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
	var yy := pr.position.y + 92.0
	if gor:
		InkUI.text(h, Vector2(pr.position.x + 10.0, yy), "ETKİ", InkUI.GOLD, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 1)
		yy = _satirlar(h, pr.position.x + 52.0, yy, pr.size.x - 64.0, String(d[4]), InkUI.BONE)
		yy += 6.0
		InkUI.text(h, Vector2(pr.position.x + 10.0, yy), "ÜSLUP", InkUI.GOLD, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 1)
		InkUI.text(h, Vector2(pr.position.x + 52.0, yy), String(d[5]), InkUI.BONE, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
		yy += 18.0
		if og != "":
			yy = _satirlar(h, pr.position.x + 10.0, yy, pr.size.x - 20.0, "Uyum: %s tomarı en öndeyken (en az 1) bu Damganın gücü x1,25." % String(Data.items["ongun"][og]["name"]), Color(InkUI.GOOD, 0.9))
		_satirlar(h, pr.position.x + 10.0, yy + 6.0, pr.size.x - 20.0, "«%s»" % String(d[6]), Color(InkUI.MUTED, 0.85))
	else:
		_satirlar(h, pr.position.x + 10.0, yy, pr.size.x - 20.0, "Bu tamga henüz Damga Taşı'nda belirmedi. Konaklarda Bengisu'nun taşına uğra.", Color(InkUI.MUTED, 0.85))
	var al_n := 0
	for did in ids:
		if Kodeks.damga_alinan(did) > 0:
			al_n += 1
	InkUI.text(h, Vector2(pr.position.x, pr.end.y - 16.0), "Vurulan %d / %d Damga   ·   %d yuva açık" % [al_n, ids.size(), Damga.yuva()], Color(InkUI.MUTED, 0.85), 1, HORIZONTAL_ALIGNMENT_CENTER, pr.size.x, 0)


static func _kod_destan(h: Control, area: Rect2, e: float, t: float) -> void:
	var rows := Kodeks.destan_kayitlari()
	var lw := 240.0
	var rh := 18.0
	var vis := int(floor(area.size.y / rh))
	if sec < kaydir:
		kaydir = sec
	if sec >= kaydir + vis:
		kaydir = sec - vis + 1
	for j in vis:
		var i := kaydir + j
		if i >= rows.size():
			break
		var rw: Array = rows[i]
		var r := Rect2(area.position.x + 12.0, area.position.y + j * rh, lw - 12.0, rh - 3.0)
		var acik := bool(rw[2])
		var col := InkUI.GOLD if String(rw[3]) == "orgu" else (InkUI.TURQUOISE if String(rw[3]) == "gorum" else InkUI.BONE)
		if i == sec:
			InkUI.select_mark(h, r, col, t)
		InkUI.text(h, Vector2(r.position.x + 6.0, r.position.y + 2.0), String(rw[0]) if acik else "· · ·", Color(col, 1.0 if acik else 0.4), 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
	if rows.is_empty():
		return
	var rw: Array = rows[clampi(sec, 0, rows.size() - 1)]
	var pr := Rect2(area.position.x + lw + 10.0, area.position.y, area.end.x - area.position.x - lw - 10.0, area.size.y)
	InkUI.scroll_frame(h, pr, 0.95)
	var acik := bool(rw[2])
	var ink := Color(0.1, 0.07, 0.06)
	InkUI.text(h, Vector2(pr.position.x + 24.0, pr.position.y + 18.0), String(rw[0]) if acik else "Bilinmeyen sayfa", ink, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
	var f := InkUI.font("lore")
	var y := pr.position.y + 44.0
	var txt := String(rw[1]) if acik else ("Bu sayfa Gün Ana'nın görümüyle açılır." if String(rw[3]) != "orgu" else "Bu örgü bir bossun elinde. Onu devir, örgüyü Gün Ana'ya döndür.")
	for ln in InkHUD.wrap_f(txt, f, 12, pr.size.x - 52.0):
		h.draw_string(f, Vector2(pr.position.x + 24.0, y), String(ln), HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color(ink, 0.92 if acik else 0.5))
		y += 16.0
	var n := 0
	for r2 in rows:
		if bool(r2[2]):
			n += 1
	InkUI.text(h, Vector2(area.position.x, area.end.y - 6.0), "Açılan %d / %d sayfa" % [n, rows.size()], Color(InkUI.MUTED, 0.85), 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)


static func _kod_basarim(h: Control, area: Rect2, e: float, t: float) -> void:
	var ids: Array = Basarim.B.keys()
	var gw := 5 * 50.0
	var cells := _grid(h, Rect2(area.position, Vector2(gw, area.size.y)), ids.size(), 5, 46.0, t)
	for c in cells:
		var i := int(c[0])
		var r: Rect2 = c[1]
		var id := String(ids[i])
		var ac := Basarim.acik(id)
		_hucre(h, r, i == sec, InkUI.VERMILION if ac else InkUI.MUTED, t)
		rozet(h, id, r.get_center(), 34.0, ac)
	var id := String(ids[clampi(sec, 0, ids.size() - 1)])
	var b: Array = Basarim.B[id]
	var ac := Basarim.acik(id)
	var pr := Rect2(area.position.x + gw + 14.0, area.position.y, area.end.x - area.position.x - gw - 14.0, area.size.y)
	_detay_panel(h, pr, InkUI.VERMILION if ac else InkUI.MUTED)
	rozet(h, id, Vector2(pr.position.x + 46.0, pr.position.y + 44.0), 64.0, ac)
	var x := pr.position.x + 92.0
	InkUI.text(h, Vector2(x, pr.position.y + 12.0), String(b[0]), InkUI.BONE if ac else Color(InkUI.BONE, 0.6), 2, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 2)
	InkUI.text(h, Vector2(x, pr.position.y + 40.0), "AÇILDI" if ac else "KAPALI", InkUI.GOOD if ac else InkUI.MUTED, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 1)
	if ac:
		var ts := int(Game.meta.get("basarim", {}).get(id, 0))
		if ts > 0:
			var dt := Time.get_datetime_dict_from_unix_time(ts)
			InkUI.text(h, Vector2(x + 52.0, pr.position.y + 40.0), "%02d.%02d.%d" % [int(dt["day"]), int(dt["month"]), int(dt["year"])], InkUI.MUTED, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
	var yy := pr.position.y + 92.0
	yy = _satirlar(h, pr.position.x + 12.0, yy, pr.size.x - 24.0, String(b[1]), InkUI.BONE)
	yy += 8.0
	InkUI.text(h, Vector2(pr.position.x + 12.0, yy), "ÖDÜL", InkUI.GOLD, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 1)
	match String(b[3]):
		"renk":
			var rid := String(b[4])
			var rc: Color = Basarim.RENK[rid][1]
			h.draw_rect(Rect2(pr.position.x + 54.0, yy + 1.0, 22.0, 9.0), rc)
			InkUI.text(h, Vector2(pr.position.x + 82.0, yy), "HUD çerçeve rengi: %s%s" % [String(Basarim.RENK[rid][0]), "  (seçili)" if String(Game.meta.get("hud_renk", "")) == rid else ""], InkUI.BONE, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
		"soz":
			_satirlar(h, pr.position.x + 54.0, yy, pr.size.x - 66.0, String(b[4]) if ac else "Ozan'ın bir dizesi (açılınca)", Color(InkUI.BONE, 0.9 if ac else 0.6))
		"kut":
			InkUI.text(h, Vector2(pr.position.x + 54.0, yy), "+%d Kut (Umay'ın bankasına)" % int(b[4]), InkUI.TURQUOISE, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
	InkUI.text(h, Vector2(pr.position.x, pr.end.y - 16.0), "Açılan %d / %d başarım" % [Basarim.acik_sayi(), ids.size()], Color(InkUI.MUTED, 0.85), 1, HORIZONTAL_ALIGNMENT_CENTER, pr.size.x, 0)


static func _kod_rekor(h: Control, area: Rect2, e: float, t: float) -> void:
	var rk: Dictionary = Game.meta.get("rekor", {}) if Game.meta.get("rekor") is Dictionary else {}
	var lw := 286.0
	var lp := Rect2(area.position.x + 6.0, area.position.y + 4.0, lw, 150.0)
	_detay_panel(h, lp, InkUI.GOLD)
	InkUI.text(h, Vector2(lp.position.x + 10.0, lp.position.y + 6.0), "DESTAN REKORLARI", InkUI.GOLD, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 1)
	var yy := lp.position.y + 24.0
	var ikon := {"derinlik": "harita", "oldurme": "kafatasi", "kombo": "davul", "en_iyi": "hiz", "verilen": "kilic", "hizli_zafer": "zaman"}
	for k in KosuOzet.REKOR:
		InkUI.icon_at(h, String(ikon[k]), Vector2(lp.position.x + 18.0, yy + 6.0), 11.0, InkUI.GOLD)
		InkUI.text(h, Vector2(lp.position.x + 30.0, yy), String(KosuOzet.REKOR_AD[k]), InkUI.BONE, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
		InkUI.text(h, Vector2(lp.position.x, yy), KosuOzet.rekor_txt(k, float(rk.get(k, -1.0))), InkUI.GOLD, 1, HORIZONTAL_ALIGNMENT_RIGHT, lw - 12.0, 2)
		yy += 18.0
	InkUI.text(h, Vector2(lp.position.x + 10.0, lp.end.y - 14.0), "%d koşu · %d zafer" % [int(Game.meta.get("runs", 0)), int(Game.meta.get("wins", 0))], InkUI.MUTED, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
	# Mühür kademelerine göre
	var rp := Rect2(lp.end.x + 14.0, lp.position.y, area.end.x - lp.end.x - 20.0, 150.0)
	_detay_panel(h, rp, InkUI.VERMILION)
	InkUI.text(h, Vector2(rp.position.x + 10.0, rp.position.y + 6.0), "KUT MÜHRÜNE GÖRE", InkUI.VERMILION.lightened(0.3), 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 1)
	var cx := [rp.position.x + 10.0, rp.position.x + 62.0, rp.position.x + 128.0, rp.position.x + 196.0]
	var hy := rp.position.y + 22.0
	for j in 4:
		InkUI.text(h, Vector2(cx[j], hy), ["MÜHÜR", "DERİN", "ÖLDÜRME", "ZAFER"][j], InkUI.MUTED, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 1)
	var rm: Dictionary = Game.meta.get("rekor_m", {}) if Game.meta.get("rekor_m") is Dictionary else {}
	var mk: Variant = Game.meta.get("muhur_kayit")
	var ry := hy + 14.0
	var kademeler: Array = []
	for key in rm.keys():
		kademeler.append(int(key))
	if mk is Dictionary:
		for key in (mk as Dictionary).keys():
			if not (int(key) in kademeler):
				kademeler.append(int(key))
	kademeler.sort()
	if kademeler.is_empty():
		InkUI.text(h, Vector2(rp.position.x + 10.0, ry), "Henüz kayıt yok: bir koşuyu bitir.", Color(InkUI.MUTED, 0.8), 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
	for m in kademeler.slice(0, 7):
		var r: Dictionary = rm.get(str(m), {})
		var exv: Variant = (mk as Dictionary).get(str(m), (mk as Dictionary).get(m, {})) if mk is Dictionary else {}
		var ext: Dictionary = exv if exv is Dictionary else {}
		var dep := maxf(float(r.get("derinlik", -1.0)), float(ext.get("derinlik", ext.get("best_depth", -1.0))))
		var zf := float(r.get("hizli_zafer", float(ext.get("sure", ext.get("en_hizli", -1.0)))))
		InkUI.text(h, Vector2(cx[0], ry), "%d. mühür" % m if m > 0 else "mühürsüz", InkUI.BONE, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
		InkUI.text(h, Vector2(cx[1], ry), str(int(dep)) if dep > 0 else "—", InkUI.GOLD, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
		InkUI.text(h, Vector2(cx[2], ry), str(int(float(r.get("oldurme", -1.0)))) if float(r.get("oldurme", -1.0)) > 0 else "—", InkUI.BONE, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
		InkUI.text(h, Vector2(cx[3], ry), KosuOzet.sure_txt(zf) if zf > 0 else "—", InkUI.GOOD if zf > 0 else InkUI.MUTED, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
		ry += 14.0
	# son koşular: derinlik sütunları
	var gp := Rect2(area.position.x + 6.0, lp.end.y + 16.0, area.size.x - 12.0, area.end.y - lp.end.y - 22.0)
	_detay_panel(h, gp, InkUI.TURQUOISE)
	InkUI.text(h, Vector2(gp.position.x + 10.0, gp.position.y + 4.0), "SON KOŞULAR", InkUI.TURQUOISE, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 1)
	var g: Array = Game.meta.get("gecmis", []) if Game.meta.get("gecmis") is Array else []
	var bw := 36.0
	var base_y := gp.end.y - 16.0
	var maxd := 10.0
	for r in g:
		maxd = maxf(maxd, float(r.get("d", 1)))
	for i in g.size():
		var r: Dictionary = g[i]
		var hh := (gp.size.y - 40.0) * float(r.get("d", 1)) / maxd
		var bx := gp.position.x + 16.0 + i * (bw + 9.0)
		var col := InkUI.GOLD if bool(r.get("z", false)) else InkUI.TURQUOISE
		h.draw_rect(Rect2(bx + 1.5, base_y - hh + 2.0, bw, hh), Color(0, 0, 0, 0.35))
		h.draw_rect(Rect2(bx, base_y - hh, bw, hh), Color(col.darkened(0.55), 0.85))
		h.draw_rect(Rect2(bx, base_y - hh, bw, hh), Color(col, 0.55), false, 1.0)
		InkUI.rect(h, Rect2(bx - 1.0, base_y - hh - 1.0, bw + 2.0, 2.4), Color(col, 0.95))
		InkUI.text(h, Vector2(bx, base_y - hh - 12.0), str(int(r.get("d", 1))), InkUI.BONE, 1, HORIZONTAL_ALIGNMENT_CENTER, bw, 2)
		InkUI.text(h, Vector2(bx, base_y + 2.0), KosuOzet.sure_txt(float(r.get("t", 0))), InkUI.MUTED, 1, HORIZONTAL_ALIGNMENT_CENTER, bw, 0)
		var dm: Array = r.get("dm", [])
		for j in mini(dm.size(), 3):
			tamga(h, String(dm[j]), Vector2(bx + 7.0 + j * 11.0, base_y - 7.0), 10.0, Damga.renk(String(dm[j])), false)
	if g.is_empty():
		InkUI.text(h, Vector2(gp.position.x, gp.get_center().y - 6.0), "İlk koşun Ozan'ın defterine burada yazılacak.", Color(InkUI.MUTED, 0.8), 1, HORIZONTAL_ALIGNMENT_CENTER, gp.size.x, 0)


# ================================================================== koşu özeti (ölüm / zafer)
static func ciz_ozet(h: Control, vp: Vector2, zafer: bool) -> void:
	var oz: Dictionary = son_ozet
	if oz.is_empty() and not Game.run.is_empty():
		oz = Game.run.get("ozet", {})
	var e: float = h._ease_open()
	var t: float = h._t
	var col := Color(1.0, 0.55, 0.45) if not zafer else InkUI.GOLD
	if zafer:
		h._dim(vp, 0.85, Color(0.06, 0.04, 0.02))
		h._title(vp, 26, "TAN SÖKTÜ", col, "Erlik Han devrildi, Gün Ana yükseldi. Ozan bu koşuyu destanına yazdı.")
	else:
		h._dim(vp, 0.8, Color(0.05, 0.01, 0.03))
		InkHUD.dead_backdrop(h, vp, e)
		h._title(vp, 26, "RUH KUŞUN DALA KONMADI", col, Hikaye.olum_satiri())
	# karolar
	var tiles := [["harita", "%d" % int(oz.get("derinlik", 1)), "DERİNLİK", col], ["zaman", KosuOzet.sure_txt(float(oz.get("sure", 0.0))), "SÜRE", PixUI.KUT],
		["kafatasi", "%d" % int(oz.get("oldurme", 0)), "DÜŞMAN", Color(1.0, 0.5, 0.42)], ["altin", "%d" % int(oz.get("altin", 0)), "ALTIN", PixUI.GOLD]]
	var tw := 104.0
	var tx := roundf((vp.x - (tw * 4 + 8.0 * 3)) * 0.5)
	var yeni: Array = oz.get("yeni", [])
	for i in 4:
		var tl: Array = tiles[i]
		var r := Rect2(tx + i * (tw + 8.0), 68.0 + (1.0 - e) * (8.0 + i * 4.0), tw, 32.0)
		InkUI.stat_tile(h, r, String(tl[0]), String(tl[1]), String(tl[2]), tl[3], clampf(e * 1.5 - i * 0.15, 0.0, 1.0))
		var rk: String = ["derinlik", "hizli_zafer", "oldurme", ""][i]
		if rk != "" and rk in yeni:
			_rekor_mohur(h, r.position + Vector2(r.size.x - 14.0, 2.0), t)
	var py := 112.0
	var ph := 184.0
	# sol: seni deviren / devrilen
	var lp := Rect2(20.0, py, 176.0, ph)
	var neden := String(oz.get("neden", ""))
	if zafer:
		neden = "erlik_han"
	_detay_panel(h, lp, col)
	InkUI.text(h, Vector2(lp.position.x, lp.position.y + 4.0), "SON DÜŞMAN" if zafer else "SENİ DEVİREN", col, 1, HORIZONTAL_ALIGNMENT_CENTER, lp.size.x, 1)
	var por := Rect2(lp.position.x + 14.0, lp.position.y + 20.0, lp.size.x - 28.0, 108.0)
	InkUI.splat(h, por.get_center() + Vector2(0, 16), 120.0, Color(col, 0.1), 0.6)
	var ciz := neden != "" and neden != "tehlike" and Kodeks.portre(h, neden, por)
	if not ciz:
		InkUI.icon_at(h, "kafatasi", por.get_center(), 54.0, Color(col, 0.8))
	var nm := Kodeks.ad(neden) if (neden != "" and neden != "tehlike") else ("Tuzak ve tehlike" if neden == "tehlike" else "—")
	InkUI.text(h, Vector2(lp.position.x, por.end.y + 4.0), nm, InkUI.BONE, 2, HORIZONTAL_ALIGNMENT_CENTER, lp.size.x, 2)
	if neden != "" and neden != "tehlike" and not zafer:
		InkUI.text(h, Vector2(lp.position.x, por.end.y + 32.0), "seni %d kez devirdi" % Kodeks.devirme(neden), InkUI.MUTED, 1, HORIZONTAL_ALIGNMENT_CENTER, lp.size.x, 0)
		if Kodeks.zaaf_acik(neden):
			InkUI.text(h, Vector2(lp.position.x, por.end.y + 44.0), "zaafı destanda yazılı (C)", InkUI.GOOD, 1, HORIZONTAL_ALIGNMENT_CENTER, lp.size.x, 0)
		else:
			InkUI.text(h, Vector2(lp.position.x, por.end.y + 44.0), "zaafı için %d öldürme gerek" % maxi(0, Kodeks.ZAAF_N - Kodeks.oldurme(neden)) if not Kodeks.boss_mu(neden) else "devirince zaafı yazılır", Color(InkUI.MUTED, 0.8), 1, HORIZONTAL_ALIGNMENT_CENTER, lp.size.x, 0)
	# orta: istatistik satırları
	var mp := Rect2(lp.end.x + 14.0, py, 214.0, ph)
	_detay_panel(h, mp, InkUI.GOLD)
	InkUI.text(h, Vector2(mp.position.x, mp.position.y + 4.0), "KOŞUNUN TARTISI", InkUI.GOLD, 1, HORIZONTAL_ALIGNMENT_CENTER, mp.size.x, 1)
	var rows := [
		["kilic", "Verilen hasar", ItemGen.fmt(float(oz.get("verilen", 0.0))), "verilen"],
		["can", "Alınan hasar", ItemGen.fmt(float(oz.get("alinan", 0.0))), ""],
		["hiz", "En ağır vuruş", "%s%s" % [ItemGen.fmt(float(oz.get("en_iyi", 0.0))), "" if String(oz.get("en_iyi_silah", "")) == "" else ""], "en_iyi"],
		["davul", "En yüksek kombo", "x%d" % int(oz.get("kombo", 0)), "kombo"],
		["yildiz", "Seçkin devrilen", str(int(oz.get("seckin", 0))), ""],
		["kut", "Toplanan Kut", str(int(oz.get("kut", 0))), ""],
		["muhur", "Sınav mührü · otağ", "%d · %d" % [int(oz.get("sinav", 0)), int(oz.get("otag", 0))], ""],
		["tilsim", "Okunan tomar", str(int(oz.get("tomar", 0))), ""],
	]
	var ry := mp.position.y + 20.0
	for i in rows.size():
		var rw: Array = rows[i]
		var a := clampf(e * 2.0 - i * 0.1, 0.0, 1.0)
		InkUI.icon_at(h, String(rw[0]), Vector2(mp.position.x + 14.0, ry + 6.0), 10.0, Color(InkUI.GOLD, a))
		InkUI.text(h, Vector2(mp.position.x + 26.0, ry), String(rw[1]), Color(InkUI.BONE, 0.92 * a), 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
		InkUI.text(h, Vector2(mp.position.x, ry), String(rw[2]), Color(InkUI.GOLD, a), 1, HORIZONTAL_ALIGNMENT_RIGHT, mp.size.x - 12.0, 2)
		if String(rw[3]) != "" and String(rw[3]) in yeni:
			_rekor_mohur(h, Vector2(mp.end.x - 12.0 - InkUI.width(String(rw[2])) - 24.0, ry + 5.0), t)
		ry += 16.0
	if String(oz.get("en_iyi_silah", "")) != "":
		InkUI.text(h, Vector2(mp.position.x, ry + 2.0), "en ağır vuruş: %s" % String(oz["en_iyi_silah"]), Color(InkUI.MUTED, 0.85), 1, HORIZONTAL_ALIGNMENT_CENTER, mp.size.x, 0)
	# sağ: av defteri
	var rp := Rect2(mp.end.x + 14.0, py, vp.x - mp.end.x - 34.0, ph)
	_detay_panel(h, rp, Color(1.0, 0.5, 0.42))
	InkUI.text(h, Vector2(rp.position.x, rp.position.y + 4.0), "AV DEFTERİ", Color(1.0, 0.6, 0.5), 1, HORIZONTAL_ALIGNMENT_CENTER, rp.size.x, 1)
	var turler: Dictionary = oz.get("turler", {})
	var ks: Array = turler.keys()
	ks.sort_custom(func(a: Variant, b: Variant) -> bool: return int(turler[a]) > int(turler[b]))
	var ay := rp.position.y + 20.0
	for i in mini(ks.size(), 6):
		var id := String(ks[i])
		var cr := Rect2(rp.position.x + 8.0, ay, 24.0, 24.0)
		InkUI.nine(h, cr, InkUI.tex("fill"), 32.0, Color(0.12, 0.1, 0.14, 0.9))
		Kodeks.portre(h, id, cr.grow(-2.0))
		InkUI.text(h, Vector2(cr.end.x + 6.0, ay + 6.0), Kodeks.ad(id), InkUI.BONE, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
		InkUI.text(h, Vector2(rp.position.x, ay + 6.0), "x%d" % int(turler[id]), Color(1.0, 0.6, 0.5), 1, HORIZONTAL_ALIGNMENT_RIGHT, rp.size.x - 10.0, 2)
		ay += 26.0
	if ks.is_empty():
		InkUI.text(h, Vector2(rp.position.x, rp.get_center().y - 6.0), "Kimse devrilmedi.", Color(InkUI.MUTED, 0.8), 1, HORIZONTAL_ALIGNMENT_CENTER, rp.size.x, 0)
	elif ks.size() > 6:
		InkUI.text(h, Vector2(rp.position.x, rp.end.y - 14.0), "+%d tür daha" % (ks.size() - 6), Color(InkUI.MUTED, 0.8), 1, HORIZONTAL_ALIGNMENT_CENTER, rp.size.x, 0)
	# alt şerit: Damgalar ve silahlar, Kut
	var by := py + ph + 12.0
	var dm: Array = oz.get("damga", [])
	var bx := 24.0
	InkUI.text(h, Vector2(bx, by), "DAMGALAR", InkUI.MUTED, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 1)
	bx += 62.0
	if dm.is_empty():
		InkUI.text(h, Vector2(bx, by), "—", InkUI.MUTED, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
		bx += 20.0
	for id in dm:
		var dc := Damga.renk(String(id))
		tamga(h, String(id), Vector2(bx + 6.0, by + 5.0), 14.0, dc)
		InkUI.text(h, Vector2(bx + 15.0, by), Damga.ad(String(id)), dc.lightened(0.2), 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
		bx += 22.0 + InkUI.width(Damga.ad(String(id)))
	var sl: Array = oz.get("silahlar", [])
	var stxt := "SİLAHLAR  " + (", ".join(sl.slice(0, 4)) if not sl.is_empty() else "—")
	InkUI.text(h, Vector2(0, by), stxt, Color(InkUI.BONE, 0.85), 1, HORIZONTAL_ALIGNMENT_RIGHT, vp.x - 24.0, 0)
	var kl := int(Game.run.get("kut_lost", 0)) if not zafer else 0
	var info := ("Taşıdığın %d Kut yitti. %s" % [kl, String(h.flash_msg) if String(h.flash_msg).begins_with("Ruh") else ""]) if not zafer else "Kut Umay'ın bankasına ulaştı."
	InkUI.text(h, Vector2(0, by + 14.0), info + "   ·   Kut bankası %d" % int(Game.meta.get("kut_bank", 0)), Color(0.6, 0.95, 1.0, 0.9), 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x, 0)
	if not yeni.is_empty():
		var yr := "YENİ REKOR: " + ", ".join(yeni.map(func(k: Variant) -> String: return String(KosuOzet.REKOR_AD.get(k, k))))
		InkUI.text(h, Vector2(0, by - 12.0 - 2.0), yr, Color(InkUI.VERMILION.lightened(0.35), 0.75 + 0.25 * sin(t * 4.0)), 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x, 1)
	h._hint(vp, [["Boşluk", "yola devam" if zafer else "yeniden doğ"], ["C", "rekorlar ve destan"]])
	h._reveal(vp)


static func _rekor_mohur(h: Control, c: Vector2, t: float) -> void:
	## Küçük kızıl "REKOR" mührü (eğik)
	var w := InkUI.width("REKOR") + 8.0
	h.draw_set_transform(c * HUD.MENU_SCALE, -0.22, Vector2.ONE * HUD.MENU_SCALE * (1.0 + 0.04 * sin(t * 5.0)))
	InkUI.seal(h, Rect2(-w * 0.5, -6.0, w, 13.0), Color(InkUI.VERMILION, 0.95))
	InkUI.text(h, Vector2(-w * 0.5, -5.0), "REKOR", InkUI.PAPER, 1, HORIZONTAL_ALIGNMENT_CENTER, w, 0)
	h.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE * HUD.MENU_SCALE)
