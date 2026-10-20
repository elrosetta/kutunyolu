class_name InkHUD
extends RefCounted
## Stil v2 oyun içi göstergeleri (HUD.gd'nin mürekkep dalları): can fırçası, şişe / altın / Kut satırı, ongunlar,
## silah yuvaları (v2 silah atlası), Kut / don halkaları (ensō), kombo hattı, boss çubuğu, yer adı, usul ölçeri.
## Yerleşim v1 ile aynı birimlerde (HUD 960x540); bütün bilgiler korunur.

const BONE := Color(0.95, 0.88, 0.74)
const HP_RED := Color(0.82, 0.12, 0.1)
const KUT := Color(0.36, 0.86, 0.9)


static func tr_upper(s: String) -> String:
	return s.replace("i", "İ").replace("ı", "I").to_upper()


static func str_w(f: Font, s: String, size: int) -> float:
	return f.get_string_size(s, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x


# ------------------------------------------------------------------ sol üst: can, şişe, altın, Kut, ongunlar
static func top_left(h: Control, R: Dictionary, hp: float, mhp: float, hpk: float, lag: float, t: float, kut_pulse: float) -> float:
	var x0 := 8.0
	var y0 := 8.0
	InkUI.wash(h, Rect2(-40, -14, 300, 84), 0.66)
	var low := hpk < 0.3
	# can: kızıl mürekkep yürek + fırça çubuğu
	var hc := Vector2(x0 + 8, y0 + 8)
	var hcol := HP_RED.lightened(0.15) if not (low and int(t * 5.0) % 2 == 0) else Color(1.0, 0.62, 0.5)
	InkUI.icon_at(h, "can", hc, 19.0, hcol)
	var br := Rect2(x0 + 22, y0 + 4, 158, 9)
	InkUI.bar(h, br, 0.0, Color(0, 0, 0, 0), Color(0.16, 0.03, 0.04, 1.0))
	InkUI.bar(h, br, lag, Color(BONE, 0.8), Color(0, 0, 0, 0))
	var fc := HP_RED if not low else Color(0.95, 0.22 + 0.12 * sin(t * 10.0), 0.18)
	InkUI.bar(h, br, hpk, fc, Color(0, 0, 0, 0))
	var f := InkUI.font("bold")
	var s := "%d / %d" % [int(ceil(hp)), int(mhp)]
	InkUI.draw_str(h, Vector2(br.position.x + (br.size.x - str_w(f, s, 10)) * 0.5, br.position.y + 8.0), s, f, 10, BONE, 2)
	# şişeler, Q mühürü, altın, Kut (bankadaki Kut parantezde)
	var y2 := y0 + 22.0
	var x := x0 + 1.0
	for i in int(R["max_flasks"]):
		var full := i < int(R["flasks"])
		InkUI.icon_at(h, "sise", Vector2(x + 4, y2 + 5), 11.0, Color(0.4, 0.92, 0.8) if full else Color(0.3, 0.28, 0.36, 0.8), full)
		x += 9.0
	PixUI.key_cap(h, Vector2(x + 3, y2), "Q", PixUI.GOLD, int(R["flasks"]) > 0)
	x += PixUI.key_w("Q") + 12.0
	InkUI.icon_at(h, "altin", Vector2(x + 4, y2 + 5), 11.0, PixUI.GOLD)
	var gs := str(R["gold"])
	InkUI.draw_str(h, Vector2(x + 11, y2 + 9), gs, f, 10, PixUI.GOLD, 1)
	x += 16.0 + str_w(f, gs, 10)
	var kc := KUT.lightened(0.4 * clampf(kut_pulse * 2.5, 0.0, 1.0))
	InkUI.icon_at(h, "kut", Vector2(x + 4, y2 + 4.5), 11.0 + kut_pulse * 6.0, kc)
	var ks := str(int(R["kut"]))
	InkUI.draw_str(h, Vector2(x + 11, y2 + 9), ks, f, 10, kc, 1)
	x += 14.0 + str_w(f, ks, 10)
	InkUI.draw_str(h, Vector2(x, y2 + 9), "(%d)" % int(Game.meta.get("kut_bank", 0)), InkUI.font("body"), 9, Color(KUT, 0.6), 1)
	# ongun rozetleri: mürekkep simge + seviye
	var y3 := y2 + 17.0
	x = x0
	for k in HUD.ONGUN_KEYS:
		var col := PixUI.ongun_col(k)
		InkUI.icon_at(h, k, Vector2(x + 6, y3 + 6), 13.0, col)
		InkUI.draw_str(h, Vector2(x + 14, y3 + 10), str(int(R["ongun"][k])), f, 10, col.lightened(0.25), 1)
		x += 30.0
	# v34: okunan Kut Tomarı sayısı (kayın kabuğu tomar simgesi)
	if TomarV2.on() and TomarV2.has("ui_tomar"):
		TomarV2.ui(h, "ui_tomar", Vector2(x + 9, y3 + 6), 22.0)
		InkUI.draw_str(h, Vector2(x + 21, y3 + 10), str(int(R.get("scrolls", 0))), f, 10, PixUI.GOLD, 1)
	return y3


# ------------------------------------------------------------------ silah / teçhizat yuvası
static func slot_box(h: Control, r: Rect2, key: String, pl: Node) -> void:
	var it: Dictionary = Game.run["slots"].get(key, {})
	var col := Color(0.5, 0.42, 0.32)
	if not it.is_empty():
		col = Color.from_string(Data.items["rarities"][int(it["rarity"])]["color"], PixUI.DIM)
	var active := false
	if not it.is_empty() and key in ["melee", "second"]:
		active = (key == pl.mel_slot and not pl.atk.is_empty()) or (key == pl.sec_slot and (pl.aim_t >= 0.0 or pl.block_t >= 0.0))
	if active:
		InkUI.splat(h, r.get_center(), r.size.x * 1.25, Color(col, 0.28), float(key.length()))
	InkUI.nine(h, Rect2(r.position + Vector2(1.5, 2.0), r.size), InkUI.tex("fill"), 32.0, Color(0, 0, 0, 0.45))
	InkUI.nine(h, r, InkUI.tex("fill"), 32.0, Color(0.075, 0.066, 0.1, 0.9))
	InkUI.nine(h, r.grow(4.5), InkUI.tex("frame_ink"), 48.0, Color(InkUI.INK, 0.9), 5.5)
	InkUI.nine(h, r.grow(4.0), InkUI.tex("frame_line"), 48.0, Color(col.lightened(0.35 if active else 0.0), 0.95 if not it.is_empty() else 0.5), 4.5)
	if it.is_empty():
		PixUI.text(h, r.position + Vector2(0, 9), "boş", Color(PixUI.DIM, 0.55), 1, HORIZONTAL_ALIGNMENT_CENTER, r.size.x, 0)
	else:
		PixUI.weapon(h, it, r.get_center() + Vector2(0, -1), r.size - Vector2(8, 9))
		PixUI.ongun_stripe(h, Rect2(r.position.x + 4, r.end.y - 3.5, r.size.x - 8, 2.2), Game.item_onguns(it), Game.item_best_ongun(it))
		Unsur.slot_badge(h, r, it, Time.get_ticks_msec() / 1000.0)   # v20 unsur simgesi
	if pl.cd.has(key) and pl.cd[key] > 0.0:
		var k := clampf(pl.cd[key] / maxf(0.01, pl.cd_max[key]), 0.0, 1.0)
		var hh := r.size.y * k
		InkUI.nine(h, Rect2(r.position.x, r.end.y - hh, r.size.x, hh), InkUI.tex("fill"), 32.0, Color(0.0, 0.0, 0.02, 0.72))
		if key in ["g1", "g2"] and pl.cd[key] >= 1.0:
			PixUI.text(h, r.position + Vector2(0, 8), str(int(ceil(pl.cd[key]))), BONE, 1, HORIZONTAL_ALIGNMENT_CENTER, r.size.x, 2)
	PixUI.key_cap(h, r.position + Vector2(-3, -6), HUD.SLOT_KEYS[key], PixUI.GOLD, not it.is_empty())


# ------------------------------------------------------------------ halkalar (Kut F, don G)
static func ring(h: Control, c: Vector2, k: float, col: Color, icon: String, icon_col: Color, key: String, key_col: Color, active: bool) -> void:
	InkUI.ring(h, c, 14.0, k, col)
	InkUI.icon_at(h, icon, c, 13.0, icon_col, false)
	PixUI.key_cap(h, Vector2(c.x - 4.5, c.y + 11.0), key, key_col, active)


# ------------------------------------------------------------------ kombo
static func combo(h: Control, vp: Vector2, pl: Node, rk_name: String, rk_col: Color, t: float) -> void:
	var rx := vp.x - 12.0
	var cy := 236.0  # kartın (sağ üst, ~66-230) altında
	var pop: float = clampf((float(pl.combo_t) - 2.0) * 2.5, 0.0, 1.0)
	InkUI.splat(h, Vector2(rx - 34, cy + 22), 78.0 + pop * 10.0, Color(InkUI.INK, 0.62), float(pl.combo_n) * 1.7)
	InkUI.splat(h, Vector2(rx - 40, cy + 20), 46.0, Color(rk_col.darkened(0.55), 0.35), float(pl.combo_n) * 2.9 + 1.0)
	var fb := InkUI.font("brush")
	var size := int(round(36.0 + pop * 9.0))
	var s := "x%d" % pl.combo_n
	var w := str_w(fb, s, size)
	InkUI.draw_str(h, Vector2(rx - 6 - w, cy + 30), s, fb, size, rk_col, 2, 3)
	var fc := InkUI.font("caps")
	var nm := "KOMBO" if rk_name == "" else tr_upper(rk_name)
	var nw := str_w(fc, nm, 10)
	InkUI.draw_str(h, Vector2(rx - 6 - nw, cy + 43), nm, fc, 10, rk_col.lightened(0.1), 2)
	PixUI.bar(h, Rect2(rx - 70, cy + 49, 64, 3), clampf(pl.combo_t / 2.4, 0.0, 1.0), rk_col)
	var hs := "+%d%% hasar" % int(round((pl.combo_mult() - 1.0) * 100.0))
	var fbody := InkUI.font("body")
	InkUI.draw_str(h, Vector2(rx - 6 - str_w(fbody, hs, 9), cy + 62), hs, fbody, 9, Color(BONE, 0.75), 1)


# ------------------------------------------------------------------ boss çubuğu
## v22: mürekkep fırçası boss çubuğu: geniş kızıl darbe, gecikmeli "hasar parçası" (kemik rengi, 0,6 sn bekler,
## sonra erir), evre çentikleri (%66 / %33; geçilen evre kızıl mühürle işaretlenir), ad + lakap, sersem / kırık uyarısı
static var _b_lag := 1.0
static var _b_hold := 0.0
static var _b_k := 1.0
static var _b_t := -1.0
static var _b_flash := 0.0
static var _b_id := 0


static func boss_bar(h: Control, vp: Vector2, name: String, k: float, t: float, boss: Node = null) -> void:
	var bid := boss.get_instance_id() if boss else 0
	if bid != _b_id or _b_t < 0.0:
		_b_id = bid
		_b_lag = k
		_b_k = k
		_b_t = t
	var dt := clampf(t - _b_t, 0.0, 0.1)
	_b_t = t
	if k < _b_k - 0.0005:
		_b_hold = 0.6
		_b_flash = 1.0
	_b_k = k
	if _b_lag < k:
		_b_lag = k
	if _b_hold > 0.0:
		_b_hold -= dt
	else:
		_b_lag = move_toward(_b_lag, k, dt * maxf(0.08, (_b_lag - k) * 2.0))
	_b_flash = maxf(0.0, _b_flash - dt * 5.0)
	var bw := 330.0
	var bx := (vp.x - bw) / 2.0
	var y := vp.y - 70.0   # yuvaların ve halkaların (F / R / G) üstünde
	var bh := 9.0
	InkUI.wash(h, Rect2(bx - 90, y - 40, bw + 180, 64), 0.78)
	var red := Color(0.95, 0.42, 0.38)
	# ad ve lakap
	var fc := InkUI.font("caps")
	var nm := tr_upper(name)
	var nw := str_w(fc, nm, 13)
	InkUI.draw_str(h, Vector2((vp.x - nw) * 0.5, y - 16), nm, fc, 13, red, 2)
	var sub := ""
	if boss:
		for b in Data.world.get("bosses", []):
			if String(b.get("enemy", "")) == String(boss.kind):
				sub = String(b.get("sub", ""))
	if sub != "":
		var fb := InkUI.font("body")
		var sw := str_w(fb, sub, 8)
		InkUI.draw_str(h, Vector2((vp.x - sw) * 0.5, y - 6), sub, fb, 8, Color(BONE, 0.6), 1)
	InkUI.tamga(h, 0, Vector2((vp.x - nw) * 0.5 - 13, y - 20), 10.0, Color(red, 0.8))
	InkUI.tamga(h, 0, Vector2((vp.x + nw) * 0.5 + 13, y - 20), 10.0, Color(red, 0.8))
	# çubuk: kalın mürekkep darbe, koyu oluk, gecikmeli parça, kızıl dolgu
	var st := InkUI.tex("stroke")
	var ts := st.get_size()
	var br := Rect2(bx, y + 3, bw, bh)
	var broken := false
	var stunned := false
	if boss:
		broken = float(boss.broken_t) > 0.0
		stunned = float(boss.stun_t) > 0.0
	var edge := Color(InkUI.INK, 0.95)
	if stunned or broken:
		edge = Color(1.0, 0.7, 0.3, 0.55 + 0.35 * sin(t * 14.0))
	h.draw_texture_rect(st, Rect2(br.position.x - 6, br.position.y - 4.5, br.size.x + 12, br.size.y + 9), false, edge)
	h.draw_texture_rect(st, br, false, Color(0.16, 0.02, 0.03, 1.0))
	if _b_lag > k + 0.001:
		var lc := Color(1.0, 0.86, 0.62).lerp(Color.WHITE, _b_flash * 0.5)
		h.draw_texture_rect_region(st, Rect2(bx + bw * k, br.position.y + 0.5, bw * (_b_lag - k), bh - 1.0), Rect2(ts.x * k, 0, ts.x * (_b_lag - k), ts.y), Color(lc, 0.95))
	if k > 0.0:
		var fcol := Color(0.8, 0.09, 0.1).lerp(Color(1.0, 0.9, 0.85), _b_flash * 0.25)
		h.draw_texture_rect_region(st, Rect2(bx, br.position.y, bw * k, bh), Rect2(0, 0, ts.x * k, ts.y), fcol)
		h.draw_texture_rect_region(st, Rect2(bx + 2, br.position.y + bh * 0.14, maxf(0.0, bw * k - 4.0), bh * 0.26), Rect2(0, ts.y * 0.2, ts.x * k, ts.y * 0.5), Color(1.0, 0.55, 0.5, 0.45))
		InkUI.splat(h, Vector2(bx + bw * k, br.get_center().y), bh * 1.5, Color(1.0, 0.4, 0.32, 0.9), t * 0.5)
	# evre çentikleri: geçilen evrede kızıl mühür
	for i in range(1, 3):
		var pk := 1.0 - i / 3.0
		var xx := bx + bw * pk
		h.draw_line(Vector2(xx, br.position.y - 3), Vector2(xx + 1.2, br.end.y + 3), Color(InkUI.INK, 0.95), 2.0, true)
		if k < pk:
			InkUI.seal(h, Rect2(xx - 3.5, br.end.y + 3.5, 7, 7), Color(InkUI.SEAL, 0.9))
	InkUI.quad(h, InkUI.tex("horn"), Vector2(bx - 15, br.get_center().y), Vector2(20, 17), -PI * 0.5, red)
	InkUI.quad(h, InkUI.tex("horn"), Vector2(bx + bw + 15, br.get_center().y), Vector2(20, 17), PI * 0.5, red)
	if broken or stunned:
		var fb2 := InkUI.font("caps")
		var s2 := "DURUŞ KIRIK" if broken else "SERSEM"
		InkUI.draw_str(h, Vector2(bx + bw - str_w(fb2, s2, 8), br.end.y + 12), s2, fb2, 8, Color(1.0, 0.75, 0.4, 0.9), 1)


# ------------------------------------------------------------------ sağ üst: yer adı
static func place(h: Control, vp: Vector2, place_name: String, info: String, col: Color) -> void:
	var fc := InkUI.font("caps")
	var nm := tr_upper(place_name)
	var nw := str_w(fc, nm, 11)
	var fb := InkUI.font("body")
	var iw := str_w(fb, info, 9) + 12.0
	var w := maxf(nw, iw) + 24.0
	var x := vp.x - 10.0 - w
	InkUI.wash(h, Rect2(x - 40, -12, w + 80, 70), 0.62)
	InkUI.draw_str(h, Vector2(x + (w - nw) * 0.5, 20), nm, fc, 11, col, 2)
	var st := InkUI.tex("stroke")
	h.draw_texture_rect(st, Rect2(x + w * 0.2, 24, w * 0.6, 2.0), false, Color(col, 0.6))
	var ix := x + (w - iw) * 0.5
	InkUI.draw_str(h, Vector2(ix, 35), info, fb, 9, Color(BONE, 0.72), 1)
	InkUI.icon_at(h, "kafatasi", Vector2(ix + iw - 4, 31.5), 9.0, Color(BONE, 0.7), false)


# ------------------------------------------------------------------ usul ölçeri
static func usul(h: Control, vp: Vector2, u: Dictionary, streak: int, flash: float) -> void:
	var mw := 128.0
	var mx := vp.x - 10.0 - mw
	var my := 128.0
	var gold := Color(1.0, 0.85, 0.45)
	InkUI.wash(h, Rect2(mx - 26, my - 12, mw + 44, 40), 0.5)
	var st := InkUI.tex("stroke")
	h.draw_texture_rect(st, Rect2(mx - 3, my, mw + 6, 6), false, Color(InkUI.INK, 0.9))
	h.draw_texture_rect(st, Rect2(mx, my + 2.2, mw, 1.6), false, Color(gold, 0.35 + 0.5 * flash))
	for i in (u["starts"] as Array).size():
		var sx := mx + float(u["starts"][i]) * mw
		var hh := 10.0 if i == 0 else 6.0
		h.draw_line(Vector2(sx, my + 3 - hh / 2.0), Vector2(sx + 0.6, my + 3 + hh / 2.0), Color(gold, 0.95 if i == 0 else 0.65), 2.0 if i == 0 else 1.3, true)
	var cxm := mx + float(u["k"]) * mw
	var near := absf(float(u["d"])) <= 0.085
	InkUI.quad(h, st, Vector2(cxm, my + 3), Vector2(14, 3.2), PI * 0.5, Color(1, 1, 1, 0.95) if near else Color(BONE, 0.7))
	if near:
		InkUI.splat(h, Vector2(cxm, my + 3), 12.0, Color(gold, 0.35))
	var lbl := "usul" if streak < 2 else "USUL x%d" % streak
	PixUI.text(h, Vector2(mx - 60, my + 9), lbl, gold.lerp(Color.WHITE, flash * 0.6), 1, HORIZONTAL_ALIGNMENT_RIGHT, mw + 60, 2)


# ------------------------------------------------------------------ bölüm girişi ve ekran başlıkları
static func banner(h: Control, vp: Vector2, title: String, sub: String, col: Color, a: float) -> void:
	var y := 96.0
	InkUI.wash(h, Rect2(vp.x * 0.5 - 330, y - 30, 660, 100), 0.7 * a)
	var fb := InkUI.font("brush")
	var t := InkUI.tr_title(title)
	var tw := str_w(fb, t, 34)
	var x0 := (vp.x - tw) / 2.0
	_fade_str(h, Vector2(x0, y + 26), t, fb, 34, col, a, 7)
	var lw := 70.0 * a
	var st := InkUI.tex("stroke")
	h.draw_texture_rect(st, Rect2(x0 - 16 - lw, y + 15, lw, 2.5), false, Color(col, a * 0.8))
	h.draw_texture_rect(st, Rect2(x0 + tw + 16, y + 15, lw, 2.5), false, Color(col, a * 0.8))
	InkUI.quad(h, InkUI.tex("horn"), Vector2(x0 - 10, y + 16), Vector2(12, 10), -PI * 0.5, Color(col, a))
	InkUI.quad(h, InkUI.tex("horn"), Vector2(x0 + tw + 10, y + 16), Vector2(12, 10), PI * 0.5, Color(col, a))
	# alt satır: başlığın fırça kuyruklarından ayrık (y + 42), arkasında kendi koyu yıkaması; tek katman yazı
	var fs := InkUI.font("body")
	var sw := str_w(fs, sub, 11)
	InkUI.wash(h, Rect2(vp.x * 0.5 - sw * 0.5 - 24, y + 33, sw + 48, 20), 0.6 * a)
	_fade_str(h, Vector2((vp.x - sw) * 0.5, y + 47), sub, fs, 11, BONE, a, 3)


static func _fade_str(h: Control, p: Vector2, t: String, f: Font, size: int, col: Color, a: float, outline: int) -> void:
	## Solan başlık yazısı: InkUI.draw_str'in kaydırılmış gölge kopyası yarı saydamken ana yazının içinden
	## görünüp metni iki kat (üst üste binmiş) gösteriyordu. Burada gölge yalnızca tam görünürken çizilir,
	## dış çizgi a² ile ana yazıdan hızlı söner: geçiş boyunca tek, okunur bir yazı kalır.
	if a >= 0.99:
		h.draw_string(f, p + Vector2(0.8, 1.1), t, HORIZONTAL_ALIGNMENT_LEFT, -1, size, Color(InkUI.INK, 0.5))
	h.draw_string_outline(f, p, t, HORIZONTAL_ALIGNMENT_LEFT, -1, size, outline, Color(InkUI.INK, 0.85 * a * a))
	h.draw_string(f, p, t, HORIZONTAL_ALIGNMENT_LEFT, -1, size, Color(col, a))


static func title_wash(h: Control, vp: Vector2, y: float, has_sub: bool, a: float) -> void:
	InkUI.wash(h, Rect2(vp.x * 0.5 - 300, y - 22, 600, 70 if has_sub else 56), 0.72 * a)


# ================================================================== menü ekranları
static func wrap_f(s: String, f: Font, size: int, maxw: float) -> Array:
	var out: Array = []
	var cur := ""
	for wd in s.split(" "):
		var t: String = (cur + " " + wd).strip_edges()
		if str_w(f, t, size) > maxw and cur != "":
			out.append(cur)
			cur = wd
		else:
			cur = t
	if cur != "":
		out.append(cur)
	return out


static func seal_mark(h: Control, c: Vector2, s: float, tamga_i: int, a := 1.0) -> void:
	## Kızıl kare mühür, ortasında kâğıt renginde tamga (sanatçı mührü gibi)
	InkUI.seal(h, Rect2(c - Vector2(s, s) * 0.5 + Vector2(0.8, 1.0), Vector2(s, s)), Color(0, 0, 0, 0.4 * a))
	InkUI.seal(h, Rect2(c - Vector2(s, s) * 0.5, Vector2(s, s)), Color(InkUI.SEAL, 0.95 * a))
	InkUI.tamga(h, tamga_i, c, s * 0.62, Color(InkUI.PAPER, 0.92 * a))


static func title_top(h: Control, vp: Vector2, t: float) -> void:
	## Başlık ekranı: mürekkep sıçrantısı üstünde fırça yazısı, kızıl alt çizgi ve Kayı mührü
	h.draw_rect(Rect2(Vector2.ZERO, vp), Color(0.02, 0.02, 0.03, 0.4))
	InkUI.vignette(h, vp, 0.95)
	var bob := sin(t * 1.5) * 1.5
	var cy := 96.0 + bob
	InkUI.wash(h, Rect2(vp.x * 0.5 - 320, cy - 78, 640, 176), 0.85)
	InkUI.splat(h, Vector2(vp.x * 0.5 - 70, cy - 2), 170.0, Color(InkUI.INK, 0.5), 0.5)
	InkUI.splat(h, Vector2(vp.x * 0.5 + 110, cy + 10), 110.0, Color(InkUI.SEAL.darkened(0.5), 0.35), 2.1)
	var fb := InkUI.font("brush")
	var s := "Kut'un Yolu"
	var size := 62
	var tw := str_w(fb, s, size)
	var x0 := (vp.x - tw) * 0.5
	var st := InkUI.tex("stroke")
	h.draw_texture_rect(st, Rect2(x0 - 6, cy + 22, tw + 6, 7), false, Color(InkUI.INK, 0.9))
	h.draw_texture_rect(st, Rect2(x0 + 4, cy + 23, tw - 14, 4.5), false, Color(InkUI.SEAL, 0.95))
	InkUI.draw_str(h, Vector2(x0, cy + 18), s, fb, size, BONE, 2, 3)
	seal_mark(h, Vector2(x0 + tw + 20, cy - 18), 24.0, 0)
	InkUI.quad(h, InkUI.tex("horn"), Vector2(x0 - 22, cy + 6), Vector2(18, 15), -PI * 0.5, Color(PixUI.GOLD, 0.9))
	var fl := InkUI.font("lore")
	var sub := "Erlik'in zincirini kır, Ulu Kayın'ı kurtar"
	InkUI.draw_str(h, Vector2((vp.x - str_w(fl, sub, 12)) * 0.5, cy + 46), sub, fl, 12, Color(0.72, 0.92, 1.0), 2)
	var a := 0.55 + 0.45 * sin(t * 3.0)
	var ps := "Başlamak için Boşluk / Enter"
	var fbd := InkUI.font("bold")
	var pw := str_w(fbd, ps, 11)
	h.draw_texture_rect(InkUI.tex("swash"), Rect2((vp.x - pw) * 0.5 - 22, 172, pw + 44, 22), false, Color(InkUI.INK, 0.85))
	h.draw_texture_rect(st, Rect2((vp.x - pw) * 0.5 - 8, 191, pw + 16, 2.2), false, Color(PixUI.GOLD, 0.8 * a))
	InkUI.draw_str(h, Vector2((vp.x - pw) * 0.5, 187), ps, fbd, 11, Color(BONE, 0.45 + 0.55 * a), 1)


static func paper_lines(h: Control, vp: Vector2, lines: Array, y_mid: float, pw: float, size := 12, lh := 16.0) -> Rect2:
	## Parşömen üstünde koyu mürekkep anlatı (ortalanmış satırlar); parşömen dikdörtgenini döndürür
	var fl := InkUI.font("lore")
	var hh := lines.size() * lh + 46.0
	var r := Rect2((vp.x - pw) * 0.5, roundf(y_mid - hh * 0.5), pw, hh)
	InkUI.paper(h, r)
	var y := r.position.y + 28.0
	var ink := Color(0.15, 0.1, 0.07)
	for l in lines:
		var s := String(l)
		if s != "":
			InkUI.draw_str(h, Vector2((vp.x - str_w(fl, s, size)) * 0.5, y + 9), s, fl, size, ink, 0)
		y += lh
	return r


static func intro(h: Control, vp: Vector2, lines: Array, i: int) -> void:
	h.draw_rect(Rect2(Vector2.ZERO, vp), Color(0.03, 0.025, 0.04, 0.8))
	InkUI.vignette(h, vp, 0.9)
	var s: String = lines[mini(i, lines.size() - 1)]
	var ws := wrap_f(s, InkUI.font("lore"), 13, 380.0)
	ws.push_front("")
	ws.push_back("")
	var r := paper_lines(h, vp, ws, 150.0, 440.0, 13, 17.0)
	seal_mark(h, Vector2(r.end.x - 26, r.end.y - 24), 18.0, i % 4, 0.9)
	var n := lines.size()
	var dx := vp.x * 0.5 - (n - 1) * 5.0
	for k in n:
		var c := Vector2(dx + k * 10.0, r.end.y + 12)
		if k == i:
			InkUI.splat(h, c, 12.0, Color(PixUI.GOLD, 0.95), float(k))
		else:
			h.draw_circle(c, 1.8, Color(BONE, 0.35), true, -1.0, true)


static func ozan(h: Control, vp: Vector2, said: Array) -> void:
	var fl := InkUI.font("lore")
	var all_l: Array = []
	for s in said:
		all_l.append_array(wrap_f("«" + String(s) + "»", fl, 12, 400.0))
		all_l.append("")
	all_l.pop_back()
	var r := paper_lines(h, vp, all_l, 66.0 + (all_l.size() * 15.0 + 46.0) * 0.5, 450.0, 12, 15.0)
	seal_mark(h, Vector2(r.end.x - 24, r.end.y - 22), 16.0, 1, 0.9)


static func ad_backdrop(h: Control, vp: Vector2, kn: float, name := "") -> void:
	## Ad töreni: adın arkasında mürekkep sıçrantısı ve yıkama
	InkUI.splat(h, Vector2(vp.x * 0.5, 146), 200.0 * (0.7 + 0.3 * kn), Color(InkUI.INK, 0.75 * kn), 0.8)
	InkUI.wash(h, Rect2(vp.x * 0.5 - 220, 112, 440, 70), 0.7 * kn)
	InkUI.splat(h, Vector2(vp.x * 0.5 + 60, 150), 90.0, Color(PixUI.GOLD.darkened(0.6), 0.3 * kn), 2.4)
	if name != "" and kn > 0.0:
		# adın sağında ozanın kızıl mührü (Kayı tamgası), altında fırça çizgisi
		var w := InkUI.width(name, 3)
		var st := InkUI.tex("stroke")
		h.draw_texture_rect(st, Rect2(vp.x * 0.5 - w * 0.5, 162, w, 5), false, Color(InkUI.SEAL, 0.9 * kn))
		seal_mark(h, Vector2(vp.x * 0.5 + w * 0.5 + 18, 134), 20.0 * (1.6 - 0.6 * kn), 0, kn)


static func dead_backdrop(h: Control, vp: Vector2, e: float) -> void:
	InkUI.splat(h, Vector2(vp.x * 0.5 - 120, 110), 150.0 * e, Color(0.45, 0.03, 0.04, 0.55), 0.3)
	InkUI.splat(h, Vector2(vp.x * 0.5 + 150, 96), 110.0 * e, Color(0.4, 0.02, 0.03, 0.45), 1.9)
