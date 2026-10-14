class_name AnimFX
extends Sprite2D
## Kare animasyonlu efekt (PVFX Foundry, CC0): assets/fx/anim/<ad>.png + anim.json.
## 20 FPS oynar; bitince silinir (loop ise `stop()` çağrılana dek döner). Işıktan etkilenmez,
## istenirse toplamalı karışım. `follow` verilirse o düğümü takip eder.

static var _meta: Dictionary = {}
static var _tex: Dictionary = {}

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


func setup(n: String, additive := true) -> void:
	anim_name = n
	var m: Dictionary = meta()[n]
	if not _tex.has(n):
		_tex[n] = load("res://assets/fx/anim/%s.png" % n)
	texture = _tex[n]
	hframes = int(m["cols"])
	vframes = int(ceil(float(m["frames"]) / float(m["cols"])))
	_n = int(m["frames"])
	fps = float(m.get("fps", 20))
	loop = bool(m.get("loop", false))
	var piv: Array = m.get("pivot", [48, 64])
	offset = Vector2(48.0 - float(piv[0]), 48.0 - float(piv[1]))
	frame = 0
	z_index = 58
	var mat := CanvasItemMaterial.new()
	mat.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	if additive:
		mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	material = mat
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST


func stop() -> void:
	_stopping = true


func _process(delta: float) -> void:
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
