// Stil v2 "mürekkep" ortam öğeleri (ot öbekleri örtü katmanı, süsler, gözetleme kulesi ayakları): boyalı doku,
// doğrusal süzgeç, ışıklar yumuşak ve kısık eklenir (zemin ile aynı kural: ground_ink.gdshader).
shader_type canvas_item;

uniform vec4 tint : source_color = vec4(1.0, 1.0, 1.0, 1.0);
uniform float moon_gain : hint_range(0.0, 2.0) = 0.6;
uniform float point_gain : hint_range(0.0, 2.0) = 1.0;
// ot öbekleri için hafif rüzgâr: dokunun üst kısmı yatayda salınır (sway_px: doku pikseli)
uniform float sway_px = 0.0;

void fragment() {
	vec2 uv = UV;
	if (sway_px > 0.0) {
		vec2 tp = 1.0 / vec2(textureSize(TEXTURE, 0));
		float cell = 48.0 * tp.y;
		float local = 1.0 - fract(UV.y / cell);
		float ph = TIME * 1.3 + floor(UV.x / (48.0 * tp.x)) * 1.7;
		uv.x += sin(ph) * sway_px * tp.x * local * local;
	}
	COLOR = texture(TEXTURE, uv) * COLOR * tint;
	NORMAL_MAP = vec3(0.5, 0.5, 1.0);
}

void light() {
	float ndl = clamp(dot(NORMAL, LIGHT_DIRECTION), 0.0, 1.0);
	float g = LIGHT_IS_DIRECTIONAL ? moon_gain : point_gain;
	LIGHT = vec4(COLOR.rgb * LIGHT_COLOR.rgb * LIGHT_ENERGY * (0.45 + 0.55 * ndl) * g, LIGHT_COLOR.a);
}
