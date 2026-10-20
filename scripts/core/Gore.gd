class_name Gore
extends Node2D
## v35 vahşet: parçalanma ve kalıcı cesetler.
## Ölen etli yaratığın o anki sprite karesi öldürücü darbe yönündeki ana yırtıkla ve rastgele yerlerden atılan
## yırtıklarla 4-8 parçaya bölünür. v35 birleştirme: yırtık çizgileri düz değil, gürültüyle kırık / lifli (sivri lif
## uçları); her parça dokusunu taşıyan bir Polygon2D, kendi üçgenlemesiyle (dış halka + iç halka + merkez) ve köşe
## verisiyle (r: yırtık kenarına yakınlık, b: et / taş) çizilir. PARCA_SHADER bunu hacimli et olarak boyar: kesit
## (koyu kızıl kenar → çiğ kırmızı et → pembe yağ), yırtığa yakın gölge, ekranın üstüne bakan kenarda cel ışık + ıslak
## parlama, altta cel gölge bantları, ince kenar ışığı. Arkada koyu "yan yüz" kopyası (kalınlık), yerde gölge. Ağır /
## kritik öldürüşte ek et topakları, bağırsak / sinir şeritleri ve kemik kırıkları saçılır. Fizik bu düğümde toplu
## (yerçekimi, döşeme / tek yönlü platform, duvar, tavan, sekme, yuvarlanma, inişte ezilip titreme); RigidBody yok.
## Uçarken kan izi bırakır, duvara çarpınca kan lekesi yapışır; durunca donar (statik çizim, işlem dışı) ve altında kan
## göllenir. Cesetler bölüm boyunca kalır: en çok MAX_CORPSES öldürüş / MAX_PIECES parça, aşılınca en eskiler söner.
## Taş yaratıklar taş yığını olarak kalır (kan yok, toz); ruh / ateş yaratıklarının parçaları tül / kor gibi söner.

const MAX_PIECES := 280
const MAX_CORPSES := 60
const GRAV := 980.0
const MAT_ET := 0
const MAT_TAS := 1
const MAT_RUH := 2
## taş / tahta gövdeliler: parçalar yığın olarak kalır (Enemy.NOT_FLESH'in alt kümesi; kalanlar ruh / ateş)
const TAS := ["balbal", "bekci", "buz_balbali", "cini_golemi", "agac_iyesi"]
const YAN := Vector2(0.8, 2.6)   # yan yüz (kalınlık) kayması, dünya px (ekranda aşağı-sağ)

## doku örnek kimliği -> [küçültülmüş Image, ölçek] (opak alan denetimi); boşsa denetim yok (başsız kip, sıkıştırma)
static var _masks: Dictionary = {}
## son _cut_all'ın yırtık doğruları [nokta, yön, tohum]
static var _cuts: Array = []

