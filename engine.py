import time
import threading
import numpy as np
import sounddevice as sd
import mlx_whisper
import os

class BoltEngine:
    def __init__(self, model_path, callback_text, callback_rms):
        self.model_path = model_path
        self.callback_text = callback_text
        self.callback_rms = callback_rms
        self.recording = []
        self.rec_lock = threading.Lock()
        self.is_recording = False
        self.fs = 16000

    def start(self):
        self.recording = []
        self.is_recording = True
        
        def cb(indata, frames, time, status):
            if status: print(f"Audio Status: {status}")
            if self.is_recording:
                self.recording.append(indata.copy())
                rms = np.sqrt(np.mean(indata**2))
                self.callback_rms(rms)

        try:
            # Сбрасываем старый поток если он есть
            if hasattr(self, 'stream') and self.stream.active:
                self.stream.stop()
                self.stream.close()
            
            # Явно берем дефолтный вход
            device_info = sd.query_devices(kind='input')
            samplerate = int(device_info['default_samplerate']) if self.fs is None else self.fs
            
            self.stream = sd.InputStream(
                samplerate=samplerate, 
                channels=1, 
                dtype='float32',
                callback=cb,
                device=None # Пусть система сама выберет текущий активный микро
            )
            self.stream.start()
        except Exception as e:
            print(f"PortAudio Critical Error: {e}")
            self.is_recording = False

    def stop(self):
        self.is_recording = False
        self.stream.stop()
        self.stream.close()
        with self.rec_lock:
            local_recording = self.recording
            self.recording = []
        if local_recording:
            audio = np.concatenate(local_recording, axis=0).flatten()
            threading.Thread(target=self._infer, args=(audio,), daemon=True).start()

    def _infer(self, audio):
        audio_duration = len(audio) / self.fs
        
        start_t = time.time()
        
        res = mlx_whisper.transcribe(audio, path_or_hf_repo=self.model_path)
        
        proc_duration = time.time() - start_t
        
        self.callback_text(res['text'].strip(), audio_duration, proc_duration)
