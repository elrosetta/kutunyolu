class_name Perde
extends CanvasLayer
## v40 ekran geçişleri: mürekkep perdesi (shaders/ink_perde.gdshader) + ölüm derecesi.
## Ağaç köküne bir kez eklenir (FX.screen_layer gibi), bölüm değişse de kalır; katman 6 (vinyet 5'in üstü, arayüz
## 10'un altı). Duraklatmadan ve yavaşlatmadan etkilenmez (PROCESS_MODE_ALWAYS; gerçek zamanla, kare başına en çok 50 ms:
## bölüm kurulumunun uzun ilk karesi perdeyi atlatmaz). Perde t = 0 iken ColorRect gizlidir: piksel doldurma yok.
## Başsız / test koşularında da çalışır (yalnızca bir uniform yazımı).
##   acilis(kind)   bölüm başı: perde kapalı başlar, fırça süpürmesiyle açılır ("bolum", "boss": sağdan; "yurt", "konak":
##                  sıcak / soğuk düz solma)
##   isin(kapat)    Kut Taşı ışınlanması: çözülme ile kapan (0,16 sn) / aç (0,42 sn), Kut rengi kenar
##   olum(mat)      ölüm: derecelendirme malzemesinde "death" 0 → 1 (1,4 sn, gerçek zaman); yeni bölümde sıfırlanır
##   --perdesiz     test / çekim: perde hiç çizilmez

const INK := Color(0.082, 0.086, 0.114, 1.0)
const KUT := Color(0.36, 0.86, 0.9, 1.0)
const AMBER := Color(0.42, 0.22, 0.08, 1.0)

static var _inst: Perde
static var _kapali := OS.get_cmdline_user_args().has("--perdesiz")

var rect: ColorRect
var mat: ShaderMaterial
var _olum_tw: Tween
var _olum_mat: ShaderMaterial
var t := 0.0
# perde canlandırması Tween değil, elle: bölüm kurulumunun ardındaki ilk kare (doku yükleme, gölgelendirici derleme)
# 0,5-2 sn sürebilir; Tween o tek karede süreyi tüketip perdeyi atlardı. Gerçek zaman (Time.get_ticks_msec), kare
# başına en çok 100 ms ilerler, 250 ms'den uzun kare (yükleme takılması) hiç saymaz: perde kapalı bekler, sonra
# süpürülür; en geç 3 sn sonra kesin açılır. Duraklatma / yavaşlatmadan etkilenmez.
var _anim := false
var _a_from := 0.0
var _a_to := 0.0
var _a_dur := 0.5
var _a_delay := 0.0
var _a_t := 0.0
var _a_ease := 0   # 0 sinüs giriş-çıkış, 1 kare giriş (hızlanarak kapanır), 2 sinüs çıkış (yavaşlayarak açılır)
var _a_cb: Callable
var _last_ms := 0
var _wall := 0.0


static func _ornek() -> Perde:
	## Tek örnek; ilk çağrıda köke eklenir. Kök çocuklarını kurarken (Main._ready içinden ilk bölüm) doğrudan
	## add_child yasak: ekleme ertelenir, perde işi ağaca girince uygulanır (_uygula; aynı karede, çizimden önce).
	if _inst != null and is_instance_valid(_inst):
		return _inst
	var ml := Engine.get_main_loop() as SceneTree
	if ml == null or ml.root == null:
		return null
	var p := Perde.new()
	_inst = p
	ml.root.add_child.call_deferred(p)
	return p


func _init() -> void:
	layer = 6
	process_mode = Node.PROCESS_MODE_ALWAYS
	rect = ColorRect.new()
	rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	rect.set_anchors_preset(Control.PRESET_FULL_RECT)
	mat = ShaderMaterial.new()
	mat.shader = load("res://shaders/ink_perde.gdshader")
	rect.material = mat
	rect.visible = false
	add_child(rect)


func _ready() -> void:
	_fit()
	get_viewport().size_changed.connect(_fit)


func _fit() -> void:
	# CanvasLayer altındaki kök Control çapayla boyutlanmaz: görünür dikdörtgene elle oturt
	var vs := get_viewport().get_visible_rect().size
	rect.position = Vector2.ZERO
	rect.size = vs
	mat.set_shader_parameter("aspect", vs.x / maxf(1.0, vs.y))


func _uygula(cb: Callable) -> void:
	## ağaçtaysa hemen, değilse (ekleme ertelendi) ağaca girince çalıştır
	if is_inside_tree():
		cb.call()
	else:
		cb.call_deferred()


func _set_t(v: float) -> void:
	t = v
	mat.set_shader_parameter("t", v)
	rect.visible = v > 0.002


func _baslat(from: float, to: float, dur: float, delay: float, ease: int, cb: Callable = Callable()) -> void:
	_a_from = from
	_a_to = to
	_a_dur = maxf(0.01, dur)
	_a_delay = delay
	_a_t = 0.0
	_a_ease = ease
	_a_cb = cb
	_anim = true
	_wall = 0.0
	_last_ms = Time.get_ticks_msec()
	_set_t(from)