## Parça gölgelendiricisi. px: bir dünya pikseli kaç doku pikseli (yaratığın ölçeğine göre ayrı malzeme).
## Ekranın "yukarısı" doku uzayında -dFdy(UV) yönü: parça dönse de ışık hep yukarıdan gelir.
const PARCA_SHADER := """
shader_type canvas_item;
uniform float telafi = 1.0;
uniform float px = 1.0;
varying vec4 vc;
void vertex() {
	vc = COLOR;
}
float h2(vec2 p) {
	return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
}
void fragment() {
	vec4 t = texture(TEXTURE, UV);
	vec2 tp = TEXTURE_PIXEL_SIZE * px;            // bir dünya pikseli (UV)
	vec2 up = normalize(-dFdy(UV) / TEXTURE_PIXEL_SIZE + vec2(0.0, 1e-6)) * tp;
	// kenar ışığı (dış hat, ~1,2 ekran px)
	vec2 d = fwidth(UV) * 1.2;
	float m = max(max(texture(TEXTURE, UV + vec2(d.x, 0.0)).a, texture(TEXTURE, UV - vec2(d.x, 0.0)).a), max(texture(TEXTURE, UV + vec2(0.0, d.y)).a, texture(TEXTURE, UV - vec2(0.0, d.y)).a));
	float o = clamp(m - t.a, 0.0, 1.0) * 0.32;
	// hacim: üst kenar ışık, alt kenar gölge (cel bantları), kenarlara yakın ortam gölgesi
	float u1 = texture(TEXTURE, UV + up * 1.5).a;
	float u3 = texture(TEXTURE, UV + up * 3.5).a;
	float d2 = texture(TEXTURE, UV - up * 2.0).a;
	float d5 = texture(TEXTURE, UV - up * 5.0).a;
	float occ = (u3 + d5) * 0.5;
	float S = 1.0;
	if (d5 < 0.5) { S = 0.74; }
	if (d2 < 0.5) { S = 0.52; }
	if (u3 < 0.5) { S = 1.14; }
	if (occ < 0.62) { S *= 0.84; }
	float ust = step(0.5, u1) * step(u3, 0.5);   // üst kenardan 1,5-3,5 px içeride: ıslak parlak bant
	// yırtık kesiti
	vec2 cell = floor(UV / (TEXTURE_PIXEL_SIZE * px * 1.6));
	float cn = vc.r + (h2(cell) - 0.5) * 0.16;
	vec3 col = t.rgb * S;
	if (vc.b > 0.5) {
		vec3 et = vec3(0.6, 0.05, 0.06) * (0.8 + 0.4 * h2(cell + 7.0));
		if (cn > 0.86) {
			col = vec3(0.2, 0.01, 0.02) * telafi;
		} else if (cn > 0.55) {
			col = et * telafi * (S < 0.6 ? 0.55 : (S < 0.8 ? 0.75 : (S > 1.1 ? 1.3 : 1.0)));
			col = mix(col, vec3(1.0, 0.8, 0.78) * telafi, ust * 0.55);
		} else if (cn > 0.47) {
			col = vec3(0.86, 0.6, 0.5) * telafi * (S < 0.8 ? 0.65 : 0.9);
		} else {
			if (cn > 0.3) { col *= 0.6; }
			// üstten cel ışık: koyu derili parça da hacimli okunur (üst kenar bandı açık, ıslak)
			col += vec3(0.2, 0.17, 0.17) * telafi * step(u3, 0.5) * step(0.5, t.a);
		}
	} else {
		if (cn > 0.9) {
			col = t.rgb * 0.35;
		} else if (cn > 0.55) {
			col = (t.rgb * 0.5 + vec3(0.32, 0.31, 0.3)) * S;
		} else if (cn > 0.3) {
			col *= 0.7;
		}
	}
	float a = t.a + o * (1.0 - t.a);
	vec3 rgb = (col * t.a + vec3(0.62, 0.56, 0.54) * telafi * o * (1.0 - t.a)) / max(a, 0.001);
	COLOR = vec4(rgb, a * vc.a);
}
"""
## yan yüz (kalınlık): parçanın koyu et / taş renginde kopyası, arkada, biraz aşağıda
const YAN_SHADER := """
shader_type canvas_item;
uniform float telafi = 1.0;
varying vec4 vc;
void vertex() {
	vc = COLOR;
}
void fragment() {
	float a = texture(TEXTURE, UV).a;
	vec3 c = vc.b > 0.5 ? vec3(0.34, 0.03, 0.04) * telafi : vec3(0.1, 0.1, 0.11);
	COLOR = vec4(c, smoothstep(0.35, 0.6, a) * vc.a);
}
"""
## düz renk (köşe rengi × telafi), dokunun opak yerinde: kemik iliği, kemik kırığı, bağırsak
const ET_SHADER := """
shader_type canvas_item;
uniform float telafi = 1.0;
varying vec4 vc;
void vertex() {
	vc = COLOR;
}
void fragment() {
	float a = texture(TEXTURE, UV).a;
	COLOR = vec4(vc.rgb * telafi, vc.a * smoothstep(0.3, 0.65, a));
}
"""
## et topağı: birim daire yerel koordinatında küre gibi cel ışık + ıslak parıltı + mürekkep kontur (dönmez)
const GIB_SHADER := """
shader_type canvas_item;
uniform float telafi = 1.0;
varying vec2 lp;
varying vec4 vc;
void vertex() {
	lp = VERTEX;
	vc = COLOR;
}
void fragment() {
	float r = length(lp);
	vec3 n = normalize(vec3(lp, sqrt(max(0.05, 1.0 - min(r * r, 0.95)))));
	float l = dot(n, normalize(vec3(-0.35, -0.8, 0.55)));
	vec3 col = vc.rgb * (l > 0.55 ? 1.12 : (l > 0.1 ? 0.78 : 0.48));
	if (l > 0.9) { col = mix(col, vec3(1.0, 0.88, 0.86), 0.75); }
	if (r > 0.9) { col = vec3(0.14, 0.01, 0.02); }
	COLOR = vec4(col * telafi, vc.a);
}
"""
static var _mat_parca: Dictionary = {}   # px (yuvarlanmış) -> ShaderMaterial
static var _mat_yan: ShaderMaterial
static var _mat_et: ShaderMaterial
static var _mat_gib: ShaderMaterial
static var _telafi := 1.0

var level: Node
var _act: Array = []     # hareketli parçalar
var _bleed: Array = []   # duran, altında kanı göllenen parçalar
var _kills: Array = []   # öldürüş başına parça dizisi (en eski önce)
var n_pieces := 0
var n_kills_total := 0
var n_pieces_total := 0


class Parca:
	extends Polygon2D
	var v := Vector2.ZERO
	var w := 0.0
	var mat := 0
	var col := Color(0.55, 0.04, 0.06)
	var grounded := false
	var bounces := 0
	var trail := 0.0
	var bleed := 0.0
	var bleed_t := 0.0
	var life := 0.0
	var age := 0.0
	var torso := false
	var hw := 4.0
	var gib := false        # et topağı / şerit / kemik kırığı
	var no_rot := false     # topak: dönmez (ışığı yerel uzayda)
	var base_scale := Vector2.ONE
	var ground_top := 0.0
	var rest_rot := 0.0
	var yan: Node2D = null


static func _sh(code: String) -> ShaderMaterial:
	var sh := Shader.new()
	sh.code = code
	var m := ShaderMaterial.new()
	m.shader = sh
	return m


static func _mats(lv: Node) -> void:
	if _mat_yan == null:
		_mat_yan = _sh(YAN_SHADER)
		_mat_et = _sh(ET_SHADER)
		_mat_gib = _sh(GIB_SHADER)
	_telafi = Blood.telafi_of(lv)
	for m in [_mat_yan, _mat_et, _mat_gib]:
		(m as ShaderMaterial).set_shader_parameter("telafi", _telafi)
	for k in _mat_parca:
		(_mat_parca[k] as ShaderMaterial).set_shader_parameter("telafi", _telafi)


static func _parca_mat(px: float) -> ShaderMaterial:
	var k := snappedf(px, 0.25)
	if not _mat_parca.has(k):
		var m := _sh(PARCA_SHADER)
		m.set_shader_parameter("px", k)
		m.set_shader_parameter("telafi", _telafi)
		_mat_parca[k] = m
	return _mat_parca[k]


static func sys() -> Gore:
	var lv: Node = FX.level
	if lv == null or not is_instance_valid(lv):
		return null
	if lv.has_meta("gore"):
		var g: Variant = lv.get_meta("gore")
		if is_instance_valid(g):
			return g
	var g2 := Gore.new()
	g2.level = lv
	g2.z_index = 3
	_mats(lv)
	lv.add_child(g2)
	lv.set_meta("gore", g2)
	return g2


