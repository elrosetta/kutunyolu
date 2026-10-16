class_name InkDraw
extends RefCounted
## Stil v2 dünya çizim yardımcıları: v1'in piksel ızgarasına oturan draw_rect / tarama satırı disklerinin
## mürekkep karşılıkları. Hepsi assets/fx/ink_p/ dokularıyla (tools/artgen/ink_parcacik.py) döndürülmüş,
## kenar yumuşatmalı dörtgen çizer; çizen düğümün süzgeci doğrusal + mipmap olmalıdır (prep()).
##   blot    dolu mürekkep lekesi (r = görünen yarıçap)      soft    yumuşak fırça dokunuşu / hale
##   cloud   mürekkep yıkaması bulutu                          ellipse yumuşak elips leke (gölge, hale)
##   ring    açık uçlu fırça halkası (elips olabilir)          stroke  a -> b incelen fırça darbesi
##   line    çoklu nokta incelen şerit fırça (şimşek, zincir)  flake / drop / star / spark: tek parça
## Parçacık dokuları: FX._particles v2'de k_*.png / soft_dot yerine particle() eşlemesini kullanır.

const DIR := "res://assets/fx/ink_p/"
static var _tex: Dictionary = {}

## v1 parçacık dokusu -> [v2 mürekkep karşılığı, raporlanan boyut]. Boyut v1 dokusunun görünen boyuna denk
## seçilir (ImageTexture.set_size_override): parçacıkların scale_amount değerleri v1 ile aynı kalır.
const PARTICLE := {"": ["nokta", Vector2(18, 18)], "soft_dot": ["nokta", Vector2(18, 18)],
	"k_spark": ["kivilcim", Vector2(14, 56)], "k_spark2": ["kivilcim", Vector2(14, 56)], "k_star": ["yildiz", Vector2(64, 64)],
	"k_star2": ["yildiz2", Vector2(60, 60)], "k_smoke": ["duman_0", Vector2(72, 72)], "k_smoke2": ["duman_1", Vector2(72, 72)],
	"k_flame": ["alev", Vector2(34, 68)], "k_flame2": ["alev", Vector2(34, 68)], "k_ring": ["halka", Vector2(60, 60)],
	"k_dirt": ["kul", Vector2(14, 14)], "k_scorch": ["leke_0", Vector2(64, 64)], "k_magic": ["yildiz2", Vector2(64, 64)],
	"k_light": ["nokta", Vector2(64, 64)], "k_flare": ["yildiz", Vector2(64, 64)], "k_muzzle": ["leke_1", Vector2(64, 64)],
	"k_slash": ["cizgi", Vector2(64, 16)], "k_trace": ["cizgi", Vector2(64, 16)], "k_twirl": ["halka", Vector2(64, 64)],
	"damla": ["damla", Vector2(12, 12)], "yaprak": ["yaprak", Vector2(7, 7)], "kul": ["kul", Vector2(10, 10)]}
static var _ptex: Dictionary = {}


static func on() -> bool:
	return Data.stil == "v2"


static func tex(n: String) -> Texture2D:
	if not _tex.has(n):
		_tex[n] = load(DIR + n + ".png") if ResourceLoader.exists(DIR + n + ".png") else null
	return _tex[n]


static func particle(v1_name: String) -> Texture2D:
	if _ptex.has(v1_name):
		return _ptex[v1_name]
	var e: Array = PARTICLE.get(v1_name, PARTICLE["soft_dot"])
	var src := tex(String(e[0]))
	var out: Texture2D = src
	if src != null:
		var img := src.get_image()
		if img != null:
			var it := ImageTexture.create_from_image(img)
			it.set_size_override(Vector2i(e[1]))
			it.resource_name = "ink_p/" + String(e[0])  # piksel denetimi bunu mürekkep dokusu sayar
			out = it
	_ptex[v1_name] = out
	return out


static func prep(ci: CanvasItem) -> void:
	## Mürekkep çizen düğüm: doğrusal süzgeç + mipmap (proje varsayılanı v1 için en yakın komşudur)
	ci.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS


static func quad(ci: CanvasItem, n: String, c: Vector2, size: Vector2, ang: float, col: Color) -> void:
	var t := tex(n)
	if t == null or col.a <= 0.002 or size.x <= 0.01 or size.y <= 0.01:
		return
	var ax := Vector2.from_angle(ang) * size.x * 0.5
	var ay := Vector2.from_angle(ang + PI * 0.5) * size.y * 0.5
	ci.draw_primitive(PackedVector2Array([c - ax - ay, c + ax - ay, c + ax + ay, c - ax + ay]),
		PackedColorArray([col, col, col, col]),
		PackedVector2Array([Vector2(0, 0), Vector2(1, 0), Vector2(1, 1), Vector2(0, 1)]), t)


