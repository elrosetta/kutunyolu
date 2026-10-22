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
## v40 mürekkep dolum: gösterilen can oranı hedefe doğru akar (hasar: hızlı çekilme, kızıl sıçrantı; şifa: yavaş yayılan
## mürekkep), fırça ucunda nabız atan mürekkep lekesi
static var _hp_show := -1.0
static var _hp_t := -1.0
static var _hp_hit := 0.0
static var _hp_heal := 0.0


static func top_left(h: Control, R: Dictionary, hp: float, mhp: float, hpk: float, lag: float, t: float, kut_pulse: float) -> float:
	var x0 := 8.0
	var y0 := 8.0
	InkUI.wash(h, Rect2(-40, -14, 310, 90), 0.7)
	var low := hpk < 0.3
	var dt := clampf(t - _hp_t, 0.0, 0.1) if _hp_t >= 0.0 else 0.0
	_hp_t = t
	if _hp_show < 0.0:
		_hp_show = hpk
	if hpk < _hp_show - 0.0005:
		if _hp_hit <= 0.0:
			_hp_hit = 1.0
		_hp_show = move_toward(_hp_show, hpk, dt * maxf(2.5, (_hp_show - hpk) * 12.0))
	elif hpk > _hp_show + 0.0005:
		_hp_heal = 1.0
		_hp_show = move_toward(_hp_show, hpk, dt * maxf(0.5, (hpk - _hp_show) * 2.2))
	_hp_hit = maxf(0.0, _hp_hit - dt * 3.0)
	_hp_heal = maxf(0.0, _hp_heal - dt * 1.2)
	# can: kızıl mürekkep yürek + fırça çubuğu
	var hc := Vector2(x0 + 9, y0 + 9)
	var hcol := HP_RED.lightened(0.15) if not (low and int(t * 5.0) % 2 == 0) else Color(1.0, 0.62, 0.5)
	if _hp_hit > 0.0:
		InkUI.splat(h, hc, 26.0 + 14.0 * (1.0 - _hp_hit), Color(HP_RED, 0.45 * _hp_hit), t)
	InkUI.icon_at(h, "can", hc, 21.0 + 3.0 * _hp_hit, hcol)
	var br := Rect2(x0 + 24, y0 + 4, 164, 10)
	InkUI.bar(h, br, 0.0, Color(0, 0, 0, 0), Color(0.16, 0.03, 0.04, 1.0))
	InkUI.bar(h, br, lag, Color(BONE, 0.8), Color(0, 0, 0, 0))
	var fc := HP_RED if not low else Color(0.95, 0.22 + 0.12 * sin(t * 10.0), 0.18)
	if _hp_heal > 0.0:
		fc = fc.lerp(Color(1.0, 0.55, 0.45), 0.4 * _hp_heal)
	InkUI.bar(h, br, _hp_show, fc, Color(0, 0, 0, 0))
	# fırça ucu: dolumun ucunda mürekkep lekesi (hasarda kızıl sıçrar)
	var tip := Vector2(br.position.x - 2.0 + (br.size.x + 4.0) * _hp_show, br.get_center().y)
	if _hp_show > 0.02:
		InkUI.splat(h, tip, br.size.y * (1.5 + 0.25 * sin(t * 6.0)) + 8.0 * _hp_hit, Color(fc.lightened(0.2), 0.9), t * 0.3)
	if _hp_hit > 0.0:
		for i in 4:
			var ang := -0.9 + i * 0.6 + float(int(t * 7.0) % 3) * 0.1
			var p := tip + Vector2.from_angle(ang) * (6.0 + 12.0 * (1.0 - _hp_hit))
			h.draw_circle(p, 1.6 * _hp_hit, Color(HP_RED, 0.85 * _hp_hit), true, -1.0, true)
	var f := InkUI.font("bold")
	var s := "%d / %d" % [int(ceil(hp)), int(mhp)]
	InkUI.draw_str(h, Vector2(br.position.x + (br.size.x - str_w(f, s, 10)) * 0.5, br.position.y + 8.5), s, f, 10, BONE, 2)
	# plakanın alt kenarı: ince altın kilim şeridi (v40 kimlik çizgisi)
	InkUI.kilim(h, Rect2(x0, y0 + 53.5, 150.0, 2.6), Color(InkUI.GOLD, 0.35))
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
		# v40: boş yuva "kutu" değil, soluk bir tamga filigranı + küçük yazıt
		InkUI.tamga(h, 2 if key in ["melee", "second"] else 3, r.get_center() + Vector2(0, -2), 16.0, Color(BONE, 0.13))
		InkUI.draw_str(h, Vector2(r.position.x + (r.size.x - str_w(InkUI.font("caps"), "BOŞ", 7)) * 0.5, r.end.y - 5.0), "BOŞ", InkUI.font("caps"), 7, Color(PixUI.DIM, 0.5), 0)
	else:
		PixUI.weapon(h, it, r.get_center() + Vector2(0, -1), r.size - Vector2(8, 9))
		PixUI.ongun_stripe(h, Rect2(r.position.x + 4, r.end.y - 3.5, r.size.x - 8, 2.2), Game.item_onguns(it), Game.item_best_ongun(it))
		Unsur.slot_badge(h, r, it, Time.get_ticks_msec() / 1000.0)   # v20 unsur simgesi
	if pl.cd.has(key) and pl.cd[key] > 0.0:
		var k := clampf(pl.cd[key] / maxf(0.01, pl.cd_max[key]), 0.0, 1.0)
		var hh := r.size.y * k
		InkUI.nine(h, Rect2(r.position.x, r.end.y - hh, r.size.x, hh), InkUI.tex("fill"), 32.0, Color(0.0, 0.0, 0.02, 0.72))
		# v40 bekleme yayı: çerçevenin üst kenarı boyunca kalan süre oranında kızıl fırça çizgisi (sağdan erir)
		var st := InkUI.tex("stroke")
		var ts := st.get_size()
		h.draw_texture_rect_region(st, Rect2(r.position.x + 2.0, r.position.y - 1.6, (r.size.x - 4.0) * k, 2.4), Rect2(0, 0, ts.x * k, ts.y), Color(InkUI.VERMILION, 0.9))
		if key in ["g1", "g2"] and pl.cd[key] >= 1.0:
			var fb := InkUI.font("brush")
			var cs := str(int(ceil(pl.cd[key])))
			InkUI.draw_str(h, Vector2(r.position.x + (r.size.x - str_w(fb, cs, 15)) * 0.5, r.position.y + r.size.y * 0.5 + 5.0), cs, fb, 15, BONE, 2, 2)
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
	InkUI.wash(h, Rect2(bx - 90, y - 44, bw + 180, 70), 0.8)
	var red := Color(0.95, 0.42, 0.38)
	# v40 ad levhası: kilim şeridi + iki yanda tamga mühürleri, Cinzel ad, altında lakap
	var fc := InkUI.font("caps")
	var nm := tr_upper(name)
	var nw := str_w(fc, nm, 13)
	var pw := nw + 70.0
	InkUI.kilim(h, Rect2((vp.x - pw) * 0.5, y - 31.0, pw, 3.2), Color(InkUI.GOLD, 0.55))
	InkUI.draw_str(h, Vector2((vp.x - nw) * 0.5, y - 16), nm, fc, 13, red, 2)
	var sub := ""
	if boss:
		for b in Data.world.get("bosses", []):
			if String(b.get("enemy", "")) == String(boss.kind):
				sub = String(b.get("sub", ""))
	if sub != "":
		var fb := InkUI.font("body")
		var sw := str_w(fb, sub, 8)
		InkUI.draw_str(h, Vector2((vp.x - sw) * 0.5, y - 6), sub, fb, 8, Color(BONE, 0.65), 1)
	for sx in [-1.0, 1.0]:
		var c := Vector2(vp.x * 0.5 + sx * (nw * 0.5 + 16.0), y - 20.0)
		InkUI.seal_round(h, c + Vector2(0.8, 1.0), 13.0, Color(0, 0, 0, 0.4), 0.2)
		InkUI.seal_round(h, c, 13.0, Color(InkUI.VERMILION, 0.95), 0.2)
		InkUI.tamga(h, 0, c, 7.5, Color(InkUI.PAPER, 0.92))
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
	InkUI.kilim(h, Rect2(x + w * 0.15, 23.5, w * 0.7, 2.4), Color(col, 0.5))   # v40: kilim ayracı
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
static func banner(h: Control, vp: Vector2, title: String, sub: String, col: Color, a: float, p := 1.0) -> void:
	## v40 fırça açılışı: başlık harf harf "yazılır" (p 0 -> 1; kalemin ucunda mürekkep lekesi), yan çizgiler
	## kalemle birlikte uzar, iki yanda Köktürk harf aksanı belirir; alt satır yazı bitince gelir
	var y := 96.0
	InkUI.wash(h, Rect2(vp.x * 0.5 - 330, y - 30, 660, 100), 0.7 * a)
	var fb := InkUI.font("brush")
	var t := InkUI.tr_title(title)
	var tw := str_w(fb, t, 34)
	var x0 := (vp.x - tw) / 2.0
	var pp := clampf(p, 0.0, 1.0)
	var n := t.length()
	var shown := clampi(int(ceil(pp * n)), 0, n)
	var ts := t.substr(0, shown)
	_fade_str(h, Vector2(x0, y + 26), ts, fb, 34, col, a, 7)
	if pp < 1.0 and shown > 0:
		# kalem ucu: son harfin sağında mürekkep lekesi ve küçük sıçrantı
		var tipx := x0 + str_w(fb, ts, 34)
		InkUI.splat(h, Vector2(tipx + 2.0, y + 16.0), 16.0, Color(col, 0.8 * a), pp * 6.0)
		h.draw_circle(Vector2(tipx + 8.0 + 6.0 * pp, y + 8.0 - 10.0 * pp), 1.4, Color(col, 0.7 * a), true, -1.0, true)
	var lw := 70.0 * a * pp
	var st := InkUI.tex("stroke")
	h.draw_texture_rect(st, Rect2(x0 - 16 - lw, y + 15, lw, 2.5), false, Color(col, a * 0.8))
	h.draw_texture_rect(st, Rect2(x0 + tw + 16, y + 15, lw, 2.5), false, Color(col, a * 0.8))
	InkUI.quad(h, InkUI.tex("horn"), Vector2(x0 - 10, y + 16), Vector2(12, 10), -PI * 0.5, Color(col, a * pp))
	InkUI.quad(h, InkUI.tex("horn"), Vector2(x0 + tw + 10, y + 16), Vector2(12, 10), PI * 0.5, Color(col, a * pp))
	# Köktürk harf aksanları: çizgilerin dışında, soluk
	var oa := a * clampf((pp - 0.5) * 2.0, 0.0, 1.0) * 0.45
	if oa > 0.0:
		InkUI.orkhon(h, Rect2(x0 - 16 - lw - 70.0, y + 9.0, 60.0, 12.0), Color(col, oa))
		InkUI.orkhon(h, Rect2(x0 + tw + 16 + lw + 10.0, y + 9.0, 60.0, 12.0), Color(col, oa))
	# alt satır: başlığın fırça kuyruklarından ayrık (y + 42), arkasında kendi koyu yıkaması; tek katman yazı
	var sa := a * clampf((pp - 0.7) / 0.3, 0.0, 1.0)
	if sa > 0.0:
		var fs := InkUI.font("body")
		var sw := str_w(fs, sub, 11)
		InkUI.wash(h, Rect2(vp.x * 0.5 - sw * 0.5 - 24, y + 33, sw + 48, 20), 0.6 * sa)
		_fade_str(h, Vector2((vp.x - sw) * 0.5, y + 47), sub, fs, 11, BONE, sa, 3)


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
	## v40 sinematik başlık: süzülen mürekkep dumanı (fare / zamanla hafif paralaks), kuru fırça kaligrafi logosu
	## (logo.png), kızıl alt çizgi, Kayı mührü, Köktürk harf aksanı, "Başla" yuvarlak mührü
	h.draw_rect(Rect2(Vector2.ZERO, vp), Color(0.02, 0.02, 0.03, 0.45))
	InkUI.vignette(h, vp, 0.95)
	# paralaks: fare konumu (yoksa yavaş salınım)
	var mp := h.get_viewport().get_mouse_position() / HUD.MENU_SCALE
	var par := Vector2.ZERO
	if Rect2(Vector2.ZERO, vp).has_point(mp):
		par = (mp - vp * 0.5) / vp * 6.0
	else:
		par = Vector2(sin(t * 0.4), cos(t * 0.3)) * 2.0
	# mürekkep dumanı: üç leke, ağır ağır kayar ve döner
	var sm := InkUI.tex("smoke")
	var smokes := [[Vector2(-170, 20), 260.0, 0.07, 0.55, InkUI.INK], [Vector2(150, 50), 220.0, -0.05, 0.42, InkUI.INK],
		[Vector2(40, -40), 180.0, 0.09, 0.28, InkUI.SEAL.darkened(0.55)]]
	for i in smokes.size():
		var d: Array = smokes[i]
		var c: Vector2 = Vector2(vp.x * 0.5, 100.0) + (d[0] as Vector2) + Vector2(sin(t * 0.17 + i * 2.1), cos(t * 0.13 + i)) * 14.0 - par * (1.5 + i * 0.6)
		InkUI.quad(h, sm, c, Vector2.ONE * float(d[1]) * (1.0 + 0.04 * sin(t * 0.3 + i)), t * float(d[2]) + i, Color(d[4] as Color, float(d[3])))
	var bob := sin(t * 1.1) * 1.2
	var cy := 92.0 + bob
	InkUI.wash(h, Rect2(vp.x * 0.5 - 330, cy - 70, 660, 170), 0.8)
	# logo: gölge kopyası + kemik rengi kaligrafi
	var lg := InkUI.tex("logo")
	var lw := 470.0
	var lh := lw * 768.0 / 2048.0
	var lc := Vector2(vp.x * 0.5, cy - 6.0) - par * 0.6
	if lg:
		h.draw_texture_rect(lg, Rect2(lc - Vector2(lw, lh) * 0.5 + Vector2(3.0, 4.0), Vector2(lw, lh)), false, Color(InkUI.INK, 0.9))
		h.draw_texture_rect(lg, Rect2(lc - Vector2(lw, lh) * 0.5, Vector2(lw, lh)), false, BONE)
	var tw := lw * 0.72
	var x0 := lc.x - tw * 0.5
	var st := InkUI.tex("stroke")
	h.draw_texture_rect(st, Rect2(x0 - 6, cy + 38, tw + 6, 7), false, Color(InkUI.INK, 0.9))
	h.draw_texture_rect(st, Rect2(x0 + 4, cy + 39, tw - 14, 4.5), false, Color(InkUI.VERMILION, 0.95))
	seal_mark(h, Vector2(x0 + tw + 26, cy - 30) - par * 0.6, 24.0, 0)
	InkUI.quad(h, InkUI.tex("horn"), Vector2(x0 - 24, cy + 20) - par * 0.6, Vector2(18, 15), -PI * 0.5, Color(InkUI.GOLD, 0.9))
	var fl := InkUI.font("lore")
	var sub := "Erlik'in zincirini kır, Ulu Kayın'ı kurtar"
	InkUI.draw_str(h, Vector2((vp.x - str_w(fl, sub, 12)) * 0.5, cy + 60), sub, fl, 12, Color(0.72, 0.92, 1.0), 2)
	InkUI.orkhon(h, Rect2(vp.x * 0.5 - 120, cy + 68, 240, 11), Color(InkUI.GOLD, 0.32))
	# Başla mührü: nabız atan kızıl yuvarlak damga, içinde fırça yazısı
	var k := InkUI.pulse(t, 0.6)
	var bc := Vector2(vp.x * 0.5, 212.0)
	var bs := 50.0 + 2.5 * k
	InkUI.seal_round(h, bc + Vector2(1.2, 1.6), bs, Color(0, 0, 0, 0.5), -0.12)
	InkUI.seal_round(h, bc, bs, Color(InkUI.VERMILION, 0.95), -0.12)
	var fb := InkUI.font("brush")
	var bt := "Başla"
	var bw := str_w(fb, bt, 17)
	h.draw_set_transform(bc * HUD.MENU_SCALE, -0.12, Vector2.ONE * HUD.MENU_SCALE)
	h.draw_string(fb, Vector2(-bw * 0.5 + 0.8, 6.8), bt, HORIZONTAL_ALIGNMENT_LEFT, -1, 17, Color(InkUI.INK, 0.45))
	h.draw_string(fb, Vector2(-bw * 0.5, 6.0), bt, HORIZONTAL_ALIGNMENT_LEFT, -1, 17, InkUI.PAPER)
	h.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE * HUD.MENU_SCALE)
	var ps := "Boşluk / Enter"
	var fbd := InkUI.font("bold")
	var pw := str_w(fbd, ps, 9)
	InkUI.draw_str(h, Vector2((vp.x - pw) * 0.5, 249), ps, fbd, 9, Color(BONE, 0.45 + 0.45 * k), 1)


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