static func stats() -> Dictionary:
	var g := sys()
	if g == null:
		return {}
	return {"parca": g.n_pieces, "hareketli": g._act.size(), "kanayan": g._bleed.size(), "ceset": g._kills.size(),
		"toplam_oldurus": g.n_kills_total, "toplam_parca": g.n_pieces_total}


static func material_of(sprite_kind: String, kind: String, flesh: bool) -> int:
	if flesh:
		return MAT_ET
	if sprite_kind in TAS or kind in TAS:
		return MAT_TAS
	return MAT_RUH


# ------------------------------------------------------------------ opak alan maskesi
static func warm(sa: Node) -> void:
	## Yaratık kurulurken dokularının maskesini önceden hazırla (ilk öldürüşte takılma olmasın)
	if sa == null or not ("meta" in sa) or DisplayServer.get_name() == "headless":
		return
	var m: Dictionary = sa.meta
	if m.has("page_texs"):
		for t in m["page_texs"]:
			_mask(t)
	elif m.has("tex"):
		_mask(m["tex"])


static func _mask(tex: Texture2D) -> Array:
	if tex == null:
		return []
	var id := tex.get_instance_id()
	if _masks.has(id):
		return _masks[id]
	var res: Array = []
	if DisplayServer.get_name() != "headless":
		var img := tex.get_image()
		if img and not img.is_empty():
			if img.is_compressed():
				img.decompress()
			if not img.is_compressed():
				var s := 4 if maxi(img.get_width(), img.get_height()) > 512 else 2
				img.resize(maxi(1, img.get_width() / s), maxi(1, img.get_height() / s), Image.INTERPOLATE_BILINEAR)
				res = [img, 1.0 / float(s)]
	_masks[id] = res
	return res


static func _alpha(m: Array, uv: Vector2) -> float:
	var img: Image = m[0]
	var q := (uv * float(m[1])).floor()
	if q.x < 0 or q.y < 0 or q.x >= img.get_width() or q.y >= img.get_height():
		return 0.0
	return img.get_pixel(int(q.x), int(q.y)).a


# ------------------------------------------------------------------ kesme
static func _split(poly: PackedVector2Array, p: Vector2, d: Vector2) -> Array:
	## Dışbükey çokgeni (p, d) doğrusuyla ikiye böl
	var nrm := d.orthogonal()
	var a := PackedVector2Array()
	var b := PackedVector2Array()
	var n := poly.size()
	for i in n:
		var c := poly[i]
		var e := poly[(i + 1) % n]
		var sc := (c - p).dot(nrm)
		var se := (e - p).dot(nrm)
		if sc >= 0.0:
			a.append(c)
		else:
			b.append(c)
		if (sc >= 0.0) != (se >= 0.0):
			var t := sc / (sc - se)
			var x := c.lerp(e, t)
			a.append(x)
			b.append(x)
	return [a, b]


static func _area(poly: PackedVector2Array) -> float:
	var s := 0.0
	for i in poly.size():
		var a := poly[i]
		var b := poly[(i + 1) % poly.size()]
		s += a.x * b.y - b.x * a.y
	return absf(s) * 0.5


static func _centroid(poly: PackedVector2Array) -> Vector2:
	var c := Vector2.ZERO
	for v in poly:
		c += v
	return c / float(maxi(1, poly.size()))


static func _cut_all(body: Rect2, ld: Vector2, n: int, exact := false) -> Array:
	## v35 birleştirme: yırtık sırası rastgele. (1) ana yırtık darbe yönünde (±30°; bitirişte KesikFX açısında) gövdenin
	## ortasına yakın bir yerden; (2+) çoğunlukla en büyük parçadan, bazen rastgele bir orta boy parçadan, parçanın
	## içinde rastgele noktadan, her açıda. Hep baş / bacak / kol değil: her öldürüşte başka yerden kopar.
	var polys: Array = [PackedVector2Array([body.position, Vector2(body.end.x, body.position.y), body.end, Vector2(body.position.x, body.end.y)])]
	var hor := Vector2(signf(ld.x) if absf(ld.x) > 0.01 else 1.0, 0.0)
	var amin := body.size.x * body.size.y * 0.1
	_cuts = []
	for k in n - 1:
		var idx := 0
		var pt := Vector2.ZERO
		var dd := Vector2.ZERO
		if k == 0:
			pt = body.get_center() + Vector2(randf_range(-0.2, 0.2), randf_range(-0.15, 0.15)) * body.size
			dd = ld.rotated(randf_range(-0.5, 0.5))
			if exact:
				pt = body.get_center() + Vector2(randf_range(-0.04, 0.04), randf_range(-0.04, 0.04)) * body.size
				dd = ld.rotated(randf_range(-0.06, 0.06))
			elif absf(dd.y) > 0.85:
				dd = hor.rotated(randf_range(-0.6, 0.6))
		else:
			var ba := -1.0
			for i in polys.size():
				var ar := _area(polys[i])
				if ar > ba:
					ba = ar
					idx = i
			if randf() < 0.4:
				var cand: Array = []
				for i in polys.size():
					if _area(polys[i]) > amin:
						cand.append(i)
				if not cand.is_empty():
					idx = cand[randi() % cand.size()]
			var bb := _bbox(polys[idx])
			pt = _centroid(polys[idx]) + Vector2(randf_range(-0.25, 0.25), randf_range(-0.25, 0.25)) * bb.size
			dd = Vector2.from_angle(randf() * PI)
		var halves := _split(polys[idx], pt, dd)
		if (halves[0] as PackedVector2Array).size() >= 3 and (halves[1] as PackedVector2Array).size() >= 3:
			polys.remove_at(idx)
			polys.append(halves[0])
			polys.append(halves[1])
			_cuts.append([pt, dd.normalized(), randf() * 100.0])
	return polys


