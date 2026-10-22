// v40 mürekkep perdesi (scripts/core/Perde.gd): ekran geçişleri.
//   mode 0  fırça süpürme: perde "dir" yönünde pürüzlü, kuru fırça kenarıyla açılır / kapanır (bölüm başı, boss arenası)
//   mode 1  çözülme: mürekkep lekeleri büyüyüp birleşerek ekranı kaplar / çekilir (Kut Taşı ışınlanması)
//   mode 2  düz solma (konak sıcak perdesi, yurt)
// t: 0 = görünmez, 1 = tam kapalı. Perde yalnızca t > 0 iken görünür (ColorRect gizlenir: piksel doldurma yok).
shader_type canvas_item;

uniform float t : hint_range(0.0, 1.0) = 0.0;
uniform vec4 ink : source_color = vec4(0.082, 0.086, 0.114, 1.0);
uniform vec4 tint : source_color = vec4(0.0, 0.0, 0.0, 1.0);   // kenarda ikinci renk (konak: amber, ışınlanma: Kut)
uniform float tint_k : hint_range(0.0, 1.0) = 0.0;
uniform int mode = 0;
uniform float dir = 1.0;        // mode 0: +1 soldan sağa, -1 sağdan sola
uniform float seed = 0.0;
uniform float aspect = 1.7778;

float hash21(vec2 p) {
	p = fract(p * vec2(123.34, 456.21));
	p += dot(p, p + 45.32);
	return fract(p.x * p.y);
}

float vnoise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	float a = hash21(i);
	float b = hash21(i + vec2(1.0, 0.0));
	float c = hash21(i + vec2(0.0, 1.0));
	float d = hash21(i + vec2(1.0, 1.0));
	return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

void fragment() {
	vec2 uv = UV;
	float a = 0.0;
	if (mode == 0) {
		// süpürme cephesi: x + gürültü (iri dalgalı kenar) + kıl çizgileri (satır başına ince düzensizlik)
		float x = dir > 0.0 ? uv.x : 1.0 - uv.x;
		float n = vnoise(vec2(uv.y * 3.0 + seed, x * 2.0)) * 0.22 + vnoise(vec2(uv.y * 14.0 + seed * 3.0, x * 6.0)) * 0.08;
		float bristle = (hash21(vec2(floor(uv.y * 160.0), seed)) - 0.5) * 0.07;
		float front = t * 1.45 - 0.22;
		float thr = x + n + bristle;
		a = 1.0 - smoothstep(front - 0.04, front + 0.015, thr);   // thr < front → kaplı
		// cephenin hemen ardında kuru fırça: seyrek beyaz boşluklar (kâğıt dokusu)
		float dry = smoothstep(front - 0.11, front - 0.04, thr) * step(0.62, vnoise(vec2(uv.y * 90.0, x * 40.0 + seed)));
		a *= 1.0 - dry * 0.7;
	} else if (mode == 1) {
		// çözülme: iki oktav gürültü eşiklenir; lekeler büyür, kenarlar mürekkep gibi yumuşak
		vec2 p = vec2(uv.x * aspect, uv.y) * 4.0 + vec2(seed * 7.0, seed * 3.0);
		float n = vnoise(p) * 0.6 + vnoise(p * 2.7 + 11.0) * 0.4;
		float r = length((uv - vec2(0.5)) * vec2(aspect, 1.0)) * 0.35;   // kenarlar önce kaplanır
		float thr = n * 0.8 + 0.1 - r;
		a = smoothstep(thr - 0.06, thr + 0.06, t * 1.25 - 0.1);
	} else {
		a = t;
	}
	// ikinci renk yalnızca perdenin kenarında (a yarıda): tam kaplıyken saf mürekkep, çözülen lekelerin ucu Kut / amber
	float edge = a * (1.0 - a) * 4.0;
	vec3 col = mix(ink.rgb, tint.rgb, tint_k * edge);
	COLOR = vec4(col, clamp(a, 0.0, 1.0) * ink.a);
}
