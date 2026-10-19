"""Ses denetimi: her WAV için süre, tepe, yükseklik (synth.loudness), DC, kırpma ve döngü dikişi.
Kullanım: python tools/audiogen/check.py [ad_öneki ...]"""
import os
import sys
import glob
import wave
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from synth import loudness

A = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'assets', 'audio')


def read(p):
    with wave.open(p) as w:
        sr = w.getframerate()
        ch = w.getnchannels()
        x = np.frombuffer(w.readframes(w.getnframes()), '<i2').astype(float) / 32768
    if ch == 2:
        x = x.reshape(-1, 2).mean(axis=1)
    return x, sr


def main():
    pre = [a for a in sys.argv[1:] if not a.startswith('-')]
    bad = 0
    for sub in ('sfx', 'music'):
        for p in sorted(glob.glob(os.path.join(A, sub, '*.wav'))):
            name = os.path.basename(p)[:-4]
            if pre and not any(name.startswith(q) for q in pre):
                continue
            x, sr = read(p)
            pk = np.max(np.abs(x))
            clip = int(np.sum(np.abs(x) > 0.999))
            dc = float(np.mean(x))
            ld = loudness(x, sr)
            seam = ''
            if name.endswith('_dongu') or sub == 'music':
                typ = np.mean(np.abs(np.diff(x))) + 1e-6
                seam = ' dikiş=%.1fx' % (abs(x[-1] - x[0]) / typ)  # dikiş sıçraması / tipik örnek farkı
            flag = ''
            if clip or abs(dc) > (0.01 if len(x) / sr < 0.3 else 0.005) or pk < 0.05 or len(x) / sr > 90 or (seam and abs(x[-1] - x[0]) > 6 * (np.mean(np.abs(np.diff(x))) + 1e-6)):
                flag = '  <-- !'
                bad += 1
            print('%-6s %-24s %6.2fs tepe=%5.2f yük=%6.1f dB dc=%+.4f kırp=%d%s%s' % (sub, name, len(x) / sr, pk, ld, dc, clip, seam, flag))
    print('sorunlu:', bad)


if __name__ == '__main__':
    main()
