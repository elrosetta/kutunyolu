class_name SanatUI
extends RefCounted
## v27 Savaş Sanatları arayüzü (mürekkep): HUD halkası (Kut ve don halkalarının yanında; tamga, bekleme yayı, Alp Nişanı
## taneleri, T tuşu), sanat kartı, duraklatma / Alp Ata ekranı (sanat listesi + kart; kuşan / öğren).
## Çizim HUD (Control) üstüne; yazı ve paneller PixUI'den (v2'de InkUI'ye yönlenir), tamgalar SanatFX.glyph fırçasıyla.

const GREY := Color(0.42, 0.4, 0.46)
const INKC := Color(0.035, 0.02, 0.05)


static func _nisan_pips(h: Control, p0: Vector2, n_full: float, cost: float, col: Color, t: float, flash: float) -> void:
	## Alp Nişanı taneleri (eşkenar dörtgen): dolu / kısmen dolu / boş; sanatın bedeli kadar tane renkli çerçeveli
	var mx := int(SavasSanati.N("en_cok", 5.0))
	var bu := SavasSanati.birim()
	for i in mx:
		var c := p0 + Vector2(i * 9.0, 0.0)
		var s := 3.6
		var dia := PackedVector2Array([c + Vector2(0, -s * 1.25), c + Vector2(s, 0), c + Vector2(0, s * 1.25), c + Vector2(-s, 0)])
		h.draw_colored_polygon(PackedVector2Array([dia[0] + Vector2(0, -1.4), dia[1] + Vector2(1.4, 0), dia[2] + Vector2(0, 1.4), dia[3] + Vector2(-1.4, 0)]), Color(INKC, 0.85))
		var fill := clampf(n_full / bu - float(i), 0.0, 1.0)
		var in_cost := float(i) < cost / bu - 0.001
		h.draw_colored_polygon(dia, Color(0.16, 0.14, 0.2, 0.95))
		if fill > 0.0:
			var fc := Color(1.0, 0.84, 0.46) if fill >= 1.0 else Color(1.0, 0.84, 0.46, 0.55)
			if fill >= 1.0 and flash > 0.0 and i == int(n_full / bu) - 1:
				fc = fc.lerp(Color.WHITE, flash)
			if fill >= 0.98:
				h.draw_colored_polygon(dia, fc)
			elif fill * s * 2.5 >= 0.6:
				# v32: kısmen dolu tane: eşkenar dörtgen alttan "top" çizgisine dek kesilir (eski nokta çökertme "Invalid
				# polygon data" veriyordu)
				var top := c.y + s * 1.25 - fill * s * 2.5
				var band := PackedVector2Array([Vector2(c.x - s - 1.0, top), Vector2(c.x + s + 1.0, top), Vector2(c.x + s + 1.0, c.y + s * 1.25 + 1.0), Vector2(c.x - s - 1.0, c.y + s * 1.25 + 1.0)])
				for part in Geometry2D.intersect_polygons(dia, band):
					# çok ince dilim (sıfıra yakın alan) üçgenlenemez: atlanır
					if part.size() >= 3 and absf(_alan(part)) >= 0.5:
						h.draw_colored_polygon(part, fc)
		if in_cost:
			var k := 0.75 + 0.25 * sin(t * 6.0) if n_full >= cost else 0.5
			h.draw_polyline(PackedVector2Array([dia[0], dia[1], dia[2], dia[3], dia[0]]), Color(col, k), 1.0, true)


static func _alan(poly: PackedVector2Array) -> float:
	var a := 0.0
	for i in poly.size():
		a += poly[i].cross(poly[(i + 1) % poly.size()])
	return a * 0.5


