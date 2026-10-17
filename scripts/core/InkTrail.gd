class_name InkTrail
extends WeaponTrail
## Stil v2 mürekkep fırçası savuruş izi (Shinobi: Art of Vengeance referansı: kızıl kuru fırça hilali).
## WeaponTrail'in yerine geçer (FX.trail, yalnızca --stil=v2): Player aynı add(kök, uç) / done / life arayüzünü kullanır.
##
## Geometri: bıçak ucunun süpürdüğü şerit (SÜPÜRME) ya da ucun yolunu izleyen şerit (YOL: saplama, kırbaç).
## Genişlik fırça baskısı eğrisini izler: savuruş başında ince (baskı rampası), hızlı orta kısımda dolgun karın,
## yaşlandıkça incelen kuyruk; doku ve renk shaders/ink_brush.gdshader'da (kıl çizgileri, kuru fırça boşlukları,
## kızıl çekirdek, siyah fırça izleri, turuncu kenar, sıcak ön kenar, kıl tellerine ayrılarak erime).
## Mürekkep zerreleri ve kıvılcımlar aynı üçgen dizisinde: iz başına tek çizim çağrısı. Düğümler havuzda tutulur.
##
## Tasarımlar (`setup`): kılıç = temiz hilal · ağır (balta / çekiç / gürz / dev kılıç) = geniş, kuru, sıvanmış yay +
## kalın zerreler + bitişte sıçrantı · mızrak saplaması = düz çizgi + iki yankı · hançer = hızlı çift fırça ·
## kırbaç = ince kıvrak şerit · uzun sap (teber / tırpan / asa) = uzun ince hilal. Ağır / şarjlı / bitiriş:
## arka koyu katman + dış ikinci hilal. Element silahları kendi paletinde (od, ayaz, zehir, ruh, yıldırım, erlik, ay, yel).
## v20: sınıflar belirgin ayrıldı (hançer ince hızlı fiske, kılıç temiz hilal, ağır kalın sürüklenen kuru fırça + damlayan
## sıçrantı, uzun sap geniş süpürme + iç yankı yayı, mızrak uzun çizgi + üç yankı, kırbaç kıvrılan kurdele) ve unsurlu
## silah (Unsur.gd) kendi paletinde + kendi zerreleriyle çizilir: od alev dilleri, ayaz buz kıymığı + sis, yıldırım
## çatırdayan kıvılcım arkları, kam tayfsı ard görüntü + ruh dumanı, Yer-Su yapraklar. Zerreler aynı üçgen dizisinde.

enum { SWEEP, PATH }

const SHADER: Shader = preload("res://shaders/ink_brush.gdshader")
const BRISTLE: Texture2D = preload("res://assets/fx/ink/bristle.png")

static var _pool: Array = []
static var _mats: Dictionary = {}
static var active: InkTrail        # son başlatılan oyuncu izi (InkFX kesik yönü için)

var mode := SWEEP
var pal := 0
var style := "kilic"
var w_frac := 0.42          # SÜPÜRME: mürekkep genişliği / bıçak boyu
var path_w := 5.0           # YOL: yarı genişlik (dünya birimi)
var layered := 0            # 0 yok, 1 arka koyu katman, 2 + dış ikinci hilal
var double := false         # hançer: içte ikinci ince fırça
var echoes := 0             # saplama yankıları
var wiggle := 0.0           # kırbaç kıvrımı (dünya birimi)
var fleck_k := 1.0          # zerre yoğunluğu
var splash_end := false     # ağır: iz bitince uçta mürekkep sıçrantısı
var min_w := 4.0            # SÜPÜRME: en az mürekkep genişliği (dünya birimi; kısa bıçaklar)
var ramp_len := 0.55        # baskı rampası: ucun ilk (bıçak boyu x ramp_len) yolu ince başlar
var unsur := ""             # v20: unsur zerreleri (od, ayaz, yildirim, kam, yersu)
var u_scale := 1.0          # v20: kıl dokusunun boyuna ölçeği (ağır < 1: uzun sürüklenen izler)
var ghost := false          # v20 kam: tayfsı ard görüntü katmanı
var inner_arc := false      # v20 uzun sap: içte soluk ikinci yay
var twist := false          # v20 kırbaç: genişlik boyunca kıvrılan kurdele
var _elem: Array = []       # v20 unsur zerreleri [konum, hız, ömür, yaş, boy, tür, açı, açısal hız]
var _u_acc := 0.0
var _crk_t := 0.0
var _s: Array = []          # [kök, uç, zaman, baskı, yay uzunluğu]
var _batch := 0             # son işlemeden beri eklenen örnek sayısı
var _prev_t := 0.0
var _t0 := -1.0
var _arc := 0.0
var _flecks: Array = []     # [konum, hız, ömür, yaş, boy, tür]
var _u_off := 0.0
var _rng := RandomNumberGenerator.new()
var _ci_inited := false
var _last_dir := Vector2.RIGHT


