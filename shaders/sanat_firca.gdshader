// v28 Savaş Sanatları sumi-e fırça darbesi (scripts/core/SanatFX.gd firca şeritleri). Doku: assets/fx/ink/sanat_firca.png
// (tools/artgen/sanat_fx_ink.py): 8 satır fırça; R mürekkep yükü, G koyu birikim, B kıl kimliği, A kâğıt tanesi.
// Köşe verisi (HDR 2D'de COLOR.rgb doğrusala çevrildiği için yalnızca UV ve COLOR.a):
//   UV.x = u (0 baş .. 1 kuyruk) + 2 x (biçem + 8 x satır)
//   UV.y = v (0..1 enine) + 2 x açılış (0..63: darbenin çizilmiş payı, fırça ucu u = açılış)
//   COLOR.a = erime (0 taze .. 1 yok)
// Biçemler: 0 mürekkep (sumi siyahı, ince yerlerde paletin rengi), 1 renkli (gövde paletin renginde, kenarda koyu
// birikim), 2 sıcak (ışıyan çekirdek), 3 yıkama (sulu, saydam), 4 varak (altın: maden parıltısı), 5 kuru mürekkep
// (yalnız kıllar, uçan ak)
shader_type canvas_item;
render_mode blend_premul_alpha, unshaded;

uniform sampler2D brush : filter_linear_mipmap, repeat_disable;
uniform vec3 c_ink = vec3(0.004, 0.003, 0.004);
uniform vec3 c_core = vec3(0.16, 0.003, 0.006);
uniform vec3 c_body = vec3(0.78, 0.012, 0.006);
uniform vec3 c_rim = vec3(1.0, 0.16, 0.02);
uniform vec3 c_hot = vec3(1.0, 0.86, 0.62);
uniform float hot_gain = 2.2;
uniform float rows = 8.0;

void fragment() {
	float code = floor(UV.x * 0.5);
	float u = UV.x - code * 2.0;
	float style = mod(code, 8.0);
	float row = floor(code / 8.0 + 0.001);
	float q = floor(UV.y * 0.5);
	float v = UV.y - q * 2.0;
	float reveal = q / 63.0;
	float diss = clamp(COLOR.a, 0.0, 1.0);
	vec4 d = texture(brush, vec2(clamp(u, 0.002, 0.998), (row + clamp(v, 0.02, 0.98)) / rows));
	// açılış: fırça ucu (u = açılış) önünde yok; uç ıslak ve bir tık kalın
	float head = reveal * 1.02 - u;
	float rv = smoothstep(-0.006, 0.012, head);
	float wet = 1.0 - smoothstep(0.0, 0.12, head);
	// kuruma ve erime: eşik yükselir; kıl kimliği sırasıyla (kılların farklı boyda kopması)
	float th = 0.5 - wet * 0.06 * (1.0 - diss) + diss * (0.18 + 0.5 * d.b);
	if (style > 4.5) {
		th += 0.14;
	} else if (style > 0.5 && style < 1.5) {
		th += 0.04;   // renk katmanı biraz daha kuru: kıllar arası kâğıt görünür
	}
	float w = fwidth(d.r) * 0.9 + 0.01;
	float a = smoothstep(th - w, th + w, d.r) * rv;
	float grain = mix(1.0, 0.72 + 0.4 * d.a, 0.55);
	float fresh = 1.0 - smoothstep(0.0, 0.4, diss);
	vec3 col;
	if (style < 0.5 || style > 4.5) {
		// sumi siyahı: gövde koyu, ince / kuru yerlerde paletin koyu tonu; ıslak uçta palet rengi parlar
		// sumi: yansız siyaha yakın (paletin mürekkebinden bir tutam), ince yerde paletin koyusu sızar
		vec3 sumi = mix(vec3(0.005, 0.0045, 0.006), c_ink, 0.35);
		float thin = 1.0 - smoothstep(0.55, 0.85, d.r);
		col = mix(sumi, c_core * 0.6, thin * 0.25);
		col = mix(col, sumi * 0.4, d.g * 0.8);
		col = mix(col, c_rim, wet * fresh * 0.25 * thin);
		a *= grain;
	} else if (style < 1.5) {
		float body = smoothstep(0.5, 0.8, d.r);
		col = mix(c_rim, c_body, body);
		col = mix(col, c_core, smoothstep(0.8, 1.0, d.r) * 0.35);
		col = mix(col, c_core, smoothstep(0.62, 0.92, d.b) * 0.4);   // kıl çizgileri: rengin içinde koyu damarlar
		col = mix(col, c_ink, clamp(d.g * 0.85, 0.0, 1.0));
		col = mix(col, c_hot * hot_gain * 0.6, wet * fresh * (1.0 - d.g) * 0.4);
		a *= grain;
	} else if (style < 2.5) {
		float core = smoothstep(0.55, 0.95, d.r) * (1.0 - smoothstep(0.0, 0.45, abs(v - 0.5)));
		col = mix(c_rim * 1.4, c_hot * hot_gain, core);
		col *= 0.75 + 0.5 * fresh;
		a *= 0.9;
	} else if (style < 3.5) {
		// yıkama: sulu, eşiği düşük ve yumuşak; kenarda kuruma halkası (G)
		float aw = smoothstep(th - 0.2, th + 0.1, d.r) * rv;
		// yansız su mürekkebi (gri-siyah), paletin renginden yalnız bir tutam
		col = mix(c_ink * 1.6 + c_core * 0.35, c_body, 0.16 + 0.1 * d.a);
		col = mix(col, c_ink, d.g * 0.5);
		a = aw * (0.32 + 0.18 * d.a) * (1.0 - diss * 0.6);
	} else {
		// altın varak: paletin gövdesi + maden parıltısı (tane yüksekse sıcak)
		float glint = smoothstep(0.72, 0.9, d.a) * fresh;
		col = mix(c_body, c_rim, smoothstep(0.3, 0.8, d.a));
		col = mix(col, c_core, d.g * 0.6);
		col += c_hot * hot_gain * glint * 0.8;
	}
	COLOR = vec4(col * a, a);
}
