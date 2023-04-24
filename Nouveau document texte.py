import time
#import pyaudio
import vosk
import wave
#import max4466
#import espeak
import espeakng
from machine import Pin, PWM, SD, ADC, SPI


# Initialize the SPI bus for SD card
spi = SPI(1, baudrate=10000000, polarity=0, phase=0)

# Initialize the SD card pins
'''
SD module    ESP32
-------------------
CS           GPIO5
MOSI         GPIO23
MISO         GPIO19
SCK          GPIO18
VCC          3V3
GND          GND
'''



# Initialize the SD card
sd = SD(spi, Pin(5))
sd.mount('/sd')

# Define the PINs used for the microphone, LED, and speaker
MIC_PIN = 34
LED_PIN = 4
SPEAKER_PIN = 25



# Initialize the speaker
spk = PWM(Pin(25))
spk.freq(16000)

# Set the speech rate and volume
espeak.set_parameter(espeak.Parameter.Rate, 140)
espeak.set_parameter(espeak.Parameter.Volume, 90)

# Define the configuration for Vosk
model_path = '/sd/vosk-model-small-en-us-0.15/vosk-model-small-en-us-0.15/'
sample_rate = 16000
model = vosk.Model(model_path)
rec = vosk.KaldiRecognizer(model, sample_rate)

# Define a function tzo toggle the LED
def toggle_led():
    led = Pin(LED_PIN, Pin.OUT)
    led.value(not led.value())
# Define a function to synthesize speech
def speak(text):
    speaker = espeakng.Speaker()
    speaker.set_voice("en")
    speaker.set_pitch(50)  # range is 0-99
    speaker.set_speed(100)  # range is 80-450
    speaker.say(text)
    speaker.start()

# Define a function to read audio from the microphone
def read_audio():
    adc = ADC(Pin(34))
    adc.atten(ADC.ATTN_11DB)
    adc.width(ADC.WIDTH_12BIT)
    audio = []
    for i in range(16000):
        sample = adc.read()
        audio.append(sample - 2048)
    return bytes(bytearray(audio))

# Define a function to play audio from a WAV file
def play_wav_file(filename):
    # Read the audio data from the WAV file
    with open('/sd/' + filename, 'rb') as f:
        audio_data = f.read()

    # Create a PWM object for the speaker pin
    speaker_pwm = PWM(Pin(SPEAKER_PIN), freq=sample_rate, duty=512)

    # Output the audio data to the speaker
    for sample in audio_data:
        speaker_pwm.duty(int(512 * sample / 128))

    # Turn off the speaker
    speaker_pwm.deinit()

# Define a function to run the voice recognition process
# Define a function to run the voice recognition process
def run_voice_recognition():

    # Define the configuration for Vosk with wake word detection
    wake_model_path = '/sd/vosk-model-small-en-us-0.15/vosk-model-small-en-us-0.15/'
    wake_sample_rate = 16000
    wake_model = vosk.Model(wake_model_path)
    wake_rec = vosk.KaldiRecognizer(wake_model, wake_sample_rate)
    wake_phrase = "hey jake"

    # Listen for the wake word
    while True:
        audio = read_audio()
        if wake_rec.AcceptWaveform(audio):
            result = wake_rec.Result()
            output_text = result["text"]
            if wake_phrase in output_text:
                print("Wake word detected.")
                speak("how can i help you sir")
                break
        time.sleep(0.1)

    # Listen for the next spoken command
    while True:
        audio = read_audio()
        if rec.AcceptWaveform(audio):
            result = rec.Result()
            output_text = result["text"]
            print("You said:", output_text)
            if "open" in output_text:
                led = Pin(LED_PIN, Pin.OUT)
                led.value(1)
                # Synthesize speech from input text
                speak("light is on")
                # Turn off the speaker
                spk.deinit()
            elif "close" in output_text:
                led = Pin(LED_PIN, Pin.OUT)
                led.value(0)
                speak("light is off")
            else:
                play_wav_file('music.wav')
            break

# Run the voice recognition process every 5 seconds
while True:
    run_voice_recognition()
    time.sleep(5.0)
