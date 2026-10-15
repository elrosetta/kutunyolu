extends Node
## Oyun durumu: giriş haritası, koşu (run) verisi, kalıcı kayıt (kilitler, parşömenler, Kut bankası),
## kamera sarsıntısı/itişi, vuruş duraklaması ve ağır çekim.

const SAVE_PATH := "user://kayit.json"
const LAYER_WORLD := 1
const LAYER_PLAYER := 2
const LAYER_ENEMY := 4
const LAYER_PLATFORM := 8

## Her koşuda açık olan eşyalar; diğerleri parşömenle Demirci'de açılır.
const BASE_UNLOCKED := ["alp_kilici", "turk_yayi", "kara_barut", "yuvarlak_kalkan", "pala", "coban_sapani"]

## Tanrı lütufları (sunaktan alınır; yurda dönene dek sürer, en çok 3)
const LUTUF := {
	"tengri": ["Tengri'nin Yıldırımı", "Darbeler %22 şansla yakındaki düşmana şimşekle sıçrar.", [0.7, 0.85, 1.0]],
	"ulgen": ["Ülgen'in Işığı", "Her öldürmede %3 can.", [1.0, 0.95, 0.6]],
	"umay": ["Umay'ın Kanadı", "Havada iki kez daha zıpla.", [0.6, 1.0, 1.0]],
	"erlik": ["Erlik'in Gölgesi", "Hasar +%35; en yüksek can -%20.", [0.7, 0.3, 0.9]],
	"kayra": ["Kayra'nın Kutu", "Kut iki kat hızlı dolar.", [0.45, 0.93, 1.0]],
	"yer_sub": ["Yer-Sub Zırhı", "Alınan hasar -%25.", [0.55, 0.85, 0.45]],
	"ay_ata": ["Ay Ata'nın Gözü", "Kritik şansı +%10.", [0.85, 0.9, 1.0]],
	"gun_ana": ["Gün Ana'nın Közü", "Darbeler %25 şansla tutuşturur.", [1.0, 0.6, 0.3]],
}
## Boss arenaları: bu derinlik bitince (Kut Kapısı) önce boss, sonra yurt
const BOSS_AFTER := {2: "kara_boru_han"}

## Umay Ana'nın kalıcı armağanları: Kut bankasıyla alınır (Dead Cells "Collector" mantığı).
## id: [ad, açıklama, [seviye maliyetleri...]]
const UMAY := {
	"sise": ["Umay'ın Şişesi", "Koşuya +1 şifa şişesiyle başla.", [30, 70]],
	"can": ["Kayın Özü", "En yüksek can +%10.", [25, 45, 75]],
	"kut_koruma": ["Ruh Düğümü", "Ölünce taşıdığın Kut'un %30 / %60'ı Umay'a ulaşır.", [40, 90]],
	"altin": ["Ata Kesesi", "Koşuya +60 altınla başla.", [20, 40]],
	"kut_hizi": ["Bozkurt Çağrısı", "Kut gücü %20 daha hızlı dolar.", [35, 70]],
	"silah": ["Demirci Dostu", "Başlangıç silahı bir kademe üstün döner.", [60]],
}

var toon_shader: Shader = preload("res://shaders/toon_light.gdshader")
var meta: Dictionary = {}
var run: Dictionary = {}
var camera: Camera2D
var shake_amount := 0.0
var kick_off := Vector2.ZERO
var _hitstop_until := 0.0
var _slow_until := 0.0
var _slow_scale := 1.0
var _zoom := 0.0


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_setup_input()
	load_meta()