static func acquire(parent: Node) -> InkTrail:
	while not _pool.is_empty():
		# havuzdaki iz bölüm değişince (FX kökü silinince) serbest kalmış olabilir: tipli atamadan önce doğrula
		var v: Variant = _pool.pop_back()
		if not is_instance_valid(v):
			continue
		var t := v as InkTrail
		if t != null and t.get_parent() == parent and not t.is_queued_for_deletion():
			t._reset()
			t.visible = true
			t.set_process(true)
			return t
		elif t != null:
			t.queue_free()
	var n := InkTrail.new()
	parent.add_child(n)
	return n


func _ready() -> void:
	z_index = 56
	top_level = true
	_rng.randomize()
	_u_off = _rng.randf() * 10.0


func _reset() -> void:
	_s.clear()
	_flecks.clear()
	_batch = 0
	_t = 0.0
	_prev_t = 0.0
	_t0 = -1.0
	_arc = 0.0
	done = false
	mode = SWEEP
	pal = 0
	style = "kilic"
	w_frac = 0.42
	path_w = 5.0
	layered = 0
	double = false
	echoes = 0
	wiggle = 0.0
	fleck_k = 1.0
	splash_end = false
	ramp_len = 0.55
	unsur = ""
	u_scale = 1.0
	ghost = false
	inner_arc = false
	twist = false
	_elem.clear()
	_u_acc = 0.0
	_crk_t = 0.0
	life = 0.2
	_auto = {}
	material = null
	_u_off = _rng.randf() * 10.0


# ------------------------------------------------------------------ tasarım seçimi
const DAGGERS := ["ikiz_bicak", "bori_hanceri", "kurt_pencesi"]
const HEAVIES := ["gurz", "civili_topuz", "dag_cekici", "kor_cekici", "savas_baltasi", "ikiz_balta", "ulu_kilic", "bozgun_kilici"]
const POLES := ["teber", "erlik_tirpani", "kayin_asasi"]
const SPEARS := ["kargi", "tulpar_mizragi"]
const WHIPS := ["kement", "od_kamcisi", "erlik_zinciri"]
const THRUSTS := ["thrust", "pole_thrust", "pole_thrust_lo", "lunge", "lunge_long", "stab_heavy", "flurry"]
const WHIP_SW := ["whip_crack", "whip_side"]


static func weapon_class(id: String) -> String:
	if id in DAGGERS:
		return "hancer"
	if id in HEAVIES:
		return "agir"
	if id in POLES:
		return "uzun"
	if id in SPEARS:
		return "mizrak"
	if id in WHIPS:
		return "kirbac"
	return "kilic"


func setup(it: Dictionary, atk: Dictionary, weight: float) -> void:
	## Silah sınıfı, savuruş ve vuruş türüne göre fırça tasarımı + palet.
	var id := String(it.get("id", ""))
	var sw := String(atk.get("c", {}).get("s", ""))
	var heavy: bool = atk.get("heavy", false)
	var finisher: bool = atk.get("pause", false) or atk.get("c", {}).get("last", false)
	var hold := float(atk.get("hold", 0.0))
	style = weapon_class(id)
	pal = InkFX.weapon_pal(it)
	InkFX.player_pal = pal
	match style:
		"kilic":
			w_frac = 0.62
			life = 0.2
		"agir":
			# v20: kalın, kuru, sürüklenen geniş darbe; kıllar boyuna uzun (u_scale), iri damlalar, uçta sıçrantı
			w_frac = 1.05
			life = 0.32
			fleck_k = 2.4
			splash_end = true
			ramp_len = 0.8
			u_scale = 0.55
		"uzun":
			# v20: uzun sapın geniş süpürmesi: ince uzun hilal, uzun ömür, içte soluk yankı yayı
			w_frac = 0.34
			life = 0.3
			fleck_k = 1.0
			inner_arc = true
			u_scale = 1.25
		"hancer":
			# hançer: kısa bıçağın süpürdüğü alan küçük; uç yolunu izleyen iki paralel hızlı, ince fiske
			mode = PATH
			path_w = 3.4
			life = 0.16
			double = true
			fleck_k = 0.5
			ramp_len = 0.25
			u_scale = 1.6
		"mizrak":
			w_frac = 0.4
			life = 0.2
		"kirbac":
			mode = PATH
			path_w = 2.8
			wiggle = 2.6
			life = 0.32
			fleck_k = 0.8
			twist = true
	if sw in THRUSTS:
		# v20 saplama: uzun düz çizgi + üç yankı (mızrak / ağır saplama daha uzun yaşar)
		mode = PATH
		path_w = (3.0 if style != "agir" else 5.0)
		echoes = 3 if style in ["mizrak", "uzun"] else 2
		life = 0.24 if style in ["mizrak", "uzun"] else 0.2
		double = false
		wiggle = 0.0
		twist = false
	elif sw in WHIP_SW:
		mode = PATH
		path_w = 2.8
		wiggle = 2.6
		life = 0.32
		twist = true
	if finisher or heavy:
		layered = 2 if (heavy and hold > 0.35) or atk.get("pause", false) else 1
		w_frac *= 1.2
		path_w *= 1.35
		life *= 1.25
		fleck_k *= 1.5
	if style == "agir":
		layered = maxi(layered, 1)   # v20: ağır silahın arkasında her zaman koyu kuru sürüntü
	unsur = Unsur.of(it)
	ghost = unsur == "kam"
	life *= 1.0 + 0.2 * weight
	active = self
	_apply_mat()


