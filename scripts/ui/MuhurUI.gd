class_name MuhurUI
extends RefCounted
## v44 Mühür yolu arayüzü (HUD üstüne çizer; girdi Main._unhandled_input):
##   * "muhur"  Mühür Taşı ekranı: solda altı mühür (açık / kilitli, zafer imi, en iyi süre), sağda seçilenin kuralları
##              (birikimli), zorluk sayıları, ödülleri (Kut / altın / nadirlik / emanet / ilk zafer / süs) ve kaydı.
##              Kilitli mühür de gösterilir (ne getireceği görünsün): "Erlik'i <önceki> ile yen".
##   * zafer özeti v44 birleştirmesinde DerinlikUI.ciz_ozet'e taşındı (koşu özeti + _ozet_muhur: mühür, süre / rekor,
##     ilk zafer Kut'u, açılan mühür, emanet, süs).
##   * HUD: sağ üstte, yer adının solunda koşunun mühür damgası (renkli yuvarlak mühür + Roma rakamı).

const SATIR_H := 34.0


static func ac(main: Node) -> void:
	var hud: Node = main.hud
	hud.sel = Zorluk.muhur_secili()
	hud.mode = "muhur"
	hud.open_anim()
	main.get_tree().paused = true
	Ses.play("ui_ac")
	Ses.play("sin_muhur", -10.0, 1.1)


static func girdi(main: Node, event: InputEvent, go: bool) -> void:
	var hud: Node = main.hud
	if event.is_action_pressed("yukari"):
		hud.sel = posmod(int(hud.sel) - 1, MuhurYolu.EN_COK + 1)
		Ses.play("ui_gez")
	elif event.is_action_pressed("asagi"):
		hud.sel = posmod(int(hud.sel) + 1, MuhurYolu.EN_COK + 1)
		Ses.play("ui_gez")
	elif event.is_action_pressed("techizat1"):
		MuhurYolu.sus_sec(1)
		if main.level and main.level.player:
			MuhurYolu.sus_uygula(main.level.player)
		Ses.play("ui_onay")
	elif go:
		var n := int(hud.sel)
		if n <= Zorluk.muhur_acik():
			MuhurYolu.sec(n)
			Ses.play("sin_muhur", -4.0)
			hud.flash_msg = "%s takıldı. Kut Kapısı'ndan geçince koşu bu mühürle başlar." % MuhurYolu.ad(n)
			hud.flash_t = 3.0
		else:
			Ses.play("ui_sec", 0.0, 0.7)
			hud.flash_msg = "Bu mühür kilitli: Erlik Han'ı %s ile yen." % MuhurYolu.ad(n - 1)
			hud.flash_t = 2.5
	elif event.is_action_pressed("duraklat") or event.is_action_pressed("yuvarlan") or event.is_action_pressed("ayarlar"):
		Ses.play("ui_iptal")
		main._start_play()


