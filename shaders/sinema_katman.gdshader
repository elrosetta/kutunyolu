// v43 sinematik katmanı (Sinema.gd): odak bulanıklığı, rüzgâr salınımı, mürekkeple belirme (sinema_ortak.gdshaderinc).
shader_type canvas_item;
#include "res://shaders/sinema_ortak.gdshaderinc"

void fragment() {
	vec2 uv = s43_sway_uv(UV, TEXTURE_PIXEL_SIZE * 40.0);
	vec4 c = texture(TEXTURE, uv);
	if (blur >= 0.35) {
		vec2 r = TEXTURE_PIXEL_SIZE * blur;
		c *= 0.12;
		for (int k = 0; k < 12; k++) {
			c += texture(TEXTURE, uv + r * S43_DISK[k].xy) * S43_DISK[k].z;
		}
	}
	float lum = dot(c.rgb, vec3(0.299, 0.587, 0.114));
	vec2 rv = s43_reveal(UV, c.a > 0.01 ? lum : 1.0);
	c.rgb *= 1.0 - rv.y * 0.4;
	c.a *= rv.x;
	COLOR = c * tint * COLOR;
}