static func _ang(seed: int) -> float:
	return float(seed) * 2.39996


static func blot(ci: CanvasItem, c: Vector2, r: float, col: Color, seed := 0) -> void:
	## Dolu leke: dokudaki gövde yarıçapı kenarın 0,33'ü
	quad(ci, "leke_%d" % (absi(seed) % 3), c, Vector2(r, r) * 3.0, _ang(seed), col)


static func soft(ci: CanvasItem, c: Vector2, r: float, col: Color, seed := 0) -> void:
	quad(ci, "nokta", c, Vector2(r, r) * 3.2, _ang(seed), col)


static func cloud(ci: CanvasItem, c: Vector2, r: float, col: Color, seed := 0) -> void:
	quad(ci, "duman_%d" % (absi(seed) % 2), c, Vector2(r, r) * 3.0, _ang(seed), col)


static func ellipse(ci: CanvasItem, c: Vector2, rx: float, ry: float, col: Color, n := "nokta") -> void:
	quad(ci, n, c, Vector2(rx, ry) * (3.2 if n == "nokta" else 3.0), 0.0, col)


static func ring(ci: CanvasItem, c: Vector2, rx: float, ry: float, col: Color, ang := 0.0) -> void:
	## Halka dokusunun yarıçapı kenarın 0,41'i
	quad(ci, "halka", c, Vector2(rx, ry) * 2.44, ang, col)


static func stroke(ci: CanvasItem, a: Vector2, b: Vector2, w: float, col: Color) -> void:
	## a (kalın baş) -> b (incelen kuyruk)
	var d := b - a
	var l := d.length()
	if l < 0.3:
		return
	quad(ci, "cizgi", (a + b) * 0.5, Vector2(l * 1.08, w * 1.25), d.angle(), col)


static func line(ci: CanvasItem, pts: PackedVector2Array, w0: float, w1: float, col: Color, col_end := Color(0, 0, 0, -1)) -> void:
	## Çoklu nokta şerit fırça: genişlik w0 -> w1, renk col -> col_end (verilirse)
	var n := pts.size()
	if n < 2:
		return
	var t := tex("serit")
	if t == null:
		return
	var total := 0.0
	for i in range(1, n):
		total += pts[i].distance_to(pts[i - 1])
	if total < 0.3:
		return
	var ce := col if col_end.a < 0.0 else col_end
	var nrm: Array = []
	for i in n:
		var dv := (pts[mini(i + 1, n - 1)] - pts[maxi(i - 1, 0)]).normalized()
		nrm.append(Vector2(-dv.y, dv.x))
	var acc := 0.0
	for i in range(n - 1):
		var k0 := acc / total
		acc += pts[i + 1].distance_to(pts[i])
		var k1 := acc / total
		var h0 := lerpf(w0, w1, k0) * 0.62
		var h1 := lerpf(w0, w1, k1) * 0.62
		var c0 := col.lerp(ce, k0)
		var c1 := col.lerp(ce, k1)
		var n0: Vector2 = nrm[i]
		var n1: Vector2 = nrm[i + 1]
		ci.draw_primitive(PackedVector2Array([pts[i] + n0 * h0, pts[i + 1] + n1 * h1, pts[i + 1] - n1 * h1, pts[i] - n0 * h0]),
			PackedColorArray([c0, c1, c1, c0]),
			PackedVector2Array([Vector2(k0, 0), Vector2(k1, 0), Vector2(k1, 1), Vector2(k0, 1)]), t)


static func flake(ci: CanvasItem, c: Vector2, s: float, ang: float, col: Color) -> void:
	quad(ci, "kul", c, Vector2(s, s * 0.8) * 1.6, ang, col)


static func drop(ci: CanvasItem, c: Vector2, s: float, ang: float, col: Color) -> void:
	## ang: hareket yönü (baş bu yönde)
	quad(ci, "damla", c, Vector2(s, s) * 2.2, ang - PI * 0.5, col)


static func star(ci: CanvasItem, c: Vector2, s: float, ang: float, col: Color, rays7 := false) -> void:
	quad(ci, "yildiz2" if rays7 else "yildiz", c, Vector2(s, s) * 2.1, ang, col)


static func flame(ci: CanvasItem, base: Vector2, w: float, h: float, col: Color, lean := 0.0) -> void:
	## base: alevin dibi; yukarı doğru h boyunda
	quad(ci, "alev", base + Vector2(lean * h * 0.3, -h * 0.45), Vector2(w * 1.6, h * 1.15), lean * 0.3, col)
