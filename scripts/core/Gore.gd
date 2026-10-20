class_name Gore
extends Node2D
## v35 vahşet: parçalanma ve kalıcı cesetler.
## Ölen etli yaratığın o anki sprite karesi öldürücü darbe yönünde çizilen kesik çizgileriyle 3-6 dışbükey parçaya
## bölünür (önce gövdeyi ikiye ayıran ana kesik, sonra baş, bacaklar, kollar). Her parça dokusunu taşıyan bir Polygon2D;
## hafif özel fizik (yerçekimi, döşemeye çarpma, sekme, sürtünme, dönüş) bu düğümde toplu işlenir (RigidBody yok).
## Uçarken arkasında kan izi bırakır, duvara çarpınca kan lekesi yapışır; durunca donar (statik çizim, işlem dışı) ve
## altında kan göllenir (Blood lekeleri birleşip büyür). Cesetler bölüm boyunca kalır: en çok MAX_CORPSES öldürüş /
## MAX_PIECES parça, aşılınca en eskiler söner. Taş yaratıklar taş yığını olarak kalır (kan yok, toz); ruh / ateş
## yaratıklarının parçaları mürekkep tülü / kor gibi yükselip söner.

const MAX_PIECES := 200
const MAX_CORPSES := 60
const GRAV := 980.0
const MAT_ET := 0
const MAT_TAS := 1
const MAT_RUH := 2
## taş / tahta gövdeliler: parçalar yığın olarak kalır (Enemy.NOT_FLESH'in alt kümesi; kalanlar ruh / ateş)
const TAS := ["balbal", "bekci", "buz_balbali", "cini_golemi", "agac_iyesi"]

## doku örnek kimliği -> [küçültülmüş Image, ölçek] (opak alan denetimi); boşsa denetim yok (başsız kip, sıkıştırma)
static var _masks: Dictionary = {}

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


static func _cut_all(body: Rect2, ld: Vector2, n: int) -> Array:
	## Kesik sırası: (1) ana kesik darbe yönünde (±20°) gövdenin ortasından; (2) üst parçadan baş (yataya yakın);
	## (3) alt parçayı bacaklara ayıran dik kesik; (4+) en büyük parçadan kol / omuz (darbe yönü ±70°)
	var polys: Array = [PackedVector2Array([body.position, Vector2(body.end.x, body.position.y), body.end, Vector2(body.position.x, body.end.y)])]
	var hor := Vector2(signf(ld.x) if absf(ld.x) > 0.01 else 1.0, 0.0)
	for k in n - 1:
		var idx := 0
		var pt := Vector2.ZERO
		var dd := Vector2.ZERO
		if k == 0:
			var c0 := body.get_center() + Vector2(randf_range(-0.12, 0.12), randf_range(-0.05, 0.12)) * body.size
			pt = c0
			dd = ld.rotated(randf_range(-0.35, 0.35))
			if absf(dd.y) > 0.8:
				dd = hor.rotated(randf_range(-0.4, 0.4))
		elif k == 1:
			var best := INF
			for i in polys.size():
				var cy := _centroid(polys[i]).y
				if cy < best:
					best = cy
					idx = i
			var bb := _bbox(polys[idx])
			pt = Vector2(bb.get_center().x, bb.position.y + bb.size.y * randf_range(0.38, 0.5))
			dd = hor.rotated(randf_range(-0.3, 0.3))
		elif k == 2:
			var best2 := -INF
			for i in polys.size():
				var cy2 := _centroid(polys[i]).y
				if cy2 > best2:
					best2 = cy2
					idx = i
			pt = _centroid(polys[idx]) + Vector2(randf_range(-2, 2), 0)
			dd = Vector2(0, 1).rotated(randf_range(-0.3, 0.3))
		else:
			var ba := -1.0
			for i in polys.size():
				var ar := _area(polys[i])
				if ar > ba:
					ba = ar
					idx = i
			pt = _centroid(polys[idx])
			dd = ld.rotated(randf_range(-1.2, 1.2))
		var halves := _split(polys[idx], pt, dd)
		if (halves[0] as PackedVector2Array).size() >= 3 and (halves[1] as PackedVector2Array).size() >= 3:
			polys.remove_at(idx)
			polys.append(halves[0])
			polys.append(halves[1])
	return polys


static func _bbox(poly: PackedVector2Array) -> Rect2:
	var r := Rect2(poly[0], Vector2.ZERO)
	for v in poly:
		r = r.expand(v)
	return r