func _apply_mat() -> void:
	var key := "%d_%s_%d_%.2f" % [pal, style, layered, u_scale]
	if not _mats.has(key):
		var m := ShaderMaterial.new()
		m.shader = SHADER
		m.set_shader_parameter("bristle", Data.tex_full(BRISTLE.resource_path))   # HD paketi varsa 2 kat (UV ile örneklenir)
		var p: Array = InkFX.palette(pal)
		m.set_shader_parameter("c_ink", p[0])
		m.set_shader_parameter("c_core", p[1])
		m.set_shader_parameter("c_body", p[2])
		m.set_shader_parameter("c_rim", p[3])
		m.set_shader_parameter("c_hot", p[4])
		m.set_shader_parameter("rough", 1.6 if style == "agir" else (0.65 if style == "hancer" else (0.9 if style == "kilic" else 1.0)))
		m.set_shader_parameter("streaks", 1.5 if style == "agir" else (0.6 if style in ["hancer", "kirbac"] else (0.9 if style == "kilic" else 1.0)))
		m.set_shader_parameter("dry_in", 0.8 if style == "agir" else 0.5)
		m.set_shader_parameter("u_scale", u_scale)
		m.set_shader_parameter("glow_gain", 0.5 + 0.25 * float(layered))
		_mats[key] = m
	material = _mats[key]


# ------------------------------------------------------------------ örnekleme
func add(base: Vector2, tip: Vector2) -> void:
	if material == null:
		_apply_mat()
	if _t0 < 0.0:
		_t0 = _t
	if _s.size() > 0:
		var last: Array = _s[_s.size() - 1]
		if (last[1] as Vector2).distance_to(tip) < 0.35:
			return
		if mode == SWEEP:
			# hızlı savuruşta kabza çevresinde açıyla ara örnek (WeaponTrail ile aynı: "V" yok)
			var lb: Vector2 = last[0]
			var lv: Vector2 = last[1] - lb
			var nv: Vector2 = tip - base
			if lv.length() > 1.0 and nv.length() > 1.0:
				var da := wrapf(nv.angle() - lv.angle(), -PI, PI)
				var steps := mini(int(ceil(absf(da) / 0.12)), 24)
				for s in range(1, steps):
					var k := float(s) / float(steps)
					var bb := lb.lerp(base, k)
					var vv := Vector2.from_angle(lv.angle() + da * k) * lerpf(lv.length(), nv.length(), k)
					_push(bb, bb + vv)
	_push(base, tip)


func _push(base: Vector2, tip: Vector2) -> void:
	var d := 0.0
	if _s.size() > 0:
		d = (tip - (_s[_s.size() - 1][1] as Vector2)).length()
	_arc += d
	_s.append([base, tip, _t, 1.0, _arc])
	_batch += 1
	# zerreler: hızla süpürülen yoldan, uzunlukla orantılı
	if d > 0.0 and _s.size() > 2:
		var n := d * 0.09 * fleck_k
		while n > 0.0:
			if _rng.randf() < n:
				_spawn_fleck(base, tip)
			n -= 1.0
		if unsur != "":
			_u_acc += d * float(U_RATE.get(unsur, 0.0)) * (1.35 if style == "agir" else (0.7 if style == "hancer" else 1.0))
			while _u_acc >= 1.0:
				_u_acc -= 1.0
				_spawn_elem(base, tip)


func _spawn_fleck(base: Vector2, tip: Vector2) -> void:
	if _flecks.size() > 64:
		return
	var dir := (tip - base).normalized()
	var prev: Vector2 = _s[_s.size() - 2][1]
	var tan := (tip - prev).normalized()
	var p := tip - dir * _rng.randf_range(0.0, (tip - base).length() * w_frac * 0.9) if mode == SWEEP else tip + tan.orthogonal() * _rng.randf_range(-path_w, path_w)
	var typ := 0
	var r := _rng.randf()
	if r < 0.22:
		typ = 1
	elif r < 0.38:
		typ = 2
	var vel := dir * _rng.randf_range(20.0, 110.0) + tan * _rng.randf_range(-30.0, 60.0) + Vector2(_rng.randf_range(-25, 25), _rng.randf_range(-40, 10))
	if mode == PATH:
		vel = tan * _rng.randf_range(10.0, 80.0) + tan.orthogonal() * _rng.randf_range(-70.0, 70.0)
	var sz := _rng.randf_range(0.6, 2.0) * (1.4 if style == "agir" else 1.0)
	if typ == 2:
		sz *= 0.55
		vel *= 1.6
	_flecks.append([p, vel, _rng.randf_range(0.22, 0.5) * (1.3 if style == "agir" else 1.0), 0.0, sz, typ])


