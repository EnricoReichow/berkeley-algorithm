import socket
import threading
import time
import random

HOST = '127.0.0.1'
PORT = 5000
NUM_CLIENTS = random.randint(3, 10)
LOG_FILE = "berkeley_log.txt"

def log_event(msg):
	with open(LOG_FILE, "a") as f:
		f.write(msg + "\n")
	print(msg)


def get_local_time():
	return random.randint(20, 40)


class ClientThread(threading.Thread):
	# cada cliente representa um processo rodando em paralelo.
	def __init__(self, client_id, offset):
		super().__init__()
		self.client_id = client_id
		self.offset = offset
		self.local_time = get_local_time() + self.offset

	def run(self):
		log_event(f"[Cliente {self.client_id}] Iniciando com relógio local = {self.local_time}")
		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
			s.connect((HOST, PORT))

			# passo 2: cliente envia seu tempo local para o coordenador.
			log_event(f"[Cliente {self.client_id}] Enviando tempo local ao Coordenador: {self.local_time}")
			s.sendall(str(self.local_time).encode())

			# passo 5: cliente recebe o ajuste e atualiza seu relógio.
			data = s.recv(1024)
			ajuste = int(data.decode())
			log_event(f"[Cliente {self.client_id}] recebeu ajuste: {ajuste}")
			self.local_time += ajuste
			log_event(f"[Cliente {self.client_id}] relógio ajustado: {self.local_time}")


def servidor():
	# o servidor é o processo coordenador do algoritmo.
	clientes_tempos = []
	conexoes = []

	# passo 1: coordenador aguarda a conexão dos clientes para receber os tempos.
	log_event(f"[Coordenador] passo 1: aguardando {NUM_CLIENTS} clientes...")
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
		s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		s.bind((HOST, PORT))
		s.listen(NUM_CLIENTS)
		for _ in range(NUM_CLIENTS):
			conn, addr = s.accept()
			log_event(f"[Coordenador] conectado a {addr}")
			data = conn.recv(1024)
			tempo_cliente = int(data.decode())
			log_event(f"[Coordenador] recebeu tempo do cliente: {tempo_cliente}")
			clientes_tempos.append(tempo_cliente)
			conexoes.append(conn)

		# passo 3: oordenador adiciona seu próprio tempo à lista.
		tempo_Coordenador = get_local_time()
		log_event(f"[Coordenador] Tempo local do Coordenador: {tempo_Coordenador}")
		clientes_tempos.append(tempo_Coordenador)
		log_event(f"[Coordenador] Tempos recebidos (clientes + Coordenador): {clientes_tempos}")

		# passo 4 (cálculo): calcula a média dos tempos.
		media = sum(clientes_tempos) // len(clientes_tempos)
		log_event(f"[Coordenador] Média calculada: {media}")

		# passo 4 (distribuição): envia o ajuste para cada cliente.
		for i, conn in enumerate(conexoes):
			ajuste = media - clientes_tempos[i]
			log_event(f"[Coordenador] Enviando ajuste para cliente {i+1}: {ajuste}")
			conn.sendall(str(ajuste).encode())
			conn.close()
		log_event(f"[Coordenador] Relógio antes = {tempo_Coordenador}, ajuste = {media - tempo_Coordenador}")
		log_event(f"[Coordenador] Relógio ajustado = {tempo_Coordenador + (media - tempo_Coordenador)}")


if __name__ == "__main__":
	# este bloco principal organiza e inicia a simulação.
	open(LOG_FILE, "w").close()
	log_event(f"[Sistema] Iniciando algoritmo de berkeley com {NUM_CLIENTS} processos (clientes)...")

	server_thread = threading.Thread(target=servidor)
	server_thread.start()
	time.sleep(1)

	offsets = [random.randint(-10, 10) for _ in range(NUM_CLIENTS)]
	client_threads = [ClientThread(i+1, offsets[i]) for i in range(NUM_CLIENTS)]

	for ct in client_threads:
		ct.start()

	for ct in client_threads:
		ct.join()

	server_thread.join()
	log_event(f"[sistema] Execução finalizada. veja o log completo em {LOG_FILE}")
	log_event(f"[Sistema] Execução finalizada. Veja o log completo em {LOG_FILE}")
	log_event(f"[Sistema] Execução finalizada. Veja o log completo em {LOG_FILE}")
