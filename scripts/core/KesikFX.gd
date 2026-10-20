class_name KesikFX
extends Node2D
## v35 sanatsal kombo bitirişi: hedefin üstüne atılan hüsnühat "kesik"i (sumi-e fırça darbesi) + mürekkep patlaması.
## Shinobi / Ōkami esinli: başta bastırılmış kalın, kuyrukta kuru kıllara ayrılan tek darbe; 0,06 sn'de çizilir,
## ~0,3 sn kalır, sonra kurur ve söner. Katmanlar: sumi konturu · sınıf vurgusu (kızıl / altın) çekirdek · ilk iki
## karede ak-sıcak kıl inceliğinde hat. Kuyrukta damla sıçrantısı, merkezde ışınsal mürekkep dikenleri.
## Yalnızca zincir bitirişi ve tam şarjlı ağır vuruş (gösteri bitirişin; ara vuruşlar sade kalır).
## Gerçek zamanlı akar (vuruş duraklamasında ve ağır çekimde de çizilir).

const INK := Color(0.05, 0.04, 0.06)
const CIZ := 0.06        # darbenin çizilme süresi (sn)
const KAL := 0.30        # tam görünür kalış
const SON := 0.12        # kuruyup sönüş
const SIVRI := 0.11      # ak-sıcak hattın ömrü (~2 kare + vuruş duraklaması)
const KIL := 13          # kuru fırça kıl şeritleri (kuyrukta ayrılır)

## Sınıf imzası: şekil, darbe eni, boy, vurgu rengi, diken sayısı
const SINIF := {
	"kilic": {"sekil": "capraz", "w": 7.0, "boy": 1.0, "vurgu": Color(0.86, 0.14, 0.09), "diken": 9},
	"duello": {"sekil": "iai", "w": 5.0, "boy": 1.15, "vurgu": Color(0.95, 0.2, 0.16), "diken": 7},
	"hancer": {"sekil": "carpi", "w": 5.0, "boy": 0.8, "vurgu": Color(0.72, 0.04, 0.16), "diken": 8},
	"mizrak": {"sekil": "saplama", "w": 5.5, "boy": 1.25, "vurgu": Color(0.95, 0.6, 0.16), "diken": 6},
	"uzun": {"sekil": "supurme", "w": 7.0, "boy": 1.2, "vurgu": Color(0.88, 0.42, 0.12), "diken": 8},
	"agir": {"sekil": "yarma", "w": 10.0, "boy": 1.05, "vurgu": Color(0.9, 0.3, 0.08), "diken": 12},
	"dev": {"sekil": "yarma", "w": 11.5, "boy": 1.15, "vurgu": Color(0.93, 0.36, 0.08), "diken": 13},
	"kirbac": {"sekil": "kivrim", "w": 4.5, "boy": 1.1, "vurgu": Color(0.9, 0.18, 0.1), "diken": 7},
}

var vurgu := Color(0.86, 0.14, 0.09)
var parlak := false       # parıltı: dikenler vurgu renginde (sumi değil)
var _t := 0.0
var _life := CIZ + KAL + SON
var _strokes: Array = []   # {"a","c","b": Vector2 (bezier), "w", "d": gecikme, "ends": Array (bant sonları), "off": Array}
var _spikes: Array = []    # {"dir","len","w","d"}
var _drops: Array = []     # {"o","v","r","d"}
var _rng := RandomNumberGenerator.new()


static func sinif_of(cls: String) -> Dictionary:
	return SINIF.get(cls, SINIF["kilic"])


