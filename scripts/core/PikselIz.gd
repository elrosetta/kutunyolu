class_name PikselIz
extends RefCounted
## Stil v2 piksel denetimi kaydı (tools/tests/piksel_tara.gd, -- --piksel_tara): v2'de hâlâ piksel görünümlü
## bir yola (v1 çizim dalı, v1 doku geri dönüşü) girilince anahtar ve sayısı kaydedilir. Denetim kapalıyken
## (varsayılan) iz() yalnızca bir bool sınar; oyun davranışı değişmez.

static var acik := false
static var kayit: Dictionary = {}


static func iz(anahtar: String) -> void:
	if not acik or Data.stil == "v1":
		return
	kayit[anahtar] = int(kayit.get(anahtar, 0)) + 1
