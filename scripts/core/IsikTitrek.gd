class_name IsikTitrek
extends Node
## v40: noktasal ışık titremesi. Eski iki adımlı Tween (0,8 → 1,0 → 0,8) mekanik bir "nabız" veriyordu; alev, kor ve
## kristal ışığı katmanlı sinüslerle + seyrek rastgele atımlarla (rüzgârda yalpalayan alev) titrer, konum ve renk de
## birlikte oynar. Işığın çocuğu olarak eklenir (ışık silinince gider). Düşük maliyet: kare başına birkaç sinüs.
##   mesale  : hızlı, geniş genlik, konum yalpası, sıcak → beyaz-sarı renk kayması (çıra, meşale, kandil)
##   ocak    : yavaş, orta genlik, derin nefes + seyrek çıtırtı (ocak, kazan, mangal)
##   lav     : çok yavaş, dalgalı, kızıl ↔ turuncu (lav havuzu, kor)
##   kristal : çok yavaş nefes, titreme yok (kristal, Kut, buz)
##   zehir   : yavaş kabarcıklı nabız (zehir havuzu)

const KIND := {
	"mesale": {"amp": 0.2, "rate": 7.0, "jit": 2.2, "pop": 0.35, "hue": 0.12, "breath": 0.0},
	"ocak": {"amp": 0.12, "rate": 3.2, "jit": 1.0, "pop": 0.2, "hue": 0.08, "breath": 0.06},
	"lav": {"amp": 0.14, "rate": 1.4, "jit": 0.0, "pop": 0.0, "hue": 0.16, "breath": 0.1},
	"kristal": {"amp": 0.05, "rate": 0.5, "jit": 0.0, "pop": 0.0, "hue": 0.0, "breath": 0.1},
	"zehir": {"amp": 0.1, "rate": 1.1, "jit": 0.0, "pop": 0.12, "hue": 0.0, "breath": 0.08},
}

var light: Light2D
var kind := "mesale"
var base_e := 1.0
var base_pos := Vector2.ZERO
var base_col := Color.WHITE
var hot_col := Color.WHITE
var _t := 0.0
var _pop := 0.0
var _pop_t := 0.0
var _ph := 0.0
var _rate_k := 1.0


static func attach(l: Light2D, k := "mesale") -> IsikTitrek:
	## Işığın şimdiki enerji / konum / rengi taban alınır; ışık kapalıysa (v38 ışık sınırı) hiç eklenmez
	if l == null or not l.enabled:
		return null
	var f := IsikTitrek.new()
	f.light = l
	f.kind = k if KIND.has(k) else "mesale"
	f.base_e = l.energy
	f.base_pos = l.position
	f.base_col = l.color
	# sıcak uç: alev beyaz-sarıya, lav turuncuya kayar; soğuk ışıklar (kristal) renk değiştirmez
	f.hot_col = Color(minf(1.0, l.color.r * 1.05), minf(1.0, l.color.g * 1.18 + 0.05), minf(1.0, l.color.b * 1.3 + 0.08))
	f._ph = randf() * 100.0
	f._rate_k = randf_range(0.85, 1.15)
	l.add_child(f)
	return f


func _process(delta: float) -> void:
	if light == null or not is_instance_valid(light):
		return
	var P: Dictionary = KIND[kind]
	var rate: float = float(P["rate"]) * _rate_k
	_t += delta * rate
	var x := _t + _ph
	# katmanlı titreme: üç uyumsuz sinüs (-1..1), çarpık (alev yukarı daha çok sıçrar)
	var n := sin(x) * 0.5 + sin(x * 2.37 + 1.3) * 0.3 + sin(x * 5.11 + 0.7) * 0.2
	# seyrek atım: rüzgâr yalaması / çıtırtı (kısa, sert)
	var pop: float = float(P["pop"])
	if pop > 0.0:
		_pop_t -= delta
		if _pop_t <= 0.0:
			_pop_t = randf_range(0.6, 2.6)
			_pop = randf_range(-0.6, 1.0) * pop
		_pop = lerpf(_pop, 0.0, minf(1.0, delta * 9.0))
	var breath: float = float(P["breath"])
	var br := sin((_t * 0.23 + _ph) * 1.0) * breath
	var e := base_e * (1.0 + float(P["amp"]) * n + _pop + br)
	light.energy = maxf(0.0, e)
	var jit: float = float(P["jit"])
	if jit > 0.0:
		light.position = base_pos + Vector2(sin(x * 1.9) * jit, sin(x * 2.7 + 1.1) * jit * 0.6 - maxf(0.0, _pop) * 3.0)
	var hue: float = float(P["hue"])
	if hue > 0.0:
		light.color = base_col.lerp(hot_col, clampf(0.5 + 0.5 * n + _pop, 0.0, 1.0) * hue * 4.0)
