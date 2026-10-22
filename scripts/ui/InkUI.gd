class_name InkUI
extends RefCounted
## Mürekkep arayüzü: PixUI'nin aynı imzalı çizim yardımcıları bu sınıfa düşer.
## Yazı: Alegreya Sans (gövde), Cinzel (büyük harf yazıt başlıkları), Kaushan Script (fırça başlık / rakam),
## Alegreya (anlatı). Hepsi SIL OFL (assets/ui/fonts/LICENSE.txt). Yazılar vektör: 1080p / 4K'da keskin.

const DIR := "res://assets/ui/fonts/"

# palet: gece mürekkebi, kâğıt, zerdeçal-bronz, kızıl mühür
const INK := Color(0.045, 0.04, 0.06)
const PAPER := Color(0.93, 0.88, 0.78)
const SEAL := Color(0.72, 0.12, 0.09)
const BLOOD := Color(0.78, 0.1, 0.09)

static var _fonts: Dictionary = {}


static func _font(key: String) -> Font:
	if _fonts.has(key):
		return _fonts[key]
	var f: Font = null
	match key:
		"body":
			f = _file("AlegreyaSans-Medium.ttf")
		"bold":
			f = _file("AlegreyaSans-Bold.ttf")
		"lore":
			f = _var(_file("Alegreya-VF.ttf"), 500)
		"caps":
			f = _var(_file("Cinzel-VF.ttf"), 700)
		"brush":
			f = _file("KaushanScript-Regular.ttf")
	if f == null:
		f = ThemeDB.fallback_font
	_fonts[key] = f
	return f


static func _file(n: String) -> FontFile:
	var f: FontFile = load(DIR + n)
	if f == null:
		return null
	f.antialiasing = TextServer.FONT_ANTIALIASING_GRAY
	f.hinting = TextServer.HINTING_LIGHT
	f.subpixel_positioning = TextServer.SUBPIXEL_POSITIONING_AUTO
	f.generate_mipmaps = true
	if n != "AlegreyaSans-Medium.ttf" and n != "AlegreyaSans-Bold.ttf":
		var fb: FontFile = load(DIR + "AlegreyaSans-Medium.ttf")
		if fb:
			f.fallbacks = [fb]
	return f


static func _var(base: FontFile, wght: int) -> Font:
	if base == null:
		return null
	var v := FontVariation.new()
	v.base_font = base
	v.variation_opentype = {TextServerManager.get_primary_interface().name_to_tag("wght"): wght}
	return v


static func font(key := "body") -> Font:
	return _font(key)


static func setup() -> void:
	## Etiketlerin (Label) varsayılan yazı tipi de mürekkep gövde yazısı olsun (seçkin düşman adları vb.)
	ThemeDB.fallback_font = _font("bold")


# ------------------------------------------------------------------ yazı seçimi
static func is_caps(s: String) -> bool:
	## Harf içeren ve küçük harfi olmayan metin (BAŞLIK) -> yazıt yazısı
	var letters := 0
	for c in s:
		if c != c.to_upper() and c != "ı":
			return false
		if c == "ı":
			return false
		if c.to_upper() != c.to_lower() or c in "İIŞĞÜÖÇ":
			letters += 1
	return letters >= 2


static func tr_lower(s: String) -> String:
	return s.replace("I", "ı").replace("İ", "i").to_lower()


static func tr_title(s: String) -> String:
	## Türkçe baş harf büyütme: "KAM TILSIMI" -> "Kam Tılsımı" (fırça yazısı büyük harf dizisinde zor okunur)
	var low := tr_lower(s)
	var out := ""
	var start := true
	for c in low:
		if start and c != " " and c != "'":
			out += "İ" if c == "i" else ("I" if c == "ı" else c.to_upper())
			start = false
		else:
			out += c
		if c == " " or c == "-" or c == "«":
			start = true
	return out


static func spec(s: String, sc: int) -> Dictionary:
	## {font, size, base(taban çizgisi kayması), txt}: PixUI ölçeğine (13 px = 1x) denk düşen yazı
	if sc >= 2:
		var t := tr_title(s) if is_caps(s) else s
		var size := 25 if sc == 2 else 38
		return {"font": _font("brush"), "size": size, "base": 21.0 if sc == 2 else 31.0, "txt": t}
	if is_caps(s):
		return {"font": _font("caps"), "size": 10, "base": 9.5, "txt": s}
	return {"font": _font("body"), "size": 10, "base": 9.0, "txt": s}


static func clean(s: String) -> String:
	return s.replace("★", "◆")


static func width(s: String, sc := 1) -> float:
	var sp := spec(clean(s), sc)
	return (sp["font"] as Font).get_string_size(sp["txt"], HORIZONTAL_ALIGNMENT_LEFT, -1, sp["size"]).x