func _process(delta: float) -> void:
	var now := Time.get_ticks_msec() / 1000.0
	var ts := 1.0
	if now < _hitstop_until:
		ts = 0.05
	elif now < _slow_until:
		ts = _slow_scale
	if get_tree().paused:
		ts = 1.0
	Engine.time_scale = ts
	var rd := delta / maxf(0.05, ts)
	if camera:
		_zoom = lerpf(_zoom, 0.0, clampf(rd * 9.0, 0.0, 1.0))
		camera.zoom = Vector2.ONE * (1.0 + _zoom)
		kick_off = kick_off.lerp(Vector2.ZERO, clampf(rd * 14.0, 0.0, 1.0))
		var off := kick_off
		if shake_amount > 0.05:
			off += Vector2(randf_range(-1, 1), randf_range(-1, 1)) * shake_amount
			shake_amount = move_toward(shake_amount, 0.0, rd * 30.0)
		camera.offset = off


func shake(amount: float) -> void:
	shake_amount = maxf(shake_amount, amount)


func kick(dir: Vector2, amount := 4.0) -> void:
	## Kamera itişi: darbe yönünde kısa bir kayma, hızla geri döner.
	if dir.length() > 0.01:
		kick_off += dir.normalized() * amount


func zoom_punch(amount := 0.05) -> void:
	## Kritik / ağır öldürmede kamera bir an yaklaşır
	_zoom = maxf(_zoom, amount)


func hitstop(duration: float) -> void:
	## Vuruş duraklaması: gerçek zamanlı; tekrar tekrar çağrılınca uzar.
	var now := Time.get_ticks_msec() / 1000.0
	_hitstop_until = maxf(_hitstop_until, now + duration)


func slowmo(scale_v: float, duration: float) -> void:
	## Ağır çekim (kritik, öldürücü vuruş, savuşturma).
	var now := Time.get_ticks_msec() / 1000.0
	_slow_scale = scale_v
	_slow_until = maxf(_slow_until, now + duration)


func new_run() -> void:
	var start_melee := ItemGen.roll("alp_kilici", 0, "demir", 0)
	var start_bow := ItemGen.roll("turk_yayi", 0, "demir", 0)
	var start_bomb := ItemGen.roll("kara_barut", 0, "demir", 0)
	if umay_level("silah") > 0:
		start_melee = ItemGen.roll("alp_kilici", 1, "tunc", 1)
	var mhp := 100.0 * (1.0 + 0.1 * umay_level("can"))
	run = {
		"hp": mhp, "max_hp": mhp, "gold": 60 * umay_level("altin"), "kut": 0, "flasks": 2 + umay_level("sise"), "max_flasks": 2 + umay_level("sise"),
		"ongun": {"kurt": 0, "kartal": 0, "ayi": 0},
		"slots": {"melee": start_melee, "second": start_bow, "g1": start_bomb, "g2": {}},
		"kills": 0, "time": 0.0, "tier": 0, "depth": 1, "scrolls": 0, "lutuf": [], "boss_done": [],
	}


func umay_level(id: String) -> int:
	return int(meta.get("umay", {}).get(id, 0))


func umay_cost(id: String) -> int:
	## -1: en üst seviye
	var lv := umay_level(id)
	var costs: Array = UMAY[id][2]
	return int(costs[lv]) if lv < costs.size() else -1


func umay_buy(id: String) -> bool:
	var c := umay_cost(id)
	if c < 0 or int(meta.get("kut_bank", 0)) < c:
		return false
	meta["kut_bank"] = int(meta["kut_bank"]) - c
	var u: Dictionary = meta.get("umay", {})
	u[id] = umay_level(id) + 1
	meta["umay"] = u
	save_meta()
	return true


func lose_run_kut() -> int:
	## Ölüm: taşınan Kut yitirilir; Ruh Düğümü bir kısmını Umay'a ulaştırır. Dönen: kurtarılan miktar.
	if run.is_empty():
		return 0
	var keep: float = [0.0, 0.3, 0.6][clampi(umay_level("kut_koruma"), 0, 2)]
	var saved := int(floor(int(run.get("kut", 0)) * keep))
	meta["kut_bank"] = int(meta.get("kut_bank", 0)) + saved
	run["kut_lost"] = int(run.get("kut", 0)) - saved
	run["kut"] = 0
	save_meta()
	return saved


