// Stil v2 sıvı tehlike havuzu (Şahmeran zehri, Tamu lavı; Level._build_hazards_ink). Her bağlı tehlike bölgesi tek
// çokgen: dalgalı yüzey çizgisi (mürekkep + parlak kenar), akan gövde (veri dokusu: R akış, G hücre kenarı, B ayrıntı),
// lavda kabuk plakaları arasında ışıyan çatlaklar, zehirde köpük ağı ve girdaplar. Gölgesiz; değerler 1'i aşar (parlama).
shader_type canvas_item;
render_mode unshaded;

uniform sampler2D noise_tex : filter_linear_mipmap, repeat_enable;
uniform float surface_y = 0.0;          // havuzun üst kenarı (dünya y)
uniform vec4 deep : source_color = vec4(0.16, 0.03, 0.02, 1.0);
uniform vec4 mid : source_color = vec4(0.75, 0.2, 0.05, 1.0);
uniform vec4 hot : source_color = vec4(1.0, 0.72, 0.3, 1.0);
uniform vec4 ink : source_color = vec4(0.082, 0.086, 0.114, 1.0);
uniform float gain = 1.6;               // ışıma çarpanı (HDR)
uniform float crust = 1.0;              // 1 lav kabuğu, 0 zehir köpüğü
uniform float flow = 0.025;
uniform float scale = 1.0;

varying vec2 wp;

void vertex() {
	wp = (MODEL_MATRIX * vec4(VERTEX, 0.0, 1.0)).xy;
}

void fragment() {
	float t = TIME;
	float surf = 3.5 + 1.6 * sin(wp.x * 0.07 + t * 1.4) + 0.9 * sin(wp.x * 0.19 - t * 2.2);
	float dz = wp.y - surface_y - surf;
	if (dz < -1.5) {
		discard;
	}
	vec2 uv = wp / 256.0 * scale;
	vec4 n1 = texture(noise_tex, uv * vec2(0.7, 1.0) + vec2(t * flow, 0.0));
	vec4 n2 = texture(noise_tex, uv * 1.7 + vec2(-t * flow * 0.6, t * flow * 0.3));
	float f = n1.r * 0.65 + n2.r * 0.35;
	vec3 col;
	if (crust > 0.5) {
		// kabuk plakaları: hücre kenarlarında (G) ışıyan çatlak, plakaların içi koyu; derinde ve kenarda ısı artar
		float crack = smoothstep(0.5, 0.9, n1.g) * (0.6 + 0.4 * f);
		float crack2 = smoothstep(0.65, 0.95, n2.g) * 0.7;
		float heat = clamp(crack + crack2 + smoothstep(0.4, 0.8, f) * 0.45 + 0.12, 0.0, 1.0);
		// akış: kabuk plakaları yavaşça nabız atar
		heat *= 0.85 + 0.15 * sin(t * 1.7 + wp.x * 0.05);
		col = mix(deep.rgb * (0.7 + 0.5 * n2.b), mid.rgb, smoothstep(0.15, 0.6, heat));
		col = mix(col, hot.rgb, smoothstep(0.6, 1.0, heat));
		col *= mix(1.0, gain, heat);
	} else {
		// zehir: koyu yeşil gövde, açık girdaplar, yüzeyde köpük ağı
		float sw = smoothstep(0.35, 0.8, f);
		col = mix(deep.rgb, mid.rgb, sw);
		// girdap çizgileri (ayrıntı dokusundan ince açık şeritler)
		col = mix(col, hot.rgb * 0.8, smoothstep(0.62, 0.7, n2.b) * (1.0 - smoothstep(0.7, 0.8, n2.b)) * 0.6);
		// yükselen kabarcıklar: hücre başına bir halka, yukarı kayar
		vec2 bc = vec2(wp.x / 7.0, (wp.y + t * 12.0) / 7.0);
		vec2 bi = floor(bc);
		float h = fract(sin(dot(bi, vec2(12.9898, 78.233))) * 43758.5453);
		vec2 bp = fract(bc) - vec2(0.5) - (vec2(h, fract(h * 7.3)) - 0.5) * 0.5;
		float br = 0.08 + 0.12 * fract(h * 3.1);
		float ring = (1.0 - smoothstep(0.03, 0.07, abs(length(bp) - br))) * step(0.86, h);
		col = mix(col, hot.rgb * gain, ring * 0.8);
		float foam = smoothstep(0.7, 0.95, n2.g) * (1.0 - smoothstep(0.0, 18.0, dz));
		col = mix(col, hot.rgb * gain, foam * 0.45);
		col += hot.rgb * smoothstep(0.82, 0.98, n1.b) * 0.6;
	}
	// yüzey: parlak kenar şeridi ve üstünde mürekkep çizgisi
	float rim = smoothstep(-0.5, 1.0, dz) * (1.0 - smoothstep(1.0, 4.5, dz));
	col = mix(col, hot.rgb * gain * 1.2, rim * 0.85);
	float inkl = 1.0 - smoothstep(0.0, 1.4, abs(dz + 0.4));
	col = mix(col, ink.rgb, inkl * 0.95);
	// derine doğru kararır
	col *= mix(1.0, 0.55, smoothstep(10.0, 46.0, dz));
	float a = smoothstep(-1.5, -0.5, dz);
	COLOR = vec4(col, a);
}