static func bitiris(pos: Vector2, facing: int, cls: String, guc := 1.0, renk := Color(0, 0, 0, 0)) -> KesikFX:
	## Zincir bitirişinin kesiği: pos hedefin merkezi, facing vuruş yönü, cls Player._tempo_class
	if FX.root == null or Game.fx_scale <= 0.0:
		return null
	var s := sinif_of(cls)
	var f := KesikFX.new()
	f._rng.randomize()
	f.position = pos
	f.z_index = 58
	f.vurgu = s["vurgu"] if renk.a <= 0.0 else (s["vurgu"] as Color).lerp(renk, 0.35)
	var fx := float(facing if facing != 0 else 1)
	var L := 38.0 * float(s["boy"]) * (0.9 + 0.2 * guc)
	var w := float(s["w"]) * (1.0 + 0.3 * guc)
	match String(s["sekil"]):
		"capraz":   # baş üstünden çapraz iniş: hafif hilal
			f._stroke(Vector2(-0.8 * fx, -0.75) * L, Vector2(1.0 * fx, 0.55) * L, -0.22 * L, w, 0.0)
		"iai":      # kınından tek yatay çekiş: uzun ince, neredeyse düz
			f._stroke(Vector2(-1.1 * fx, -0.12) * L, Vector2(1.25 * fx, 0.05) * L, -0.06 * L, w, 0.0)
		"carpi":    # hançer: iki kesişen hızlı darbe (X)
			f._stroke(Vector2(-0.75 * fx, -0.7) * L, Vector2(0.85 * fx, 0.6) * L, -0.12 * L, w, 0.0)
			f._stroke(Vector2(-0.75 * fx, 0.65) * L, Vector2(0.85 * fx, -0.7) * L, 0.12 * L, w * 0.85, 0.045)
		"saplama":  # mızrak: uzun düz deliş + iki ince hız teli
			f._stroke(Vector2(-1.2 * fx, 0.02) * L, Vector2(1.35 * fx, -0.02) * L, 0.0, w, 0.0)
			f._stroke(Vector2(-0.6 * fx, -0.32) * L, Vector2(0.9 * fx, -0.26) * L, 0.0, w * 0.28, 0.02)
			f._stroke(Vector2(-0.5 * fx, 0.34) * L, Vector2(0.8 * fx, 0.3) * L, 0.0, w * 0.24, 0.03)
		"supurme":  # uzun sap: geniş yatay hilal
			f._stroke(Vector2(-1.1 * fx, -0.35) * L, Vector2(1.15 * fx, -0.05) * L, -0.35 * L, w, 0.0)
		"yarma":    # ağır: baş üstünden dik yarma + yerde kısa yatay sürüntü
			f._stroke(Vector2(-0.3 * fx, -1.15) * L, Vector2(0.35 * fx, 0.75) * L, -0.18 * L, w, 0.0)
			f._stroke(Vector2(-0.55 * fx, 0.8) * L, Vector2(0.95 * fx, 0.72) * L, -0.05 * L, w * 0.55, 0.05)
		"kivrim":   # kırbaç: kıvrık S darbe (iki yarım)
			f._stroke(Vector2(-1.0 * fx, -0.3) * L, Vector2(0.05 * fx, 0.05) * L, -0.35 * L, w, 0.0)
			f._stroke(Vector2(0.0, 0.05) * L, Vector2(1.1 * fx, -0.1) * L, 0.3 * L, w * 0.75, 0.03)
	# ışınsal mürekkep dikenleri (vuruş yönüne yığılmış)
	var n := int(s["diken"])
	for i in n:
		var a := TAU * float(i) / float(n) + f._rng.randf_range(-0.25, 0.25)
		var d := Vector2.from_angle(a)
		var on := 0.6 + 0.4 * maxf(0.0, d.x * fx)   # öne bakan dikenler uzun
		f._spikes.append({"dir": d, "len": f._rng.randf_range(7.0, 14.0) * on * (0.85 + 0.3 * guc) * float(s["boy"]),
			"w": f._rng.randf_range(1.1, 2.0) * (0.9 + 0.3 * guc), "d": f._rng.randf_range(0.0, 0.025)})
	FX.root.add_child(f)
	return f


func _stroke(a: Vector2, b: Vector2, bulge: float, w: float, delay: float) -> void:
	## Darbe = KIL kıl şerit (kuru fırça): her kılın enine yeri, eni, titreşimi, bitişi ve rengi ayrı. Kenar kılları sumi
	## ve kuyrukta erken kopar; içtekiler vurgu renginde (ton farkıyla), arada bir sumi damar; en ortadaki uca dek gider.
	var mid := (a + b) * 0.5 + (b - a).normalized().orthogonal() * bulge
	var kil: Array = []
	for k in KIL:
		var lc := (float(k) + 0.5) / KIL - 0.5
		var edge := absf(lc) * 2.0
		var sumi := edge > 0.62 or _rng.randf() < 0.18
		var ton := _rng.randf_range(-0.18, 0.12)
		kil.append({"lc": lc + _rng.randf_range(-0.02, 0.02), "hw": 0.5 / KIL * _rng.randf_range(1.15, 1.8),
			"s0": _rng.randf_range(0.0, 0.05) * edge, "end": clampf(1.0 - edge * _rng.randf_range(0.2, 0.5) - _rng.randf_range(0.0, 0.08), 0.42, 1.0),
			"wob": _rng.randf_range(0.01, 0.035), "ph": _rng.randf_range(0.0, TAU), "sumi": sumi, "ton": ton,
			"a": _rng.randf_range(0.82, 1.0)})
	_strokes.append({"a": a, "c": mid, "b": b, "w": w, "d": delay, "kil": kil})
	# kuyruk damlaları: darbe yönünde savrulan
	var dir := (b - mid).normalized()
	for i in _rng.randi_range(4, 6):
		var sp := _rng.randf_range(60.0, 170.0)
		_drops.append({"o": b - dir * _rng.randf_range(0.0, 4.0), "v": dir.rotated(_rng.randf_range(-0.45, 0.45)) * sp,
			"r": _rng.randf_range(0.7, 1.7) * (w / 7.0), "d": delay + CIZ * 0.8})


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS


