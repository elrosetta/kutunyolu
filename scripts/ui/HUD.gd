class_name HUD
extends Control
## Arayüz: can, şişe, altın, kut, silah yuvaları, Kut göstergesi, eşya kartı,
## başlık / hikâye / ölüm / bölüm sonu ekranları.

var main: Node
var level: Node
var mode := "title"
var intro_i := 0
var _t := 0.0
var _card_t := 0.0
var font: Font
var sel := 0
var flash_msg := ""
var flash_t := 0.0
var ozan_i := 0

const C_INK := Color(0.07, 0.05, 0.1, 0.92)
const C_GOLD := Color(1.0, 0.83, 0.42)
const C_TEXT := Color(0.96, 0.93, 0.86)
const C_DIM := Color(0.62, 0.6, 0.72)


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	font = ThemeDB.fallback_font


func _process(delta: float) -> void:
	_t += delta
	_card_t += delta
	flash_t -= delta
	queue_redraw()


func _txt(pos: Vector2, s: String, size: int, col: Color, align := HORIZONTAL_ALIGNMENT_LEFT, width := -1.0) -> void:
	draw_string_outline(font, pos, s, align, width, size, 4, Color(0.05, 0.03, 0.08, col.a))
	draw_string(font, pos, s, align, width, size, col)


