class_name BenguKusak
extends Node2D
## v39: Bengü'nün turkuaz kuşak kuyrukları — çalışma zamanında Verlet zinciri (eskiden sprite'a çizili, gövdeyle
## birlikte kaskatı dönüyordu). Kök = sprite karesinin 'kusak' çapası (belin arkasındaki düğüm, tools/artgen/bengu_ink.py).
## Küresel uzayda benzetilir: koşuda geriye akar, sıçrayışta aşağı sarkar, düşüşte havalanır, savuruşta gövde döndükçe
## gecikmeyle savrulur (takip ve örtüşen hareket). SpriteAnim'in çocuğu (ezilme / eğilme / görünürlük gövdeyle aynı);
## gövde malzemesini (ink_char) paylaşır: vuruş parlaması, ay gölgesi, sahne ışıkları aynı.

const DT := 1.0 / 120.0
const G := 760.0
const SURT := 2.2            # hava sürtünmesi (1/sn)
const ITERS := 4
const MAX_STEPS := 8
# zincirler: [nokta sayısı, parça boyu (dünya birimi), kök eni, kök ofseti (yerel, bakışa göre), ton]
const ZINCIR := [[9, 2.1, 2.1, Vector2(-0.4, 0.4), 1.0], [7, 1.9, 1.65, Vector2(0.5, 0.9), 0.78]]
const C_TABAN := Color("22ad9f")
const C_GOLGE := Color("0c4e5e")
const C_ISIK := Color("8eeedc")
const C_MUREKKEP := Color("15161d")
const C_PUSKUL := Color("b3343c")
const C_ALTIN := Color("d6a64c")

var anim: SpriteAnim
var pl: CharacterBody2D
var _p: Array = []      # her zincir: PackedVector2Array konum
var _o: Array = []      # önceki konum
var _acc := 0.0
var _t := 0.0
var _reset := true
var _root := Vector2.ZERO
var _root_v := Vector2.ZERO


static func ekle(sprite: SpriteAnim, owner_body: CharacterBody2D) -> BenguKusak:
	if sprite == null or not Data.is_linear(sprite.meta):
		return null
	var any := false
	for an in sprite.meta["anims"].values():
		var d: Array = an.get("data", [])
		if d.size() > 0 and (d[0] as Dictionary).has("kusak"):
			any = true
			break
	if not any:
		return null
	var k := BenguKusak.new()
	k.name = "Kusak"
	k.anim = sprite
	k.pl = owner_body
	sprite.add_child(k)
	sprite.move_child(k, 0)   # gövdenin (ve saçın arka katmanının) arkasında
	if sprite.mat:
		k.material = sprite.mat
	for z in ZINCIR:
		var a := PackedVector2Array()
		a.resize(int(z[0]))
		k._p.append(a)
		k._o.append(a.duplicate())
	return k


func _kok_yerel() -> Vector2:
	var v: Variant = anim.anchor("kusak")
	if v == null:
		return Vector2(-4.0 * anim.facing, -31.0)
	return v as Vector2


func _process(delta: float) -> void:
	if anim == null or not is_visible_in_tree():
		_reset = true
		return
	var f := float(anim.facing)
	var r := anim.to_global(_kok_yerel())
	if _reset or delta <= 0.0 or r.distance_to(_root) > 48.0:
		_dinlen(r, f)
		_root = r
		_reset = false
		queue_redraw()
		return
	_acc = minf(_acc + delta, DT * MAX_STEPS)
	var r0 := _root
	var n := int(_acc / DT)
	var floor_y := pl.global_position.y if pl and pl.is_on_floor() else INF
	for s in n:
		var k := float(s + 1) / float(n)
		var rk := r0.lerp(r, k)
		_adim(rk, f, floor_y)
	_acc -= n * DT
	_root_v = (r - r0) / maxf(delta, 1e-4)
	_root = r
	_t += delta
	queue_redraw()


func _dinlen(r: Vector2, f: float) -> void:
	for zi in ZINCIR.size():
		var z: Array = ZINCIR[zi]
		var off := Vector2(float(z[3].x) * f, float(z[3].y))
		var dir := Vector2(-f * 0.45, 1.0).normalized()
		var a: PackedVector2Array = _p[zi]
		for i in a.size():
			a[i] = r + off + dir * float(z[1]) * i
		_p[zi] = a
		_o[zi] = a.duplicate()


