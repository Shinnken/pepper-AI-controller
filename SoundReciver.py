import math
import numpy as np
from time import sleep
import speech_recognition as sr
import pyaudio
import wave
import io
import time  # Add this import for timing.
import threading  # <--- Add this import


# --- Energy Calculation Functions ---
# Method 2: Recommended approach using the NumPy library for performance

def calculate_rms_energy(samples):
    """
    Calculates the Root Mean Square (RMS) energy of a list of audio samples.
    RMS is a more meaningful measure of signal power and perceived loudness.
    
    Args:
        samples: A list or array of numerical audio samples.
        
    Returns:
        The RMS energy of the frame. Returns 0 if the list is empty.
    """
    # FIX: Use len(samples) to check for emptiness. This works for both
    # standard Python lists and NumPy arrays, avoiding the ValueError.
    if len(samples) == 0:
        return 0
        
    # Calculate the sum of squares, divide by the number of samples (mean),
    # then take the square root.
    sum_of_squares = np.sum(np.square(samples))
    mean_square = sum_of_squares / len(samples)
    return math.sqrt(mean_square)


# --- Conversion Functions ---

def convert_bytes_to_floats_numpy(byte_data):
    """
    Converts a byte string of 16-bit little-endian samples to a NumPy
    array of floats normalized between -1.0 and 1.0. This is the fastest method.
    
    Args:
        byte_data: A bytes or bytearray object.
        
    Returns:
        A NumPy array of normalized float samples.
    """
    # Create a NumPy array directly from the buffer.
    # The dtype np.int16 automatically handles the signed 16-bit conversion.
    # NumPy defaults to the system's endianness, which is usually little-endian.
    int_array = np.frombuffer(byte_data, dtype=np.int16)
    
    # Convert the array to float and perform vectorized division for normalization.
    # This is extremely fast as the operations are performed in C.
    float_array = int_array.astype(np.float32) / 32768.0
    
    return float_array


def get_rms_energy_from_bytes(byte_data):
    """
    Calculates the RMS energy from a byte string of audio data.
    """
    float_array = convert_bytes_to_floats_numpy(byte_data)
    return calculate_rms_energy(float_array)


class SoundReceiverModule(object):
    """
    A NAOqi module to subscribe to ALAudioDevice and process microphone data.
    """
    def __init__(self, session, name="SoundReceiverModule", thresholdRMSEnergy = 0.01, language="Polski"):
        super(SoundReceiverModule, self).__init__()
        self.session = session
        self.audio_service = session.service("ALAudioDevice")
        self.module_name = name
        self.channels = 1  # Assuming you want to process the front microphone
        self.accumulated_frames = []
        self.is_accumulating = False
        self.is_accumulating_or_recognizing_speech = False
        self.lastBelowThresholdTime = None
        self.r = sr.Recognizer()
        self.is_listening = False
        self.stt_output = None  # Variable to store STT output
        self.thresholdRMSEnergy = thresholdRMSEnergy
        self.language_map = {"Polski": "pl-PL", "English": "en-US"}
        self.stt_language = self.language_map.get(language, "pl-PL")

    def start(self):
        """
        Subscribes to the audio device.
        """
        self.audio_service.closeAudioInputs()
        self.audio_service.setClientPreferences(self.module_name, 16000, self.channels, 0)
        self.audio_service.subscribe(self.module_name)
        #print ("[SoundReceiver] Subscribed to ALAudioDevice.")

    def stop(self):
        """
        Unsubscribes from the audio device.
        """
        self.audio_service.unsubscribe(self.module_name)
        print ("[SoundReceiver] Unsubscribed from ALAudioDevice.")
   

    def _processSpeechRecognition(self, full_recording):
        """
        Process speech recognition in a separate thread with simple compression.
        """
        try:
            # Simple compression: reduce audio data by removing every other sample
            audio_array = np.frombuffer(full_recording, dtype=np.int16)
            compressed_audio = audio_array[::2]  # Take every second sample
            compressed_bytes = compressed_audio.tobytes()
            
            # Create WAV file in memory with compressed data
            p = pyaudio.PyAudio()
            audio_format = pyaudio.paInt16
            channels = 1
            rate = 8000  # Half the original rate due to downsampling

            byte_buffer = io.BytesIO()
            with wave.open(byte_buffer, "wb") as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(p.get_sample_size(audio_format))
                wf.setframerate(rate)
                wf.writeframes(compressed_bytes)

            byte_buffer.seek(0)
            print("[SoundReceiver] Processing accumulated audio on a separate thread.")
            
            with sr.AudioFile(byte_buffer) as source:
                audio_data = self.r.record(source)
                
                print("[SoundReceiver] Recognizing speech...")
                text = self.r.recognize_google(audio_data, language=self.stt_language, pfilter=1)
                print("[SoundReceiver] Recognized text:", text)
                self.stt_output = None if text.strip() == "" else text

        except sr.UnknownValueError:
            print("[SoundReceiver] Could not understand audio")
        except sr.RequestError as e:
            print("[SoundReceiver] Speech Recognition request error:", e)
        except Exception as e:
            print(f"[SoundReceiver] Error during audio processing: {e}")
        finally:
            self.is_accumulating_or_recognizing_speech = False
            self.setListening()
    def setListening(self):
        """
        Enables or disables listening mode.
        """
        self.is_listening = True
        print("[SoundReceiver] Started listening.")

    def setNotListening(self):
        """
        Disables listening mode.
        """
        self.is_listening = False
        self.is_accumulating = False
        self.accumulated_frames = []
        self.lastBelowThresholdTime = None
        print("[SoundReceiver] Stopped listening and cleared accumulated frames.")

    def processRemote(self, nbOfChannels, nbrOfSamplesByChannel, timestamp, buffer):
        if not self.is_listening:
            return
        rms = get_rms_energy_from_bytes(buffer)
        print("[SoundReceiver] RMS Energy:", rms)
        # Start accumulating if we detect a loud signal
        if not self.is_accumulating:
            if rms > self.thresholdRMSEnergy:
                self.is_accumulating = True
                self.is_accumulating_or_recognizing_speech = True
                self.accumulated_frames = []
                self.accumulated_frames.append(buffer)
                self.lastBelowThresholdTime = None
        else:
            # Already accumulating; append the buffer
            self.accumulated_frames.append(buffer)
            if rms > self.thresholdRMSEnergy:
                self.lastBelowThresholdTime = None
            else:
                # If below threshold, check timer
                if self.lastBelowThresholdTime is None:
                    self.lastBelowThresholdTime = time.time()
                else:
                    if time.time() - self.lastBelowThresholdTime >= 2.0:
                        # Finalize
                        self.is_accumulating = False
                        print("[SoundReceiver] Below threshold for 2s, spawning thread...")

                        full_recording = b''.join(self.accumulated_frames)
                        self.accumulated_frames = []
                        self.is_listening = False
                        threading.Thread(
                            target=self._processSpeechRecognition,
                            args=(full_recording,)
                        ).start()