func _process(delta: float) -> void:
	if not _auto.is_empty():
		_auto_step(delta)
	# bu karede eklenen örneklerin zamanı önceki kare ile bu kare arasına yayılır (kademesiz yaş)
	if _batch > 0:
		var n := _s.size()
		var b := mini(_batch, n)
		for i in range(b):
			var k := float(i + 1) / float(b)
			_s[n - b + i][2] = lerpf(_prev_t, _t, k) if _prev_t < _t else _t
		_update_pressure(n - b)
		_batch = 0
	_prev_t = _t
	_t += delta
	while _s.size() > 0 and _t - float(_s[0][2]) > life:
		_s.pop_front()
	for f in _flecks:
		f[3] += delta
		f[1] = (f[1] as Vector2) * maxf(0.0, 1.0 - 3.2 * delta) + Vector2(0, 420.0 * delta)
		f[0] = (f[0] as Vector2) + (f[1] as Vector2) * delta
	var i := _flecks.size() - 1
	while i >= 0:
		if float(_flecks[i][3]) >= float(_flecks[i][2]):
			_flecks.remove_at(i)
		i -= 1
	if done and splash_end and _s.size() > 1:
		splash_end = false
		var last: Array = _s[_s.size() - 1]
		var dir := ((last[1] as Vector2) - (last[0] as Vector2)).normalized()
		for k in 9:
			_flecks.append([(last[1] as Vector2) - dir * _rng.randf_range(0, 6), dir.rotated(_rng.randf_range(-1.2, 1.2)) * _rng.randf_range(40, 150) + Vector2(0, -40), _rng.randf_range(0.3, 0.6), 0.0, _rng.randf_range(1.0, 2.6), 0 if k % 3 else 1])
	_elem_step(delta)
	if _s.is_empty() and _flecks.is_empty() and _elem.is_empty() and done:
		_release()
		return
	queue_redraw()


func _update_pressure(from: int) -> void:
	## Baskı: ucun ilk yolu (ramp_len) ince başlar; uç hızı yüksekse dolgun (karın).
	for i in range(maxi(from, 0), _s.size()):
		var s: Array = _s[i]
		var L := maxf(((s[1] as Vector2) - (s[0] as Vector2)).length() / 0.65, 6.0)
		# ince başlangıç: ucun ilk ramp_len yolu boyunca baskı artar (süre değil yol: hızlı savuruşta da görünür)
		var ramp := smoothstep(0.0, L * ramp_len, float(s[4])) * 0.8 + 0.2
		# uç hızı: en az 1/60 sn'lik pencere üzerinden yay uzunluğu / süre (ara örnekler aynı zamanı paylaşabilir),
		# sonra örnekten örneğe yumuşatılır: iç kenar basamaklanmasın
		var spd := 0.0
		var j := i
		while j > 0 and float(s[2]) - float(_s[j][2]) < 1.0 / 60.0:
			j -= 1
		var dt := float(s[2]) - float(_s[j][2])
		if dt > 0.0001:
			spd = (float(s[4]) - float(_s[j][4])) / dt
		var sp := clampf(spd / (L * 20.0), 0.0, 1.0)
		var prev_sp: float = float(_s[i - 1][5]) if i > 0 and _s[i - 1].size() > 5 else sp
		sp = lerpf(prev_sp, sp, 0.3)
		if s.size() > 5:
			s[5] = sp
		else:
			s.append(sp)
		s[3] = ramp * lerpf(0.55, 1.0, sp)


func _release() -> void:
	visible = false
	set_process(false)
	_s.clear()
	_flecks.clear()
	_elem.clear()
	if active == self:
		active = null
	if _pool.size() < 6:
		_pool.append(self)
	else:
		queue_free()


func tip_dir() -> Vector2:
	## Son örneklerin uç hareket yönü (vuruş kesiği için); yoksa sıfır.
	var n := _s.size()
	if n < 2 or _t - float(_s[n - 1][2]) > 0.12:
		return Vector2.ZERO
	var a: Vector2 = _s[maxi(0, n - 4)][1]
	var b: Vector2 = _s[n - 1][1]
	return (b - a).normalized() if a.distance_to(b) > 0.5 else Vector2.ZERO


# ------------------------------------------------------------------ çizim
var _vp := PackedVector2Array()
var _vuv := PackedVector2Array()
var _vcol := PackedColorArray()
var _vidx := PackedInt32Array()


func _vert(p: Vector2, u: float, v: float, age: float) -> void:
	_vp.append(p)
	_vuv.append(Vector2(u, v))
	_vcol.append(Color(1, 1, 1, age))