static func _bbox(poly: PackedVector2Array) -> Rect2:
	var r := Rect2(poly[0], Vector2.ZERO)
	for v in poly:
		r = r.expand(v)
	return r


static func _cut_idx(a: Vector2, b: Vector2) -> int:
	for i in _cuts.size():
		var c: Array = _cuts[i]
		var p: Vector2 = c[0]
		var nn: Vector2 = (c[1] as Vector2).orthogonal()
		if absf((a - p).dot(nn)) < 0.05 and absf((b - p).dot(nn)) < 0.05:
			return i
	return -1


static func _on_cut(a: Vector2) -> bool:
	for c in _cuts:
		if absf((a - (c[0] as Vector2)).dot((c[1] as Vector2).orthogonal())) < 0.05:
			return true
	return false


static func _tear(s: float, seed: float) -> float:
	## yırtık profili (s: kesik boyunca dünya px): iki dalga + seyrek sivri lif uçları; iki yan aynı işlevi kullanır
	var f := sin(s * 0.85 + seed) * 0.55 + sin(s * 2.3 + seed * 1.7) * 0.3
	var q := floorf(s / 1.7)
	var hh := fposmod(sin(q * 12.9898 + seed * 3.1) * 43758.5453, 1.0)
	if hh > 0.74:
		f += (hh - 0.74) / 0.26 * 2.4 * (1.0 if fposmod(q + floorf(seed), 2.0) < 1.0 else -1.0)
	return f


static func _jag(pl: PackedVector2Array, sc: float) -> Array:
	## Düz kesik kenarlarını gürültüyle kırık, lifli yırtığa çevirir. Dönen: [sınır noktaları, yırtığa yakınlık (0/1)]
	var out := PackedVector2Array()
	var cf := PackedFloat32Array()
	var step := 1.6 / sc
	var amp := 1.5 / sc
	for i in pl.size():
		var a := pl[i]
		var b := pl[(i + 1) % pl.size()]
		out.append(a)
		cf.append(1.0 if _on_cut(a) else 0.0)
		var ci := _cut_idx(a, b)
		if ci < 0:
			continue
		var cut: Array = _cuts[ci]
		var p0: Vector2 = cut[0]
		var d: Vector2 = cut[1]
		var nn := d.orthogonal()
		var m := int(a.distance_to(b) / step)
		for k in range(1, m):
			var q := a.lerp(b, float(k) / float(m))
			var s := (q - p0).dot(d) * sc
			out.append(q + nn * _tear(s, float(cut[2])) * amp)
			cf.append(1.0)
	return [out, cf]


static func _build(p: Polygon2D, b: PackedVector2Array, bc: PackedFloat32Array, c: Vector2, gt: Transform2D, uvf: Callable, sc: float, flesh: bool) -> void:
	## Dış halka (yırtık kenarında r=1) + iç halka (~6 dünya px içeride, r=0) + merkez; kendi üçgenleri
	var n := b.size()
	var band := 3.6 / sc
	var fb := 1.0 if flesh else 0.0
	var pts := PackedVector2Array()
	var uvs := PackedVector2Array()
	var cols := PackedColorArray()
	for i in n:
		pts.append(gt.basis_xform(b[i] - c))
		uvs.append(uvf.call(b[i]))
		cols.append(Color(bc[i], 0.0, fb, 1.0))
	for i in n:
		var to := c - b[i]
		var L := to.length()
		var q := b[i] + (to / maxf(L, 0.001)) * minf(band, L * 0.55)
		pts.append(gt.basis_xform(q - c))
		uvs.append(uvf.call(q))
		cols.append(Color(0.0, 0.0, fb, 1.0))
	pts.append(Vector2.ZERO)
	uvs.append(uvf.call(c))
	cols.append(Color(0.0, 0.0, fb, 1.0))
	var tris: Array = []
	for i in n:
		var j := (i + 1) % n
		tris.append(PackedInt32Array([i, j, n + j]))
		tris.append(PackedInt32Array([i, n + j, n + i]))
		tris.append(PackedInt32Array([2 * n, n + i, n + j]))
	p.polygon = pts
	p.uv = uvs
	p.vertex_colors = cols
	p.internal_vertex_count = n + 1
	p.polygons = tris


static func _ilik(p: Polygon2D, pl: PackedVector2Array, c: Vector2, gt: Transform2D, uvf: Callable, sc: float, tex: Texture2D, filt: int) -> void:
	## Uzuv parçasının en uzun yırtığında kemik: fildişi oval + ortasında koyu kızıl ilik noktası (dokunun opak yerinde)
	var best := -1.0
	var ea := Vector2.ZERO
	var eb := Vector2.ZERO
	for i in pl.size():
		var a := pl[i]
		var b := pl[(i + 1) % pl.size()]
		if _cut_idx(a, b) >= 0 and a.distance_to(b) > best:
			best = a.distance_to(b)
			ea = a
			eb = b
	if best * sc < 5.0:
		return
	var nrm := (eb - ea).orthogonal().normalized()
	if nrm.dot(c - (ea + eb) * 0.5) < 0.0:
		nrm = -nrm
	var m := ea.lerp(eb, randf_range(0.35, 0.65)) + nrm * (2.0 / sc)
	var ax := (eb - ea).normalized()
	for layer in 2:
		var rx := (1.6 if layer == 0 else 0.6) / sc
		var ry := (1.15 if layer == 0 else 0.5) / sc
		var pts := PackedVector2Array()
		var uvs := PackedVector2Array()
		for k in 8:
			var an := TAU * float(k) / 8.0
			var q := m + ax * cos(an) * rx + nrm * sin(an) * ry
			pts.append(gt.basis_xform(q - c))
			uvs.append(uvf.call(q))
		var s := Polygon2D.new()
		s.polygon = pts
		s.uv = uvs
		s.color = Color(0.95, 0.9, 0.8) if layer == 0 else Color(0.42, 0.03, 0.05)
		s.texture = tex
		s.texture_filter = filt
		s.material = _mat_et
		p.add_child(s)