func _process(delta: float) -> void:
	var d := delta / maxf(0.05, Engine.time_scale)
	_t += d
	if _t >= _life:
		queue_free()
		return
	for e in _drops:
		if _t >= float(e["d"]):
			e["o"] = (e["o"] as Vector2) + (e["v"] as Vector2) * d
			e["v"] = (e["v"] as Vector2) * (1.0 - 6.0 * d) + Vector2(0, 220.0 * d)
	queue_redraw()


static func _bez(a: Vector2, c: Vector2, b: Vector2, s: float) -> Vector2:
	var u := 1.0 - s
	return a * u * u + c * 2.0 * u * s + b * s * s


static func _prof(s: float) -> float:
	## Fırça baskısı: başta hızla dolan (bastırma), ortada dolgun, kuyruğa doğru incelen
	## (baş küt ve yuvarlak: "tome"), kuyrukta kıl inceliğine dek sivrilen
	return lerpf(0.7, 1.0, sqrt(clampf(s / 0.1, 0.0, 1.0))) * lerpf(1.0, 0.04, pow(s, 1.15))


func _kil(st: Dictionary, h: Dictionary, s_to: float, wmul: float, col: Color) -> void:
	## Tek kıl şeridi: s0 → min(s_to, bitiş); enine yeri dalgalanır, sonunda sivrilir
	var se := minf(s_to, float(h["end"]))
	var s0 := float(h["s0"])
	if se <= s0 + 0.02:
		return
	var n := maxi(3, int(ceil((se - s0) * 26.0)))
	var a: Vector2 = st["a"]
	var c: Vector2 = st["c"]
	var b: Vector2 = st["b"]
	var cols := PackedColorArray([col, col, col, col])
	var uvs := PackedVector2Array([Vector2.ZERO, Vector2.ZERO, Vector2.ZERO, Vector2.ZERO])
	var pl := Vector2.ZERO
	var ph := Vector2.ZERO
	for i in n + 1:
		var s := lerpf(s0, se, float(i) / float(n))
		var p := _bez(a, c, b, s)
		var tg := (_bez(a, c, b, minf(1.0, s + 0.02)) - _bez(a, c, b, maxf(0.0, s - 0.02))).normalized()
		var nn := tg.orthogonal()
		var W := float(st["w"]) * _prof(s) * wmul
		var tip := clampf((float(h["end"]) - s) / 0.1, 0.0, 1.0) * clampf((s - s0) / 0.04 + 0.4, 0.0, 1.0)
		var lc := float(h["lc"]) + float(h["wob"]) * sin(s * 9.0 + float(h["ph"]))
		var hw := float(h["hw"]) * tip
		var ql := p + nn * W * (lc - hw)
		var qh := p + nn * W * (lc + hw)
		if i > 0:
			draw_primitive(PackedVector2Array([pl, ql, qh, ph]), cols, uvs)
		pl = ql
		ph = qh


