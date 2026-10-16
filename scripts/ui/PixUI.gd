class_name PixUI
extends RefCounted
## Piksel arayüz çizim yardımcıları: keskin yazı (gölge / dış çizgi), çentikli paneller, piksel simgeler,
## ongun rozetleri. Her şey tam sayı koordinatlarda çizilir; yazı tipi 13 px = 1x (tools/artgen/pixfont.py).

const FS := 13
const BASE := 10

# palet: gece mürekkebi, bronz çerçeve, kemik beyazı metin
const INK := Color(0.055, 0.043, 0.082, 0.94)
const INK2 := Color(0.1, 0.08, 0.14, 0.96)
const EDGE := Color(0.62, 0.47, 0.25)
const EDGE_HI := Color(0.95, 0.78, 0.45)
const EDGE_LO := Color(0.25, 0.17, 0.12)
const TEXT := Color(0.95, 0.91, 0.83)
const DIM := Color(0.6, 0.57, 0.66)
const GOLD := Color(1.0, 0.82, 0.38)
const KUT := Color(0.45, 0.93, 1.0)
const RED := Color(0.86, 0.24, 0.22)
const GOOD := Color(0.55, 0.92, 0.45)
const BAD := Color(1.0, 0.42, 0.36)
const SHADOW := Color(0.03, 0.02, 0.05, 0.95)

## 7x7 piksel simgeler ('#' ana renk, '+' açık ton, 'o' koyu ton)
const ICONS := {
	"kurt": ["#.....#", "##...##", "#######", "#o###o#", "#######", ".##+##.", "..###.."],
	"kartal": ["...#...", "#.###.#", "##+#+##", ".#####.", "..###..", "..#.#..", ".##.##."],
	"ayi": [".#...#.", "###.###", "#######", "#o###o#", "##+++##", ".#####.", "..###.."],
	"altin": [".###.", "#+###", "#+#o#", "####o", ".###."],
	"kut": ["..#..", ".#+#.", "#+###", "#####", ".###.", "..#.."],
	"sise": [".###.", "..#..", ".#+#.", "#+###", "#####", "#####", ".###."],
	"can": [".##.##.", "#+#####", "#######", ".#####.", "..###..", "...#..."],
	"kafatasi": [".#####.", "#######", "#o##o##", "#######", ".##.##.", ".#####.", ".#.#.#."],
	"tilsim": ["#####", "#+++#", "#####", "#+++#", "#####"],
	"kilic": ["......#", ".....#.", "....#..", "#..#...", ".##....", ".##....", "#..#..."],
	"zaman": [".###.", "#.#.#", "#.##.", "#...#", ".###."],
}


static func font() -> Font:
	return Data.pixel_font if Data.pixel_font else ThemeDB.fallback_font


static func width(s: String, sc := 1) -> float:
	if InkUI.on():
		return InkUI.width(s, sc)
	return font().get_string_size(s, HORIZONTAL_ALIGNMENT_LEFT, -1, FS * sc).x


static func text(ci: CanvasItem, pos: Vector2, s: String, col: Color, sc := 1, align := HORIZONTAL_ALIGNMENT_LEFT, w := -1.0, style := 1) -> void:
	## pos: satır kutusunun SOL ÜST köşesi. style 0: düz, 1: gölge, 2: tam dış çizgi.
	if InkUI.on():
		InkUI.text(ci, pos, s, col, sc, align, w, style)
		return
	var x := pos.x
	if w > 0.0 and align != HORIZONTAL_ALIGNMENT_LEFT:
		var tw := width(s, sc)
		x += (w - tw) * (0.5 if align == HORIZONTAL_ALIGNMENT_CENTER else 1.0)
	var p := Vector2(roundf(x), roundf(pos.y) + BASE * sc)
	var f := font()
	var sh := Color(SHADOW, SHADOW.a * col.a)
	if style == 2:
		for o in [Vector2(-1, 0), Vector2(1, 0), Vector2(0, -1), Vector2(0, 1), Vector2(1, 1), Vector2(-1, 1), Vector2(1, -1), Vector2(-1, -1)]:
			ci.draw_string(f, p + o * sc, s, HORIZONTAL_ALIGNMENT_LEFT, -1, FS * sc, sh)
	elif style == 1:
		ci.draw_string(f, p + Vector2(1, 1) * sc, s, HORIZONTAL_ALIGNMENT_LEFT, -1, FS * sc, sh)
	ci.draw_string(f, p, s, HORIZONTAL_ALIGNMENT_LEFT, -1, FS * sc, col)


static func wrap(s: String, maxw: float, sc := 1) -> Array:
	var words := s.split(" ")
	var lines: Array = []
	var cur := ""
	for wd in words:
		var t: String = (cur + " " + wd).strip_edges()
		if width(t, sc) > maxw and cur != "":
			lines.append(cur)
			cur = wd
		else:
			cur = t
	if cur != "":
		lines.append(cur)
	return lines


static func rect(ci: CanvasItem, r: Rect2, col: Color) -> void:
	if InkUI.on():
		InkUI.rect(ci, r, col)
		return
	ci.draw_rect(Rect2(r.position.round(), r.size.round()), col)