# ------------------------------------------------------------------ parçalama
static func dismember(src: Sprite2D, dir: Vector2, power: float, n: int, col: Color, mat := MAT_ET, boss := false, kesik := Vector2.ZERO) -> int:
	## src: ölen yaratığın sprite'ı (o anki kare); dir: öldürücü darbenin yönü; power 0,8..3 (aşırı hasar, ağır, kritik);
	## n: parça sayısı; kesik: verilirse ilk yırtığın dünya yönü (bitiriş kesiği KesikFX ile aynı açı).
	## Dönen değer: oluşan parça sayısı (0: yapılamadı → eski ceset yolu)
	var g := sys()
	if g == null or src == null or src.texture == null or not src.is_inside_tree():
		return 0
	var tex := src.texture
	var reg := src.region_rect if src.region_enabled else Rect2(Vector2.ZERO, tex.get_size())
	var sz := reg.size
	var rp := (-sz * 0.5 if src.centered else Vector2.ZERO) + src.offset
	var flip := src.flip_h
	var m := _mask(tex)
	var uvf := func(p: Vector2) -> Vector2:
		var u := p.x - rp.x
		if flip:
			u = sz.x - u
		return reg.position + Vector2(u, p.y - rp.y)
	# opak sınır kutusu (kesikler gövdenin içinden geçsin, boş kenar payı parça olmasın)
	var body := Rect2(rp, sz)
	if not m.is_empty():
		var bb := Rect2()
		var found := false
		var step := maxf(2.0, 1.0 / float(m[1]))
		var y := rp.y
		while y < rp.y + sz.y:
			var x := rp.x
			while x < rp.x + sz.x:
				if _alpha(m, uvf.call(Vector2(x, y))) > 0.35:
					if not found:
						bb = Rect2(Vector2(x, y), Vector2.ZERO)
						found = true
					else:
						bb = bb.expand(Vector2(x, y))
				x += step
			y += step
		if not found:
			return 0
		body = bb.grow(step).intersection(Rect2(rp, sz))
	if body.size.x < 4.0 or body.size.y < 4.0:
		return 0
	var gt := src.global_transform
	var sc := maxf(0.05, absf(gt.get_scale().x))
	var wd := dir.normalized() if dir.length() > 0.01 else Vector2(1, -0.3).normalized()
	var exact := kesik.length() > 0.01
	var ld := gt.affine_inverse().basis_xform(kesik.normalized() if exact else wd)
	ld = ld.normalized() if ld.length() > 0.001 else Vector2.RIGHT
	var polys := _cut_all(body, ld, clampi(n, 2, 9), exact)
	var mod := src.modulate * src.self_modulate
	var wc := gt * body.get_center()
	var made: Array = []
	var areas: Array = []
	var pmat := _parca_mat(1.0 / sc)
	for poly in polys:
		var pl: PackedVector2Array = poly
		if pl.size() < 3:
			continue
		var bbp := _bbox(pl)
		if not m.is_empty():
			# kapsama: parçanın içinde yeterince opak doku pikseli var mı (boş köşe parçası atılır)
			var hit := 0
			for sy in 5:
				for sx in 5:
					var q := bbp.position + bbp.size * Vector2((sx + 0.5) / 5.0, (sy + 0.5) / 5.0)
					if Geometry2D.is_point_in_polygon(q, pl) and _alpha(m, uvf.call(q)) > 0.35:
						hit += 1
			if hit < 2:
				continue
		var c := _centroid(pl)
		var p := Parca.new()
		p.texture = tex
		p.texture_filter = src.texture_filter
		if mat == MAT_RUH:
			var wpts := PackedVector2Array()
			var uvs := PackedVector2Array()
			for v in pl:
				wpts.append(gt.basis_xform(v - c))
				uvs.append(uvf.call(v))
			p.polygon = wpts
			p.uv = uvs
			p.modulate = mod
		else:
			var jg := _jag(pl, sc)
			_build(p, jg[0], jg[1], c, gt, uvf, sc, mat == MAT_ET)
			p.material = pmat
			p.modulate = Color(1, 1, 1, mod.a)
			# yan yüz: kalınlık (arkada, aşağıda koyu kopya)
			var yn := Polygon2D.new()
			yn.polygon = p.polygon
			yn.uv = p.uv
			yn.vertex_colors = p.vertex_colors
			yn.internal_vertex_count = p.internal_vertex_count
			yn.polygons = p.polygons
			yn.texture = tex
			yn.texture_filter = src.texture_filter
			yn.material = _mat_yan
			yn.show_behind_parent = true
			yn.position = YAN
			p.add_child(yn)
			p.yan = yn
		var hw := 0.0
		for v in p.polygon:
			hw = maxf(hw, v.length())
		p.position = gt * c
		p.set_meta("pl", pl)
		p.mat = mat
		p.col = col
		p.hw = hw
		made.append(p)
		areas.append(_area(pl))
	if made.is_empty():
		return 0
	# en büyük parça gövde: daha ağır, daha az savrulur, daha çok kanar
	var ti := 0
	for i in areas.size():
		if float(areas[i]) > float(areas[ti]):
			ti = i
	var pw := clampf(power, 0.6, 3.2)
	for i in made.size():
		var p: Parca = made[i]
		p.torso = i == ti
		if mat == MAT_ET and not p.torso and randf() < 0.75:
			# uzuvda kemik / ilik (en uzun yırtıkta)
			var pl3: PackedVector2Array = p.get_meta("pl")
			_ilik(p, pl3, _centroid(pl3), gt, uvf, sc, tex, src.texture_filter)
		p.remove_meta("pl")
		var out := (p.position - wc)
		out = out.normalized() if out.length() > 0.5 else Vector2(randf_range(-1, 1), -1).normalized()
		var k := 0.45 if p.torso else 1.0
		if mat == MAT_RUH:
			p.v = wd * 50.0 * pw + out * 40.0 + Vector2(0, -30.0)
			p.w = randf_range(-2.0, 2.0)
			p.life = randf_range(0.8, 1.3)
		else:
			p.v = (wd * Vector2(1.0, 0.3) * randf_range(120.0, 240.0) + out * randf_range(60.0, 130.0)) * pw * k \
				+ Vector2(0, -randf_range(150.0, 280.0) * minf(pw, 2.2) * (0.7 if p.torso else 1.0))
			p.v.y += wd.y * 160.0 * minf(pw, 2.0) * k   # bitiriş savurması (yukarı darbe) parçalara geçer
			p.v = p.v.limit_length(950.0 if boss else 820.0)
			p.w = (randf_range(-1.0, 1.0) * 7.0 + signf(wd.x) * 5.0) * minf(pw, 2.0) * (0.4 if p.torso else 1.0)
		g.add_child(p)
		g._act.append(p)
	if mat == MAT_ET:
		# ek et topakları, bağırsak / sinir şeritleri, kemik kırıkları
		var big := pw >= 1.6
		var nb := 1 + int(pw * 1.4) + (4 if boss else 0)
		var nr := (randi_range(1, 2) if big else (1 if randf() < 0.45 else 0)) + (2 if boss else 0)
		var nk := (randi_range(1, 3) if big else (1 if randf() < 0.35 else 0)) + (2 if boss else 0)
		made.append_array(g._gibs(wc, wd, pw, col, nb, nr, nk, boss))
	if mat != MAT_RUH:
		g._kills.append(made)
		g.n_pieces += made.size()
		g.n_kills_total += 1
		g.n_pieces_total += made.size()
		g._enforce_caps()
	return made.size()


