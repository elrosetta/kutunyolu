class_name SpriteAnim
extends Node2D
## JSON meta ile çalışan sprite animasyonu. Renk + normal map (CanvasTexture) ve ayrı bir
## parlama katmanı (ışıktan etkilenmeyen, toplamalı) kullanır. Kareler bir atlas satırındadır.

signal finished(anim_name: String)

var meta: Dictionary
var base: Sprite2D
var glow: Sprite2D
var mat: ShaderMaterial
var anim := ""
var frame := 0
var speed := 1.0
var manual := false
var facing := 1
var texel := 1.0  # doku yoğunluğu (meta "texel"): 1.5 = 1.5x piksel; sprite 1/texel ölçekle çizilir, dünya boyu aynı
var _t := 0.0


func setup(sprite_name: String) -> void:
	meta = Data.sprite(sprite_name)
	texel = float(meta.get("texel", 1.0))
	base = Sprite2D.new()
	base.texture = meta["tex"]
	base.region_enabled = true
	base.centered = false
	mat = ShaderMaterial.new()
	mat.shader = Game.toon_shader
	base.material = mat
	add_child(base)
	if meta.get("glow_tex") != null:
		glow = Sprite2D.new()
		glow.texture = meta["glow_tex"]
		glow.region_enabled = true
		glow.centered = false
		var gm := CanvasItemMaterial.new()
		gm.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
		gm.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
		glow.material = gm
		glow.self_modulate = Color(1.6, 1.6, 1.6)
		add_child(glow)
	set_facing(1)
	play(meta["anims"].keys()[0])


func has_anim(n: String) -> bool:
	return meta["anims"].has(n)


func play(n: String, restart := false) -> void:
	if not has_anim(n):
		return
	if n == anim and not restart:
		return
	anim = n
	frame = 0
	_t = 0.0
	manual = false
	_apply()


func show_frame(n: String, f: int) -> void:
	## Saldırı gibi zamanlaması kodla yönetilen animasyonlar için doğrudan kare seçimi.
	if not has_anim(n):
		return
	anim = n
	manual = true
	frame = clampi(f, 0, int(meta["anims"][n]["frames"]) - 1)
	_apply()


func frame_count(n: String) -> int:
	return int(meta["anims"][n]["frames"]) if has_anim(n) else 1


func set_facing(dir: int) -> void:
	facing = 1 if dir >= 0 else -1
	var cell: Array = meta["cell"]
	var org: Array = meta["origin"]
	var x := -float(org[0]) if facing > 0 else -(float(cell[0]) - float(org[0]))
	base.flip_h = facing < 0
	base.scale = Vector2.ONE / texel
	base.position = Vector2(x, -float(org[1])) / texel
	if glow:
		glow.flip_h = base.flip_h
		glow.scale = base.scale
		glow.position = base.position


func set_flash(v: float) -> void:
	mat.set_shader_parameter("flash", v)


func set_tint(c: Color) -> void:
	mat.set_shader_parameter("tint", c)


func _process(delta: float) -> void:
	if anim == "" or manual:
		return
	var a: Dictionary = meta["anims"][anim]
	_t += delta * float(a["fps"]) * speed
	while _t >= 1.0:
		_t -= 1.0
		frame += 1
		if frame >= int(a["frames"]):
			if a["loop"]:
				frame = 0
			else:
				frame = int(a["frames"]) - 1
				_t = 0.0
				_apply()
				finished.emit(anim)
				return
	_apply()


func _apply() -> void:
	var a: Dictionary = meta["anims"][anim]
	var cell: Array = meta["cell"]
	var r := Rect2(frame * float(cell[0]), float(a["row"]) * float(cell[1]), float(cell[0]), float(cell[1]))
	base.region_rect = r
	if glow:
		glow.region_rect = r


func anchor(key: String) -> Variant:
	## Ayak noktasına göre çapa konumu (yöne göre aynalanmış); yoksa null.
	var a: Dictionary = meta["anims"][anim]
	var data: Array = a["data"]
	if frame >= data.size():
		return null
	var d: Dictionary = data[frame]
	if not d.has(key):
		return null
	return Vector2(float(d[key][0]) * facing, float(d[key][1]))


func anchor_angle(key: String) -> float:
	var a: Dictionary = meta["anims"][anim]
	var data: Array = a["data"]
	if frame >= data.size():
		return 0.0
	var d: Dictionary = data[frame]
	var ang := float(d.get(key, 0.0))
	return ang if facing > 0 else PI - ang
