import time
import threading
import numpy as np
import sounddevice as sd
import mlx_whisper
import os
import gc
import mlx.core as mx
from huggingface_hub import snapshot_download


class BoltEngine:
    def __init__(self, model_path, callback_text, callback_rms, callback_status):
        self.model_path = model_path
        self.callback_text = callback_text
        self.callback_rms = callback_rms
        self.callback_status = callback_status
        self.recording = []
        self.is_recording = False
        self.model_loaded = False
        self.fs = 16000
        self.is_loading = False
    
    def cancel(self):
        if not self.is_recording: return
        self.is_recording = False
        
        try:
            if hasattr(self, 'stream'):
                self.stream.stop()
                self.stream.close()
        except: pass

        self.recording = []
        print("Запись отменена пользователем. Буфер очищен.")
    
    def download_model(self, model_id, repo_id):
        target_dir = os.path.expanduser(f"~/Library/Application Support/BoltAI/models/{model_id}")
        
        def _target():
            def progress_callback(fraction):
                self.callback_status("loading", int(fraction * 100))

            try:
                self.callback_status("loading", 10)
                
                snapshot_download(
                    repo_id=repo_id,
                    local_dir=target_dir,
                    local_dir_use_symlinks=False
                )
                
                self.model_path = target_dir
                self.callback_status("ready", 100)
                print(f"Модель {model_id} готова.")
            except Exception as e:
                self.callback_status("error", 0)
                print(f"Download error: {e}")

        threading.Thread(target=_target, daemon=True).start()


    def load_model(self, path=None):
        if self.is_loading: return
        if path: self.model_path = path
        
        self.is_loading = True
        def _load():
            self.callback_status("loading", 0)
            try:
                mlx_whisper.transcribe(np.zeros(16000), path_or_hf_repo=self.model_path)
                self.model_loaded = True
                self.callback_status("ready", 100)
            except Exception as e:
                self.callback_status("error", 0)
                print(f"Ошибка зажигания: {e}")
            finally:
                self.is_loading = False

        threading.Thread(target=_load, daemon=True).start()

    def unload(self):
        self.model_loaded = False
        self.is_loading = False
        gc.collect()
        mx.clear_cache()
        self.callback_status("unloaded", 0)
        print("Двигатель заглушен, VRAM свободна.")

    def start(self):
        if not self.model_loaded: return
        
        self.recording = []
        self.is_recording = True
        
        def cb(indata, frames, time, status):
            if status: print(f"Audio Status: {status}")
            if self.is_recording:
                self.recording.append(indata.copy())
                rms = np.sqrt(np.mean(indata**2))
                self.callback_rms(rms)

        try:
            if hasattr(self, 'stream'):
                try: self.stream.abort()
                except: pass
            
            self.stream = sd.InputStream(
                samplerate=self.fs, 
                channels=1, 
                dtype='float32', 
                callback=cb,
                blocksize=0,
                latency='high'
            )
            self.stream.start()
            print("Микрофон заведен.")
        except Exception as e:
            print(f"Ошибка захвата (Bluetooth?): {e}")
            self.is_recording = False

    def stop(self):
        if not self.is_recording: return
        self.is_recording = False
        
        try:
            if hasattr(self, 'stream'):
                self.stream.stop()
                self.stream.close()
        except: pass

        if self.recording:
            audio_data = np.concatenate(self.recording, axis=0).flatten()
            threading.Thread(target=self._infer, args=(audio_data,), daemon=True).start()

    def _infer(self, audio):
        if not self.model_loaded:
            print("Автозагрузка модели...")
            self.load_model()
            return

        audio_duration = len(audio) / self.fs
        start_t = time.time()
        try:
            res = mlx_whisper.transcribe(audio, path_or_hf_repo=self.model_path)
            proc_duration = time.time() - start_t
            self.callback_text(res['text'].strip(), audio_duration, proc_duration)
        except Exception as e:
            print(f"Inference error: {e}")