# ------------------------------------------------------------------ parçalama
static func dismember(src: Sprite2D, dir: Vector2, power: float, n: int, col: Color, mat := MAT_ET, boss := false) -> int:
	## src: ölen yaratığın sprite'ı (o anki kare); dir: öldürücü darbenin yönü; power 0,8..3 (aşırı hasar, ağır, kritik);
	## n: parça sayısı (3-6). Dönen değer: oluşan parça sayısı (0: yapılamadı → eski ceset yolu)
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
	var wd := dir.normalized() if dir.length() > 0.01 else Vector2(1, -0.3).normalized()
	var ld := gt.affine_inverse().basis_xform(wd)
	ld = ld.normalized() if ld.length() > 0.001 else Vector2.RIGHT
	var polys := _cut_all(body, ld, clampi(n, 2, 7))
	var mod := src.modulate * src.self_modulate
	var wc := gt * body.get_center()
	var made: Array = []
	var areas: Array = []
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
		var wpts := PackedVector2Array()
		var uvs := PackedVector2Array()
		var hw := 0.0
		for v in pl:
			var wv := gt.basis_xform(v - c)
			wpts.append(wv)
			uvs.append(uvf.call(v))
			hw = maxf(hw, wv.length())
		p.polygon = wpts
		p.uv = uvs
		p.texture = tex
		p.texture_filter = src.texture_filter
		p.modulate = mod if mat != MAT_ET else mod * Color(0.92, 0.8, 0.8)
		p.position = gt * c
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
			p.v = p.v.limit_length(950.0 if boss else 820.0)
			p.w = (randf_range(-1.0, 1.0) * 7.0 + signf(wd.x) * 5.0) * minf(pw, 2.0) * (0.4 if p.torso else 1.0)
		g.add_child(p)
		g._act.append(p)
	if mat != MAT_RUH:
		g._kills.append(made)
		g.n_pieces += made.size()
		g.n_kills_total += 1
		g.n_pieces_total += made.size()
		g._enforce_caps()
	return made.size()


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
	## dönmüş parçanın merkezine göre dünya sınır kutusu
	var xf := Transform2D(p.rotation, Vector2.ZERO)
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
						Blood.splat(Vector2(wx, wy), p.col, 4 + int(absf(p.v.x) / 120.0), true)
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
			p.rotation += p.w * delta
			# uçan etli parça kan izi bırakır
			if p.mat == MAT_ET and not p.grounded:
				p.trail += delta
				if p.trail > 0.03 and p.v.length() > 70.0:
					p.trail = 0.0
					if b == null:
						b = Blood.sys()
					if b:
						b._add(p.position + Vector2(randf_range(-2, 2), randf_range(-2, 2)), p.v * 0.12 + Vector2(randf_range(-20, 20), 0), Blood._tone(p.col, randf()), 1.4, 1.0 if randf() < 0.6 else 2.0)
		else:
			p.v.x = move_toward(p.v.x, 0.0, 760.0 * delta)
			p.position.x += p.v.x * delta
			var under := _cell(Vector2(p.position.x, p.position.y + e.end.y + 2.0))
			if not (under == 1 or under == 4 or under == 2):
				p.grounded = false
			elif absf(p.v.x) < 6.0:
				_rest(p, e)
				_act.remove_at(i)
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
				b.stains.add(Vector2(q.position.x + randf_range(ex.position.x, ex.end.x) * 0.7, gy + Blood.PX * 0.5), Blood._tone(q.col, randf() * 0.5), randi_range(2, 4 if q.torso else 3), true)
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
			b.stains.add(Vector2(p.position.x, top + Blood.PX * 0.5), p.col, clampi(int(p.v.y / 110.0) + 2, 2, 6), true)
		if p.v.y > 120.0:
			Ses.play("vahset_dusme", -9.0 if not p.torso else -5.0, 1.0 if not p.torso else 0.85, 0.12, 0.05, p.position)
	elif p.v.y > 140.0:
		FX.dust(Vector2(p.position.x, top), Vector2.UP, 3, 0.25)
		Ses.play("darbe_tas", -14.0, 1.2, 0.1, 0.06, p.position)
	if fast:
		p.bounces += 1
		p.v = Vector2(p.v.x * 0.55, -p.v.y * (0.22 if not p.torso else 0.12))
		p.w *= 0.45
	else:
		p.v.y = 0.0
		p.w = 0.0
		p.grounded = true


func _rest(p: Parca, e: Rect2) -> void:
	## donar: bundan sonra yalnızca statik çizim; etliyse altında kan göllenmeye başlar
	p.v = Vector2.ZERO
	p.w = 0.0
	if p.mat == MAT_ET:
		p.bleed = randf_range(2.5, 4.0) if p.torso else randf_range(0.8, 1.8)
		p.bleed_t = 0.0
		_bleed.append(p)
		# yere yapışmış etin rengi koyulaşır (kurumuş kan)
		var tw := p.create_tween()
		tw.tween_property(p, "modulate", p.modulate * Color(0.82, 0.68, 0.68), 6.0)
