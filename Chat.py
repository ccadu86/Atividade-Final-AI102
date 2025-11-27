from openai import OpenAI
import base64
import os
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from PIL import Image, ImageTk
from dotenv import load_dotenv
import json
import re

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Como instalar as dependências:
# 1. Certifique-se de ter Python 3.7 ou superior instalado
# 2. Execute o comando abaixo no terminal para instalar as dependências do requirements.txt:
#    pip install -r requirements.txt
# 3. Ou instale manualmente com: pip install openai Pillow python-dotenv
# 4. Crie um arquivo .env na raiz do projeto com suas credenciais (use .env.example como modelo)

class AnalisadorImagens:
    def __init__(self, root):
        self.root = root
        self.root.title("Analisador de Caixa e Nota Fiscal")
        self.root.geometry("900x700")
        
        # Carregar credenciais das variáveis de ambiente
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1")
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        
        # Validar se as credenciais foram carregadas
        if not self.endpoint or not self.api_key:
            raise ValueError(
                "Credenciais não encontradas! \n"
                "Certifique-se de criar um arquivo .env com:\n"
                "AZURE_OPENAI_ENDPOINT=seu_endpoint\n"
                "AZURE_OPENAI_API_KEY=sua_api_key\n"
                "AZURE_OPENAI_DEPLOYMENT=gpt-4.1"
            )
        
        self.client = OpenAI(
            base_url=self.endpoint,
            api_key=self.api_key
        )
        
        self.imagem_caixa_path = None
        self.imagem_nota_path = None
        self.informacoes_caixa = None
        self.informacoes_nota = None
        
        self.criar_interface()
    
    def criar_interface(self):
        # Criar sistema de abas
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Aba 1: Análise Individual
        self.tab_analise = tk.Frame(self.notebook)
        self.notebook.add(self.tab_analise, text="1. Análise Individual")
        
        # Aba 2: Cruzamento de Informações
        self.tab_cruzamento = tk.Frame(self.notebook)
        self.notebook.add(self.tab_cruzamento, text="2. Cruzamento de Informações")
        
        self.criar_aba_analise()
        self.criar_aba_cruzamento()
        
        # Botão de Reset Global
        btn_reset = tk.Button(self.root, text="🔄 Nova Análise (Reset)", command=self.resetar_sistema, bg="#FF5722", fg="white", font=("Arial", 11, "bold"))
        btn_reset.pack(fill="x", padx=10, pady=5)
        
    def criar_aba_analise(self):
        # Frame para Caixa
        frame_caixa = tk.LabelFrame(self.tab_analise, text="1. Imagem da Caixa", padx=10, pady=10)
        frame_caixa.pack(fill="x", padx=10, pady=5)
        
        self.btn_caixa = tk.Button(frame_caixa, text="Anexar Imagem da Caixa", command=self.anexar_caixa, bg="#4CAF50", fg="white", font=("Arial", 10, "bold"))
        self.btn_caixa.pack(side="left", padx=5)
        
        self.label_caixa = tk.Label(frame_caixa, text="Nenhuma imagem selecionada", fg="gray")
        self.label_caixa.pack(side="left", padx=5)
        
        self.btn_analisar_caixa = tk.Button(frame_caixa, text="Analisar Caixa", command=self.analisar_caixa, state="disabled", bg="#2196F3", fg="white", font=("Arial", 10, "bold"))
        self.btn_analisar_caixa.pack(side="right", padx=5)
        
        # Frame para Nota
        frame_nota = tk.LabelFrame(self.tab_analise, text="2. Imagem da Nota Fiscal", padx=10, pady=10)
        frame_nota.pack(fill="x", padx=10, pady=5)
        
        self.btn_nota = tk.Button(frame_nota, text="Anexar Imagem da Nota", command=self.anexar_nota, state="disabled", bg="#4CAF50", fg="white", font=("Arial", 10, "bold"))
        self.btn_nota.pack(side="left", padx=5)
        
        self.label_nota = tk.Label(frame_nota, text="Primeiro analise a caixa", fg="gray")
        self.label_nota.pack(side="left", padx=5)
        
        self.btn_analisar_nota = tk.Button(frame_nota, text="Analisar Nota", command=self.analisar_nota, state="disabled", bg="#2196F3", fg="white", font=("Arial", 10, "bold"))
        self.btn_analisar_nota.pack(side="right", padx=5)
        
        # Frame para resultados
        frame_resultados = tk.LabelFrame(self.tab_analise, text="Resultados da Análise", padx=10, pady=10)
        frame_resultados.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.text_resultados = scrolledtext.ScrolledText(frame_resultados, wrap=tk.WORD, font=("Arial", 10))
        self.text_resultados.pack(fill="both", expand=True)
        
    def criar_aba_cruzamento(self):
        # Header Frame (Título + Reset)
        frame_header = tk.Frame(self.tab_cruzamento, bg="#3F51B5")
        frame_header.pack(fill="x")
        
        # Título
        titulo = tk.Label(frame_header, text="Análise de Cruzamento de Informações", font=("Arial", 16, "bold"), bg="#3F51B5", fg="white", pady=10)
        titulo.pack(side="left", padx=10)
        
        # Botão de Reset na aba 2 (Solicitado pelo usuário)
        btn_reset_aba2 = tk.Button(frame_header, text="🔄 Resetar", command=self.resetar_sistema, bg="#FF5722", fg="white", font=("Arial", 10, "bold"))
        btn_reset_aba2.pack(side="right", padx=10)
        
        # Frame de status
        self.frame_status = tk.Frame(self.tab_cruzamento, padx=10, pady=10)
        self.frame_status.pack(fill="x")
        
        self.lbl_status_caixa = tk.Label(self.frame_status, text="❌ Informações da Caixa: Pendente", fg="red", font=("Arial", 10))
        self.lbl_status_caixa.pack(anchor="w")
        
        self.lbl_status_nota = tk.Label(self.frame_status, text="❌ Informações da Nota: Pendente", fg="red", font=("Arial", 10))
        self.lbl_status_nota.pack(anchor="w")
        
        # Label para o Veredito Final
        self.lbl_veredito = tk.Label(self.frame_status, text="", font=("Arial", 14, "bold"))
        self.lbl_veredito.pack(anchor="w", pady=10)
        
        # Botões de ação
        frame_botoes = tk.Frame(self.tab_cruzamento, padx=10, pady=10)
        frame_botoes.pack(fill="x")
        
        self.btn_cruzar = tk.Button(frame_botoes, text="🔍 Realizar Cruzamento de Informações", command=self.realizar_cruzamento, state="disabled", bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), padx=20, pady=10)
        self.btn_cruzar.pack(side="left", padx=5)
        
        self.btn_salvar = tk.Button(frame_botoes, text="💾 Salvar Relatório", command=self.salvar_relatorio, state="disabled", bg="#2196F3", fg="white", font=("Arial", 12, "bold"), padx=20, pady=10)
        self.btn_salvar.pack(side="left", padx=5)
        
        # Área de resultados do cruzamento
        frame_resultados = tk.LabelFrame(self.tab_cruzamento, text="Resultado do Cruzamento", padx=10, pady=10)
        frame_resultados.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.text_cruzamento = scrolledtext.ScrolledText(frame_resultados, wrap=tk.WORD, font=("Arial", 10), state="disabled")
        self.text_cruzamento.pack(fill="both", expand=True)

    def atualizar_status_cruzamento(self):
        if self.informacoes_caixa:
            self.lbl_status_caixa.config(text="✓ Informações da Caixa: Carregadas", fg="green")
        
        if self.informacoes_nota:
            self.lbl_status_nota.config(text="✓ Informações da Nota: Carregadas", fg="green")
            
        if self.informacoes_caixa and self.informacoes_nota:
            self.btn_cruzar.config(state="normal")
            
    def realizar_cruzamento(self):
        self.text_cruzamento.config(state="normal")
        self.text_cruzamento.delete(1.0, tk.END)
        self.text_cruzamento.insert(tk.END, "🔄 Realizando cruzamento de informações...\n\n")
        self.text_cruzamento.config(state="disabled")
        self.root.update()
        
        try:
            completion = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Realize um cruzamento SIMPLIFICADO e DIRETO entre as informações da caixa e da nota fiscal.
