class_name HUD
extends Control
## Piksel arayüz (PixUI): can, şişe, altın, Kut, ongun rozetleri, silah yuvaları (ongun şeritli), Kut göstergesi,
## yerdeki eşya kartı (karşılaştırmalı), yuva seçimi, tılsım seçimi, başlık / hikâye / ölüm / bölüm sonu,
## Umay / Demirci / Ozan ekranları ve duraklatma.

var main: Node
var level: Node
var mode := "title"
var intro_i := 0
var _t := 0.0
var _card_t := 0.0
var sel := 0
var flash_msg := ""
var flash_t := 0.0
var ozan_i := 0
var ad_id := ""
var ad_t := 0.0
var _usul_flash := 0.0
var _last_streak := 0
var slot_opts: Array = []
var _open_t := 1.0
var _hp_lag := -1.0
var _kut_pulse := 0.0
var _last_mode := ""
var _ducked := false
var back_mode := "title"   # ayarlar ekranı kapanınca dönülecek mod

const SLOT_KEYS := {"melee": "J", "second": "K", "g1": "U", "g2": "I"}
const SLOT_NAMES := {"melee": "1. silah", "second": "2. silah", "g1": "1. teçhizat", "g2": "2. teçhizat"}
const CAT_TXT := {"weapons": "Silah", "shields": "Kalkan", "gadgets": "Teçhizat"}
const ONGUN_KEYS := ["kurt", "kartal", "ayi"]


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	material = Game.hd_material()  # 2K/4K: yazı ve simgeler de Scale2x/4x ile yumuşar


func _process(delta: float) -> void:
	_t += delta
	_card_t += delta
	flash_t -= delta
	_open_t = minf(1.0, _open_t + delta * 6.0)
	_kut_pulse = maxf(0.0, _kut_pulse - delta)
	ad_t += delta
	_usul_flash = maxf(0.0, _usul_flash - delta * 3.0)
	if mode != _last_mode:
		if mode in ["tilsim", "slot", "umay", "demirci", "ozan", "dead", "done", "ad"]:
			_open_t = 0.0
		_last_mode = mode
	# menülerde ses kısılır (Ses.menu_duck varsa)
	var menu := mode != "play" or get_tree().paused
	if menu != _ducked:
		_ducked = menu
		if Ses.has_method("menu_duck"):
			Ses.call("menu_duck", menu)
	queue_redraw()


func open_anim() -> void:
	_open_t = 0.0


func kut_pulse() -> void:
	_kut_pulse = 0.4


func _ease_open() -> float:
	var u := clampf(_open_t, 0.0, 1.0)
	return 1.0 - pow(1.0 - u, 3.0)


func _blink(speed := 3.0) -> float:
	return 0.55 + 0.45 * sin(_t * speed)


func _dim(vp: Vector2, a := 0.72, col := Color(0.02, 0.015, 0.04)) -> void:
	draw_rect(Rect2(Vector2.ZERO, vp), Color(col, a * _ease_open()))
	# kenar karartması (vinyet)
	for i in 6:
		var k := float(6 - i) / 6.0
		draw_rect(Rect2(0, i * 4, vp.x, 4), Color(0, 0, 0, 0.12 * k * _ease_open()))
		draw_rect(Rect2(0, vp.y - (i + 1) * 4, vp.x, 4), Color(0, 0, 0, 0.12 * k * _ease_open()))


func _title(vp: Vector2, y: float, s: String, col := PixUI.GOLD, sub := "") -> void:
	var slide := (1.0 - _ease_open()) * -10.0
	PixUI.text(self, Vector2(0, y + slide), s, col, 2, HORIZONTAL_ALIGNMENT_CENTER, vp.x, 2)
	var tw := PixUI.width(s, 2)
	var x0 := (vp.x - tw) / 2.0
	PixUI.horn(self, Vector2(x0 - 14, y + slide + 8), col, -1)
	PixUI.horn(self, Vector2(x0 + tw + 8, y + slide + 8), col, 1)
	if sub != "":
		PixUI.text(self, Vector2(0, y + 26 + slide), sub, PixUI.TEXT, 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x)


func _hint(vp: Vector2, items: Array, y := -1.0) -> void:
	## Alt bilgi satırı: [[tuş, açıklama], ...] tuş rozetleriyle
	var total := 0.0
	for it in items:
		total += maxf(9.0, PixUI.width(it[0]) + 4.0) + 3.0 + PixUI.width(it[1]) + 12.0
	total -= 12.0
	var x := roundf((vp.x - total) / 2.0)
	var yy := vp.y - 22.0 if y < 0.0 else y
	for it in items:
		PixUI.key_cap(self, Vector2(x, yy), it[0])
		x += maxf(9.0, PixUI.width(it[0]) + 4.0) + 3.0
		PixUI.text(self, Vector2(x, yy), it[1], Color(PixUI.TEXT, 0.85))
		x += PixUI.width(it[1]) + 12.0


func _draw() -> void:
	var vp := get_viewport_rect().size
	if mode == "ayarlar":
		if back_mode == "title" or Game.run.is_empty() or level == null or level.player == null:
			_draw_title(vp)
		else:
			_draw_hud(vp)
		_draw_settings(vp)
		return
	match mode:
		"title":
			_draw_title(vp)
			return
		"intro":
			_draw_intro(vp)
			return
		"demirci":
			_draw_demirci(vp)
			return
		"umay":
			_draw_umay(vp)
			return
		"ozan":
			_draw_ozan(vp)
			return
		"ad":
			_draw_ad(vp)
			return
	if Game.run.is_empty() or level == null or level.player == null:
		return
	var paused_play := mode == "play" and get_tree().paused
	if _card_t < 4.0 and mode == "play" and not paused_play:
		_draw_banner(vp)
	_draw_hud(vp)
	match mode:
		"dead":
			_draw_dead(vp)
		"done":
			_draw_done(vp)
		"tilsim":
			_draw_tilsim(vp)
		"slot":
			_draw_slot(vp)
		"play":
			if get_tree().paused:
				_draw_pause(vp)


func _draw_banner(vp: Vector2) -> void:
	## Bölüm girişi: büyük ad, ince süslü çizgiler
	var a := clampf(minf(_card_t * 2.0, (4.0 - _card_t) * 1.5), 0.0, 1.0)
	var bm: Dictionary = level.biome
	var title: String
	var sub: String
	var col: Color
	if level.hub:
		title = "ULU KAYIN YURDU"
		sub = "Kut'unu Umay Ana'ya götür  ·  Demirci parşömen döver  ·  kapı derine indirir"
		col = Color(0.6, 1.0, 1.0)
	else:
		title = String(bm.get("name", "Kararan Ötüken")).to_upper()
		sub = "%d. derinlik  ·  %s" % [int(Game.run["depth"]), String(bm.get("sub", ""))]
		col = PixUI.GOLD
	var y := 96.0
	var tw := PixUI.width(title, 2)
	var x0 := (vp.x - tw) / 2.0
	draw_rect(Rect2(0, y - 6, vp.x, 50), Color(0.02, 0.01, 0.04, 0.45 * a))
	PixUI.text(self, Vector2(0, y), title, Color(col, a), 2, HORIZONTAL_ALIGNMENT_CENTER, vp.x, 2)
	var lw := 60.0 * a
	draw_rect(Rect2(roundf(x0 - 10 - lw), y + 12, roundf(lw), 1), Color(col, a * 0.8))
	draw_rect(Rect2(roundf(x0 + tw + 10), y + 12, roundf(lw), 1), Color(col, a * 0.8))
	PixUI.text(self, Vector2(0, y + 28), sub, Color(PixUI.TEXT, a), 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x)