static func text(ci: CanvasItem, pos: Vector2, s: String, col: Color, sc := 1, align := HORIZONTAL_ALIGNMENT_LEFT, w := -1.0, style := 1) -> void:
	## PixUI.text ile aynı: pos satır kutusunun sol üstü. style 0 düz, 1 fırça gölgesi, 2 mürekkep dış çizgisi.
	var sp := spec(clean(s), sc)
	var f: Font = sp["font"]
	var size: int = sp["size"]
	var t: String = sp["txt"]
	var x := pos.x
	if w > 0.0 and align != HORIZONTAL_ALIGNMENT_LEFT:
		var tw := f.get_string_size(t, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x
		x += (w - tw) * (0.5 if align == HORIZONTAL_ALIGNMENT_CENTER else 1.0)
	var p := Vector2(x, pos.y + float(sp["base"]))
	draw_str(ci, p, t, f, size, col, style, sc)


static func draw_str(ci: CanvasItem, p: Vector2, t: String, f: Font, size: int, col: Color, style := 1, sc := 1) -> void:
	var sh := Color(INK, 0.85 * col.a)
	if style == 2:
		var o := 4 if sc == 1 else (6 if sc == 2 else 8)
		ci.draw_string(f, p + Vector2(0.6, 0.9) * maxf(1.0, sc * 0.8), t, HORIZONTAL_ALIGNMENT_LEFT, -1, size, Color(INK, 0.55 * col.a))
		ci.draw_string_outline(f, p, t, HORIZONTAL_ALIGNMENT_LEFT, -1, size, o, sh)
	elif style == 1:
		ci.draw_string(f, p + Vector2(0.6, 0.8) * maxf(1.0, sc * 0.8), t, HORIZONTAL_ALIGNMENT_LEFT, -1, size, Color(INK, 0.7 * col.a))
	ci.draw_string(f, p, t, HORIZONTAL_ALIGNMENT_LEFT, -1, size, col)


# ================================================================== dokular (tools/artgen/ui_ink.py)
const TEX_DIR := "res://assets/ui/ink/"
const ICONS := ["can", "sise", "altin", "kut", "kurt", "kartal", "ayi", "kafatasi", "zaman", "kilic", "tilsim", "davul", "ruh", "kalkan"]
## v40 ek simgeler (tools/artgen/ui_ink40.py -> icons2.png): durumlar, nişan, harita, ok, seçkin yıldızı, hız, nakış, mühür
const ICONS2 := ["ates", "buz", "zehir", "kan", "damga", "nazar", "nisan", "harita", "ok", "yildiz", "hiz", "nakis", "muhur"]
const ICON_PX := 128.0
## doku yoğunluğu: arayüz biriminde kaç doku pikseli (menüler 3 = 1080p'de 1:1; HUD daha ince çizgi için 4)
static var den := 3.0
static var _tex: Dictionary = {}


static func tex(n: String) -> Texture2D:
	if not _tex.has(n):
		_tex[n] = Data.tex(TEX_DIR + n + ".png")   # HD paketi varsa 2 kat ayrıntı (temel boyutta raporlanır)
	return _tex[n]


static func nine(ci: CanvasItem, r: Rect2, t: Texture2D, m_px: float, col: Color, d := -1.0) -> void:
	## 9 dilim: köşeler doku yoğunluğunda (m_px / den birim), kenarlar ve orta gerilir
	if t == null or r.size.x <= 0.5 or r.size.y <= 0.5:
		return
	var dd := den if d <= 0.0 else d
	var ts := t.get_size()
	var mu := minf(m_px / dd, minf(r.size.x, r.size.y) * 0.5)
	var xs := [r.position.x, r.position.x + mu, r.end.x - mu, r.end.x]
	var ys := [r.position.y, r.position.y + mu, r.end.y - mu, r.end.y]
	# orta dilimler: kaynak, hedef uzunluğu x yoğunluk kadar kırpılır (sıkıştırılmaz). Aksi hâlde küçük panelde
	# uzun kenar tek yönde 10 kat küçülür, mipmap çizgiyi geniş bir renk bandına yayar.
	var k := minf(1.0, mu * dd / m_px)  # köşe küçüldüyse kenar yoğunluğu da aynı oranda
	var sw := minf(ts.x - 2.0 * m_px, maxf(4.0, (xs[2] - xs[1]) * dd / k))
	var sh := minf(ts.y - 2.0 * m_px, maxf(4.0, (ys[2] - ys[1]) * dd / k))
	var cx0 := roundf((ts.x - sw) * 0.5)
	var cy0 := roundf((ts.y - sh) * 0.5)
	var us := [Vector2(0.0, m_px), Vector2(cx0, sw), Vector2(ts.x - m_px, m_px)]
	var vs := [Vector2(0.0, m_px), Vector2(cy0, sh), Vector2(ts.y - m_px, m_px)]
	for j in 3:
		for i in 3:
			var dst := Rect2(xs[i], ys[j], xs[i + 1] - xs[i], ys[j + 1] - ys[j])
			if dst.size.x <= 0.01 or dst.size.y <= 0.01:
				continue
			var u: Vector2 = us[i]
			var v: Vector2 = vs[j]
			ci.draw_texture_rect_region(t, dst, Rect2(u.x, v.x, u.y, v.y), col)


static func quad(ci: CanvasItem, t: Texture2D, c: Vector2, size: Vector2, ang: float, col: Color, region := Rect2()) -> void:
	## Döndürülmüş doku dörtgeni (çizim dönüşümünü bozmadan)
	if t == null:
		return
	var ts := t.get_size()
	var rg := region if region.size != Vector2.ZERO else Rect2(Vector2.ZERO, ts)
	var ax := Vector2.from_angle(ang) * size.x * 0.5
	var ay := Vector2.from_angle(ang + PI * 0.5) * size.y * 0.5
	var pts := PackedVector2Array([c - ax - ay, c + ax - ay, c + ax + ay, c - ax + ay])
	var u0 := rg.position / ts
	var u1 := rg.end / ts
	var uvs := PackedVector2Array([u0, Vector2(u1.x, u0.y), u1, Vector2(u0.x, u1.y)])
	ci.draw_primitive(pts, PackedColorArray([col, col, col, col]), uvs, t)


# ================================================================== PixUI karşılıkları
static func panel(ci: CanvasItem, r: Rect2, edge: Color, fill: Color, drop := true) -> void:
	## Mürekkep yıkaması dolgu + kalın siyah fırça çerçeve + renkli ince kuru fırça çizgi.
	## Alçak paneller (rozet, satır) yatay fırça sürmesi olur.
	var a := fill.a
	if r.size.y < 19.0:
		var sw := tex("swash")
		var rr := r.grow_individual(4.0, 2.0, 6.0, 2.0)
		if drop:
			ci.draw_texture_rect(sw, Rect2(rr.position + Vector2(1.5, 1.5), rr.size), false, Color(0, 0, 0, 0.35 * a))
		ci.draw_texture_rect(sw, rr, false, Color(fill.r * 1.25, fill.g * 1.25, fill.b * 1.25, minf(1.0, a * 1.02)))
		var st := tex("stroke")
		ci.draw_texture_rect(st, Rect2(r.position.x + 1.0, r.end.y - 1.2, r.size.x - 2.0, 2.4), false, Color(edge, edge.a * 0.85))
		return
	var fl := tex("fill")
	if drop:
		nine(ci, Rect2(r.position + Vector2(2.5, 3.0), r.size), fl, 32.0, Color(0, 0, 0, 0.4 * a))
	nine(ci, r.grow(1.0), fl, 32.0, Color(fill.r * 1.35, fill.g * 1.35, fill.b * 1.35, a))
	if r.size.y < 44.0:
		# satır: alt kenarda renkli fırça çizgisi, uçlarda mürekkep tırnakları
		var st := tex("stroke")
		ci.draw_texture_rect(st, Rect2(r.position.x - 3.0, r.end.y - 2.2, r.size.x + 6.0, 3.6), false, Color(INK, 0.9 * maxf(a, edge.a)))
		ci.draw_texture_rect(st, Rect2(r.position.x + 2.0, r.end.y - 1.6, r.size.x - 4.0, 2.0), false, Color(edge.lightened(0.1), edge.a * 0.95))
		ci.draw_texture_rect(st, Rect2(r.position.x + 6.0, r.position.y - 0.6, r.size.x * 0.55, 1.4), false, Color(edge, edge.a * 0.3))
		for sx in [r.position.x - 1.0, r.end.x - 1.0]:
			quad(ci, st, Vector2(sx + 0.5, r.get_center().y), Vector2(r.size.y + 4.0, 3.2), PI * 0.5, Color(INK, 0.85 * a))
		return
	# kalın çerçeve kenarın üstünde durur (içerik alanını yemesin): doku yoğunluğu 4, 7 birim dışa
	nine(ci, r.grow(7.0), tex("frame_ink"), 48.0, Color(INK, 0.95 * maxf(a, edge.a)), 4.0)
	nine(ci, r.grow(7.0), tex("frame_line"), 48.0, Color(edge.lightened(0.1), edge.a * 0.95), 4.0)


static func fancy_panel(ci: CanvasItem, r: Rect2, edge: Color, fill: Color) -> void:
	## Süslü panel: üst kenarın ortasında mürekkep lekesi üstünde koçboynuzu, alt köşelerde küçük boynuzlar
	panel(ci, r, edge, fill)
	var hs := clampf(r.size.x * 0.08, 12.0, 22.0)
	var c := Vector2(r.get_center().x, r.position.y - 1.0)
	ci.draw_texture_rect(tex("splat"), Rect2(c - Vector2(hs, hs) * 0.75, Vector2(hs, hs) * 1.5), false, Color(INK, 0.85 * edge.a))
	ci.draw_texture_rect(tex("horn"), Rect2(c - Vector2(hs, hs * 0.8) * 0.5, Vector2(hs, hs * 0.8)), false, Color(edge.lightened(0.15), edge.a))
	for sx in [-1.0, 1.0]:
		var p := Vector2(r.get_center().x + sx * (r.size.x * 0.5 - 8.0), r.end.y - 5.0)
		quad(ci, tex("horn"), p, Vector2(8, 7), PI, Color(edge, 0.55 * edge.a))


static func horn(ci: CanvasItem, p: Vector2, col: Color, dir := 1) -> void:
	## Küçük koçboynuzu süsü (PixUI.horn 5x4 kutusunun ortasına, yana yatık)
	var c := p + Vector2(2.5, 2.0)
	quad(ci, tex("horn"), c, Vector2(10, 9), PI * 0.5 * float(dir), col)


static func divider(ci: CanvasItem, x: float, y: float, w: float, col: Color) -> void:
	var st := tex("stroke")
	var cx := x + w * 0.5
	ci.draw_texture_rect(st, Rect2(x, y - 1.2, w * 0.5 - 7.0, 2.4), false, Color(col, 0.75 * col.a))
	ci.draw_texture_rect(st, Rect2(cx + 7.0, y - 1.2, w * 0.5 - 7.0, 2.4), false, Color(col, 0.75 * col.a))
	ci.draw_texture_rect(tex("horn"), Rect2(cx - 5.5, y - 5.0, 11, 9), false, col)


static func icon_region(name: String) -> Rect2:
	var i := ICONS.find(name)
	if i < 0:
		i = ICONS2.find(name)   # v40 ek simgeler (icons2.png)
	if i < 0:
		return Rect2()
	return Rect2(i * ICON_PX, 0, ICON_PX, ICON_PX)


static func icon_tex(name: String) -> Texture2D:
	return tex("icons") if ICONS.has(name) else tex("icons2")


static func has_icon(name: String) -> bool:
	return ICONS.has(name) or ICONS2.has(name)


static func icon(ci: CanvasItem, name: String, pos: Vector2, col: Color, sc := 1.0, shadow := true, box := Vector2.ZERO) -> void:
	## PixUI.icon kutusunun (box = piksel simge boyu x ölçek) ortasına, biraz daha büyük mürekkep simge
	var rg := icon_region(name)
	if rg.size == Vector2.ZERO:
		return
	var b := box if box != Vector2.ZERO else Vector2(7, 7) * sc
	var s := maxf(b.x, b.y) * 1.55
	var c := pos + b * 0.5
	var r := Rect2(c - Vector2(s, s) * 0.5, Vector2(s, s))
	var t := icon_tex(name)
	if shadow:
		ci.draw_texture_rect_region(t, Rect2(r.position + Vector2(0.8, 1.0) * maxf(1.0, sc * 0.6), r.size), rg, Color(0, 0, 0, 0.5 * col.a))
	ci.draw_texture_rect_region(t, r, rg, col.lightened(0.08))


static func icon_at(ci: CanvasItem, name: String, c: Vector2, s: float, col: Color, shadow := true) -> void:
	## Merkezden, s birim boyunda simge
	var b := Vector2(s, s) / 1.55
	icon(ci, name, c - b * 0.5, col, 1.0, shadow, b)


static func seal(ci: CanvasItem, r: Rect2, col: Color) -> void:
	nine(ci, r, tex("seal"), 52.0, col, 4.0)


static func key_w(k: String) -> float:
	if pad_on and PAD_MAP.has(k):
		return 13.0 if (PAD_MAP[k] as Array).size() == 1 else 25.0
	var fs := 9 if k.length() <= 3 else 8
	return maxf(9.0, _font("bold").get_string_size(k, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x + 4.0)


static func key_cap(ci: CanvasItem, pos: Vector2, k: String, col: Color, active := true) -> void:
	## Tuş mühürü: kızıl (ya da verilen renkte) fırça damgası, üstünde kâğıt rengi harf.
	## v40: son girdi oyun kolundan geldiyse (pad_on) klavye etiketi yerine kol simgesi (pad.png) çizilir.
	if pad_on and PAD_MAP.has(k):
		pad_glyph(ci, pos, k, col, active)
		return
	var f := _font("bold")
	var fs := 9 if k.length() <= 3 else 8
	var tw := f.get_string_size(k, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
	var w := maxf(9.0, tw + 4.0)
	var gold := Color(1.0, 0.82, 0.38)
	var sc: Color
	if active:
		sc = SEAL if Color(col, 1.0).is_equal_approx(gold) else col.darkened(0.35)
		sc.a = 1.0
	else:
		sc = Color(0.22, 0.2, 0.24, 0.8)
	sc.a *= col.a
	var r := Rect2(pos + Vector2(-1.5, -1.5), Vector2(w + 3.0, 14.0))
	seal(ci, Rect2(r.position + Vector2(0.8, 1.0), r.size), Color(0, 0, 0, 0.45 * col.a))
	seal(ci, r, sc)
	var tc := Color(PAPER, (1.0 if active else 0.6) * col.a)
	ci.draw_string(f, Vector2(pos.x + (w - tw) * 0.5, pos.y + 8.6), k, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, tc)


static func bar(ci: CanvasItem, r: Rect2, k: float, col: Color, bg: Color) -> void:
	## Fırça darbesi çubuk: koyu mürekkep zemin, renkli dolgu (doku soldan kırpılır), ince parlak üst kıl
	var st := tex("stroke")
	var ts := st.get_size()
	var g := maxf(1.5, r.size.y * 0.45)
	var rr := Rect2(r.position.x - 2.0, r.position.y - g, r.size.x + 4.0, r.size.y + g * 2.0)
	if bg.a > 0.0:
		ci.draw_texture_rect(st, rr, false, Color(INK.lerp(Color(bg, 1.0), 0.35), 0.82 * maxf(bg.a, 0.6)))
	var kk := clampf(k, 0.0, 1.0)
	if kk <= 0.0:
		return
	var fw := rr.size.x * kk
	var fr := Rect2(rr.position.x, rr.position.y + g * 0.35, fw, rr.size.y - g * 0.7)
	ci.draw_texture_rect_region(st, fr, Rect2(0, 0, ts.x * kk, ts.y), col)
	var hr := Rect2(fr.position.x + 2.0, fr.position.y + fr.size.y * 0.18, maxf(0.0, fw - 4.0), maxf(1.0, fr.size.y * 0.22))
	ci.draw_texture_rect_region(st, hr, Rect2(0, ts.y * 0.2, ts.x * kk, ts.y * 0.5), Color(col.lightened(0.45), 0.45 * col.a))


static func ongun_stripe(ci: CanvasItem, r: Rect2, cols: Array, dims: Array) -> void:
	## Ongun şeridi: yan yana kısa fırça darbeleri
	var n := cols.size()
	if n == 0:
		return
	var st := tex("stroke")
	var w := r.size.x / n
	for i in n:
		var c: Color = cols[i]
		if dims[i]:
			c = c.darkened(0.45)
		ci.draw_texture_rect(st, Rect2(r.position.x + i * w - 0.5, r.position.y - 0.8, w + 1.0, r.size.y + 1.6), false, c)


static func weapon(ci: CanvasItem, it: Dictionary, center: Vector2, max_size: Vector2, sc := 1.0) -> bool:
	## v2 silah atlası (weapons_v2): sığacak en büyük boyda, mürekkep gölgeli. Atlasta yoksa false (PixUI v1 çizer).
	if it.is_empty():
		return true
	var d: Dictionary = Data.weapon_sprite(it["id"], it.get("material", "demir"))
	if not d.get("linear", false):
		return false
	var reg: Rect2 = d["region"]
	var s := minf(max_size.x / reg.size.x, max_size.y / reg.size.y) * minf(1.0, sc)
	var size := reg.size * s
	var p := center - size * 0.5
	var t: Texture2D = d["tex"]
	ci.draw_texture_rect_region(t, Rect2(p + Vector2(1.2, 1.5), size), reg, Color(0, 0, 0, 0.55))
	ci.draw_texture_rect_region(t, Rect2(p, size), reg)
	return true


# ================================================================== özel parçalar
static func brush_arc(ci: CanvasItem, c: Vector2, r: float, a0: float, a1: float, w: float, col: Color) -> void:
	## Fırça yayı: ana çizgi + iki ince kıl izi
	if absf(a1 - a0) < 0.01:
		return
	var n := maxi(8, int(absf(a1 - a0) * r * 0.6))
	var sg := signf(a1 - a0)
	ci.draw_arc(c, r, a0, a1, n, col, w, true)
	ci.draw_arc(c, r + w * 0.42, a0 + 0.05 * sg, a1 - 0.12 * sg, n, Color(col, col.a * 0.55), w * 0.22, true)
	ci.draw_arc(c, r - w * 0.4, a0 + 0.12 * sg, a1 - 0.05 * sg, n, Color(col.lightened(0.3), col.a * 0.5), w * 0.2, true)


static func ring(ci: CanvasItem, c: Vector2, rad: float, k: float, col: Color, back := true) -> void:
	## Halka göstergesi: koyu yıkama + fırça daire (ensō) + dolum yayı
	if back:
		ci.draw_circle(c, rad * 0.98, Color(0.03, 0.028, 0.045, 0.82), true, -1.0, true)
		ci.draw_texture_rect(tex("enso"), Rect2(c - Vector2(rad, rad) * 1.3, Vector2(rad, rad) * 2.6), false, Color(INK, 0.95))
		ci.draw_texture_rect(tex("enso"), Rect2(c - Vector2(rad, rad) * 1.16, Vector2(rad, rad) * 2.32), false, Color(col, 0.3 * col.a))
	var kk := clampf(k, 0.0, 1.0)
	if kk > 0.0:
		brush_arc(ci, c, rad * 0.78, -PI * 0.5, -PI * 0.5 + TAU * kk, rad * 0.22, col)


static func wash(ci: CanvasItem, r: Rect2, a := 0.6) -> void:
	## Yatay mürekkep yıkama şeridi (başlık ve bilgi arkası)
	ci.draw_texture_rect(tex("band"), r, false, Color(INK, a))


static func vignette(ci: CanvasItem, vp: Vector2, a: float, col := INK) -> void:
	ci.draw_texture_rect(tex("vignette"), Rect2(Vector2.ZERO, vp), false, Color(col, a))


static func tamga(ci: CanvasItem, i: int, c: Vector2, s: float, col: Color) -> void:
	ci.draw_texture_rect_region(tex("tamga"), Rect2(c - Vector2(s, s) * 0.5, Vector2(s, s)), Rect2((i % 4) * 128, 0, 128, 128), col)


static func rect(ci: CanvasItem, r: Rect2, col: Color) -> void:
	## PixUI.rect karşılığı: ince şerit -> fırça darbesi, küçük kare -> mürekkep noktası, geniş alan -> yıkama dolgusu
	if r.size.x <= 0.0 or r.size.y <= 0.0:
		return
	if r.size.x <= 5.0 and r.size.y <= 5.0:
		splat(ci, r.get_center(), maxf(r.size.x, r.size.y) * 1.6, col, r.position.x * 0.7)
	elif r.size.y <= 4.0:
		ci.draw_texture_rect(tex("stroke"), r.grow_individual(1.5, 1.0, 1.5, 1.0), false, col)
	elif r.size.x <= 4.0:
		quad(ci, tex("stroke"), r.get_center(), Vector2(r.size.y + 3.0, r.size.x + 2.0), PI * 0.5, col)
	else:
		nine(ci, r.grow(1.0), tex("fill"), 32.0, Color(col.r * 1.2, col.g * 1.2, col.b * 1.2, col.a))


static func splat(ci: CanvasItem, c: Vector2, s: float, col: Color, ang := 0.0) -> void:
	quad(ci, tex("splat"), c, Vector2(s, s), ang, col)


static func paper(ci: CanvasItem, r: Rect2, a := 1.0) -> void:
	nine(ci, Rect2(r.position + Vector2(3, 4), r.size), tex("paper"), 80.0, Color(0, 0, 0, 0.45 * a))
	nine(ci, r, tex("paper"), 80.0, Color(1, 1, 1, a))


# ================================================================== v40 tasarım sistemi (docs/TASARIM.md "v40: arayüz cilası")
## Renk belirteçleri: parşömen, sumi (gece mürekkebi), kızıl mühür (vermilyon), altın, turkuaz (Kut), kemik (metin), gölge metin
const PARCHMENT := Color(0.90, 0.84, 0.70)
const SUMI := Color(0.045, 0.04, 0.06)
const VERMILION := Color(0.78, 0.16, 0.10)
const GOLD := Color(0.97, 0.80, 0.42)
const TURQUOISE := Color(0.38, 0.86, 0.90)
const BONE := Color(0.95, 0.88, 0.74)
const MUTED := Color(0.72, 0.68, 0.76)
const GOOD := Color(0.58, 0.92, 0.48)
const BAD := Color(1.0, 0.44, 0.38)
## Aralık ızgarası (arayüz birimi, menü 640x360 / HUD 960x540): 4; panel iç boşluğu 8; satır boyları 14 / 22 / 30
const GRID := 4.0
const PAD := 8.0
## Yazı ölçeği (birim): fırça başlık 38 / 25 (sc 3 / 2), Cinzel yazıt 13 / 11 / 9, gövde 10 / 9 / 8

## Oyun kolu simgeleri: son girdi kol ise tuş mühürleri yerine (HUD._input ayarlar). Etiket -> pad.png hücreleri
static var pad_on := false
const PAD_CELLS := ["a", "b", "x", "y", "lb", "rb", "lt", "rt", "yukari", "asagi", "sol", "sag", "ls", "rs", "start", "back"]
const PAD_MAP := {
	"J": ["x"], "K": ["y"], "L": ["b"], "Boşluk": ["a"], "E": ["lb"], "R": ["rb"], "Q": ["ls"], "F": ["rs"],
	"T": ["lt"], "G": ["rt"], "W": ["yukari"], "Esc": ["start"], "A/D": ["sol", "sag"], "W/S": ["yukari", "asagi"],
	"J/K": ["x", "y"], "E/R": ["lb", "rb"], "S": ["asagi"], "S+Boşluk": ["asagi", "a"], "Shift": ["b"], "M / Esc": ["start"],
	"Esc → T": ["start", "lt"], "bekle+J": ["x"],
}


static func pad_glyph(ci: CanvasItem, pos: Vector2, k: String, col: Color, active := true) -> void:
	## Kol simgesi: mürekkep konturlu beyaz düğme (pad.png), etkin değilse soluk; iki simgeli etiketler yan yana
	var cells: Array = PAD_MAP.get(k, [])
	var x := pos.x - 1.0
	for c in cells:
		var i := PAD_CELLS.find(String(c))
		if i < 0:
			continue
		var rg := Rect2(i * ICON_PX, 0, ICON_PX, ICON_PX)
		var r := Rect2(x, pos.y - 2.0, 13.0, 13.0)
		ci.draw_texture_rect_region(tex("pad"), Rect2(r.position + Vector2(0.8, 1.0), r.size), rg, Color(0, 0, 0, 0.5 * col.a))
		var tint := Color(PARCHMENT, col.a) if active else Color(0.5, 0.47, 0.52, 0.8 * col.a)
		ci.draw_texture_rect_region(tex("pad"), r, rg, tint)
		x += 12.0


static func kilim(ci: CanvasItem, r: Rect2, col: Color) -> void:
	## Kilim şeridi: doku boyuna oranla döşenir (son parça kırpılır)
	var t := tex("kilim")
	if t == null or r.size.y <= 0.2:
		return
	var ts := t.get_size()
	var seg := r.size.y * ts.x / ts.y
	var x := r.position.x
	while x < r.end.x - 0.1:
		var w := minf(seg, r.end.x - x)
		ci.draw_texture_rect_region(t, Rect2(x, r.position.y, w, r.size.y), Rect2(0, 0, ts.x * w / seg, ts.y), col)
		x += w


static func orkhon(ci: CanvasItem, r: Rect2, col: Color) -> void:
	## Köktürk harf şeridi (süs): ortadan simetrik kırpılır
	var t := tex("orkhon")
	if t == null or r.size.y <= 0.2:
		return
	var ts := t.get_size()
	var full := r.size.y * ts.x / ts.y
	var w := minf(r.size.x, full)
	var u0 := (ts.x - ts.x * w / full) * 0.5
	ci.draw_texture_rect_region(t, Rect2(r.position.x + (r.size.x - w) * 0.5, r.position.y, w, r.size.y), Rect2(u0, 0, ts.x * w / full, ts.y), col)


static func scroll_frame(ci: CanvasItem, r: Rect2, a := 1.0, d := 6.0) -> void:
	## Parşömen tomar: iki yanda sarılı uçlar (scroll.png 9 dilim; d = doku yoğunluğu, 6 -> 16 birim uç)
	nine(ci, Rect2(r.position + Vector2(2.5, 3.5), r.size), tex("scroll"), 96.0, Color(0, 0, 0, 0.45 * a), d)
	nine(ci, r, tex("scroll"), 96.0, Color(1, 1, 1, a), d)


static func seal_round(ci: CanvasItem, c: Vector2, s: float, col: Color, ang := 0.0) -> void:
	quad(ci, tex("seal_round"), c, Vector2(s, s), ang, col)


static func select_mark(ci: CanvasItem, r: Rect2, col: Color, t: float, a := 1.0) -> void:
	## Seçim imi (v40): satırın solunda nabız atan kızıl yuvarlak mühür (ortasında kâğıt rengi tamga), satırın altında
	## renkli fırça altı çizgisi, arkada hafif renkli yıkama. "→" yazısının yerine.
	var k := 0.5 + 0.5 * sin(t * 5.0)
	var fl := tex("fill")
	nine(ci, r.grow(1.0), fl, 32.0, Color(col.r, col.g, col.b, 0.10 * a))
	var st := tex("stroke")
	ci.draw_texture_rect(st, Rect2(r.position.x + 2.0, r.end.y - 1.8, r.size.x - 4.0, 2.6), false, Color(col, (0.75 + 0.2 * k) * a))
	var c := Vector2(r.position.x - 7.0, r.get_center().y)
	var s := 12.0 + 1.2 * k
	seal_round(ci, c + Vector2(0.8, 1.0), s, Color(0, 0, 0, 0.45 * a), 0.3)
	seal_round(ci, c, s, Color(VERMILION, 0.96 * a), 0.3)
	tamga(ci, 1, c, s * 0.56, Color(PAPER, 0.9 * a))


static func reveal(ci: CanvasItem, vp: Vector2, k: float, col := SUMI) -> void:
	## Fırça perdesi: ekran açılırken (k 0 -> 1) soldan sağa süpürülen geniş mürekkep darbesi; kuyruğu dağınık,
	## perde geçtikçe solar. Menü içeriği bunun arkasında alfa ile belirir (HUD._ease_open).
	if k >= 0.999 or k <= 0.0:
		return
	var t := tex("wipe")
	if t == null:
		return
	var u := clampf(k, 0.0, 1.0)
	var e := 1.0 - pow(1.0 - u, 2.0)
	var w := vp.x * 1.35
	var h := vp.y * 1.5
	var cx := lerpf(-w * 0.55, vp.x + w * 0.6, e)
	quad(ci, t, Vector2(cx, vp.y * 0.5), Vector2(w, h), 0.0, Color(col, (1.0 - u) * 0.9))


static func card_head(ci: CanvasItem, r: Rect2, col: Color, title: String, sub := "") -> float:
	## Kart başlığı (v40 hiyerarşi): renkli yıkama bandı, kilim ince şerit, Cinzel / gövde başlık; alt satır soluk.
	## Dönüş: başlığın bittiği y.
	var bh := 16.0 if sub == "" else 25.0
	var band := Rect2(r.position.x + 2.0, r.position.y + 2.0, r.size.x - 4.0, bh)
	nine(ci, band, tex("fill"), 32.0, Color(col.r, col.g, col.b, 0.16))
	kilim(ci, Rect2(band.position.x + 4.0, band.end.y - 2.2, band.size.x - 8.0, 2.4), Color(col, 0.55))
	text(ci, Vector2(band.position.x + 4.0, band.position.y + 2.0), title, col, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 1)
	if sub != "":
		text(ci, Vector2(band.position.x + 4.0, band.position.y + 12.0), sub, MUTED, 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
	return band.end.y + 3.0


static func delta(v: float, pct := -1000) -> Array:
	## ▲ / ▼ fark yazısı ve rengi: [metin, renk]
	var s := ("▲ +%s" if v >= 0.0 else "▼ %s") % ItemGen.fmt(v)
	if pct > -1000:
		s += (" (+%%%d)" if v >= 0.0 else " (-%%%d)") % absi(pct)
	return [s, GOOD if v >= 0.0 else BAD]


static func stat_tile(ci: CanvasItem, r: Rect2, icon_name: String, value: String, label: String, col: Color, a := 1.0) -> void:
	## İstatistik karosu (ölüm / bölüm sonu): mürekkep yıkaması kutu, solda simge, büyük fırça rakam, altında Cinzel etiket
	nine(ci, Rect2(r.position + Vector2(2.0, 2.5), r.size), tex("fill"), 32.0, Color(0, 0, 0, 0.4 * a))
	nine(ci, r, tex("fill"), 32.0, Color(0.09, 0.075, 0.11, 0.95 * a))
	nine(ci, r.grow(3.0), tex("frame_line"), 48.0, Color(col, 0.5 * a), 4.0)
	icon_at(ci, icon_name, r.position + Vector2(13.0, r.size.y * 0.5), 16.0, Color(col, a))
	var fb := _font("brush")
	draw_str(ci, Vector2(r.position.x + 26.0, r.position.y + r.size.y * 0.5 + 3.0), value, fb, 17, Color(BONE, a), 2, 2)
	var fc := _font("caps")
	draw_str(ci, Vector2(r.position.x + 26.0, r.end.y - 4.0), label, fc, 7, Color(col, 0.9 * a), 1)


static func tooltip(ci: CanvasItem, at: Vector2, lines: Array, w: float, col := GOLD, a := 1.0) -> void:
	## İpucu balonu: kâğıt rengi yazı, koyu yıkama; at = sol üst
	var h := 8.0 + lines.size() * 10.0
	var r := Rect2(at, Vector2(w, h))
	nine(ci, Rect2(r.position + Vector2(2.0, 2.5), r.size), tex("fill"), 32.0, Color(0, 0, 0, 0.45 * a))
	nine(ci, r, tex("fill"), 32.0, Color(0.08, 0.07, 0.1, 0.96 * a))
	ci.draw_texture_rect(tex("stroke"), Rect2(r.position.x + 3.0, r.position.y - 0.6, r.size.x * 0.6, 1.6), false, Color(col, 0.7 * a))
	var y := r.position.y + 4.0
	for l in lines:
		text(ci, Vector2(r.position.x + 6.0, y), String(l), Color(BONE, a), 1, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 0)
		y += 10.0


static func pulse(t: float, hz := 1.0, lo := 0.0, hi := 1.0) -> float:
	return lerpf(lo, hi, 0.5 + 0.5 * sin(t * TAU * hz))