func _wrap(s: String, size: int, maxw: float) -> Array:
	var words := s.split(" ")
	var lines: Array = []
	var cur := ""
	for w in words:
		var t: String = (cur + " " + w).strip_edges()
		if font.get_string_size(t, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x > maxw and cur != "":
			lines.append(cur)
			cur = w
		else:
			cur = t
	if cur != "":
		lines.append(cur)
	return lines


func _draw() -> void:
	var vp := get_viewport_rect().size
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
	if Game.run.is_empty() or level == null or level.player == null:
		return
	_draw_hud(vp)
	if flash_t > 0.0 and mode == "play":
		_txt(Vector2(0, vp.y - 70), flash_msg, 9, Color(C_GOLD, clampf(flash_t, 0.0, 1.0)), HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	if _card_t < 4.0 and mode == "play":
		var a := clampf(minf(_card_t * 2.0, (4.0 - _card_t) * 1.5), 0.0, 1.0)
		var bm: Dictionary = level.biome
		if level.hub:
			_txt(Vector2(0, 120), "ULU KAYIN YURDU", 26, Color(0.6, 1.0, 1.0, a), HORIZONTAL_ALIGNMENT_CENTER, vp.x)
			_txt(Vector2(0, 142), "Kut'unu Umay Ana'ya götür (E)  ·  Demirci parşömen döver  ·  kapı derine indirir", 10, Color(C_TEXT, a), HORIZONTAL_ALIGNMENT_CENTER, vp.x)
		else:
			_txt(Vector2(0, 120), String(bm.get("name", "Kararan Ötüken")).to_upper(), 26, Color(C_GOLD, a), HORIZONTAL_ALIGNMENT_CENTER, vp.x)
			_txt(Vector2(0, 142), "%d. derinlik  ·  %s" % [int(Game.run["depth"]), String(bm.get("sub", ""))], 10, Color(C_TEXT, a), HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	if mode == "dead":
		_draw_dead(vp)
	elif mode == "done":
		_draw_done(vp)
	elif mode == "tilsim":
		_draw_tilsim(vp)


# ------------------------------------------------------------------ oyun içi
func _draw_hud(vp: Vector2) -> void:
	var R: Dictionary = Game.run
	var pl: Node = level.player
	# can
	var hpk := clampf(float(R["hp"]) / float(R["max_hp"]), 0.0, 1.0)
	draw_rect(Rect2(9, 9, 152, 11), C_INK)
	draw_rect(Rect2(10, 10, 150, 9), Color(0.25, 0.08, 0.12))
	var low := hpk < 0.3 and int(_t * 4.0) % 2 == 0
	draw_rect(Rect2(10, 10, 150 * hpk, 9), Color(1.0, 0.5, 0.42) if low else Color(0.86, 0.22, 0.2))
	draw_rect(Rect2(10, 10, 150 * hpk, 2), Color(1.0, 0.62, 0.5))
	draw_rect(Rect2(9, 9, 152, 11), Color(0.8, 0.6, 0.25), false, 1.0)
	_txt(Vector2(14, 18), "%d / %d" % [int(ceil(float(R["hp"]))), int(R["max_hp"])], 8, C_TEXT)
	# şişeler, altın, kut
	for i in int(R["max_flasks"]):
		var full := i < int(R["flasks"])
		draw_rect(Rect2(11 + i * 9, 26, 6, 8), Color(0.37, 0.85, 0.75) if full else Color(0.2, 0.18, 0.28))
		draw_rect(Rect2(12 + i * 9, 23, 4, 3), Color(0.8, 0.78, 0.85) if full else Color(0.3, 0.28, 0.4))
	_txt(Vector2(12 + int(R["max_flasks"]) * 9, 33), "%d/%d  Q" % [int(R["flasks"]), int(R["max_flasks"])], 7, C_TEXT if int(R["flasks"]) > 0 else Color(1.0, 0.5, 0.45))
	draw_circle(Vector2(74, 30), 3.5, C_GOLD)
	_txt(Vector2(80, 34), str(R["gold"]), 9, C_GOLD)
	var kp := 1.0 + 0.3 * maxf(0.0, sin(_t * 6.0)) * (1.0 if _kut_pulse > 0.0 else 0.0)
	_kut_pulse -= 0.016
	draw_circle(Vector2(112, 30), 3.0 * kp, Color(0.5, 0.95, 1.0))
	_txt(Vector2(118, 34), "%d" % int(R["kut"]), 9, Color(0.6, 0.95, 1.0))
	_txt(Vector2(136, 34), "(%d)" % int(Game.meta.get("kut_bank", 0)), 7, Color(0.6, 0.95, 1.0, 0.6))
	# ongun seviyeleri
	var on: Dictionary = R["ongun"]
	_txt(Vector2(10, 46), "Kurt %d" % int(on["kurt"]), 7, Color(1.0, 0.45, 0.32))
	_txt(Vector2(50, 46), "Kartal %d" % int(on["kartal"]), 7, Color(0.4, 0.8, 1.0))
	_txt(Vector2(98, 46), "Ayı %d" % int(on["ayi"]), 7, Color(0.62, 0.9, 0.42))
	# yuvalar
	var slots := [["melee", "J"], ["second", "K"], ["g1", "U"], ["g2", "I"]]
	var y0 := vp.y - 44.0
	for i in slots.size():
		var key: String = slots[i][0]
		var it: Dictionary = R["slots"].get(key, {})
		var x0 := 10.0 + i * 42.0
		var col := C_DIM
		if not it.is_empty():
			col = Color.from_string(Data.items["rarities"][int(it["rarity"])]["color"], C_DIM)
		draw_rect(Rect2(x0, y0, 38, 30), C_INK)
		draw_rect(Rect2(x0, y0, 38, 30), col, false, 1.0)
		if not it.is_empty() and Data.has_weapon_sprite(it["id"]):
			var reg := Data.weapon_region(it["id"], it["material"])
			var piv := Data.weapon_pivot(it["id"])
			var sc := 0.55
			var center_off := Vector2(32, 20) - piv
			var dst := Rect2(x0 + 19 - 32 * sc + center_off.x * sc * 0.5, y0 + 15 - 20 * sc, 64 * sc, 40 * sc)
			draw_texture_rect_region(Data.weapon_tex.diffuse_texture, dst, reg)
		var cdk := "second" if key == "second" else key
		if pl.cd.has(cdk) and pl.cd[cdk] > 0.0:
			var k := clampf(pl.cd[cdk] / maxf(0.01, pl.cd_max[cdk]), 0.0, 1.0)
			draw_rect(Rect2(x0 + 1, y0 + 1 + 28 * (1.0 - k), 36, 28 * k), Color(0.02, 0.01, 0.05, 0.72))
			if key in ["g1", "g2"]:
				_txt(Vector2(x0, y0 + 19), str(int(ceil(pl.cd[cdk]))), 9, C_TEXT, HORIZONTAL_ALIGNMENT_CENTER, 38)
		_txt(Vector2(x0, y0 + 40), slots[i][1], 7, C_DIM, HORIZONTAL_ALIGNMENT_CENTER, 38)
	# Kut göstergesi
	var kx := 10.0 + 4 * 42.0 + 18.0
	var ky := y0 + 15.0
	var kk: float = pl.kut / 100.0
	draw_circle(Vector2(kx, ky), 13.0, C_INK)
	draw_arc(Vector2(kx, ky), 11.0, -PI / 2.0, -PI / 2.0 + TAU * kk, 32, Color(0.45, 0.95, 1.0) if kk < 1.0 else Color(0.8, 1.0, 1.0, 0.6 + 0.4 * sin(_t * 8.0)), 3.0)
	_txt(Vector2(kx - 20, ky + 4), "KUT", 7, Color(0.6, 0.95, 1.0), HORIZONTAL_ALIGNMENT_CENTER, 40)
	_txt(Vector2(kx - 20, y0 + 40), "F", 7, C_DIM if kk < 1.0 else Color(0.8, 1.0, 1.0), HORIZONTAL_ALIGNMENT_CENTER, 40)
	if pl.wolf_t > 0.0:
		_txt(Vector2(0, 40), "BOZKURT  %.1f" % pl.wolf_t, 11, Color(0.6, 1.0, 1.0), HORIZONTAL_ALIGNMENT_CENTER, vp.x)
		_txt(Vector2(0, 52), "J ısır  ·  K / Shift sıçra  ·  F ulu", 7, Color(0.6, 0.9, 1.0), HORIZONTAL_ALIGNMENT_CENTER, vp.x)
		draw_rect(Rect2(vp.x / 2.0 - 60, 58, 120, 3), Color(0.1, 0.15, 0.2))
		draw_rect(Rect2(vp.x / 2.0 - 60, 58, 120 * clampf(pl.wolf_t / 9.0, 0.0, 1.0), 3), Color(0.6, 0.95, 1.0))
	# sağ üst
	_txt(Vector2(vp.x - 210, 18), ("Ulu Kayın Yurdu · %d. derinlik sonrası" % int(R.get("depth", 1))) if level.hub else ("%s · %d. derinlik" % [String(level.biome.get("name", "Kararan Ötüken")), int(R.get("depth", 1))]), 9, C_GOLD if not level.hub else Color(0.6, 1.0, 1.0), HORIZONTAL_ALIGNMENT_RIGHT, 200)
	var tm := float(R["time"])
	_txt(Vector2(vp.x - 210, 30), "%d:%02d  ·  %d düşman  ·  %d tılsım" % [int(tm / 60.0), int(tm) % 60, int(R["kills"]), int(R.get("scrolls", 0))], 7, C_DIM, HORIZONTAL_ALIGNMENT_RIGHT, 200)
	if flash_t > 0.0 and flash_msg != "":
		_txt(Vector2(0, 60), flash_msg, 9, Color(C_GOLD, clampf(flash_t, 0.0, 1.0)), HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	# yerdeki eşya kartı
	var p: Node = level.nearest_item(pl.global_position + Vector2(0, -10))
	if p and p.kind == "tilsim":
		var sp0: Vector2 = p.get_global_transform_with_canvas().origin
		_txt(Vector2(sp0.x - 50, sp0.y - 36), "E: Tılsımı oku", 8, C_GOLD, HORIZONTAL_ALIGNMENT_CENTER, 100)
	elif p:
		_draw_card(p.item, Vector2(vp.x - 196, 52), "YERDEKİ")
		var slot := _slot_for(p.item)
		var cur: Dictionary = R["slots"].get(slot, {})
		if not cur.is_empty():
			_draw_card(cur, Vector2(vp.x - 196, 52 + _card_h(p.item) + 14), "ELİNDEKİ")
		var pr := "E: Al" if cur.is_empty() else "E: Değiştir"
		var sp: Vector2 = p.get_global_transform_with_canvas().origin
		_txt(Vector2(sp.x - 40, sp.y - 26), pr, 8, C_TEXT, HORIZONTAL_ALIGNMENT_CENTER, 80)


func _slot_for(it: Dictionary) -> String:
	if it["cat"] == "gadgets":
		return "g1"
	if it["cat"] == "shields" or it.get("kind", "") in ["bow", "throw", "magic"]:
		return "second"
	return "melee"


func _card_h(it: Dictionary) -> float:
	var lines := ItemGen.describe(it)
	var n := 0
	for l in lines:
		n += _wrap(l, 7, 172).size()
	return 58.0 + n * 9.0 + (9.0 if it["flaw"] != "" else 0.0) + (10.0 if it["epithet"] != "" else 0.0) + (10.0 if Data.find_item(it["id"]).has("upgrade_of") else 0.0)


func _draw_card(it: Dictionary, pos: Vector2, title: String) -> void:
	var R: Dictionary = Data.items["rarities"][int(it["rarity"])]
	var col := Color.from_string(R["color"], C_TEXT)
	var h := _card_h(it)
	draw_rect(Rect2(pos, Vector2(186, h)), C_INK)
	draw_rect(Rect2(pos, Vector2(186, h)), col, false, 1.0)
	_txt(pos + Vector2(4, -3), title, 7, C_DIM)
	var y := pos.y + 12.0
	_txt(Vector2(pos.x + 6, y), it["name"], 9, col)
	y += 10.0
	if it["epithet"] != "":
		_txt(Vector2(pos.x + 6, y), "«%s»" % it["epithet"], 7, Color(1.0, 0.88, 0.55))
		y += 10.0
	var cat_txt: String = {"weapons": "Silah", "shields": "Kalkan", "gadgets": "Teçhizat"}[it["cat"]]
	_txt(Vector2(pos.x + 6, y), "%s · %s · Kalite %%%d" % [R["name"], cat_txt, int(it["quality"])], 7, C_DIM)
	y += 11.0
	var base_def := Data.find_item(it["id"])
	if base_def.has("upgrade_of"):
		_txt(Vector2(pos.x + 6, y), "▲ %s'nın gelişmiş hali" % Data.find_item(base_def["upgrade_of"]).get("name", ""), 7, Color(1.0, 0.85, 0.5))
		y += 10.0
	if it["cat"] == "weapons":
		_txt(Vector2(pos.x + 6, y), "Hasar %s   Hız %s/sn   Krit %%%s ×%s" % [ItemGen.fmt(it["dmg"]), ItemGen.fmt(it["aps"]), ItemGen.fmt(it["crit"]), ItemGen.fmt(it["crit_mult"])], 7, C_TEXT)
		y += 9.0
		_txt(Vector2(pos.x + 6, y), "Saniyede hasar: %s" % ItemGen.fmt(ItemGen.dps(it)), 7, C_GOLD)
	elif it["cat"] == "shields":
		_txt(Vector2(pos.x + 6, y), "Blok %%%d   Savuşturma penceresi %s sn" % [int(float(it["block"]) * 100.0), ItemGen.fmt(it["parry_win"])], 7, C_TEXT)
		y += 9.0
	else:
		_txt(Vector2(pos.x + 6, y), "Bekleme %s sn   Güç ×%s" % [ItemGen.fmt(it["cd"]), ItemGen.fmt(it["power"])], 7, C_TEXT)
		y += 9.0
	y += 4.0
	for l in ItemGen.describe(it):
		var is_aff := String(l).begins_with("•")
		for w in _wrap(l, 7, 172):
			y += 9.0
			_txt(Vector2(pos.x + 6, y), w, 7, Color(0.5, 0.82, 1.0) if is_aff else C_TEXT)
	if it["flaw"] != "":
		for f in Data.items["flaws"]:
			if f["id"] == it["flaw"]:
				y += 9.0
				_txt(Vector2(pos.x + 6, y), "Kusur: %s (%s)" % [f["name"], f["desc"]], 7, Color(1.0, 0.45, 0.4))
	draw_rect(Rect2(pos.x + 6, pos.y + h - 5, 174, 2), Color(0.18, 0.16, 0.24))
	draw_rect(Rect2(pos.x + 6, pos.y + h - 5, 174 * float(it["quality"]) / 100.0, 2), col)


# ------------------------------------------------------------------ ekranlar
func _draw_title(vp: Vector2) -> void:
	draw_rect(Rect2(Vector2.ZERO, vp), Color(0.04, 0.03, 0.08, 0.55))
	var bob := sin(_t * 1.5) * 2.0
	_txt(Vector2(0, 118 + bob), "KUT'UN YOLU", 40, C_GOLD, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	_txt(Vector2(0, 140), "Erlik'in zincirini kır, Ulu Kayın'ı kurtar", 11, Color(0.7, 0.92, 1.0), HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	var a := 0.55 + 0.45 * sin(_t * 3.0)
	_txt(Vector2(0, 205), "Başlamak için Boşluk / Enter", 10, Color(C_TEXT, a), HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	_txt(Vector2(0, vp.y - 30), "A/D hareket · Boşluk zıpla (çift) · J yakın · K yay/kalkan · L yuvarlan · U/I teçhizat · Q şişe · F Kut · E al", 7, C_DIM, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	_txt(Vector2(0, vp.y - 18), "Kombo: J'ye art arda bas = zincir  ·  iki vuruş, kısa bekle, bas = silahın özel bitirişi  ·  Shift ile alçak geçitlerden yuvarlan", 7, Color(1.0, 0.85, 0.5), HORIZONTAL_ALIGNMENT_CENTER, vp.x)


func _draw_intro(vp: Vector2) -> void:
	draw_rect(Rect2(Vector2.ZERO, vp), Color(0.03, 0.02, 0.06, 0.78))
	var lines: Array = Data.story["intro"]
	var s: String = lines[mini(intro_i, lines.size() - 1)]
	var ws := _wrap(s, 12, 440)
	var y := 150.0 - ws.size() * 9.0
	for w in ws:
		_txt(Vector2(0, y), w, 12, C_TEXT, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
		y += 18.0
	_txt(Vector2(0, vp.y - 24), "%d / %d   ·   Boşluk: devam   ·   Esc: atla" % [intro_i + 1, lines.size()], 7, C_DIM, HORIZONTAL_ALIGNMENT_CENTER, vp.x)


func _draw_dead(vp: Vector2) -> void:
	draw_rect(Rect2(Vector2.ZERO, vp), Color(0.04, 0.02, 0.07, 0.7))
	_txt(Vector2(0, 112), "RUH KUŞUN DALA KONMADI", 22, C_GOLD, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	_txt(Vector2(0, 132), "Umay Ana seni yeniden yoğuruyor.", 10, Color(0.7, 0.92, 1.0), HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	var R: Dictionary = Game.run
	_txt(Vector2(0, 162), "%d. derinlik   ·   Öldürülen: %d   ·   Altın: %d" % [int(R.get("depth", 1)), int(R["kills"]), int(R["gold"])], 9, C_TEXT, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	_txt(Vector2(0, 176), "Taşıdığın %d Kut yitti. %s  Kut bankası: %d   ·   Bekleyen parşömen: %d" % [int(R.get("kut_lost", 0)), flash_msg, int(Game.meta.get("kut_bank", 0)), Game.meta.get("blueprints", []).size()], 8, Color(0.6, 0.95, 1.0), HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	_txt(Vector2(0, 205), "Boşluk / Enter: yeniden doğ", 10, Color(C_TEXT, 0.6 + 0.4 * sin(_t * 3.0)), HORIZONTAL_ALIGNMENT_CENTER, vp.x)


func _draw_done(vp: Vector2) -> void:
	draw_rect(Rect2(Vector2.ZERO, vp), Color(0.03, 0.06, 0.08, 0.7))
	var R: Dictionary = Game.run
	_txt(Vector2(0, 112), "KUT KAPISI", 22, Color(0.6, 1.0, 1.0), HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	_txt(Vector2(0, 132), "%d. derinliği geçtin. Silahların, ongunların ve canın seninle; şişelerin doldu." % int(R.get("depth", 1)), 10, C_TEXT, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	_txt(Vector2(0, 150), "Aşağısı daha karanlık: düşmanlar güçlenir, eşyalar daha nadir düşer.", 8, C_DIM, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	_txt(Vector2(0, 205), "Boşluk / Enter: derine in", 10, Color(C_TEXT, 0.6 + 0.4 * sin(_t * 3.0)), HORIZONTAL_ALIGNMENT_CENTER, vp.x)


func _draw_tilsim(vp: Vector2) -> void:
	draw_rect(Rect2(Vector2.ZERO, vp), Color(0.03, 0.02, 0.06, 0.72))
	_txt(Vector2(0, 70), "KAM TILSIMI", 22, C_GOLD, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	_txt(Vector2(0, 90), "Bir ongun seç; yolun o yöne güçlenir.", 9, C_TEXT, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	var keys := ["kurt", "kartal", "ayi"]
	var descs := ["Yakın dövüş hasarı +%15", "Yay, fırlatma ve teçhizat +%15", "Hasar azaltma +%3, can +%15"]
	var hp_txt := ["+%6 can", "+%6 can", "+%15 can"]
	var R: Dictionary = Game.run
	for i in 3:
		var k: String = keys[i]
		var o: Dictionary = Data.items["ongun"][k]
		var col := Color.from_string(o["color"], C_TEXT)
		var w := 150.0
		var x := vp.x / 2.0 - 240.0 + i * 165.0
		var y := 118.0
		var is_sel := i == sel
		if is_sel:
			y -= 6.0
		var rect := Rect2(x, y, w, 120)
		draw_rect(rect, Color(0.08, 0.06, 0.12, 0.95) if not is_sel else Color(col, 0.18))
		draw_rect(rect, col if is_sel else Color(col, 0.4), false, 2.0 if is_sel else 1.0)
		_txt(Vector2(x, y + 20), o["name"], 13, col, HORIZONTAL_ALIGNMENT_CENTER, w)
		_txt(Vector2(x, y + 36), "Seviye %d → %d" % [int(R["ongun"][k]), int(R["ongun"][k]) + 1], 8, C_TEXT, HORIZONTAL_ALIGNMENT_CENTER, w)
		var dl := _wrap(o["desc"], 7, w - 16)
		for j in dl.size():
			_txt(Vector2(x + 8, y + 54 + j * 9), dl[j], 7, C_DIM, HORIZONTAL_ALIGNMENT_LEFT, w - 16)
		_txt(Vector2(x, y + 92), descs[i], 7, C_TEXT, HORIZONTAL_ALIGNMENT_CENTER, w)
		_txt(Vector2(x, y + 104), hp_txt[i], 8, Color(0.62, 0.9, 0.42), HORIZONTAL_ALIGNMENT_CENTER, w)
		draw_circle(Vector2(x + w / 2.0, y + 8), 3.0, col)
	_txt(Vector2(0, vp.y - 60), "A / D: seç   ·   E ya da Boşluk: onayla", 8, Color(C_TEXT, 0.6 + 0.4 * sin(_t * 3.0)), HORIZONTAL_ALIGNMENT_CENTER, vp.x)


var _kut_pulse := 0.0


func kut_pulse() -> void:
	_kut_pulse = 0.4


func _draw_umay(vp: Vector2) -> void:
	draw_rect(Rect2(Vector2.ZERO, vp), Color(0.03, 0.05, 0.08, 0.82))
	_txt(Vector2(0, 40), "UMAY ANA", 22, Color(0.6, 1.0, 1.0), HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	_txt(Vector2(0, 58), "«Getirdiğin Kut ağaca işledi. Söyle, hangi dalı güçlendireyim?»", 9, Color(0.8, 0.9, 0.95), HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	_txt(Vector2(0, 78), "Kut bankası: %d" % int(Game.meta.get("kut_bank", 0)), 12, Color(0.6, 0.95, 1.0), HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	var keys: Array = Game.UMAY.keys()
	var y := 96.0
	for i in keys.size():
		var id: String = keys[i]
		var u: Array = Game.UMAY[id]
		var lv := Game.umay_level(id)
		var mx: int = (u[2] as Array).size()
		var cost := Game.umay_cost(id)
		var is_sel := i == sel
		var rect := Rect2(vp.x / 2.0 - 200, y - 2, 400, 24)
		if is_sel:
			draw_rect(rect, Color(0.6, 0.95, 1.0, 0.14))
			draw_rect(rect, Color(0.6, 0.95, 1.0), false, 1.0)
		_txt(Vector2(vp.x / 2.0 - 192, y + 10), u[0], 9, C_TEXT if lv < mx else Color(0.6, 0.95, 1.0))
		_txt(Vector2(vp.x / 2.0 - 192, y + 19), u[1], 7, C_DIM)
		for k in mx:
			draw_rect(Rect2(vp.x / 2.0 + 60 + k * 10, y + 4, 8, 8), Color(0.6, 0.95, 1.0) if k < lv else Color(0.2, 0.22, 0.3))
		var ct := ("%d Kut" % cost) if cost >= 0 else "tamam"
		var can := cost >= 0 and int(Game.meta.get("kut_bank", 0)) >= cost
		_txt(Vector2(vp.x / 2.0 + 120, y + 12), ct, 9, (Color(0.6, 0.95, 1.0) if can else Color(0.6, 0.55, 0.65)) if cost >= 0 else Color(0.5, 0.8, 0.6))
		y += 28.0
	if flash_t > 0.0:
		_txt(Vector2(0, vp.y - 44), flash_msg, 9, C_GOLD, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	_txt(Vector2(0, vp.y - 24), "W/S: seç   ·   E: al   ·   Boşluk / Esc: ayrıl", 8, Color(C_TEXT, 0.6 + 0.4 * sin(_t * 3.0)), HORIZONTAL_ALIGNMENT_CENTER, vp.x)


func _draw_ozan(vp: Vector2) -> void:
	draw_rect(Rect2(Vector2.ZERO, vp), Color(0.06, 0.04, 0.03, 0.8))
	_txt(Vector2(0, 50), "OZAN BİLGE KOPUZ", 22, C_GOLD, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	var npc: Dictionary = Data.story["npcs"]["ozan"]
	var lines: Array = npc["first"] + npc["repeat"]
	var R: Dictionary = Game.run
	var bid: String = String(R.get("biome", "otuken"))
	var lore: Array = Data.story["lore"].get("otuken", [])
	var said: Array = []
	for k in mini(ozan_i + 1, 4):
		if k < 3:
			said.append(lines[(k + int(Game.meta.get("runs", 0))) % lines.size()])
		else:
			said.append(lore[int(Game.meta.get("runs", 0)) % maxi(1, lore.size())])
	var y := 86.0
	for s in said:
		for l in _wrap("«" + s + "»", 9, 420):
			_txt(Vector2(0, y), l, 9, Color(0.95, 0.9, 0.8), HORIZONTAL_ALIGNMENT_CENTER, vp.x)
			y += 13.0
		y += 6.0
	_txt(Vector2(0, vp.y - 60), "Bu koşu: %d. derinlik  ·  %d düşman  ·  %d:%02d  ·  en derin: %d" % [int(R.get("depth", 1)), int(R.get("kills", 0)), int(R.get("time", 0.0)) / 60, int(R.get("time", 0.0)) % 60, int(Game.meta.get("best_depth", 1))], 8, C_DIM, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	_txt(Vector2(0, vp.y - 24), "E / Boşluk: dinle   ·   Esc: ayrıl", 8, Color(C_TEXT, 0.6 + 0.4 * sin(_t * 3.0)), HORIZONTAL_ALIGNMENT_CENTER, vp.x)


func _draw_demirci(vp: Vector2) -> void:
	draw_rect(Rect2(Vector2.ZERO, vp), Color(0.05, 0.03, 0.04, 0.82))
	_txt(Vector2(0, 46), "DEMİRCİ KAM KUZGUN", 22, C_GOLD, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	_txt(Vector2(0, 64), "«Tomar getirdin. Kut ver, dövüp koşuna katayım.»", 9, Color(0.8, 0.75, 0.85), HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	_txt(Vector2(0, 84), "Kut bankası: %d" % int(Game.meta.get("kut_bank", 0)), 11, Color(0.6, 0.95, 1.0), HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	var bps: Array = Game.meta.get("blueprints", [])
	if bps.is_empty():
		_txt(Vector2(0, 150), "Bekleyen parşömen yok. Düşmanlar parşömen düşürür; seçkinler kesin düşürür.", 9, C_DIM, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	else:
		var n := bps.size()
		var w := 118.0
		var gap := 10.0
		var total := n * w + (n - 1) * gap
		var x0 := vp.x / 2.0 - total / 2.0
		if total > vp.x - 40:
			x0 = (vp.x - w) / 2.0 - sel * (w + gap)
		for i in n:
			var id: String = bps[i]
			var base := Data.find_item(id)
			var cost := Game.unlock_cost(id)
			var can := int(Game.meta.get("kut_bank", 0)) >= cost
			var x := x0 + i * (w + gap)
			var y := 104.0 - (6.0 if i == sel else 0.0)
			var rect := Rect2(x, y, w, 130)
			var col := Color(0.6, 0.95, 1.0) if can else Color(0.6, 0.55, 0.65)
			draw_rect(rect, Color(0.08, 0.06, 0.1, 0.96) if i != sel else Color(col, 0.16))
			draw_rect(rect, col if i == sel else Color(col, 0.4), false, 2.0 if i == sel else 1.0)
			if Data.has_weapon_sprite(id):
				var reg := Data.weapon_region(id, "demir")
				draw_texture_rect_region(Data.weapon_tex.diffuse_texture, Rect2(x + w / 2.0 - 32, y + 8, 64, 40), reg)
			_txt(Vector2(x, y + 60), base.get("name", id), 9, C_TEXT, HORIZONTAL_ALIGNMENT_CENTER, w)
			var cat_txt: String = {"weapons": "Silah", "shields": "Kalkan", "gadgets": "Teçhizat"}.get(base.get("cat", ""), "")
			_txt(Vector2(x, y + 72), cat_txt, 7, C_DIM, HORIZONTAL_ALIGNMENT_CENTER, w)
			var mech: Dictionary = base.get("mech", {})
			var desc: String = String(mech.get("desc", base.get("desc", ""))).replace("{v}", "?")
			var lines := _wrap(desc, 7, w - 12)
			for j in mini(4, lines.size()):
				_txt(Vector2(x + 6, y + 86 + j * 9), lines[j], 7, C_TEXT, HORIZONTAL_ALIGNMENT_LEFT, w - 12)
			_txt(Vector2(x, y + 124), "%d Kut" % cost, 9, col, HORIZONTAL_ALIGNMENT_CENTER, w)
	if flash_t > 0.0 and flash_msg != "":
		_txt(Vector2(0, 258), flash_msg, 9, Color(C_GOLD, clampf(flash_t, 0.0, 1.0)), HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	_txt(Vector2(0, vp.y - 40), "A / D: seç   ·   E: parşömeni aç   ·   Boşluk / Enter: yola çık", 8, Color(C_TEXT, 0.6 + 0.4 * sin(_t * 3.0)), HORIZONTAL_ALIGNMENT_CENTER, vp.x)
	_txt(Vector2(0, vp.y - 26), "Açılan eşyalar bundan sonraki koşularda düşer.", 7, C_DIM, HORIZONTAL_ALIGNMENT_CENTER, vp.x)