func _draw() -> void:
	var fade := 1.0 - clampf((_t - (CIZ + KAL)) / SON, 0.0, 1.0)
	if fade <= 0.0:
		return
	# 1) ışınsal dikenler: sumi, ucu vurguda (önce ve altta)
	for sp in _spikes:
		var tt := _t - float(sp["d"])
		if tt <= 0.0:
			continue
		var g := clampf(tt / 0.05, 0.0, 1.0)
		var dfade := 1.0 - clampf((tt - 0.12) / 0.14, 0.0, 1.0)
		if dfade <= 0.0:
			continue
		var dir: Vector2 = sp["dir"]
		var l0 := (1.0 if parlak else 9.0 + 6.0 * g)
		var l1 := l0 + float(sp["len"]) * g
		var w := float(sp["w"]) * dfade
		var p0 := dir * l0
		var p1 := dir * l1
		var nn := dir.orthogonal() * w * 0.5
		draw_colored_polygon(PackedVector2Array([p0 + nn, p1, p0 - nn]), Color(vurgu if parlak else INK, 0.92 * dfade))
		draw_line(dir * (l1 - (l1 - l0) * 0.35), p1, Color(vurgu, 0.9 * dfade), maxf(0.6, w * 0.35))
		if not parlak:
			draw_circle(p1 + dir * w * 0.6, w * 0.55, Color(INK, 0.92 * dfade))
	# 2) kesik darbeleri
	for st in _strokes:
		var tt := _t - float(st["d"])
		if tt <= 0.0:
			continue
		var s_to := clampf(tt / CIZ, 0.0, 1.0)
		s_to = 1.0 - pow(1.0 - s_to, 2.2)   # hızlı çıkış, yumuşak duruş
		var dry := clampf((tt - CIZ) / KAL, 0.0, 1.0)
		var a: Vector2 = st["a"]
		var W0 := float(st["w"]) * _prof(0.0)
		# başta bastırma göleti (yuvarlak, ıslak sumi) + altta ince sumi gövde (kıllar arası boşluk kâğıt değil gölge)
		draw_circle(a, W0 * 0.5, Color(INK, 0.95 * fade))
		var vc := vurgu.lerp(vurgu.darkened(0.6), dry)
		for h in st["kil"]:
			_kil(st, {"lc": h["lc"], "hw": float(h["hw"]) * 1.25, "s0": h["s0"], "end": float(h["end"]) * 0.97, "wob": h["wob"], "ph": h["ph"]},
				s_to, 1.15, Color(INK, 0.9 * fade))
		# kıllar: kenarlar ve damarlar sumi, içtekiler vurgu (kurudukça koyulaşır, kıllar kuyruktan geri çekilir)
		for h in st["kil"]:
			var kc: Color = INK if h["sumi"] else (vc.lightened(float(h["ton"])) if float(h["ton"]) > 0.0 else vc.darkened(-float(h["ton"])))
			_kil(st, h, s_to * (1.0 - 0.15 * dry * absf(float(h["lc"])) * 2.0), 1.0, Color(kc, float(h["a"]) * fade))
		# ak-sıcak kıl hattı: yalnızca ilk iki kare (bıçak ağzı yanında)
		if tt < SIVRI:
			var hk := 1.0 - tt / SIVRI
			_kil(st, {"lc": -0.18, "hw": 0.1 * hk + 0.03, "s0": 0.02, "end": 0.92, "wob": 0.0, "ph": 0.0}, s_to, 1.0, Color(1.6, 1.45, 1.2, hk))
	# 3) damlalar
	for e in _drops:
		if _t < float(e["d"]):
			continue
		var o: Vector2 = e["o"]
		var v: Vector2 = e["v"]
		var r := float(e["r"]) * fade
		if r < 0.2:
			continue
		draw_circle(o, r, Color(INK, 0.95 * fade))
		if v.length() > 20.0:
			var dv := v.normalized()
			draw_colored_polygon(PackedVector2Array([o + dv.orthogonal() * r, o - dv * r * 3.2, o - dv.orthogonal() * r]), Color(INK, 0.95 * fade))


static func parilti(pos: Vector2, renk: Color) -> void:
	## Bitiriş hazırlığının sonunda bıçak ucunda kısa iğne parıltısı (beklenti / "tell"): dört kollu sumi yıldız, uçları vurguda
	if FX.root == null or Game.fx_scale <= 0.0:
		return
	var f := KesikFX.new()
	f.position = pos
	f.z_index = 58
	f.vurgu = renk
	f._life = 0.09
	f.parlak = true
	f._spikes = []
	for i in 4:
		f._spikes.append({"dir": Vector2.from_angle(PI * 0.5 * i + 0.2), "len": 9.0 if i % 2 == 0 else 5.0, "w": 1.6, "d": 0.0})
	FX.root.add_child(f)
