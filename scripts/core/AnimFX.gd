class_name AnimFX
extends Sprite2D
## Kare animasyonlu efekt: mürekkep karesi assets/fx/anim/<ad>_v2.png + anim_v2.json (tools/artgen/sus_fx.py).
## anim.json: eski (PVFX Foundry, CC0) piksel animasyonlarının kimlik / meta listesi; mürekkep karesi olmayan
## kimlikler FX.anim'de mürekkep sıçrantısına düşer (v30: piksel kareleri kaldırıldı).
## 20 FPS oynar; bitince silinir (loop ise `stop()` çağrılana dek döner). Işıktan etkilenmez,
## istenirse toplamalı karışım. `follow` verilirse o düğümü takip eder.

static var _meta: Dictionary = {}
static var _meta_v2: Dictionary = {}
static var _tex: Dictionary = {}
## mürekkep karesinin hücresi 4 kat yoğun: FX.anim ölçeği tex_k ile çarpar (dünya boyu eski kareyle aynı)
var tex_k := 1.0

var anim_name := ""
var fps := 20.0
var loop := false
var follow: Node2D
var follow_off := Vector2.ZERO
var speed := 1.0
var _t := 0.0
var _n := 1
var _stopping := false


static func meta() -> Dictionary:
	if _meta.is_empty():
		_meta = Data.load_json("res://assets/fx/anim/anim.json")
	return _meta


static func has(n: String) -> bool:
	return meta().has(n)


static func meta_v2() -> Dictionary:
	if _meta_v2.is_empty():
		var p := "res://assets/fx/anim/anim_v2.json"
		_meta_v2 = Data.load_json(p) if FileAccess.file_exists(p) else {"_": {}}
	return _meta_v2


func setup(n: String, additive := true) -> void:
	anim_name = n
	# yalnızca mürekkep karesi olan kimlikler (FX.anim diğerlerini mürekkep sıçrantısına çevirir)
	var m: Dictionary = meta_v2()[n]
	var key := n + "_v2"
	tex_k = 1.0 / float(m.get("texel", 4.0))
	if not _tex.has(key):
		_tex[key] = Data.tex("res://assets/fx/anim/%s.png" % key)
	texture = _tex[key]
	hframes = int(m["cols"])
	vframes = int(ceil(float(m["frames"]) / float(m["cols"])))
	_n = int(m["frames"])
	fps = float(m.get("fps", 20))
	loop = bool(m.get("loop", false))
	var piv: Array = m.get("pivot", [48, 64])
	var half := float(m.get("cell", 96)) * 0.5
	offset = Vector2(half - float(piv[0]), half - float(piv[1]))
	frame = 0
	z_index = 58
	var mat := CanvasItemMaterial.new()
	mat.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	if additive:
		mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	material = mat
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST if tex_k == 1.0 else CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS


func stop() -> void:
	_stopping = true


func _process(delta: float) -> void:
	if Prof.on:
		var t0 := Time.get_ticks_usec()
		_process_ic(delta)
		Prof.ekle(&"fx", t0)
		return
	_process_ic(delta)


func _process_ic(delta: float) -> void:
	if follow and is_instance_valid(follow):
		global_position = follow.global_position + follow_off
	_t += delta * fps * speed
	var f := int(_t)
	if f >= _n:
		if loop and not _stopping:
			_t -= float(_n)
			f = int(_t)
		else:
			queue_free()
			return
	frame = clampi(f, 0, _n - 1)
