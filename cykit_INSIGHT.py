import time, signal, queue, sys, os, time, threading
from datetime import datetime
from cyCrypto import Random
from cyCrypto.Cipher import AES
from graph import Window_Insight
import cyPyWinUSB as hid
sys.path.insert(0, '..//py3//cyUSB//cyPyWinUSB')
sys.path.insert(0, '..//py3')

"""Tempo de aquisição: 5, 15, 30, 45, 60, 300
-> chegar em um valor minimo neecessário para treinar IA
-> CORES: preto; branco
-> DESCOMPRESSÃO: 10 à 0 para não afetar os dados de outro dataset
-> Calibração_cor_preto_estimulovocal
-> Calibração_cor_preto_estimulovisual
-> Calibração_cor_preto_estimulmisto
-> Calibração_cor_branco_estimulovocal
-> Calibração_cor_branco_estimulovisual
-> Calibração_cor_branco_estimulmisto
-> todos com 300 segundos

1. Coletar dados para animado, frustação: sentimentos de dentro para fora
2. Coletar para movimento: vocal visual e misto -> tipo do movimento, fechar e abrir o mão
Ação_movimentofechado_pensamento
Ação_movimentofechado_misto
Ação_movimentoaberto_pensamento
Ação_movimentoaberto_misto
3. Fazer a comparação
"""


tasks = queue.Queue()
EEG_name = {"AF3": 3, "T7": 5, "Pz": 7, "T8": 12, "AF4": 14}

print('Iniciando o objeto')

