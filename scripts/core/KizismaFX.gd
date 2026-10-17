extends Node2D
## v20 Kızışma görseli: saldırı hızı yükü (Kızışma pasifi ya da yatağanın ivmesi) arttıkça kolda ve silahta
## yoğunlaşan mürekkep. Yük yokken hiçbir şey çizmez.
##   * savururken: bıçağın son karelerdeki yolunun gerisinde incelen hız çizgileri; yük arttıkça sayısı (1-4),
##     kalınlığı ve koyuluğu artar (bıçağın kendi izinden / InkTrail'den ayrı, onun içinde ince çizgiler)
##   * her an: elden ve önkoldan geriye-yukarı savrulan ince mürekkep tülleri (sıcak hava gibi), yükle sıklaşır
##   * renk kızıl mürekkepten altına kayar; tam yükte kısa altın parıltı (halka + elde altın hale, Player.kz_flash)
## Player._hiz_tick ilk karede ekler; top_level: dünya koordinatında çizer. v1 (piksel) stilde düz çizgi.

const HOT := Color(0.9, 0.3, 0.17)
const GOLD := Color(1.0, 0.82, 0.38)
const COOL := Color(0.78, 0.86, 1.0)   # yatağan ivmesi: çelik rengi

var pl: Node
var amt := 0.0            # 0..1 yumuşatılmış yoğunluk (yük / en çok)
var _kind := "kizisma"
var _hist: Array = []     # son karelerde [el, uç] (dünya)
var _wisps: Array = []    # [konum, hız, ömür, en çok ömür, boy]
var _acc := 0.0
var _t := 0.0
var _hand := Vector2.ZERO
var _rng := RandomNumberGenerator.new()


func _ready() -> void:
	top_level = true
	z_index = -1   # gövdenin arkasında: kolun çevresinde hale gibi, bıçağın kendi izi önde kalır
	global_position = Vector2.ZERO
	InkDraw.prep(self)
	_rng.randomize()


func _process(delta: float) -> void:
	if pl == null or not is_instance_valid(pl):
		queue_free()
		return
	_t += delta
	var y: Array = pl.hiz_yuk()
	var k := 0.0
	if not y.is_empty() and int(y[1]) > 0:
		k = clampf(float(y[0]) / float(y[1]), 0.0, 1.0)
		_kind = String(y[3])
	amt = move_toward(amt, k, delta * (6.0 if k > amt else 2.2))
	var face := int(pl.facing)
	var arm_on: bool = not pl.atk.is_empty() and pl.arm_root != null and pl.arm_root.visible and pl.weapon != null and pl.weapon.visible
	if arm_on:
		var R := float(pl._reach(pl.slot(pl.mel_slot)))
		_hand = pl.arm_root.to_global(pl._hand_local)
		var tip: Vector2 = pl.arm_root.to_global(pl._hand_local + pl._blade_local * R)
		_hist.push_front([_hand, tip])
		if _hist.size() > 5:
			_hist.pop_back()
	else:
		_hist.clear()
		_hand = pl.center() + Vector2(face * 7.0, 3.0)
	# tüller: elden / önkoldan geriye-yukarı savrulur
	if amt > 0.03 and pl.visible:
		_acc += delta * (5.0 + 34.0 * amt)
		while _acc >= 1.0:
			_acc -= 1.0
			var at := _hand + Vector2(_rng.randf_range(-3.0, 3.0), _rng.randf_range(-4.0, 4.0))
			if arm_on and not _hist.is_empty() and _rng.randf() < 0.5:
				at = (_hist[0][0] as Vector2).lerp(_hist[0][1], _rng.randf_range(0.1, 0.6))
			var v := Vector2(-face * _rng.randf_range(12.0, 34.0), _rng.randf_range(-62.0, -30.0))
			var life := _rng.randf_range(0.22, 0.42)
			_wisps.append([at, v, life, life, _rng.randf_range(3.5, 8.0) * (0.7 + 0.5 * amt)])
	else:
		_acc = 0.0
	for i in range(_wisps.size() - 1, -1, -1):
		var w: Array = _wisps[i]
		w[2] = float(w[2]) - delta
		if float(w[2]) <= 0.0:
			_wisps.remove_at(i)
			continue
		w[0] = (w[0] as Vector2) + (w[1] as Vector2) * delta
		w[1] = (w[1] as Vector2) * (1.0 - 2.5 * delta)
	if _wisps.size() > 90:
		_wisps = _wisps.slice(_wisps.size() - 90)
	queue_redraw()


