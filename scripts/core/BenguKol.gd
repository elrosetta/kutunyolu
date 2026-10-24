class_name BenguKol
extends Node2D
## v43 yaşayan kol (Bengü): omuz -> dirsek -> bilek boyunca BÜKÜLEN tek doku şeridi (mesh deform). Eski üç ayrı dönen
## sprite (üst kol / ön kol / yumruk) omuzda ve dirsekte menteşe gibi kırılıyordu ("kukla"); burada kumaş kol tek parça:
## dirsekte yuvarlatılmış (Bezier köşe) bir eğri boyunca satır satır yerleştirilir, kesit eğrinin normaline dik durur.
##
## Doku: tools/artgen/bengu43_ink.render_arm_strip — düz (dinlenme) kol, omuz başı üstte (pivot), dirsek upper_len,
## bilek upper_len + fore_len aşağıda (dünya birimi x texel piksel). Omuz başı pivot merkezli yuvarlak: kol dönerken omuz
## çevresi değişmez (menteşe izi yok). Ön kol gerçek boyuna göre esner (vuruş anındaki "ext" abartısı korunur).
## Malzeme kol parçalarıyla aynı (ink_char + alt_uv: ışığı aynalanmış ikinci satır): kenar ışığı, ay gölgesi, vuruş
## parlaması aynen çalışır. Yön (facing < 0) kesiti kemik ekseninde aynalar.

const SATIR_UST := 3          # omuz başı (pivotun üstü) satırları
const SATIR_KOL := 16         # omuz -> bilek satırları
const SATIR_ALT := 2          # bilek altı
const KOSE_R := 2.4           # dirsek köşe yarıçapı (dünya birimi; büküme göre küçülür)

var tex: Texture2D
var region := Rect2()         # şeridin doku hücresi (piksel)
var pivot := Vector2.ZERO     # omuz, hücre içinde (piksel)
var texel := 4.0              # doku pikseli / dünya birimi
var l1 := 10.0
var l2 := 9.4
var sh := Vector2.ZERO
var el := Vector2(0, 10)
var wr := Vector2(0, 19.4)
var yon := 1

var _uv := PackedVector2Array()
var _idx := PackedInt32Array()
var _pos := PackedVector2Array()
var _col := PackedColorArray()
var _s := PackedFloat32Array()   # satırların dinlenme uzunluk konumu (dünya; omuz 0)
var _o := PackedFloat32Array()   # sütunların enine konumu (dünya; doku +x)


func kur(t: Texture2D, reg: Rect2, piv: Vector2, tx: float, up_len: float, fore_len: float) -> void:
	tex = t
	region = reg
	pivot = piv
	texel = tx
	l1 = up_len
	l2 = fore_len
	_hazirla()


func _hazirla() -> void:
	var top := -pivot.y / texel
	var bot := (region.size.y - pivot.y) / texel
	var L := l1 + l2
	_s.clear()
	for i in SATIR_UST:
		_s.append(lerpf(top, 0.0, float(i) / float(SATIR_UST)))
	for i in SATIR_KOL + 1:
		# dirsek çevresinde sık satır (büküm yumuşak görünsün)
		var u := float(i) / float(SATIR_KOL)
		var s := u * L
		var de := (s - l1) / L
		s = clampf(s - 0.18 * L * de * exp(-de * de * 18.0), 0.0, L)
		_s.append(s)
	for i in range(1, SATIR_ALT + 1):
		_s.append(lerpf(L, bot, float(i) / float(SATIR_ALT)))
	var hw := region.size.x * 0.5 / texel
	_o = PackedFloat32Array([-hw, -hw * 0.45, 0.0, hw * 0.45, hw])
	var tw := float(tex.get_width()) if tex else 1.0
	var th := float(tex.get_height()) if tex else 1.0
	_uv.clear()
	for s in _s:
		for o in _o:
			var px := region.position + pivot + Vector2(o, s) * texel
			_uv.append(Vector2(px.x / tw, px.y / th))
	var nc := _o.size()
	_idx.clear()
	for r in _s.size() - 1:
		for c in nc - 1:
			var a := r * nc + c
			_idx.append_array([a, a + 1, a + nc + 1, a, a + nc + 1, a + nc])
	_pos.resize(_uv.size())
	_col.resize(_uv.size())
	_col.fill(Color.WHITE)


func kemik(a: Vector2, b: Vector2, c: Vector2, facing: int) -> void:
	sh = a
	el = b
	wr = c
	yon = 1 if facing >= 0 else -1
	queue_redraw()


func _egri(s: float, d1: Vector2, d2: Vector2, k1: float, k2: float, r: float) -> Array:
	## Dinlenme uzunluğu s -> [nokta, teğet]. Üst kol k1, ön kol k2 kat esner; dirsekte r yarıçaplı ikinci derece Bezier.
	if s <= l1 - r:
		return [sh + d1 * s * k1, d1]
	if s >= l1 + r:
		return [el + d2 * (s - l1) * k2, d2]
	var p0 := el - d1 * r * k1
	var p2 := el + d2 * r * k2
	var t := (s - (l1 - r)) / (2.0 * r)
	var q := p0.lerp(el, t).lerp(el.lerp(p2, t), t)
	var tg := ((el - p0) * (1.0 - t) + (p2 - el) * t)
	return [q, tg.normalized() if tg.length() > 1e-5 else d1]


func _draw() -> void:
	if tex == null or _uv.is_empty():
		return
	var v1 := el - sh
	var v2 := wr - el
	var n1 := v1.length()
	var n2 := v2.length()
	if n1 < 0.01 or n2 < 0.01:
		return
	var d1 := v1 / n1
	var d2 := v2 / n2
	var k1 := n1 / l1
	var k2 := n2 / l2
	# köşe yarıçapı: büküm arttıkça küçülür (keskin bükümde kesit içe katlanmasın), kemik boyunu aşmaz
	var bend := absf(d1.angle_to(d2))
	var r := clampf(KOSE_R * (1.0 - 0.35 * bend / PI), 0.4, 0.42 * minf(l1, l2))
	var nc := _o.size()
	var i := 0
	for s in _s:
		var ct: Array = _egri(s, d1, d2, k1, k2, r)
		var p: Vector2 = ct[0]
		var tg: Vector2 = ct[1]
		var nrm := Vector2(-tg.y, tg.x)
		for o in _o:
			_pos[i] = p - nrm * (o * float(yon))
			i += 1
	RenderingServer.canvas_item_add_triangle_array(get_canvas_item(), _idx, _pos, _col, _uv, PackedInt32Array(),
		PackedFloat32Array(), tex.get_rid())


func kopya(xf: Transform2D, m: Material) -> BenguKol:
	## Darbe karesi / hayalet için dondurulmuş kopya (aynı kemikler, verilen dönüşüm ve malzeme).
	var k := BenguKol.new()
	k.tex = tex
	k.region = region
	k.pivot = pivot
	k.texel = texel
	k.l1 = l1
	k.l2 = l2
	k._hazirla()
	k.kemik(sh, el, wr, yon)
	k.transform = xf
	k.material = m
	k.texture_filter = texture_filter
	return k