static func hud(h: Control, c: Vector2, pl: Node, t: float) -> void:
	## Oyun içi halka: seçili sanatın tamgası, bekleme yayı, hazır parıltısı; sağında nişan taneleri, altında T
	if pl == null or not ("sanat" in pl) or pl.sanat == null:
		return
	var sn: SavasSanati = pl.sanat
	var id := SavasSanati.secili()
	if id == "":
		return
	var d := SavasSanati.def_of(id)
	var col := SavasSanati.renk(id)
	var ok := SavasSanati.uygun(id)
	var cost := SavasSanati.bedel_nisan(id)
	var n := SavasSanati.nisan()
	var hazir := sn.hazir()
	var cc := c + Vector2(sin(t * 60.0) * 2.0 * sn.fail_flash, 0.0)
	var bek := float(d.get("bekleme", 4.0))
	var k := 1.0 - clampf(sn.cd / maxf(0.1, bek), 0.0, 1.0)
	var ring_col := col if ok else GREY
	if hazir:
		ring_col = col.lerp(Color.WHITE, 0.25 + 0.25 * sin(t * 7.0))
	elif n < cost or sn.cd > 0.0:
		ring_col = Color(ring_col, 0.55)
	if hazir:
		InkUI.splat(h, cc, 40.0, Color(col, 0.22 + 0.08 * sin(t * 7.0)), t)
	InkUI.ring(h, cc, 14.0, k if ok else 0.0, ring_col)
	var gcol: Color = (col.lightened(0.15) if (hazir or (ok and n >= cost)) else Color(col, 0.45)) if ok else GREY
	SanatFX.glyph(h, id, cc, 8.5, Color(INKC, 0.8), 1.5)
	SanatFX.glyph(h, id, cc, 8.5, gcol, 0.85)
	if not ok:
		# sınıf uygun değil: çapraz fırça çizgisi
		SanatFX.stroke(h, PackedVector2Array([cc + Vector2(-9, -9), cc + Vector2(9, 9)]), PackedFloat32Array([1.0, 2.6]), Color(0.75, 0.25, 0.22, 0.85))
	elif sn.cd > 0.0:
		PixUI.text(h, Vector2(cc.x - 20, cc.y - 6), "%.0f" % ceilf(sn.cd), PixUI.TEXT, 1, HORIZONTAL_ALIGNMENT_CENTER, 40, 2)
	PixUI.key_cap(h, Vector2(c.x - 4.5, c.y + 11.0), "T", col if ok else GREY, hazir)
	_nisan_pips(h, Vector2(c.x + 21.0, c.y - 3.0), n, cost, col, t, sn.ready_flash)
	var nm := String(d.get("ad", ""))
	PixUI.text(h, Vector2(c.x + 16.0, c.y + 5.0), nm, Color(col if ok else GREY, 0.9), 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 2)


