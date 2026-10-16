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
var ink := InkUI.on()   # piksel denetimi: v2'de ad / balon yazıları InkUI'ye düşer (PixUI v2 yönlendirmesi)


func _ready() -> void:
	z_index = 3
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
	PixUI.text(self, Vector2(-80, -101), display_name, PixUI.TEXT, 1, HORIZONTAL_ALIGNMENT_CENTER, 160, 2)
	if id == "ozan" and not Adlar.pending().is_empty():
		var by := roundf(-132.0 + sin(_t * 4.0) * 2.0)
		PixUI.text(self, Vector2(-80, by), "! destan: %d" % Adlar.pending().size(), PixUI.GOLD, 1, HORIZONTAL_ALIGNMENT_CENTER, 160, 2)
	if near:
		var y := roundf(-116.0 + sin(_t * 5.0) * 2.0)
		PixUI.key_cap(self, Vector2(-5, y), "E")
