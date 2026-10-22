// v40 ekran uzayı ışık hüzmesi / hacimli ışık geçişi (Level._build_huzme; yalnızca Işık ve parlama "Tam").
// Dünyanın ÜSTÜNE toplamalı çizilir (karakterler de hüzmenin içinden geçer: havadaki toz / sis ışığı saçar).
// Üç kip, her biri tek geçişte karışır (ağırlıklar biyom "huzme" anahtarından):
//   band  : eğik, nefes alan ışık perdeleri (Ötüken ay hüzmeleri, Bozkır güneş yelpazesi, Kaf kar parıltısı)
//   blob  : yavaş süzülen yumuşak ışık lekeleri (Şahmeran biyolüminesans)
//   heat  : alttan yükselen titrek kor ışığı (Tamu lav parıltısı)
// Doku yok, yalnızca ALU. Çeyrek çözünürlüklü SubViewport'a (480x270, HDR) çizilip toplamalı karışımla ekrana gerilir
// (tam ekranda UHD 750'de ~2,5 ms'ydi; şimdi < 0,5 ms). Kamera kayması "scroll" ile hüzmeler ortamla birlikte kayar.
shader_type canvas_item;
render_mode blend_add, unshaded;

uniform vec4 color : source_color = vec4(0.6, 0.72, 0.85, 1.0);
uniform float intensity : hint_range(0.0, 1.0) = 0.1;
uniform float angle = 0.5;            // radyan; + = ışık sol üstten (hüzmeler sağ alta eğik)
uniform float count = 4.0;            // ekran genişliğinde yaklaşık hüzme sayısı
uniform float width = 0.5;            // 0..1: hüzmelerin dolgunluğu (küçük = ince ışık çizgileri)
uniform float top_fade = 1.6;         // aşağı doğru sönme üssü (büyük = yalnızca üstte)
uniform float band_k = 1.0;
uniform float blob_k = 0.0;
uniform float heat_k = 0.0;
uniform float scroll = 0.0;           // kamera x (ekran birimi); Level yazar
uniform float aspect = 1.7778;
uniform float speed = 1.0;

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
	float t = TIME * speed;
	vec2 uv = UV;
	float out_v = 0.0;
	if (band_k > 0.001) {
		// eğik eksen: hüzme boyunca sabit kalan koordinat
		float ca = cos(angle);
		float sa = sin(angle);
		float x = (uv.x * aspect + scroll) * ca - uv.y * sa;
		float f = count * 1.1;
		// üç uyumsuz frekansın toplamı: düzensiz aralıklı, farklı kalınlıkta perdeler; her biri yavaşça kayar
		float s = sin(x * f + t * 0.07) * 0.5 + 0.5;
		float s2 = sin(x * f * 0.61 + 1.7 - t * 0.05) * 0.5 + 0.5;
		float s3 = sin(x * f * 2.3 + 4.1 + t * 0.11) * 0.5 + 0.5;
		float m = s * 0.55 + s2 * 0.3 + s3 * 0.15;
		float sharp = mix(9.0, 2.2, clamp(width, 0.0, 1.0));
		float band = pow(clamp(m, 0.0, 1.0), sharp);
		// nefes: her hüzme kendi evresinde (yavaş)
		band *= 0.72 + 0.28 * sin(t * 0.33 + x * 2.0);
		// yukarıdan aşağı sönüş + alt kenarda tam sönüş
		float vf = pow(1.0 - uv.y, top_fade);
		out_v += band_k * band * vf;
	}
	if (blob_k > 0.001) {
		// yumuşak ışık lekeleri: iki oktav değer gürültüsü, yavaş süzülür; parlak uçları yumuşak
		vec2 p = vec2(uv.x * aspect + scroll * 0.6, uv.y) * (count * 0.55);
		float n = vnoise(p + vec2(t * 0.03, -t * 0.02)) * 0.65 + vnoise(p * 2.1 + vec2(-t * 0.05, t * 0.04)) * 0.35;
		float blob = smoothstep(0.5, 0.86, n);
		blob *= 0.75 + 0.25 * sin(t * 0.5 + n * 9.0);
		out_v += blob_k * blob;
	}
	if (heat_k > 0.001) {
		// alttan yükselen kor ışığı: alt kenarda güçlü, yukarı doğru söner; yatayda yavaş dalgalanan sıcak lekeler
		float n = vnoise(vec2(uv.x * aspect * 2.4 + t * 0.12, uv.y * 3.0 - t * 0.35)) * 0.6
			+ vnoise(vec2(uv.x * aspect * 5.0 - t * 0.2, uv.y * 6.0 - t * 0.7)) * 0.4;
		float vf = pow(clamp(uv.y, 0.0, 1.0), top_fade);
		float fl = 0.85 + 0.15 * sin(t * 2.3 + uv.x * 7.0) * sin(t * 1.3);
		out_v += heat_k * vf * (0.45 + 0.55 * n) * fl;
	}
	COLOR = vec4(color.rgb * (out_v * intensity), 1.0);
}
