"""Programmatic sound generation for Moon Lander.

Generates simple WAV files at startup using only the standard library
(wave, struct, math, random). No external assets or numpy required.
"""

import math
import os
import random
import struct
import tempfile
import wave

import arcade


def _make_wav(filepath, samples, sample_rate=22050):
    """Write a list of float samples (-1.0 to 1.0) to a 16-bit mono WAV."""
    int_samples = [int(max(-1.0, min(1.0, s)) * 32767) for s in samples]
    data = struct.pack(f'<{len(int_samples)}h', *int_samples)
    with wave.open(filepath, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(data)


def _gen_thrust(duration=2.0, sample_rate=22050):
    """Low-frequency rumble with harmonics and noise."""
    samples = []
    n = int(sample_rate * duration)
    for i in range(n):
        t = i / sample_rate
        val = 0.30 * math.sin(2 * math.pi * 70 * t)
        val += 0.15 * math.sin(2 * math.pi * 140 * t)
        val += 0.10 * math.sin(2 * math.pi * 55 * t)
        val += 0.12 * (random.random() * 2 - 1)
        # Fade-in / fade-out for seamless looping
        env = 1.0
        fade = 0.05 * sample_rate
        if i < fade:
            env = i / fade
        elif i > n - fade:
            env = (n - i) / fade
        samples.append(val * 0.45 * env)
    return samples


def _gen_crash(duration=0.6, sample_rate=22050):
    """Short noise burst that decays."""
    samples = []
    n = int(sample_rate * duration)
    for i in range(n):
        t = i / sample_rate
        envelope = max(0.0, 1.0 - t / duration) ** 2
        noise = random.random() * 2 - 1
        # Add a low thump
        thump = math.sin(2 * math.pi * 40 * t) * max(0, 1 - t * 8)
        samples.append((noise * 0.6 + thump * 0.4) * envelope * 0.7)
    return samples


def _gen_land(duration=0.8, sample_rate=22050):
    """Rising tone chime for successful landing."""
    samples = []
    n = int(sample_rate * duration)
    for i in range(n):
        t = i / sample_rate
        freq = 500 + 500 * (t / duration)
        envelope = (1.0 - (t / duration) ** 2) * 0.5
        val = math.sin(2 * math.pi * freq * t) * envelope
        # Add a softer harmonic
        val += 0.2 * math.sin(2 * math.pi * freq * 1.5 * t) * envelope
        samples.append(val)
    return samples


class SoundManager:
    """Generates and manages game sounds. Gracefully degrades if audio fails."""

    def __init__(self):
        self._sounds = {}
        self._thrust_player = None
        self._thrust_playing = False
        self._sound_dir = None
        try:
            self._generate_sounds()
        except Exception as e:
            print(f"[SoundManager] Could not generate sounds: {e}")

    def _generate_sounds(self):
        self._sound_dir = tempfile.mkdtemp(prefix='moon_lander_snd_')

        thrust_path = os.path.join(self._sound_dir, 'thrust.wav')
        crash_path = os.path.join(self._sound_dir, 'crash.wav')
        land_path = os.path.join(self._sound_dir, 'land.wav')

        _make_wav(thrust_path, _gen_thrust())
        _make_wav(crash_path, _gen_crash())
        _make_wav(land_path, _gen_land())

        self._sounds['thrust'] = arcade.Sound(thrust_path)
        self._sounds['crash'] = arcade.Sound(crash_path)
        self._sounds['land'] = arcade.Sound(land_path)

    # -- Thrust (looping) --

    def start_thrust(self, volume=0.3):
        if not self._thrust_playing and 'thrust' in self._sounds:
            try:
                self._thrust_player = self._sounds['thrust'].play(
                    volume=max(0.05, min(0.6, volume)), loop=True
                )
                self._thrust_playing = True
            except Exception:
                pass
        elif self._thrust_playing and self._thrust_player:
            try:
                self._thrust_player.volume = max(0.05, min(0.6, volume))
            except Exception:
                pass

    def stop_thrust(self):
        if self._thrust_playing and self._thrust_player:
            try:
                self._thrust_player.pause()
            except Exception:
                pass
            self._thrust_playing = False

    # -- One-shot effects --

    def play_crash(self):
        if 'crash' in self._sounds:
            try:
                self._sounds['crash'].play(volume=0.5)
            except Exception:
                pass

    def play_land(self):
        if 'land' in self._sounds:
            try:
                self._sounds['land'].play(volume=0.5)
            except Exception:
                pass