func _col() -> Color:
	var base := COOL if _kind == "ivme" else HOT
	return base.lerp(GOLD, amt * amt * 0.55)


func _draw() -> void:
	var fl := float(pl.kz_flash) if pl != null and is_instance_valid(pl) else 0.0
	if amt <= 0.01 and fl <= 0.0 and _wisps.is_empty():
		return
	var ink := InkDraw.on()
	var col := _col()
	var dark := Color(0.06, 0.03, 0.04)
	# hız çizgileri: bıçak boyunca birkaç noktanın son kareler yolu
	if _hist.size() >= 3 and amt > 0.02:
		var nl := 1 + int(round(amt * 3.0))
		for li in nl:
			var f := 0.55 + 0.45 * (float(li) + 0.5) / float(nl)   # bıçağın uç yarısı
			# kareler arası bıçak açısı kabza çevresinde ara örneklenir: yay kirişi değil, bıçağın gerçek hilali
			var pts := PackedVector2Array()
			for hi in _hist.size():
				var h0: Array = _hist[hi]
				var hd0: Vector2 = h0[0]
				var bd0: Vector2 = (h0[1] as Vector2) - hd0
				if hi == _hist.size() - 1:
					pts.append(hd0 + bd0 * f)
					break
				var h1: Array = _hist[hi + 1]
				var hd1: Vector2 = h1[0]
				var bd1: Vector2 = (h1[1] as Vector2) - hd1
				for s in 4:
					var q := float(s) / 4.0
					var ang := lerp_angle(bd0.angle(), bd1.angle(), q)
					pts.append(hd0.lerp(hd1, q) + Vector2.from_angle(ang) * lerpf(bd0.length(), bd1.length(), q) * f)
			if pts[0].distance_to(pts[pts.size() - 1]) < 5.0:
				continue
			var a := 0.15 + 0.45 * amt
			if ink:
				InkDraw.line(self, pts, 0.9 + 1.2 * amt, 0.15, Color(dark, a * 0.4), Color(dark, 0.0))
				InkDraw.line(self, pts, 0.6 + 0.9 * amt, 0.1, Color(col, a), Color(col, 0.0))
			else:
				draw_polyline(pts, Color(col, a), 1.0)
	# elde hale
	if amt > 0.02 and ink:
		InkDraw.soft(self, _hand, 3.5 + 4.0 * amt, Color(col, 0.1 * amt + 0.03), int(_t * 9.0))
	# tüller
	for w in _wisps:
		var k := float(w[2]) / float(w[3])
		var p: Vector2 = w[0]
		var v: Vector2 = w[1]
		var tail := p - v.normalized() * float(w[4])
		var a2 := (0.25 + 0.55 * amt) * k
		if ink:
			InkDraw.stroke(self, p, tail, 1.0 + 0.8 * amt, Color(col, a2))
		else:
			draw_line(p, tail, Color(col, a2), 1.0)
	# tam yük parıltısı
	if fl > 0.0:
		var r := 10.0 + 18.0 * (1.0 - fl)
		if ink:
			InkDraw.ring(self, pl.center(), r, r * 0.92, Color(GOLD, 0.75 * fl), _t)
			InkDraw.soft(self, _hand, 4.0 + 9.0 * fl, Color(GOLD, 0.55 * fl), 3)
		else:
			draw_arc(pl.center(), r, 0.0, TAU, 24, Color(GOLD, 0.8 * fl), 1.0)
