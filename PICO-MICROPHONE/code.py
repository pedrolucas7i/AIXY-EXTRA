import time
import array
import board
import audiobusio
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.mouse import Mouse
import tinyusb
import ulab  # Importando a biblioteca ulab para FFT

# Definindo os pinos para o microfone PDM (NP0555)
clock_pin = board.GP2  # SCK (Serial Clock)
word_select_pin = board.GP3  # WS (Word Select)
data_pin = board.GP4  # SD (Serial Data)

# Configuração da captura de áudio PDM
pdm_in = audiobusio.PDMIn(data_pin, clock_pin, word_select_pin, sample_rate=16000, bit_depth=16)

# Tamanho do buffer de áudio (quantidade de amostras)
buffer_size = 512
audio_buffer = array.array('H', [0] * buffer_size)

# Inicializando o TinyUSB para criar um dispositivo USB
usb_device = tinyusb.usb_device()

# Inicializa o dispositivo de áudio (USB Audio Device)
class AudioUSB(tinyusb.Device):
    def __init__(self):
        super().__init__(usb_device)
        self.audio_interface = tinyusb.Interface("Audio", 1)
        self.endpoint = tinyusb.Endpoint(self.audio_interface, tinyusb.Direction.OUT, 1)

    def send_audio_data(self, audio_data):
        # Enviar os dados do áudio capturado como pacotes USB
        self.endpoint.write(audio_data)

# Instanciando o dispositivo de áudio USB
audio_usb_device = AudioUSB()

# Função para capturar o áudio do microfone
def capture_audio():
    while True:
        # Captura de áudio para o buffer
        pdm_in.record(audio_buffer, len(audio_buffer))
        
        # Processar o áudio capturado (aplicar FFT e/ou filtro)
        process_audio(audio_buffer)

        # Enviar os dados de áudio capturados via USB
        audio_usb_device.send_audio_data(bytes(audio_buffer))

        # Atraso entre as capturas para evitar sobrecarga
        time.sleep(0.01)

# Função para processar os dados de áudio
def process_audio(buffer):
    # Passo 1: Convertendo os dados do buffer de áudio para um formato utilizável para FFT
    # Convertendo os dados capturados (array de inteiros) para float para o FFT
    audio_float = ulab.numpy.array(buffer, dtype=float)

    # Passo 2: Aplicando a Transformada Rápida de Fourier (FFT)
    fft_result = ulab.numpy.fft(audio_float)

    # Passo 3: Filtragem (Filtro Passa-Baixa)
    filtered_audio = low_pass_filter(fft_result)

    # Passo 4: Converter os dados filtrados de volta para o formato original e processar
    # Se desejado, podemos inverter o FFT para obter o sinal no domínio do tempo
    processed_audio = ulab.numpy.fft.ifft(filtered_audio)
    processed_audio = processed_audio.real  # Pegando apenas a parte real do sinal

    # Exibir algumas informações sobre as frequências (exemplo de monitoramento)
    print("FFT Frequencies: ", fft_result[:10])  # Mostra as primeiras 10 frequências
    print("Filtered Audio (first 10 samples): ", processed_audio[:10])

    # (Opcional) Aqui você pode aplicar mais processamentos, como detecção de voz ou outras técnicas

# Função para aplicar um filtro passa-baixa (exemplo simples)
def low_pass_filter(fft_data, cutoff_freq=2000, sample_rate=16000):
    """
    Aplica um filtro passa-baixa simples aos dados FFT.
    :param fft_data: Dados após a FFT (frequências)
    :param cutoff_freq: Frequência de corte do filtro passa-baixa em Hz
    :param sample_rate: Taxa de amostragem do áudio em Hz
    :return: Dados filtrados
    """
    # Calculando o índice correspondente à frequência de corte
    cutoff_index = int(cutoff_freq * len(fft_data) / sample_rate)
    
    # Aplicando o filtro: Zera as frequências acima do limite de corte
    fft_data[cutoff_index:] = 0
    fft_data[-cutoff_index:] = 0  # Reflete as frequências negativas
    
    return fft_data

# Iniciar a captura de áudio e emulação de microfone USB
capture_audio()
