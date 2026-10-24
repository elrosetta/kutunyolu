// v43 sinematik birleştirici (Sinema.gd): iki çekim (a: önceki, b: şimdiki) arasında geçiş + son işlem.
// tur: 0 kesme, 1 mürekkep yıkaması (koyu leke yayılır, kenarda ıslak halka), 2 fırça silmesi (kıl izli yatay darbe),
// 3 kâğıt yırtığı (pürüzlü çapraz yırtık, beyaz lif + gölge), 4 karart (siyahtan), 5 ak ışık (beyaza patlayıp açılır).
// Son işlem: kâğıt tanesi, kenar kararması, ince sinema bantları (bant 0..1), saydam kipte alfa korunur.
shader_type canvas_item;

uniform sampler2D tex_a : filter_linear, repeat_disable;
uniform sampler2D tex_b : filter_linear, repeat_disable;
uniform float k : hint_range(0.0, 1.0) = 1.0;
uniform int tur = 0;
uniform float seed = 0.0;
uniform float grain = 0.05;
uniform float vign = 0.35;
uniform float bant = 0.0;
uniform float aspect = 1.7778;
uniform float solma = 1.0;
uniform vec4 flas : source_color = vec4(1.0, 0.95, 0.85, 0.0);
uniform bool saydam = false;
uniform bool dogrusal = false;   // ana görüntü HDR (doğrusal): sRGB çekim dokuları çevrilir

float h21(vec2 p) {
	p = fract(p * vec2(233.34, 851.73) + seed);
	p += dot(p, p + 23.45);
	return fract(p.x * p.y);
}

float vn(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(h21(i), h21(i + vec2(1, 0)), f.x), mix(h21(i + vec2(0, 1)), h21(i + vec2(1, 1)), f.x), f.y);
}

float fbm(vec2 p) {
	return vn(p) * 0.55 + vn(p * 2.1 + 7.0) * 0.27 + vn(p * 4.3 + 3.0) * 0.12 + vn(p * 9.1 + 1.0) * 0.06;
}

void fragment() {
	vec2 uv = UV;
	vec4 A = texture(tex_a, uv);
	vec4 B = texture(tex_b, uv);
	vec4 c = B;
	float kk = clamp(k, 0.0, 1.0);
	if (kk < 1.0) {
		if (tur == 1) {
			float n = fbm(uv * vec2(4.0 * aspect, 4.0));
			float cen = length((uv - 0.5) * vec2(aspect, 1.0)) * 0.35;
			float v = kk * 1.55 - 0.05 - n * 0.75 - cen;
			float m = smoothstep(0.0, 0.06, v);
			float rim = smoothstep(-0.07, 0.0, v) * (1.0 - smoothstep(0.0, 0.12, v));
			c = mix(A, B, m);
			c.rgb = mix(c.rgb, vec3(0.03, 0.028, 0.04), rim * 0.85);
			c.a = max(c.a, rim * 0.85 * max(A.a, B.a));
		} else if (tur == 2) {
			float st = vn(vec2(0.0, uv.y * 160.0)) * 0.6 + vn(vec2(0.0, uv.y * 23.0)) * 0.4;
			float x = uv.x - (st - 0.5) * 0.1 - sin(uv.y * 3.1) * 0.03;
			float edge = kk * 1.35 - 0.15;
			float m = smoothstep(edge, edge - 0.025, x);
			float stroke = smoothstep(edge + 0.05, edge, x) * smoothstep(edge - 0.1, edge - 0.02, x);
			stroke *= 0.6 + 0.4 * step(0.35, vn(vec2(x * 30.0, uv.y * 220.0)));
			c = mix(A, B, m);
			c.rgb = mix(c.rgb, vec3(0.03, 0.028, 0.04), stroke * 0.92);
			c.a = max(c.a, stroke * 0.9 * max(A.a, B.a));
		} else if (tur == 3) {
			float jag = (vn(vec2(uv.y * 40.0, 1.0)) - 0.5) * 0.035 + (vn(vec2(uv.y * 9.0, 4.0)) - 0.5) * 0.06;
			float d = uv.x * 0.85 + (1.0 - uv.y) * 0.3 + jag;
			float edge = kk * 1.5 - 0.2;
			float m = step(d, edge);
			float fib = smoothstep(edge + 0.012, edge, d) * (1.0 - m);
			float sh = smoothstep(edge - 0.05, edge, d) * m;
			vec4 A2 = texture(tex_a, uv + vec2(0.02, -0.01) * kk);
			c = mix(A2, B, m);
			c.rgb = mix(c.rgb, vec3(0.96, 0.93, 0.86), fib * (0.7 + 0.3 * vn(uv * 300.0)));
			c.rgb *= 1.0 - sh * 0.35;
			c.a = max(c.a, fib);
		} else if (tur == 4) {
			float f = kk < 0.5 ? 1.0 - kk * 2.0 : (kk - 0.5) * 2.0;
			c = kk < 0.5 ? A : B;
			c.rgb *= f;
			if (saydam) {
				c.a *= f;
			}
		} else if (tur == 5) {
			float f = kk < 0.35 ? kk / 0.35 : 1.0 - (kk - 0.35) / 0.65;
			c = kk < 0.35 ? A : B;
			c.rgb = mix(c.rgb, vec3(1.0, 0.96, 0.88), clamp(f, 0.0, 1.0));
		} else {
			c = kk < 0.5 ? A : B;
		}
	}
	// son işlem: tane, kâğıt lifi, kenar kararması, flaş, bantlar
	float g = (h21(uv * vec2(1931.0, 1093.0) + fract(TIME * 7.3)) - 0.5) * grain;
	float paper = (fbm(uv * vec2(90.0 * aspect, 90.0)) - 0.5) * grain * 0.8;
	c.rgb += vec3(g + paper);
	vec2 q = (uv - 0.5) * vec2(aspect, 1.0);
	float vg = 1.0 - vign * smoothstep(0.45, 1.25, length(q));
	c.rgb *= vg;
	c.rgb = mix(c.rgb, flas.rgb, flas.a);
	float bh = bant * 0.075;
	if (uv.y < bh || uv.y > 1.0 - bh) {
		c = vec4(0.012, 0.01, 0.014, 1.0);
	}
	c.rgb *= solma;
	if (dogrusal) {
		c.rgb = mix(c.rgb / 12.92, pow((max(c.rgb, vec3(0.0)) + 0.055) / 1.055, vec3(2.4)), step(vec3(0.04045), c.rgb));
	}
	if (saydam) {
		c.a *= solma;
	} else {
		c.a = 1.0;
	}
	COLOR = c;
}