static func panel(ci: CanvasItem, r: Rect2, edge := EDGE, fill := INK, drop := true) -> void:
	## Çentikli köşeli panel: 1 px gölge, iç dolgu, kenarda açık üst / koyu alt çizgi.
	if InkUI.on():
		InkUI.panel(ci, r, edge, fill, drop)
		return
	var x := roundf(r.position.x)
	var y := roundf(r.position.y)
	var w := roundf(r.size.x)
	var h := roundf(r.size.y)
	if drop:
		ci.draw_rect(Rect2(x + 2, y + h, w - 2, 2), Color(0, 0, 0, 0.35 * fill.a))
		ci.draw_rect(Rect2(x + w, y + 2, 2, h), Color(0, 0, 0, 0.35 * fill.a))
	ci.draw_rect(Rect2(x + 1, y + 1, w - 2, h - 2), fill)
	# kenarlar (köşeler çentikli)
	ci.draw_rect(Rect2(x + 2, y, w - 4, 1), edge)
	ci.draw_rect(Rect2(x + 2, y + h - 1, w - 4, 1), edge.darkened(0.35))
	ci.draw_rect(Rect2(x, y + 2, 1, h - 4), edge.darkened(0.15))
	ci.draw_rect(Rect2(x + w - 1, y + 2, 1, h - 4), edge.darkened(0.15))
	ci.draw_rect(Rect2(x + 1, y + 1, 1, 1), edge)
	ci.draw_rect(Rect2(x + w - 2, y + 1, 1, 1), edge)
	ci.draw_rect(Rect2(x + 1, y + h - 2, 1, 1), edge.darkened(0.35))
	ci.draw_rect(Rect2(x + w - 2, y + h - 2, 1, 1), edge.darkened(0.35))
	# iç parıltı çizgisi
	ci.draw_rect(Rect2(x + 2, y + 1, w - 4, 1), Color(1, 1, 1, 0.06))


static func fancy_panel(ci: CanvasItem, r: Rect2, edge := EDGE, fill := INK) -> void:
	## Süslü panel: köşelerde koçboynuzu motifi
	if InkUI.on():
		InkUI.fancy_panel(ci, r, edge, fill)
		return
	panel(ci, r, edge, fill)
	var x := roundf(r.position.x)
	var y := roundf(r.position.y)
	var w := roundf(r.size.x)
	var h := roundf(r.size.y)
	horn(ci, Vector2(x + 3, y + 3), edge, 1)
	horn(ci, Vector2(x + w - 8, y + 3), edge, -1)
	ci.draw_rect(Rect2(x + 3, y + h - 4, 5, 1), edge.darkened(0.3))
	ci.draw_rect(Rect2(x + w - 8, y + h - 4, 5, 1), edge.darkened(0.3))


static func horn(ci: CanvasItem, p: Vector2, col: Color, dir := 1) -> void:
	## Küçük koçboynuzu (kilim motifi), 5x4 px
	if InkUI.on():
		InkUI.horn(ci, p, col, dir)
		return
	var pts := [Vector2(0, 0), Vector2(1, 0), Vector2(2, 0), Vector2(0, 1), Vector2(0, 2), Vector2(1, 2), Vector2(2, 1), Vector2(3, 3), Vector2(4, 3)]
	for q in pts:
		var qx: float = q.x if dir > 0 else 4.0 - q.x
		ci.draw_rect(Rect2(p.x + qx, p.y + q.y, 1, 1), col)


static func divider(ci: CanvasItem, x: float, y: float, w: float, col := EDGE) -> void:
	## Ortasında elmas olan ince ayraç
	if InkUI.on():
		InkUI.divider(ci, x, y, w, col)
		return
	var cx := roundf(x + w / 2.0)
	ci.draw_rect(Rect2(roundf(x), roundf(y), roundf(w / 2.0) - 4, 1), Color(col, 0.6))
	ci.draw_rect(Rect2(cx + 4, roundf(y), roundf(w / 2.0) - 4, 1), Color(col, 0.6))
	ci.draw_rect(Rect2(cx - 1, roundf(y) - 1, 3, 3), col)
	ci.draw_rect(Rect2(cx, roundf(y) - 2, 1, 5), col)
	ci.draw_rect(Rect2(cx - 2, roundf(y), 5, 1), col)


static func icon(ci: CanvasItem, name: String, pos: Vector2, col: Color, sc := 1, shadow := true) -> void:
	if InkUI.on() and InkUI.has_icon(name):
		InkUI.icon(ci, name, pos, col, sc, shadow, icon_size(name) * sc)
		return
	PikselIz.iz("PixUI.icon piksel simge: " + name)
	var rows: Array = ICONS.get(name, [])
	var p := pos.round()
	for pass_i in (2 if shadow else 1):
		for y in rows.size():
			var r: String = rows[y]
			for x in r.length():
				var ch := r[x]
				if ch == ".":
					continue
				var c := col
				if pass_i == 0 and shadow:
					c = SHADOW
				elif ch == "+":
					c = col.lightened(0.45)
				elif ch == "o":
					c = col.darkened(0.6)
				var off := Vector2(sc, sc) if (pass_i == 0 and shadow) else Vector2.ZERO
				ci.draw_rect(Rect2(p + Vector2(x, y) * sc + off, Vector2(sc, sc)), c)


