class_name SilahCizim
extends RefCounted
## v31 profesyonel silah mürekkebi: dokusuz (köşe renkli) fırça şeridi yardımcıları. Uzak silah çizimleri (şimşek,
## Kam Küzgüsü ışını, Tengri Bağı zinciri, fırlatılan silahın dönüş lekesi) bunları kullanır.
##   serit   değişken genişlikli şerit; iki kenarda yarım piksellik saydam pay (kenar yumuşatma: draw_line'ın
##           sabit kalınlığı yerine baskıyla incelip kalınlaşan fırça hattı)
##   kalem   hat kalemi (yassı uçlu fırça) genişlik profili: çizgi yönü uç açısına dik geçerken kalın, paralel
##           geçerken ince (hat sanatının kalın-ince ritmi) + baş basışı + kuyruğa incelme
##   yay     yay noktaları
## Hepsi tek çizim çağrısı (RenderingServer üçgen dizisi); düğümün malzemesi (toplamalı / normal) aynen geçerli.

const FEATHER := 0.55   # kenar yumuşatma payı (dünya birimi; 1080p yakın kamerada ~1 piksel)


static func serit(ci: CanvasItem, pts: PackedVector2Array, ws: PackedFloat32Array, col: Color, col_tail := Color(-1, 0, 0, 0)) -> void:
	## pts boyunca yarı genişlik ws[i] ile şerit; col_tail verilirse renk kuyruğa (son nokta) doğru ona geçer.
	var n := pts.size()
	if n < 2:
		return
	var P := PackedVector2Array()
	var C := PackedColorArray()
	var I := PackedInt32Array()
	var grad := col_tail.r >= 0.0
	for i in n:
		var a := pts[maxi(0, i - 1)]
		var b := pts[mini(n - 1, i + 1)]
		var d := b - a
		if d.length_squared() < 0.000001:
			d = Vector2.RIGHT
		var nr := d.normalized().orthogonal()
		var w := maxf(float(ws[mini(i, ws.size() - 1)]), 0.0)
		var c := col.lerp(col_tail, float(i) / float(n - 1)) if grad else col
		var c0 := Color(c.r, c.g, c.b, 0.0)
		# ince hat (pikselden ince) kapsama oranında solar: titreşen kırık çizgi olmasın
		var cov := clampf(w / FEATHER, 0.0, 1.0)
		var cc := Color(c.r, c.g, c.b, c.a * cov)
		var wi := maxf(w - FEATHER * 0.5, 0.0)
		var wo := w + FEATHER * 0.5
		P.append(pts[i] + nr * wo)
		P.append(pts[i] + nr * wi)
		P.append(pts[i] - nr * wi)
		P.append(pts[i] - nr * wo)
		C.append(c0)
		C.append(cc)
		C.append(cc)
		C.append(c0)
	for i in n - 1:
		var k := i * 4
		for j in 3:
			var a0 := k + j
			I.append_array([a0, a0 + 1, a0 + 4, a0 + 1, a0 + 5, a0 + 4])
	RenderingServer.canvas_item_add_triangle_array(ci.get_canvas_item(), I, P, C)


static func kalem(pts: PackedVector2Array, w: float, nib := 0.7, head := 0.12, tail := 0.35, thin := 0.3) -> PackedFloat32Array:
	## Hat kalemi yarı genişlikleri: yassı uç açısı nib (rad); çizgi uca dik giderken w, paralel giderken w × thin.
	## head: baştaki basış payı (yay uzunluğu oranı, hafif şişkin), tail: kuyruğa incelme payı.
	var n := pts.size()
	var out := PackedFloat32Array()
	out.resize(n)
	if n < 2:
		return out
	var cum := PackedFloat32Array()
	cum.resize(n)
	var tot := 0.0
	for i in range(1, n):
		tot += pts[i].distance_to(pts[i - 1])
		cum[i] = tot
	tot = maxf(tot, 0.001)
	var prev_f := -1.0
	for i in n:
		var d := pts[mini(n - 1, i + 1)] - pts[maxi(0, i - 1)]
		var f := thin + (1.0 - thin) * absf(sin(d.angle() - nib))
		if prev_f >= 0.0:
			f = lerpf(prev_f, f, 0.6)   # köşede yumuşak geçiş (basamaksız)
		prev_f = f
		var t := cum[i] / tot
		var hk := 1.0 + 0.35 * (1.0 - smoothstep(0.0, head, t)) if head > 0.0 else 1.0
		var tk := 1.0 - smoothstep(1.0 - tail, 1.0, t) * 0.92 if tail > 0.0 else 1.0
		var sk := smoothstep(0.0, 0.035, t) * 0.6 + 0.4   # en baş da sivri değil, yuvarlak basış
		out[i] = w * f * hk * tk * sk
	return out


static func yay(c: Vector2, r: Vector2, a0: float, a1: float, n: int) -> PackedVector2Array:
	var out := PackedVector2Array()
	for i in n + 1:
		var a := lerpf(a0, a1, float(i) / float(n))
		out.append(c + Vector2(cos(a) * r.x, sin(a) * r.y))
	return out