Foque EXCLUSIVAMENTE nas informações cruciais: Produtos (Nome e Quantidade) e Número da Nota.

INFORMAÇÕES DA CAIXA:
{self.informacoes_caixa}

INFORMAÇÕES DA NOTA FISCAL:
{self.informacoes_nota}

Por favor, forneça a análise no seguinte formato:

1. COMPARAÇÃO DE PRODUTOS (Crucial):
   Liste cada produto encontrado e compare a quantidade.
   Formato:
   - [Nome do Produto]: Caixa [Qtd] x Nota [Qtd] -> [Status: OK/DIVERGENTE]

2. COMPARAÇÃO DO NÚMERO DA NOTA:
   - Caixa: [Número]
   - Nota: [Número]
   - Status: [OK/DIVERGENTE]

3. CONCLUSÃO RÁPIDA:
   - Aprovado ou Reprovado com base apenas nos produtos e número da nota.

4. DADOS ESTRUTURADOS (JSON):
   Por favor, inclua ao final da resposta, EXATAMENTE o seguinte bloco JSON (e nada mais depois dele):
   ```json
   {{
       "score": <numero_inteiro_0_a_100_baseado_apenas_em_produtos_e_numero_nota>,
       "produtos_match": <true_se_nomes_e_quantidades_batem_senao_false>,
       "nota_match": <true_se_numero_nota_igual_senao_false>
   }}
   ```"""
                    }
                ],
            )
            
            resultado_cruzamento = completion.choices[0].message.content
            
            # Extrair JSON do final
            try:
                json_match = re.search(r"```json\s*({.*?})\s*```", resultado_cruzamento, re.DOTALL)
                if json_match:
                    dados_json = json.loads(json_match.group(1))
                    score = dados_json.get("score", 0)
                    produtos_match = dados_json.get("produtos_match", False)
                    nota_match = dados_json.get("nota_match", False)
                    
                    # Lógica de Aprovação
                    if score >= 70 and produtos_match and nota_match:
                        self.lbl_veredito.config(text="✅ APROVADO", fg="green")
                    else:
                        motivos = []
                        if score < 70: motivos.append(f"Score baixo ({score}%)")
                        if not produtos_match: motivos.append("Produtos divergentes")
                        if not nota_match: motivos.append("Nota fiscal divergente")
                        
                        texto_reprovado = "❌ REPROVADO"
                        if motivos:
                            texto_reprovado += f" ({', '.join(motivos)})"
                        
                        self.lbl_veredito.config(text=texto_reprovado, fg="red")
                else:
                    self.lbl_veredito.config(text="⚠️ Análise Manual Necessária (JSON não encontrado)", fg="orange")
            except Exception as e:
                print(f"Erro ao processar JSON: {e}")
                self.lbl_veredito.config(text="⚠️ Erro ao processar veredito automático", fg="orange")
            
            self.text_cruzamento.config(state="normal")
            self.text_cruzamento.delete(1.0, tk.END)
            self.text_cruzamento.insert(tk.END, "="*90 + "\n")
            self.text_cruzamento.insert(tk.END, "ANÁLISE DE CRUZAMENTO - CAIXA vs NOTA FISCAL\n")
            self.text_cruzamento.insert(tk.END, "="*90 + "\n\n")
            self.text_cruzamento.insert(tk.END, resultado_cruzamento + "\n\n")
            self.text_cruzamento.insert(tk.END, "="*90 + "\n")
            self.text_cruzamento.insert(tk.END, "Análise concluída com sucesso!\n")
            self.text_cruzamento.config(state="disabled")
            self.text_cruzamento.see(1.0)
            
            self.btn_cruzar.config(state="disabled")
            self.btn_salvar.config(state="normal")
            
            messagebox.showinfo("Sucesso", "Cruzamento de informações concluído!")
            
        except Exception as e:
            erro_msg = str(e)
            if "429" in erro_msg:
                erro_msg = "O sistema da IA está sobrecarregado no momento (Erro 429). Por favor, aguarde alguns instantes e tente novamente."
            
            self.text_cruzamento.config(state="normal")
            self.text_cruzamento.insert(tk.END, f"\n❌ Erro ao realizar cruzamento: {erro_msg}\n")
            self.text_cruzamento.config(state="disabled")
            messagebox.showerror("Erro", f"Erro ao realizar cruzamento: {erro_msg}")
    
    def salvar_relatorio(self):
        try:
            filepath = filedialog.asksaveasfilename(
                title="Salvar Relatório de Cruzamento",
                defaultextension=".txt",
                filetypes=[("Arquivo de Texto", "*.txt"), ("Todos os arquivos", "*.*")]
            )
            if filepath:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(self.text_cruzamento.get(1.0, tk.END))
                messagebox.showinfo("Sucesso", f"Relatório salvo em:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar relatório: {str(e)}")

    def resetar_sistema(self):
        if messagebox.askyesno("Confirmar Reset", "Deseja limpar tudo e iniciar uma nova análise?"):
            # Limpar variáveis
            self.imagem_caixa_path = None
            self.imagem_nota_path = None
            self.informacoes_caixa = None
            self.informacoes_nota = None
            
            # Resetar UI Aba 1
            self.label_caixa.config(text="Nenhuma imagem selecionada", fg="gray")
            self.label_nota.config(text="Primeiro analise a caixa", fg="gray")
            self.btn_analisar_caixa.config(state="disabled")
            self.btn_nota.config(state="disabled")
            self.btn_analisar_nota.config(state="disabled")
            self.text_resultados.delete(1.0, tk.END)
            
            # Resetar UI Aba 2
            self.lbl_status_caixa.config(text="❌ Informações da Caixa: Pendente", fg="red")
            self.lbl_status_nota.config(text="❌ Informações da Nota: Pendente", fg="red")
            self.lbl_veredito.config(text="")
            self.btn_cruzar.config(state="disabled")
            self.btn_salvar.config(state="disabled")
            self.text_cruzamento.config(state="normal")
            self.text_cruzamento.delete(1.0, tk.END)
            self.text_cruzamento.config(state="disabled")
            
            # Voltar para primeira aba
            self.notebook.select(0)
            
            messagebox.showinfo("Reset", "Sistema pronto para nova análise!")
    
    def anexar_caixa(self):
        filepath = filedialog.askopenfilename(
            title="Selecione a imagem da caixa",
            filetypes=[("Imagens", "*.png *.jpg *.jpeg *.bmp *.gif")]
        )
        if filepath:
            self.imagem_caixa_path = filepath
            self.label_caixa.config(text=os.path.basename(filepath), fg="green")
            self.btn_analisar_caixa.config(state="normal")
            self.text_resultados.insert(tk.END, f"✓ Imagem da caixa selecionada: {os.path.basename(filepath)}\n\n")
    
    def anexar_nota(self):
        filepath = filedialog.askopenfilename(
            title="Selecione a imagem da nota fiscal",
            filetypes=[("Imagens", "*.png *.jpg *.jpeg *.bmp *.gif")]
        )
        if filepath:
            self.imagem_nota_path = filepath
            self.label_nota.config(text=os.path.basename(filepath), fg="green")
            self.btn_analisar_nota.config(state="normal")
            self.text_resultados.insert(tk.END, f"✓ Imagem da nota selecionada: {os.path.basename(filepath)}\n\n")
    
    def analisar_caixa(self):
        if not self.imagem_caixa_path:
            messagebox.showerror("Erro", "Selecione uma imagem da caixa primeiro!")
            return
        
        self.text_resultados.insert(tk.END, "🔍 Analisando imagem da caixa...\n")
        self.root.update()
        
        try:
            with open(self.imagem_caixa_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            completion = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Por favor, extraia todas as informações contidas nesta imagem da caixa. Liste todos os detalhes visíveis como textos, números, códigos de barras, etiquetas, endereços, dimensões, produtos e qualquer outra informação relevante."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
            )
            
            self.informacoes_caixa = completion.choices[0].message.content
            
            self.text_resultados.insert(tk.END, "="*80 + "\n")
            self.text_resultados.insert(tk.END, "INFORMAÇÕES DA CAIXA:\n")
            self.text_resultados.insert(tk.END, "="*80 + "\n")
            self.text_resultados.insert(tk.END, self.informacoes_caixa + "\n\n")
            self.text_resultados.see(tk.END)
            
            # Habilitar próxima etapa
            self.btn_nota.config(state="normal")
            self.label_nota.config(text="Nenhuma imagem selecionada", fg="gray")
            self.atualizar_status_cruzamento()
            
            messagebox.showinfo("Sucesso", "Análise da caixa concluída! Agora você pode anexar a imagem da nota.")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao analisar a caixa: {str(e)}")
            self.text_resultados.insert(tk.END, f"❌ Erro: {str(e)}\n\n")
    
    def analisar_nota(self):
        if not self.imagem_nota_path:
            messagebox.showerror("Erro", "Selecione uma imagem da nota primeiro!")
            return
        
        self.text_resultados.insert(tk.END, "🔍 Analisando imagem da nota fiscal...\n")
        self.root.update()
        
        try:
            with open(self.imagem_nota_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            completion = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Por favor, extraia todas as informações contidas nesta nota fiscal. Liste todos os detalhes visíveis como número da nota, data, produtos, quantidades, valores, destinatário, remetente, CNPJ, e qualquer outra informação relevante."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
            )
            
            self.informacoes_nota = completion.choices[0].message.content
            
            self.text_resultados.insert(tk.END, "="*80 + "\n")
            self.text_resultados.insert(tk.END, "INFORMAÇÕES DA NOTA FISCAL:\n")
            self.text_resultados.insert(tk.END, "="*80 + "\n")
            self.text_resultados.insert(tk.END, self.informacoes_nota + "\n\n")
            self.text_resultados.see(tk.END)
            
            self.atualizar_status_cruzamento()
            
            messagebox.showinfo("Sucesso", "Análise da nota concluída! Vá para a aba 'Cruzamento de Informações'.")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao analisar a nota: {str(e)}")
            self.text_resultados.insert(tk.END, f"❌ Erro: {str(e)}\n\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = AnalisadorImagens(root)
    root.mainloop()