class EEG_insight(object):

    def __init__(self):
        
        self.hid = None
        devicesUsed = 0
        self.delimiter = ';'
        self.channel  = { "AF3":[], "T7":[], "Pz":[], "T8":[], "AF4":[] }

        #Preset
        self.opc = 3
        self.save = 'S'
        self.timing = '00:00:15'
        self.filename = 'Teste1'
        self.start = 0
        self.mathplot = 0
        self.range = 0
        self.sensors = ["AF3","T7","Pz","T8","AF4"]
        self.tmp = []
        #self.sensors = ["AF3","T7","Pz","T8","AF4"]

        signal.signal(signal.SIGINT, self.signal_handler)
        
        self.cipher = None

        if self.opc == 1 or self.opc == 3:
            for device in hid.find_all_hid_devices():
                if device.product_name == 'EEG Signals':
                    devicesUsed += 1
                    self.hid = device
                    self.hid.open()
                    self.serial_number = device.serial_number
                    device.set_raw_data_handler(self.dataHandler)
            
            if devicesUsed == 0:
                os._exit(0)
            
            sn = bytearray()
            for i in range(0, len(self.serial_number)):
                sn += bytearray([ord(self.serial_number[i])])

            # Insight Keymodel.
            k = ['\0'] * 16
            k = [sn[-1], 00, sn[-2], 21, sn[-3], 00, sn[-4], 12, sn[-3], 00, sn[-2], 68, sn[-1], 00, sn[-2], 88]
            
            self.key = bytes(bytearray(k))
            self.cipher = AES.new(self.key, AES.MODE_ECB)
        
    def signal_handler(self, signal, frame):
        
        if self.opc == 1 and self.save == 'S':
            
            self.window.close_graph()
            self.gen_file()  
                   
            
        elif self.opc == 1 and self.save == 'N':
            
            self.window.close_graph()
            self.gen_file()  
        
        elif self.opc == 2:
            
            print("\nArquivo lido")
            self.window.close_graph()
            sys.exit(0) 
        
        elif self.opc == 3:
            
            print('\nEncerrado...')
            self.end_program()
            sys.exit(0) 

        print("\n\033[7;32mFIM\n\033[m")
        
    def dataHandler(self, data):
        
        if self.cipher == None:
            
            return
        
        join_data = ''.join(map(chr, data[1:]))
        data = self.cipher.decrypt(bytes(join_data, 'latin-1')[0:32])
        tasks.put(data)

    def convert_v2(self, value_1, value_2):
        
        edk_value = "%.8f" % (((int(value_1) - 128) * 32.82051289) + ((int(value_2) * .128205128205129) + 4201.02564096001))
        
        return edk_value

    def get_data(self):

        try:
            data = tasks.get()

            packet_data = [data[0]]
            z = ''
            for i in range(1, len(data)):
                z = z + format(data[i], '08b')

            i_1 = -14
            for i in range(0, 18):
                i_1 += 14
                v_1 = '0b' + z[(i_1):(i_1 + 8)]
                v_2 = '0b' + z[(i_1 + 8):(i_1 + 14)]
                packet_data.append(str(self.convert_v2(str(eval(v_1)), str(eval(v_2)))))
            return packet_data

        except Exception as exception2:

            print(str(exception2))
            
    def gen_file(self):
        
        self.end_program()
        
        if self.save == 'S':
            
            if ".csv" not in self.filename:
                self.filename += ".csv"
            
            with open("datasets/" + self.filename, "w+") as f:
                f.write(f"AF3; T7; Pz; T8; AF4; Tempo; Início: {self.s}; Fim: {self.e}; Tempo de aquisição: {self.dur}\n")

                for c in range(len(self.channel["AF3"])):
                    linha = str(self.channel["AF3"][c]) + self.delimiter + \
                            str(self.channel["T7"][c])  + self.delimiter + \
                            str(self.channel["Pz"][c])  + self.delimiter + \
                            str(self.channel["T8"][c])  + self.delimiter + \
                            str(self.channel["AF4"][c]) + self.delimiter + \
                            str(self.tmp[c]) + self.delimiter + "\n"
                        
                    f.write(linha)
        else:
            print("Erro, não informou se deve ser salvo")
                
        print("Dados salvos")
        sys.exit(0)
             
    def time_close(self):

        horas, minutos, segundos = 0, 0, 0
        
        str_split = self.timing.split(":")
        
        if len(str_split) == 3:
            horas = int(str_split[0])
            minutos = int(str_split[1])
            segundos = int(str_split[2])
        
        elif len(str_split) == 2:
            
            minutos = int(str_split[0])
            segundos = int(str_split[1])
        
        elif len(str_split) == 1:
            
            segundos = int(str_split[0])
        
        else:
            
            print("Formato de tempo inválido")
            
        self.tempo = horas * 3600 + minutos * 60 + segundos
    
    def data_list(self):
        
        sensors = ["AF3","T7","Pz","T8","AF4"]
        a = []
        
        print("Iniciando coleta de dados...")

        if self.opc == 3:
            self.time_close()

        self.start = time.time()
        b = datetime.now().timestamp()

        while 1:  

            if self.opc == 3:

                if len(self.channel["AF4"]) == int(self.tempo * 128): 
                    self.gen_file()

            
            a = datetime.now().timestamp()
            self.tmp.append(a - b)

            eeg_data = cyHeadset.get_data()
            for sensor in sensors:
                self.channel[sensor].append(float(eeg_data[EEG_name[sensor]]))
            
            
    def end_program(self):
        
        print("Encerrando a execução...")
        
        #Marcação do fim do programa
        self.end = time.time()
        
        #Duração da execução do programa;
        if self.opc == 1:
            self.dur = self.end - self.start
        
        elif self.opc == 3:
            self.dur = self.tempo
        
        #Formatação da string do tempo de início
        self.s = time.gmtime(self.start)
        self.s = time.strftime("%d/%m/%Y %H:%M:%S", self.s)
        
        #Formatação da string do tempo de encerramento
        self.e = time.gmtime(self.end)
        self.e = time.strftime("%d/%m/%Y %H:%M:%S", self.e)
        
        print(f'\n\033[1;32mInício:\033[m {self.s}'
            f'\n\033[1;32mTempo de aquisição:\033[m {self.dur:.0f} segundos'
            f'\n\033[1;32mFim:\033[m {self.e}')
        
        
if os.name == 'nt':
    os.system("mode con:cols=80 lines=14")  # Resize screen (for Windows)

cyHeadset = EEG_insight()
eeg_data = []

data_thread = threading.Thread(name=" Update_EEG_Headset", target=cyHeadset.data_list, daemon=False)
init = True

while 1:

    if init == True:
            
            if cyHeadset.opc == 1:
                
                cyHeadset.window = Window_Insight(opc=cyHeadset.opc, filename=cyHeadset.filename, save=cyHeadset.save, start=cyHeadset.start, channel=cyHeadset.channel, mathplot=cyHeadset.mathplot, range=cyHeadset.range, sensors=cyHeadset.sensors, tempo=cyHeadset.tmp)
                data_thread.start()
                cyHeadset.window.execute_graph()
                
            elif cyHeadset.opc == 2:
                
                cyHeadset.window = Window_Insight(opc=cyHeadset.opc, filename=cyHeadset.filename, save=cyHeadset.save, start=cyHeadset.start, channel=cyHeadset.channel, mathplot=cyHeadset.mathplot, range=cyHeadset.range, sensors=cyHeadset.sensors, tempo=cyHeadset.tmp)
                cyHeadset.window.execute_graph()
                
            elif cyHeadset.opc == 3:
                
                data_thread.start()
                
            init = False
    

    while tasks.empty():
        pass