func _adim(r: Vector2, f: float, floor_y: float) -> void:
	var spd := absf(_root_v.x)
	for zi in ZINCIR.size():
		var z: Array = ZINCIR[zi]
		var seg := float(z[1])
		var off := Vector2(float(z[3].x) * f, float(z[3].y))
		var a: PackedVector2Array = _p[zi]
		var o: PackedVector2Array = _o[zi]
		var m := a.size()
		a[0] = r + off
		o[0] = a[0]
		var drag := exp(-SURT * DT)
		for i in range(1, m):
			var t := float(i) / float(m - 1)
			var v := (a[i] - o[i]) * drag
			var acc := Vector2(0.0, G)
			# çırpınma: hızla büyüyen, uca doğru artan enine salınım (kumaş rüzgârda)
			acc.y += sin(_t * 15.0 + i * 0.9 + zi * 1.7) * minf(spd, 260.0) * 2.2 * t
			acc.x += -f * (18.0 + 10.0 * sin(_t * 1.3 + zi)) * t   # bakışın tersine hafif esinti
			o[i] = a[i]
			a[i] += v + acc * DT * DT
		for it in ITERS:
			for i in range(1, m):
				var d := a[i] - a[i - 1]
				var L := d.length()
				if L > 1e-5:
					var c := d * (1.0 - seg / L)
					if i == 1:
						a[i] -= c
					else:
						a[i - 1] += c * 0.5
						a[i] -= c * 0.5
			# kök yönü: ilk parça aşağı-geri doğrultusuna yayla çekilir (kuşak düğümden sarkar, öne katlanmaz)
			var want := a[0] + Vector2(-f * 0.5, 1.0).normalized() * seg
			a[1] = a[1].lerp(want, 0.18)
			for i in range(1, m):
				# gövdenin önüne geçmesin: kökün önüne (bakış yönünde) taşan nokta geri itilir
				var fwd := (a[i].x - a[0].x) * f
				if fwd > 1.0:
					a[i].x -= f * (fwd - 1.0) * 0.5
				if a[i].y > floor_y - 0.3:
					a[i].y = floor_y - 0.3
					o[i].x = lerpf(o[i].x, a[i].x, 0.3)   # yerde sürtünme
		_p[zi] = a
		_o[zi] = o


func _draw() -> void:
	if _p.is_empty():
		return
	var light := Vector2(-0.74, -0.67)
	for zi in range(ZINCIR.size() - 1, -1, -1):
		var z: Array = ZINCIR[zi]
		var a: PackedVector2Array = _p[zi]
		var m := a.size()
		var q := PackedVector2Array()
		for i in m:
			q.append(to_local(a[i]))
		var w0 := float(z[2])
		var ton := float(z[4])
		var left := PackedVector2Array()
		var right := PackedVector2Array()
		var mid_l := PackedVector2Array()
		for i in m:
			var t := float(i) / float(m - 1)
			var d := (q[mini(i + 1, m - 1)] - q[maxi(i - 1, 0)]).normalized()
			var nrm := Vector2(-d.y, d.x)
			# en: kökte dolgun, ortada hafif kıvrım (kumaş bükülüyor), uca doğru incelir
			var w := w0 * maxf(0.25, (1.0 - 0.55 * t)) * (0.78 + 0.22 * absf(cos(t * 5.0 + _t * 3.0 * 0.0 + zi)))
			left.append(q[i] + nrm * w)
			right.append(q[i] - nrm * w)
			mid_l.append(q[i] - nrm * w * (0.15 if nrm.dot(light) > 0.0 else -0.15))
		var body := left.duplicate()
		var rr := right.duplicate()
		rr.reverse()
		body.append_array(rr)
		var base := C_TABAN.darkened(1.0 - ton) if ton < 1.0 else C_TABAN
		if Geometry2D.triangulate_polygon(body).size() > 0:
			draw_colored_polygon(body, base)
			# gölge bandı: ışığın tersindeki yarı (ikinci cel bandı)
			var sh := PackedVector2Array()
			var lit_left := (left[m / 2] - right[m / 2]).dot(light) > 0.0
			var far := right if lit_left else left
			sh.append_array(far)
			var mm := mid_l.duplicate()
			mm.reverse()
			sh.append_array(mm)
			if Geometry2D.triangulate_polygon(sh).size() > 0:
				draw_colored_polygon(sh, C_GOLGE.darkened(0.15 * (1.0 - ton)))
			# ışık yanı ince parlama
			var near := left if lit_left else right
			var hl := PackedVector2Array()
			for i in range(1, mini(m, 5)):
				hl.append(near[i].lerp(q[i], 0.35))
			if hl.size() > 1:
				draw_polyline(hl, C_ISIK if ton >= 1.0 else C_ISIK.darkened(0.3), 0.32, true)
		# mürekkep konturu
		var ol := body.duplicate()
		ol.append(body[0])
		draw_polyline(ol, C_MUREKKEP, 0.42, true)
		# uç: püskül + altın halka
		var e := q[m - 1]
		var dd := (q[m - 1] - q[m - 2]).normalized()
		for j in 3:
			var tip := e + dd.rotated((j - 1) * 0.35) * 2.6
			draw_line(e, tip, C_MUREKKEP, 0.95, true)
			draw_line(e, tip, C_PUSKUL, 0.55, true)
		draw_circle(e, 0.95, C_MUREKKEP)
		draw_circle(e, 0.68, C_ALTIN)
