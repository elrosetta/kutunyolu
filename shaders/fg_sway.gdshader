// Stil v2 ön plan siluet şeritleri (ForegroundV2): rüzgârda salınan koyu otlar / sarkan dallar.
// Salınım UV kaydırmasıyla yapılır (dokunun "kök" kenarı sabit, uçlar salınır). Oyuncunun ve yakındaki
// düşmanların çevresinde (holes: ekran UV'si, en çok 6) şerit yarı saydamlaşır: oynanış hiçbir zaman örtülmez.
shader_type canvas_item;
render_mode unshaded;

uniform float amp_px = 7.0;          // uçlarda en çok kayma (doku pikseli)
uniform float speed = 1.1;
uniform bool root_bottom = true;     // true: kök alt kenarda (otlar), false: üstte (sarkan dallar)
uniform vec2 holes[6];
uniform int hole_count = 0;
uniform float hole_r = 0.15;         // ekran yüksekliği biriminde
uniform float hole_alpha = 0.28;
uniform float aspect = 1.7778;
uniform float alpha = 1.0;

void fragment() {
	vec2 tp = TEXTURE_PIXEL_SIZE;
	float tipness = root_bottom ? (1.0 - UV.y) : UV.y;
	float w = sin(TIME * speed + UV.x * 38.0) * 0.65 + sin(TIME * speed * 1.7 + UV.x * 91.0) * 0.35;
	vec2 uv = UV + vec2(w * amp_px * tp.x * tipness * tipness, 0.0);
	vec4 c = texture(TEXTURE, uv);
	float k = 1.0;
	for (int i = 0; i < 6; i++) {
		if (i >= hole_count) {
			break;
		}
		// dikeyde uzun elips: ayakta duran gövdeyi baştan ayağa açar
		vec2 dd = (SCREEN_UV - holes[i]) * vec2(aspect, 0.6);
		k = min(k, smoothstep(hole_r * 0.5, hole_r, length(dd)));
	}
	c.a *= mix(hole_alpha, 1.0, k) * alpha;
	COLOR = c * COLOR;
}
