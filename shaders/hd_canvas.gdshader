// Gölgelendiricisi olmayan sprite'lar (arka plan katmanları, oklar, arayüz) için HD doku örneklemesi.
shader_type canvas_item;

#include "res://shaders/hdpix.gdshaderinc"

varying vec4 vcol;

void vertex() {
	vcol = COLOR;
}

void fragment() {
	vec4 c = texture(TEXTURE, UV);
	if (hd_level > 0) {
		HD_SAMPLE(c, TEXTURE, UV, TEXTURE_PIXEL_SIZE);
	}
	COLOR = c * vcol;
}
