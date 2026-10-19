// Stil v2 ok uçuş izi (scripts/actors/OkIz.gd, v25): çok ince (1080p'de 1,5-3 px), kuyruğa doğru incelen mürekkep
// fırça çizgisi. Kenar yumuşatma piksel cinsinden: enine uzaklık / fwidth = kenara kaç piksel; bir pikselden ince
// kalan çizgi kapsama oranında solar (kırpık / titrek değil). Kenar koyu mürekkep, çekirdek unsur renginde (unsursuz
// okta soluk kızıl); başa yakın çekirdek hafif HDR parlar; kuyruk kuru fırça kıllarına ayrılarak erir.
// Köşe verisi:
//   UV.x   iz boyunca dünya uzunluğu / 40 (bristle.png boyuna sarar)
//   UV.y   enine 0..1 (0,5 orta çizgi)
//   COLOR.rgb  çekirdek rengi (HDR olabilir), COLOR.a  0 baş (ok) .. 1 kuyruk / yaşlanmış
shader_type canvas_item;
render_mode blend_premul_alpha, unshaded;

uniform sampler2D bristle : filter_linear_mipmap, repeat_enable;
uniform vec3 c_ink = vec3(0.012, 0.008, 0.014);
uniform float hot_gain = 1.35;    // HDR: başa yakın çekirdek parlar (ışıma eşiğini hafifçe aşar)
uniform float rim = 0.3;          // kenarın mürekkep payı (0: düz renk)

void fragment() {
	float u = clamp(COLOR.a, 0.0, 1.0);
	float yy = UV.y * 2.0 - 1.0;
	float y = abs(yy);
	float fw = max(fwidth(yy), 1e-4);          // enine birim / piksel
	float half_px = 1.0 / fw;                  // yarı genişlik (piksel)
	float edge_px = (1.0 - y) * half_px;       // kenara uzaklık (piksel)
	float a = clamp(edge_px + 0.35, 0.0, 1.0);
	a *= clamp(half_px * 1.4, 0.0, 1.0);       // pikselden ince: kapsama oranında solar
	vec4 b = texture(bristle, vec2(UV.x, clamp(UV.y, 0.004, 0.996)));
	// kuru fırça: kuyruk kıllara ayrılır, en uçta tamamen erir
	float strand = smoothstep(-0.1, 0.1, b.r + 0.45 - u * 1.1);
	a *= mix(1.0, strand, smoothstep(0.35, 0.9, u));
	a *= 1.0 - smoothstep(0.78, 1.0, u);
	// renk: dış kenar koyu mürekkep, çekirdek unsur rengi; ince çizgide kenar payı en çok yarım piksel
	float rim_px = min(rim * half_px, 0.6);
	float core = smoothstep(rim_px - 0.3, rim_px + 0.5, edge_px);
	vec3 cc = COLOR.rgb * mix(hot_gain, 1.0, smoothstep(0.0, 0.5, u));
	vec3 col = mix(mix(c_ink, COLOR.rgb, 0.18), cc, core);
	COLOR = vec4(col * a, a);
}