# ------------------------------------------------------------------ kart
static func card(h: Control, r: Rect2, id: String, t: float, mentor: bool) -> void:
	var d := SavasSanati.def_of(id)
	if d.is_empty():
		return
	var col := SavasSanati.renk(id)
	var acik := SavasSanati.acik_mi(id)
	PixUI.fancy_panel(h, r, col.darkened(0.15) if acik else PixUI.EDGE.darkened(0.3), PixUI.INK2)
	# başlık: büyük tamga ensō içinde
	var gc := r.position + Vector2(34, 36)
	InkUI.splat(h, gc, 70.0, Color(col, 0.18), 0.6)
	var pts := PackedVector2Array()
	var ws := PackedFloat32Array()
	for i in 33:
		var u := float(i) / 32.0
		var a := -2.0 + u * TAU * 0.88
		pts.append(gc + Vector2(cos(a), sin(a)) * 24.0)
		ws.append(lerpf(1.0, 5.0, sin(u * PI)))
	SanatFX.stroke(h, pts, ws, Color(INKC, 0.85))
	var ws2 := PackedFloat32Array()
	for w in ws:
		ws2.append(w * 0.4)
	SanatFX.stroke(h, pts, ws2, Color(col, 0.9) if acik else GREY)
	SanatFX.glyph(h, id, gc, 14.0, Color(INKC, 0.85), 1.5)
	SanatFX.glyph(h, id, gc, 14.0, col.lightened(0.15) if acik else GREY, 0.8)
	var tx := r.position.x + 68.0
	PixUI.text(h, Vector2(tx, r.position.y + 12), String(d["ad"]), col if acik else PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 2)
	PixUI.text(h, Vector2(tx, r.position.y + 26), "«%s»" % String(d.get("lakap", "")), Color(PixUI.TEXT, 0.7), 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
	var y := r.position.y + 70.0
	for l in PixUI.wrap(String(d.get("aciklama", "")), r.size.x - 20.0):
		PixUI.text(h, Vector2(r.position.x + 10, y), l, PixUI.TEXT, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 1)
		y += 11.0
	y += 4.0
	PixUI.divider(h, r.position.x + 10, y, r.size.x - 20)
	y += 7.0
	var cost := float(d.get("nisan", 1.0))
	var rows := [
		["Bedel", ("%s Alp Nişanı" % ItemGen.fmt(cost)) + ("  (+%s / ek tur)" % ItemGen.fmt(float((d.get("ek_tur", [0.5]) as Array)[0])) if d.has("ek_tur") else "")],
		["Bekleme", "%s sn" % ItemGen.fmt(float(d.get("bekleme", 4.0)))],
		["Hasar", _hasar_metni(d)],
		["Silahlar", SavasSanati.siniflar_metni(id)],
	]
	for row in rows:
		PixUI.text(h, Vector2(r.position.x + 10, y), String(row[0]), PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
		var lines := PixUI.wrap(String(row[1]), r.size.x - 78.0)
		for l in lines:
			PixUI.text(h, Vector2(r.position.x + 66, y), l, PixUI.TEXT, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
			y += 10.0
		y += 1.0
	# kuşanılan silahla uygun mu
	y += 3.0
	if not Game.run.is_empty():
		var ok := SavasSanati.uygun(id)
		var mel := SavasSanati.yakin_esya()
		var wn := String(mel.get("name", "—")) if not ("yay" in d.get("sinif", [])) else String(SavasSanati.yay_esya().get("name", "yay yok"))
		PixUI.text(h, Vector2(r.position.x + 10, y), ("%s ile kullanılır" if ok else "%s ile kullanılamaz") % wn, PixUI.GOOD if ok else PixUI.BAD, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
		y += 12.0
	if not acik:
		var b := SavasSanati.bedel(id)
		var bank := int(Game.meta.get("kut_bank", 0))
		if mentor:
			PixUI.text(h, Vector2(r.position.x + 10, y), "Öğrenme bedeli: %d Kut (bankan: %d)" % [b, bank], PixUI.KUT if bank >= b else PixUI.BAD, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
		else:
			PixUI.text(h, Vector2(r.position.x + 10, y), "Kilitli: yurtta Alp Ata öğretir ya da Sanat Tomarı bulunur", PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)


static func _hasar_metni(d: Dictionary) -> String:
	var hs := "silahın ×%s" % ItemGen.fmt(float(d.get("hasar", 1.0)))
	match String(d["id"]):
		"kasirga":
			hs = "tur başına 2 × ×%s, son ×%s" % [ItemGen.fmt(float(d["hasar"])), ItemGen.fmt(float(d.get("son_hasar", 1.0)))]
		"goge_yukselis":
			hs = "×%s + 2 × ×%s + dalış ×%s" % [ItemGen.fmt(float(d["hasar"])), ItemGen.fmt(float(d.get("tepe_hasar", 0.9))), ItemGen.fmt(float(d.get("dalis_hasar", 2.0)))]
		"bozkurt_atilisi":
			hs = "geçiş ×%s + kın ×%s" % [ItemGen.fmt(float(d["hasar"])), ItemGen.fmt(float(d.get("kin_hasar", 0.9)))]
		"ok_yagmuru":
			hs = "%d ok × yayın ×%s" % [int(d.get("ok", 18)), ItemGen.fmt(float(d["hasar"]))]
		"demir_durus":
			hs = "karşılık ×%s (kesin kritik)" % ItemGen.fmt(float(d["hasar"]))
		"kurt_dansi":
			hs = "%d kesik × ×%s + patlama ×%s" % [int(d.get("adim", 4)), ItemGen.fmt(float(d["hasar"])), ItemGen.fmt(float(d.get("kin_hasar", 1.3)))]
		"pehlivan_savurmasi":
			hs = "tutuş ×%s, savrulan ×%s / tur, çarptığı ×%s, çakılma ×%s" % [ItemGen.fmt(float(d["hasar"])), ItemGen.fmt(float(d.get("tutus_hasar", 0.3))), ItemGen.fmt(float(d.get("savurma_hasar", 0.55))), ItemGen.fmt(float(d.get("firlatma_hasar", 1.3)))]
		"yildirim_agi":
			hs = "kazık ×%s, ağ ×%s / tık, zincir ×%s, yıldırım ×%s" % [ItemGen.fmt(float(d["hasar"])), ItemGen.fmt(float(d.get("ag_hasar", 0.12))), ItemGen.fmt(float(d.get("zincir_hasar", 0.8))), ItemGen.fmt(float(d.get("son_hasar", 1.5)))]
		"tulpar_dortnali":
			hs = "%d vuruş ×%s (+%s / vuruş), dörtnal ×%s" % [int(d.get("vurus", 4)), ItemGen.fmt(float(d["hasar"])), ItemGen.fmt(float(d.get("artis", 0.12))), ItemGen.fmt(float(d.get("son_hasar", 1.5)))]
		"akinci_akini":
			hs = "%d + %d ok × ×%s, delen ok ×%s" % [int(d.get("yaylim_ok", 5)), int(d.get("seri_ok", 6)), ItemGen.fmt(float(d.get("seri_hasar", 0.35))), ItemGen.fmt(float(d.get("delis_hasar", 1.6)))]
	if d.has("ritim_k"):
		hs += " · TAM ×%s%s" % [("%.2f" % float(d["ritim_k"])).replace(".", ",").trim_suffix("0"), " (her vuruş; dördü TAM: dörtnal)" if String(d["id"]) == "tulpar_dortnali" else ""]
	return hs + " · duruş %s · boss ×%s" % [ItemGen.fmt(float(d.get("durus", 1.0))), ItemGen.fmt(float(d.get("boss_k", 0.7)))]


# ------------------------------------------------------------------ duraklatma / Alp Ata ekranı
static func menu(h: Control, vp: Vector2, sel: int, mentor: bool, t: float, e: float, msg: String, msg_t: float) -> void:
	var ids := SavasSanati.ids()
	var lw := 214.0
	var cw := 240.0
	var x0 := roundf((vp.x - (lw + 14.0 + cw)) / 2.0 + (1.0 - e) * -16.0)
	var y := 84.0
	var cur := SavasSanati.secili()
	# üst bilgi: nişan / Kut bankası
	var info := ""
	if mentor:
		info = "Kut bankası: %d" % int(Game.meta.get("kut_bank", 0))
	else:
		info = "Alp Nişanı: %s / %d" % [ItemGen.fmt(floorf(SavasSanati.nisan() / SavasSanati.birim() * 10.0) / 10.0), int(SavasSanati.N("en_cok", 5.0))]
	var iw := PixUI.width(info) + 20.0
	PixUI.panel(h, Rect2((vp.x - iw) / 2.0, 62, iw, 15), PixUI.KUT if mentor else PixUI.GOLD)
	PixUI.text(h, Vector2(0, 64), info, PixUI.KUT if mentor else PixUI.GOLD, 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	# v31: 13 sanat: liste kayar (en çok 8 satır görünür, seçili ortada); üstte / altta kalan varsa fırça oku
	var vis := 8
	var first := clampi(sel - 3, 0, maxi(0, ids.size() - vis))
	if first > 0:
		_kaydir_oku(h, Vector2(x0 + lw * 0.5, y - 6.0), -1.0, t)
	for i in range(first, mini(ids.size(), first + vis)):
		var id: String = ids[i]
		var d := SavasSanati.def_of(id)
		var col := SavasSanati.renk(id)
		var acik := SavasSanati.acik_mi(id)
		var is_sel := i == sel
		var r := Rect2(x0, y, lw, 25.0)
		PixUI.panel(h, r, (col if acik else PixUI.GOLD) if is_sel else PixUI.EDGE.darkened(0.4), PixUI.INK2 if is_sel else PixUI.INK, false)
		if is_sel:
			PixUI.text(h, Vector2(x0 - 10 + sin(t * 8.0) * 2.0, y + 6), "→", col, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 2)
		var gc := Vector2(x0 + 14, y + 12.5)
		h.draw_circle(gc, 9.5, Color(INKC, 0.7), true, -1.0, true)
		SanatFX.glyph(h, id, gc, 7.0, col if acik else GREY, 0.9)
		PixUI.text(h, Vector2(x0 + 28, y + 2), String(d["ad"]), (PixUI.TEXT if acik else PixUI.DIM) if id != cur else col, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 2)
		var sub := ""
		if id == cur:
			sub = "KUŞANILDI"
		elif acik:
			sub = "öğrenildi"
		else:
			sub = ("%d Kut" % SavasSanati.bedel(id)) if mentor else "kilitli"
		var ok := SavasSanati.uygun(id)
		PixUI.text(h, Vector2(x0 + 28, y + 13), "%s · %s nişan%s" % [sub, ItemGen.fmt(float(d.get("nisan", 1.0))), "" if ok else " · silah uymaz"], Color(PixUI.DIM, 0.95) if id != cur else Color(col, 0.85), 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
		if not acik:
			var lk := Vector2(x0 + lw - 12, y + 12.5)
			h.draw_rect(Rect2(lk + Vector2(-3.5, -1.0), Vector2(7, 6)), Color(GREY, 0.9))
			h.draw_arc(lk + Vector2(0, -1.5), 2.6, PI, TAU, 8, Color(GREY, 0.9), 1.2, true)
		y += 28.0
	if first + vis < ids.size():
		_kaydir_oku(h, Vector2(x0 + lw * 0.5, y + 2.0), 1.0, t)
	card(h, Rect2(x0 + lw + 14.0, 84.0, cw, 222.0), String(ids[clampi(sel, 0, ids.size() - 1)]), t, mentor)
	if msg_t > 0.0 and msg != "":
		PixUI.text(h, Vector2(0, vp.y - 42), msg, PixUI.GOLD, 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x, 2)


static func _kaydir_oku(h: Control, c: Vector2, dir: float, t: float) -> void:
	## Listenin kayan ucu: küçük üçgen (dir -1 yukarı, 1 aşağı), hafif nabız
	var k := 0.7 + 0.3 * sin(t * 5.0)
	var o := Vector2(0, dir * 1.5 * sin(t * 5.0))
	var tri := PackedVector2Array([c + o + Vector2(-6, -dir * 2.5), c + o + Vector2(6, -dir * 2.5), c + o + Vector2(0, dir * 3.5)])
	h.draw_colored_polygon(tri, Color(PixUI.GOLD, k))
