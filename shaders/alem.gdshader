// Üç Âlem: kam transında ekranın tümü öbür âlemin rengine bürünür.
// gök (Ülgen): sıcak altın ışık, yumuşak parlama, yukarıdan süzülen aydınlık.
// yer (Erlik): soluk, mor-kızıl, kenarları kararan, hafifçe dalgalanan görüntü.
shader_type canvas_item;

uniform sampler2D scr : hint_screen_texture, filter_linear_mipmap;
uniform float gok = 0.0;
uniform float yer = 0.0;
uniform float t = 0.0;

void fragment() {
	vec2 uv = SCREEN_UV;
	uv.x += sin(uv.y * 38.0 + t * 2.2) * 0.0016 * yer;
	vec3 c = texture(scr, uv).rgb;
	if (gok > 0.001) {
		vec3 bl = textureLod(scr, uv, 3.0).rgb;
		vec3 g = c + bl * 0.2;
		g = g * vec3(1.06, 1.0, 0.84) + vec3(0.035, 0.028, 0.0);
		g += vec3(1.0, 0.88, 0.55) * pow(1.0 - uv.y, 3.0) * 0.2;
		float rays = pow(max(0.0, sin(uv.x * 9.0 - uv.y * 4.0 + t * 0.3)), 8.0) * (1.0 - uv.y) * 0.08;
		g += vec3(1.0, 0.9, 0.6) * rays;
		c = mix(c, g, gok);
	}
	if (yer > 0.001) {
		float l = dot(c, vec3(0.3, 0.59, 0.11));
		vec3 y = mix(vec3(l), c, 0.35) * vec3(0.95, 0.58, 0.85);
		float r = texture(scr, uv + vec2(0.0025, 0.0)).r;
		y.r = mix(y.r, r * 0.95, 0.35);
		float v = smoothstep(0.85, 0.25, distance(uv, vec2(0.5, 0.5)));
		y *= mix(0.4, 1.05, v);
		c = mix(c, y, yer);
	}
	COLOR = vec4(c, 1.0);
}