# ------------------------------------------------------------------ Mühür Taşı ekranı
static func ciz(h: Control, vp: Vector2) -> void:
	h._dim(vp, 0.84, Color(0.03, 0.02, 0.04))
	var e: float = h._ease_open()
	h._title(vp, 18, "MÜHÜR TAŞI", Color(1.0, 0.72, 0.45), "«%s»" % MuhurYolu.satir("ekran", int(Game.meta.get("runs", 0))))
	var acik := Zorluk.muhur_acik()
	var secili := Zorluk.muhur_secili()
	var sel := clampi(int(h.sel), 0, MuhurYolu.EN_COK)
	var t: float = h._t
	# --- sol: mühür listesi
	var lx := roundf(vp.x * 0.5 - 300.0)
	var y := 64.0 + (1.0 - e) * 8.0
	for n in MuhurYolu.EN_COK + 1:
		var col := MuhurYolu.renk(n)
		var kilit := n > acik
		var r := Rect2(lx, y, 214, SATIR_H - 4)
		var is_sel := n == sel
		PixUI.panel(h, r, (col if is_sel else PixUI.EDGE.darkened(0.45)), Color(0.08, 0.06, 0.08, 0.95) if is_sel else PixUI.INK, false)
		if is_sel:
			InkUI.select_mark(h, r, col, t)
		var sc := Vector2(lx + 16, y + 15)
		if kilit:
			h.draw_arc(sc, 9.0, 0, TAU, 18, Color(col, 0.35), 1.2, true)
			PixUI.text(h, sc + Vector2(-10, -6), "?", Color(PixUI.DIM, 0.6), 1, HORIZONTAL_ALIGNMENT_CENTER, 20, 0)
		else:
			InkUI.seal_round(h, sc, 22.0, col.darkened(0.1), float(n) * 0.6)
			PixUI.text(h, sc + Vector2(-10, -6), MuhurYolu.ROMA[n], Color(0.08, 0.04, 0.03), 1, HORIZONTAL_ALIGNMENT_CENTER, 20, 0)
		var adc := (PixUI.TEXT if not kilit else Color(PixUI.DIM, 0.7))
		PixUI.text(h, Vector2(lx + 32, y + 3), MuhurYolu.ad(n), adc)
		var alt := MuhurYolu.kural_ad(n) if n > 0 else "Kural yok"
		PixUI.text(h, Vector2(lx + 32, y + 15), alt, Color(col.lerp(PixUI.DIM, 0.45), 0.9 if not kilit else 0.55), 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
		var kr := MuhurYolu.kayit(n)
		var sag := ""
		if n == secili and not kilit:
			sag = "takılı"
		elif kilit:
			sag = "kilitli"
		PixUI.text(h, Vector2(lx, y + 3), sag, Color(col, 0.9) if n == secili else Color(PixUI.DIM, 0.6), 1, HORIZONTAL_ALIGNMENT_RIGHT, 206, 0)
		if int(kr.get("zafer", 0)) > 0:
			PixUI.text(h, Vector2(lx, y + 15), "✓ %d · %s" % [int(kr["zafer"]), MuhurYolu.sure_yazi(float(kr.get("en_iyi", 0.0)))], Color(1.0, 0.85, 0.45, 0.95), 1, HORIZONTAL_ALIGNMENT_RIGHT, 206, 0)
		y += SATIR_H
	# --- sağ: seçilen mühür
	var rx := lx + 226.0
	var rw := 374.0
	var top := 64.0 + (1.0 - e) * 8.0
	var col_s := MuhurYolu.renk(sel)
	PixUI.panel(h, Rect2(rx, top, rw, SATIR_H * 6 - 4), col_s.darkened(0.35), Color(0.05, 0.04, 0.06, 0.95))
	var yy := top + 6.0
	PixUI.text(h, Vector2(rx + 10, yy), Sinema.buyuk(MuhurYolu.ad(sel)), col_s.lerp(PixUI.TEXT, 0.25), 1)
	if sel > acik:
		PixUI.text(h, Vector2(rx, yy), "Kilitli: Erlik Han'ı %s ile yen" % MuhurYolu.ad(sel - 1), Color(PixUI.BAD, 0.9), 1, HORIZONTAL_ALIGNMENT_RIGHT, rw - 10, 0)
	yy += 14.0
	# kurallar (birikimli)
	PixUI.text(h, Vector2(rx + 10, yy), "KURALLAR", Color(PixUI.GOLD, 0.8), 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
	yy += 11.0
	if sel == 0:
		PixUI.text(h, Vector2(rx + 14, yy), "Kut'un ilk yolu. Kural yok; yalnızca gece.", PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
		yy += 11.0
	for n in range(1, sel + 1):
		var kd := MuhurYolu.kural(n)
		var satir := "%s  %s — %s" % [MuhurYolu.ROMA[n], String(kd.get("ad", "")), String(kd.get("desc", ""))]
		var cc := MuhurYolu.renk(n).lerp(PixUI.TEXT, 0.55) if n == sel else Color(PixUI.DIM, 0.85)
		for li in PixUI.wrap(satir, rw - 26):
			PixUI.text(h, Vector2(rx + 14, yy), String(li), cc, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
			yy += 10.0
	# zorluk sayıları
	var md := Zorluk.muhur_def(sel)
	yy += 3.0
	var sise := int(md.get("sise", 0))
	var zs := "Yaratık canı ×%s · hasarı ×%s · saldırganlık ×%s · şişe %s · şifa ×%s" % [_f(float(md.get("can", 1.0))), _f(float(md.get("hasar", 1.0))), _f(float(md.get("saldirganlik", 1.0))), ("%+d" % sise) if sise != 0 else "±0", _f(float(md.get("sifa", 1.0)))]
	if float(md.get("ofkeli", 0.0)) > 0.0:
		zs += " · öfkeli %%%d" % int(round(float(md.get("ofkeli", 0.0)) * 100.0))
	PixUI.text(h, Vector2(rx + 10, yy), "ZORLUK", Color(PixUI.BAD, 0.8), 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
	yy += 11.0
	for li in PixUI.wrap(zs, rw - 26):
		PixUI.text(h, Vector2(rx + 14, yy), String(li), Color(PixUI.TEXT, 0.8), 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
		yy += 10.0
	# ödüller
	var od := MuhurYolu.odul(sel)
	yy += 3.0
	PixUI.text(h, Vector2(rx + 10, yy), "ÖDÜL", Color(PixUI.GOOD, 0.85), 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
	yy += 11.0
	var ol: Array = []
	if sel > 0:
		ol.append("Kut ×%s · altın ×%s · nadirlik +%d%s" % [_f(float(od.get("kut", 1.0))), _f(float(od.get("altin", 1.0))), int(od.get("nadir", 0)),
			(" · en az %s" % String(Data.items["rarities"][int(od.get("nadir_taban", 0))]["name"])) if int(od.get("nadir_taban", 0)) > 0 else ""])
		var em := MuhurYolu.emanet_def(String(od.get("emanet", "")))
		if not em.is_empty():
			var bul: bool = String(od.get("emanet", "")) in Game.meta.get("muhur_emanet_bulunan", [])
			ol.append("Emanet: %s%s — yalnızca bu mühürde ve üstünde düşer" % [String(em.get("ad", "")), " (bulundu)" if bul else ""])
		var han: Array = []
		if int(od.get("han_tomar", 0)) > 0:
			han.append("+1 Kut Tomarı")
		if float(od.get("han_emanet", 0.0)) > 0.0:
			han.append("%%%d emanet" % int(round(float(od.get("han_emanet", 0.0)) * 100.0)))
		if not han.is_empty():
			ol.append("Han Otağı: " + ", ".join(han))
	var kr2 := MuhurYolu.kayit(sel)
	if int(od.get("ilk_zafer", 0)) > 0 and int(kr2.get("zafer", 0)) == 0:
		ol.append("İlk zafer: Umay'a %d Kut" % int(od.get("ilk_zafer", 0)))
	if sel > 0:
		ol.append("Bengü'ye süs: %s%s" % [MuhurYolu.SUS_AD[sel], " (kazanıldı)" if MuhurYolu.sus_acik(sel) else " (bu mühürde zafer)"])
	if sel == MuhurYolu.EN_COK:
		ol.append("Gerçek son: Gün Ana'nın son sözü" + (" (görüldü)" if bool(Game.meta.get("gercek_son", false)) else ""))
	if ol.is_empty():
		ol.append("Ulu Kayın'ın Kut'u, Gün Ana'nın ilk örgüsü.")
	for s in ol:
		for li in PixUI.wrap(String(s), rw - 26):
			PixUI.text(h, Vector2(rx + 14, yy), String(li), Color(0.8, 0.95, 0.75, 0.9), 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
			yy += 10.0
	# kayıt
	PixUI.text(h, Vector2(rx + 10, top + SATIR_H * 6 - 18), "Deneme %d · zafer %d · en iyi %s · en derin %d" % [int(kr2.get("deneme", 0)), int(kr2.get("zafer", 0)), MuhurYolu.sure_yazi(float(kr2.get("en_iyi", 0.0))), int(kr2.get("en_derin", 0))], Color(PixUI.DIM, 0.85), 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
	if h.flash_t > 0.0:
		PixUI.text(h, Vector2(0, vp.y - 40), h.flash_msg, PixUI.GOLD, 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x, 2)
	h._hint(vp, [["W/S", "mühür"], ["Boşluk", "tak"], ["E", "süs: " + MuhurYolu.SUS_AD[MuhurYolu.sus()]], ["Esc", "ayrıl"]])
	h._reveal(vp)


static func _f(v: float) -> String:
	return ItemGen.fmt(v)


# ------------------------------------------------------------------ HUD mühür damgası
static func hud(h: Control, vp: Vector2, place_name: String, info: String) -> void:
	## Sağ üst yer adının solunda koşunun mührü (mühürsüzde yok); yurtta seçili mühür soluk
	var n := Zorluk.muhur()
	var lv: Node = h.level
	if lv != null and bool(lv.get("hub")):
		n = Zorluk.muhur_secili()
	if n <= 0:
		return
	var col := MuhurYolu.renk(n)
	# InkHUD.place ile aynı genişlik hesabı
	var place_w := maxf(InkHUD.str_w(InkUI.font("caps"), InkHUD.tr_upper(place_name), 11), InkHUD.str_w(InkUI.font("body"), info, 9) + 12.0) + 24.0
	var c := Vector2(vp.x - 10.0 - place_w - 16.0, 26.0)
	h.draw_circle(c, 13.0, Color(0.02, 0.015, 0.03, 0.55))
	InkUI.seal_round(h, c, 22.0, col.darkened(0.1), 0.3)
	var f: Font = InkUI.font("caps")
	var s: String = MuhurYolu.ROMA[n]
	var w := f.get_string_size(s, HORIZONTAL_ALIGNMENT_LEFT, -1, 9).x
	h.draw_string(f, c + Vector2(-w * 0.5, 3.5), s, HORIZONTAL_ALIGNMENT_LEFT, -1, 9, Color(0.08, 0.04, 0.03))
