class_name HaritaUI
extends RefCounted
## v32 harita çizimi (HUD.gd'nin mürekkep dalı): sağ altta parşömen küçük harita (sis, oyuncu, işaretler) ve tam ekran
## harita (M): bütün bölüm, Kut Taşı seçimi ve ışınlanma, lejant. Birimler HUD (960x540) / menü (640x360) tasarımında.

const PAPER_INK := Color(0.16, 0.11, 0.08)
const KUT := Color(0.36, 0.86, 0.9)
const GOLD := Color(1.0, 0.82, 0.38)
const BONE := Color(0.95, 0.88, 0.74)
const SIZES := [Vector2.ZERO, Vector2(126, 76), Vector2(168, 100), Vector2(228, 136)]   # Kapalı / Küçük / Normal / Büyük
const PPT := [0.0, 2.2, 2.6, 3.0]   # birim / karo (v33: küçük bölümde daha geniş pencere: Normal ~65 x 38 karo, 3-4 oda)


# ------------------------------------------------------------------ küçük harita (oyun içi, sağ alt)
static func minimap(h: Control, vp: Vector2, lv: Node, t: float) -> void:
	var hm: Harita = lv.get("harita")
	if hm == null or hm.tex == null:
		return
	var si: int = clampi(int(Ayarlar.get("harita_i")), 0, 3)
	if si == 0:
		return
	var size: Vector2 = SIZES[si]
	var ppt: float = PPT[si]
	var alpha: float = [0.55, 0.8, 1.0][clampi(int(Ayarlar.get("harita_a")), 0, 2)]
	var r := Rect2(vp.x - size.x - 10.0, vp.y - size.y - 10.0, size.x, size.y)
	var pl: Node = lv.player
	var TS: int = lv.TS
	var pc := Vector2(pl.global_position.x / TS, (pl.global_position.y - 12.0) / TS)
	# pencere (karo): oyuncu ortada; bölüm sınırlarına kenetli
	var wt := size / ppt
	var b: Rect2i = lv.bounds
	var ox := clampf(pc.x - wt.x * 0.5, float(b.position.x), maxf(float(b.position.x), float(b.end.x) - wt.x))
	var oy := clampf(pc.y - wt.y * 0.5, float(b.position.y), maxf(float(b.position.y), float(b.end.y) - wt.y))
	InkUI.paper(h, r, alpha)
	h.draw_rect(r, Color(0.07, 0.05, 0.04, 0.82 * alpha))   # sis: görülmeyen alan koyu (keşfedilen açık parşömen olarak belirir)
	var src := Rect2(ox * Harita.PX, oy * Harita.PX, wt.x * Harita.PX, wt.y * Harita.PX)
	h.draw_texture_rect_region(hm.tex, r, src, Color(1, 1, 1, alpha))
	_markers(h, hm, r, Vector2(ox, oy), ppt, -1, t, false, alpha)
	# oyuncu: kızıl mühür noktası + yön çentiği
	var pp := r.position + (pc - Vector2(ox, oy)) * ppt
	if r.has_point(pp):
		h.draw_circle(pp, 3.2, Color(InkUI.SEAL, alpha), true, -1.0, true)
		h.draw_circle(pp, 3.2, Color(BONE, alpha), false, 1.0, true)
		var f := float(pl.get("facing"))
		h.draw_line(pp + Vector2(f * 3.0, 0), pp + Vector2(f * 6.0, 0), Color(BONE, alpha), 1.2, true)
	# çerçeve, başlık ve keşif yüzdesi
	InkUI.nine(h, r.grow(3.5), InkUI.tex("frame_ink"), 48.0, Color(InkUI.INK, 0.9 * alpha), 5.5)
	PixUI.key_cap(h, Vector2(r.position.x + 3, r.position.y - 7), "M", GOLD, true)
	var f2 := InkUI.font("caps")
	InkUI.draw_str(h, Vector2(r.position.x + 18, r.position.y + 1), "HARİTA", f2, 7, Color(BONE, 0.85 * alpha), 1)
	var ys := "%%%d" % int(round(hm.yuzde() * 100.0))
	InkUI.draw_str(h, Vector2(r.end.x - 4 - InkHUD.str_w(InkUI.font("body"), ys, 8), r.position.y + 1), ys, InkUI.font("body"), 8, Color(BONE, 0.7 * alpha), 1)