func _gibs(wc: Vector2, wd: Vector2, pw: float, col: Color, nb: int, nr: int, nk: int, boss: bool) -> Array:
	## Et topakları (yuvarlak / düzensiz, küre cel ışığı), bağırsak / sinir şeritleri (kısa bezier ip), kemik kırıkları
	var res: Array = []
	var meat := Color(minf(1.0, col.r * 0.95 + 0.04), col.g * 0.5 + 0.02, col.b * 0.5 + 0.03)
	for i in nb + nr + nk:
		var p := Parca.new()
		p.gib = true
		p.mat = MAT_ET
		p.col = col
		if i < nb:
			var r := randf_range(1.2, 2.6) * (1.0 + 0.1 * pw) * (1.4 if boss else 1.0)
			var pts := PackedVector2Array()
			var nv := 9
			var sq := randf_range(0.65, 1.0)
			for k in nv:
				var an := TAU * float(k) / float(nv)
				pts.append(Vector2.from_angle(an) * randf_range(0.78, 1.18) * Vector2(1.0, sq))
			p.polygon = pts
			p.color = meat.lerp(Color(0.95, 0.6, 0.55), 0.25 if randf() < 0.3 else 0.0)
			p.material = _mat_gib
			p.base_scale = Vector2(r, r)
			p.scale = p.base_scale
			p.no_rot = true
			p.hw = r * 1.1
		elif i < nb + nr:
			# bağırsak / sinir: görünmez taşıyıcı üçgen + iki katman Line2D (koyu kontur, pembe-kızıl iç)
			p.polygon = PackedVector2Array([Vector2(-1, -1), Vector2(1, -1), Vector2(0, 1)])
			p.color = Color(0, 0, 0, 0)
			var L := randf_range(6.0, 13.0) * (1.4 if boss else 1.0)
			var c1 := Vector2(randf_range(-0.3, 0.3) * L, randf_range(-0.5, 0.5) * L)
			var c2 := Vector2(randf_range(0.6, 1.0) * L, randf_range(-0.4, 0.4) * L)
			var pts2 := PackedVector2Array()
			for k in 9:
				var t := float(k) / 8.0
				var q := Vector2.ZERO.bezier_interpolate(c1, c2 - Vector2(L * 0.2, 0), c2, t)
				pts2.append(q - c2 * 0.5)
			for layer in 2:
				var ln := Line2D.new()
				ln.points = pts2
				ln.width = (2.4 if layer == 0 else 1.3) * (1.3 if boss else 1.0)
				ln.default_color = Color(0.2, 0.02, 0.03) if layer == 0 else Color(0.86, 0.36, 0.4)
				ln.begin_cap_mode = Line2D.LINE_CAP_ROUND
				ln.end_cap_mode = Line2D.LINE_CAP_ROUND
				ln.joint_mode = Line2D.LINE_JOINT_ROUND
				ln.material = _mat_et
				p.add_child(ln)
			p.hw = L * 0.5
		else:
			# kemik kırığı: ince sivri fildişi parça
			var Lb := randf_range(2.5, 4.5)
			p.polygon = PackedVector2Array([Vector2(-Lb, -0.5), Vector2(-Lb * 0.2, -0.8), Vector2(Lb, 0.0), Vector2(Lb * 0.1, 0.9), Vector2(-Lb * 0.8, 0.6)])
			p.color = Color(0.93, 0.88, 0.78)
			p.material = _mat_et
			p.hw = Lb
		p.position = wc + Vector2(randf_range(-6, 6), randf_range(-8, 6))
		var a := wd.angle() + randf_range(-1.2, 1.2) - 0.35 * signf(wd.x)
		p.v = Vector2.from_angle(a) * randf_range(100.0, 260.0) * minf(pw, 2.4) * 0.8 + Vector2(0, -randf_range(140.0, 300.0))
		p.v = p.v.limit_length(780.0)
		p.w = 0.0 if p.no_rot else randf_range(-14.0, 14.0)
		add_child(p)
		_act.append(p)
		res.append(p)
	return res