static func icon_size(name: String) -> Vector2:
	var rows: Array = ICONS.get(name, [])
	return Vector2(String(rows[0]).length() if rows.size() > 0 else 0, rows.size())


static func key_w(k: String) -> float:
	## Tuş rozetinin genişliği (yerleşim için)
	if InkUI.on():
		return InkUI.key_w(k)
	return maxf(9.0, width(k) + 4.0)


static func key_cap(ci: CanvasItem, pos: Vector2, k: String, col := GOLD, active := true) -> void:
	## Tuş rozeti: [J]
	if InkUI.on():
		InkUI.key_cap(ci, pos, k, col, active)
		return
	var w := maxf(9.0, width(k) + 4.0)
	var r := Rect2(pos.round(), Vector2(w, 11))
	ci.draw_rect(Rect2(r.position + Vector2(1, 1), r.size), SHADOW)
	ci.draw_rect(r, Color(0.16, 0.12, 0.2) if active else Color(0.1, 0.09, 0.13))
	ci.draw_rect(Rect2(r.position, Vector2(w, 1)), Color(col, 0.9 if active else 0.4))
	ci.draw_rect(Rect2(r.position + Vector2(0, 10), Vector2(w, 1)), Color(col, 0.5 if active else 0.25).darkened(0.4))
	text(ci, r.position + Vector2(0, 0), k, col if active else DIM, 1, HORIZONTAL_ALIGNMENT_CENTER, w, 0)


static func ongun_col(o: String) -> Color:
	return Color.from_string(Data.items["ongun"].get(o, {}).get("color", "#ffffff"), TEXT)


static func ongun_stripe(ci: CanvasItem, r: Rect2, onguns: Array, active := "") -> void:
	## Yuva altındaki renk şeridi: tek ya da iki renk (Dead Cells gibi); etkin olan parlak.
	if onguns.is_empty():
		return
	if InkUI.on():
		var cs: Array = []
		var dm: Array = []
		for o in onguns:
			cs.append(ongun_col(o))
			dm.append(onguns.size() > 1 and active != "" and o != active)
		InkUI.ongun_stripe(ci, r, cs, dm)
		return
	var n := onguns.size()
	var w := roundf(r.size.x / n)
	for i in n:
		var c := ongun_col(onguns[i])
		if n > 1 and active != "" and onguns[i] != active:
			c = c.darkened(0.45)
		var x := roundf(r.position.x) + i * w
		var ww := w if i < n - 1 else roundf(r.size.x) - w * (n - 1)
		ci.draw_rect(Rect2(x, roundf(r.position.y), ww, roundf(r.size.y)), c)
		ci.draw_rect(Rect2(x, roundf(r.position.y), ww, 1), c.lightened(0.35))


static func weapon(ci: CanvasItem, it: Dictionary, center: Vector2, max_size: Vector2, sc := 1.0) -> void:
	## Silah sprite'ını sıkı kırpılmış hâliyle ortalayarak çizer; sığmazsa küçültür.
	if InkUI.on() and InkUI.weapon(ci, it, center, max_size, sc):
		return
	if it.is_empty() or not Data.has_weapon_sprite(it["id"]):
		return
	PikselIz.iz("PixUI.weapon v1 piksel silah simgesi: " + String(it["id"]))
	var reg := Data.weapon_icon_rect(it["id"], it["material"])
	var s := sc / Data.weapon_texel
	if reg.size.x * s > max_size.x or reg.size.y * s > max_size.y:
		s = minf(max_size.x / reg.size.x, max_size.y / reg.size.y)
		if s >= 1.0:
			s = floorf(s)
	var size := reg.size * s
	var p := (center - size / 2.0).round()
	ci.draw_texture_rect_region(Data.weapon_tex.diffuse_texture, Rect2(p + Vector2(1, 1) * maxf(1.0, s), size), reg, Color(0, 0, 0, 0.55))
	ci.draw_texture_rect_region(Data.weapon_tex.diffuse_texture, Rect2(p, size), reg)


static func bar(ci: CanvasItem, r: Rect2, k: float, col: Color, bg := Color(0.12, 0.08, 0.14)) -> void:
	if InkUI.on():
		InkUI.bar(ci, r, k, col, bg)
		return
	var x := roundf(r.position.x)
	var y := roundf(r.position.y)
	var w := roundf(r.size.x)
	var h := roundf(r.size.y)
	ci.draw_rect(Rect2(x, y, w, h), bg)
	var fw := roundf(w * clampf(k, 0.0, 1.0))
	if fw > 0:
		ci.draw_rect(Rect2(x, y, fw, h), col)
		ci.draw_rect(Rect2(x, y, fw, 1), col.lightened(0.35))
		if h > 2:
			ci.draw_rect(Rect2(x, y + h - 1, fw, 1), col.darkened(0.35))