func biome_for_depth(depth: int) -> Dictionary:
	## Derinlik aralıklarına göre biyom (world.json "depths"); eşleşme yoksa en derin biyom
	var last: Dictionary = {}
	for b in Data.world["biomes"]:
		if not b.get("impl", false):
			continue
		var r: Array = b.get("depths", [0, 0])
		if depth >= int(r[0]) and depth <= int(r[1]):
			return b
		if int(r[1]) >= 99:
			last = b
	return last if not last.is_empty() else Data.world["biomes"][0]


func next_depth() -> void:
	## Kut Kapısı'ndan geçiş: eşyalar, ongunlar ve can korunur; şişeler dolar; düşmanlar sertleşir.
	run["depth"] = int(run.get("depth", 1)) + 1
	run["tier"] = mini(5, int(run.get("tier", 0)) + 1)
	run["flasks"] = int(run["max_flasks"])
	run["hp"] = minf(float(run["max_hp"]), float(run["hp"]) + float(run["max_hp"]) * 0.25)


func has_lutuf(id: String) -> bool:
	return not run.is_empty() and id in run.get("lutuf", [])


func grant_lutuf(id: String) -> void:
	var l: Array = run.get("lutuf", [])
	if id in l:
		return
	l.append(id)
	run["lutuf"] = l
	if id == "erlik":
		run["max_hp"] = float(run["max_hp"]) * 0.8
		run["hp"] = minf(float(run["hp"]), float(run["max_hp"]))


func ongun_mult(ongun: String) -> float:
	if run.is_empty():
		return 1.0
	return 1.0 + 0.15 * float(run["ongun"].get(ongun, 0))


func item_onguns(it: Dictionary) -> Array:
	## Eşyanın ongunları: bir ya da iki renk (Dead Cells'in çift renkli eşyaları).
	var out: Array = []
	var o: Variant = it.get("ongun", "")
	if o is Array:
		out = (o as Array).duplicate()
	elif String(o) != "":
		out.append(String(o))
	var o2 := String(it.get("ongun2", ""))
	if o2 != "" and not (o2 in out):
		out.append(o2)
	return out


func item_best_ongun(it: Dictionary) -> String:
	## Çift renkli eşya hangi ongun daha yüksekse ona göre güçlenir; eşitlikte ilk renk.
	var best := ""
	var best_lv := -1
	for o in item_onguns(it):
		var lv := int(run.get("ongun", {}).get(o, 0)) if not run.is_empty() else 0
		if lv > best_lv:
			best_lv = lv
			best = o
	return best if best != "" else "kurt"


func item_mult(it: Dictionary) -> float:
	return ongun_mult(item_best_ongun(it))


func bank_run_kut() -> void:
	## Koşu bitince (ölüm ya da kapı) toplanan Kut, Umay'ın bankasına eklenir.
	if run.is_empty():
		return
	meta["kut_bank"] = int(meta.get("kut_bank", 0)) + int(run.get("kut", 0))
	run["kut"] = 0
	save_meta()


func is_unlocked(id: String) -> bool:
	## Temel eşyalar baştan açık; yalnızca gelişmiş sürümler (upgrade_of) parşömenle açılır.
	if id in BASE_UNLOCKED or id in meta.get("unlocked", []):
		return true
	var base := Data.find_item(id)
	return not base.is_empty() and not base.has("upgrade_of")


func unlock_cost(id: String) -> int:
	var base := Data.find_item(id)
	var c := 12
	if base.get("cat", "") == "weapons":
		c = 14 + int(float(base.get("dmg", 8)) * 0.4)
	elif base.get("cat", "") == "gadgets":
		c = 12
	else:
		c = 10
	return c


func add_blueprint(id: String) -> bool:
	## Parşömen toplandı; henüz açılmadı. true: yeni.
	var bps: Array = meta.get("blueprints", [])
	if id in bps or is_unlocked(id):
		return false
	bps.append(id)
	meta["blueprints"] = bps
	save_meta()
	return true