func _ribbon(layer: int, wmul: float, shift: float, u_shift: float, age_add: float, offs: Vector2 = Vector2.ZERO) -> void:
	## Bir fırça şeridi: her örnekte iç kenar, mürekkep dış kenarı ötesinde ışıma kenarı (v 0 .. 1).
	var n := _s.size()
	if n < 2:
		return
	if mode == PATH:
		_ribbon_path(layer, wmul, u_shift, age_add, offs)
		return
	var start := _vp.size()
	var lv := float(layer) * 2.0
	var count := 0
	for i in n:
		var s: Array = _s[i]
		var age := clampf((_t - float(s[2])) / life + age_add, 0.0, 1.0)
		var base: Vector2 = s[0]
		var tip: Vector2 = s[1]
		var shrink := 1.0 - 0.6 * pow(age, 1.4)
		var press: float = s[3]
		var inner: Vector2
		var outer: Vector2
		if mode == SWEEP:
			var bl := (tip - base).length() / 0.65
			var dir := (tip - base) / maxf((tip - base).length(), 0.001)
			# uç bıçak ekseni boyunca kayıyorsa (geriden öne savurma, saplama benzeri an) şerit çizgiye çöker:
			# enine yön bıçaktan yol normaline kayar, şerit uç yolunu izleyen fırça çizgisine döner
			var ta: Vector2 = _s[maxi(0, i - 1)][1]
			var tb: Vector2 = _s[mini(n - 1, i + 1)][1]
			var across := dir
			var wk := 1.0
			if ta.distance_to(tb) > 0.05:
				var tan := (tb - ta).normalized()
				var sn := absf(tan.cross(dir))
				var pw := smoothstep(0.18, 0.55, sn)
				if pw < 1.0:
					var nside := tan.orthogonal()
					if nside.dot(dir) < 0.0:
						nside = -nside
					across = (dir * pw + nside * (1.0 - pw)).normalized()
					wk = lerpf(0.45, 1.0, pw)
			# kuyruk ucu (en eski örnek) her zaman sivri: kare bayrak gibi kesik başlangıç yok
			var tail := smoothstep(0.0, bl * 0.45, float(s[4]) - float(_s[0][4]))
			var w := maxf(w_frac * bl, min_w) * press * shrink * wmul * wk * lerpf(0.12, 1.0, tail)
			var c := tip + across * shift * bl + offs * (0.4 + 0.6 * age)
			inner = c - across * w
			outer = c + across * w * 0.3
		else:
			var a: Vector2 = _s[maxi(0, i - 1)][1]
			var b: Vector2 = _s[mini(n - 1, i + 1)][1]
			var tan := (b - a).normalized() if a.distance_to(b) > 0.01 else _last_dir
			_last_dir = tan
			var nrm := tan.orthogonal()
			var hw := path_w * press * shrink * wmul
			var c := tip + offs
			if wiggle > 0.0:
				c += nrm * sin(float(s[4]) * 0.32 + _t * 26.0) * wiggle * (1.0 - age) * smoothstep(0.0, 0.4, float(i) / float(n))
			inner = c - nrm * hw
			outer = c + nrm * hw * 1.4
		var u := (float(s[4]) / 40.0) + _u_off + u_shift
		_vert(inner, u, lv + 0.0, age)
		_vert(outer, u, lv + 1.0, age)
		count += 1
	for i in range(count - 1):
		var a := start + i * 2
		_vidx.append_array([a, a + 1, a + 2, a + 1, a + 3, a + 2])