func _process(_delta: float) -> void:
	if not _anim:
		return
	var now := Time.get_ticks_msec()
	var d := float(now - _last_ms) / 1000.0
	_last_ms = now
	_wall += d
	if d > 0.25:
		d = 0.0   # yükleme takılması (doku / gölgelendirici): perde olduğu yerde bekler
	d = minf(d, 0.1)
	if _wall > _a_delay + _a_dur + 3.0:
		d = _a_dur   # güvenlik: sürekli takılan makinede perde 3 sn içinde kesin açılır
	if _a_delay > 0.0:
		_a_delay -= d
		return
	_a_t += d
	var u := clampf(_a_t / _a_dur, 0.0, 1.0)
	match _a_ease:
		1:
			u = u * u
		2:
			u = sin(u * PI * 0.5)
		_:
			u = 0.5 - 0.5 * cos(u * PI)
	_set_t(lerpf(_a_from, _a_to, u))
	if _a_t >= _a_dur:
		_anim = false
		if _a_cb.is_valid():
			var cb := _a_cb
			_a_cb = Callable()
			cb.call()


static func acilis(kind := "bolum") -> void:
	## Bölüm başı perdesi: kapalı başlar, açılır. Ölüm derecesi varsa sıfırlanır (yeni koşu).
	if _kapali:
		return
	var p := _ornek()
	if p == null:
		return
	p._uygula(p._acilis.bind(kind))


func _acilis(kind: String) -> void:
	olum_sifirla()
	mat.set_shader_parameter("seed", randf() * 10.0)
	var dur := 0.75
	match kind:
		"boss":
			mat.set_shader_parameter("mode", 0)
			mat.set_shader_parameter("dir", -1.0)
			mat.set_shader_parameter("ink", INK)
			mat.set_shader_parameter("tint", Color(0.3, 0.05, 0.06, 1.0))
			mat.set_shader_parameter("tint_k", 0.35)
			dur = 0.9
		"konak":
			mat.set_shader_parameter("mode", 2)
			mat.set_shader_parameter("ink", Color(0.06, 0.03, 0.01, 1.0))
			mat.set_shader_parameter("tint", AMBER)
			mat.set_shader_parameter("tint_k", 0.6)
			dur = 1.1
		"yurt":
			mat.set_shader_parameter("mode", 2)
			mat.set_shader_parameter("ink", Color(0.02, 0.02, 0.05, 1.0))
			mat.set_shader_parameter("tint", Color(0.1, 0.12, 0.3, 1.0))
			mat.set_shader_parameter("tint_k", 0.4)
			dur = 1.0
		_:
			mat.set_shader_parameter("mode", 0)
			mat.set_shader_parameter("dir", 1.0)
			mat.set_shader_parameter("ink", INK)
			mat.set_shader_parameter("tint_k", 0.0)
	_baslat(1.0, 0.0, dur, 0.08, 0)   # 0,08 sn kapalı bekler (ilk kare), sonra açılır


static func isin(kapat: bool, cb: Callable = Callable()) -> void:
	## Işınlanma çözülmesi: kapat = true → perde 0,16 sn'de kaplar (sonra cb), false → 0,42 sn'de çekilir
	if _kapali:
		if cb.is_valid():
			cb.call()
		return
	var p := _ornek()
	if p == null:
		if cb.is_valid():
			cb.call()
		return
	p._uygula(p._isin.bind(kapat, cb))


func _isin(kapat: bool, cb: Callable) -> void:
	mat.set_shader_parameter("mode", 1)
	mat.set_shader_parameter("ink", Color(0.05, 0.08, 0.1, 1.0))
	mat.set_shader_parameter("tint", KUT)
	mat.set_shader_parameter("tint_k", 0.45)
	if kapat:
		mat.set_shader_parameter("seed", randf() * 10.0)
		_baslat(t, 1.0, 0.16, 0.0, 1, cb)
	else:
		_baslat(1.0, 0.0, 0.42, 0.0, 2)


static func olum(grade_mat: ShaderMaterial) -> void:
	## Ölüm derecesi: vinyet / derecelendirme malzemesinin "death" parametresi 1,4 sn'de 1'e (gerçek zaman, duraklatmada sürer)
	if grade_mat == null:
		return
	var p := _ornek()
	if p == null:
		grade_mat.set_shader_parameter("death", 1.0)
		return
	p._uygula(p._olum.bind(grade_mat))


func _olum(grade_mat: ShaderMaterial) -> void:
	olum_sifirla()
	_olum_mat = grade_mat
	_olum_tw = create_tween()
	_olum_tw.set_pause_mode(Tween.TWEEN_PAUSE_PROCESS)
	_olum_tw.set_ignore_time_scale(true)
	_olum_tw.tween_method(func(v: float) -> void:
		if is_instance_valid(grade_mat):
			grade_mat.set_shader_parameter("death", v), 0.0, 1.0, 1.4).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)


func olum_sifirla() -> void:
	if _olum_tw != null and _olum_tw.is_valid():
		_olum_tw.kill()
	_olum_tw = null
	if _olum_mat != null and is_instance_valid(_olum_mat):
		_olum_mat.set_shader_parameter("death", 0.0)
	_olum_mat = null