func unlock(id: String) -> bool:
	var cost := unlock_cost(id)
	if int(meta.get("kut_bank", 0)) < cost:
		return false
	meta["kut_bank"] = int(meta["kut_bank"]) - cost
	var ul: Array = meta.get("unlocked", [])
	ul.append(id)
	meta["unlocked"] = ul
	var bps: Array = meta.get("blueprints", [])
	bps.erase(id)
	meta["blueprints"] = bps
	save_meta()
	return true


func load_meta() -> void:
	meta = {"runs": 0, "wins": 0, "kut_bank": 0, "unlocked": [], "blueprints": [], "best_depth": 1}
	if FileAccess.file_exists(SAVE_PATH):
		var f := FileAccess.open(SAVE_PATH, FileAccess.READ)
		var d: Variant = JSON.parse_string(f.get_as_text())
		if d is Dictionary:
			meta.merge(d, true)


func save_meta() -> void:
	var f := FileAccess.open(SAVE_PATH, FileAccess.WRITE)
	if f:
		f.store_string(JSON.stringify(meta))


# ------------------------------------------------------------------ giriş haritası
func _bind(action: String, keys: Array, mouse := -1, buttons: Array = [], axes: Array = []) -> void:
	if not InputMap.has_action(action):
		InputMap.add_action(action, 0.3)
	for k in keys:
		var e := InputEventKey.new()
		e.physical_keycode = k
		InputMap.action_add_event(action, e)
	if mouse >= 0:
		var m := InputEventMouseButton.new()
		m.button_index = mouse
		InputMap.action_add_event(action, m)
	for b in buttons:
		var j := InputEventJoypadButton.new()
		j.button_index = b
		InputMap.action_add_event(action, j)
	for ax in axes:
		var a := InputEventJoypadMotion.new()
		a.axis = ax[0]
		a.axis_value = ax[1]
		InputMap.action_add_event(action, a)


func _setup_input() -> void:
	_bind("sol", [KEY_A, KEY_LEFT], -1, [JOY_BUTTON_DPAD_LEFT], [[JOY_AXIS_LEFT_X, -1.0]])
	_bind("sag", [KEY_D, KEY_RIGHT], -1, [JOY_BUTTON_DPAD_RIGHT], [[JOY_AXIS_LEFT_X, 1.0]])
	_bind("yukari", [KEY_W, KEY_UP], -1, [JOY_BUTTON_DPAD_UP], [[JOY_AXIS_LEFT_Y, -1.0]])
	_bind("asagi", [KEY_S, KEY_DOWN], -1, [JOY_BUTTON_DPAD_DOWN], [[JOY_AXIS_LEFT_Y, 1.0]])
	_bind("zipla", [KEY_SPACE], -1, [JOY_BUTTON_A])
	_bind("saldiri1", [KEY_J], MOUSE_BUTTON_LEFT, [JOY_BUTTON_X])
	_bind("saldiri2", [KEY_K], MOUSE_BUTTON_RIGHT, [JOY_BUTTON_Y])
	_bind("yuvarlan", [KEY_L, KEY_SHIFT], -1, [JOY_BUTTON_B])
	_bind("techizat1", [KEY_U], -1, [JOY_BUTTON_LEFT_SHOULDER])
	_bind("techizat2", [KEY_I], -1, [JOY_BUTTON_RIGHT_SHOULDER])
	_bind("kut", [KEY_F], -1, [JOY_BUTTON_RIGHT_STICK])
	_bind("sise", [KEY_Q], -1, [JOY_BUTTON_LEFT_STICK])
	_bind("etkiles", [KEY_E], -1, [JOY_BUTTON_BACK])
	_bind("duraklat", [KEY_ESCAPE, KEY_P], -1, [JOY_BUTTON_START])
