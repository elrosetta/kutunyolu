// Stil v2 mürekkep kan (scripts/core/Blood.gd, yalnızca --stil=v2): v1'in 2/3 dünya pikseli kareleri yerine
// fırça biçimleri. Renk köşe renginden (düşmana özgü kan rengi), biçim UV'den:
//   UV.x = u (0..1) + 2 x tohum (0..63: biçim çeşitlemesi)   UV.y = v (0..1) + 2 x tür
//   tür 0 uçan damla (u kuyruk -> baş, hız yönünde uzamış gözyaşı)
//   tür 1 leke (düzensiz mürekkep lekesi, koyu kenar, ıslak parlama, 2-3 uydu nokta)
//   tür 2 duvardan süzülen iz (yukarıda geniş, aşağı incelen fırça akıntısı + uçta damla)
//   tür 3 et parçası (mürekkep konturlu düzensiz parça, üstte açık ton)
// Sahne ışığı (ay, çıra) etkiler (light() varsayılan).
shader_type canvas_item;

const vec3 INK = vec3(0.0075, 0.008, 0.012);

float h1(float n) {
	return fract(sin(n * 127.1 + 31.7) * 43758.5453);
}

void fragment() {
	float seed = floor(UV.x * 0.5);
	float kind = floor(UV.y * 0.5);
	vec2 uv = vec2(UV.x - seed * 2.0, UV.y - kind * 2.0);
	vec3 col = COLOR.rgb;
	float a = 0.0;
	if (kind < 0.5) {
		float y = abs(uv.y * 2.0 - 1.0);
		float w = sin(3.14159 * pow(clamp(uv.x, 0.0, 1.0), 1.8));
		float m = w - y;
		float aa = fwidth(m) + 0.02;
		a = smoothstep(-aa, aa, m);
		col *= mix(0.65, 1.0, smoothstep(0.2, 0.8, uv.x));
	} else if (kind < 1.5 || kind > 2.5) {
		vec2 p = uv * 2.0 - 1.0;
		float th = atan(p.y, p.x);
		float s1 = h1(seed) * 6.28;
		float s2 = h1(seed + 7.0) * 6.28;
		float s3 = h1(seed + 13.0) * 6.28;
		float r = 0.66 + 0.13 * sin(3.0 * th + s1) + 0.08 * sin(5.0 * th + s2) + 0.05 * sin(9.0 * th + s3);
		if (kind > 2.5) {
			r = 0.72 + 0.12 * sin(2.0 * th + s1) + 0.1 * sin(4.0 * th + s2);  // parça: daha köşeli, yuvarlak
		}
		float d = length(p) - r;
		float sat = 1.0;
		if (kind < 1.5) {
			for (int i = 0; i < 3; i++) {
				float fi = float(i);
				float an = h1(seed + 3.0 + fi * 5.0) * 6.28;
				float rr = 0.8 + 0.12 * h1(seed + 11.0 + fi);
				float rad = 0.05 + 0.07 * h1(seed + 17.0 + fi);
				float ds = length(p - vec2(cos(an), sin(an)) * rr) - rad;
				sat = min(sat, ds);
			}
		}
		float dd = min(d, sat);
		float aa = fwidth(dd) * 0.9 + 0.01;
		a = smoothstep(aa, -aa, dd);
		if (kind < 1.5) {
			// koyu kenar (mürekkep sinmesi) + ortada ıslak parlama
			col *= mix(0.42, 1.0, smoothstep(0.0, 0.22, -d));
			float wet = 1.0 - smoothstep(0.0, 0.16, length(p - vec2(-0.25, -0.3)));
			col = mix(col, col * 1.7 + 0.04, wet * 0.5);
		} else {
			col = mix(col, col * 1.45 + 0.03, smoothstep(0.1, -0.5, p.y + p.x * 0.4) * 0.6);
			col = mix(col, INK, smoothstep(-0.2, -0.1, d));
		}
	} else {
		// süzülen iz: u enine (0..1), v boyuna (0 üst .. 1 alt); uçta damla
		float x = abs(uv.x * 2.0 - 1.0);
		float w = mix(1.0, 0.35, uv.y) * (1.0 - smoothstep(0.85, 1.0, uv.y));
		float tipd = length(vec2(x * 0.5, (uv.y - 0.9) * 2.2)) - 0.42;
		float m = max(w - x, -tipd);
		float aa = fwidth(m) + 0.02;
		a = smoothstep(-aa, aa, m);
		col *= mix(0.55, 1.0, smoothstep(0.0, 0.5, w - x));
	}
	COLOR = vec4(col, a * COLOR.a);
}
