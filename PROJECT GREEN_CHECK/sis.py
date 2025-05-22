import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
from datetime import datetime
import json
import os
from PIL import Image, ImageTk
import math

class SistemaInspecaoVisual:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Sistema de Inspeção Visual - Verificação de Adesivos")
        self.root.geometry("1200x800")
        
        # Variáveis de controle
        self.camera = None
        self.capturando = False
        self.camera_index = 0
        self.cameras_disponiveis = []
        self.imagem_padrao = None
        self.template_adesivo = None
        self.posicao_padrao = None
        self.rotacao_padrao = None
        self.tolerancia_posicao = 50  # pixels
        self.tolerancia_rotacao = 15  # graus
        self.tolerancia_cor = 30
        
        # Configurações de detecção
        self.config = {
            'area_min_chapa': 5000,
            'area_min_adesivo': 500,
            'threshold_match': 0.7,
            'blur_kernel': 5
        }
        
        # Log de inspeções
        self.log_inspecoes = []
        
        self.setup_interface()
        self.detectar_cameras()
        self.carregar_configuracoes()
        
    def setup_interface(self):
        """Configura a interface gráfica"""
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Frame superior - controles
        control_frame = ttk.LabelFrame(main_frame, text="Controles", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Primeira linha - seleção de câmera
        camera_frame = ttk.Frame(control_frame)
        camera_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(camera_frame, text="Câmera:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.camera_var = tk.StringVar()
        self.camera_combo = ttk.Combobox(camera_frame, textvariable=self.camera_var, 
                                        width=30, state="readonly")
        self.camera_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.camera_combo.bind('<<ComboboxSelected>>', self.trocar_camera)
        
        # Botões de controle
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(fill=tk.X)
        
        self.btn_camera = ttk.Button(btn_frame, text="Iniciar Câmera", command=self.toggle_camera)
        self.btn_camera.pack(side=tk.LEFT, padx=(0, 10))
        
        self.btn_padrao = ttk.Button(btn_frame, text="Capturar Padrão", command=self.capturar_padrao)
        self.btn_padrao.pack(side=tk.LEFT, padx=(0, 10))
        
        # Botão SCAN especial com estilo
        scan_style = ttk.Style()
        scan_style.configure('Scan.TButton', foreground='white', background='#4CAF50')
        
        self.btn_scan = ttk.Button(btn_frame, text="🔍 SCAN", command=self.realizar_inspecao, 
                                  style='Scan.TButton')
        self.btn_scan.pack(side=tk.LEFT, padx=(0, 10))
        
        self.btn_config = ttk.Button(btn_frame, text="Configurações", command=self.abrir_configuracoes)
        self.btn_config.pack(side=tk.LEFT, padx=(0, 10))
        
        self.btn_log = ttk.Button(btn_frame, text="Ver Log", command=self.mostrar_log)
        self.btn_log.pack(side=tk.LEFT, padx=(0, 10))
        
        # Status com fonte maior
        self.status_var = tk.StringVar(value="Sistema Pronto")
        status_label = tk.Label(control_frame, textvariable=self.status_var, 
                               font=('Arial', 11), fg='blue')
        status_label.pack(pady=(10, 0))
        
        # Frame do meio - visualização
        view_frame = ttk.Frame(main_frame)
        view_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame da câmera
        camera_frame = ttk.LabelFrame(view_frame, text="Visualização da Câmera", padding=5)
        camera_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.camera_label = ttk.Label(camera_frame, text="Câmera não iniciada")
        self.camera_label.pack(expand=True)
        
        # Frame do padrão
        padrao_frame = ttk.LabelFrame(view_frame, text="Imagem Padrão", padding=5)
        padrao_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.padrao_label = ttk.Label(padrao_frame, text="Nenhum padrão capturado")
        self.padrao_label.pack(expand=True)
        
        # Frame inferior - resultado
        self.resultado_frame = ttk.LabelFrame(main_frame, text="Resultado da Inspeção", padding=10)
        self.resultado_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.resultado_var = tk.StringVar(value="Aguardando inspeção...")
        self.resultado_label = tk.Label(self.resultado_frame, textvariable=self.resultado_var, 
                                       font=('Arial', 16, 'bold'), fg='black')
        self.resultado_label.pack()

    def detectar_cameras(self):
        """Detecta todas as câmeras disponíveis no sistema"""
        self.cameras_disponiveis = []
        
        # Testar até 10 índices de câmera
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    # Tentar obter informações da câmera
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    fps = int(cap.get(cv2.CAP_PROP_FPS))
                    
                    camera_info = f"Câmera {i} ({width}x{height}@{fps}fps)"
                    self.cameras_disponiveis.append((i, camera_info))
                cap.release()
        
        # Atualizar o combobox
        if self.cameras_disponiveis:
            valores = [info for _, info in self.cameras_disponiveis]
            self.camera_combo['values'] = valores
            self.camera_combo.set(valores[0])  # Selecionar primeira câmera
            self.camera_index = self.cameras_disponiveis[0][0]
            self.status_var.set(f"Detectadas {len(self.cameras_disponiveis)} câmera(s)")
        else:
            self.camera_combo['values'] = ["Nenhuma câmera detectada"]
            self.camera_combo.set("Nenhuma câmera detectada")
            self.status_var.set("Nenhuma câmera detectada")

    def trocar_camera(self, event=None):
        """Troca a câmera selecionada"""
        if not self.cameras_disponiveis:
            return
        
        selected_text = self.camera_var.get()
        
        # Encontrar o índice da câmera selecionada
        for index, info in self.cameras_disponiveis:
            if info == selected_text:
                self.camera_index = index
                break
        
        # Se a câmera estiver ativa, reiniciar com nova câmera
        if self.capturando:
            self.parar_camera()
            time.sleep(0.5)  # Aguardar um pouco
            self.iniciar_camera()
        
        self.status_var.set(f"Câmera {self.camera_index} selecionada")

    def toggle_camera(self):
        """Liga/desliga a câmera"""
        if not self.capturando:
            self.iniciar_camera()
        else:
            self.parar_camera()

    def iniciar_camera(self):
        """Inicia a captura da câmera"""
        try:
            if not self.cameras_disponiveis:
                messagebox.showerror("Erro", "Nenhuma câmera disponível")
                return
            
            self.camera = cv2.VideoCapture(self.camera_index)
            if not self.camera.isOpened():
                messagebox.showerror("Erro", f"Não foi possível abrir a câmera {self.camera_index}")
                return
            
            # Configurar resolução se possível
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            
            self.capturando = True
            self.btn_camera.config(text="Parar Câmera")
            self.status_var.set(f"Câmera {self.camera_index} ativa")
            
            # Thread para captura contínua
            self.thread_camera = threading.Thread(target=self.loop_camera)
            self.thread_camera.daemon = True
            self.thread_camera.start()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao iniciar câmera: {str(e)}")
            self.status_var.set("Erro ao iniciar câmera")

    def parar_camera(self):
        """Para a captura da câmera"""
        self.capturando = False
        if self.camera:
            self.camera.release()
        self.btn_camera.config(text="Iniciar Câmera")
        self.status_var.set("Câmera desligada")
        self.camera_label.config(image='', text="Câmera não iniciada")

    def loop_camera(self):
        """Loop principal da câmera"""
        while self.capturando:
            try:
                ret, frame = self.camera.read()
                if ret:
                    # Redimensionar para visualização
                    frame_display = cv2.resize(frame, (400, 300))
                    frame_rgb = cv2.cvtColor(frame_display, cv2.COLOR_BGR2RGB)
                    
                    # Converter para PhotoImage
                    img_pil = Image.fromarray(frame_rgb)
                    img_tk = ImageTk.PhotoImage(img_pil)
                    
                    # Atualizar interface
                    self.camera_label.config(image=img_tk, text="")
                    self.camera_label.image = img_tk
                    
                time.sleep(0.033)  # ~30 FPS
            except Exception as e:
                print(f"Erro na captura: {e}")
                break

    def capturar_padrao(self):
        """Captura a imagem padrão"""
        if not self.capturando:
            messagebox.showwarning("Aviso", "Inicie a câmera primeiro")
            return
        
        try:
            ret, frame = self.camera.read()
            if ret:
                self.imagem_padrao = frame.copy()
                
                # Detectar chapa verde e adesivo amarelo
                chapa_detectada, adesivo_detectado = self.detectar_componentes(frame)
                
                if chapa_detectada and adesivo_detectado:
                    self.posicao_padrao = adesivo_detectado['centro']
                    self.rotacao_padrao = adesivo_detectado['rotacao']
                    self.template_adesivo = adesivo_detectado['template']
                    
                    # Mostrar imagem padrão na interface
                    self.mostrar_imagem_padrao()
                    
                    self.status_var.set("Padrão capturado com sucesso")
                    messagebox.showinfo("Sucesso", "Padrão capturado e analisado com sucesso!")
                    
                    # Salvar configuração
                    self.salvar_configuracoes()
                else:
                    messagebox.showerror("Erro", "Não foi possível detectar a chapa verde ou adesivo amarelo")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao capturar padrão: {str(e)}")

    def mostrar_imagem_padrao(self):
        """Mostra a imagem padrão na interface"""
        if self.imagem_padrao is not None:
            # Redimensionar e converter
            img_display = cv2.resize(self.imagem_padrao, (400, 300))
            img_rgb = cv2.cvtColor(img_display, cv2.COLOR_BGR2RGB)
            
            # Desenhar indicadores do padrão detectado
            if self.posicao_padrao:
                # Escalar posição para tamanho de display
                scale_x = 400 / self.imagem_padrao.shape[1]
                scale_y = 300 / self.imagem_padrao.shape[0]
                pos_display = (int(self.posicao_padrao[0] * scale_x), 
                             int(self.posicao_padrao[1] * scale_y))
                
                cv2.circle(img_rgb, pos_display, 10, (255, 0, 0), 2)
                cv2.putText(img_rgb, "PADRAO", (pos_display[0]-30, pos_display[1]-15), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
            
            img_pil = Image.fromarray(img_rgb)
            img_tk = ImageTk.PhotoImage(img_pil)
            
            self.padrao_label.config(image=img_tk, text="")
            self.padrao_label.image = img_tk

    def detectar_componentes(self, frame):
        """Detecta chapa verde e adesivo amarelo"""
        # Suavizar imagem
        frame_blur = cv2.GaussianBlur(frame, (self.config['blur_kernel'], self.config['blur_kernel']), 0)
        hsv = cv2.cvtColor(frame_blur, cv2.COLOR_BGR2HSV)
        
        # Detectar chapa verde
        lower_green = np.array([40, 50, 50])
        upper_green = np.array([80, 255, 255])
        mask_green = cv2.inRange(hsv, lower_green, upper_green)
        
        contours_green, _ = cv2.findContours(mask_green, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        chapa_detectada = None
        
        for contour in contours_green:
            area = cv2.contourArea(contour)
            if area > self.config['area_min_chapa']:
                chapa_detectada = {
                    'contorno': contour,
                    'area': area,
                    'centro': self.calcular_centro(contour)
                }
                break
        
        # Detectar adesivo amarelo
        lower_yellow = np.array([20, 100, 100])
        upper_yellow = np.array([30, 255, 255])
        mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
        
        contours_yellow, _ = cv2.findContours(mask_yellow, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        adesivo_detectado = None
        
        for contour in contours_yellow:
            area = cv2.contourArea(contour)
            if area > self.config['area_min_adesivo']:
                centro = self.calcular_centro(contour)
                rotacao = self.calcular_rotacao(contour)
                
                # Extrair template do adesivo
                x, y, w, h = cv2.boundingRect(contour)
                template = frame[y:y+h, x:x+w]
                
                adesivo_detectado = {
                    'contorno': contour,
                    'area': area,
                    'centro': centro,
                    'rotacao': rotacao,
                    'template': template
                }
                break
        
        return chapa_detectada, adesivo_detectado

    def calcular_centro(self, contour):
        """Calcula o centro de um contorno"""
        M = cv2.moments(contour)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            return (cx, cy)
        return None

    def calcular_rotacao(self, contour):
        """Calcula a rotação de um contorno usando PCA"""
        if len(contour) < 5:
            return 0
        
        # Aplicar PCA para encontrar orientação principal
        pts = contour.reshape(-1, 2).astype(np.float32)
        mean, eigenvec = cv2.PCACompute(pts, mean=None)
        
        # Calcular ângulo do primeiro componente principal
        angle = math.atan2(eigenvec[0, 1], eigenvec[0, 0])
        return math.degrees(angle)

    def realizar_inspecao(self):
        """Realiza a inspeção comparando com o padrão"""
        if not self.capturando:
            messagebox.showwarning("Aviso", "Inicie a câmera primeiro")
            return
        
        if self.imagem_padrao is None:
            messagebox.showwarning("Aviso", "Capture o padrão primeiro")
            return
        
        try:
            # Capturar frame atual
            ret, frame_atual = self.camera.read()
            if not ret:
                messagebox.showerror("Erro", "Erro ao capturar imagem")
                return
            
            # Detectar componentes na imagem atual
            chapa_atual, adesivo_atual = self.detectar_componentes(frame_atual)
            
            resultado = self.comparar_com_padrao(chapa_atual, adesivo_atual)
            
            # Registrar inspeção
            self.registrar_inspecao(resultado, frame_atual)
            
            # Mostrar resultado
            self.exibir_resultado(resultado)
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro durante inspeção: {str(e)}")

    def comparar_com_padrao(self, chapa_atual, adesivo_atual):
        """Compara a detecção atual com o padrão"""
        resultado = {
            'aprovado': False,
            'detalhes': [],
            'timestamp': datetime.now(),
            'diferencas': {}
        }
        
        # Verificar se detectou chapa
        if not chapa_atual:
            resultado['detalhes'].append("❌ Chapa verde não detectada")
            return resultado
        else:
            resultado['detalhes'].append("✅ Chapa verde detectada")
        
        # Verificar se detectou adesivo
        if not adesivo_atual:
            resultado['detalhes'].append("❌ Adesivo amarelo não detectado")
            return resultado
        else:
            resultado['detalhes'].append("✅ Adesivo amarelo detectado")
        
        # Comparar posição
        pos_atual = adesivo_atual['centro']
        diff_pos = math.sqrt((pos_atual[0] - self.posicao_padrao[0])**2 + 
                            (pos_atual[1] - self.posicao_padrao[1])**2)
        
        resultado['diferencas']['posicao'] = diff_pos
        
        if diff_pos <= self.tolerancia_posicao:
            resultado['detalhes'].append(f"✅ Posição OK (diferença: {diff_pos:.1f}px)")
        else:
            resultado['detalhes'].append(f"❌ Posição incorreta (diferença: {diff_pos:.1f}px)")
            return resultado
        
        # Comparar rotação
        rot_atual = adesivo_atual['rotacao']
        diff_rot = abs(rot_atual - self.rotacao_padrao)
        if diff_rot > 180:
            diff_rot = 360 - diff_rot
        
        resultado['diferencas']['rotacao'] = diff_rot
        
        if diff_rot <= self.tolerancia_rotacao:
            resultado['detalhes'].append(f"✅ Rotação OK (diferença: {diff_rot:.1f}°)")
        else:
            resultado['detalhes'].append(f"❌ Rotação incorreta (diferença: {diff_rot:.1f}°)")
            return resultado
        
        # Se chegou até aqui, está aprovado
        resultado['aprovado'] = True
        resultado['detalhes'].append("🎉 INSPEÇÃO APROVADA!")
        
        return resultado

    def exibir_resultado(self, resultado):
        """Exibe o resultado da inspeção"""
        if resultado['aprovado']:
            self.resultado_var.set("✅ APROVADO - Adesivo posicionado corretamente")
            self.resultado_label.config(fg='green')
        else:
            self.resultado_var.set("❌ REPROVADO - Posicionamento incorreto")
            self.resultado_label.config(fg='red')
        
        # Mostrar detalhes em popup
        detalhes = '\n'.join(resultado['detalhes'])
        if resultado['aprovado']:
            messagebox.showinfo("Resultado da Inspeção", detalhes)
        else:
            messagebox.showerror("Resultado da Inspeção", detalhes)

    def registrar_inspecao(self, resultado, frame):
        """Registra a inspeção no log"""
        registro = {
            'timestamp': resultado['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
            'aprovado': resultado['aprovado'],
            'detalhes': resultado['detalhes'],
            'diferencas': resultado.get('diferencas', {})
        }
        
        self.log_inspecoes.append(registro)
        
        # Salvar frame da inspeção
        filename = f"inspecao_{resultado['timestamp'].strftime('%Y%m%d_%H%M%S')}.jpg"
        cv2.imwrite(f"logs/{filename}", frame)
        
        # Salvar log em JSON
        self.salvar_log()

    def abrir_configuracoes(self):
        """Abre janela de configurações"""
        config_window = tk.Toplevel(self.root)
        config_window.title("Configurações")
        config_window.geometry("400x300")
        
        # Tolerâncias
        ttk.Label(config_window, text="Tolerância de Posição (pixels):").pack(pady=5)
        pos_var = tk.StringVar(value=str(self.tolerancia_posicao))
        ttk.Entry(config_window, textvariable=pos_var).pack(pady=5)
        
        ttk.Label(config_window, text="Tolerância de Rotação (graus):").pack(pady=5)
        rot_var = tk.StringVar(value=str(self.tolerancia_rotacao))
        ttk.Entry(config_window, textvariable=rot_var).pack(pady=5)
        
        def salvar_config():
            try:
                self.tolerancia_posicao = float(pos_var.get())
                self.tolerancia_rotacao = float(rot_var.get())
                self.salvar_configuracoes()
                messagebox.showinfo("Sucesso", "Configurações salvas!")
                config_window.destroy()
            except ValueError:
                messagebox.showerror("Erro", "Valores inválidos")
        
        # Botão para atualizar lista de câmeras
        ttk.Button(config_window, text="🔄 Atualizar Câmeras", 
                  command=self.detectar_cameras).pack(pady=10)
        
        ttk.Button(config_window, text="Salvar", command=salvar_config).pack(pady=20)

    def mostrar_log(self):
        """Mostra o log de inspeções"""
        if not self.log_inspecoes:
            messagebox.showinfo("Log", "Nenhuma inspeção registrada")
            return
        
        log_window = tk.Toplevel(self.root)
        log_window.title("Log de Inspeções")
        log_window.geometry("600x400")
        
        # Criar Treeview para mostrar log
        tree = ttk.Treeview(log_window, columns=('Timestamp', 'Resultado'), show='headings')
        tree.heading('Timestamp', text='Data/Hora')
        tree.heading('Resultado', text='Resultado')
        
        for registro in self.log_inspecoes[-50:]:  # Últimas 50 inspeções
            resultado_text = "APROVADO" if registro['aprovado'] else "REPROVADO"
            tree.insert('', 'end', values=(registro['timestamp'], resultado_text))
        
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def salvar_configuracoes(self):
        """Salva configurações em arquivo"""
        config_data = {
            'tolerancia_posicao': self.tolerancia_posicao,
            'tolerancia_rotacao': self.tolerancia_rotacao,
            'posicao_padrao': self.posicao_padrao,
            'rotacao_padrao': self.rotacao_padrao,
            'config': self.config
        }
        
        os.makedirs('config', exist_ok=True)
        with open('config/sistema_config.json', 'w') as f:
            json.dump(config_data, f, indent=2)

    def carregar_configuracoes(self):
        """Carrega configurações do arquivo"""
        try:
            if os.path.exists('config/sistema_config.json'):
                with open('config/sistema_config.json', 'r') as f:
                    config_data = json.load(f)
                
                self.tolerancia_posicao = config_data.get('tolerancia_posicao', 50)
                self.tolerancia_rotacao = config_data.get('tolerancia_rotacao', 15)
                self.posicao_padrao = config_data.get('posicao_padrao')
                self.rotacao_padrao = config_data.get('rotacao_padrao')
                self.config.update(config_data.get('config', {}))
        except:
            pass

    def salvar_log(self):
        """Salva log em arquivo"""
        os.makedirs('logs', exist_ok=True)
        with open('logs/inspecoes_log.json', 'w') as f:
            json.dump(self.log_inspecoes, f, indent=2, default=str)

    def executar(self):
        """Executa o sistema"""
        # Criar diretórios necessários
        os.makedirs('logs', exist_ok=True)
        os.makedirs('config', exist_ok=True)
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def on_closing(self):
        """Executado ao fechar o sistema"""
        self.parar_camera()
        self.root.destroy()

# DEPENDÊNCIAS NECESSÁRIAS:
# pip install opencv-python numpy pillow
# tkinter já vem instalado com Python

if __name__ == "__main__":
    print("🔧 Sistema de Inspeção Visual v1.0")
    print("📋 Verificando dependências...")
    
    try:
        import cv2
        import numpy as np
        from PIL import Image, ImageTk
        print("✅ Todas as dependências estão OK!")
        print("🚀 Iniciando sistema...")
        
        sistema = SistemaInspecaoVisual()
        sistema.executar()
        
    except ImportError as e:
        print(f"❌ Erro de dependência: {e}")
        print("\n📦 Para instalar as dependências necessárias, execute:")
        print("pip install opencv-python numpy pillow")
        print("\nNota: tkinter já vem com Python, não precisa instalar")