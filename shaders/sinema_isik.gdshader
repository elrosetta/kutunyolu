// v43 sinematik ışık katmanı (Sinema.gd): altın varak / kor ışıması toplamalı karışır; aynı salınım ve belirme.
shader_type canvas_item;
render_mode blend_add;
#include "res://shaders/sinema_ortak.gdshaderinc"

void fragment() {
	vec2 uv = s43_sway_uv(UV, TEXTURE_PIXEL_SIZE * 20.0);
	vec4 c = texture(TEXTURE, uv);
	if (blur >= 0.35) {
		vec2 r = TEXTURE_PIXEL_SIZE * blur;
		c *= 0.12;
		for (int k = 0; k < 12; k++) {
			c += texture(TEXTURE, uv + r * S43_DISK[k].xy) * S43_DISK[k].z;
		}
	}
	vec2 rv = s43_reveal(UV, 0.0);
	vec4 o = c * tint * COLOR;
	COLOR = vec4(o.rgb * o.a * rv.x, 1.0);
}
