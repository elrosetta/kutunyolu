// v20 mürekkep yer tozu (scripts/core/InkDust.gd): ağır silah yere indiğinde kabaran mürekkep yıkaması bulutları,
// yere yatık sürünen toz, moloz kırıkları ve kor. Hepsi yordamsal, fwidth ile kenar yumuşatmalı (piksel kare yok).
//
// Köşe verisi (renk değil):
//   UV.x  yerel u (0..1) + 2 x tür   tür: 0 kabaran bulut, 1 moloz kırığı, 2 yere yatık sürünen toz, 3 kor / kıvılcım
//   UV.y  yerel v (0..1) + 2 x tohum (0..7: biçim ve gürültü çeşitlemesi)
//   COLOR.a yaş 0 (taze) .. 1 (ölü)
// Renkler biyomdan (uniform): koyu, orta, açık ton + mürekkep konturu + sıcak (kor). Bulut: üstte ışık alan açık
// yıkama, altta orta ton, kenarda koyulaşan ıslak pigment bandı, alt kenarda ince mürekkep konturu; yaşlandıkça
// gürültüyle kenardan yenerek dağılır (kâğıt üstünde kuruyan yıkama gibi).
shader_type canvas_item;
render_mode blend_premul_alpha, unshaded;

uniform vec3 c_dark = vec3(0.12, 0.1, 0.08);
uniform vec3 c_mid = vec3(0.3, 0.26, 0.2);
uniform vec3 c_light = vec3(0.6, 0.54, 0.45);
uniform vec3 c_ink = vec3(0.01, 0.008, 0.006);
uniform vec3 c_hot = vec3(1.0, 0.45, 0.1);
uniform float opacity = 0.84;

float hash(vec2 p) {
	p = fract(p * vec2(123.34, 456.21));
	p += dot(p, p + 45.32);
	return fract(p.x * p.y);
}

float vnoise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), u.x), mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x), u.y);
}

float fbm(vec2 p) {
	float s = 0.0;
	float a = 0.5;
	for (int i = 0; i < 4; i++) {
		s += vnoise(p) * a;
		p = p * 2.03 + vec2(17.1, 9.7);
		a *= 0.5;
	}
	return s;
}

void fragment() {
	float typ = floor(UV.x * 0.5);
	float seed = floor(UV.y * 0.5);
	vec2 uv = vec2(UV.x - typ * 2.0, UV.y - seed * 2.0);
	vec2 p = uv * 2.0 - 1.0;
	float age = clamp(COLOR.a, 0.0, 1.0);
	vec3 col;
	float alpha;
	if (typ < 0.5 || (typ > 1.5 && typ < 2.5)) {
		// bulut (0) / yere yatık sürünen toz (2: yassı, alt kenarı düz)
		vec2 q = p;
		if (typ > 1.5) {
			q.y = q.y < 0.0 ? q.y : q.y * 1.8;
		}
		float r = length(q);
		vec2 np = p * 1.7 + vec2(seed * 7.31, seed * 3.17) + vec2(0.0, age * 0.9);
		float n = fbm(np);
		float n2 = fbm(np * 2.6 + 4.0);
		// karnabahar silüeti: kenar gürültüyle kabarır; yaşla kenardan yenir
		float edge = 1.0 - r + (n - 0.5) * 0.62 + (n2 - 0.5) * 0.18 - age * age * 0.7 - age * 0.12;
		float aa = fwidth(edge) * 0.9 + 0.012;
		alpha = smoothstep(-aa, aa, edge);
		// kuruyan yıkamanın içindeki boşluklar (yaşla açılır)
		float holes = smoothstep(0.62 - age * 0.35, 0.7 - age * 0.3, n2 + (1.0 - edge) * 0.25);
		alpha *= 1.0 - holes * smoothstep(0.25, 0.8, age);
		// cel ışık: sol üstten; iki ton + yumuşak geçiş
		float lit = dot(normalize(q + vec2(0.0001)), vec2(-0.45, -0.89)) * smoothstep(0.0, 0.9, r) + (n - 0.5) * 0.9 - q.y * 0.35;
		// her tutam biraz farklı tonda: üst üste binen kabarıklar ayrı okunur
		float tone = fract(seed * 0.618 + 0.13);
		col = mix(c_mid, c_light, smoothstep(-0.05, 0.25, lit) * (0.75 + 0.25 * tone));
		col = mix(col, c_dark, (1.0 - tone) * 0.18);
		col = mix(col, c_dark, smoothstep(0.05, 0.6, q.y + (n2 - 0.5) * 0.5) * 0.55);
		// ıslak kenar: pigment kenarda birikir
		float rim = 1.0 - smoothstep(0.0, 0.11 + 0.05 * age, edge);
		col = mix(col, c_dark, rim * 0.65);
		// alt kenarda ince mürekkep konturu (çizgi roman), yaşla söner
		float outline = (1.0 - smoothstep(0.0, 0.045, edge)) * smoothstep(-0.1, 0.5, q.y);
		col = mix(col, c_ink, outline * 0.45 * (1.0 - age));
		// iç yıkama dalgalı: kenar dolgun, ortası yer yer açık (kuru fırça yıkaması)
		alpha *= opacity * (0.92 - 0.4 * age) * (0.78 + 0.22 * n2) * (0.82 + 0.18 * smoothstep(0.0, 0.35, 1.0 - edge * 1.4 + rim));
	} else if (typ < 1.5) {
		// moloz kırığı: tohuma göre dönmüş düzensiz çokgen, ışıklı üst yüz, mürekkep kontur
		float ang = seed * 0.785;
		vec2 q = mat2(vec2(cos(ang), sin(ang)), vec2(-sin(ang), cos(ang))) * p;
		float k1 = 0.9 + 0.25 * fract(seed * 0.37);
		float m = 1.0 - max(abs(q.x) * k1 + q.y * 0.35, abs(q.y) * 1.35 - q.x * 0.25);
		m = min(m, 1.0 - (abs(q.x + q.y) * 0.9));
		float aa = fwidth(m) * 1.1 + 0.02;
		alpha = smoothstep(-aa, aa, m) * (1.0 - smoothstep(0.75, 1.0, age));
		col = mix(c_dark, c_mid, step(p.y, -0.05) * 0.8 + 0.2);
		col = mix(col, c_light, (1.0 - smoothstep(0.0, 0.2, abs(p.y + 0.35))) * step(p.y, 0.0) * 0.6);
		col = mix(col, c_ink, 1.0 - smoothstep(0.0, 0.22, m));
	} else {
		// kor: sıcak çekirdekli yuvarlak kıvılcım (toplamalı)
		float r = length(p);
		float core = 1.0 - smoothstep(0.15, 0.45, r);
		float glow = 1.0 - smoothstep(0.3, 1.0, r);
		alpha = clamp(core + glow * 0.4, 0.0, 1.0) * (1.0 - age);
		col = mix(c_hot, vec3(1.0, 0.92, 0.7), core) * 2.0;
	}
	// kor toplamalı (alfa 0), diğerleri örten mürekkep
	COLOR = vec4(col * alpha, typ > 2.5 ? 0.0 : alpha);
}
