import socket
import threading
import time
import random

HOST = '127.0.0.1'
PORT = 5000
NUM_CLIENTS = random.randint(3, 10)
LOG_FILE = "berkeley_log.txt"
LOG_LOCK = threading.Lock()

def log_event(msg):
    with LOG_LOCK:
        with open(LOG_FILE, "a") as f:
            f.write(msg + "\n")
        print(msg)

def get_local_time():
    return random.randint(20, 40)

class ClientThread(threading.Thread):
    def __init__(self, client_id, offset):
        super().__init__()
        self.client_id = client_id
        self.offset = offset
        self.local_time = get_local_time() + self.offset

    def run(self):
        log_event(f"[Cliente {self.client_id}] Iniciando com relógio local = {self.local_time}")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))

            # Passo 2: Cliente recebe o tempo do coordenador
            data = s.recv(1024)
            tempo_coordenador = int(data.decode())
            log_event(f"[Cliente {self.client_id}] Recebeu tempo do Coordenador: {tempo_coordenador}")

            # Passo 3: Cliente calcula a diferença e envia para o coordenador
            diferenca = self.local_time - tempo_coordenador
            log_event(f"[Cliente {self.client_id}] Enviando diferença para o Coordenador: {diferenca}")
            s.sendall(str(diferenca).encode())

            # Passo 6: Cliente recebe o ajuste e atualiza seu relógio
            data = s.recv(1024)
            ajuste = int(data.decode())
            log_event(f"[Cliente {self.client_id}] Recebeu ajuste: {ajuste}")
            self.local_time += ajuste
            log_event(f"[Cliente {self.client_id}] Relógio ajustado: {self.local_time}")

def servidor():
    conexoes = []
    diferencas = []

    # Passo 1: Coordenador aguarda a conexão dos clientes
    log_event(f"[Coordenador] Passo 1: Aguardando {NUM_CLIENTS} clientes...")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(NUM_CLIENTS)
        for i in range(NUM_CLIENTS):
            conn, addr = s.accept()
            log_event(f"[Coordenador] Conectado a cliente {i+1} em {addr}")
            conexoes.append(conn)

        # Passo 2: Coordenador envia seu tempo para os clientes
        tempo_coordenador = get_local_time()
        log_event(f"[Coordenador] Tempo local do Coordenador: {tempo_coordenador}")
        log_event("[Coordenador] Enviando tempo para todos os clientes...")
        for conn in conexoes:
            conn.sendall(str(tempo_coordenador).encode())

        # Passo 3: Coordenador recebe as diferenças dos clientes
        log_event("[Coordenador] Aguardando diferenças dos clientes...")
        for i, conn in enumerate(conexoes):
            data = conn.recv(1024)
            diferenca = int(data.decode())
            log_event(f"[Coordenador] Recebeu diferença do cliente {i+1}: {diferenca}")
            diferencas.append(diferenca)

        # Adiciona a diferença do próprio coordenador (que é 0)
        diferencas.append(0)
        log_event(f"[Coordenador] Diferenças recebidas (clientes + Coordenador): {diferencas}")

        # Passo 4: Calcula a média das diferenças
        media_diferencas = sum(diferencas) // len(diferencas)
        log_event(f"[Coordenador] Média das diferenças calculada: {media_diferencas}")

        # Passo 5: Envia o ajuste para cada cliente
        for i, conn in enumerate(conexoes):
            ajuste = media_diferencas - diferencas[i]
            log_event(f"[Coordenador] Enviando ajuste para cliente {i+1}: {ajuste}")
            conn.sendall(str(ajuste).encode())
            conn.close()

        # Passo 6: Ajusta o relógio do coordenador
        ajuste_coordenador = media_diferencas - 0  # A diferença do coordenador é 0
        log_event(f"[Coordenador] Relógio antes = {tempo_coordenador}, ajuste = {ajuste_coordenador}")
        tempo_coordenador_ajustado = tempo_coordenador + ajuste_coordenador
        log_event(f"[Coordenador] Relógio ajustado = {tempo_coordenador_ajustado}")

if __name__ == "__main__":
    open(LOG_FILE, "w").close()
    log_event(f"[Sistema] Iniciando algoritmo de Berkeley com {NUM_CLIENTS} processos (clientes)...")

    server_thread = threading.Thread(target=servidor)
    server_thread.start()
    time.sleep(1)

    offsets = [random.randint(-10, 10) for _ in range(NUM_CLIENTS)]
    client_threads = [ClientThread(i + 1, offsets[i]) for i in range(NUM_CLIENTS)]

    for ct in client_threads:
        ct.start()

    for ct in client_threads:
        ct.join()

    server_thread.join()
    log_event(f"[Sistema] Execução finalizada. Veja o log completo em {LOG_FILE}")
