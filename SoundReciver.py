import qi
import time
import sys

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
        self.buffer = None

    def start(self):
        """
        Subscribes to the audio device.
        """
        self.audio_service.openAudioInputs()
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

    def getBuffer(self):
        """
        Returns the last received audio buffer.
        """
        if self.buffer is not None:
            buff = self.buffer
            self.buffer = None  # Clear the buffer after returning it
            return buff
        else:
            print ("[SoundReceiver] No audio buffer available.")
            return None

    def processRemote(self, nbOfChannels, nbrOfSamplesByChannel, timestamp, buffer):
        """
        This method is called by ALAudioDevice with the audio data.
        """
        # Your processing logic goes here.
        # For example, you can print the characteristics of the received audio buffer.
        self.buffer = buffer
        # print ("Received audio buffer:")
        # print (" - Channels:", nbOfChannels)
        # print (" - Samples per channel:", nbrOfSamplesByChannel)
        # print (" - Timestamp:", timestamp)  
        # The buffer contains the raw audio data. You can process it as needed.