class_name PixUI
extends RefCounted
## Arayüz çizim yardımcıları (ortak imzalar ve palet): yazı, paneller, simgeler, ongun rozetleri, silah simgeleri.
## Çizimin kendisi mürekkep arayüzündedir (InkUI: vektör yazı + boyalı dokular). v30: eski piksel çizim dalları
## (pixel.fnt yazı tipi, çentikli piksel paneller, 7x7 piksel simgeler) kaldırıldı.

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

## Simge yerleşim kutuları (eski 7x7 piksel ızgarası; InkUI.icon simgeyi bu kutuya oturtur, HUD ölçüleri buna göre)
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


static func width(s: String, sc := 1) -> float:
	return InkUI.width(s, sc)


static func text(ci: CanvasItem, pos: Vector2, s: String, col: Color, sc := 1, align := HORIZONTAL_ALIGNMENT_LEFT, w := -1.0, style := 1) -> void:
	## pos: satır kutusunun SOL ÜST köşesi. style 0: düz, 1: gölge, 2: tam dış çizgi.
	InkUI.text(ci, pos, s, col, sc, align, w, style)


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
	InkUI.rect(ci, r, col)


static func panel(ci: CanvasItem, r: Rect2, edge := EDGE, fill := INK, drop := true) -> void:
	## Panel (InkUI: boyalı çerçeve, iç dolgu)
	InkUI.panel(ci, r, edge, fill, drop)


static func fancy_panel(ci: CanvasItem, r: Rect2, edge := EDGE, fill := INK) -> void:
	## Süslü panel: köşelerde koçboynuzu motifi
	InkUI.fancy_panel(ci, r, edge, fill)


static func horn(ci: CanvasItem, p: Vector2, col: Color, dir := 1) -> void:
	## Küçük koçboynuzu (kilim motifi), 5x4 px
	InkUI.horn(ci, p, col, dir)


static func divider(ci: CanvasItem, x: float, y: float, w: float, col := EDGE) -> void:
	## Ortasında elmas olan ince ayraç
	InkUI.divider(ci, x, y, w, col)


static func icon(ci: CanvasItem, name: String, pos: Vector2, col: Color, sc := 1, shadow := true) -> void:
	if InkUI.has_icon(name):
		InkUI.icon(ci, name, pos, col, sc, shadow, icon_size(name) * sc)
	else:
		PikselIz.iz("PixUI.icon mürekkep simgesi yok: " + name)


static func icon_size(name: String) -> Vector2:
	var rows: Array = ICONS.get(name, [])
	return Vector2(String(rows[0]).length() if rows.size() > 0 else 0, rows.size())


static func key_w(k: String) -> float:
	## Tuş rozetinin genişliği (yerleşim için)
	return InkUI.key_w(k)


static func key_cap(ci: CanvasItem, pos: Vector2, k: String, col := GOLD, active := true) -> void:
	## Tuş rozeti: [J]
	InkUI.key_cap(ci, pos, k, col, active)


static func ongun_col(o: String) -> Color:
	return Color.from_string(Data.items["ongun"].get(o, {}).get("color", "#ffffff"), TEXT)


static func ongun_stripe(ci: CanvasItem, r: Rect2, onguns: Array, active := "") -> void:
	## Yuva altındaki renk şeridi: tek ya da iki renk (Dead Cells gibi); etkin olan parlak.
	if onguns.is_empty():
		return
	var cs: Array = []
	var dm: Array = []
	for o in onguns:
		cs.append(ongun_col(o))
		dm.append(onguns.size() > 1 and active != "" and o != active)
	InkUI.ongun_stripe(ci, r, cs, dm)


static func weapon(ci: CanvasItem, it: Dictionary, center: Vector2, max_size: Vector2, sc := 1.0) -> void:
	## Silah sprite'ını sıkı kırpılmış hâliyle ortalayarak çizer; sığmazsa küçültür (mürekkep-cel atlas, InkUI.weapon).
	InkUI.weapon(ci, it, center, max_size, sc)


static func bar(ci: CanvasItem, r: Rect2, k: float, col: Color, bg := Color(0.12, 0.08, 0.14)) -> void:
	InkUI.bar(ci, r, k, col, bg)