# ------------------------------------------------------------------ tam ekran harita (M)
static func full(h: Control, vp: Vector2, lv: Node, sel: int, t: float, isin_t: float) -> void:
	var hm: Harita = lv.get("harita")
	h.draw_rect(Rect2(Vector2.ZERO, vp), Color(0.02, 0.015, 0.04, 0.78))
	InkUI.vignette(h, vp, 0.9)
	if hm == null or hm.tex == null:
		PixUI.text(h, Vector2(0, vp.y * 0.5), "Bu yerin haritası yok.", PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
		return
	var b: Rect2i = lv.bounds
	var bw := float(b.size.x)
	var bh := float(b.size.y)
	var maxw := vp.x - 60.0
	var maxh := vp.y - 118.0
	var ppt := minf(maxw / bw, maxh / bh)
	var size := Vector2(bw, bh) * ppt
	var r := Rect2(Vector2((vp.x - size.x) * 0.5, 54.0 + (maxh - size.y) * 0.5), size)
	var pr := r.grow(10.0)
	InkUI.paper(h, pr, 1.0)
	h.draw_rect(r, Color(0.07, 0.05, 0.04, 0.8))   # sis: görülmeyen alan koyu kâğıt
	var src := Rect2(b.position.x * Harita.PX, b.position.y * Harita.PX, bw * Harita.PX, bh * Harita.PX)
	h.draw_texture_rect_region(hm.tex, r, src, Color(1, 1, 1, 1))
	_markers(h, hm, r, Vector2(b.position), ppt, sel, t, true, 1.0)
	var pl: Node = lv.player
	var TS: int = lv.TS
	var pp := r.position + (Vector2(pl.global_position.x / TS, (pl.global_position.y - 12.0) / TS) - Vector2(b.position)) * ppt
	h.draw_circle(pp, 4.0, InkUI.SEAL, true, -1.0, true)
	h.draw_circle(pp, 4.0, BONE, false, 1.2, true)
	h.draw_circle(pp, 7.0 + 2.0 * sin(t * 5.0), Color(InkUI.SEAL, 0.5), false, 1.0, true)
	# başlık
	var fc := InkUI.font("caps")
	var title := InkHUD.tr_upper(String(lv.biome.get("name", "Harita")))
	var tw := InkHUD.str_w(fc, title, 14)
	InkUI.wash(h, Rect2(vp.x * 0.5 - 200, 10, 400, 40), 0.7)
	InkUI.draw_str(h, Vector2((vp.x - tw) * 0.5, 30), title, fc, 14, GOLD, 2)
	var sub := "%d. derinlik  ·  keşif %%%d  ·  Kut Taşı %d / %d" % [int(Game.run.get("depth", 1)), int(round(hm.yuzde() * 100.0)), hm.bulunan().size(), hm.tasi.size()]
	var fb := InkUI.font("body")
	InkUI.draw_str(h, Vector2((vp.x - InkHUD.str_w(fb, sub, 9)) * 0.5, 43), sub, fb, 9, Color(BONE, 0.8), 1)
	# seçili taş
	var found: Array = hm.bulunan()
	var ly := pr.end.y + 10.0
	if found.is_empty():
		PixUI.text(h, Vector2(0, ly), "Henüz Kut Taşı bulunmadı: taşların yanından geçince haritaya işlenir.", PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	elif isin_t > 0.0:
		PixUI.text(h, Vector2(0, ly), "Kut'a bağlanıyor...", KUT, 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	else:
		var i: int = found[clampi(sel, 0, found.size() - 1)]
		var td: Dictionary = hm.tasi[i]
		var yakin: bool = lv.tasi_yakin() == i
		var s := "%s" % String(td["ad"])
		if yakin:
			s += "  (buradasın)"
		PixUI.text(h, Vector2(0, ly), s, KUT if not yakin else PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	# lejant
	var lx := pr.position.x + 4.0
	var lyy := ly + 16.0
	var items := [["tasi", "Kut Taşı"], ["cikis", "Kut Kapısı"], ["tomar", "Tomar"], ["esya", "Eşya"], ["pazar", "Bezirgân"], ["sunak", "Sunak"], ["seckin", "Seçkin"], ["zamanli", "Zamanlı kapı"]]
	for it in items:
		_glyph(h, String(it[0]), Vector2(lx + 6, lyy + 6), 1.0, t, false, 1.0, false)
		PixUI.text(h, Vector2(lx + 15, lyy + 1), String(it[1]), Color(BONE, 0.8), 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
		lx += 15.0 + PixUI.width(String(it[1])) + 14.0
	var hints: Array = [["A/D", "taş seç"], ["Boşluk", "ışınlan"], ["M / Esc", "kapat"]]
	if found.size() <= 1:
		hints = [["Boşluk", "ışınlan"], ["M / Esc", "kapat"]]
	_hint(h, vp, hints)


static func _hint(h: Control, vp: Vector2, items: Array) -> void:
	var total := 0.0
	for it in items:
		total += PixUI.key_w(it[0]) + 3.0 + PixUI.width(it[1]) + 12.0
	total -= 12.0
	var x := roundf((vp.x - total) / 2.0)
	var yy := vp.y - 22.0
	for it in items:
		PixUI.key_cap(h, Vector2(x, yy), it[0])
		x += PixUI.key_w(it[0]) + 3.0
		PixUI.text(h, Vector2(x, yy), it[1], Color(PixUI.TEXT, 0.85))
		x += PixUI.width(it[1]) + 12.0


# ------------------------------------------------------------------ işaretler
static func _markers(h: Control, hm: Harita, r: Rect2, origin: Vector2, ppt: float, sel: int, t: float, big: bool, alpha: float) -> void:
	var found: Array = hm.bulunan()
	var sel_i := -1
	if sel >= 0 and not found.is_empty():
		sel_i = int(found[clampi(sel, 0, found.size() - 1)])
	for m in hm.isaretler():
		var c: Vector2i = m["cell"]
		var p := r.position + (Vector2(c.x + 0.5, c.y + 0.5) - origin) * ppt
		if not r.grow(2.0).has_point(p):
			continue
		var tur := String(m["tur"])
		var selected: bool = tur == "tasi" and int(m["i"]) == sel_i
		_glyph(h, tur, p, 1.0 if not big else 1.25, t, selected, alpha, bool(m.get("acik", true)))
		if big and tur == "tasi":
			var fb := InkUI.font("body")
			var s := String(m["ad"])
			var w := InkHUD.str_w(fb, s, 8)
			InkUI.draw_str(h, Vector2(p.x - w * 0.5, p.y - 9), s, fb, 8, KUT if selected else Color(BONE, 0.85), 1)
		elif big and tur == "zamanli":
			var fb := InkUI.font("body")
			var s := String(m["ad"])
			var w := InkHUD.str_w(fb, s, 8)
			InkUI.draw_str(h, Vector2(p.x - w * 0.5, p.y - 8), s, fb, 8, Color(BONE, 0.85), 1)


static func _glyph(h: Control, tur: String, p: Vector2, k: float, t: float, selected: bool, alpha: float, acik := true) -> void:
	## Küçük mürekkep simgeler: Kut Taşı (dikili taş + ışık), kapı (kemer), tomar / eşya / altın / ruh / kafatası / zaman simgeleri
	match tur:
		"tasi", "tasi_sonuk":
			var col := KUT if tur == "tasi" else Color(0.5, 0.48, 0.5)
			if selected:
				h.draw_circle(p, 7.0 * k + 1.5 * sin(t * 6.0), Color(KUT, 0.8 * alpha), false, 1.3, true)
				InkUI.splat(h, p, 16.0 * k, Color(KUT, 0.25 * alpha), t * 0.2)
			var pts := PackedVector2Array([p + Vector2(-2.6, 4.0) * k, p + Vector2(-2.0, -4.5) * k, p + Vector2(0.4, -5.2) * k, p + Vector2(2.6, -3.6) * k, p + Vector2(2.4, 4.0) * k])
			h.draw_colored_polygon(pts, Color(PAPER_INK, alpha))
			h.draw_line(p + Vector2(-0.6, -2.6) * k, p + Vector2(0.4, 1.8) * k, Color(col, alpha), 1.2 * k, true)
			if tur == "tasi":
				h.draw_circle(p + Vector2(0, -0.4) * k, 1.4 * k, Color(col.lightened(0.3), alpha), true, -1.0, true)
		"cikis":
			var col := Color(0.45, 0.9, 1.0)
			h.draw_arc(p + Vector2(0, 1.5 * k), 4.2 * k, PI, TAU, 10, Color(PAPER_INK, alpha), 2.4 * k, true)
			h.draw_line(p + Vector2(-4.2 * k, 1.5 * k), p + Vector2(-4.2 * k, 5.0 * k), Color(PAPER_INK, alpha), 2.4 * k, true)
			h.draw_line(p + Vector2(4.2 * k, 1.5 * k), p + Vector2(4.2 * k, 5.0 * k), Color(PAPER_INK, alpha), 2.4 * k, true)
			h.draw_circle(p + Vector2(0, 1.5 * k), 1.8 * k, Color(col, (0.7 + 0.3 * sin(t * 4.0)) * alpha), true, -1.0, true)
		"tomar":
			InkUI.icon_at(h, "tilsim", p, 9.0 * k, Color(GOLD, alpha), false)
		"esya":
			InkUI.icon_at(h, "kilic", p, 9.0 * k, Color(BONE, alpha), false)
		"pazar":
			InkUI.icon_at(h, "altin", p, 9.0 * k, Color(GOLD, alpha), false)
		"sunak":
			InkUI.icon_at(h, "ruh", p, 9.0 * k, Color(0.85, 0.6, 1.0, alpha), false)
		"seckin":
			InkUI.icon_at(h, "kafatasi", p, 9.0 * k, Color(1.0, 0.35, 0.3, alpha), false)
		"zamanli":
			InkUI.icon_at(h, "zaman", p, 9.0 * k, Color(BONE if acik else Color(0.5, 0.45, 0.45), alpha), false)