func _ribbon_path(layer: int, wmul: float, u_shift: float, age_add: float, offs: Vector2) -> void:
	## YOL şeridi (saplama, kırbaç): uç yolu Catmull-Rom ile yumuşatılır (seyrek örnekte köşe olmasın),
	## enine yön yol normali; kırbaçta baş (en taze uç) iğne gibi incelir.
	var n := _s.size()
	var P: Array = []   # [konum, zaman, baskı, yay]
	for i in range(n - 1):
		var p0: Vector2 = _s[maxi(0, i - 1)][1]
		var p1: Vector2 = _s[i][1]
		var p2: Vector2 = _s[i + 1][1]
		var p3: Vector2 = _s[mini(n - 1, i + 2)][1]
		var k := clampi(int(ceil(p1.distance_to(p2) / 2.0)), 1, 8)
		for j in k:
			var t := float(j) / float(k)
			var t2 := t * t
			var t3 := t2 * t
			var q := 0.5 * ((2.0 * p1) + (p2 - p0) * t + (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * t2 + (3.0 * p1 - p0 - 3.0 * p2 + p3) * t3)
			P.append([q, lerpf(float(_s[i][2]), float(_s[i + 1][2]), t), lerpf(float(_s[i][3]), float(_s[i + 1][3]), t), lerpf(float(_s[i][4]), float(_s[i + 1][4]), t)])
	var sl: Array = _s[n - 1]
	P.append([sl[1], sl[2], sl[3], sl[4]])
	var m := P.size()
	var start := _vp.size()
	var lv := float(layer) * 2.0
	for i in m:
		var e: Array = P[i]
		var age := clampf((_t - float(e[1])) / life + age_add, 0.0, 1.0)
		var a: Vector2 = P[maxi(0, i - 1)][0]
		var b: Vector2 = P[mini(m - 1, i + 1)][0]
		var tan := (b - a).normalized() if a.distance_to(b) > 0.01 else _last_dir
		_last_dir = tan
		var nrm := tan.orthogonal()
		var hw := path_w * float(e[2]) * (1.0 - 0.6 * pow(age, 1.4)) * wmul
		if style == "kirbac":
			hw *= 0.25 + 0.75 * smoothstep(0.0, 0.12, 1.0 - float(i) / float(m - 1))
		if twist:
			# v20 kurdele: genişlik yay boyunca kıvrılır (dönen şerit), kıvrımda ince bel
			hw *= 0.35 + 0.65 * absf(sin(float(e[3]) * 0.15 + _u_off * 3.0))
		var c: Vector2 = (e[0] as Vector2) + offs
		if wiggle > 0.0:
			c += nrm * sin(float(e[3]) * 0.32 + _t * 26.0) * wiggle * (1.0 - age) * smoothstep(0.0, 0.4, float(i) / float(m))
		var u := (float(e[3]) / 40.0) + _u_off + u_shift
		_vert(c - nrm * hw, u, lv + 0.0, age)
		_vert(c + nrm * hw * 1.4, u, lv + 1.0, age)
	for i in range(m - 1):
		var q := start + i * 2
		_vidx.append_array([q, q + 1, q + 2, q + 1, q + 3, q + 2])


func _draw() -> void:
	_vp.clear()
	_vuv.clear()
	_vcol.clear()
	_vidx.clear()
	if _s.size() >= 2:
		if layered >= 1:
			_ribbon(1, 1.35, 0.04, 0.31, 0.05)
		_ribbon(0, 1.0, 0.0, 0.0, 0.0)
		if layered >= 2 and mode == SWEEP:
			_ribbon(0, 0.32, 0.36, 0.53, 0.18)
		if inner_arc and mode == SWEEP:
			_ribbon(2, 0.5, -0.5, 0.43, 0.1)
		if ghost:
			# v20 kam: tayfsı ard görüntü, savuruşun arkasına ve yukarı kayarak süzülür
			var ga: Vector2 = _s[0][1]
			var gb: Vector2 = _s[_s.size() - 1][1]
			var gd := (gb - ga).normalized() if ga.distance_to(gb) > 1.0 else Vector2.RIGHT
			_ribbon(2, 1.15, 0.0, 0.37, 0.1, -gd * 14.0 + Vector2(0, -9.0))
		if double and mode == SWEEP:
			_ribbon(0, 0.45, -0.62, 0.71, 0.22)
		if double and mode == PATH:
			var a0: Vector2 = _s[0][1]
			var b0: Vector2 = _s[_s.size() - 1][1]
			var td0 := (b0 - a0).normalized() if a0.distance_to(b0) > 1.0 else Vector2.RIGHT
			_ribbon(0, 0.6, 0.0, 0.71, 0.18, td0.orthogonal() * 5.0 - td0 * 2.0)
		if echoes > 0 and mode == PATH:
			var a: Vector2 = _s[0][1]
			var b: Vector2 = _s[_s.size() - 1][1]
			var td := (b - a).normalized() if a.distance_to(b) > 1.0 else Vector2.RIGHT
			for k in echoes:
				# yankı: saplamanın arkada kalan soluk kopyaları (iz + sonraki görüntü), dönüşümlü üst/alt
				_ribbon(2, 0.7 - 0.22 * k, 0.0, 0.17 * (k + 1), 0.1 * (k + 1), -td * (9.0 + 9.0 * k) + td.orthogonal() * (3.5 * (k + 1) * (1 if k % 2 == 0 else -1)))
	for f in _flecks:
		var p: Vector2 = f[0]
		var vel: Vector2 = f[1]
		var age := clampf(float(f[3]) / float(f[2]), 0.0, 1.0)
		var sz: float = f[4]
		var typ: int = f[5]
		var d := vel.normalized() if vel.length() > 1.0 else Vector2.DOWN
		var L := sz * (1.6 + minf(vel.length(), 300.0) * 0.012) * (2.2 if typ == 2 else 1.0)
		var nrm := d.orthogonal() * sz * 0.5
		var head := p + d * L * 0.3
		var tail := p - d * L * 0.7
		var st := _vp.size()
		var u0 := float(typ) * 2.0
		_vert(tail - nrm, u0, 6.0, age)
		_vert(tail + nrm, u0, 7.0, age)
		_vert(head - nrm, u0 + 1.0, 6.0, age)
		_vert(head + nrm, u0 + 1.0, 7.0, age)
		_vidx.append_array([st, st + 1, st + 2, st + 1, st + 3, st + 2])
	_elem_draw()
	if _vidx.is_empty():
		return
	RenderingServer.canvas_item_add_triangle_array(get_canvas_item(), _vidx, _vp, _vcol, _vuv)


# ------------------------------------------------------------------ v20 unsur zerreleri
## tür: 3 alev dili, 4 buz kıymığı, 5 şimşek arkı (parça), 6 ruh dumanı / ayaz sisi, 7 yaprak
const U_RATE := {"od": 0.15, "ayaz": 0.16, "yildirim": 0.06, "kam": 0.1, "yersu": 0.1}


func _spawn_elem(base: Vector2, tip: Vector2) -> void:
	if _elem.size() > 90:
		return
	var dir := (tip - base).normalized()
	var prev: Vector2 = _s[_s.size() - 2][1]
	var tan := (tip - prev).normalized() if prev.distance_to(tip) > 0.01 else dir.orthogonal()
	# doğuş noktası: mürekkebin dış (bıçak ucu) yarısında
	var p := tip - dir * _rng.randf_range(0.0, (tip - base).length() * w_frac * 0.6) if mode == SWEEP else tip + tan.orthogonal() * _rng.randf_range(-path_w, path_w) * 1.5
	var big := 1.3 if style == "agir" else (0.75 if style == "hancer" else 1.0)
	match unsur:
		"od":
			_elem.append([p, Vector2(_rng.randf_range(-25, 25), _rng.randf_range(-150, -80)) + tan * 30.0, _rng.randf_range(0.2, 0.4), 0.0, _rng.randf_range(2.2, 6.0) * big, 3, clampf(-tan.x * 0.7, -0.8, 0.8) + _rng.randf_range(-0.3, 0.3), _rng.randf_range(-0.8, 0.8)])
			if _rng.randf() < 0.35:
				_flecks.append([p, Vector2(_rng.randf_range(-40, 40), _rng.randf_range(-160, -80)), _rng.randf_range(0.3, 0.6), 0.0, _rng.randf_range(0.5, 1.0), 2])
		"ayaz":
			if _rng.randf() < 0.72:
				_elem.append([p, tan * _rng.randf_range(20, 90) + Vector2(_rng.randf_range(-40, 40), _rng.randf_range(-70, 10)), _rng.randf_range(0.45, 0.75), 0.0, _rng.randf_range(3.0, 5.6) * big, 4, _rng.randf() * TAU, _rng.randf_range(-10, 10)])
				if _rng.randf() < 0.4:
					_flecks.append([p, tan * _rng.randf_range(30, 120) + Vector2(0, -40), _rng.randf_range(0.2, 0.4), 0.0, _rng.randf_range(0.5, 0.9), 2])
			else:
				_elem.append([p, Vector2(_rng.randf_range(-15, 15), _rng.randf_range(-25, 5)), _rng.randf_range(0.5, 0.8), 0.0, _rng.randf_range(5.0, 8.0) * big, 6, _rng.randf() * TAU, _rng.randf_range(-1, 1)])
		"yildirim":
			_flecks.append([p, tan * _rng.randf_range(60, 200) + tan.orthogonal() * _rng.randf_range(-120, 120), _rng.randf_range(0.15, 0.3), 0.0, _rng.randf_range(0.5, 1.1), 2])
		"kam":
			_elem.append([p, Vector2(_rng.randf_range(-20, 20), _rng.randf_range(-45, -15)) - tan * 15.0, _rng.randf_range(0.55, 0.9), 0.0, _rng.randf_range(6.0, 11.0) * big, 6, _rng.randf() * TAU, _rng.randf_range(-1.5, 1.5)])
			if _rng.randf() < 0.3:
				_flecks.append([p, Vector2(_rng.randf_range(-30, 30), _rng.randf_range(-90, -40)), _rng.randf_range(0.4, 0.7), 0.0, _rng.randf_range(0.5, 0.9), 2])
		"yersu":
			_elem.append([p, tan * _rng.randf_range(20, 70) + Vector2(_rng.randf_range(-30, 30), _rng.randf_range(-80, -20)), _rng.randf_range(0.7, 1.1), 0.0, _rng.randf_range(3.8, 5.8) * big, 7, _rng.randf() * TAU, _rng.randf_range(-8, 8)])


func _elem_step(delta: float) -> void:
	for f in _elem:
		f[3] = float(f[3]) + delta
		var v: Vector2 = f[1]
		match int(f[5]):
			3:
				v = v * maxf(0.0, 1.0 - 2.5 * delta) + Vector2(0, -90.0 * delta)
			4:
				v = v * maxf(0.0, 1.0 - 1.8 * delta) + Vector2(0, 300.0 * delta)
			6:
				v = v * maxf(0.0, 1.0 - 1.5 * delta) + Vector2(0, -20.0 * delta)
			7:
				v = v * maxf(0.0, 1.0 - 2.2 * delta) + Vector2(sin(float(f[3]) * 8.0 + float(f[6])) * 220.0 * delta, 130.0 * delta)
		f[1] = v
		f[0] = (f[0] as Vector2) + v * delta
		f[6] = float(f[6]) + float(f[7]) * delta
	var i := _elem.size() - 1
	while i >= 0:
		if float(_elem[i][3]) >= float(_elem[i][2]):
			_elem.remove_at(i)
		i -= 1
	# yıldırım: taze iz boyunca çatırdayan kısa arklar (sık yenilenir: titreşir)
	if unsur == "yildirim" and _s.size() > 3:
		_crk_t -= delta
		if _crk_t <= 0.0:
			_crk_t = 0.03
			for k in (3 if style == "agir" else 2):
				_crackle()


func _crackle() -> void:
	var n := _s.size()
	var fresh := 0
	while fresh < n and _t - float(_s[n - 1 - fresh][2]) < life * 0.6:
		fresh += 1
	if fresh < 2:
		return
	var s: Array = _s[n - 1 - _rng.randi_range(0, fresh - 1)]
	var base: Vector2 = s[0]
	var tip: Vector2 = s[1]
	var dir := (tip - base).normalized() if tip.distance_to(base) > 0.1 else Vector2.RIGHT
	var p := tip - dir * _rng.randf_range(0.0, (tip - base).length() * w_frac * 0.7) if mode == SWEEP else tip
	# ark izin dış kenarından dışa doğru (bıçak yönünde) ya da iz boyunca sıçrar
	var a := dir.angle() + _rng.randf_range(-1.3, 1.3)
	var L := _rng.randf_range(12.0, 26.0) * (1.3 if style == "agir" else 1.0)
	var segs := _rng.randi_range(3, 5)
	var q := p
	for j in segs:
		var nq := q + Vector2.from_angle(a + _rng.randf_range(-0.9, 0.9)) * (L / float(segs))
		_elem.append([(q + nq) * 0.5, Vector2.ZERO, _rng.randf_range(0.07, 0.13), 0.0, q.distance_to(nq), 5, (nq - q).angle(), 0.0])
		q = nq


func _elem_draw() -> void:
	for f in _elem:
		var p: Vector2 = f[0]
		var age := clampf(float(f[3]) / float(f[2]), 0.0, 1.0)
		var sz: float = f[4]
		var typ: int = f[5]
		var ax: Vector2   # u ekseni (kuyruk -> baş)
		var hw: float
		var L: float
		match typ:
			3:
				ax = Vector2.from_angle(-PI * 0.5 + float(f[6]) + sin(float(f[3]) * 18.0 + float(f[7])) * 0.22)
				L = sz * 2.9 * (1.0 - 0.55 * age)
				hw = sz * 0.9 * (1.0 - 0.35 * age)
			4:
				ax = Vector2.from_angle(float(f[6]))
				L = sz * 2.0
				hw = sz * 0.55
			5:
				ax = Vector2.from_angle(float(f[6]))
				L = sz + 2.0
				hw = 3.2
			6:
				ax = Vector2.from_angle(float(f[6]))
				L = sz * 2.0 * (1.0 + 0.8 * age)
				hw = L * 0.5
			_:
				ax = Vector2.from_angle(float(f[6]))
				L = sz * 2.0
				hw = sz * 0.6
		var nrm := ax.orthogonal() * hw
		var tail := p - ax * L * (0.25 if typ == 3 else 0.5)
		var head := p + ax * L * (0.75 if typ == 3 else 0.5)
		var st := _vp.size()
		var u0 := float(typ) * 2.0
		_vert(tail - nrm, u0, 6.0, age)
		_vert(tail + nrm, u0, 7.0, age)
		_vert(head - nrm, u0 + 1.0, 6.0, age)
		_vert(head + nrm, u0 + 1.0, 7.0, age)
		_vidx.append_array([st, st + 1, st + 2, st + 1, st + 3, st + 2])


# ------------------------------------------------------------------ kendiliğinden yay (düşman / boss savuruşu)
var _auto: Dictionary = {}


static func auto_arc(center: Vector2, radius: float, a0: float, a1: float, dur: float, p: int, facing := 1, heavy := false) -> InkTrail:
	## Kendi kendine süpürülen fırça hilali (FX.slash, boss arc_heavy yerine): merkez çevresinde a0 -> a1
	## (facing < 0: aynalanır), dur saniyede; sonra normal iz gibi erir.
	if FX.root == null:
		return null
	var t := acquire(FX.root)
	t.pal = p
	t.style = "agir" if heavy else "kilic"
	t.w_frac = 0.62 if heavy else 0.46
	t.life = 0.24 if heavy else 0.18
	t.layered = 1 if heavy else 0
	t.fleck_k = 1.4 if heavy else 0.9
	t._apply_mat()
	t._auto = {"c": center, "r": radius, "a0": a0, "a1": a1, "d": maxf(dur, 0.02), "f": 1 if facing >= 0 else -1, "k": 0.0}
	return t


func _auto_step(delta: float) -> void:
	var A := _auto
	var k0 := float(A["k"])
	var k1 := minf(1.0, k0 + delta / float(A["d"]))
	A["k"] = k1
	for i in range(1, 4):
		var k := lerpf(k0, k1, float(i) / 3.0)
		var e := 1.0 - pow(1.0 - k, 2.2)
		var a := lerpf(float(A["a0"]), float(A["a1"]), e)
		if int(A["f"]) < 0:
			a = PI - a
		var d := Vector2.from_angle(a)
		add(A["c"] + d * float(A["r"]) * 0.35, A["c"] + d * float(A["r"]))
	if k1 >= 1.0:
		_auto = {}
		done = true
