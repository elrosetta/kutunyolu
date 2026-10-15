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
	# piksel yazı tipi (tools/artgen/pixfont.py): 13 = 1x, 26 = 2x, 39 = 3x; yalnızca tam sayı ölçek
	pixel_font = load("res://assets/ui/pixel.fnt")
	if pixel_font:
		pixel_font.fixed_size_scale_mode = TextServer.FIXED_SIZE_SCALE_INTEGER_ONLY
		pixel_font.antialiasing = TextServer.FONT_ANTIALIASING_NONE
	else:
		push_error("Piksel yazı tipi yüklenemedi")


var pixel_font: FontFile
var _icon_cache: Dictionary = {}


func weapon_icon_rect(item_id: String, mat_id: String) -> Rect2:
	## Silah karesinin dolu bölgesi (arayüz simgeleri için sıkı kırpma); önbellekli.
	var key := item_id + "/" + mat_id
	if _icon_cache.has(key):
		return _icon_cache[key]
	var reg := weapon_region(item_id, mat_id)
	var r := reg
	var img: Image = weapon_tex.diffuse_texture.get_image() if weapon_tex and weapon_tex.diffuse_texture else null
	if img:
		if img.is_compressed():
			img.decompress()
		var used := img.get_region(Rect2i(reg)).get_used_rect()
		if used.size.x > 0:
			r = Rect2(reg.position + Vector2(used.position), Vector2(used.size))
	_icon_cache[key] = r
	return r


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
