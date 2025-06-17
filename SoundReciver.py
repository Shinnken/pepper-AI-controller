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
def calculate_energy(samples):
    """
    Calculates the total energy of a list or array of audio samples.
    Energy is defined as `E = \Sigma x_n^2`  the sum of the squares of the sample amplitudes.
    
    Args:
        samples: A list or NumPy array of numerical audio samples.
        
    Returns:
        The total energy of the frame.
    """
    return np.sum(np.square(samples))


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
    def __init__(self, session, name="SoundReceiverModule"):
        super(SoundReceiverModule, self).__init__()
        self.session = session
        self.audio_service = session.service("ALAudioDevice")
        self.is_processing = False
        self.module_name = name
        # self.client_name = "soundReceiverClient"
        self.channels = 1  # Assuming you want to process the front microphone
        self.buffer_frames = []
        self.buffer = None
        self.energy = 0.0
        self.accumulated_frames = []
        self.is_accumulating = False
        self.lastBelowThresholdTime = None
        self.r = sr.Recognizer()
        self.is_listening = False
        self.stt_output = []  # List to store STT output

    def start(self):
        """
        Subscribes to the audio device.
        """
        self.audio_service.closeAudioInputs()
        self.audio_service.setClientPreferences(self.module_name, 16000, self.channels, 0)
        self.audio_service.subscribe(self.module_name)
        print ("[SoundReceiver] Subscribed to ALAudioDevice.")
        self.is_processing = True

    def stop(self):
        """
        Unsubscribes from the audio device.
        """
        if self.is_processing:
            self.audio_service.unsubscribe(self.module_name)
            print ("[SoundReceiver] Unsubscribed from ALAudioDevice.")
            self.is_processing = False

    def calcRMSLevel(self,data) :
        """
        Calculate RMS level
        """
        rms = 20 * np.log10( np.sqrt( np.sum( np.power(data,2) / len(data)  )) + 1e-12)
        return rms
    
    def convertStr2SignedInt(self, data) :
        """
        This function takes a string containing 16 bits little endian sound
        samples as input and returns a vector containing the 16 bits sound
        samples values converted between -1 and 1.
        """
        signedData=[]
        ind=0
        for i in range (0,len(data)/2) :
            signedData.append(data[ind]+data[ind+1]*256)
            ind=ind+2

        for i in range (0,len(signedData)) :
            if signedData[i]>=32768 :
                signedData[i]=signedData[i]-65536

        for i in range (0,len(signedData)) :
            signedData[i]=signedData[i]/32768.0

        return signedData

    def getBuffer(self):
        """
        Returns the last received audio buffer.
        """
        if self.buffer is not None:
            buff = self.buffer
            self.buffer = []  # Clear the buffer after returning it
            # sleep(0.06)  # Allow some time for the unsubscribe to take effect
            # self.audio_service.unsubscribe(self.module_name)  # Unsubscribe to avoid duplicate subscriptions
            return buff
        else:
            print ("[SoundReceiver] No audio buffer available.")
            return None
        
    def getBufferFrames(self):
        """
        Returns the list of audio frames received.
        """
        if self.buffer_frames:
            frames = self.buffer_frames
            self.buffer_frames = []
            return frames
        else:
            print ("[SoundReceiver] No audio frames available.")
            return []


    def getEnergy(self):
        """
        Returns the energy of the last received audio buffer.
        """
        if self.energy is not None:
            energy = self.energy
            self.energy = 0.0
            return energy
        else:
            print ("[SoundReceiver] No energy value available.")
            return 0.0

    def _processSpeechRecognition(self, full_recording):
        """
        Process speech recognition in a separate thread.
        """
        p = pyaudio.PyAudio()
        audio_format = pyaudio.paInt16
        channels = 1
        rate = 16000

        byte_buffer = io.BytesIO()
        with wave.open(byte_buffer, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(p.get_sample_size(audio_format))
            wf.setframerate(rate)
            wf.writeframes(full_recording)

        byte_buffer.seek(0)
        print("[SoundReceiver] Processing accumulated audio on a separate thread.")
        with sr.AudioFile(byte_buffer) as source:
            audio_data = self.r.record(source)
            try:
                print("[SoundReceiver] Recognizing speech...")
                text = self.r.recognize_google(audio_data, language='pl-PL', pfilter=1)
                print("[SoundReceiver] Recognized text:", text)
                self.stt_output = text
            except sr.UnknownValueError:
                print("[SoundReceiver] Could not understand audio")
            except sr.RequestError as e:
                print("[SoundReceiver] Speech Recognition request error:", e)

    def setListening(self):
        """
        Enables or disables listening mode.
        """
        self.is_listening = True

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
            if rms > 0.09:
                self.is_accumulating = True
                self.accumulated_frames = []
                self.accumulated_frames.append(buffer)
                self.lastBelowThresholdTime = None
        else:
            # Already accumulating; append the buffer
            self.accumulated_frames.append(buffer)
            if rms > 0.09:
                self.lastBelowThresholdTime = None
            else:
                # If below threshold, check timer
                if self.lastBelowThresholdTime is None:
                    self.lastBelowThresholdTime = time.time()
                else:
                    if time.time() - self.lastBelowThresholdTime >= 2.0:
                        # Finalize
                        # self.audio_service.unsubscribe(self.module_name)
                        self.is_accumulating = False
                        print("[SoundReceiver] Below threshold for 2s, spawning thread...")

                        full_recording = b''.join(self.accumulated_frames)
                        self.accumulated_frames = []
                        self.is_listening = False
                        threading.Thread(
                            target=self._processSpeechRecognition,
                            args=(full_recording,)
                        ).start()

