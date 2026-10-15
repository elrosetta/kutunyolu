class_name SlashFX
extends Sprite2D
## Kesik / darbe sprite'ı (tools/artgen/slashfx.py ile üretilir): assets/fx/slash/<ad>.png, kareler yan yana.
## Beyaz çizilir, silah rengiyle boyanır, toplamalı ve ışıksız. Bitince silinir. `follow` ile düğümü izler.

static var _meta: Dictionary = {}
static var _tex: Dictionary = {}

var fps := 26.0
var follow: Node2D
var follow_off := Vector2.ZERO
var _t := 0.0
var _n := 1


static func meta() -> Dictionary:
	if _meta.is_empty():
		_meta = Data.load_json("res://assets/fx/slash/slash.json")
	return _meta


static func has(n: String) -> bool:
	return meta().has(n)


func setup(n: String, additive := true, pivot := Vector2(-1, -1)) -> void:
	var m: Dictionary = meta()[n]
	if not _tex.has(n):
		_tex[n] = Data.tex("res://assets/fx/slash/%s.png" % n)
	texture = _tex[n]
	_n = int(m["frames"])
	hframes = _n
	vframes = 1
	frame = 0
	var w := float(m["w"])
	var h := float(m["h"])
	# varsayılan pivot: merkez; saplama çizgisinde sol-orta
	if pivot.x >= 0.0:
		offset = Vector2(w / 2.0 - pivot.x * w, h / 2.0 - pivot.y * h)
	z_index = 57
	var mat := CanvasItemMaterial.new()
	mat.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	if additive:
		mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	material = mat
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST


func _process(delta: float) -> void:
	if follow and is_instance_valid(follow):
		global_position = follow.global_position + follow_off
	_t += delta * fps
	var f := int(_t)
	if f >= _n:
		queue_free()
		return
	frame = f