# ------------------------------------------------------------------ oyun içi
func _draw_hud(vp: Vector2) -> void:
	var R: Dictionary = Game.run
	var pl: Node = level.player
	# ---- can çubuğu
	var hp := float(R["hp"])
	var mhp := float(R["max_hp"])
	var hpk := clampf(hp / mhp, 0.0, 1.0)
	if _hp_lag < 0.0:
		_hp_lag = hpk
	_hp_lag = hpk if hpk > _hp_lag else lerpf(_hp_lag, hpk, 0.04)
	var bx := 8.0
	var by := 8.0
	var bw := 150.0
	PixUI.panel(self, Rect2(bx, by, bw + 20, 16))
	var low := hpk < 0.3
	PixUI.icon(self, "can", Vector2(bx + 4, by + 5), Color(1.0, 0.35, 0.32) if not (low and int(_t * 5.0) % 2 == 0) else Color(1.0, 0.75, 0.6))
	var br := Rect2(bx + 15, by + 4, bw, 8)
	draw_rect(br, Color(0.18, 0.05, 0.08))
	draw_rect(Rect2(br.position, Vector2(roundf(br.size.x * _hp_lag), br.size.y)), Color(1.0, 0.85, 0.6))
	PixUI.bar(self, br, hpk, Color(0.85, 0.2, 0.2) if not low else Color(0.95, 0.3 + 0.15 * sin(_t * 10.0), 0.28), Color(0, 0, 0, 0))
	for i in range(1, 10):
		draw_rect(Rect2(roundf(br.position.x + br.size.x * i / 10.0), br.position.y + 5, 1, 3), Color(0, 0, 0, 0.25))
	PixUI.text(self, Vector2(br.position.x, by + 2), "%d / %d" % [int(ceil(hp)), int(mhp)], PixUI.TEXT, 1, HORIZONTAL_ALIGNMENT_CENTER, bw, 2)
	# ---- şişe, altın, Kut
	var y2 := by + 20.0
	PixUI.panel(self, Rect2(bx, y2, bw + 20, 15))
	var x := bx + 4.0
	for i in int(R["max_flasks"]):
		var full := i < int(R["flasks"])
		PixUI.icon(self, "sise", Vector2(x, y2 + 4), Color(0.35, 0.9, 0.78) if full else Color(0.3, 0.27, 0.38), 1, full)
		x += 7.0
	PixUI.key_cap(self, Vector2(x + 1, y2 + 2), "Q", PixUI.GOLD, int(R["flasks"]) > 0)
	x += 18.0
	PixUI.icon(self, "altin", Vector2(x, y2 + 5), PixUI.GOLD)
	PixUI.text(self, Vector2(x + 7, y2 + 1), str(R["gold"]), PixUI.GOLD)
	x += 12.0 + PixUI.width(str(R["gold"]))
	var kp := 1.0 + (0.6 if _kut_pulse > 0.0 else 0.0)
	PixUI.icon(self, "kut", Vector2(x, y2 + 4), PixUI.KUT.lightened(0.3 * (kp - 1.0)))
	PixUI.text(self, Vector2(x + 7, y2 + 1), str(int(R["kut"])), PixUI.KUT)
	x += 10.0 + PixUI.width(str(int(R["kut"])))
	PixUI.text(self, Vector2(x, y2 + 1), "(%d)" % int(Game.meta.get("kut_bank", 0)), Color(PixUI.KUT, 0.55), 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
	# ---- ongun rozetleri
	var y3 := y2 + 19.0
	x = bx
	for k in ONGUN_KEYS:
		var col := PixUI.ongun_col(k)
		var lv := int(R["ongun"][k])
		var w := 27.0
		PixUI.panel(self, Rect2(x, y3, w, 13), col.darkened(0.25), PixUI.INK)
		PixUI.icon(self, k, Vector2(x + 3, y3 + 3), col)
		PixUI.text(self, Vector2(x + 12, y3 + 1), str(lv), col.lightened(0.2), 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 1)
		x += w + 3.0
	# ---- silah ve teçhizat yuvaları
	var y0 := vp.y - 40.0
	var sx := 8.0
	for key in ["melee", "second", "g1", "g2"]:
		if key == "g1":
			sx += 6.0
		_draw_slot_box(Rect2(sx, y0, 46, 30), key, pl)
		sx += 50.0
	# ---- Kut göstergesi
	var kx := sx + 16.0
	var ky := y0 + 15.0
	var kk: float = pl.kut / 100.0
	draw_circle(Vector2(kx, ky), 15.0, PixUI.SHADOW)
	draw_circle(Vector2(kx, ky), 14.0, PixUI.INK)
	draw_arc(Vector2(kx, ky), 14.0, 0.0, TAU, 28, PixUI.EDGE, 1.0)
	var full_k := kk >= 1.0
	var acol := PixUI.KUT if not full_k else Color(0.8, 1.0, 1.0, 0.6 + 0.4 * sin(_t * 8.0))
	draw_arc(Vector2(kx, ky), 11.0, -PI / 2.0, -PI / 2.0 + TAU * clampf(kk, 0.0, 1.0), 32, acol, 3.0)
	PixUI.icon(self, "kurt", Vector2(kx - 3, ky - 3), PixUI.KUT if full_k else Color(PixUI.KUT, 0.5), 1, false)
	PixUI.key_cap(self, Vector2(kx - 4, y0 + 25), "F", PixUI.KUT, full_k)
	if pl.wolf_t > 0.0:
		var wx := vp.x / 2.0 - 70.0
		PixUI.panel(self, Rect2(wx, 30, 140, 26), Color(0.4, 0.85, 1.0))
		PixUI.text(self, Vector2(wx, 32), "BOZKURT  %.1f" % pl.wolf_t, Color(0.7, 1.0, 1.0), 1, HORIZONTAL_ALIGNMENT_CENTER, 140, 1)
		PixUI.bar(self, Rect2(wx + 6, 46, 128, 4), clampf(pl.wolf_t / 9.0, 0.0, 1.0), Color(0.6, 0.95, 1.0))
		PixUI.text(self, Vector2(0, 60), "J ısır  ·  K / Shift sıçra  ·  F ulu", Color(0.6, 0.9, 1.0), 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	# ---- kombo sayacı (sağ, ortanın biraz üstü)
	if pl.combo_n >= 3:
		var rk_name := ""
		var rk_col := Color(0.95, 0.92, 0.85)
		for i in pl.COMBO_RANKS.size():
			if pl.combo_n >= int(pl.COMBO_RANKS[i][0]):
				rk_name = pl.COMBO_RANKS[i][1]
				rk_col = pl.COMBO_RANKS[i][2]
		var cx := vp.x - 70.0
		var cy := 70.0
		var pop := 1 + (1 if pl.combo_t > 2.2 else 0)
		PixUI.text(self, Vector2(cx - 60, cy), "x%d" % pl.combo_n, rk_col, pop + 1, HORIZONTAL_ALIGNMENT_RIGHT, 120, 2)
		PixUI.text(self, Vector2(cx - 60, cy + 26), "KOMBO" if rk_name == "" else rk_name, rk_col.darkened(0.1), 1, HORIZONTAL_ALIGNMENT_RIGHT, 120, 2)
		PixUI.bar(self, Rect2(cx - 4, cy + 38, 64, 3), clampf(pl.combo_t / 2.4, 0.0, 1.0), rk_col)
		PixUI.text(self, Vector2(cx - 60, cy + 43), "+%d%% hasar" % int(round((pl.combo_mult() - 1.0) * 100.0)), PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_RIGHT, 120, 0)
	_draw_v12(vp, pl, kx, y0)
	# ---- boss can çubuğu
	if level.boss != null and is_instance_valid(level.boss) and not level.boss.dead and level.boss.state != "intro":
		var bw2 := 260.0
		var bx2 := (vp.x - bw2) / 2.0
		PixUI.panel(self, Rect2(bx2 - 6, vp.y - 72, bw2 + 12, 24), Color(0.9, 0.3, 0.4))
		PixUI.text(self, Vector2(bx2, vp.y - 71), level.boss._label.text, Color(1.0, 0.6, 0.65), 1, HORIZONTAL_ALIGNMENT_CENTER, bw2)
		PixUI.bar(self, Rect2(bx2, vp.y - 58, bw2, 6), clampf(level.boss.hp / level.boss.max_hp, 0.0, 1.0), Color(0.9, 0.2, 0.3))
		for i in range(1, 3):
			draw_rect(Rect2(roundf(bx2 + bw2 * i / 3.0), vp.y - 58, 1, 6), Color(0, 0, 0, 0.5))
	# ---- lütuflar
	var lut: Array = R.get("lutuf", [])
	if not lut.is_empty():
		var lx := bx
		var ly := y3 + 17.0
		for id in lut:
			var l: Array = Game.LUTUF[id]
			var lc := Color(l[2][0], l[2][1], l[2][2])
			var w2 := PixUI.width(String(l[0])) + 10.0
			PixUI.panel(self, Rect2(lx, ly, w2, 12), lc.darkened(0.2), PixUI.INK)
			draw_circle(Vector2(lx + 5, ly + 6), 2.0, lc)
			PixUI.text(self, Vector2(lx + 9, ly + 1), String(l[0]), lc.lightened(0.2), 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
			lx += w2 + 3.0
	# ---- sağ üst: biyom, derinlik, süre
	var place: String = ("Ulu Kayın Yurdu") if level.hub else String(level.biome.get("name", "Kararan Ötüken"))
	var ptxt := "%s" % place
	var pw := maxf(PixUI.width(ptxt), 120.0) + 14.0
	PixUI.panel(self, Rect2(vp.x - 8 - pw, 8, pw, 29))
	PixUI.text(self, Vector2(vp.x - 8 - pw, 10), ptxt, PixUI.GOLD if not level.hub else Color(0.6, 1.0, 1.0), 1, HORIZONTAL_ALIGNMENT_CENTER, pw)
	var tm := float(R["time"])
	var info := "%d. derinlik · %d:%02d · %d" % [int(R.get("depth", 1)), int(tm / 60.0), int(tm) % 60, int(R["kills"])]
	var iw := PixUI.width(info) + 9.0
	var ix := vp.x - 8 - pw + (pw - iw) / 2.0
	PixUI.text(self, Vector2(ix, 22), info, PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
	PixUI.icon(self, "kafatasi", Vector2(ix + iw - 7, 24), PixUI.DIM, 1, false)
	# ---- kısa mesaj
	if flash_t > 0.0 and flash_msg != "" and mode == "play":
		var a := clampf(flash_t, 0.0, 1.0)
		var fw := PixUI.width(flash_msg) + 16.0
		PixUI.panel(self, Rect2((vp.x - fw) / 2.0, 72, fw, 15), Color(PixUI.GOLD, a), Color(PixUI.INK, PixUI.INK.a * a))
		PixUI.text(self, Vector2(0, 73), flash_msg, Color(PixUI.GOLD, a), 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	# ---- yerdeki eşya
	if mode != "play" or get_tree().paused:
		return
	var p: Node = level.nearest_item(pl.global_position + Vector2(0, -10))
	if p and p.kind == "tilsim":
		var sp0: Vector2 = p.get_global_transform_with_canvas().origin
		_world_prompt(sp0 + Vector2(0, -34), "E", "Tılsımı oku")
	elif p and p.kind == "lutuf":
		var sp1: Vector2 = p.get_global_transform_with_canvas().origin
		_world_prompt(sp1 + Vector2(0, -58), "E", "Tanrı sunağı: lütuf dile")
	elif p and not p.item.is_empty():
		var opts: Array = level.slot_options(p.item)
		var nat: String = level.natural_slot(p.item)
		var tgt := nat
		var free := false
		for sl in [nat] + opts:
			if R["slots"].get(sl, {}).is_empty():
				tgt = sl
				free = true
				break
		var cur: Dictionary = {} if free else R["slots"].get(nat, {})
		var ch := _card_h(p.item)
		_draw_card(p.item, Vector2(vp.x - 198, 46), "YERDEKİ", cur)
		var sp: Vector2 = p.get_global_transform_with_canvas().origin
		var pr := "Al" if free else "Yuva seç"
		_world_prompt(sp + Vector2(0, -38), "E", pr)
		var note := "İki yuva da dolu: E ile hangisini değiştireceğini seç." if not free else "Boş yuvaya gider: %s [%s]" % [SLOT_NAMES[tgt], SLOT_KEYS[tgt]]
		var ny := 46 + ch + 4
		for l in PixUI.wrap(note, 186):
			PixUI.text(self, Vector2(vp.x - 196, ny), l, PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 2)
			ny += 10


func _world_prompt(at: Vector2, key: String, label: String) -> void:
	var w := PixUI.width(label) + 18.0
	var x := roundf(at.x - w / 2.0)
	var y := roundf(at.y + sin(_t * 4.0) * 1.5)
	PixUI.panel(self, Rect2(x, y, w, 14), PixUI.GOLD)
	PixUI.key_cap(self, Vector2(x + 2, y + 1), key)
	PixUI.text(self, Vector2(x + 14, y + 1), label, PixUI.TEXT)


func _draw_slot_box(r: Rect2, key: String, pl: Node) -> void:
	var it: Dictionary = Game.run["slots"].get(key, {})
	var col := PixUI.EDGE.darkened(0.3)
	if not it.is_empty():
		col = Color.from_string(Data.items["rarities"][int(it["rarity"])]["color"], PixUI.DIM)
	var active := false
	if not it.is_empty() and key in ["melee", "second"]:
		active = (key == pl.mel_slot and not pl.atk.is_empty()) or (key == pl.sec_slot and (pl.aim_t >= 0.0 or pl.block_t >= 0.0))
	PixUI.panel(self, r, col if not active else col.lightened(0.4), PixUI.INK2)
	if it.is_empty():
		# boş yuva: soluk silüet
		PixUI.text(self, r.position + Vector2(0, 9), "boş", Color(PixUI.DIM, 0.5), 1, HORIZONTAL_ALIGNMENT_CENTER, r.size.x, 0)
	else:
		PixUI.weapon(self, it, r.position + Vector2(r.size.x / 2.0, r.size.y / 2.0 - 1), Vector2(r.size.x - 4, r.size.y - 7))
		PixUI.ongun_stripe(self, Rect2(r.position.x + 2, r.position.y + r.size.y - 4, r.size.x - 4, 2), Game.item_onguns(it), Game.item_best_ongun(it))
	# bekleme süresi
	if pl.cd.has(key) and pl.cd[key] > 0.0:
		var k := clampf(pl.cd[key] / maxf(0.01, pl.cd_max[key]), 0.0, 1.0)
		var hh := roundf((r.size.y - 2) * k)
		draw_rect(Rect2(r.position.x + 1, r.position.y + r.size.y - 1 - hh, r.size.x - 2, hh), Color(0.02, 0.01, 0.05, 0.7))
		if key in ["g1", "g2"] and pl.cd[key] >= 1.0:
			PixUI.text(self, r.position + Vector2(0, 9), str(int(ceil(pl.cd[key]))), PixUI.TEXT, 1, HORIZONTAL_ALIGNMENT_CENTER, r.size.x, 2)
	PixUI.key_cap(self, r.position + Vector2(-2, -5), SLOT_KEYS[key], PixUI.GOLD, not it.is_empty())


# ------------------------------------------------------------------ eşya kartı
func _card_lines(it: Dictionary) -> Array:
	## [[metin, renk], ...] — açıklama, ek özellikler, kusur (sarılmış)
	var out: Array = []
	for l in ItemGen.describe(it):
		var is_aff := String(l).begins_with("•")
		for w in PixUI.wrap(String(l), 176):
			out.append([w, Color(0.55, 0.82, 1.0) if is_aff else PixUI.TEXT])
	if it.get("flaw", "") != "":
		for f in Data.items["flaws"]:
			if f["id"] == it["flaw"]:
				for w in PixUI.wrap("Kusur: %s (%s)" % [f["name"], f["desc"]], 176):
					out.append([w, PixUI.BAD])
	return out


func _card_h(it: Dictionary) -> float:
	var h := 12.0 + 11.0 + 11.0 + 13.0 + 11.0 + 6.0
	if it.get("epithet", "") != "":
		h += 10.0
	if Data.find_item(it["id"]).has("upgrade_of"):
		h += 10.0
	if it["cat"] == "weapons":
		h += 11.0
	h += _card_lines(it).size() * 10.0
	return h + 8.0


func _eff_dps(it: Dictionary) -> float:
	return ItemGen.dps(it) * Game.item_mult(it)


func _draw_card(it: Dictionary, pos: Vector2, title: String, cmp: Dictionary = {}) -> void:
	var R: Dictionary = Data.items["rarities"][int(it["rarity"])]
	var col := Color.from_string(R["color"], PixUI.TEXT)
	var h := _card_h(it)
	var w := 190.0
	var x := roundf(pos.x)
	var y0 := roundf(pos.y)
	PixUI.panel(self, Rect2(x, y0, w, h), col.darkened(0.15))
	# başlık bandı: nadirlik renginde
	draw_rect(Rect2(x + 2, y0 + 2, w - 4, 2), col)
	PixUI.text(self, Vector2(x + 4, y0 - 9), title, PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 2)
	var y := y0 + 5.0
	PixUI.text(self, Vector2(x + 6, y), it["name"], col, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 1)
	y += 11.0
	if it.get("epithet", "") != "":
		PixUI.text(self, Vector2(x + 6, y), "«%s»" % it["epithet"], Color(1.0, 0.88, 0.55))
		y += 10.0
	PixUI.text(self, Vector2(x + 6, y), "%s · %s · Kalite %%%d" % [R["name"], CAT_TXT.get(it["cat"], ""), int(it["quality"])], PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
	y += 11.0
	var base_def := Data.find_item(it["id"])
	if base_def.has("upgrade_of"):
		PixUI.text(self, Vector2(x + 6, y), "▲ %s'nın gelişmiş hali" % Data.find_item(base_def["upgrade_of"]).get("name", ""), Color(1.0, 0.85, 0.5))
		y += 10.0
	# ongun rozetleri: hangi renge göre güçlenir
	var ons := Game.item_onguns(it)
	var best := Game.item_best_ongun(it)
	var ox := x + 6.0
	for o in ons:
		var oc := PixUI.ongun_col(o)
		var on_best: bool = o == best
		var lbl := "%s ×%s" % [Data.items["ongun"][o]["name"], ItemGen.fmt(Game.ongun_mult(o))]
		if ons.size() > 1 and on_best:
			lbl += " ★"
		var bw := PixUI.width(lbl) + 15.0
		PixUI.panel(self, Rect2(ox, y, bw, 12), oc if on_best else oc.darkened(0.5), Color(oc, 0.16) if on_best else PixUI.INK, false)
		PixUI.icon(self, o, Vector2(ox + 3, y + 3), oc if on_best else oc.darkened(0.4), 1, false)
		PixUI.text(self, Vector2(ox + 12, y + 1), lbl, oc.lightened(0.2) if on_best else PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
		ox += bw + 3.0
	y += 13.0
	# değerler
	if it["cat"] == "weapons":
		PixUI.text(self, Vector2(x + 6, y), "Hasar %s  Hız %s/sn  Krit %%%s ×%s" % [ItemGen.fmt(it["dmg"]), ItemGen.fmt(it["aps"]), ItemGen.fmt(it["crit"]), ItemGen.fmt(it["crit_mult"])], PixUI.TEXT, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
		y += 11.0
		var d := _eff_dps(it)
		PixUI.text(self, Vector2(x + 6, y), "Saniyede hasar: %s" % ItemGen.fmt(d), PixUI.GOLD)
		if not cmp.is_empty() and cmp.get("cat", "") == "weapons":
			var dd := d - _eff_dps(cmp)
			var s := ("▲ +%s" if dd >= 0.0 else "▼ %s") % ItemGen.fmt(dd)
			PixUI.text(self, Vector2(x + 6, y), s, PixUI.GOOD if dd >= 0.0 else PixUI.BAD, 1, HORIZONTAL_ALIGNMENT_RIGHT, w - 12, 0)
	elif it["cat"] == "shields":
		PixUI.text(self, Vector2(x + 6, y), "Blok %%%d   Savuşturma %s sn" % [int(float(it["block"]) * 100.0), ItemGen.fmt(it["parry_win"])], PixUI.TEXT, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
		if not cmp.is_empty() and cmp.get("cat", "") == "shields":
			var db := int(round((float(it["block"]) - float(cmp["block"])) * 100.0))
			PixUI.text(self, Vector2(x + 6, y), ("▲ +%d" if db >= 0 else "▼ %d") % db, PixUI.GOOD if db >= 0 else PixUI.BAD, 1, HORIZONTAL_ALIGNMENT_RIGHT, w - 12, 0)
	else:
		PixUI.text(self, Vector2(x + 6, y), "Bekleme %s sn   Güç ×%s" % [ItemGen.fmt(it["cd"]), ItemGen.fmt(float(it["power"]) * Game.item_mult(it))], PixUI.TEXT, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
	y += 11.0
	PixUI.divider(self, x + 8, y + 2, w - 16, col.darkened(0.3))
	y += 6.0
	for l in _card_lines(it):
		PixUI.text(self, Vector2(x + 6, y), l[0], l[1], 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
		y += 10.0
	PixUI.bar(self, Rect2(x + 6, y0 + h - 5, w - 12, 2), float(it["quality"]) / 100.0, col)


# ------------------------------------------------------------------ yuva seçimi
func _draw_slot(vp: Vector2) -> void:
	_dim(vp, 0.7)
	var p: Node = main.slot_pickup if main else null
	if p == null or not is_instance_valid(p):
		return
	_title(vp, 18, "HANGİ YUVAYA?", PixUI.GOLD)
	var e := _ease_open()
	var it: Dictionary = p.item
	var cx := roundf(vp.x / 2.0 - 205.0 + (1.0 - e) * -20.0)
	_draw_card(it, Vector2(cx, 64), "YENİ EŞYA")
	# iki seçenek
	var bx := roundf(vp.x / 2.0 + 10.0 + (1.0 - e) * 20.0)
	var oy := 64.0
	for i in slot_opts.size():
		var key: String = slot_opts[i]
		var cur: Dictionary = Game.run["slots"].get(key, {})
		var is_sel := i == sel
		var bh := 96.0
		var r := Rect2(bx, oy + i * (bh + 8), 196, bh)
		var col := PixUI.GOLD if is_sel else PixUI.EDGE.darkened(0.25)
		PixUI.panel(self, r, col, PixUI.INK2 if is_sel else PixUI.INK)
		if is_sel:
			# seçili: yanıp sönen ok
			var ax := r.position.x - 9 + sin(_t * 8.0) * 2.0
			PixUI.text(self, Vector2(ax, r.position.y + bh / 2.0 - 6), "→", PixUI.GOLD, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 2)
		PixUI.key_cap(self, r.position + Vector2(6, 5), SLOT_KEYS[key], PixUI.GOLD, is_sel)
		PixUI.text(self, r.position + Vector2(20, 5), SLOT_NAMES[key].to_upper(), col if is_sel else PixUI.DIM)
		if cur.is_empty():
			PixUI.text(self, r.position + Vector2(0, 40), "boş", PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)
		else:
			var rc := Color.from_string(Data.items["rarities"][int(cur["rarity"])]["color"], PixUI.TEXT)
			draw_rect(Rect2(r.position.x + 6, r.position.y + 20, 56, 34), Color(0, 0, 0, 0.25))
			PixUI.weapon(self, cur, r.position + Vector2(34, 37), Vector2(54, 32))
			PixUI.ongun_stripe(self, Rect2(r.position.x + 6, r.position.y + 55, 56, 2), Game.item_onguns(cur), Game.item_best_ongun(cur))
			var nl := PixUI.wrap(String(cur["name"]), 124)
			for j in mini(2, nl.size()):
				PixUI.text(self, r.position + Vector2(66, 20 + j * 10), nl[j], rc)
			var cat := String(cur["cat"])
			var stat := ""
			var delta := 0.0
			if cat == "weapons":
				stat = "SnH %s" % ItemGen.fmt(_eff_dps(cur))
				if it["cat"] == "weapons":
					delta = _eff_dps(it) - _eff_dps(cur)
			elif cat == "shields":
				stat = "Blok %%%d" % int(float(cur["block"]) * 100.0)
			else:
				stat = "Bekleme %s sn" % ItemGen.fmt(cur["cd"])
			PixUI.text(self, r.position + Vector2(66, 42), stat, PixUI.TEXT, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
			if cat == "weapons" and it["cat"] == "weapons":
				var s := ("yeni ▲ +%s" if delta >= 0.0 else "yeni ▼ %s") % ItemGen.fmt(delta)
				PixUI.text(self, r.position + Vector2(66, 52), s, PixUI.GOOD if delta >= 0.0 else PixUI.BAD, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
			PixUI.text(self, r.position + Vector2(6, bh - 14), "Bu eşya yere bırakılır" if is_sel else "Yerinde kalır", Color(PixUI.BAD, 0.9) if is_sel else PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
	var keys := ["J", "K"] if "melee" in slot_opts else ["U", "I"]
	_hint(vp, [["A/D", "seç"], ["E", "onayla"], [keys[0] + "/" + keys[1], "doğrudan"], ["Esc", "vazgeç"]], 286.0)


# ------------------------------------------------------------------ tılsım (ongun seçimi)
func _draw_tilsim(vp: Vector2) -> void:
	_dim(vp, 0.72)
	_title(vp, 58, "KAM TILSIMI", PixUI.GOLD, "Bir ongun seç: o renkteki eşyaların güçlenir. Çift renkli eşya en yüksek ongununu kullanır.")
	var R: Dictionary = Game.run
	var descs := {"kurt": "Kırmızı eşyalar +%15 hasar", "kartal": "Mavi eşyalar +%15 hasar / güç", "ayi": "Yeşil eşyalar +%15  ·  %3 hasar azaltma"}
	var hp_txt := {"kurt": "+%6 en yüksek can", "kartal": "+%6 en yüksek can", "ayi": "+%15 en yüksek can"}
	var e := _ease_open()
	var cw := 176.0
	var gap := 10.0
	var x0 := roundf((vp.x - (cw * 3 + gap * 2)) / 2.0)
	for i in 3:
		var k: String = ONGUN_KEYS[i]
		var o: Dictionary = Data.items["ongun"][k]
		var col := PixUI.ongun_col(k)
		var is_sel := i == sel
		var x := x0 + i * (cw + gap)
		var y := 104.0 + (1.0 - e) * (20.0 + i * 10.0) - (5.0 if is_sel else 0.0)
		var ch := 186.0
		var r := Rect2(x, y, cw, ch)
		PixUI.fancy_panel(self, r, col if is_sel else col.darkened(0.5), Color(col.darkened(0.82), 0.97) if is_sel else PixUI.INK)
		# simge (3x)
		var isz := PixUI.icon_size(k) * 3.0
		PixUI.icon(self, k, Vector2(x + (cw - isz.x) / 2.0, y + 10), col if is_sel else col.darkened(0.35), 3)
		PixUI.text(self, Vector2(x, y + 36), String(o["name"]).to_upper(), col, 1, HORIZONTAL_ALIGNMENT_CENTER, cw, 2)
		var lv := int(R["ongun"][k])
		PixUI.text(self, Vector2(x, y + 49), "Seviye %d  →  %d" % [lv, lv + 1], PixUI.TEXT, 1, HORIZONTAL_ALIGNMENT_CENTER, cw)
		PixUI.text(self, Vector2(x, y + 60), "×%s  →  ×%s" % [ItemGen.fmt(1.0 + 0.15 * lv), ItemGen.fmt(1.0 + 0.15 * (lv + 1))], col.lightened(0.25), 1, HORIZONTAL_ALIGNMENT_CENTER, cw, 0)
		PixUI.divider(self, x + 10, y + 75, cw - 20, col.darkened(0.3))
		var yy := y + 80.0
		for l in PixUI.wrap(String(o["desc"]), cw - 16):
			PixUI.text(self, Vector2(x + 8, yy), l, PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
			yy += 10.0
		yy += 3.0
		PixUI.text(self, Vector2(x + 8, yy), descs[k], PixUI.TEXT, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
		yy += 10.0
		PixUI.text(self, Vector2(x + 8, yy), hp_txt[k], PixUI.GOOD, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
		yy += 14.0
		# bu seçimden güçlenecek eşyalar
		PixUI.text(self, Vector2(x + 8, yy), "Güçlenen eşyaların:", PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
		yy += 11.0
		var any := false
		for sk in ["melee", "second", "g1", "g2"]:
			var it: Dictionary = R["slots"].get(sk, {})
			if it.is_empty():
				continue
			var ons := Game.item_onguns(it)
			if not (k in ons):
				continue
			var now := Game.item_mult(it)
			var after := 1.0 + 0.15 * (lv + 1)
			var gain := maxf(now, after) - now
			if gain <= 0.001:
				continue
			any = true
			draw_rect(Rect2(x + 9, yy + 4, 3, 3), col)
			var nm := String(it["name_base"])
			PixUI.text(self, Vector2(x + 15, yy), nm, PixUI.TEXT, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
			PixUI.text(self, Vector2(x + 8, yy), "+%%%d" % int(round(gain / now * 100.0)), PixUI.GOOD, 1, HORIZONTAL_ALIGNMENT_RIGHT, cw - 16, 0)
			yy += 10.0
		if not any:
			PixUI.text(self, Vector2(x + 8, yy), "(bu renkte eşyan yok)", Color(PixUI.DIM, 0.7), 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
	_hint(vp, [["A/D", "seç"], ["E", "onayla"]], 304.0)


# ------------------------------------------------------------------ ekranlar
func _draw_title(vp: Vector2) -> void:
	draw_rect(Rect2(Vector2.ZERO, vp), Color(0.03, 0.02, 0.06, 0.5))
	for i in 10:
		draw_rect(Rect2(0, vp.y - (i + 1) * 6, vp.x, 6), Color(0.02, 0.01, 0.04, 0.05 * (10 - i)))
	var bob := roundf(sin(_t * 1.5) * 2.0)
	var title := "KUT'UN YOLU"
	var tw := PixUI.width(title, 3)
	var x0 := (vp.x - tw) / 2.0
	PixUI.text(self, Vector2(0, 84 + bob), title, PixUI.GOLD, 3, HORIZONTAL_ALIGNMENT_CENTER, vp.x, 2)
	var lw := 70.0
	draw_rect(Rect2(roundf(x0 - 16 - lw), 101 + bob, lw, 1), PixUI.EDGE)
	draw_rect(Rect2(roundf(x0 + tw + 16), 101 + bob, lw, 1), PixUI.EDGE)
	PixUI.horn(self, Vector2(x0 - 14, 99 + bob), PixUI.GOLD, -1)
	PixUI.horn(self, Vector2(x0 + tw + 9, 99 + bob), PixUI.GOLD, 1)
	PixUI.text(self, Vector2(0, 128), "Erlik'in zincirini kır, Ulu Kayın'ı kurtar", Color(0.7, 0.92, 1.0), 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	var a := _blink()
	var pw := 180.0
	PixUI.panel(self, Rect2((vp.x - pw) / 2.0, 176, pw, 18), Color(PixUI.GOLD, a))
	PixUI.text(self, Vector2(0, 179), "Başlamak için Boşluk / Enter", Color(PixUI.TEXT, a), 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	if mode == "title":
		_hint(vp, [["Tab", "ayarlar"]], 200.0)
	# kontroller
	var rows := [
		[["A/D", "hareket"], ["Boşluk", "zıpla"], ["J", "1. silah"], ["K", "2. silah"], ["L", "yuvarlan"]],
		[["U/I", "teçhizat"], ["Q", "şişe"], ["F", "Kut gücü"], ["E", "al / konuş"], ["Esc", "duraklat"]],
	]
	PixUI.panel(self, Rect2(vp.x / 2.0 - 230, vp.y - 76, 460, 46))
	_hint(vp, rows[0], vp.y - 70)
	_hint(vp, rows[1], vp.y - 56)
	PixUI.text(self, Vector2(0, vp.y - 42), "R kam transı: göğe geç (S+R yeraltı) · G don: seçkin ruhunun kılığı · müziğin usulüne denk vuruş güçlü · destanını Ozan'a anlat, adın konsun", Color(0.85, 0.75, 1.0, 0.9), 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x, 0)
	PixUI.text(self, Vector2(0, vp.y - 29), "J art arda = zincir · bekle+J = bitiriş · basılı = ağır · ↑J göğe savur · havada ↓J dalış · koşarken J akın · yuvarlan+J dönüş · S+J diz biçen", Color(1.0, 0.85, 0.5, 0.85), 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x, 0)
	PixUI.text(self, Vector2(0, vp.y - 17), "Shift basılı = koş · S = çömel (çömelirken saldırı ve yay) · duvara doğru zıpla = kenara tutun", Color(0.75, 0.9, 1.0, 0.8), 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x, 0)


func _draw_intro(vp: Vector2) -> void:
	draw_rect(Rect2(Vector2.ZERO, vp), Color(0.03, 0.02, 0.06, 0.82))
	var lines: Array = Data.story["intro"]
	var s: String = lines[mini(intro_i, lines.size() - 1)]
	var ws := PixUI.wrap(s, 400)
	var h := ws.size() * 14.0 + 26.0
	var y := roundf(150.0 - h / 2.0)
	PixUI.fancy_panel(self, Rect2(vp.x / 2.0 - 216, y, 432, h))
	var yy := y + 13.0
	for w in ws:
		PixUI.text(self, Vector2(0, yy), w, PixUI.TEXT, 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
		yy += 14.0
	# sayfa noktaları
	var n := lines.size()
	var dx := roundf(vp.x / 2.0 - n * 4.0)
	for i in n:
		draw_rect(Rect2(dx + i * 8, y + h + 8, 4, 4), PixUI.GOLD if i == intro_i else Color(PixUI.DIM, 0.4))
	_hint(vp, [["Boşluk", "devam"], ["Esc", "atla"]])


func _stat_row(vp: Vector2, y: float, items: Array) -> void:
	## [[simge, metin, renk], ...] ortalanmış sıra
	var total := 0.0
	for it in items:
		total += 10.0 + PixUI.width(it[1]) + 14.0
	total -= 14.0
	var x := roundf((vp.x - total) / 2.0)
	for it in items:
		PixUI.icon(self, it[0], Vector2(x, y + 3), it[2])
		x += 10.0
		PixUI.text(self, Vector2(x, y), it[1], it[2])
		x += PixUI.width(it[1]) + 14.0


func _draw_dead(vp: Vector2) -> void:
	_dim(vp, 0.74, Color(0.05, 0.01, 0.03))
	var e := _ease_open()
	_title(vp, 92, "RUH KUŞUN DALA KONMADI", Color(1.0, 0.55, 0.45), "Umay Ana seni yeniden yoğuruyor.")
	var R: Dictionary = Game.run
	var pw := 360.0
	var y := 144.0 + (1.0 - e) * 12.0
	PixUI.panel(self, Rect2((vp.x - pw) / 2.0, y, pw, 52))
	var tm := float(R.get("time", 0.0))
	_stat_row(vp, y + 6, [["kilic", "%d. derinlik" % int(R.get("depth", 1)), PixUI.TEXT], ["kafatasi", "%d düşman" % int(R["kills"]), PixUI.TEXT], ["altin", str(R["gold"]), PixUI.GOLD], ["zaman", "%d:%02d" % [int(tm / 60.0), int(tm) % 60], PixUI.DIM]])
	PixUI.text(self, Vector2(0, y + 22), "Taşıdığın %d Kut yitti. %s" % [int(R.get("kut_lost", 0)), flash_msg], Color(0.6, 0.95, 1.0), 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	PixUI.text(self, Vector2(0, y + 34), "Kut bankası: %d   ·   Bekleyen parşömen: %d" % [int(Game.meta.get("kut_bank", 0)), Game.meta.get("blueprints", []).size()], PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	_hint(vp, [["Boşluk", "yeniden doğ"]], 214.0)


func _draw_done(vp: Vector2) -> void:
	_dim(vp, 0.7, Color(0.01, 0.04, 0.06))
	var R: Dictionary = Game.run
	_title(vp, 96, "KUT KAPISI", Color(0.6, 1.0, 1.0), "%d. derinliği geçtin. Silahların, ongunların ve canın seninle; şişelerin doldu." % int(R.get("depth", 1)))
	PixUI.text(self, Vector2(0, 138), "Aşağısı daha karanlık: düşmanlar güçlenir, eşyalar daha nadir düşer.", PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	_hint(vp, [["Boşluk", "derine in"]], 200.0)


func _draw_pause(vp: Vector2) -> void:
	draw_rect(Rect2(Vector2.ZERO, vp), Color(0.02, 0.015, 0.04, 0.62))
	_title(vp, 64, "DURAKLATILDI", PixUI.GOLD)
	var R: Dictionary = Game.run
	var pw := 340.0
	var x := (vp.x - pw) / 2.0
	PixUI.fancy_panel(self, Rect2(x, 104, pw, 120), PixUI.EDGE, PixUI.INK2)
	PixUI.text(self, Vector2(x, 110), "ONGUNLAR", PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_CENTER, pw)
	var ox := x + 16.0
	for k in ONGUN_KEYS:
		var col := PixUI.ongun_col(k)
		PixUI.icon(self, k, Vector2(ox, 126), col, 2)
		PixUI.text(self, Vector2(ox + 18, 125), "%s %d" % [Data.items["ongun"][k]["name"], int(R["ongun"][k])], col)
		PixUI.text(self, Vector2(ox + 18, 135), "×%s" % ItemGen.fmt(Game.ongun_mult(k)), PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
		ox += 108.0
	PixUI.divider(self, x + 12, 152, pw - 24)
	var yy := 160.0
	for sk in ["melee", "second", "g1", "g2"]:
		var it: Dictionary = R["slots"].get(sk, {})
		PixUI.key_cap(self, Vector2(x + 14, yy), SLOT_KEYS[sk], PixUI.GOLD, not it.is_empty())
		if it.is_empty():
			PixUI.text(self, Vector2(x + 28, yy), "—", PixUI.DIM)
		else:
			var rc := Color.from_string(Data.items["rarities"][int(it["rarity"])]["color"], PixUI.TEXT)
			PixUI.text(self, Vector2(x + 28, yy), String(it["name"]), rc)
			PixUI.ongun_stripe(self, Rect2(x + pw - 40, yy + 4, 26, 3), Game.item_onguns(it), Game.item_best_ongun(it))
		yy += 14.0
	_hint(vp, [["Esc", "devam et"], ["Tab", "ayarlar"]])


func _draw_settings(vp: Vector2) -> void:
	## Görüntü ayarları: pencere modu, çözünürlük, ölçekleme, doku kalitesi (2K / 4K HD paketleri), dikey eşitleme
	_dim(vp, 0.93)
	_title(vp, 40, "AYARLAR", PixUI.GOLD, "Görüntü ve çözünürlük")
	var rows: Array = Ayarlar.rows()
	var pw := 380.0
	var x := roundf((vp.x - pw) / 2.0)
	var y := 96.0
	PixUI.fancy_panel(self, Rect2(x, y - 8, pw, rows.size() * 22.0 + 14), PixUI.EDGE, PixUI.INK2)
	for i in rows.size():
		var r: Array = rows[i]
		var is_sel := i == sel
		var on: bool = r[2]
		var col := PixUI.GOLD if is_sel else (PixUI.TEXT if on else PixUI.DIM)
		if is_sel:
			draw_rect(Rect2(x + 4, y - 2, pw - 8, 18), Color(PixUI.GOLD, 0.12))
			PixUI.text(self, Vector2(x - 10 + sin(_t * 8.0) * 2.0, y + 1), "→", PixUI.GOLD, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 2)
		PixUI.text(self, Vector2(x + 12, y + 1), r[0], col)
		var v: String = r[1]
		var vx := x + pw - 150.0
		PixUI.text(self, Vector2(vx, y + 1), "<" if on else "", col, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
		PixUI.text(self, Vector2(vx + 8, y + 1), v, col if on else PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_CENTER, 124)
		PixUI.text(self, Vector2(vx + 136, y + 1), ">" if on else "", col, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
		y += 22.0
	var tips := [
		"Pencereli, tam ekran (kenarsız) ya da özel tam ekran.",
		"Pencereli modda pencere boyutu. Tam ekranda ekranın kendi çözünürlüğü kullanılır.",
		"Ekranı doldur: her çözünürlükte boşluksuz. Keskin piksel: tam sayı ölçek, kenarlarda siyah pay kalabilir.",
		"2K / 4K: piksel sanatı Scale2x / Scale4x ile büyütülür; köşegenler yumuşar, ayrıntı keskin kalır. Otomatik: 1440p'de 2K, 2160p'de 4K.",
		"Kare hızını ekran yenilemesine kilitler (yırtılmayı önler).",
	]
	var tl := PixUI.wrap(tips[clampi(sel, 0, tips.size() - 1)], 420)
	var ty := y + 14.0
	for l in tl:
		PixUI.text(self, Vector2(0, ty), l, PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
		ty += 11.0
	var ws := get_tree().root.size
	PixUI.text(self, Vector2(0, ty + 6), "Pencere: %dx%d  ·  ölçek ×%s" % [ws.x, ws.y, ItemGen.fmt(float(ws.y) / 360.0)], Color(PixUI.KUT, 0.8), 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x, 0)
	_hint(vp, [["W/S", "seç"], ["A/D", "değiştir"], ["Esc", "geri"]])


func _draw_umay(vp: Vector2) -> void:
	_dim(vp, 0.8, Color(0.01, 0.04, 0.06))
	_title(vp, 22, "UMAY ANA", Color(0.6, 1.0, 1.0), "«Getirdiğin Kut ağaca işledi. Söyle, hangi dalı güçlendireyim?»")
	var bank := int(Game.meta.get("kut_bank", 0))
	var bt := "Kut bankası: %d" % bank
	var bw := PixUI.width(bt) + 26.0
	PixUI.panel(self, Rect2((vp.x - bw) / 2.0, 66, bw, 15), PixUI.KUT)
	PixUI.icon(self, "kut", Vector2((vp.x - bw) / 2.0 + 6, 70), PixUI.KUT)
	PixUI.text(self, Vector2((vp.x - bw) / 2.0 + 16, 68), bt, PixUI.KUT)
	var keys: Array = Game.UMAY.keys()
	var y := 90.0
	var pw := 420.0
	var x := roundf((vp.x - pw) / 2.0)
	for i in keys.size():
		var id: String = keys[i]
		var u: Array = Game.UMAY[id]
		var lv := Game.umay_level(id)
		var mx: int = (u[2] as Array).size()
		var cost := Game.umay_cost(id)
		var is_sel := i == sel
		var r := Rect2(x, y, pw, 30)
		PixUI.panel(self, r, PixUI.KUT if is_sel else PixUI.EDGE.darkened(0.4), Color(0.06, 0.12, 0.14, 0.95) if is_sel else PixUI.INK, false)
		if is_sel:
			PixUI.text(self, Vector2(x - 10 + sin(_t * 8.0) * 2.0, y + 9), "→", PixUI.KUT, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 2)
		PixUI.text(self, Vector2(x + 8, y + 3), u[0], PixUI.TEXT if lv < mx else PixUI.KUT)
		PixUI.text(self, Vector2(x + 8, y + 15), u[1], PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
		for k in mx:
			var c := PixUI.KUT if k < lv else Color(0.2, 0.22, 0.3)
			draw_rect(Rect2(x + 280 + k * 10, y + 11, 7, 7), c)
			draw_rect(Rect2(x + 280 + k * 10, y + 11, 7, 1), c.lightened(0.4))
		var ct := ("%d" % cost) if cost >= 0 else "tamam"
		var can := cost >= 0 and bank >= cost
		var cc := (PixUI.KUT if can else Color(0.6, 0.55, 0.65)) if cost >= 0 else PixUI.GOOD
		if cost >= 0:
			PixUI.icon(self, "kut", Vector2(x + pw - 14 - PixUI.width(ct) - 8, y + 11), cc, 1, false)
		PixUI.text(self, Vector2(x + 8, y + 9), ct, cc, 1, HORIZONTAL_ALIGNMENT_RIGHT, pw - 18)
		y += 34.0
	if flash_t > 0.0:
		PixUI.text(self, Vector2(0, vp.y - 40), flash_msg, PixUI.GOLD, 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x, 2)
	_hint(vp, [["W/S", "seç"], ["E", "al"], ["Esc", "ayrıl"]])


func _draw_ozan(vp: Vector2) -> void:
	_dim(vp, 0.8, Color(0.05, 0.03, 0.02))
	_title(vp, 30, "OZAN BİLGE KOPUZ", PixUI.GOLD)
	var npc: Dictionary = Data.story["npcs"]["ozan"]
	var lines: Array = npc["first"] + npc["repeat"]
	var R: Dictionary = Game.run
	var lore: Array = Data.story["lore"].get("otuken", [])
	var said: Array = []
	for k in mini(ozan_i + 1, 4):
		if k < 3:
			said.append(lines[(k + int(Game.meta.get("runs", 0))) % lines.size()])
		else:
			said.append(lore[int(Game.meta.get("runs", 0)) % maxi(1, lore.size())])
	var all_l: Array = []
	for s in said:
		all_l.append_array(PixUI.wrap("«" + s + "»", 400))
		all_l.append("")
	var h := all_l.size() * 12.0 + 16.0
	var pw := 430.0
	PixUI.fancy_panel(self, Rect2((vp.x - pw) / 2.0, 66, pw, h))
	var y := 76.0
	for l in all_l:
		PixUI.text(self, Vector2(0, y), l, Color(0.95, 0.9, 0.8), 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
		y += 12.0
	var tm := float(R.get("time", 0.0))
	PixUI.text(self, Vector2(0, vp.y - 44), "Bu koşu: %d. derinlik  ·  %d düşman  ·  %d:%02d  ·  en derin: %d" % [int(R.get("depth", 1)), int(R.get("kills", 0)), int(tm) / 60, int(tm) % 60, int(Game.meta.get("best_depth", 1))], PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	_hint(vp, [["E", "dinle"], ["Esc", "ayrıl"]])


func _draw_demirci(vp: Vector2) -> void:
	_dim(vp, 0.82, Color(0.05, 0.02, 0.02))
	_title(vp, 24, "DEMİRCİ KAM KUZGUN", PixUI.GOLD, "«Tomar getirdin. Kut ver, dövüp koşuna katayım.»")
	var bank := int(Game.meta.get("kut_bank", 0))
	var bt := "Kut bankası: %d" % bank
	var bw := PixUI.width(bt) + 26.0
	PixUI.panel(self, Rect2((vp.x - bw) / 2.0, 68, bw, 15), PixUI.KUT)
	PixUI.icon(self, "kut", Vector2((vp.x - bw) / 2.0 + 6, 72), PixUI.KUT)
	PixUI.text(self, Vector2((vp.x - bw) / 2.0 + 16, 70), bt, PixUI.KUT)
	var bps: Array = Game.meta.get("blueprints", [])
	if bps.is_empty():
		PixUI.text(self, Vector2(0, 150), "Bekleyen parşömen yok. Düşmanlar parşömen düşürür; seçkinler kesin düşürür.", PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	else:
		var n := bps.size()
		var w := 122.0
		var gap := 10.0
		var total := n * w + (n - 1) * gap
		var x0 := vp.x / 2.0 - total / 2.0
		if total > vp.x - 40:
			x0 = (vp.x - w) / 2.0 - sel * (w + gap)
		for i in n:
			var id: String = bps[i]
			var base := Data.find_item(id)
			var cost := Game.unlock_cost(id)
			var can := bank >= cost
			var x := roundf(x0 + i * (w + gap))
			var y := 94.0 - (5.0 if i == sel else 0.0)
			var col := PixUI.KUT if can else Color(0.6, 0.55, 0.65)
			PixUI.fancy_panel(self, Rect2(x, y, w, 150), col if i == sel else col.darkened(0.5), PixUI.INK2 if i == sel else PixUI.INK)
			if Data.has_weapon_sprite(id):
				draw_rect(Rect2(x + 8, y + 10, w - 16, 40), Color(0, 0, 0, 0.25))
				PixUI.weapon(self, {"id": id, "material": "demir"}, Vector2(x + w / 2.0, y + 30), Vector2(w - 20, 36))
			PixUI.text(self, Vector2(x, y + 56), base.get("name", id), PixUI.TEXT, 1, HORIZONTAL_ALIGNMENT_CENTER, w)
			PixUI.text(self, Vector2(x, y + 67), CAT_TXT.get(base.get("cat", ""), ""), PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_CENTER, w, 0)
			var mech: Dictionary = base.get("mech", {})
			var desc: String = String(mech.get("desc", base.get("desc", ""))).replace("{v}", "?")
			var lines := PixUI.wrap(desc, w - 12)
			for j in mini(5, lines.size()):
				PixUI.text(self, Vector2(x + 6, y + 80 + j * 10), lines[j], PixUI.TEXT, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
			var ct := "%d" % cost
			PixUI.icon(self, "kut", Vector2(x + (w - PixUI.width(ct)) / 2.0 - 7, y + 136), col, 1, false)
			PixUI.text(self, Vector2(x + 5, y + 134), ct, col, 1, HORIZONTAL_ALIGNMENT_CENTER, w)
	if flash_t > 0.0 and flash_msg != "":
		PixUI.text(self, Vector2(0, 256), flash_msg, Color(PixUI.GOLD, clampf(flash_t, 0.0, 1.0)), 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x, 2)
	PixUI.text(self, Vector2(0, vp.y - 36), "Açılan eşyalar bundan sonraki koşularda düşer.", PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	_hint(vp, [["A/D", "seç"], ["E", "parşömeni aç"], ["Boşluk", "yola çık"]])



# ================================================================== v12 göstergeleri
func _draw_v12(vp: Vector2, pl: Node, kx: float, y0: float) -> void:
	# ---- kam gücü (R): öbür âleme geçiş
	var ax := kx + 36.0
	var ay := y0 + 15.0
	var kk: float = pl.kam / 100.0
	var rcol: Color = Alem.GOK_COL if pl.realm == "gok" else (Alem.YER_COL if pl.realm == "yer" else Color(0.95, 0.8, 0.55))
	draw_circle(Vector2(ax, ay), 15.0, PixUI.SHADOW)
	draw_circle(Vector2(ax, ay), 14.0, PixUI.INK)
	draw_arc(Vector2(ax, ay), 14.0, 0.0, TAU, 28, PixUI.EDGE, 1.0)
	var ok: bool = kk >= 0.3 or pl.realm != ""
	draw_arc(Vector2(ax, ay), 11.0, -PI / 2.0, -PI / 2.0 + TAU * clampf(kk, 0.0, 1.0), 32, rcol if ok else Color(rcol, 0.35), 3.0)
	# kam davulu simgesi
	draw_circle(Vector2(ax, ay), 4.5, Color(rcol, 0.8 if ok else 0.35))
	draw_line(Vector2(ax - 4, ay), Vector2(ax + 4, ay), PixUI.INK, 1.0)
	draw_line(Vector2(ax, ay - 4), Vector2(ax, ay + 4), PixUI.INK, 1.0)
	PixUI.key_cap(self, Vector2(ax - 4, y0 + 25), "R", rcol, ok)
	# ---- don (G): emilmiş seçkin ruhu
	var dx := ax + 36.0
	var has_don: bool = pl.don_kind != ""
	var dcol := DonForm.COL
	draw_circle(Vector2(dx, ay), 15.0, PixUI.SHADOW)
	draw_circle(Vector2(dx, ay), 14.0, PixUI.INK)
	draw_arc(Vector2(dx, ay), 14.0, 0.0, TAU, 28, PixUI.EDGE, 1.0)
	if has_don:
		draw_arc(Vector2(dx, ay), 11.0, 0.0, TAU, 32, Color(dcol, 0.6 + 0.4 * sin(_t * 6.0)), 3.0)
		draw_circle(Vector2(dx, ay), 4.0, dcol)
		var nm := String(Data.enemy_def(pl.don_kind).get("name", ""))
		PixUI.text(self, Vector2(dx - 60, y0 - 11), nm, dcol, 1, HORIZONTAL_ALIGNMENT_CENTER, 120, 2)
	else:
		draw_circle(Vector2(dx, ay), 4.0, Color(dcol, 0.25))
	PixUI.key_cap(self, Vector2(dx - 4, y0 + 25), "G", dcol, has_don)
	# ---- âlem başlığı ve süre
	var py := 30.0
	if pl.realm != "":
		var wx := vp.x / 2.0 - 80.0
		PixUI.panel(self, Rect2(wx, py, 160, 26), rcol)
		PixUI.text(self, Vector2(wx, py + 2), "ÜLGEN'İN GÖĞÜ" if pl.realm == "gok" else "ERLİK'İN YERALTI", rcol.lightened(0.2), 1, HORIZONTAL_ALIGNMENT_CENTER, 160, 1)
		PixUI.bar(self, Rect2(wx + 6, py + 16, 148, 4), kk, rcol)
		var hint := "bulutlara bas · ruh kuşlarını yakala · R dön" if pl.realm == "gok" else "ruh taşlarından geç · gölgeleri avla · R dön"
		PixUI.text(self, Vector2(0, py + 30), hint, Color(rcol, 0.85), 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
		py += 44.0
	if pl.don_on:
		var wx2 := vp.x / 2.0 - 80.0
		PixUI.panel(self, Rect2(wx2, py, 160, 26), dcol)
		PixUI.text(self, Vector2(wx2, py + 2), "DON: %s  %.1f" % [pl.don.display_name().to_upper(), pl.don.t], dcol.lightened(0.3), 1, HORIZONTAL_ALIGNMENT_CENTER, 160, 1)
		PixUI.bar(self, Rect2(wx2 + 6, py + 16, 148, 4), clampf(pl.don.t / pl.don.dur, 0.0, 1.0), dcol)
		var moves := {"kurt": "J atılış · K sıçrayış", "kalkan": "J kalkan vuruşu · K siper", "kabuk": "J yuvarlan · K kabuğa çekil",
			"hucum": "J hücum · K ezme", "dev": "J yere çak · K sarsıntı", "kanat": "Boşluk uç · J pike · K tüy", "buyucu": "J büyü · K ışınlan"}
		PixUI.text(self, Vector2(0, py + 30), String(moves.get(pl.don.arch, "")), Color(dcol, 0.85), 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	# ---- usul ölçeri (sağ): müziğin aksak usulü; vuruşlar çizgi, imleç akar
	if not level.hub:
		var u := Ses.usul_now()
		if not u.is_empty():
			var mw := 128.0
			var mx := vp.x - 8.0 - mw
			var my := 128.0
			if pl.usul_streak != _last_streak:
				if pl.usul_streak > _last_streak:
					_usul_flash = 1.0
				_last_streak = pl.usul_streak
			var gold := Color(1.0, 0.85, 0.45)
			PixUI.panel(self, Rect2(mx - 4, my - 4, mw + 8, 14), Color(gold, 0.4 + 0.6 * _usul_flash))
			for i in (u["starts"] as Array).size():
				var sx := roundf(mx + float(u["starts"][i]) * mw)
				var hh := 8.0 if i == 0 else 5.0
				draw_rect(Rect2(sx, my + 3 - hh / 2.0, 2 if i == 0 else 1, hh), Color(gold, 0.9 if i == 0 else 0.6))
			var cxm := roundf(mx + float(u["k"]) * mw)
			var near := absf(float(u["d"])) <= 0.085
			draw_rect(Rect2(cxm - 1, my - 2, 2, 10), Color(1, 1, 1, 0.95) if near else Color(0.85, 0.8, 0.7, 0.7))
			var lbl := "usul" if pl.usul_streak < 2 else "USUL x%d" % pl.usul_streak
			PixUI.text(self, Vector2(mx - 60, my + 12), lbl, gold.lerp(Color.WHITE, _usul_flash * 0.6), 1, HORIZONTAL_ALIGNMENT_RIGHT, mw + 60, 2)
	# ---- ad ve bekleyen destan (can çubuğunun yanında)
	var tt := Adlar.title()
	var tx := 186.0
	if tt != "":
		PixUI.text(self, Vector2(tx, 10), "Bengü «%s»" % tt, PixUI.GOLD, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 2)
	var pend := Adlar.pending().size()
	if pend > 0:
		PixUI.text(self, Vector2(tx, 22), "destan: %d · Ozan'a anlat" % pend, Color(PixUI.GOLD, 0.6 + 0.4 * sin(_t * 4.0)), 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 2)


func _draw_ad(vp: Vector2) -> void:
	## Ad Koyma Töreni: Ozan destanı anlatır, yiğide adını koyar
	_dim(vp, 0.86, Color(0.06, 0.035, 0.02))
	if not Adlar.ADLAR.has(ad_id):
		return
	var a: Array = Adlar.ADLAR[ad_id]
	_title(vp, 34, "AD KOYMA TÖRENİ", PixUI.GOLD)
	var k := clampf(ad_t / 0.9, 0.0, 1.0)
	var l1 := "«Ozan kopuzunu eline aldı, boy boylayıp soy soylayıp şöyle dedi:»"
	PixUI.text(self, Vector2(0, 78), l1, Color(0.9, 0.85, 0.75, k), 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	var l2 := "«Bu yiğit %s. Adını ben koyayım:»" % String(a[1]).to_lower()
	PixUI.text(self, Vector2(0, 94), l2, Color(0.95, 0.9, 0.8, clampf((ad_t - 0.4) / 0.6, 0.0, 1.0)), 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	var kn := clampf((ad_t - 0.9) / 0.5, 0.0, 1.0)
	if kn > 0.0:
		var glow := Color(1.0, 0.85, 0.45, 0.25 * kn)
		draw_rect(Rect2(vp.x / 2.0 - 120, 120, 240, 44), glow)
		PixUI.text(self, Vector2(0, 124), String(a[0]).to_upper(), Color(1.0, 0.88, 0.5, kn), 3, HORIZONTAL_ALIGNMENT_CENTER, vp.x, 2)
		PixUI.text(self, Vector2(0, 176), "«Adın %s olsun!»" % String(a[0]), Color(1.0, 0.95, 0.85, kn), 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
		PixUI.text(self, Vector2(0, 200), "Ad gücü: " + String(a[2]), Color(0.7, 1.0, 0.85, kn), 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
		var book: Dictionary = Game.meta.get("adlar", {})
		PixUI.text(self, Vector2(0, 220), "Ad Defteri: %d / %d ad" % [book.size(), Adlar.ADLAR.size()], PixUI.DIM, 1, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	if ad_t > 1.2:
		var more := not Adlar.pending().is_empty()
		_hint(vp, [["E", "sıradaki destan" if more else "devam"]])
