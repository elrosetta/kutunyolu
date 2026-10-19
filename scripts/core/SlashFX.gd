class_name SlashFX
extends RefCounted
## Kesik / darbe kimliklerinin meta bilgisi (assets/fx/slash/slash.json: kare sayısı, hücre boyu). Eski piksel kesik
## sprite'ları (tools/artgen/slashfx.py) v30'da kaldırıldı; kimlikler FX.slash_sprite / FX.decal'de mürekkebe çevrilir
## (yayın yarıçapı "w" ile ölçülür).

static var _meta: Dictionary = {}


static func meta() -> Dictionary:
	if _meta.is_empty():
		_meta = Data.load_json("res://assets/fx/slash/slash.json")
	return _meta


static func has(n: String) -> bool:
	return meta().has(n)
