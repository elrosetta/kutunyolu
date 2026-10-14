extends Node
## Veri ve görsel önbelleği: JSON verileri, sprite meta bilgisi, CanvasTexture'lar (renk + normal map).

var items: Dictionary = {}
var world: Dictionary = {}
var story: Dictionary = {}
var weapon_meta: Dictionary = {}
var decor_meta: Dictionary = {}
var tile_meta: Dictionary = {}
var weapon_tex: CanvasTexture
var weapon_glow: Texture2D
var _sprites: Dictionary = {}
var _decor: Dictionary = {}


func _ready() -> void:
	items = load_json("res://data/items.json")
	world = load_json("res://data/world.json")
	story = load_json("res://data/story.json")
	weapon_meta = load_json("res://assets/weapons/weapons.json")
	decor_meta = load_json("res://assets/decor/decor.json")
	tile_meta = load_json("res://assets/tiles/otuken.json")
	weapon_tex = canvas_tex("res://assets/weapons/weapons.png", "res://assets/weapons/weapons_n.png")
	weapon_glow = load("res://assets/weapons/weapons_e.png")


func load_json(path: String) -> Dictionary:
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		push_error("JSON açılamadı: %s" % path)
		return {}
	var parsed: Variant = JSON.parse_string(f.get_as_text())
	if parsed == null or not (parsed is Dictionary):
		push_error("JSON çözümlenemedi: %s" % path)
		return {}
	return parsed


func canvas_tex(diffuse: String, normal: String) -> CanvasTexture:
	var ct := CanvasTexture.new()
	ct.diffuse_texture = load(diffuse)
	if ResourceLoader.exists(normal):
		ct.normal_texture = load(normal)
	ct.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	return ct


func sprite(sprite_name: String) -> Dictionary:
	if _sprites.has(sprite_name):
		return _sprites[sprite_name]
	var meta := load_json("res://assets/sprites/%s.json" % sprite_name)
	meta["tex"] = canvas_tex("res://assets/sprites/%s.png" % sprite_name, "res://assets/sprites/%s_n.png" % sprite_name)
	var gp := "res://assets/sprites/%s_e.png" % sprite_name
	meta["glow_tex"] = load(gp) if ResourceLoader.exists(gp) else null
	_sprites[sprite_name] = meta
	return meta


func decor(decor_name: String) -> Dictionary:
	if _decor.has(decor_name):
		return _decor[decor_name]
	var d: Dictionary = decor_meta.get(decor_name, {}).duplicate()
	d["tex"] = canvas_tex("res://assets/decor/%s.png" % decor_name, "res://assets/decor/%s_n.png" % decor_name)
	var gp := "res://assets/decor/%s_e.png" % decor_name
	d["glow_tex"] = load(gp) if ResourceLoader.exists(gp) else null
	_decor[decor_name] = d
	return d


func find_item(id: String) -> Dictionary:
	for cat in ["weapons", "shields", "gadgets"]:
		for it in items[cat]:
			if it["id"] == id:
				var d: Dictionary = it.duplicate(true)
				d["cat"] = cat
				return d
	return {}


func material_def(id: String) -> Dictionary:
	for m in items["materials"]:
		if m["id"] == id:
			return m
	return items["materials"][0]


func has_weapon_sprite(item_id: String) -> bool:
	return weapon_meta.has("items") and weapon_meta["items"].has(item_id)


func weapon_region(item_id: String, mat_id: String) -> Rect2:
	var cell: Array = weapon_meta["cell"]
	var row := int(weapon_meta["items"][item_id]["row"])
	var col: int = weapon_meta["materials"].find(mat_id)
	if col < 0:
		col = 0
	return Rect2(col * cell[0], row * cell[1], cell[0], cell[1])


func weapon_pivot(item_id: String) -> Vector2:
	var p: Array = weapon_meta["items"][item_id]["pivot"]
	return Vector2(p[0], p[1])


func enemy_def(id: String) -> Dictionary:
	for e in world["enemies"]:
		if e["id"] == id:
			return e
	return {}