func _enforce_caps() -> void:
	while _kills.size() > MAX_CORPSES or (n_pieces > MAX_PIECES and _kills.size() > 1):
		var old: Array = _kills.pop_front()
		n_pieces -= old.size()
		for p in old:
			if is_instance_valid(p):
				_act.erase(p)
				_bleed.erase(p)
				var tw: Tween = p.create_tween()
				tw.tween_property(p, "modulate:a", 0.0, 1.2)
				tw.tween_callback(p.queue_free)


# ------------------------------------------------------------------ fizik
func _cell(p: Vector2) -> int:
	var TS: float = level.TS
	return level.cell(int(floorf(p.x / TS)), int(floorf(p.y / TS)))


func _ext(p: Parca) -> Rect2:
	## dönmüş (ölçekli) parçanın merkezine göre dünya sınır kutusu
	var xf := Transform2D(p.rotation, p.scale, 0.0, Vector2.ZERO)
	var r := Rect2(xf.basis_xform(p.polygon[0]), Vector2.ZERO)
	for v in p.polygon:
		r = r.expand(xf.basis_xform(v))
	return r


func _physics_process(delta: float) -> void:
	if level == null or not is_instance_valid(level):
		return
	var TS: float = level.TS
	var b: Blood = null
	var i := _act.size() - 1
	while i >= 0:
		var p: Parca = _act[i]
		if not is_instance_valid(p):
			_act.remove_at(i)
			i -= 1
			continue
		p.age += delta
		if p.mat == MAT_RUH:
			# mürekkep tülü / kor: yükselir, döner, söner
			p.v = p.v * (1.0 - 1.6 * delta) + Vector2(0, -70.0 * delta)
			p.position += p.v * delta
			p.rotation += p.w * delta
			p.modulate.a = clampf(1.0 - p.age / p.life, 0.0, 1.0)
			if Engine.get_physics_frames() % 4 == 0:
				FX.burst(p.position, p.col, 1, 30, 0.5, 0.18, -60, true)
			if p.age >= p.life:
				_act.remove_at(i)
				p.queue_free()
			i -= 1
			continue
		var e := _ext(p)
		if not p.grounded:
			p.v.y += GRAV * delta
			p.v *= 1.0 - 0.3 * delta
			# yatay: duvar
			var nx := p.position.x + p.v.x * delta
			var side := e.end.x if p.v.x > 0.0 else e.position.x
			var wy := p.position.y + e.get_center().y
			var cw := _cell(Vector2(nx + side, wy))
			if cw == 1 or cw == 4:
				if absf(p.v.x) > 140.0 and p.mat == MAT_ET:
					if b == null:
						b = Blood.sys()
					if b:
						var wx := (floorf((nx + side) / TS) * TS) if p.v.x > 0.0 else (floorf((nx + side) / TS) + 1.0) * TS
						Blood.splat(Vector2(wx, wy), p.col, (4 if not p.gib else 2) + int(absf(p.v.x) / 120.0), true)
				p.v.x = -p.v.x * 0.25
				p.w *= 0.5
				nx = p.position.x
			p.position.x = nx
			# dikey: zemin / tavan
			var ny := p.position.y + p.v.y * delta
			if p.v.y > 0.0:
				var foot := Vector2(p.position.x, ny + e.end.y)
				var c := _cell(foot)
				var c0 := _cell(Vector2(p.position.x, p.position.y + e.end.y))
				if c == 1 or c == 4 or (c == 2 and c0 != 2):
					var top := floorf(foot.y / TS) * TS
					ny = top - e.end.y
					_land(p, top, b)
			else:
				var head := Vector2(p.position.x, ny + e.position.y)
				var ch := _cell(head)
				if ch == 1 or ch == 4:
					p.v.y = 0.0
					ny = p.position.y
			p.position.y = ny
			if not p.no_rot:
				p.rotation += p.w * delta
			# uçan etli parça kan izi bırakır
			if p.mat == MAT_ET and not p.grounded:
				p.trail += delta
				if p.trail > (0.03 if not p.gib else 0.06) and p.v.length() > 70.0:
					p.trail = 0.0
					if b == null:
						b = Blood.sys()
					if b:
						b._add(p.position + Vector2(randf_range(-2, 2), randf_range(-2, 2)), p.v * 0.12 + Vector2(randf_range(-20, 20), 0), Blood._tone(p.col, randf()), 1.4, 1.0 if randf() < 0.6 else 2.0)
		else:
			# yerde: dikilip kalmaz, en yakın yatık duruşa devrilip yuvarlanır (hız ~ v / yarıçap), sürtünmeyle durur;
			# alt ucu hep zeminde
			p.v.x = move_toward(p.v.x, 0.0, 760.0 * delta)
			p.position.x += p.v.x * delta
			var settled := true
			if not p.no_rot:
				p.rotation = move_toward(p.rotation, p.rest_rot, (3.0 + absf(p.v.x) / maxf(3.0, p.hw)) * delta)
				settled = absf(p.rotation - p.rest_rot) < 0.01
				p.position.y = p.ground_top - _ext(p).end.y
			var under := _cell(Vector2(p.position.x, p.position.y + e.end.y + 2.0))
			if not (under == 1 or under == 4 or under == 2):
				p.grounded = false
			elif absf(p.v.x) < 6.0 and settled:
				_rest(p, e)
				_act.remove_at(i)
		if p.yan:
			# yan yüz hep ekranda aşağı-sağda kalsın (parça dönse de)
			p.yan.position = YAN.rotated(-p.rotation) / p.scale
		if p.age > 7.0 or p.position.y > float(level.H) * TS + 60.0:
			# takılmış ya da düşmüş: dondur / sil
			_act.erase(p)
			if p.position.y > float(level.H) * TS + 60.0:
				p.queue_free()
		i -= 1
	# göllenme: duran etli parçaların altında kan birikir (lekeler birleşip büyür)
	var j := _bleed.size() - 1
	while j >= 0:
		var q: Parca = _bleed[j]
		if not is_instance_valid(q):
			_bleed.remove_at(j)
			j -= 1
			continue
		q.bleed -= delta
		q.bleed_t -= delta
		if q.bleed_t <= 0.0:
			q.bleed_t = randf_range(0.12, 0.3)
			if b == null:
				b = Blood.sys()
			if b:
				var ex := _ext(q)
				var gy := floorf((q.position.y + ex.end.y + 1.0) / TS) * TS
				b.stains.add(Vector2(q.position.x + randf_range(ex.position.x, ex.end.x) * 0.8, gy + Blood.PX * 0.5), Blood._tone(q.col, randf() * 0.5), randi_range(3, 6 if q.torso else 4), true)
				if randf() < 0.35:
					b._add(q.position + Vector2(randf_range(-3, 3), ex.end.y - 2.0), Vector2(randf_range(-8, 8), 10), Blood._tone(q.col, randf()), 1.0, 1.0)
		if q.bleed <= 0.0:
			_bleed.remove_at(j)
		j -= 1


