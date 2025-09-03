
import socket
import threading
import time
import random

# Configurações
HOST = '127.0.0.1'
PORT = 5000
NUM_CLIENTS = random.randint(3, 10)
LOG_FILE = "berkeley_log.txt"

def log_event(msg):
	with open(LOG_FILE, "a") as f:
		f.write(msg + "\n")
	print(msg)


def get_local_time():
	"""Simula o relógio local com valor pequeno para facilitar visualização."""
	# Valor base entre 20 e 40
	return random.randint(20, 40)


class ClientThread(threading.Thread):
	def __init__(self, client_id, offset):
		super().__init__()
		self.client_id = client_id
		self.offset = offset  # diferença simulada do relógio
		self.local_time = get_local_time() + self.offset

	def run(self):
		log_event(f"[Cliente {self.client_id}] Iniciando com relógio local = {self.local_time}")
		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
			s.connect((HOST, PORT))
			# Passo 2: Envia tempo local ao coordenador
			log_event(f"[Cliente {self.client_id}] Enviando tempo local ao coordenador: {self.local_time}")
			s.sendall(str(self.local_time).encode())
			# Passo 5: Recebe ajuste do coordenador
			data = s.recv(1024)
			ajuste = int(data.decode())
			log_event(f"[Cliente {self.client_id}] Recebeu ajuste: {ajuste}")
			self.local_time += ajuste
			log_event(f"[Cliente {self.client_id}] Relógio ajustado: {self.local_time}")


def servidor():
	clientes_tempos = []
	conexoes = []
	log_event(f"[Coordenador] Passo 1: Aguardando {NUM_CLIENTS} clientes...")
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
		s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		s.bind((HOST, PORT))
		s.listen(NUM_CLIENTS)
		for _ in range(NUM_CLIENTS):
			conn, addr = s.accept()
			log_event(f"[Coordenador] Conectado a {addr}")
			data = conn.recv(1024)
			tempo_cliente = int(data.decode())
			log_event(f"[Coordenador] Recebeu tempo do cliente: {tempo_cliente}")
			clientes_tempos.append(tempo_cliente)
			conexoes.append(conn)
		# Passo 3: Tempo do coordenador
		tempo_coordenador = get_local_time()
		log_event(f"[Coordenador] Tempo local do coordenador: {tempo_coordenador}")
		clientes_tempos.append(tempo_coordenador)
		log_event(f"[Coordenador] Tempos recebidos (clientes + coordenador): {clientes_tempos}")
		# Passo 4: Calcula média
		media = sum(clientes_tempos) // len(clientes_tempos)
		log_event(f"[Coordenador] Média calculada: {media}")
		# Passo 5: Envia ajuste para cada cliente
		for i, conn in enumerate(conexoes):
			ajuste = media - clientes_tempos[i]
			log_event(f"[Coordenador] Enviando ajuste para Cliente {i+1}: {ajuste}")
			conn.sendall(str(ajuste).encode())
			conn.close()
		log_event(f"[Coordenador] Relógio antes = {tempo_coordenador}, ajuste = {media - tempo_coordenador}")
		log_event(f"[Coordenador] Relógio ajustado = {tempo_coordenador + (media - tempo_coordenador)}")


if __name__ == "__main__":
	# Limpa o log anterior
	open(LOG_FILE, "w").close()
	log_event(f"[Sistema] Iniciando algoritmo de Berkeley com {NUM_CLIENTS} processos (clientes)...")
	# Inicia o servidor em uma thread separada
	server_thread = threading.Thread(target=servidor)
	server_thread.start()
	time.sleep(1)  # Garante que o servidor está pronto
	# Inicia os clientes com offsets aleatórios
	offsets = [random.randint(-10, 10) for _ in range(NUM_CLIENTS)]
	client_threads = [ClientThread(i+1, offsets[i]) for i in range(NUM_CLIENTS)]
	for ct in client_threads:
		ct.start()
	for ct in client_threads:
		ct.join()
	server_thread.join()
	log_event(f"[Sistema] Execução finalizada. Veja o log completo em {LOG_FILE}")
