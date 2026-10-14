class_name NPC
extends Node2D
## Yurt sakini: Umay Ana / Demirci Kam Kuzgun / Ozan Bilge Kopuz. Oyuncuya döner, yaklaşınca "E" balonu çıkar,
## konuşunca kısa "talk" animasyonu oynar. Etkileşimi Level yönetir (npc_requested sinyali).

var id := ""
var display_name := ""
var level: Node
var anim: SpriteAnim
var near := false
var talk_t := 0.0
var _t := 0.0
var font: Font


func _ready() -> void:
	z_index = 3
	font = ThemeDB.fallback_font
	anim = SpriteAnim.new()
	add_child(anim)
	anim.setup("npc_" + id)
	anim.set_facing(1)
	anim.play("idle")
	anim.speed = 0.8
	if level:
		var col := Color(0.6, 0.95, 1.0) if id == "umay" else (Color(1.0, 0.6, 0.3) if id == "demirci" else Color(1.0, 0.85, 0.5))
		level.add_light(Vector2(0, -40), col, 110.0, 0.55, self)


func talk() -> void:
	talk_t = 1.2
	anim.play("talk", true)


func _process(delta: float) -> void:
	_t += delta
	talk_t -= delta
	var pl: Node = level.player if level else null
	if pl:
		# yüzünü oyuncuya dön (çizim sola bakar: oyuncu soldaysa facing 1)
		anim.set_facing(1 if pl.global_position.x <= global_position.x else -1)
		near = absf(pl.global_position.x - global_position.x) < 30.0 and absf(pl.global_position.y - global_position.y) < 40.0
	if talk_t <= 0.0 and anim.anim != "idle":
		anim.play("idle")
	queue_redraw()


func _draw() -> void:
	var w := font.get_string_size(display_name, HORIZONTAL_ALIGNMENT_LEFT, -1, 7).x
	draw_string_outline(font, Vector2(-w / 2.0, -92), display_name, HORIZONTAL_ALIGNMENT_LEFT, -1, 7, 3, Color(0.05, 0.03, 0.08, 0.9))
	draw_string(font, Vector2(-w / 2.0, -92), display_name, HORIZONTAL_ALIGNMENT_LEFT, -1, 7, Color(0.96, 0.93, 0.86))
	if near:
		var y := -104.0 + sin(_t * 5.0) * 2.0
		draw_rect(Rect2(-7, y - 8, 14, 11), Color(0.07, 0.05, 0.1, 0.92))
		draw_rect(Rect2(-7, y - 8, 14, 11), Color(1.0, 0.83, 0.42), false, 1.0)
		draw_string(font, Vector2(-3, y + 1), "E", HORIZONTAL_ALIGNMENT_LEFT, -1, 8, Color(1.0, 0.83, 0.42))