func _land(p: Parca, top: float, b: Blood) -> void:
	var fast := p.v.y > 170.0 and p.bounces < 2
	if p.mat == MAT_ET:
		if b == null:
			b = Blood.sys()
		if b:
			b.stains.add(Vector2(p.position.x, top + Blood.PX * 0.5), p.col, clampi(int(p.v.y / 110.0) + 2, 2, 6) - (1 if p.gib else 0), true)
		if p.v.y > 120.0 and not p.gib:
			Ses.play("vahset_dusme", -9.0 if not p.torso else -5.0, 1.0 if not p.torso else 0.85, 0.12, 0.05, p.position)
	elif p.v.y > 140.0:
		FX.dust(Vector2(p.position.x, top), Vector2.UP, 3, 0.25)
		Ses.play("darbe_tas", -14.0, 1.2, 0.1, 0.06, p.position)
	if p.v.y > 110.0 and p.mat == MAT_ET:
		# inişte ezilip titrer (yumuşak et)
		var k := clampf(p.v.y / 700.0, 0.06, 0.24)
		p.scale = p.base_scale * Vector2(1.0 + k, 1.0 - k)
		var tw := p.create_tween()
		tw.tween_property(p, "scale", p.base_scale, 0.34).set_trans(Tween.TRANS_ELASTIC).set_ease(Tween.EASE_OUT)
	if fast:
		p.bounces += 1
		p.v = Vector2(p.v.x * 0.55, -p.v.y * (0.22 if not p.torso else 0.12))
		p.w *= 0.45
	else:
		p.v.y = 0.0
		p.w = 0.0
		p.grounded = true
		p.ground_top = top
		# yatık duruş: parçanın uzun ekseni yatay (yerel sınır kutusuna göre), şimdiki açıya en yakın
		var lb := Rect2(p.polygon[0], Vector2.ZERO)
		for v in p.polygon:
			lb = lb.expand(v)
		var flat := 0.0 if lb.size.x >= lb.size.y * 0.8 else PI * 0.5
		p.rest_rot = flat + roundf((p.rotation - flat) / PI) * PI


func _rest(p: Parca, e: Rect2) -> void:
	## donar: bundan sonra yalnızca statik çizim; etliyse altında kan göllenmeye başlar; yerde yumuşak gölge
	p.v = Vector2.ZERO
	p.w = 0.0
	if level == null:
		return
	e = _ext(p)
	var gy := p.ground_top if p.ground_top > 0.0 else floorf((p.position.y + e.end.y + 1.0) / float(level.TS)) * float(level.TS)
	if p.mat != MAT_RUH and e.size.x > 2.0:
		var sh := Polygon2D.new()
		var pts := PackedVector2Array()
		var rx := e.size.x * 0.55
		for k in 12:
			var an := TAU * float(k) / 12.0
			pts.append(Vector2(cos(an) * rx, sin(an) * minf(2.2, rx * 0.35)))
		sh.polygon = pts
		sh.color = Color(0.0, 0.0, 0.0, 0.4)
		sh.top_level = true
		sh.show_behind_parent = true
		sh.position = Vector2(p.position.x + e.get_center().x, gy - 0.6)
		p.add_child(sh)
	if p.mat == MAT_ET:
		# v35 birleştirme: daha uzun ve geniş göllenme (gövde 5-8 sn, uzuv 1,5-3 sn, topak 0,5-1 sn); gövdenin altına iri göl
		p.bleed = randf_range(5.0, 8.0) if p.torso else (randf_range(0.5, 1.0) if p.gib else randf_range(1.5, 3.0))
		p.bleed_t = 0.0
		_bleed.append(p)
		var bl := Blood.sys()
		if bl:
			for k in (3 if p.torso else (0 if p.gib else 1)):
				bl.stains.add(Vector2(p.position.x + randf_range(e.position.x, e.end.x) * 0.6, gy + Blood.PX * 0.5), Blood._tone(p.col, randf() * 0.3), 6 if p.torso else 4, true)
