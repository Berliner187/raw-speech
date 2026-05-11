import numpy as np
import sounddevice as sd
import mlx_whisper
import threading
import os

class BoltEngine:
    def __init__(self, model_path, callback_text, callback_rms):
        self.model_path = model_path
        self.callback_text = callback_text
        self.callback_rms = callback_rms
        self.recording = []
        self.is_recording = False
        self.fs = 16000

    def start(self):
        self.recording = []
        self.is_recording = True
        def cb(indata, frames, time, status):
            if self.is_recording:
                self.recording.append(indata.copy())
                rms = np.sqrt(np.mean(indata**2))
                self.callback_rms(rms)
        
        self.stream = sd.InputStream(samplerate=self.fs, channels=1, callback=cb)
        self.stream.start()

    def stop(self):
        self.is_recording = False
        self.stream.stop()
        self.stream.close()
        if self.recording:
            audio = np.concatenate(self.recording, axis=0).flatten()
            threading.Thread(target=self._infer, args=(audio,), daemon=True).start()

    def _infer(self, audio):
        import time
        audio_duration = len(audio) / self.fs
        
        start_t = time.time()
        
        res = mlx_whisper.transcribe(audio, path_or_hf_repo=self.model_path)
        
        proc_duration = time.time() - start_t
        
        self.callback_text(res['text'].strip(), audio_duration, proc_duration)
